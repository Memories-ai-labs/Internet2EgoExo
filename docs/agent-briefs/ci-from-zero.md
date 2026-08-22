# Brief — CI from zero, and the ten red tests

**Branch** `claude/ci-from-zero` · **Owns** `.github/`, `scripts/`, the
`README.md` metrics block, `tests/conftest.py`,
`tests/test_tool_policy_integration.py`, `tests/test_streaming_performance.py` ·
**Blocked by** nothing

---

You are the CI agent. Work autonomously; no human is watching. Develop on branch
`claude/ci-from-zero`, commit, push with `git push -u origin
claude/ci-from-zero`, and open a DRAFT pull request when done.

## Context

This repository has **no CI at all** — `.github/` does not exist. It has 900+
tests, a strict mypy config and a ruff config, none of which run on a pull
request. A refactor is about to move most of the source tree (branch
`claude/phase0-carve-core`, running in parallel with you), and it will be far
safer to land with a green light than without one.

Read `docs/ARCHITECTURE.md` on branch
`claude/multi-agent-parallel-architecture-822z3w` for the target package layout —
§5 and §6 describe the jobs proposed here:

```
git fetch origin claude/multi-agent-parallel-architecture-822z3w
git show origin/claude/multi-agent-parallel-architecture-822z3w:docs/ARCHITECTURE.md
```

## What to build

**1. `.github/workflows/ci.yml` — the basics, on every PR and push to `main`.**
`uv sync`, then `ruff check`, `mypy` under the project's strict config, and
`pytest`. Cache the uv environment. Python 3.11 per `requires-python`. No secrets
and no network-dependent tests: the suite must pass on a fork PR with no API
keys configured.

**2. The ten red tests — this is the substantial part.**
`main` has roughly ten failures, all in
`tests/test_tool_policy_integration.py` and
`tests/test_streaming_performance.py`, reported as missing-key environment
issues. Diagnose each one properly and fix it at the root:

- A test that needs a real API key should **skip** with a clear reason when the
  key is absent (`pytest.mark.skipif`), and run when it is present. A skip that
  states its condition is honest; a silently absent test is not.
- A test that only needs *some* value in the environment should get one from a
  fixture in `tests/conftest.py`, not from the developer's shell.
- A test that is genuinely broken should be fixed.

**Never delete, `xfail`, or quarantine a test to get the suite green.** If one of
the ten turns out to be a real product bug rather than an environment problem,
leave the test failing, mark the workflow's expectations honestly, and say so
prominently in the PR body — a red CI that tells the truth is worth more than a
green one that does not. State in the PR exactly how many of the ten now pass,
how many skip and why, and how many remain failing.

**3. `scripts/check_layering.py` — the guard that keeps the refactor honest.**
Walks the AST of every file under `packages/` and `src/` and fails if a stage
package imports a sibling stage package. Read the package list and the allowed
edges from a small declarative config (`scripts/layering.toml` or similar) rather
than hard-coding them, because the package set arrives incrementally over the
next several PRs. It must **pass trivially today** — `packages/` does not exist
yet — and start biting as soon as it does. Add it to the workflow as its own job.

**4. `scripts/check_paths.py` — the ownership guard.**
Given a branch named `agent/PKG/topic`, fail if the PR's diff touches anything
outside `packages/PKG/**`. Make it a no-op for every other branch name, and give
it a documented label-based escape hatch (`contract-change`) for PRs that must
touch `packages/core`.

**5. The README metrics table, generated rather than hand-written.**
`eval/run_eval.py` writes a scorecard; `eval/sample-scorecard.md` shows its
shape. Add `scripts/rollup_scorecard.py` that reads the scorecard JSON and
rewrites a marked block in `README.md` between `<!-- METRICS:START -->` and
`<!-- METRICS:END -->`, with a `--check` mode for CI that fails if the block is
stale. Then a scheduled workflow that runs the eval and commits the refreshed
block — the eval costs real money, so read `eval/README.md` for the cost model
first and default the schedule to something modest and clearly stated. If the
full 200-query set is too expensive to run on a schedule, wire the job up
against `--dry-run` or a small `--limit` and say plainly in the PR what the
scheduled run does and does not measure.

The point of that block: **no agent ever hand-edits the metrics table.**
`README.md` is 60k and one file, and it is the hottest merge-conflict surface in
the repository.

## Stay inside your boundary

You own `.github/`, `scripts/`, the `README.md` metrics block, and the three test
files named at the top. Do **not** touch anything else under `src/`,
`packages/`, `pyproject.toml`, `uv.lock`, `docs/` or `eval/` — the Phase 0 agent
is rewriting most of `src/` right now and will conflict with you. If a CI fix
seems to require a source change, say so in the PR body and leave it.

Two exceptions, both narrow: you may add `[tool.pytest.ini_options]` markers or
similar test-only configuration to `pyproject.toml` if a skip condition needs
it — keep that diff to a few lines and flag it, since Phase 0 also edits that
file. And `uv.lock` must not be regenerated by you at all.

## Done means

A PR opens CI on itself, and the run is green or red for reasons the PR body
states exactly. The layering and paths guards pass trivially today and are wired
to bite later. The README metrics block is generated, with a `--check` job
proving it stays fresh.
