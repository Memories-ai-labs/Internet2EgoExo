# Splitting this up, so it can be optimised in pieces

24,524 lines, 13 packages, 45 package-to-package import edges, 6 cycles. The goal
is a set of boxes that can be worked on and measured independently. This document
says where the lines go, and — more importantly — what each line is protecting
against, because "cleaner" is not a reason and cleanliness is not a property you
can test.

Everything here is derived from the current tree and from defects this codebase
actually produced. Where a claim has no measurement behind it, it says so.

---

## 1. What the tree looks like now

```
agent        6,767 lines  14 files   imports 9 packages, imported by 5
tools        4,599        12         imports 6, imported by 2
curation     3,748        12         imports 5, imported by 7
pipeline     2,079         7         imports 5, imported by 2
api          1,871         6         imports 1, imported by 6
models       1,492         7         imports 1, imported by 7
evaluation   1,465         4
router       1,063         3         imports 4, imported by 2
web            733         6         imports 9, imported by 1
config         523         3         imports 0, imported by 6
utils          176         2
```

Six cycles. Four are one thing wearing four hats — a piece of *infrastructure*
that ended up inside a *business* package, so everyone who needs the
infrastructure now depends on the business:

| cycle | what actually crosses |
| --- | --- |
| `agent ↔ curation` | agent needs 7 curation modules; curation needs `agent.react.parse_json_object` |
| `agent ↔ router` | agent needs `router.query_parser`; router needs `agent.prompts` |
| `agent ↔ pipeline` | agent needs `pipeline.media_probe`; pipeline needs two agents |
| `curation ↔ models` | curation needs 3 models; models needs `curation.cost`, `curation.scoring`, `curation.viewpoint` |

JSON repair, prompts, MP4 header parsing, a cost type, an enum. None of them is
a dependency between two stages of the work. The remaining two cycles
(`(root) ↔ agent`, `(root) ↔ web`) are packaging artefacts of `utils` living at
the root.

So the split is cheaper than the graph suggests. **Moving five files breaks four
of the six cycles**, and it can be done before any package is extracted.

One honest note on provenance: I added weight to `agent ↔ curation` today, by
giving both ReAct agents a `find_frames` tool that imports
`curation.embedding_search`. That import is the right dependency pointing the
wrong way, and it is exactly what §4's ports fix.

---

## 2. What the split has to protect against

Not tidiness. Three failure modes this codebase produced, all of which a
structure can make harder.

### 2.1 Boundary-name bugs

Every genuinely hard bug found recently was one module calling another's API by
guessing a name:

| the guess | the truth | how it presented |
| --- | --- | --- |
| `self._llm` | the field is `_gemini` | a unit test went from 0.4s to 4.7s by reaching the network |
| `wait_for_operation(timeout=)` | `max_wait_seconds=` | `TypeError` caught by the caller's own `except`, reported as "still indexing" |
| `search(video_id=…)` | `filter={"video_ids": […]}` | **the server accepted it and ignored it** — results from nine other videos, looking scoped |
| `ClippingResult()` | requires `video_id` | only surfaced when the code ran |

The third is the important one, because no amount of layering prevents it: a
vendor API that silently accepts an unknown parameter cannot be defended against
by types on our side. It needs **one hand-written adapter that owns the vendor's
vocabulary, and a test recorded against the live endpoint**. Which is a
structural requirement, not a coding-style preference.

### 2.2 Numbers that were never measured, presented as measurements

The most valuable rules in this codebase are currently prose in docstrings:

- *nothing is scored on a number we did not measure* — an uncomputable gate
  reports `measured: false` and is excluded, not failed
- *scores rank; they do not measure* — the visual index's 0.40 for a true query
  against 0.354 for gibberish means no cutoff exists
- *sharpness measures texture, not quality* — so it is reported and never gated
- *cost `None` is not cost `0`* — a provider that reports no price must not make
  a bill look complete
- *`gated` names what was allowed to reject*, so a number that is merely present
  is not mistaken for one that was enforced

Every one of these was learned by getting it wrong first. They are enforced today
by memory plus a test here and there, which is the same as not enforced. §3 makes
them types.

### 2.3 The cost of one iteration

Changing an annotation prompt today means search → download → upload → index
before the change can be observed: an hour, and real money, per attempt. That is
the actual ceiling on how fast any of this improves, and it is a bigger lever
than any amount of parallelism. §4 is aimed squarely at it.

---

## 3. Core types, because the discipline should not be remembered

`i2e-core` holds no business logic. It holds the vocabulary, and the vocabulary
is where the rules live.

### `Measured[T]`

```python
Measured.of(0.047, unit="mean abs frame diff")   # measured, and it is 0.047
Measured.unmeasured("no decoder available")      # not measured, and here is why
```

