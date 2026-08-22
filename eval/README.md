# Performance metrics — the eval set and the scorecard

The QA sweep (`qa/run_qa.py`) proves the deployment still behaves. The
whole-pipeline run (`qa/run_pipeline.py`) proves five task queries produce a set
the audit accepts. Neither answers the question this directory exists for:

> Of the footage this pipeline finds, how much is usable — and what did a clip
> of each quality grade cost to get?

That is three numbers, and they are the three the annotation-pipeline page says
any batch has to be able to answer. This directory produces them.

```
eval/
  README.md              ← what everything means (this file)
  task_map.csv           ← the controlled vocabulary, 1,965 canonical tasks
  queries.json           ← the frozen eval set, v1.0, 200 queries
  build_query_set.py     ← rebuilds queries.json from task_map.csv
  run_eval.py            ← runs the set through the pipeline, writes a scorecard
  publish.py             ← the eight-hourly job: run, report, commit, push
  sample-scorecard.md    ← a real scorecard, so the shape is visible without spending
  history.jsonl          ← one line per recurring run, append-only: the trend
  REPORT.md              ← the latest report
  reports/               ← every dated report
  results/               ← raw run records (git-ignored)
```

The parts worth testing live in `src/video_searching_agent/evaluation/`:
`task_map.py` (the vocabulary and the sampling), `runner.py` (driving the
deployment), `metrics.py` (the arithmetic), `scorecard.py` (the rendering) and
`report.py` (the trend). 95 tests cover them.

---

## 1. Quick start

```bash
# Free: what the search finds, and what discovery costs. No downloads.
python eval/run_eval.py --dry-run --limit 40

# ~$1: two queries, one clip each, end to end. Start here.
python eval/run_eval.py --limit 2 --per-query 1 --yes

# One slice of the set
python eval/run_eval.py --difficulty easy --limit 20 --yes
python eval/run_eval.py --family laundry --yes

# The whole frozen set. Hours, and roughly $60-120.
python eval/run_eval.py --yes --out eval/results/v1.0-full.jsonl

# Resume an interrupted run, or re-score a finished one for free
python eval/run_eval.py --resume eval/results/v1.0-full.jsonl --yes
python eval/run_eval.py --score-only eval/results/v1.0-full.jsonl
```

Each query is written to the run's `.jsonl` as it finishes, so an interruption
costs the time and not the money. `--score-only` recomputes a scorecard from
that record, which means a change to the metrics can be applied to a run that
already happened.

`QA_DEPLOYMENT` selects the deployment; it defaults to the Vercel one.

---

## 2. What A, B, C and D mean

Straight from the quality standard's 100-point scorecard (§7), and implemented
in `curation/quality_gates.py` — this eval does not define its own grades, it
reports the ones the pipeline already assigns.

The 100 points:

| Dimension | Weight | Scored on |
| --- | --- | --- |
| Annotation depth and quality (Gate 2) | **45** | the L grade, 30 pts (L0=0 · L1=10 · L2=22 · L3=30) + per-layer thresholds, 15 pts |
| Diversity and deduplication (Gate 3) | **25** | 4 pts per axis (people / sites / tasks / execution) + 9 for dedup and coverage |
| Media quality (Gate 1) | **20** | resolution 5 · wearer's own hands in frame + glove fit 7 · nobody else's hands or face 4 · shake, exposure, integrity, sync 4 |
| Licensability and provenance | **10** | commercially usable + sublicensable + complete provenance = 10 · research-only = 3 · provenance gaps = 0 |

And the bands, which are dispositions rather than adjectives — this is why a
single "we produced 1,000 clips" number means nothing until it is split:

| Grade | Score | What it may be used for |
| --- | --- | --- |
| **A** | ≥ 85 | Main training set, **and sellable externally** |
| **B** | 70–84 | Main training set, not yet external |
| **C** | 55–69 | Pretrain / scene-diversity supplement only — **must not count toward high-quality hours** |
| **D** | < 55 | Not ingested |

