#!/usr/bin/env python3
"""Run the eval and publish the report — the recurring job.

Every eight hours, against whatever is deployed:

    run the core slice → score it → append the history →
    write the dated report → rewrite the README's metrics block →
    commit and push to main

Three decisions are baked in here, and each of them is a trade somebody could
reasonably want made differently.

**A fixed slice, not the whole set.** The full 200 queries take hours and cost
$60-120. Three times a day is $180-360 a day, which nobody is going to sign off
on to watch a number move. So the recurring run uses the `core` slice — 12
queries marked in `eval/queries.json`, stratified across difficulty and family
— for about $6 a tick. *Fixed*, not rotating: a trend line over a changing slice
measures the slice.

**The report is committed.** A trend that lives in a build artifact is a trend
nobody looks at. `eval/history.jsonl` is append-only and is the record;
`eval/reports/` keeps every dated report; `eval/REPORT.md` is the latest; and
the README carries the headline between its markers so it is the first thing
visible in the repository.

**It pushes to `main`.** Report commits only — `eval/history.jsonl`,
`eval/reports/`, `eval/REPORT.md`, `README.md`. It refuses to run on a dirty
tree or a branch that is behind, because a report that quietly includes somebody
else's uncommitted work is worse than no report.

    python eval/publish.py --yes                    # the recurring job
    python eval/publish.py --yes --no-push          # everything but the push
    python eval/publish.py --from eval/results/run-3.jsonl   # publish a finished run, free
    python eval/publish.py --slice all --yes        # the full 200; hours, and $60-120

Exit code is non-zero when the run could not be published — not when the numbers
are bad. A bad number is the point.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from video_searching_agent.evaluation.metrics import (  # noqa: E402
    QueryOutcome,
    outcome_as_dict,
    outcome_from_dict,
    score_run,
)
from video_searching_agent.evaluation.report import (  # noqa: E402
    append_history,
    load_history,
    render_readme_block,
    render_report,
    snapshot_of,
    update_readme,
)
from video_searching_agent.evaluation.runner import health, run_query  # noqa: E402

QUERIES_PATH = ROOT / "eval" / "queries.json"
HISTORY_PATH = ROOT / "eval" / "history.jsonl"
REPORTS_DIR = ROOT / "eval" / "reports"
LATEST_PATH = ROOT / "eval" / "REPORT.md"
README_PATH = ROOT / "README.md"
RESULTS_DIR = ROOT / "eval" / "results"
DEPLOYMENT = os.environ.get("QA_DEPLOYMENT", "https://internet-egoexo-video-search.vercel.app")

PUBLISHED = ("eval/history.jsonl", "eval/reports", "eval/REPORT.md", "README.md")


def git(*args: str, check: bool = True) -> str:
    """Run git in the repository and return its stdout."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def ready_to_publish(branch: str) -> str | None:
    """Why publishing would be unsafe right now, or None if it is fine."""
    dirty = [
        line
        for line in git("status", "--porcelain").splitlines()
        if line and not line[3:].startswith(PUBLISHED)
    ]
    if dirty:
        return f"the working tree has changes outside the report files: {dirty[:3]}"
    current = git("rev-parse", "--abbrev-ref", "HEAD")
    if current != branch:
        return f"on branch {current}, not {branch}"
    git("fetch", "origin", branch)
    behind = git("rev-list", "--count", f"HEAD..origin/{branch}")
    if behind != "0":
        return f"{behind} commit(s) behind origin/{branch} — pull before publishing"
    return None


