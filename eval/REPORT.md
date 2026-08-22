# Performance report — 2026-08-22T09:11:13Z

Eval set `v1.0` · `replayed:publish-20260822T083809Z.jsonl` slice · 10 queries · 5 clips graded

| what was measured | |
| --- | --- |
| deployment | https://internet-egoexo-video-search.vercel.app |
| build | version `0.1.0`, model `openrouter · google/gemini-3.7-flash`, viewpoint check `frames` |
| harness commit | `dedecbb95d9d` |
| spent | $0.86 |

## Headline

| metric | this run | 95% interval | previous | window (1 tick, 5 clips) |
| --- | --- | --- | --- | --- |
| survived the screen | — | — | — | — |
| acceptance rate | 0% (0/5) | 0%–43% | — | 0% |
| A or B share | 0% (0/5) | 0%–43% | — | 0% |
| usable time ratio | 95% | — | — | 95% |
| $ / usable hour | $9.11 | — | — | $9.11 |
| $ / accepted clip | — | — | — | — |

> The acceptance rate here is 0 of 5 clips, so its 95% interval spans 43 points. A change smaller than that is not visible in one tick — the rolling column is the one to read, and the full 200-query run is the number to quote.

## Grades

| grade | clips | $ to obtain one |
| --- | --- | --- |
| A | 0 | — |
| B | 0 | — |
| C | 0 | — |
| D | 5 | $0.17 |

## Trend

| ran at | slice | clips | accepted | A+B | usable h | $ | $/usable h |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-22T09:11:13Z | replayed:publish-20260822T083809Z.jsonl | 5 | 0 (0%) | 0 (0%) | 0.09 | $0.86 | $9.11 |

## Full scorecard


Eval set `v1.0` · 10 queries run

## 1. Yield — where the funnel loses things

| step | count | of the step before |
| --- | --- | --- |
| queries asked | 10 | — |
| queries that found candidates | 10 | 100% |
| videos the search found | 66 | — |
| survived the pre-download screen | 66 | 100% |
| candidates we tried to collect | 10 | 15% |
| reached the Datalake | 5 | 50% |
| graded by the gates | 5 | 100% |
| **accepted** | **0** | **0%** |
| of those, an A or a B | 0 | 0% |
| queries with at least one accepted clip | 0 | 0% |

| time and anchors | value |
| --- | --- |
| delivered hours (what reached us) | 0.10 |
| usable hours (Gate 0+1, idle removed) | 0.09 |
| usable time ratio | 95% |
| idle hours, explicitly marked | 0.01 |
| action anchors produced | 7 |
| anchors per accepted clip | 0.0 |
| anchors per usable hour | 74.5 |

## 2. Grade bands — the same output, split four ways

| grade | clips | share | usable h | anchors | $ attributed | $/clip | $/usable h | $ to obtain one |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** | 0 | 0% | 0.00 | 0 | $0.00 | — | — | — |
| **B** | 0 | 0% | 0.00 | 0 | $0.00 | — | — | — |
| **C** | 0 | 0% | 0.00 | 0 | $0.00 | — | — | — |
| **D** | 5 | 100% | 0.09 | 7 | $0.70 | $0.14 | $7.48 | $0.17 |

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
| discovery (measured: model + search tools) | $0.54 |
| indexing (Datalake, per video-minute) | $0.30 |
| annotation (moment search + read per anchor) | $0.00 |
| derived reads (caption / transcription / summary) | $0.0150 |
| looking at frames (measured by the agents) | $0.0000 |
| **total** | **$0.86** |
| of which paid for queries that yielded nothing | $0.15 |

Cost per usable hour delivered: **$9.11/h**. Cost per accepted clip: **—**. Cost per A-or-B clip: **—**.

## 4. By difficulty

| stratum | queries | graded | accepted | A+B | usable h | $/accepted clip |
| --- | --- | --- | --- | --- | --- | --- |
| easy | 4 | 3 | 0 (0%) | 0 (0%) | 0.09 | — |
| hard | 3 | 1 | 0 (0%) | 0 (0%) | 0.00 | — |
| medium | 3 | 1 | 0 (0%) | 0 (0%) | 0.01 | — |

## 5. By task family — worst acceptance first

| stratum | queries | graded | accepted | A+B | usable h | $/accepted clip |
| --- | --- | --- | --- | --- | --- | --- |
| Articulated Object Operation | 2 | 1 | 0 (0%) | 0 (0%) | 0.01 | — |
| Deformable Object Manipulation | 1 | 1 | 0 (0%) | 0 (0%) | 0.01 | — |
| Grasping & Lifting | 1 | 1 | 0 (0%) | 0 (0%) | 0.06 | — |
| Other | 1 | 1 | 0 (0%) | 0 (0%) | 0.02 | — |
| Shopping & Errands | 1 | 1 | 0 (0%) | 0 (0%) | 0.00 | — |
| Assembly & Fastening | 1 | 0 | 0 (—) | 0 (—) | 0.00 | — |
| Food & Beverage Preparation | 1 | 0 | 0 (—) | 0 (—) | 0.00 | — |
| Pouring, Filling & Scooping | 1 | 0 | 0 (—) | 0 (—) | 0.00 | — |
| Stacking & Arrangement | 1 | 0 | 0 (—) | 0 (—) | 0.00 | — |

## 6. Where the pipeline contradicts the standard

Nothing — every accepted clip is one the standard would accept.

## 7. What this run did not measure

* curation, cleaning and narration model tokens — not reported over the pipeline API (the frame-examination spend inside them is, and is counted)
* download egress and disk — $0 on owned infrastructure, not billed per run
* Gate 3 diversity and dedup — scored per dataset, not per clip
* human ground truth (IAA, boundary F1, caption 5-scale) — needs annotators

## 8. Queries that errored (5)

* rdt-00003-assemble-cabinet: nothing reached the Datalake: ['stopped at downloading']
* rdt-00098-kitchen-sequence: nothing reached the Datalake: ['stopped at downloading']
* rdt-00207-pick-up-the-book-in-the-middle-and-place: nothing reached the Datalake: ['POST /videos (multipart) returned 402: {"error":{"code":"quota_exceeded","message":"insuff']
* rdt-00448-stack-pyramid: nothing reached the Datalake: ['POST /videos (multipart) returned 402: {"error":{"code":"quota_exceeded","message":"insuff']
* rdt-00522-water-plants: nothing reached the Datalake: ['stopped at downloading']
