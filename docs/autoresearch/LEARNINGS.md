# Learnings — what the experiments actually taught us

Distilled from `experiments/`. The experiment files are the objective record —
what was run, what the numbers did. This file is the layer above: the things
that generalised, stated once, so a fresh session gets the accumulated judgement
without reading every day's log.

**What belongs here.** A learning that changes what the next iteration would do.
It must name the experiment it came from, and it must be falsifiable in
principle — "measure before changing" earned its place by being tested; "quality
matters" would not.

**What does not.** Activity. Restatements of the plan. Anything that would still
read as true if the experiment had come out the other way.

**Negative learnings rank equal.** "We tried the obvious fix and it did nothing"
saves a future hour, and is the first thing habit leaves out. Record the shape of
the failure, not just the fact of it — *why* it failed is what narrows the space.

Each entry: the learning, then the evidence, then what it implies.

---

## L1 · A decision derived in two places will eventually disagree

**Evidence.** `2026-08-22` experiment 1. Acceptance was defined in
`evaluate_clip` as *no blocking failure AND grade != D*, and re-derived in
`_regrade` as *no blocking failure*. The halves diverged silently and shipped a
clip scoring 25/100 with zero annotations as `accepted: true`. Two earlier bugs
of the same family: `self.gemini` vs `self.llm` (bitten twice), and
`wait_for_operation(timeout=)` swallowed by the function's own `except`.

**Implies.** When a rule exists in code, there is exactly one place it lives and
everywhere else calls that place. Where a second derivation is unavoidable,
a test must assert the two agree. Auditing for remaining duplicate derivations
is worth an iteration on its own — prime suspects are the annotation-level
ladder, the idle-time definition and the hand-ratio threshold.

## L2 · The contradiction check earns its keep

**Evidence.** Scorecard §6 ("where the pipeline contradicts the standard") found
L1 unprompted, on the fifth query of a run whose purpose was something else
entirely. No test, review or reading of the code had caught it.

**Implies.** A metric that checks the *system against its own standard* catches
a class of bug that unit tests structurally cannot: tests assert what a function
does, §6 asserts that two independently-correct components mean the same thing.
Keep it, read it first, and treat a new entry there as blocking — which is why
the promotion rule refuses to promote past one.

## L3 · A guessed constant has been wrong every time; a measured one has held

**Evidence.** Wrong when guessed: the 8-word query cut (produced queries ending
on dangling prepositions, which returned Toca Boca clips), the blur filter
(sharpness measures texture, not quality — usable footage scored 96, an end card
4144), embedding-score cutoffs (gibberish scores 0.354 against a true query's
0.400). Held when derived from footage: every threshold in `clip_quality`.

**Implies.** "No constant without a fixture" is not hygiene, it is the highest
base-rate rule in this repo. A threshold nobody measured is a guess with a
decimal point.

## L4 · Three stills are thin evidence, and the failure is asymmetric

**Evidence.** An activity rule rejected a genuine laundry video 3 runs out of 3,
because its three sampled stills happened to show a cat and a bookshelf. Fixing
it required making the answer three-way so only an affirmative wrong-kind
verdict rejects. Currently the frame screen keeps 7% of candidates (8 of 120).

**Implies.** Where a gate's evidence is sparse, make its answers three-way —
yes / no / cannot tell — and let only one value reject. And the standing
uncertainty: we still do not know how much of that 93% rejection is correct,
which is why growing the calibration set is the highest-value measurement
available.

## L5 · Vendor APIs lie by silence, so never guess a parameter name

**Evidence.** The Datalake accepts unknown top-level search parameters and
*ignores* them: `video_id=` returns other videos' hits while looking scoped.
Only `filter.video_ids` works. Its upload endpoint accepts only `title` and
`custom` metadata keys and reports "json part is not valid JSON" when it means
"unknown key". `clip_embedding` returns nothing at all, for a 22-second clip and
a 400-second video alike.

**Implies.** Probe the contract live before building on it, and record the
finding where the next session will read it. A plausible parameter name that is
silently dropped is worse than an error, because the result looks right.

## L6 · Restarting a measurement is cheaper than reconciling two definitions

**Evidence.** `2026-08-22` experiment 1. The acceptance fix landed 4 queries into
a 200-query run. Restarting cost $1.25 and 15 minutes; carrying on would have
produced a scorecard whose acceptance rate mixed two definitions and could not
honestly be quoted as either.

**Implies.** When a fix changes what a metric *means*, restart the measurement
rather than annotating the mixture. Corollary for in-flight runs: a running
process holds its launch-time code, so editing the measuring script mid-run
desynchronises code from records — which is why `run_eval.py:236` stays
unfixed until this run ends.

## L7 · Selection, not volume, is the product — externally corroborated

**Evidence.** SiMDex (arXiv 2608.04196): mining under 5% of a 32 M-sample
egocentric pool raised VLA success from 47.7% to 61.1% against a baseline
trained on an *equal quantity* of randomly sampled human data — 13.4 points from
selection alone. Independently, RynnVLA-001's curation stage converged on the
same two gates this repo is least able to defend from first principles:
discard on a visible face, keep on visible wrist and hand keypoints.

**Implies.** A low acceptance rate is not obviously bad news; a pipeline that
rejects 95% and can defend the 5% is what that result endorses. What must never
be lost is the *reason* for each rejection, because the deliverable is the
argument for the hours, not the hours. Check periodically that for any accepted
clip we can still reconstruct what was rejected alongside it and why.

## L8 · The licence is the C/B boundary, and it costs exactly 7 points

**Evidence.** `2026-08-22` experiment 3. One fixed L3 tree of 9 annotations
scored through `evaluate_clip` with only the licence varied: CC-BY **75 → B**,
YouTube standard 68 → C, unknown 65 → C. Per-clip weights are annotation depth
30 + tree structure 15 + media 20 + licensing 10, and Gate 3's diversity 25 is
dataset-level, so **75 is the per-clip ceiling — which is a B**.

**Implies.** A non-CC clip is capped at 68 and can never be better than a C
however well it is annotated. So licence is not a downstream footnote, it is the
grade: filtering search to Creative Commons is the highest-leverage change
available, which promotes `INSPIRATION.md` Q-SRC4 from a curiosity to the top of
the list. Grade A stays unreachable per clip at any licence — that part is Gate
3's accounting and remains a product decision.

Worth noting the shape of the mistake this corrects: the baseline read
"annotation depth is the binding constraint" off **one** clip
(`rdt-00003`, 0 anchors, score 7) and would have sent several iterations after a
non-problem. Four of the next five clips reached L2/L3 with 7–9 annotations.
**n=1 is not a bottleneck, it is an anecdote** — and the cheapest guard against
it is to decompose a score before believing a story about it.

## L9 · Refusing to label beats labelling badly

**Evidence.** External, not yet tested here. Action100M discards segments under
4 seconds and marks ~3.23% of segments `N/A` for non-action content. Panda-70M's
most instructive result is negative: no single captioner produced a good caption
for more than ~35% of videos, while the union of teachers covered 88.8%.

**Implies.** Two things this repo already believes in one place and not another.
It excludes unmeasured checks from the score (same instinct), but its annotation
agent currently returns *nothing* rather than `N/A` — which scores identically
to "not measured" while meaning something quite different. And low annotator
confidence should widen the panel, not drop the span. Both are open in
`INSPIRATION.md` stage 5 — not because the grade distribution is stuck there
(L8 shows it is stuck on licence) but because one clip in five still returns no
labels at all, and scoring 7 is not the same fact as scoring nothing.
