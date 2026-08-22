# Brief — CI from zero, and the ten red tests

**Branch** `claude/ci-from-zero` · **Owns** `.github/`, `scripts/` except
`check_layering.py`, the `README.md` metrics block, `tests/conftest.py`,
`tests/test_tool_policy_integration.py`, `tests/test_streaming_performance.py` ·
**Blocked by** nothing

---

Work autonomously; no human is watching. Develop on `claude/ci-from-zero` cut
from `main`, commit as you go, push with `git push -u origin
claude/ci-from-zero`, and open a DRAFT pull request.

## Context

This repository has **no CI at all** — `.github/` does not exist — while carrying
900+ tests, a strict mypy config and a ruff config that never run on a pull
request. A refactor of most of the source tree is starting in parallel
(`claude/core-move-and-types`, implementing §8 steps 1–2 of
[`docs/MODULES.md`](../MODULES.md)), and it is far safer to land with a green
light than without one.

Read §7 of `docs/MODULES.md` for the mechanics these jobs enforce.

## What to build

**1. `.github/workflows/ci.yml` — the basics, on every PR and push to `main`.**
`uv sync`, then `ruff check`, `mypy` under the project's strict config, and
`pytest`. Cache the uv environment. Python 3.11 per `requires-python`. It must
pass on a fork PR with no API keys configured: no secrets, no network-dependent
tests.

**2. The ten red tests — the substantial part.**
`main` has roughly ten failures, all in `tests/test_tool_policy_integration.py`
and `tests/test_streaming_performance.py`, reported as missing-key environment
issues. Diagnose each and fix it at the root:

- A test that needs a real API key should **skip** with a stated reason when the
  key is absent, and run when it is present. A skip that names its condition is
  honest; a silently absent test is not.
- A test that only needs *some* value in the environment should get one from a
  `tests/conftest.py` fixture, not from the developer's shell.
- A test that is genuinely broken should be fixed.

**Never delete, `xfail`, or quarantine a test to get the suite green.** If one of
the ten turns out to be a real product bug rather than an environment problem,
leave it failing and say so prominently in the PR body — a red CI that tells the
truth is worth more than a green one that does not. State exactly how many now
pass, how many skip and why, and how many remain red.

**3. `scripts/check_paths.py` — the ownership guard.**
Given a branch named `agent/PKG/topic`, fail if the diff touches anything outside
`packages/PKG/**`. A no-op for every other branch name, with a documented
label-based escape hatch (`contract-change`) for PRs that must touch
`packages/core`.

**4. Wire `scripts/check_layering.py` as its own job.** You do not write it — the
core agent does, because it is the proof its move worked. Add the job that runs
it, and expect it to report two remaining cycles rather than zero.

**5. The README metrics table, generated rather than hand-written.**
`eval/run_eval.py` writes a scorecard and `eval/sample-scorecard.md` shows its
shape. Add `scripts/rollup_scorecards.py` reading the scorecard JSON and
rewriting a marked block in `README.md` between `<!-- METRICS:START -->` and
`<!-- METRICS:END -->`, with a `--check` mode that fails CI if the block is
stale. Then a scheduled workflow that refreshes and commits it.

The eval spends real money — read `eval/README.md` for the cost model before
choosing a schedule, keep it modest, and state plainly in the PR what the
scheduled run does and does not measure. If the full 200-query set is too
expensive to run on a schedule, wire it to `--dry-run` or a small `--limit` and
say so.

The point of the marked block: **no agent ever hand-edits the metrics table.**
`README.md` is 60k in one file and the hottest merge-conflict surface here.

## Boundary

You own `.github/`, everything in `scripts/` except `check_layering.py` and its
config, the `README.md` metrics block, and the three test files named at the top.
Touch nothing else under `src/`, `packages/`, `docs/` or `eval/` — the core agent
is moving files across `src/` right now. Do not regenerate `uv.lock`. If a CI fix
appears to need a source change, say so in the PR body and leave it.

One narrow exception: you may add test-only configuration to `pyproject.toml`
(markers, options) if a skip condition needs it. Keep that diff to a few lines
and flag it, since the core agent edits that file too.

## Done means

A PR opens CI on itself, and the run is green or red for reasons the PR body
states exactly. The paths guard is wired and no-ops on normal branches; the
layering job runs and reports what remains. The README metrics block is
generated, with a `--check` job proving it stays fresh.