def run_slice(cases: list[dict], per_query: int, dry_run: bool) -> list[QueryOutcome]:
    """Run every query in the slice, printing as it goes."""
    outcomes: list[QueryOutcome] = []
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    record = RESULTS_DIR / f"publish-{stamp}.jsonl"
    with record.open("a", encoding="utf-8") as handle:
        for index, case in enumerate(cases, start=1):
            print(f"--- [{index}/{len(cases)}] {case['id']}: {case['query']}", flush=True)
            outcome = run_query(
                case, deployment=DEPLOYMENT, per_query=per_query, dry_run=dry_run
            )
            handle.write(json.dumps(outcome_as_dict(outcome), ensure_ascii=False) + "\n")
            handle.flush()
            outcomes.append(outcome)
            print(
                f"    {outcome.candidates} found → {outcome.indexed}/{outcome.attempted} "
                f"indexed → {outcome.accepted}/{outcome.graded} accepted"
                f"{f' — {outcome.error}' if outcome.error else ''}",
                flush=True,
            )
    print(f"\nrun record: {record}")
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slice", default="core", choices=["core", "all"], help="which queries to run"
    )
    parser.add_argument("--per-query", type=int, default=1, help="clips per query (default 1)")
    parser.add_argument(
        "--from",
        dest="record",
        type=Path,
        help="publish a finished run's .jsonl instead of running anything",
    )
    parser.add_argument("--dry-run", action="store_true", help="search only; spends little")
    parser.add_argument("--no-push", action="store_true", help="commit but do not push")
    parser.add_argument("--no-commit", action="store_true", help="write the files only")
    parser.add_argument("--branch", default="main", help="branch to publish to")
    parser.add_argument("--yes", action="store_true", help="do not ask before spending")
    args = parser.parse_args()

    payload = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    version = payload.get("eval_version", "")

    publishing = not (args.no_commit and args.no_push)
    if publishing:
        blocker = ready_to_publish(args.branch)
        if blocker:
            print(f"refusing to publish: {blocker}")
            return 2

    commit = git("rev-parse", "HEAD", check=False)
    build = health(DEPLOYMENT)
    if not build:
        print(f"warning: {DEPLOYMENT} did not answer /health — the report will not say "
              "which build it measured")

    # --- get the outcomes ------------------------------------------------
    if args.record:
        outcomes = [
            outcome_from_dict(json.loads(line))
            for line in args.record.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        slice_name = f"replayed:{args.record.name}"
    else:
        cases = payload["queries"]
        if args.slice == "core":
            cases = [case for case in cases if case.get("core")]
        estimate = 0.05 * len(cases) + (
            0 if args.dry_run else len(cases) * args.per_query * 0.47
        )
        print(f"{DEPLOYMENT} — {args.slice} slice, {len(cases)} queries, "
              f"{args.per_query} clip(s) each, ~${estimate:.2f}")
        if estimate > 1 and not args.yes:
            print("re-run with --yes to spend it")
            return 3
        outcomes = run_slice(cases, args.per_query, args.dry_run)
        slice_name = args.slice + (" (dry)" if args.dry_run else "")

    if not outcomes:
        print("nothing ran; nothing to publish")
        return 1

    # --- score, record, render -------------------------------------------
    card = score_run(outcomes, eval_version=version)
    snapshot = snapshot_of(
        card,
        slice_name=slice_name,
        commit=commit,
        deployment=DEPLOYMENT,
        build=build,
    )
    append_history(HISTORY_PATH, snapshot)
    history = load_history(HISTORY_PATH)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = render_report(card, snapshot, history)
    dated = REPORTS_DIR / f"{snapshot.ran_at.replace(':', '').replace('-', '')}.md"
    dated.write_text(report, encoding="utf-8")
    LATEST_PATH.write_text(report, encoding="utf-8")
    README_PATH.write_text(
        update_readme(README_PATH.read_text(encoding="utf-8"), render_readme_block(history)),
        encoding="utf-8",
    )

    print(
        f"\n{snapshot.graded} clips graded, {snapshot.accepted} accepted "
        f"({100 * snapshot.acceptance_rate:.0f}%), {snapshot.high_quality} A-or-B, "
        f"${snapshot.total_usd:.2f} spent"
    )
    print(f"report: {dated}")

    # --- publish ----------------------------------------------------------
    if args.no_commit:
        print("not committing (--no-commit)")
        return 0

    git("add", *PUBLISHED)
    if not git("status", "--porcelain", "--", *PUBLISHED):
        print("nothing changed; not committing")
        return 0
    subject = (
        f"report(eval): {snapshot.accepted}/{snapshot.graded} accepted, "
        f"{snapshot.high_quality} A-or-B, ${snapshot.total_usd:.2f} — {snapshot.ran_at}"
    )
    body = (
        f"Recurring eval, {slice_name} slice, {snapshot.queries} queries against "
        f"{DEPLOYMENT}.\n\n"
        f"Accepted {snapshot.accepted}/{snapshot.graded}, A-or-B {snapshot.high_quality}, "
        f"usable {snapshot.usable_hours:.2f}h of {snapshot.delivered_hours:.2f}h delivered, "
        f"{snapshot.action_anchors} anchors, ${snapshot.total_usd:.2f}.\n"
        f"Build: {build or 'unknown'}.\n\n"
        "A 12-clip slice cannot resolve a small change on its own; the report's\n"
        "interval and rolling window are the numbers to read."
    )
    git("commit", "-m", subject, "-m", body)
    print(f"committed: {subject}")

    if args.no_push:
        print("not pushing (--no-push)")
        return 0
    for attempt in range(4):
        result = subprocess.run(
            ["git", "-C", str(ROOT), "push", "-u", "origin", args.branch],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"pushed to origin/{args.branch}")
            return 0
        print(f"push failed (attempt {attempt + 1}): {result.stderr.strip()[:200]}")
        if attempt < 3:
            subprocess.run(["sleep", str(2 ** (attempt + 1))], check=False)
    return 4


if __name__ == "__main__":
    sys.exit(main())
