#!/usr/bin/env python3
"""Build the frozen eval query set from the robotics downstream task map.

The quality standard forbids inventing task names: the task layer of the
narration hierarchy has one controlled vocabulary, and it is the robotics
downstream task map. So the eval queries are not written — they are *drawn*,
from `eval/task_map.csv`, stratified by difficulty and spread across task
families, and frozen into `eval/queries.json`.

Freezing matters for the same reason the eval spec gives: a set that changes
between runs makes two scorecards incomparable. So this script is deterministic
— same task map, same size, same output, byte for byte — and the output carries
no timestamp, because a timestamp would make it churn.

    python eval/build_query_set.py                 # rebuild the frozen 200
    python eval/build_query_set.py --size 100      # the 100-query pilot
    python eval/build_query_set.py --check         # fail if the frozen set is stale

`--check` is the one to run in CI: it rebuilds in memory and diffs, so an edit
to the task map or to the sampling rules cannot quietly desynchronise the set
that every published scorecard cites.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from video_searching_agent.evaluation.task_map import (  # noqa: E402
    DIFFICULTY_MIX,
    filmable,
    imperative_verbs,
    load_task_map,
    sample,
    suspect_gerunds,
)

EVAL_VERSION = "v1.1"
DEFAULT_SIZE = 200
# v1.0 lives at eval/queries.json and is FROZEN: every published scorecard
# cites it, and the filter has since been tightened, so it can no longer be
# rebuilt byte-for-byte. Each version gets its own file rather than overwriting
# the last, so an old run record stays interpretable against the set it used.

QUERIES_PATH = ROOT / "eval" / f"queries-{EVAL_VERSION}.json"
TASK_MAP_PATH = ROOT / "eval" / "task_map.csv"

SOURCE = {
    "name": "Robotics downstream task map — controlled vocabulary",
    "owner": "Yunze Liu",
    "notion": "First-Person Data Quality Standard & Acceptance Criteria v1.0, §11 item 6",
    "sheet": "https://docs.google.com/spreadsheets/d/1mRYvC6fnVCoICTwl6JXVXkYfJ5tHoJgO/edit",
    "retrieved": "2026-08-22",
    "rows": 1965,
    "local_copy": "eval/task_map.csv",
}

NOTE = (
    "Eval queries drawn from the robotics downstream task map, not written by "
    "hand: the quality standard's G2-HIER gate requires task names to come from "
    "that vocabulary. Each query is one canonical task, phrased the way somebody "
    "looking for footage of it would phrase it; `task_instruction` keeps the "
    "canonical wording verbatim so the RDT id stays traceable. Regenerate with "
    "`python eval/build_query_set.py`."
)


def build(size: int) -> dict[str, object]:
    """Draw the set and wrap it with the accounting for how it was drawn."""
    every = load_task_map(TASK_MAP_PATH)
    usable, dropped = filmable(every)
    selection = sample(usable, size)
    flagged = suspect_gerunds(selection.tasks, imperative_verbs(every))

    return {
        "eval_version": EVAL_VERSION,
        "note": NOTE,
        "source": SOURCE,
        "sampling": {
            "size": size,
            "difficulty_mix": DIFFICULTY_MIX,
            "difficulty": dict(sorted(selection.per_difficulty.items())),
            "task_families": len(selection.per_family),
            "per_family": dict(sorted(selection.per_family.items())),
            "shortfall": selection.shortfall,
            "review": flagged,
            "pool": {
                "rows_in_task_map": len(every),
                "filmable_by_a_person": len(usable),
                "dropped": dict(sorted(dropped.items(), key=lambda kv: (-kv[1], kv[0]))),
            },
        },
        "queries": [task.as_dict() for task in selection.tasks],
    }


def serialise(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="queries to draw")
    parser.add_argument("--out", type=Path, default=QUERIES_PATH, help="where to write")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit non-zero if the file on disk is not what this builds",
    )
    args = parser.parse_args()

    text = serialise(build(args.size))

    if args.check:
        if not args.out.exists():
            print(f"{args.out} does not exist")
            return 1
        if args.out.read_text(encoding="utf-8") != text:
            print(f"{args.out} is stale — run: python eval/build_query_set.py")
            return 1
        print(f"{args.out} is up to date")
        return 0

    args.out.write_text(text, encoding="utf-8")
    payload = json.loads(text)
    sampling = payload["sampling"]
    print(f"wrote {args.out} — {len(payload['queries'])} queries, {EVAL_VERSION}")
    print(f"  difficulty: {sampling['difficulty']}")
    print(f"  families:   {sampling['task_families']}")
    print(
        f"  pool:       {sampling['pool']['filmable_by_a_person']} filmable "
        f"of {sampling['pool']['rows_in_task_map']} canonical tasks"
    )
    if sampling["review"]:
        print(f"  review:     {len(sampling['review'])} queries built from a non-verb head")
        for rdt_id, query in sampling["review"].items():
            print(f"                {rdt_id}: {query}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
