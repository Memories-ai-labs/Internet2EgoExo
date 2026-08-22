# Agent briefs

The design is [`../MODULES.md`](../MODULES.md), and it is the only spec: the
package boundaries and why they fall where they do, the core types, the ports,
the calibration-set rule, the roster in §7 and the order of work in §8. Nothing
here restates it.

A brief is the operational half — which step of §8 an agent is doing, which
branch it works on, which files it owns, which files it must not touch, and what
"done" means. Paste one into a fresh session and it should need nothing but the
repository.

## Running order

§8 is a sequence, and its first two steps are the serial part. The five stage
agents in §7 are blocked until those land: before them, all five would be editing
`agent/cleaning_agent.py`, `curation/`, `models/` and `pyproject.toml` at the same
time — the exact collision the split exists to prevent.

| brief | §8 step | branch | owns |
|---|---|---|---|
| `core-steps-1-2.md` | 1 and 2 | `claude/core-move-and-types` | `src/`, `packages/core/`, `pyproject.toml`, `uv.lock`, `scripts/check_layering.py` |
| `ci-from-zero.md` | the §7 mechanics | `claude/ci-from-zero` | `.github/`, the rest of `scripts/`, the `README.md` metrics block, three test files |
| the five stage briefs | 4 and 5 | `agent/<pkg>/<topic>` | `packages/<pkg>/**` |

The two runnable now are disjoint by construction. The core agent touches no CI
and no source outside the five-file move; the CI agent touches no source file
except the two test modules already failing on `main`. They meet in one
directory, `scripts/`, and the split there is by filename: the core agent writes
`check_layering.py`, because it is the proof that step 1 worked and it needs to
watch it go from four cycles to two; the CI agent wires it into a job and owns
everything else there.

## Why boundaries go in the brief

§7's claim is that an agent can be handed one box, one number it moves and one
eval, and be trusted to work alone. That only holds if the box is stated, so every
brief names both what it owns and what it must not touch. An agent left to infer
its boundary will find a reason to widen it.

## Two things learned spawning the first pair

- **A child session inherits a permission mode that blocks.** Both stalled inside
  a minute on a permission prompt, with no human watching to approve it. Spawn
  autonomous agents with a mode that does not prompt, or they sit there forever.
- **Read `main` before writing a spec.** The first version of these briefs
  pointed at a second design document, written in parallel with `MODULES.md` and
  largely redundant with it. That document has been deleted. Two competing specs
  is worse than either one alone, and the duplicated effort was avoidable by
  fetching `main` first.
