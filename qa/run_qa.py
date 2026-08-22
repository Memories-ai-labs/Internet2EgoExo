#!/usr/bin/env python3
"""Run the whole process and report what is broken.

Four phases, cheapest first, so a failure is found before money is spent:

1. **offline** — the test suite and the labelled validation set
   (`tests/validation/`). Free, and it is where a judgement regression shows up.
2. **structural** — the whole UI-facing path against a local instance in demo
   mode: health, search, collect (every stage), curate. Free, and it catches
   contract and shape breakage.
3. **live** — the deployment: health and tool health, then one of the ten
   example queries (`qa/queries.json`), rotating by clock so the set is covered
   across the day rather than all at once.
4. **judgement** — a real curation pass on an already-indexed video, which
   exercises the Datalake reads and the gates against real captions.

Costs are deliberate. Phase 3 spends model and scraper credits for one query;
phase 4 spends about a tenth of a cent. `--full` runs all ten queries, and
`--offline` stops after phase 2 and spends nothing.

    python qa/run_qa.py                    # the half-hourly sweep
    python qa/run_qa.py --full             # all ten queries
    python qa/run_qa.py --offline          # free

Exit code is non-zero when anything failed, so a scheduler can act on it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERIES = json.loads((ROOT / "qa" / "queries.json").read_text())["queries"]
DEPLOYMENT = os.environ.get("QA_DEPLOYMENT", "https://internet-egoexo-video-search.vercel.app")
# An indexed video with real captions, for the judgement phase.
JUDGEMENT_VIDEO = os.environ.get("QA_VIDEO_ID", "vid_5btyh22t6knevmlcks2ufonn5q")
JUDGEMENT_COLLECTION = os.environ.get("QA_COLLECTION", "col_bngey4z7vxpqyimcogrolfnw5i")
LOCAL_PORT = int(os.environ.get("QA_LOCAL_PORT", "8899"))


_HOURS = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:hours?|hrs?)\b", re.IGNORECASE)
# Words that make an hour figure a claim about what THIS run produced, rather
# than a fact quoted about somebody else's published dataset.
_YIELD_CUES = (
    "collected",
    "delivered",
    "accepted",
    "curated",
    "ingested",
    "gathered",
    "assembled",
    "we found",
    "i found",
    "this run",
    "these clips",
    "the clips below",
)


def hour_claims(answer: str) -> list[str]:
    """Every hour figure the answer states, with the line it sits on."""

    found: list[str] = []
    for line in answer.splitlines():
        found.extend(match.group(0).strip() for match in _HOURS.finditer(line))
    return found


def own_yield_claims(answer: str) -> list[str]:
    """Hour figures the answer presents as this run's own output.

    A literature answer may legitimately say Ego4D is 3,670 hours. What it may
    never do is say that the run collected, delivered or accepted hours that
    were never measured, so the cue is the verb, not the number.
    """

    found: list[str] = []
    for line in answer.splitlines():
        lowered = line.lower()
        if not any(cue in lowered for cue in _YIELD_CUES):
            continue
        found.extend(match.group(0).strip() for match in _HOURS.finditer(line))
    return found


# Every expectation key the runner knows how to check. An unknown key is a
# failure rather than a shrug: an expectation that silently does nothing is
# worse than no expectation, because the report reads as if it were checked.
KNOWN_EXPECTATIONS = frozenset(
    {
        "min_clips",
        "quotes_published_hours",
        "max_clips",
        "viewpoint_present",
        "all_reusable",
        "only_platforms",
        "reports_target",
        "tools_used",
    }
)


@dataclass
class Result:
    """One check, and what it found."""

    phase: str
    name: str
    passed: bool
    detail: str = ""
    skipped: bool = False


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)

    def add(self, phase: str, name: str, passed: bool, detail: str = "") -> bool:
        self.results.append(Result(phase, name, passed, detail))
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""), flush=True)
        return passed

    def skip(self, phase: str, name: str, why: str) -> None:
        self.results.append(Result(phase, name, True, why, skipped=True))
        print(f"  [skip] {name} — {why}", flush=True)

    @property
    def failures(self) -> list[Result]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.passed and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        lines = [f"checks: {passed} passed, {len(self.failures)} failed, {skipped} skipped"]
        for failure in self.failures:
            lines.append(f"  FAIL {failure.phase}/{failure.name}: {failure.detail}")
        return "\n".join(lines)


# ------------------------------------------------------------------ helpers


def _sse(url: str, body: dict, timeout: float = 90.0, headers: dict | None = None):
    """POST and parse the SSE frames that come back."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    events: list[tuple[str, dict]] = []
    with urllib.request.urlopen(request, timeout=timeout) as response:
        buffer = ""
        for chunk in response:
            buffer += chunk.decode("utf-8", "replace")
            while True:
                for separator in ("\r\n\r\n", "\n\n"):
                    if separator in buffer:
                        frame, buffer = buffer.split(separator, 1)
                        break
                else:
                    break
                name = None
                data: list[str] = []
                for line in frame.replace("\r\n", "\n").split("\n"):
                    if line.startswith("event:"):
                        name = line[6:].strip()
                    elif line.startswith("data:"):
                        data.append(line[5:].strip())
                if name and data:
                    try:
                        events.append((name, json.loads("\n".join(data))))
                    except json.JSONDecodeError:
                        pass
    return events


