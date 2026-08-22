# Agent briefs

One file per parallel agent. A brief is the whole of what that agent is given:
its box, its branch, its file boundary, and what "done" means. Paste one into a
fresh session and it should need nothing else.

The roster and the reasoning behind the boundaries are in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md). The briefs here are the executable
form of §5 of that document.

## Running order

**Only two of these can run at once today.** The five stage agents are blocked
until `phase0-core` lands, because the package boundaries they depend on do not
exist yet — before Phase 0, all five would be editing
`agent/cleaning_agent.py`, `curation/*`, `models/*` and `pyproject.toml` at the
same time.

| brief | branch | owns | blocked by |
|---|---|---|---|
| `phase0-core.md` | `claude/phase0-carve-core` | `packages/`, `src/`, `pyproject.toml`, `uv.lock` | — |
| `ci-from-zero.md` | `claude/ci-from-zero` | `.github/`, `scripts/`, `README.md` metrics block, the two failing test files, `tests/conftest.py` | — |
| the five stage briefs | `agent/<pkg>/<topic>` | `packages/<pkg>/**` | `phase0-core` |

The two runnable now are disjoint by construction: Phase 0 touches no CI or
scripts, and the CI agent touches no source file except the two test modules
that are already failing on `main`.

## Why boundaries are written into the brief

The design's claim is that an agent can be handed one box, one metric and one
test command, and be trusted to work alone for a day. That only holds if the box
is stated, so every brief names both what it owns and what it must not touch.
An agent that has to guess its boundary will find a reason to widen it.
