# Brief — `core`, steps 1 and 2

**Branch** `claude/core-move-and-types` · **Owns** `src/`, `packages/core/`,
`pyproject.toml`, `uv.lock`, `scripts/check_layering.py` · **Blocks** the five
stage agents in §7

---

Work autonomously; no human is watching. Develop on `claude/core-move-and-types`
cut from `main`, commit at every green step, push with `git push -u origin
claude/core-move-and-types`, and open a DRAFT pull request.

## The spec

Read [`docs/MODULES.md`](../MODULES.md) in full — it is on `main`, it is the only
design document, and it is not summarised here. You are implementing **§8 steps 1
and 2, and nothing after them.** Do not extract any stage package: no
`sourcing`, `screening`, `acquire`, `lake`, `labeling`, `refine`, `curation` or
`audit`. Five other agents get those and they are blocked on you.

§8 makes a commitment worth taking literally: steps 1 and 2 are worth doing even
if nothing after them ever happens. Treat them as the deliverable, not as
preamble to a refactor.

## Step 1 — move five files

Per §1, four of the six cycles are one mistake wearing four hats: infrastructure
that landed inside a business package, so everyone needing the infrastructure
depends on the business. The five moves §8 names:

| what | to |
|---|---|
| `parse_json_object` (from `agent/react.py`) | `core/json_repair` |
| `agent/prompts.py` | `core/prompts` |
| `pipeline/media_probe.py` | `core/media` |
| `Viewpoint` (from `curation/viewpoint.py`) | `core/contracts` |
| `CostBreakdown` (from `curation/cost.py`) | `core/spend` |

That clears `agent ↔ curation`, `agent ↔ router`, `agent ↔ pipeline` and
`curation ↔ models` without extracting a single package.

Then write `scripts/check_layering.py` — the AST pass §7 calls the highest-value
test in the repository. Two requirements, and the second is the point:

- It must **report the two cycles that remain** (`(root) ↔ agent` and
  `(root) ↔ web`, both artefacts of `utils` living at the root), not pass
  vacuously. A guard that is green because it checks nothing is worse than no
  guard.
- Read the package set and the allowed edges from a small declarative config
  beside it, because packages arrive incrementally over the next several PRs.

Whether you also fix the `utils` cycles is your call — they are packaging, not
design, and if the fix is small, take it and say so.

## Step 2 — land the core types

`Measured`, `Spend`, `Verdict` with its `gated` declaration, and `Outcome` — as
§3 specifies them, including the properties that are the whole point:
`Measured.unmeasured(...)` must raise on comparison rather than compare false,
and `sum()` over `Spend` must return a total **and** a count of unpriced items.

§8 attaches a condition to this step and it is the part that matters:
**migrate one real caller of each**, so they are real rather than aspirational.
Pick the caller where the type prevents a defect the codebase actually produced —
§2 names them, including the `x or 0.0` that ate a stillness assertion because
`(0.0 or 1.0)` is `1.0`. A type with no caller is a proposal.

If `Verdict.gated` is to mean anything, the generated test §3 describes has to
exist for at least one stage: varying a dimension that is measured but not gated
must not change `usable`.

## Hard constraints

1. **Step 1 is a move.** No behaviour changes. If you find a bug while
   relocating, leave it and note it in the PR body.
2. **`video_searching_agent` keeps working.** It becomes a shim re-exporting from
   the new locations. The Vercel deployment, `qa/` and `eval/` all import it and
   must not break. Do not delete it.
3. **No regression.** Record `main`'s `pytest` baseline before you start and put
   both numbers in the PR body. `main` carries ~10 pre-existing failures in
   `tests/test_tool_policy_integration.py` and `tests/test_streaming_performance.py`
   (missing-key env issues). Those two files and `tests/conftest.py` belong to
   the CI agent running in parallel — **do not edit them**, and do not count
   their failures against yourself.
4. **`ruff check` and `mypy --strict` clean** on `packages/core`, and no worse
   than `main` elsewhere.
5. **Boundary.** You own `src/`, `packages/core/`, `pyproject.toml`, `uv.lock`
   and `scripts/check_layering.py` plus its config. Do **not** touch `.github/`,
   anything else in `scripts/`, `README.md`, `docs/`, or `eval/` — the CI agent
   owns those right now and will conflict with you.

## Done means

`check_layering.py` reports two cycles instead of six, and says which. Each of
the four core types has at least one real caller. `packages/core/README.md`
states what belongs in core and what does not. The PR body lists every symbol
that moved with its old and new path, the before/after test counts, which caller
was migrated for each type, and anything deliberately left alone.

If you cannot keep the suite green, stop and say so in the PR rather than pushing
a partial move that blocks five other agents.