Two properties, and they are the whole point: it has no `.value` that returns a
default, and it does not compare. `Measured.unmeasured(...) >= 0.6` raises rather
than being false. Today the same protection is a hand-written `if measurement.
measured:` at the top of each judge, remembered each time — and `x or 0.0`
already ate a real test, because `(0.0 or 1.0)` is `1.0` and a perfectly still
clip failed a stillness assertion.

Scoring becomes structural: a scorecard sums `Measured` values and reports its
own denominator, so "excluded because unmeasured" and "zero because it failed"
can no longer render as the same 0.

### `Spend`

```python
Spend.usd(0.008, "moment search")
Spend.unpriced("gemini reports no cost", tokens=2795)
```

`sum()` of a list of `Spend` returns a total **and** a count of unpriced items.
There is no way to add an unpriced call and get a number that looks complete —
which is the bug the search-time spend log had, silently adding `None` as zero.
Four separate cost accounts exist today (frame-check log, refine cuts, eval
ledger, agent usage metrics); this is one.

### `Verdict`

```python
Verdict(usable=False, reasons=[...], gated=("static_graphic",), notes=[...])
```

`gated` is the declaration of what this stage is allowed to reject on. A test
generated from it asserts that varying anything *not* in `gated` never changes
`usable` — so "sharpness is measured and never gated" is checked rather than
promised, at every value, for every stage that says it.

### `Outcome[T]` — four states, not two

`ok` / `rejected` / `pending` / `failed`. `ingest.py` already draws this
distinction and it was worth a defect each to learn: **rejected** is a judgement
the pipeline stands behind, **pending** is a budget that ran out and can be
resumed with the id, **failed** is a fault. Collapsing pending into failed is how
"a clip neither accepted nor rejected, with no reason" happened.

Every stage returns `Outcome[T]` plus `StageMetrics` (wall time, `Spend`,
implementation name and version). That is the data behind every table anyone
wants to read later.

---

## 4. Ports in core, adapters where the resource lives

The rule that makes the boxes independent: **a stage depends on `core` and on
nothing else.** When labeling needs a frame, it does not import the lake — it
takes a `FrameSource`.

```
core/ports.py     FrameSource · MomentReader · ClipCutter · Uploader
                  TagWriter · LlmClient · Ledger · Clock
lake/adapters     the real ones, owning the vendor's vocabulary
eval/replay       recorded ones, from cassettes
orchestrator      decides which to inject
```

Two consequences, and the second is the one worth the work.

**Vendor vocabulary stops at the adapter.** `filter={"video_ids": […]}` is
written once, in one file, next to a test recorded against the live endpoint that
asserts a scoped search returns only the video asked for. Every silently-ignored
parameter is then one test away from being caught, instead of one careful reader
away.

**Labeling becomes cheap to iterate.** With `FrameSource` and `MomentReader`
behind ports, changing a prompt is a replay against cassettes: seconds, and a
bounded token bill, instead of an hour and a download. That is the difference
between twenty attempts a day and two, and it is the real bottleneck — not merge
conflicts.

The cassettes are recorded from real runs and committed. They are also how the
`clip_embedding` finding stays true: it returns nothing for a 22-second clip and
nothing for a 400-second one, so dedup is built on `frame_embedding`, and a
replay fixture pins that rather than a comment.

---

## 5. Eight stages, cut where the work unit changes

The line goes where the **unit of work, the dominant cost, and the failure mode**
all change together. That test puts the boundaries here:

| package | unit | dominant cost | how it fails |
| --- | --- | --- | --- |
| `sourcing` | a query | search fees + tokens | finds nothing, or finds the wrong genre |
| `screening` | a candidate | **$0.002** a look | drops good footage; passes a tripod |
| `acquire` | a URL | **$0.09–0.12** a download | bot wall; read-only disk |
| `lake` | a file | **$0.05** per video-minute | 402; slow index; ignored parameters |
| `labeling` | a video | tokens + $0.005 a look | invents a hand; restates its parent |
| `refine` | an anchor | **$0.005** a cut | keyframe drift; a title card |
| `curation` | a set | ~free | double-counted hours |
| `audit` | a set | tokens | confirms where it should refute |

Two of these boundaries are ones I crossed painfully today and would not merge
again:

- **`screening` apart from `sourcing`.** Sourcing spends search fees on metadata;
  screening spends money per candidate on looks. They fail differently too:
  sourcing's failure is an empty list, screening's is a *wrong rejection*, and
  the second needs a held-out set of hand-judged candidates that sourcing has no
  use for.
