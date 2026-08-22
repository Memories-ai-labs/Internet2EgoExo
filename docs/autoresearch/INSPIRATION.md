# Inspiration — things worth trying, and how we would know

This is the idea bank. Every entry is **open-ended on purpose**: a change we
suspect would help, paired with the measurement that would settle it. An idea
without a falsifier does not belong here — that is the whole difference between
this file and a wish list.

## Where inspiration comes from

Refill this file every run, from three places, in this order:

1. **`RELATED_WORK.md`** (on the `claude/related-work-integration-hkv7ez`
   branch of the public repo; a routine keeps it current). Read a section that
   maps onto a stage you are about to work on and ask what is *transferable* —
   not what is impressive. The best entries below came from exactly that:
   RynnVLA's keypoint rule, Panda-70M's ensemble-of-teachers, Action100M's
   4-second floor and `N/A` class, a learning-free binary-search localiser.
   Adopt mechanisms, never conclusions: their corpus is not our corpus, and the
   whole point of an entry is that we go and check.
2. **`LEARNINGS.md`**. A distilled learning usually implies the next
   experiment — most often "this held on one stage, does it hold on the
   adjacent one?". Negative learnings are the richer source: knowing *why*
   something failed narrows what could work.
3. **The newest scorecard.** The worst number on it is a standing invitation. If
   nothing here addresses it, that is the gap to write down.

Nothing here is approved, and nothing is ranked by how interesting it sounds —
only by which number it would move. When an entry gets tested, record the
experiment in `experiments/<date>.md`, distil anything durable into
`LEARNINGS.md`, and strike the entry here with a one-line verdict **including
when the answer was no**. A dead idea recorded is worth more than a live idea
forgotten, because the loop starts from nothing every hour and will otherwise
try it again.

**Format.** Each entry gives the hypothesis, how to measure it, what result
would kill it, the rough spend, and where the idea came from. Stage headings
match the eight stages in `MODULES.md`.

---

## Stage 0 · Sourcing — what we type into the search box

This stage is the cheapest place in the pipeline to be wrong, and the most
expensive place to *stay* wrong: every downstream dollar is spent on what search
handed back. It is also the least measured.

### Q-SRC1 · Do gear words help or hurt? *(Shawn's example — start here)*

**Hypothesis.** Query wording, not query meaning, decides what comes back.
Searching `first-person cooking GoPro` and searching `first-person cooking` are
not the same request: the gear word is a proxy for viewpoint that also acts as a
hard filter on the corpus. Our current rewrite leans on gear and viewpoint words
(`POV`, `first person`, `GoPro`, `head-mounted`), which plausibly buys precision
at the cost of most of the recall — a huge amount of genuine egocentric footage
is uploaded by people who never say any of those words.

**Measure.** Take 20 queries spread across task families. For each, build four
variants and run only stage 0 and stage 1 (search + frame screen), which is the
cheap part:

| variant | example |
|---|---|
| bare task | `someone folding laundry` |
| task + viewpoint | `first person folding laundry` |
| task + gear | `folding laundry GoPro` |
| task + viewpoint + gear (today) | `first person POV folding laundry GoPro` |

Report per variant: candidates found, share surviving the frame screen, and
**unique survivors it alone contributed** (the union across variants is the
denominator that matters — a variant that finds 20 clips the others also found
is worth nothing). Screening cost is the budget line; no downloads.

**Falsifier.** If today's variant contributes ≥80% of the union's survivors, the
gear words are not costing recall and this is closed. If a bare-task query
contributes a large unique share, the rewrite is over-constrained and the fix is
to **issue several variants per query and union the results** rather than to
pick a better single phrasing.

**Cost.** ~20 queries × 4 variants × screening ≈ $4–8. The single most
information-dense measurement available right now.

**Provenance.** Shawn, 2026-08-22. Note the shape of the answer he expected:
not "which phrasing is best" but "stop searching one way".

### Q-SRC2 · Is one search per query leaving the tail on the table?