Gate 0 (rights: licence, consent, PII, jurisdiction, provenance) is not scored.
It is a veto: a clip that fails it is worth zero no matter what the other 100
points say, and shows up as a blocking failure rather than a low score.

Two things follow, and both are reported separately:

* **"Accepted"** means the gates let a clip through. **"High quality"** means
  accepted *and* an A or a B, because the standard says a C may not be counted
  as high-quality hours. The gap between the two rates is the interesting
  number.
* **Gate 3 is scored per dataset, not per clip**, so its 25 points cannot be
  earned by any single clip. Per-clip scores are therefore bounded below 100 by
  construction, and a run of C-grade clips is not automatically a bad run — read
  the band shares, not the absolute scores.

### Annotation depth L0–L3

The 45-point dimension, because "raw pixels are no longer scarce — what is
scarce is annotation":

| Level | Contains | Standing |
| --- | --- | --- |
| **L0** | metadata only | raw material; no commercial premium |
| **L1** | one clip-level caption or coarse label | transitional |
| **L2** | task → action narration hierarchy, own text per level, time anchors, verb-object action labels | **the minimum that is trainable and presentable externally** |
| **L3** | plus object and hand boxes, contact / grasp state, event-level detail, explicit error and rework samples | **the grade sold externally** |

The scorecard reports the L-level histogram inside each band, and flags an
accepted clip below L2 as a contradiction (§5).

---

## 3. The metrics

### 3.1 Yield — where the funnel loses things

Every step is reported as a count next to the ratio it makes with the step
before it, because a percentage without its denominator hides which claim is
being made.

| Metric | Definition |
| --- | --- |
| `candidates` | clips the search returned for a query |
| `attempted` | of those, the ones we tried to collect (capped by `--per-query`) |
| `indexed` | reached the Datalake — survived download, upload and index |
| `index_rate` | `indexed / attempted` |
| `graded` | clips the gates returned a verdict for |
| `accepted` | clips that passed Gate 0 + 1 + 2 |
| **`acceptance_rate`** | `accepted / graded` — the "usable share" number |
| **`high_quality_rate`** | A-or-B clips `/ graded` |
| `query_success_rate` | queries that produced at least one accepted clip |
| `delivered_hours` | duration of everything that reached us |
| `usable_hours` | Gate 0 + 1 passed, idle removed — the standard's `accepted_hours` |
| **`usable_time_ratio`** | `usable_hours / delivered_hours` — the "effective time" number |
| `action_anchors` | action-level narration anchors produced |
| `anchors_per_accepted_clip` | how many labelled spans one accepted video yields |
| `anchors_per_usable_hour` | the same, per hour |

On anchors rather than clips: the standard is explicit that **no clips are
delivered** (`G2-TREE-5`). One video file stays one video file; the hierarchy
lives in `[start_s, end_s]` anchors inside the annotation. So where a request
says "1,000 clips", the number that exists is 1,000 *action anchors* across
however many videos, and that is what `action_anchors` counts.

### 3.2 Cost

Four measured terms. The rates live in `curation/cost.py`, from the published
Datalake price list, and a run is recorded in billable *units* rather than
dollars so it can be re-costed when the price list changes.

| Term | How it is measured |
| --- | --- |
| discovery | the search reports its own spend — model tokens plus per-call search and scrape fees |
| indexing | video-minutes × $0.05 (the dominant term: $3.00 per hour at fps 1.0) |
| annotation | one moment search per video + one moment read per shortlisted span, $0.008 each |
| derived reads | caption, transcription and summary read back per clip, $0.001 each |
| looking | frame examination, which the agents report themselves |

Then the same total, split by grade, two different ways — and the difference
between them matters:

* **`$ attributed`** — every dollar lands on exactly one clip: its own indexing
  and annotation, plus a pro-rata share of its query's discovery spend. The
  band column sums to the run total, less stranded spend. Use this to ask where
  the money went.