- **`refine` apart from `labeling`.** Labeling's unit is a video, refine's is an
  anchor, and refine is the only stage that writes new media. Keeping them
  together is what made "cut the anchors" feel like a change to the annotator.

Then `orchestrator` (sequencing, budgets, deadlines), `service` (HTTP, SSE, the
UI), `eval` (the frozen set, the metrics, the replay adapters).

---

## 6. Calibration sets are package contents, not commit messages

Every threshold in this codebase was derived from footage, and every derivation
currently lives in a docstring:

| constant | derived from |
| --- | --- |
| `STATIC_MOTION_MAX = 0.030`, `GRAPHIC_SHARPNESS_MIN = 2500` | 9 spans across 3 videos; an end card at 0.018/4144 against usable footage at 0.047/96 |
| the viewpoint check's asymmetry | 19 candidates hand-judged from their frames; 18/19 at four different frame resolutions |
| "no cutoff on embedding score" | 0.400 true / 0.362 absurd / 0.354 gibberish, one video |
| the activity rule's three-way answer | 9-of-9 caught, 0-of-27 good clips lost, three runs |

So: `packages/<pkg>/calibration/` holds the fixtures and the labels, and
`test_calibration.py` **re-derives every constant from them**. A threshold that
someone nudges without new footage fails a test. A threshold with no fixture
cannot be added. The rule is one line — *no constant without a fixture* — and it
is the difference between a number somebody measured and a number somebody liked.

These sets are small (three clips, nineteen thumbnails, a score table) and they
are the most expensive knowledge here, because each one cost a wrong version
first.

---

## 7. Six agents, and the mechanics of not colliding

| agent | package | the number it moves | its eval |
| --- | --- | --- | --- |
| A | `sourcing` | egocentric share of candidates found | replay: frozen queries → judged candidates |
| B | `screening` + `acquire` | wrong-rejection rate; download success | the 19-candidate held-out set |
| C | `lake` | index success; $ per indexed minute | contract tests against the live API |
| D | `labeling` | anchors per usable hour; audit pass rate | cassette replay, no paid calls |
| E | `refine` + `curation` | clips surviving the pixel pass; hours accuracy | the 3-clip calibration set |
| F | integration | the whole funnel, end to end | the frozen 200, and it is the only one that spends |

Each agent gets a worktree and a branch `agent/<pkg>/<topic>`; CI rejects a PR
touching outside `packages/<pkg>/**`. Implementations are **named and versioned**
rather than replaced — `frames@v2` lands beside `frames@v1` and the package's
default flips a string — so experiments stack, two can be live at once, and a
regression is reverted by editing one string.

Three files would otherwise collide on every merge, and each has a mechanical
answer:

- **the README's results table** → generated by `rollup_scorecards.py` from
  `packages/*/eval/scorecard.json`, committed only by the scheduled job. No agent
  edits it.
- **`pyproject.toml`** → one per package.
- **`uv.lock`** → regenerated only by the scheduled job.

A contract change (anything in `core` beyond adding an optional field) is its own
PR: bumps `CONTRACT_VERSION`, updates the golden JSON snapshots, merges alone.

And `scripts/check_layering.py` — twenty lines of AST asserting no package
imports a sibling — is the highest-value test in the repository. Without it the
graph is back to today's within a month, and I would know, because I made one of
today's edges myself.

---

## 8. Order of work

Each step leaves the tree working and testable. Nothing below needs the step
after it.

1. **Move five files.** `parse_json_object` → `core/json_repair`, `prompts` →
   `core/prompts`, `media_probe` → `core/media`, `Viewpoint` → `core/contracts`,
   `CostBreakdown` → `core/spend`. Four of six cycles gone, no package extracted.
   Add `check_layering.py` immediately, failing on what remains.
2. **Land the core types.** `Measured`, `Spend`, `Verdict.gated`, `Outcome`.
   Migrate one caller of each so they are real, not aspirational.
3. **Ports and one adapter pair.** `FrameSource` + `MomentReader`, real against
   the Datalake, replay against cassettes. Prove it by running the labeling
   tests with no network.
4. **Carve the two cheap packages first** — `sourcing` and `screening`. Smallest
   surface, and they hold the calibration set that makes B's work measurable.
5. **Then `lake`, `labeling`, `refine`, `curation`, `audit`**, in that order:
   `lake` first because everything downstream mocks it, `audit` last because it
   depends on every contract being settled.
6. **`orchestrator` and `service` last.** They are the only things that should
   know the order of the stages, and they cannot be written until the stages
   exist.

The commitment worth making explicitly: step 1 and step 2 are worth doing even
if nothing after them happens. Moving five files removes four cycles, and
`Measured` plus `Spend` prevent a class of defect that has cost this project more
than any other.