**Hypothesis.** We issue one rewritten query per task and take the top 20. Recall
is capped by that single ranking. Multi-query expansion — the task phrased as an
instruction, as a noun phrase, as a tool name, as a room — would reach different
neighbourhoods of the index.

**Measure.** Overlap analysis over the same 20 queries: how much do the result
sets of differently-phrased searches actually intersect? If the Jaccard index is
low, expansion is nearly free recall. Reuse the Q-SRC1 harness.

**Falsifier.** High overlap (>0.7) means the index is already returning
everything it has for this concept and expansion only costs money.

**Cost.** Folds into Q-SRC1 at no extra spend.

### Q-SRC3 · Subtitle search to find the minute before downloading the video

**Hypothesis.** The unit of value is "the 40 seconds where they pick up the
tool", not the video. Searching a candidate channel's *subtitles* locates that
minute for almost nothing, before a single byte of video is fetched — which
would cut both download volume and the indexing bill.

**Measure.** On 10 accepted videos we already hold, compare the timestamp our
pipeline chose (via frame search and the cleaning agent) against the timestamp a
subtitle search would have proposed for the same task phrase. Report offset
distribution and how often the subtitle hit lands inside the accepted span.

**Falsifier.** Egocentric task footage is frequently silent or wordless
(`yt-fts`'s premise assumes talking heads). If subtitles are absent or
uninformative on more than half the sample, this dies for our corpus even
though it works for instructional video.

**Cost.** ~$0. Transcripts we already index.

**Provenance.** `yt-fts` (§7 of RELATED_WORK) — noted there as "the cheapest
known way to find *the moment*". Also the Action100M corpus is 1.2 M
*instructional* videos, i.e. exactly the talking kind; our corpus may not be.

### Q-SRC4 · Licence as a search-time facet, not a downstream footnote

**Hypothesis.** Filtering for Creative Commons at search time changes the yield
curve, and we would rather know the size of the CC-only corpus than discover
per-clip that Gate 0 fails.

**Measure.** Run the same 20 queries with and without the YouTube Data API's CC
filter. Report candidates, survivors, and what share of our current accepted
clips would have been reachable under a CC-only policy.

**Falsifier.** If CC-only yield is a small fraction, the answer is not "filter
early" but "record provenance and let the buyer decide", which is what Gate 0
already does.

**Cost.** ~$2 (search only).

**Provenance.** `YT_crawler` exposes CC as a first-class search facet while the
large curation pipelines treat licence as a downstream footnote (§7).

---

## Stage 1 · Screening — the frame look that rejects 77%

### Q-SCR1 · Is the screen over-rejecting? *(highest-value measurement in the repo)*

**Hypothesis.** The frame screen currently drops ~77% of what search finds
(62 of 80 over five live queries), almost all as "frames show exocentric
footage". Either that is the honest yield of web video, or three stills are too
thin an evidence base and we are throwing away good footage. We already know
this failure mode is real: an earlier activity rule rejected a genuine laundry
video 3 runs out of 3 because its three stills happened to show a cat and a
bookshelf.

**Measure.** Grow the calibration set from 19 candidates to ~50 across more task
families, label each by hand from the actual footage, and report the
**wrong-rejection rate** with a confidence interval. Then freeze the set as
`packages/screening/calibration/` so any change to the screen must re-derive
against it.

**Falsifier.** A wrong-rejection rate under ~5% means the screen is right and
the yield ceiling is genuinely low — which is itself a headline result, because
it caps every acceptance number the project can ever report.

**Cost.** ~$5–10 of looking, plus human labelling time.

### Q-SCR2 · Would keypoints beat asking a VLM about viewpoint?

**Hypothesis.** A pose model gives a cheaper and more consistent viewpoint
signal than a VLM reading stills: **a visible face means third-person; visible
wrist and finger keypoints near the camera mean egocentric manipulation.** These
are mechanical, per-frame, and free of prompt drift.

**Measure.** Run both on the Q-SCR1 calibration set of 50. Report agreement,
and the disagreement cases one at a time — those are the interesting ones.
Compare cost per candidate screened.

**Falsifier.** If keypoint detection is unreliable on compressed web video at
the frame rates we sample, or if it cannot distinguish "hands because
egocentric" from "hands because the camera is on a tripod facing someone", the
VLM stays.

**Cost.** ~$0 for the model, ~$5 for the paired VLM run.

**Provenance.** RynnVLA-001's curation stage (§8) — described in RELATED_WORK as
"the strongest external corroboration in this document": a different group
solving a different problem independently converged on our viewpoint gate and
hands gate. Worth noting they use it as *silent preprocessing*; we would keep
the cues in the manifest either way, because a delivered dataset has to defend
its inclusions.

### Q-SCR3 · Does the screen get better stills if we choose the frames?

**Hypothesis.** We sample stills at fixed offsets. Sampling where motion is
highest, or where the frame embedding scores highest for the task phrase, would
put the decisive moment in front of the model instead of a random second.

**Measure.** On the calibration set, compare wrong-rejection rate under fixed
sampling versus motion-peak sampling versus embedding-guided sampling.

**Falsifier.** No change in wrong-rejection rate. Note that "the stills look
better to me" is not the metric — the metric is decisions that flip.

**Cost.** ~$5 (re-screening one set three ways).

---

## Stage 2–3 · Acquire and index

### Q-ACQ1 · What does the 400-second video cost us that a 60-second cut would not?

**Hypothesis.** We index whole videos and then cut. Indexing is billed per
video-minute, so indexing the whole thing to use 22 seconds of it is the
single largest avoidable line in the bill.

**Measure.** Over accepted clips, compute indexed minutes against usable
seconds delivered. That ratio is the waste multiple. Then test whether a
subtitle- or embedding-guided pre-cut (Q-SRC3) could have bounded the region
before indexing, and what it would have cost in missed spans.

**Falsifier.** If pre-cutting misses the action often enough that we re-fetch,
the whole-video index is cheaper than it looks.

**Cost.** ~$0 to compute from existing records.

---

## Stage 4 · Clean and segment — where the boundaries come from

### Q-SEG1 · Can natural-language binary search hit the boundary we cannot?

**Hypothesis.** Keyframe-aligned cuts drift: a requested 20.0 s span came back
22.0 s and 23.0 s, and the quality standard's G2-SEG asks for ±0.3 s, which
this mechanism cannot deliver. A **learning-free binary search over the
timeline** can: tile sampled frames into one image with frame-index labels, ask
a VLM which frame is closest to the action's start, narrow the window around
the answer, repeat.

**Measure.** Implement over ~10 spans we have hand-checked. Report the offset
distribution against hand-marked boundaries, and the number of VLM calls per
boundary. Compare against the current cut's drift, which must be measured over
the same 10 spans first (open question 3 in the README).

**Falsifier.** If it converges no closer than the keyframe grid, or costs more
per boundary than the span is worth, then the honest answer is to **state the
achievable tolerance in the report and stop promising ±0.3 s** — which is a
valid outcome, not a failure.

**Cost.** ~$3–5.

**Provenance.** Microsoft's VLM-Video-Action-Localization (§10). Its authors
state plainly that it does not surpass model-based approaches — which is exactly
why it is the right thing to try first: zero training cost, no labelled data, so
it sets the floor any trained localiser must clear before it earns its
complexity.

### Q-SEG2 · A four-second floor and an explicit "not an action" class

**Hypothesis.** Two cheap refusals would raise mean quality more than any
scoring change: discard segments under 4 seconds, and give the annotator an
explicit `N/A` class for non-action content instead of forcing a label.

**Measure.** Re-score existing accepted clips with a 4 s floor applied. Report
how many anchors disappear and what happens to anchors-per-usable-hour. For
`N/A`, measure what share of spans the annotator currently labels with something
vacuous.

**Falsifier.** If almost no anchors are under 4 s, the floor is a no-op here and
only matters at Action100M's scale.

**Cost.** ~$0 for the floor (re-score from records); ~$2 for the `N/A` test.

**Provenance.** Action100M (§10) discards sub-4 s segments and marks ~3.23% of
segments `N/A`. RELATED_WORK's reading: both are ways of *refusing to label
rather than labelling badly*, which is the same instinct as excluding unmeasured
checks from the score.

---

## Stage 5 · Annotate — the binding constraint

Annotation depth is 45 of the 100 points and currently sits near zero: a real
clip scored 25/100 with `annotations: 0` after the agent read three spans and
returned nothing, landing at L0 where L2 is the minimum trainable depth. **No
other change in this file can lift the grade distribution while this holds.**

### Q-ANN1 · Why does the agent read spans and return no labels?

**Hypothesis.** Unknown, and that is the problem — this is a diagnosis before it
is an improvement. Candidates: the reads come back empty; the model returns
prose the parser drops; a confidence threshold rejects everything; the tool
contract is wrong in the way `wait_for_operation(timeout=)` was wrong, failing
silently inside its own `except`.

**Measure.** Instrument one real clip end to end and record, per span: what the
read returned, what the model replied verbatim, and what the parser did with it.
Do not guess from the outside — the last two bugs of this shape were both
invisible from outside and obvious from the trace.

**Falsifier.** n/a — this is a measurement, not a change. It cannot fail, it can
only be informative.

**Cost.** ~$0.50.

### Q-ANN2 · Widen the panel instead of dropping the clip

**Hypothesis.** Low annotator confidence is a reason to **ask more annotators**,
not to discard the span. Several teachers propose, an adjudicator selects.

**Measure.** On 10 spans the single annotator currently fails to label, run three
differently-prompted annotators (spatial detail from mid-frames; temporal
dynamics at span level; transcript-grounded) and adjudicate. Report label yield
and hand-judged label quality against the single-annotator baseline.

**Falsifier.** If the three fail on the same spans for the same reason, the
problem is upstream — the span itself is not an action — and the fix belongs to
Q-SEG2's `N/A` class instead.

**Cost.** ~$5.

**Provenance.** Panda-70M (§3, §10). Its most instructive result is negative:
**no single captioner produced a good caption for more than ~35% of videos,
while the union of teachers covered 88.8%.** If that ratio holds even loosely
here, single-annotator yield is the whole bug. Note the design is
select-don't-generate — a trained retrieval model picks among candidates,
supervised by a small human preference set; our equivalent of that supervision
is the validation set.

### Q-ANN3 · Does hierarchical clustering beat our anchor proposals?

**Hypothesis.** We propose anchors from caption segments and frame search.
Frame representations over overlapping windows, clustered agglomeratively, give
temporally coherent segments at several scales at once — which is the same
task → action → event tree we already want.

**Measure.** On 5 clips, compare cluster-proposed segments against our anchors
against hand-marked ground truth. Report boundary agreement and count.

**Falsifier.** Our anchors already agree with ground truth as well as clustering
does, at lower cost.

**Cost.** ~$2, plus compute.

**Provenance.** Action100M's stage 1 (§10): V-JEPA 2 features over 64-frame
windows at 8-frame stride, then hierarchical agglomerative clustering. The
bearing noted in RELATED_WORK is that their three-level hierarchy is the same
shape as ours "at a scale that proves the shape survives full automation".

---

## Stage 6 · Grade

### Q-GRD1 · A per-clip score cannot reach A. Should the scorecard stop implying it can?

**Hypothesis.** Gate 3's 25 points are dataset-level and uncreditable to a
single clip, so a per-clip score caps at 75 while grade A needs 85. Every
per-clip A/B share we report is therefore measuring against an unreachable
ceiling.

**Measure.** Nothing to measure — this is arithmetic, and it is already
confirmed.

**Decision, not an experiment.** This is Shawn's call, and the loop must not
"fix" it by moving a threshold. The three coherent options: report A/B at the
dataset level only; define a per-clip band set that tops out at 75; or credit
Gate 3 per clip against the batch it shipped in. Until he chooses, the report
must state the cap plainly so no reader mistakes 0% A for a quality finding.

### Q-GRD2 · Is our own quality standard internally consistent?

**Hypothesis.** Section 6 of the scorecard — "where the pipeline contradicts the
standard" — is the highest-yield check we have. It already caught `_regrade`
keeping `accepted=true` on clips it re-graded to D. There are probably more.

**Measure.** Enumerate every place a decision is derived in two locations, and
assert in a test that they agree. The acceptance rule was one. Prime suspects:
the annotation-level ladder, the idle-time definition, and the hand-ratio
threshold.

**Falsifier.** No duplicated derivations remain. (Unlikely.)

**Cost.** $0, offline.

---

## Stage 7–8 · Refine, store and the library

### Q-REF1 · Near-duplicate detection before we pay to store duplicates

**Hypothesis.** Cutting overlapping spans from one source produces
near-duplicates that inflate delivered hours and hurt Gate 3 diversity.

**Measure.** Cut deliberately overlapping spans from one source, then measure
whether `frame_embedding` search separates them from genuinely distinct clips.
Establish the separation *before* writing any dedup code — a dedup threshold
nobody measured is a guess with a decimal point.

**Falsifier.** Embeddings do not separate overlap from similarity, in which case
dedup has to be structural (source id plus span overlap) rather than semantic —
which is cheaper anyway.

**Cost.** ~$1.

### Q-LIB1 · Does the library answer the question a buyer actually asks?

**Hypothesis.** The library searches titles, action labels and narrations. A
buyer asks "how many hours of two-handed tool use in a kitchen, licensed for
commercial use". That is a facet query over the tree, and we have the rows for
it.

**Measure.** Write down five questions a buyer would ask, then try to answer
each from the UI. Count how many need a hand-written SQL query instead. That
count is the backlog.

**Falsifier.** All five are answerable, in which case stop adding facets.

**Cost.** $0.

---

## Cross-cutting

### Q-X1 · Cassette replay for the agents

**Hypothesis.** The loop's iteration speed is bounded by whether it can test the
labelling agents offline. Recorded `FrameSource` / `MomentReader` cassettes
would make agent changes testable with no spend and no network — which changes
what every other question in this file costs to answer.

**Measure.** Time to test one annotation-agent change, before and after.

**Falsifier.** None; this is infrastructure. Its risk is different: a cassette
that drifts from the live contract is worse than no cassette, so recording must
be re-runnable against the real API.

**Cost.** $0 offline, ~$1 to record.

### Q-X2 · Five per cent chosen well beats a hundred chosen randomly

**Hypothesis, external.** Selection is the whole game: mining under 5% of a
32 M-sample egocentric pool raised VLA success from 47.7% to 61.1% against a
baseline trained on an equal quantity of *randomly sampled* human data — 13.4
points from selection alone, at a twentieth of the data.

**Bearing.** This is the empirical case for the project's premise, and it
reframes what we deliver: not hours, but **the argument for why these hours**.
The manifest, the viewpoint evidence and the quality gates are that argument. It
also means a low acceptance rate is not obviously bad news — a pipeline that
rejects 95% and defends the 5% is the pipeline the result endorses.

**Measure.** Not directly measurable here without training a VLA. What we can
do is make sure every rejection is *recorded with its reason*, so the selection
argument is reconstructible. Check: can we produce, for any accepted clip, the
full list of what was rejected alongside it and why?

**Provenance.** SiMDex, arXiv 2608.04196 (§3) — described in RELATED_WORK as
"the most direct intellectual neighbour to this project, arrived at from the
other end of the pipe".

### Q-X3 · Where does the money actually go?

**Hypothesis.** We attribute cost per clip and per grade, but the largest line
may be spend on queries that yielded nothing — $2.01 of $2.01 in the 40-query
dry run, and $0.08 of $1.25 in the five-query live sample.

**Measure.** Track stranded discovery spend as a first-class metric over the
full run, split by difficulty. If hard queries strand most of their spend, the
scheduler should stop early on them rather than paying the full screen.

**Falsifier.** Stranded spend is a small share once collection dominates.

**Cost.** $0 from existing records.