def _get(url: str, timeout: float = 30.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())


def _final(events: list[tuple[str, dict]], name: str) -> dict | None:
    for event, payload in reversed(events):
        if event == name:
            return payload
    return None


# ------------------------------------------------------------------- phases


def phase_offline(report: Report) -> None:
    print("\n1. offline — suite and validation set")
    env = {**os.environ, "TESTING": "true"}
    env.setdefault("GOOGLE_API_KEY", "qa")
    env.setdefault("YOUTUBE_API_KEY", "qa")

    suite = subprocess.run(
        ["uv", "run", "pytest", "-q", "--no-header"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    tail = (suite.stdout or suite.stderr).strip().splitlines()[-1:] or [""]
    report.add("offline", "test suite", suite.returncode == 0, tail[0][:160])

    validation = subprocess.run(
        ["uv", "run", "pytest", "-q", "--no-header", "tests/test_validation_set.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    tail = (validation.stdout or validation.stderr).strip().splitlines()[-1:] or [""]
    report.add("offline", "validation set", validation.returncode == 0, tail[0][:160])

    lint = subprocess.run(
        ["uv", "run", "ruff", "check", "src", "tests", "qa"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    report.add("offline", "lint", lint.returncode == 0, (lint.stdout or "").strip()[:160])


def phase_structural(report: Report) -> None:
    """The whole path against a local demo-mode instance: free, and it catches shapes."""
    print("\n2. structural — the whole path locally, in demo mode")
    env = {**os.environ, "DEMO_MODE": "1", "TESTING": "true", "RATE_LIMIT_ENABLED": "false"}
    server = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-m",
            "uvicorn",
            "video_searching_agent.web.main:app",
            "--port",
            str(LOCAL_PORT),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{LOCAL_PORT}"
    try:
        for _ in range(40):
            try:
                _get(f"{base}/api/v1/health", timeout=3)
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        else:
            report.add("structural", "local server starts", False, "never answered")
            return

        health = _get(f"{base}/api/v1/health")
        report.add("structural", "local server starts", health.get("demo_mode") is True)
        report.add(
            "structural",
            "health names the cap, the auth and the look",
            {"max_collect_urls", "auth_required", "viewpoint_check"} <= set(health),
            f"cap={health.get('max_collect_urls')} auth={health.get('auth_required')} "
            f"look={health.get('viewpoint_check')}",
        )

        ui = urllib.request.urlopen(f"{base}/ui/", timeout=10).read().decode()
        report.add("structural", "UI is served", '<div id="root">' in ui)

        events = _sse(f"{base}/api/v1/queries/stream", {"query": "first-person cooking"})
        complete = _final(events, "complete")
        report.add("structural", "search stream completes", complete is not None)
        if complete:
            manifest = complete.get("dataset") or {}
            hours = manifest.get("hours") or {}
            report.add(
                "structural",
                "manifest keeps the hour measures apart",
                {"delivered_hours", "accepted_hours", "accepted_labeled_hours"} <= set(hours),
            )
            report.add(
                "structural",
                "clips carry an annotation tree",
                any(clip.get("annotations") for clip in manifest.get("clips", [])),
            )

        events = _sse(
            f"{base}/api/v1/collect/stream",
            {"urls": ["https://youtube.com/watch?v=a", "https://youtube.com/watch?v=b"]},
            timeout=120,
        )
        stages = {payload["clip"]["stage"] for event, payload in events if event == "clip_stage"}
        report.add(
            "structural",
            "collect streams every stage",
            {"probing", "looking", "downloading", "uploading", "indexing", "cleaning"} <= stages,
            f"{len(stages)} distinct stages",
        )
        collect = _final(events, "complete")
        if collect:
            rejected = collect.get("rejected") or []
            report.add(
                "structural",
                "a hands-free clip is dropped with a reason",
                bool(rejected) and bool(rejected[0].get("rejection_reason")),
                rejected[0].get("rejection_reason", "") if rejected else "none rejected",
            )

        events = _sse(f"{base}/api/v1/curate/stream", {"tag": "clean_pass"}, timeout=120)
        curation = _final(events, "complete")
        report.add("structural", "curate stream completes", curation is not None)
        if curation:
            dup = next((c for c in curation.get("dataset_checks", []) if c["id"] == "G3-DUP"), None)
            report.add(
                "structural",
                "G3-DUP still reports unmeasured",
                bool(dup) and dup.get("measured") is False,
            )
    finally:
        server.terminate()
        server.wait(timeout=10)


# The example queries are the only part of the sweep that spends YouTube quota,
# and they spend it fast: search.list costs 100 units of a 10,000/day allowance,
# and one query fires about two searches. Run at every sweep that is 9,600 units
# a day — 96% of the allowance, leaving roughly four searches for the people
# actually using the deployment, which is exactly how a user came to see nothing
# but TikTok. So the query runs every fourth hour rather than every sweep: still
# six real runs a day, still rotating through all ten, and 88% of the quota left
# for its intended purpose.
LIVE_QUERY_EVERY_N_HOURS = 4


def _should_run_example_query(now: datetime) -> bool:
    """Whether this sweep is one of the six a day that spends search quota."""

    return now.hour % LIVE_QUERY_EVERY_N_HOURS == 0 and now.minute < 30


def phase_live(
    report: Report, full: bool, only: str | None = None, light: bool = False
) -> None:
    print(f"\n3. live — {DEPLOYMENT}")
    try:
        health = _get(f"{DEPLOYMENT}/api/v1/health")
    except Exception as exc:  # noqa: BLE001 - any failure here is the finding
        report.add("live", "deployment answers", False, str(exc)[:140])
        return

    report.add("live", "deployment answers", health.get("status") == "healthy")
    tools = health.get("tools", {})
    unhealthy = [
        name for name, info in (tools.get("details") or {}).items() if not info.get("healthy")
    ]
    report.add(
        "live",
        "every tool is configured",
        not unhealthy,
        f"down: {', '.join(unhealthy)}" if unhealthy else f"{tools.get('healthy')} healthy",
    )
    if health.get("demo_mode"):
        report.skip("live", "example queries", "deployment is in demo mode")
        return

    if light or not (full or only or _should_run_example_query(datetime.now(UTC))):
        report.skip(
            "live",
            "example query",
            "skipped to leave YouTube search quota for real users; "
            f"runs every {LIVE_QUERY_EVERY_N_HOURS}h",
        )
        return

    # Rotate through the ten so the whole set is covered across a day.
    if only:
        chosen = [case for case in QUERIES if case["id"] == only]
        if not chosen:
            report.add("live", f"query {only} exists", False, "no such query id")
            return
    elif full:
        chosen = QUERIES
    else:
        chosen = [QUERIES[int(time.time() // 1800) % len(QUERIES)]]
    for case in chosen:
        unknown = set(case.get("expect") or {}) - KNOWN_EXPECTATIONS
        if unknown:
            report.add(
                "live",
                f"query {case['id']} expectations are checkable",
                False,
                f"the runner ignores {sorted(unknown)}",
            )
        body = {
            key: case[key]
            for key in (
                "query",
                "viewpoint",
                "min_duration_seconds",
                "license_filter",
                "target_hours",
                "sources",
            )
            if key in case
        }
        label = f"query {case['id']}"
        try:
            events = _sse(f"{DEPLOYMENT}/api/v1/queries/stream", body, timeout=120)
        except Exception as exc:  # noqa: BLE001
            report.add("live", label, False, str(exc)[:140])
            continue

        complete = _final(events, "complete")
        if not complete:
            errors = [p.get("message") for e, p in events if e == "error"]
            report.add("live", label, False, f"no completion; errors={errors}")
            continue

        manifest = complete.get("dataset") or {}
        clips = manifest.get("clips") or []
        expect = case.get("expect") or {}
        problems = []

        if len(clips) < expect.get("min_clips", 0):
            problems.append(f"{len(clips)} clips, wanted >={expect['min_clips']}")
        if expect.get("viewpoint_present") and not any(
            c.get("viewpoint") == expect["viewpoint_present"] for c in clips
        ):
            problems.append(f"no {expect['viewpoint_present']} clip")
        if expect.get("all_reusable") and clips:
            if manifest.get("reusable_license_clips", 0) != len(clips):
                problems.append("licence filter let a non-reusable clip through")
        if expect.get("only_platforms"):
            extra = set(manifest.get("by_platform") or {}) - set(expect["only_platforms"])
            if extra:
                problems.append(f"unpinned sources: {sorted(extra)}")
        if expect.get("max_clips") is not None and len(clips) > expect["max_clips"]:
            problems.append(f"{len(clips)} clips, wanted <={expect['max_clips']}")
        if expect.get("reports_target") and not manifest.get("target_hours"):
            problems.append("target hours not reported")
        for tool in expect.get("tools_used", []):
            if not any(
                event == "tool_result" and payload.get("tool") == tool and payload.get("success")
                for event, payload in events
            ):
                problems.append(f"{tool} was never used successfully")

        # Invariants that hold for every query, whatever it asked for.
        floor = body.get("min_duration_seconds")
        if floor:
            short = [
                c for c in clips if c.get("duration_seconds") and c["duration_seconds"] < floor
            ]
            if short:
                problems.append(f"{len(short)} kept clips are shorter than the {floor}s minimum")
        if manifest.get("excluded_clips") and not manifest.get("exclusion_reasons"):
            problems.append("clips were excluded without a reason")
        for clip in clips:
            if clip.get("viewpoint") not in ("egocentric", "exocentric", "unknown"):
                problems.append(f"clip has an unknown viewpoint value: {clip.get('viewpoint')}")
                break

        # The rule that matters most: the answer may not invent quantities.
        # By default any hour figure in an answer with no measured hours is a
        # defect. A query that asks about published datasets declares
        # quotes_published_hours, and is then held to the narrower rule that
        # matters there: it may quote a dataset's size, with a source, but it
        # still may not claim hours of its own.
        answer_text = complete.get("answer") or ""
        if expect.get("quotes_published_hours"):
            claimed = own_yield_claims(answer_text)
            if claimed and not manifest.get("total_hours"):
                problems.append(f"answer claims {claimed} of its own with none measured")
            if hour_claims(answer_text) and "http" not in answer_text:
                problems.append("answer quotes hours without citing a single source")
        elif hour_claims(answer_text) and not manifest.get("total_hours"):
            problems.append(f"answer states {hour_claims(answer_text)} but the manifest has none")

        # A tool that failed outright is a finding, not a footnote. This ran as
        # a detail string for a while, which is how "every result is TikTok
        # because YouTube was rate limited" reached a user before it reached
        # the report.
        failed_tools = [
            p.get("tool") for e, p in events if e == "tool_result" and not p.get("success")
        ]
        if failed_tools:
            problems.append(f"tools failed: {sorted(set(failed_tools))}")
        detail = f"{len(clips)} clips, {manifest.get('total_hours')}h"
        if failed_tools:
            detail += f", tool failures: {sorted(set(failed_tools))}"
        report.add("live", label, not problems, "; ".join(problems) or detail)


def check_live_collect(report: Report) -> None:
    """Send one real URL through the deployment's ingest path.

    Phase 2 exercises collect in demo mode, which is why the hosted backend
    could report sixteen healthy tools while being unable to download anything:
    ``./downloads`` is read-only on a serverless host, so every real fetch died
    with ``[Errno 30]`` and no check ever saw it.

    What is asserted is narrow on purpose. A candidate the agent *judges*
    unusable is a pass — that is the pipeline working. What fails the sweep is
    the pipeline being unable to try: a read-only filesystem, a missing
    credential, a timeout with nothing streamed.
    """
    # A 30-second clip. Long enough to be real, short enough that the Datalake
    # bill for running this every half hour is rounding error.
    body = {
        "urls": [os.environ.get("QA_COLLECT_URL", "https://www.youtube.com/watch?v=XWgeWBdh1pY")],
        "min_duration_seconds": 10,
    }
    try:
        events = _sse(f"{DEPLOYMENT}/api/v1/collect/stream", body, timeout=300)
    except Exception as exc:  # noqa: BLE001
        report.add("live", "collect reaches the download on the deployment", False, str(exc)[:160])
        return

    stages = [p.get("clip", {}).get("stage") for e, p in events if e == "clip_stage"]
    clips = [p.get("clip", {}) for e, p in events if e == "clip_stage"]
    errors = [c.get("error") for c in clips if c.get("error")]

    # An infrastructure failure names the machine, not the footage.
    markers = ("Read-only file system", "No space left", "not configured", "Permission denied")
    infra = [err for err in errors if any(marker in str(err) for marker in markers)]
    report.add(
        "live",
        "collect reaches the download on the deployment",
        bool(stages) and not infra,
        f"stages={stages} infra_errors={infra}" if infra or not stages else f"stages={stages}",
    )


def phase_judgement(report: Report) -> None:
    """A real curation pass: real captions, real gates."""
    print("\n4. judgement — a real curation pass on indexed footage")
    keys = {
        "X-Memories-Key": os.environ.get("MEMORIES_API_KEY", ""),
        "X-OpenRouter-Key": os.environ.get("OPENROUTER_API_KEY", ""),
        "X-Memories-Collection": JUDGEMENT_COLLECTION,
    }
    if not keys["X-Memories-Key"]:
        report.skip("judgement", "real curation pass", "no MEMORIES_API_KEY in the environment")
        return

    try:
        events = _sse(
            f"{DEPLOYMENT}/api/v1/curate/stream",
            {"video_ids": [JUDGEMENT_VIDEO], "annotate": False},
            timeout=150,
            headers={k: v for k, v in keys.items() if v},
        )
    except Exception as exc:  # noqa: BLE001
        report.add("judgement", "real curation pass", False, str(exc)[:140])
        return

    clip = _final(events, "clip_done")
    complete = _final(events, "complete")
    report.add("judgement", "curation returns a verdict", clip is not None and complete is not None)
    if not clip:
        return

    verdict = clip.get("clip") or clip
    # This video is a pot rotating on a turntable: no hands, so it must be dropped.
    reason = (verdict.get("rejection_reason") or "").lower()
    report.add(
        "judgement",
        "the no-hands clip is still rejected",
        verdict.get("accepted") is False and "hand" in reason,
        reason or "accepted",
    )
    if complete:
        hours = complete.get("hours") or {}
        report.add(
            "judgement",
            "accepted hours never exceed delivered",
            hours.get("accepted_hours", 0) <= hours.get("delivered_hours", 0) + 1e-9,
            json.dumps(hours),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="run all ten example queries")
    parser.add_argument("--offline", action="store_true", help="phases 1-2 only; spends nothing")
    parser.add_argument("--query", help="run only this example query id, to re-check one failure")
    parser.add_argument(
        "--light",
        action="store_true",
        help="skip the example query; everything else, including the real "
        "collect against the deployment, still runs",
    )
    args = parser.parse_args()

    started = datetime.now(UTC)
    print(f"QA sweep {started:%Y-%m-%d %H:%M} UTC — {DEPLOYMENT}")
    report = Report()

    phase_offline(report)
    phase_structural(report)
    if not args.offline:
        phase_live(report, full=args.full, only=args.query, light=args.light)
        check_live_collect(report)
        phase_judgement(report)

    print("\n" + report.summary())
    elapsed = (datetime.now(UTC) - started).total_seconds()
    print(f"took {elapsed:.0f}s")
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main())
