#!/usr/bin/env python3
"""Run the eval set through the pipeline and score what came out.

`qa/run_pipeline.py` asks whether five task queries each produced a set the
audit accepts — a release gate, and a yes/no. This asks the questions that
decide whether the pipeline is worth running at all:

    Of the footage it finds, what fraction is usable?
    Split A / B / C / D, how much of each does a run produce?
    What did one clip of each grade cost?

The set is `eval/queries.json` — 200 canonical tasks drawn from the robotics
downstream task map, stratified 20/50/30 across easy / medium / hard. The
scorecard is `src/video_searching_agent/evaluation/`.

🔴 **This spends real money.** Every query pays for a search; every clip pays
for a download, a minute-rate index pass, a caption pass and a moment read.
At two clips a query, 200 queries is roughly $60-120 depending on how long the
footage is — which is why the whole set needs `--yes`, why the estimate is
printed before anything runs, and why a run writes itself down as it goes so an
interruption costs nothing but the time.

    python eval/run_eval.py --limit 5                 # start here
    python eval/run_eval.py --difficulty easy --limit 20
    python eval/run_eval.py --dry-run --limit 40      # search only: the funnel's top
    python eval/run_eval.py --yes                     # the whole frozen set
    python eval/run_eval.py --resume eval/results/run-1.jsonl --yes
    python eval/run_eval.py --score-only eval/results/run-1.jsonl

Exit code is non-zero when nothing was graded at all, which means the run failed
rather than the pipeline scoring badly. A bad scorecard is a result, not an
error, and does not fail the command.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from video_searching_agent.curation.cost import (  # noqa: E402
    INDEX_PER_VIDEO_MINUTE,
    MOMENT_PER_CALL,
    SEARCH_PER_CALL,
)
from video_searching_agent.evaluation.metrics import (  # noqa: E402
    ClipOutcome,
    QueryOutcome,
    outcome_as_dict,
    outcome_from_dict,
    score_run,
)
from video_searching_agent.evaluation.scorecard import render  # noqa: E402

QUERIES_PATH = ROOT / "eval" / "queries.json"
RESULTS_DIR = ROOT / "eval" / "results"
DEPLOYMENT = os.environ.get("QA_DEPLOYMENT", "https://internet2egoexo.vercel.app")

# The cleaning agent reads a clip's caption, transcription and summary back out
# of the Datalake before it grades anything. Three derived reads, every clip,
# every time — a fixed property of the code path rather than an estimate, which
# is why it is counted rather than left unmeasured.
DERIVED_READS_PER_CLIP = 3

# Rough per-clip spend, used only for the estimate printed before a run.
ESTIMATED_MINUTES_PER_CLIP = 8.0


def _sse(url: str, body: dict, timeout: float = 600.0) -> list[tuple[str, dict]]:
    """Read a whole SSE stream into (event, payload) pairs."""
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    events: list[tuple[str, dict]] = []
    event = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    events.append((event or "", json.loads(line[5:].strip())))
                except json.JSONDecodeError:
                    continue
    return events


def _final(events: list[tuple[str, dict]], name: str = "complete") -> dict:
    return next((payload for event, payload in reversed(events) if event == name), {})


def run_one(case: dict, per_query: int, dry_run: bool, viewpoint: str) -> QueryOutcome:
    """Search, collect and curate one eval query."""
    outcome = QueryOutcome(
        query_id=case["id"],
        query=case["query"],
        rdt_id=case.get("rdt_id", ""),
        task_family=case.get("task_family", ""),
        difficulty=case.get("difficulty", ""),
    )
    started = time.time()

    # ---- 1. search ------------------------------------------------------
    try:
        events = _sse(
            f"{DEPLOYMENT}/api/v1/queries/stream",
            {"query": case["query"], "viewpoint": viewpoint},
            timeout=300,
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        outcome.error = f"search failed: {exc}"
        outcome.seconds = time.time() - started
        return outcome

    complete = _final(events)
    manifest = complete.get("dataset") or {}
    clips = manifest.get("clips") or []
    outcome.candidates = len(clips)
    # What the search found before the pre-download screen, and why the screen
    # dropped what it dropped. Reported because "0 candidates" was being used to
    # mean two opposite things: the search could not answer the query, and the
    # search answered it with eighteen tripod-shot videos.
    outcome.screened_out = int(manifest.get("excluded_clips") or 0)
    outcome.screen_reasons = dict(manifest.get("exclusion_reasons") or {})
    outcome.found = outcome.candidates + outcome.screened_out
    # The search reports its own spend — model tokens plus per-call search fees.
    outcome.discovery_usd = float(((manifest.get("cost") or {}).get("discovery_usd")) or 0.0)

    urls = [clip["url"] for clip in clips if clip.get("url")][:per_query]
    # A dry run attempted nothing, and saying otherwise would report a 0% index
    # rate against candidates that were never collected.
    outcome.dry_run = dry_run
    outcome.attempted = 0 if dry_run else len(urls)
    if dry_run or not urls:
        if not urls:
            if outcome.screened_out:
                top = ", ".join(
                    f"{reason} ×{count}"
                    for reason, count in sorted(
                        outcome.screen_reasons.items(), key=lambda kv: -kv[1]
                    )[:2]
                )
                outcome.error = outcome.error or (
                    f"{outcome.found} found, all screened out ({top})"
                )
            else:
                outcome.error = outcome.error or "search found nothing"
        outcome.seconds = time.time() - started
        return outcome

    # ---- 2. collect, one URL per request --------------------------------
    #
    # One request per clip because a serverless function has 300s and a long
    # video spends most of that being downloaded and indexed; two in one request
    # means the stream is cut before the summary arrives.
    indexed: list[str] = []
    failures: list[str] = []
    for url in urls:
        try:
            events = _sse(
                f"{DEPLOYMENT}/api/v1/collect/stream",
                {
                    "urls": [url],
                    "viewpoint": viewpoint,
                    "require_hands": True,
                    "annotate": True,
                    "viewpoint_verified_urls": [url],
                },
                timeout=900,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"collect cut off: {exc}")
            continue
        last: dict = {}
        for event, payload in events:
            if event in ("clip_stage", "clip_done"):
                last = payload.get("clip") or {}
        if last.get("video_id"):
            indexed.append(str(last["video_id"]))
        else:
            failures.append(
                str(
                    last.get("rejection_reason")
                    or last.get("error")
                    or f"stopped at {last.get('stage') or 'nothing streamed'}"
                )[:90]
            )
    outcome.indexed = len(indexed)
    if not indexed:
        outcome.error = f"nothing reached the Datalake: {sorted(set(failures)) or ['no events']}"
        outcome.seconds = time.time() - started
        return outcome

    # ---- 3. curate: clean, annotate, grade ------------------------------
    try:
        events = _sse(
            f"{DEPLOYMENT}/api/v1/curate/stream",
            {"video_ids": indexed, "query": case["query"], "viewpoint": viewpoint},
            timeout=900,
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        outcome.error = f"curation failed: {exc}"
        outcome.seconds = time.time() - started
        return outcome

    curation = _final(events)
    for clip in curation.get("clips") or []:
        outcome.clips.append(_clip_outcome(outcome.query_id, clip))
    if not outcome.clips:
        outcome.error = "curation returned no graded clips"
    outcome.seconds = time.time() - started
    return outcome


def _clip_outcome(query_id: str, clip: dict) -> ClipOutcome:
    """Read one curated clip into the record, in billable units."""
    cleaning = clip.get("cleaning") or {}
    annotation = clip.get("annotation") or {}
    anchors = cleaning.get("segments") or []
    labels = annotation.get("annotations") or []
    duration = int(clip.get("duration_seconds") or 0)
    spans_read = int(annotation.get("spans_considered") or 0)

    return ClipOutcome(
        query_id=query_id,
        video_id=str(clip.get("video_id") or ""),
        grade=str(clip.get("grade") or "D"),
        score=int(clip.get("score") or 0),
        accepted=bool(clip.get("accepted")),
        annotation_level=str(clip.get("annotation_level") or "L0"),
        duration_seconds=duration,
        usable_seconds=int(clip.get("usable_seconds") or 0),
        idle_seconds=int(clip.get("idle_seconds") or 0),
        action_anchors=sum(1 for a in anchors if a.get("hier_level") == "action"),
        total_anchors=len(anchors),
        annotations=len(labels),
        blocking_failures=list(clip.get("blocking_failures") or []),
        indexed_minutes=duration / 60,
        # One moment search per video, then one read per span it shortlisted.
        moment_search_calls=1 if annotation else 0,
        moment_read_calls=spans_read,
        derived_reads=DERIVED_READS_PER_CLIP,
        look_usd=float(annotation.get("look_cost_usd") or 0.0),
    )


def select(cases: list[dict], args: argparse.Namespace) -> list[dict]:
    """Narrow the frozen set without reordering it."""
    if args.query:
        wanted = set(args.query)
        cases = [c for c in cases if c["id"] in wanted or c.get("rdt_id") in wanted]
    if args.difficulty:
        cases = [c for c in cases if c.get("difficulty") in set(args.difficulty)]
    if args.family:
        needles = [f.lower() for f in args.family]
        cases = [
            c for c in cases if any(n in (c.get("task_family") or "").lower() for n in needles)
        ]
    if args.limit:
        cases = cases[: args.limit]
    return cases


def estimate_usd(cases: int, per_query: int, dry_run: bool) -> float:
    """What the run is about to spend, before it spends it."""
    # Discovery is the measured term the estimate cannot know; the observed
    # range is a few cents a query, so it is included at 5c to keep the number
    # honest rather than flatteringly low.
    discovery = 0.05 * cases
    if dry_run:
        return discovery
    per_clip = (
        ESTIMATED_MINUTES_PER_CLIP * INDEX_PER_VIDEO_MINUTE + SEARCH_PER_CALL + 6 * MOMENT_PER_CALL
    )
    return discovery + cases * per_query * per_clip


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="run only the first N queries of the set")
    parser.add_argument(
        "--difficulty",
        action="append",
        choices=["easy", "medium", "hard"],
        help="restrict to a difficulty tier; repeatable",
    )
    parser.add_argument("--family", action="append", help="substring match on task family")
    parser.add_argument("--query", action="append", help="run only this query id or RDT id")
    parser.add_argument(
        "--per-query", type=int, default=2, help="clips to collect per query (default 2)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="search only — measures the top of the funnel and the discovery spend",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        help="a run's .jsonl: keep its finished queries and only run what is missing",
    )
    parser.add_argument(
        "--score-only",
        type=Path,
        help="score an existing run's .jsonl and write its scorecard; spends nothing",
    )
    parser.add_argument("--out", type=Path, help="where to write the run record (.jsonl)")
    parser.add_argument("--yes", action="store_true", help="do not ask before spending")
    args = parser.parse_args()

    payload = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    version = payload.get("eval_version", "")

    # --- score an existing run -------------------------------------------
    if args.score_only:
        outcomes = [
            outcome_from_dict(json.loads(line))
            for line in args.score_only.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return _report(outcomes, version, args.score_only)

    cases = select(payload["queries"], args)
    if not cases:
        print("no queries selected")
        return 2

    done: dict[str, QueryOutcome] = {}
    record = args.out or args.resume
    if args.resume and args.resume.exists():
        for line in args.resume.read_text(encoding="utf-8").splitlines():
            if line.strip():
                outcome = outcome_from_dict(json.loads(line))
                done[outcome.query_id] = outcome
        print(f"resuming {args.resume}: {len(done)} queries already run")
    todo = [case for case in cases if case["id"] not in done]

    if record is None:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        existing = len(list(RESULTS_DIR.glob("run-*.jsonl")))
        record = RESULTS_DIR / f"run-{existing + 1}.jsonl"

    estimate = estimate_usd(len(todo), args.per_query, args.dry_run)
    print(f"eval set {version} — {DEPLOYMENT}")
    print(
        f"{len(todo)} queries to run"
        f"{f' ({len(done)} resumed)' if done else ''}"
        f", up to {args.per_query} clips each"
        f"{' (dry run: search only)' if args.dry_run else ''}"
    )
    print(f"estimated spend: ~${estimate:.2f}    record: {record}\n")
    if estimate > 5 and not args.yes:
        print("that is more than $5 — re-run with --yes to spend it")
        return 3

    outcomes = list(done.values())
    with record.open("a", encoding="utf-8") as handle:
        for index, case in enumerate(todo, start=1):
            print(f"--- [{index}/{len(todo)}] {case['id']}: {case['query']}", flush=True)
            outcome = run_one(case, args.per_query, args.dry_run, viewpoint="egocentric")
            handle.write(json.dumps(outcome_as_dict(outcome), ensure_ascii=False) + "\n")
            handle.flush()
            outcomes.append(outcome)
            print(f"    {_line(outcome)}", flush=True)

    return _report(outcomes, version, record)


def _line(outcome: QueryOutcome) -> str:
    """One line saying what a query produced."""
    if outcome.error and not outcome.clips:
        return f"[----] {outcome.candidates} candidates — {outcome.error}"
    grades = "".join(clip.grade for clip in sorted(outcome.clips, key=lambda c: -c.score))
    anchors = sum(clip.action_anchors for clip in outcome.clips)
    return (
        f"[{grades or '----'}] {outcome.candidates} found → "
        f"{outcome.indexed}/{outcome.attempted} indexed → "
        f"{outcome.accepted}/{outcome.graded} accepted, {anchors} anchors "
        f"({outcome.seconds:.0f}s)"
    )


def _report(outcomes: list[QueryOutcome], version: str, record: Path) -> int:
    """Score the run, write the scorecard beside its record, and summarise."""
    card = score_run(outcomes, eval_version=version)
    stem = record.with_suffix("")
    json_path = stem.with_suffix(".scorecard.json")
    md_path = stem.with_suffix(".scorecard.md")
    json_path.write_text(json.dumps(card.as_dict(), indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render(card, title=f"Eval scorecard — {record.name}"), encoding="utf-8")

    chain = card.chain
    print("\n" + "=" * 72)
    print(
        f"{chain.graded} clips graded from {chain.queries} queries: "
        f"{chain.accepted} accepted ({100 * chain.acceptance_rate:.0f}%), "
        f"{chain.high_quality} of them A or B "
        f"({100 * chain.high_quality_rate:.0f}%)"
    )
    for grade in ("A", "B", "C", "D"):
        band = card.band(grade)
        if not band.clips:
            continue
        print(
            f"  {grade}: {band.clips:4d} clips  {band.usable_hours:6.2f} usable h  "
            f"${band.usd_per_clip:6.2f}/clip attributed  "
            f"${band.usd_per_clip_obtained:6.2f} to obtain one"
        )
    print(
        f"spent ${card.cost.total_usd:.2f}, of which "
        f"${card.cost.stranded_discovery_usd:.2f} on queries that yielded nothing"
    )
    for item in card.contradictions:
        print(f"  ! {item}")
    print(f"\nscorecard: {md_path}")
    # A dry run grades nothing by design; a live run that grades nothing failed.
    if chain.graded or not outcomes or all(o.dry_run for o in outcomes):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
