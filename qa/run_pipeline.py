#!/usr/bin/env python3
"""Run the whole process on real task queries, then audit what came out.

The half-hourly sweep (`qa/run_qa.py`) proves the *path* works: every stage
streams, the gates fire, a real URL reaches the Datalake. What it does not prove
is that the thing at the end is any good. Twenty videos in and fifty clips out is
only a result if the fifty clips would survive somebody reading them.

So this runs the pipeline end to end on the task queries in
`qa/queries.json` — laundry, kitchen, bike repair, packing, assembly — and then
hands the delivered clips to the quality-check agent, which is allowed to fail
what the pipeline accepted:

    search → collect (download · index · clean · annotate) → curate → AUDIT

It costs real money: a download through Apify (~$0.10), a minute of Datalake
indexing and a caption pass per clip, plus model calls. Five queries at three
clips each is roughly $2. That is why it is a separate script rather than part of
the recurring sweep.

    python qa/run_pipeline.py                  # all five task queries
    python qa/run_pipeline.py --query laundry  # one of them
    python qa/run_pipeline.py --per-query 1    # cheaper: one clip each
    python qa/run_pipeline.py --dry-run        # search and audit only, no collecting

Exit code is non-zero when the audit rejects a set, so this can gate a release.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

QUERIES = json.loads((ROOT / "qa" / "queries.json").read_text())["pipeline_queries"]
DEPLOYMENT = os.environ.get("QA_DEPLOYMENT", "https://internet2egoexo.vercel.app")


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


@dataclass
class QueryRun:
    """What one task query produced, all the way through."""

    query_id: str
    query: str
    candidates: int = 0
    collected: int = 0
    accepted: int = 0
    pending: int = 0
    anchors: int = 0
    annotations: int = 0
    batch_grade: str = "-"
    audit_verdict: str = "not run"
    audit_passed: bool = False
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    seconds: float = 0.0
    error: str = ""

    def line(self) -> str:
        if self.error:
            return f"  [ERROR] {self.query_id}: {self.error}"
        mark = "PASS" if self.audit_passed else "FAIL"
        return (
            f"  [{mark}] {self.query_id}: {self.candidates} found → "
            f"{self.accepted}/{self.collected} accepted"
            f"{f' ({self.pending} still indexing at collect time)' if self.pending else ''}"
            f" → {self.anchors} anchors, "
            f"{self.annotations} annotations → grade {self.batch_grade} → "
            f"{self.audit_verdict} ({self.seconds:.0f}s)"
        )


async def run_one(case: dict, per_query: int, dry_run: bool) -> QueryRun:
    from video_searching_agent.agent.quality_check_agent import QualityCheckAgent
    from video_searching_agent.curation.viewpoint import Viewpoint

    run = QueryRun(query_id=case["id"], query=case["query"])
    started = time.time()
    wanted = Viewpoint(case["viewpoint"]) if case.get("viewpoint") else None

    # ---- 1. search -----------------------------------------------------
    try:
        events = _sse(
            f"{DEPLOYMENT}/api/v1/queries/stream",
            {"query": case["query"], "viewpoint": case.get("viewpoint")},
            timeout=300,
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        run.error = f"search failed: {exc}"
        return run

    complete = next((p for e, p in events if e == "complete"), {})
    manifest = complete.get("dataset") or {}
    clips = manifest.get("clips") or []
    run.candidates = len(clips)
    urls = [c["url"] for c in clips if c.get("url")][:per_query]
    if not urls:
        run.error = "search returned no candidates to collect"
        return run
    if dry_run:
        run.audit_verdict = "skipped (dry run)"
        run.audit_passed = True
        run.seconds = time.time() - started
        return run

    # ---- 2. collect, one URL per request -------------------------------
    #
    # One request per clip on purpose. A serverless function has 300s, and a
    # twelve-minute video spends most of that being downloaded and indexed, so
    # two in one request means the stream is cut before the summary arrives —
    # which is how this run first reported "no clips returned" for work that had
    # in fact reached the Datalake. The per-clip events are the reliable record;
    # the final summary is a convenience that may never be sent.
    indexed_ids: list[str] = []
    outcomes: list[str] = []
    run.collected = len(urls)
    for url in urls:
        try:
            events = _sse(
                f"{DEPLOYMENT}/api/v1/collect/stream",
                {
                    "urls": [url],
                    "viewpoint": case.get("viewpoint"),
                    "require_hands": True,
                    "annotate": True,
                    # The search already looked at these frames.
                    "viewpoint_verified_urls": [url],
                },
                timeout=900,
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            outcomes.append(f"collect cut off: {exc}")
            continue

        last = {}
        for event, payload in events:
            if event in ("clip_stage", "clip_done"):
                last = payload.get("clip") or {}
        if last.get("video_id"):
            indexed_ids.append(str(last["video_id"]))
            if last.get("pending_reason"):
                run.pending += 1
        else:
            outcomes.append(
                str(
                    last.get("rejection_reason")
                    or last.get("error")
                    or f"stopped at {last.get('stage') or 'nothing streamed'}"
                )[:90]
            )

    if not indexed_ids:
        run.error = f"nothing reached the Datalake: {sorted(set(outcomes)) or ['no events']}"
        run.seconds = time.time() - started
        return run

    # ---- 3. curate: clean, annotate and grade what is indexed ----------
    curated: list[dict] = []
    claimed = None
    try:
        events = _sse(
            f"{DEPLOYMENT}/api/v1/curate/stream",
            {"video_ids": indexed_ids, "query": case["query"], "viewpoint": case.get("viewpoint")},
            timeout=900,
        )
        curation = next((p for e, p in events if e == "complete"), {})
        run.batch_grade = str(curation.get("batch_grade") or "-")
        claimed = (curation.get("hours") or {}).get("delivered_hours")
        curated = curation.get("clips") or []
    except (urllib.error.URLError, TimeoutError) as exc:
        run.error = f"curation failed: {exc}"
        run.seconds = time.time() - started
        return run

    delivered = []
    for clip in curated:
        cleaning = clip.get("cleaning") or {}
        annotation = clip.get("annotation") or {}
        anchors = cleaning.get("segments") or []
        labels = annotation.get("annotations") or []
        run.anchors += len(anchors)
        run.annotations += len(labels)
        delivered.append(
            {
                "video_id": clip.get("video_id"),
                "title": clip.get("uploader"),
                "url": clip.get("video_id"),
                "duration_seconds": clip.get("duration_seconds"),
                "viewpoint": (cleaning.get("frame_check") or {}).get("viewpoint"),
                "segments": anchors,
                "annotations": labels,
            }
        )
    run.accepted = sum(1 for clip in curated if clip.get("accepted"))

    # ---- 4. audit what came out ----------------------------------------
    agent = QualityCheckAgent()
    audit = await agent.audit(
        delivered,
        wanted_viewpoint=wanted,
        claimed_hours=claimed,
        verify_evidence=True,
    )
    run.audit_verdict = audit.verdict
    run.audit_passed = audit.passed
    run.failures = [
        f"{f.check} [{f.clip[:14]}]: {f.detail[:110]}"
        for f in audit.all_findings()
        if f.severity == "fail"
    ]
    run.warnings += [
        f"{f.check} [{f.clip[:14]}]: {f.detail[:110]}"
        for f in audit.all_findings()
        if f.severity == "warn"
    ]
    run.seconds = time.time() - started
    return run


async def main_async(args: argparse.Namespace) -> int:
    cases = QUERIES
    if args.query:
        cases = [c for c in QUERIES if c["id"] == args.query]
        if not cases:
            print(f"no such pipeline query: {args.query}")
            return 2

    print(f"whole-pipeline run {datetime.now(UTC):%Y-%m-%d %H:%M} UTC — {DEPLOYMENT}")
    print(f"{len(cases)} task queries, up to {args.per_query} clips each"
          f"{' (dry run)' if args.dry_run else ''}\n")

    runs: list[QueryRun] = []
    for case in cases:
        print(f"--- {case['id']}: {case['query']}", flush=True)
        run = await run_one(case, args.per_query, args.dry_run)
        runs.append(run)
        print(run.line(), flush=True)
        for failure in run.failures:
            print(f"        FAIL {failure}", flush=True)
        for warning in run.warnings[:4]:
            print(f"        warn {warning}", flush=True)

    print("\n" + "=" * 72)
    passed = sum(1 for r in runs if r.audit_passed and not r.error)
    errored = [r for r in runs if r.error]
    total_anchors = sum(r.anchors for r in runs)
    total_accepted = sum(r.accepted for r in runs)
    print(
        f"{passed} of {len(runs)} task queries produced a set the audit accepts; "
        f"{total_accepted} clips, {total_anchors} anchors"
    )
    for run in errored:
        print(f"  errored: {run.query_id} — {run.error}")
    for run in runs:
        if run.failures:
            print(f"  {run.query_id}: {len(run.failures)} failing checks")
    return 0 if passed == len(runs) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="run only this task query id")
    parser.add_argument(
        "--per-query", type=int, default=3, help="clips to collect per query (default 3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="search only, collecting nothing — free, and checks the candidates",
    )
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