* **`$ to obtain one`** — the whole run divided by that band's clip count.
  Answers "if A-grade footage is all we wanted, what did each one cost?", which
  is the number that matters when deciding whether to run the pipeline at all.
  It deliberately does **not** sum across bands.

**Stranded spend.** A query that returns nothing has still paid for its search.
That spend belongs to no clip, so it is held in `stranded_discovery_usd` and
still counted in the total. Dropping it would make a run that failed half its
queries look cheaper per clip than one that succeeded on all of them.

### 3.3 Stratification

Scored per difficulty tier and per task family, worst acceptance first — the
eval spec's rule is that a batch green on easy and red on hard is a fail
overall, and an average hides exactly that.

---

## 4. Where the queries come from

The quality standard is blunt: *"Task names must come from the robotics
downstream task map; inventing them is not allowed"* (`G2-HIER`, §9 `task_id`).
So the eval queries are drawn, not written.

**Source.** *Robotics downstream task map — controlled vocabulary*, owner Yunze
Liu, the deliverable of open item 6 on the quality-standard page:
[Google Sheet](https://docs.google.com/spreadsheets/d/1mRYvC6fnVCoICTwl6JXVXkYfJ5tHoJgO/edit).
Retrieved 2026-08-22: 1,965 canonical tasks, each with an `RDT-#####` id, an
instruction template, a domain, a task family and a granularity.
`eval/task_map.csv` is the six columns this repository uses. The sheet is the
authority; the CSV is a copy, and re-copying it is a diff.

**From 1,965 rows to 200 queries**, in three steps, each of which is a judgement
and is reported in `queries.json` under `sampling` rather than applied silently:

1. **Filmable by a person** — 1,716 of 1,965 survive. The vocabulary also covers
   robot benchmarks, and those are dropped by rule: whole domains (quadruped
   locomotion, embodied navigation), families that are language-grounding or
   reasoning probes, instructions naming a rig or a goal image or a benchmark
   difficulty level, and instructions with unfilled slots (`[*vegetables*]`) or
   a referent that never got filled in. The per-rule counts are in
   `sampling.pool.dropped`.

2. **Families normalised.** The family column is not yet internally consistent —
   `Cleaning`, `Cleaning & Hygiene` and `Cleaning & Surface Treatment` are one
   family; `Pick and place` and `Pick–Place & Transport` are another. Aliases
   collapse them in `task_map.py`. The sheet is not edited: the normalisation
   lives in the consumer, where it is tested.

3. **Stratified, coverage-first.** Difficulty follows the eval spec's 20/50/30
   target — 40 easy, 100 medium, 60 hard — mapped from granularity (primitive
   and atomic → easy, composite and benchmark → medium, long-horizon → hard),
   which is the closest honest proxy the map carries. Within a tier the draw is
   round-robin across families, smallest first. That is deliberate: family sizes
   in the vocabulary reflect which benchmarks were harvested, not which footage
   is worth having, so weighting by them would be weighting by an accident. 200
   queries reach 25 families.

**Instruction → query.** `Assemble the cabinet.` is an instruction to a robot;
`someone assembling the cabinet` is what a person looking for footage types. The
conversion is mechanical, and stays mechanical because a model rewriting 200
queries would make the set unreproducible: the leading verb becomes a gerund,
multi-sentence and scene-description instructions fall back to the canonical
task name, and anything still too long is cut at its first clause.
`task_instruction` keeps the canonical wording verbatim, so every query stays
traceable to its `RDT` id.

**Frozen.** `eval/queries.json` is v1.0 and rebuilds byte-for-byte —
`build_query_set.py --check` is the CI guard, and a test asserts it. Two
scorecards are only comparable if they ran the same set, which is the eval
spec's own rule (§9). Changing the sampling means a version bump and a note,
not a quiet rebuild.

`sampling.review` lists queries whose gerund was formed from a word the map does
not use as a verb. It is a look-at-these list, not an error: most entries are
correct and it exists so a resize cannot quietly introduce a query like
"someone cheesying bread".

---

## 5. The recurring report

```bash
python eval/publish.py --yes            # run, report, commit, push to main
python eval/publish.py --yes --no-push  # everything but the push
python eval/publish.py --from eval/results/run-3.jsonl   # publish a finished run, free
python eval/publish.py --slice all --yes                 # the full 200
```

**Every eight hours**, against whatever is deployed. Each tick runs the `core`
slice, scores it, appends `history.jsonl`, writes a dated report to `reports/`,
copies it to `REPORT.md`, rewrites the metrics block in the top-level README, and
pushes the four report paths to `main`. It refuses to run on a dirty tree or a
branch behind `origin/main`.

### Why a 12-query slice

The full set is hours and $60–120. Three times a day is $180–360 daily, which is
not a price worth paying to watch a number move. So the recurring run uses the
`core` slice — 12 queries marked `"core": true` in `queries.json`, four per
difficulty tier, spread across families, drawn at a stride through the set rather
than off its head (the low `RDT` ids are the robot-benchmark rows the vocabulary
was seeded from, so the first four of any tier are the four least footage-like
queries in it). About $6 a tick.

The slice is **fixed, not rotating**. A rotating slice would confound "the
pipeline changed" with "the queries changed", which is the one thing a trend line
must not do.

### What that costs in resolution, and what the report does about it

Twelve clips put a **±25-point** 95% interval around an acceptance rate. A tick
cannot resolve a small improvement, and a report that printed `58%` as though it
could would be worse than no report. So:

* every rate is printed with its **Wilson interval** and its **denominator**;
* next to a **rolling nine-tick window** — about three days, a hundred-odd clips,
  roughly ±9 points — which is where a real change first shows;
* windows **sum counts, never average rates**, so a 2-clip tick does not weigh as
  much as a 100-clip one;
* every comparison is drawn from ticks that ran **the same slice** — a
  `--slice all` run starts its own lineage rather than being pooled into the core
  one;
* and the caveat is in the report, in words, every time.

The number to quote externally is a full 200-query run. The tick is for noticing.

### What each snapshot records

The pipeline under test is a *deployment*, not this checkout, and the two
settings that most move yield and cost — the model, and how hard it looks before
downloading — change without a commit. So every snapshot carries the
deployment's own `/health` payload (`version`, `model`, `viewpoint_check`,
`max_collect_urls`) alongside the harness commit. A step in the trend with
nothing behind it is unattributable, which makes it useless.

