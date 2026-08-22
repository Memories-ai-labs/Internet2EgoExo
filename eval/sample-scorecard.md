# Sample scorecard — two queries, one clip each

*A real run, kept in the repository so the shape of the output is visible
without spending anything. Two queries (`someone folding cloth`, `someone doing
laundry`), one clip each, against the Vercel deployment on 2026-08-22. It is a
smoke test, not a result: two clips say nothing about the pipeline's yield, and
§6 is the interesting part.*

Eval set `v1.0` · 2 queries run

## 1. Yield — where the funnel loses things

| step | count | of the step before |
| --- | --- | --- |
| queries asked | 2 | — |
| queries that found candidates | 2 | 100% |
| candidates found | 10 | — |
| candidates we tried to collect | 2 | 20% |
| reached the Datalake | 2 | 100% |
| graded by the gates | 2 | 100% |
| **accepted** | **1** | **50%** |
| of those, an A or a B | 0 | 0% |
| queries with at least one accepted clip | 1 | 50% |

| time and anchors | value |
| --- | --- |
| delivered hours (what reached us) | 0.32 |
| usable hours (Gate 0+1, idle removed) | 0.30 |
| usable time ratio | 95% |
| idle hours, explicitly marked | 0.02 |
| action anchors produced | 22 |
| anchors per accepted clip | 6.0 |
| anchors per usable hour | 72.4 |

## 2. Grade bands — the same output, split four ways

| grade | clips | share | usable h | anchors | $ attributed | $/clip | $/usable h | $ to obtain one |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** | 0 | 0% | 0.00 | 0 | $0.00 | — | — | — |
| **B** | 0 | 0% | 0.00 | 0 | $0.00 | — | — | — |
| **C** | 0 | 0% | 0.00 | 0 | $0.00 | — | — | — |
| **D** | 2 | 100% | 0.30 | 22 | $1.09 | $0.54 | $3.57 | $0.54 |

`$ attributed` splits the run so every dollar lands on one clip; the column sums to the run total less stranded discovery spend. `$ to obtain one` is the whole run divided by that band's clips — it answers "if this grade is all we wanted, what did each one cost", and deliberately does not sum.

| grade | what the standard allows |
| --- | --- |
| A | score >=85 — main training set, and sellable externally |
| B | score 70-84 — main training set, not yet external |
| C | score 55-69 — pretrain / scene-diversity only; not high-quality hours |
| D | score <55 — not ingested |

## 3. Cost

| term | USD |
| --- | --- |
| discovery (measured: model + search tools) | $0.06 |
| indexing (Datalake, per video-minute) | $0.96 |
| annotation (moment search + read per anchor) | $0.06 |
| derived reads (caption / transcription / summary) | $0.0060 |
| looking at frames (measured by the agents) | $0.0000 |
| **total** | **$1.09** |
| of which paid for queries that yielded nothing | $0.00 |

Cost per usable hour delivered: **$3.57/h**. Cost per accepted clip: **$1.09**. Cost per A-or-B clip: **—**.

## 4. By difficulty

| stratum | queries | graded | accepted | A+B | usable h | $/accepted clip |
| --- | --- | --- | --- | --- | --- | --- |
| medium | 1 | 1 | 0 (0%) | 0 (0%) | 0.19 | — |
| hard | 1 | 1 | 1 (100%) | 0 (0%) | 0.12 | $0.44 |

## 5. By task family — worst acceptance first

| stratum | queries | graded | accepted | A+B | usable h | $/accepted clip |
| --- | --- | --- | --- | --- | --- | --- |
| Deformable Object Manipulation | 1 | 1 | 0 (0%) | 0 (0%) | 0.19 | — |
| Laundry & Clothing Care | 1 | 1 | 1 (100%) | 0 (0%) | 0.12 | $0.44 |

## 6. Where the pipeline contradicts the standard

* 1 accepted clip(s) graded D, which the standard says is not ingested: vid_anwuyaqa2sd36zlxnivub36lum

## 7. What this run did not measure

* curation, cleaning and narration model tokens — not reported over the pipeline API (the frame-examination spend inside them is, and is counted)
* download egress and disk — $0 on owned infrastructure, not billed per run
* Gate 3 diversity and dedup — scored per dataset, not per clip
* human ground truth (IAA, boundary F1, caption 5-scale) — needs annotators
