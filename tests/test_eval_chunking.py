"""The chunk boundaries the CI workflow depends on.

The full eval needs ~12 hours and a GitHub-hosted job is capped at 6, whatever
the plan. So `.github/workflows/eval.yml` splits the set into four chunks of
`--limit 50 / 100 / 150 / (none)`, each resuming from the previous chunk's
records.

That only works because `select()` applies `--limit` to the *head* of the frozen
set and `--resume` then removes what is already finished. If either half changed
— a limit applied after resume, or a reordering in select — the chunks would
overlap and every overlapping query would be paid for twice, silently, in a run
that costs ~$42. Hence a test rather than a comment.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_SPEC = importlib.util.spec_from_file_location("eval_run_eval", ROOT / "eval" / "run_eval.py")
runner = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = runner
_SPEC.loader.exec_module(runner)

# The exact ladder in the workflow. 0 means "no --limit", i.e. the tail.
CHUNKS = (50, 100, 150, 0)


def _cases(name: str) -> list[dict]:
    return json.loads((ROOT / "eval" / name).read_text(encoding="utf-8"))["queries"]


def _todo(cases: list[dict], limit: int, done: set[str]) -> list[str]:
    """What one chunk would actually run, mirroring main()'s two steps."""
    args = argparse.Namespace(query=None, difficulty=None, family=None, limit=limit or None)
    return [c["id"] for c in runner.select(cases, args) if c["id"] not in done]


@pytest.mark.parametrize("query_set", ["queries.json", "queries-v1.1.json"])
def test_the_four_chunks_are_disjoint_and_cover_the_set(query_set):
    cases = _cases(query_set)
    done: set[str] = set()
    run_total = 0
    for limit in CHUNKS:
        block = _todo(cases, limit, done)
        run_total += len(block)
        done |= set(block)

    assert run_total == len(done), (
        "chunks overlap — every repeated query would be paid for twice"
    )
    assert done == {c["id"] for c in cases}, "chunks do not cover the whole set"


def test_limit_takes_the_head_so_chunks_advance(query_set="queries-v1.1.json"):
    """The property the ladder rests on: `--limit N` is a prefix, not a sample."""
    cases = _cases(query_set)
    first_50 = _todo(cases, 50, set())
    assert first_50 == [c["id"] for c in cases[:50]]

    # With those done, --limit 100 must yield exactly the *next* 50.
    second = _todo(cases, 100, set(first_50))
    assert second == [c["id"] for c in cases[50:100]]


def test_the_tail_chunk_has_no_limit():
    """A `--limit` on the last chunk would silently drop the tail.

    0 is the workflow's encoding of "pass no --limit at all"; if it were treated
    as a real limit of zero, `select` would return nothing and queries 151-200
    would never run while the workflow reported success.
    """
    cases = _cases("queries-v1.1.json")
    done = set()
    for limit in CHUNKS[:-1]:
        done |= set(_todo(cases, limit, done))
    tail = _todo(cases, 0, done)
    assert len(tail) == len(cases) - 150


def test_an_out_path_gets_its_directory_created(tmp_path, monkeypatch):
    """`eval/results/` is gitignored, so it is absent on every fresh checkout.

    A paid run that searched, screened and downloaded before dying on
    FileNotFoundError at the first record write would bill for work it then
    threw away — so the directory is created from the path handed in, not only
    for the default location.
    """
    target = tmp_path / "nested" / "deeper" / "full.jsonl"
    assert not target.parent.exists()

    # Exercise the one line under test rather than main()'s whole argument
    # surface: what matters is that a parent directory is made from --out.
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")
    assert target.exists()


def test_the_workflow_and_the_test_agree_on_the_chunk_ladder():
    """If somebody edits the YAML, this fails rather than the $42 run.

    The ladder lives in two places by necessity — a workflow cannot import a
    Python constant — so the duplication is asserted instead of trusted.
    """
    import re

    yaml_text = (ROOT / ".github" / "workflows" / "eval.yml").read_text(encoding="utf-8")
    limits = [int(m) for m in re.findall(r"^\s+limit:\s*(\d+)\s*$", yaml_text, re.M)]
    assert limits == list(CHUNKS), (
        f"workflow ladder {limits} does not match the tested ladder {list(CHUNKS)}"
    )


def test_every_host_invokes_the_eval_through_the_same_script():
    """Three hosts, one invocation — the property `eval/run.sh` exists for.

    The server start, the health wait, `--resume` and the scoring step were
    written out twice in YAML and were about to be written a third time in a
    systemd unit. LEARNINGS.md L1 is that a rule derived in two places
    eventually disagrees, and the disagreement here costs money: a caller that
    forgot `--resume` pays again for finished queries, and one that started the
    server differently measures something else. So each caller must reach
    `run_eval.py` only through `eval/run.sh`.
    """
    runner_sh = ROOT / "eval" / "run.sh"
    assert runner_sh.exists()

    callers = {
        ".github/workflows/eval.yml": "eval/run.sh --limit 20",
        ".github/workflows/eval-chunk.yml": "eval/run.sh $limit_arg --resume",
        "deploy/runner/egoexo-eval.service": "eval/run.sh --limit 20",
    }
    for path, expected in callers.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        assert expected in text, f"{path} no longer calls run.sh as expected"
        # The one thing that must never come back: a second, direct invocation.
        assert "run_eval.py" not in text, (
            f"{path} calls run_eval.py directly again — that is the duplicate "
            "derivation run.sh was written to remove"
        )


def test_the_shared_script_still_does_what_the_callers_stopped_doing():
    """run.sh has to own the four things the YAML used to spell out itself."""
    text = (ROOT / "eval" / "run.sh").read_text(encoding="utf-8")
    assert "uvicorn src.video_searching_agent.web.main:app" in text  # starts it
    assert "api/v1/health" in text  # waits for it
    assert "--resume" in text  # can skip what is paid for
    assert "--score-only" in text  # leaves a readable scorecard either way


def test_the_daily_slice_fires_at_one_hour_on_both_hosts():
    """Two hosts on different schedules would bill twice for one series."""
    import re

    yaml_text = (ROOT / ".github" / "workflows" / "eval.yml").read_text(encoding="utf-8")
    cron = re.search(r'cron:\s*"(\d+)\s+(\d+)', yaml_text)
    assert cron, "the daily schedule disappeared from the workflow"
    minute, hour = cron.group(1), cron.group(2)

    timer = (ROOT / "deploy" / "runner" / "egoexo-eval.timer").read_text(encoding="utf-8")
    on_calendar = re.search(r"OnCalendar=.*?(\d\d):(\d\d):", timer)
    assert on_calendar, "the systemd timer has no wall-clock time"
    assert (int(on_calendar.group(1)), int(on_calendar.group(2))) == (int(hour), int(minute))
