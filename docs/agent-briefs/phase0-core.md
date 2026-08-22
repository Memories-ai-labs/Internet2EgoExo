# Brief — Phase 0: carve `i2e-core`

**Branch** `claude/phase0-carve-core` · **Owns** `packages/`, `src/`,
`pyproject.toml`, `uv.lock` · **Blocks** all five stage agents

---

You are Phase 0 of a planned refactor of this repository. Work autonomously; no
human is watching. Develop on branch `claude/phase0-carve-core`, commit, push
with `git push -u origin claude/phase0-carve-core`, and open a DRAFT pull
request when done.

## Read the spec first

The design document may not be on `main` yet. Get it:

```
git fetch origin claude/multi-agent-parallel-architecture-822z3w
git show origin/claude/multi-agent-parallel-architecture-822z3w:docs/ARCHITECTURE.md
```

Read all of it, then implement **Phase 0 and only Phase 0** — the table in §8.
Do not start Phase 1. Do not create `packages/sourcing`, `packages/acquire`,
`packages/lake`, `packages/labeling` or `packages/curation`; five other agents
get those, and they are blocked until your PR lands.

## What Phase 0 is

Create `packages/core/` as a `uv` workspace member exposing `i2e_core`, and move
into it exactly the things that today cause the four import cycles, plus the new
contract and port definitions. The measured cycles are:

- `agent ↔ curation` (12 / 2) — quality gates and scoring reach into `agent`;
  `curation/frame_viewpoint.py` and `curation/query_rewrite.py` import
  `parse_json_object` from `agent/react.py`
- `models ↔ curation` (5 / 3) — `models/{dataset,query,result}.py` import
  `Viewpoint`, `CostBreakdown`, `is_reusable_license`
- `pipeline ↔ agent` (2 / 1) — `agent/eyes.py` imports `read_mp4_dimensions`
  from `pipeline/media_probe.py`
- `router ↔ agent` (1 / 1) — `router/classifier.py` imports
  `CLASSIFICATION_PROMPT` from `agent/prompts.py`

Move: `Viewpoint` and `classify_viewpoint`; the ReAct loop, `AgentTrace` and
`parse_json_object`; `CostBreakdown`, pricing and token accounting;
`read_mp4_dimensions`; the LLM clients (`api/llm.py`, `api/gemini_client.py`,
`api/openrouter_client.py`); settings; and the generic tool base, registry and
retry executor. Write `i2e_core/contracts.py` (the five models,
`CONTRACT_VERSION`, and the `Outcome`/`StageResult`/`StageMetrics` envelope) and
`i2e_core/ports.py` (the four Protocols). Contracts and ports are new code;
everything else is a move.

## Hard constraints

1. **No behaviour changes.** This is a move plus new type definitions. If you
   find a bug while moving, leave it and note it in the PR body. Resist every
   temptation to improve code you are relocating.
2. **`video_searching_agent` keeps working.** It becomes a shim that re-exports
   from the new locations. The deployed Vercel app, `qa/`, `eval/` and the whole
   existing test suite import it and must not break. Do not delete it.
3. **The test suite must not regress.** Record `pytest` output on `main` BEFORE
   you start and put both numbers in the PR body. `main` currently has ~10
   pre-existing failures in `tests/test_tool_policy_integration.py` and
   `tests/test_streaming_performance.py` (missing-key env issues). Those two
   files and `tests/conftest.py` belong to another agent working in parallel —
   **do not edit them**, and do not count their failures against yourself.
4. **`ruff check` and `mypy --strict` clean** on `packages/core`, and no worse
   than `main` elsewhere.
5. **Stay inside your boundary.** You may touch `packages/`, `src/`,
   `pyproject.toml`, `uv.lock`, and tests other than the three files named
   above. Do **not** touch `.github/`, `scripts/`, `README.md`, `docs/`, or
   `eval/` — a second agent owns those right now and will conflict with you.

## Suggested order

Contracts and ports first (new files, nothing depends on them yet), then the
leaf utilities with the fewest importers (`read_mp4_dimensions`,
`CLASSIFICATION_PROMPT`), then `Viewpoint` and cost, then the ReAct loop, then
the LLM clients and settings last since everything imports them. Run the suite
after each move rather than at the end — a green step is a place to commit.

## Done means

The import graph is a star: nothing under `src/` or `packages/` imports a
sibling stage package. Write a `packages/core/README.md` stating what belongs in
core and what does not. In the PR body, list every symbol that moved with its
old and new path, state the before/after test counts, and name anything you
deliberately left alone.

If you cannot keep the suite green, stop and say so in the PR rather than
pushing a partial move that blocks five other agents.