`history.jsonl` is append-only and committed. A trend that lives in a build
artifact is a trend nobody looks at.

---

## 6. What the scorecard also reports

**Contradictions.** An eval that only totals up what the pipeline says about
itself is a self-report. So the scorecard checks the pipeline's verdicts against
the standard's text and names the disagreements: a clip accepted while graded D
("not ingested"), accepted while carrying a blocking gate failure (a veto is not
a deduction), or accepted below L2 (the minimum trainable depth). The first live
run found one of these immediately — an accepted clip scoring 52. That is a
finding about the pipeline, not a bug in the harness, and it is reported rather
than smoothed over.

**What was not measured.** Printed at the bottom of every scorecard, in words,
because a cost table with a missing term looks exactly like a complete one:

* curation, cleaning and narration model tokens — not reported over the pipeline
  API (the frame-examination spend inside them *is*, and is counted)
* download egress and disk — $0 on owned infrastructure, not billed per run
* Gate 3 diversity and dedup — scored per dataset, not per clip
* human ground truth — boundary F1 at ±0.3 s, caption 5-scale, action-label
  accuracy, Fleiss κ. These are the eval spec's Track A metrics and they need
  annotators, not a script. This harness measures what the pipeline produced and
  what it cost; it does not check the narration against a human's.

That last one is the boundary of this directory. It scores the pipeline against
the gates. Scoring the gates against people is the human-annotated eval set, and
that is a different piece of work.
