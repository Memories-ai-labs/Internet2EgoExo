# Related Work

This project is not a model and not a dataset. It is the step in between: a way to
turn the open internet into **ego/exo training footage that a team can actually
use** — viewpoint-labelled, licence-checked, hands-verified, annotated to a
task → action → event tree, and priced per delivered hour.

That framing is what separates it from most of the literature it sits next to.
Almost everything below either *commissions* footage, or *consumes* a corpus
somebody else already owns. Very little of it is about acquisition against a
stated requirement.

The document has two halves:

- **[Part I — The literature](#part-i--the-literature)**: the datasets and
  systems this work is positioned against.
- **[Part II — The open-source pipeline](#part-ii--the-open-source-pipeline)**:
  stage by stage, what already exists in code for crawl → viewpoint → clip →
  annotate, what is safe to reuse, and what has to be built. Including the two
  findings that change the build decision: the licence trap under the best 4D
  pipeline, and ten thousand hours of factory egocentric video given away under
  Apache 2.0.

---

# Part I — The literature

## 1. Commissioned egocentric and ego–exo capture

The reference datasets in this space are staged captures: recruited
participants, consented sites, a fixed activity taxonomy, and an annotation
budget spent up front.

| Dataset | Scale | What it fixes in place |
|---|---|---|
| [EPIC-KITCHENS-100](https://arxiv.org/abs/1804.02748) | ~100 h, 45 kitchens, ~90 k action clips | One domain, head-mounted, dense action labels |
| [Ego4D](https://ego4d-data.org/) | 3,670+ h daily-life egocentric | Breadth of everyday activity, benchmark suite |
| [Ego-Exo4D](https://arxiv.org/abs/2311.18259) (CVPR 2024) | 1,286 h, 740 participants, 13 cities, 123 scenes, 200 k+ annotator hours | *Simultaneous* ego + multi-exo of skilled activity |
| [EgoExoLearn](https://github.com/OpenGVLab/EgoExoLearn) (CVPR 2024) | 120 h + gaze | Demonstration-following: exo demo → ego execution |
| [HOI4D](https://arxiv.org/pdf/2404.09933) | 2.4 M RGB-D frames, 4,000 sequences, 610 rooms | Category-level hand–object interaction with 4D labels |
| [ENIGMA-360](https://arxiv.org/pdf/2603.09741) | industrial ego-exo | Ego–exo behaviour in an industrial setting |

**What we take from it.** Ego-Exo4D is the clearest statement of why the two
viewpoints are worth pairing at all, and its annotation depth is the bar that
the `L0–L3` annotation gates in this repo are written against.

**Where we differ.** Commissioned capture buys control and pays for it in cost
and coverage: you get exactly the 123 scenes you funded. This system inverts the
trade — the footage already exists, so the money goes into *verification*
(viewpoint classification with cited cues, the hands gate, licence checks)
rather than into recording. The failure modes are correspondingly different:
a staged dataset never has a licence problem and never has to prove a clip is
first-person; ours has to prove both, per clip, with evidence.

---

## 2. Scaling human video for robot learning

The current wave treats human video as a substitute for robot data, and the
scaling numbers have moved fast.

- **[EgoDex](https://arxiv.org/html/2505.11709v1)** — 829 h, 338 k demonstrations
  across 194 tabletop tasks, captured on Apple Vision Pro with SE(3) annotations
  for both hands. The cleanest argument that *hands* are the payload.
- **[EgoScale](https://rpl.cs.utexas.edu/publications/2026/02/18/zheng-arxiv26-egoscale/)** —
  a VLA trained on 20,854 h of action-labelled egocentric human video for
  dexterous transfer.
- **[HumanNet](https://arxiv.org/abs/2605.06747)** — a one-million-hour
  human-centric corpus spanning first- and third-person, with interaction-centric
  annotations (captions, motion descriptions, hand/body signals). Its headline
  result is the one that matters for a collection system: under fixed
  validation, continued training on **1,000 h of egocentric human video beat
  100 h of real-robot data**.
- **[Ego2Robot](https://arxiv.org/html/2608.02580)** — ego video → robot training
  data via action retargeting, robot-arm visual synthesis, and multi-level
  quality curation.
- **[From Human Videos to Robot Manipulation](https://arxiv.org/html/2606.00054v1)** —
  the survey that maps this whole cluster.

**Where we sit.** All of these start from a pool. This repo is the step before
the pool: given a requirement ("N hours of two-handed assembly, head-mounted,
reusable licence"), find the footage, prove it matches, and report what the
hour cost. HumanNet's result is the economic case for doing that work at all;
EgoDex's hand annotations are why the hands gate here has no override.

---

## 3. Selection is the hard part, not collection

The most directly comparable line of work is about *choosing* clips, because
undifferentiated hours stopped being the bottleneck.

- **[SiMDex](https://arxiv.org/abs/2608.04196)** — casts human-data selection as
  recommendation: a three-layer recall → rank → re-rank pipeline over ~32 M
  egocentric samples. Mining ~1.49 M samples (**<5 % of the pool**) beat an
  equal-size random draw. This is the same thesis as our usability ranking,
  reached from the other side of the pipe.
- **[Panda-70M](https://github.com/snap-research/Panda-70M)** (CVPR 2024) —
  70 M video–caption pairs from multi-teacher captioning. Its most useful finding
  is negative: **no single captioner produced a good caption for more than ~35 %
  of videos**, while an ensemble covered 88.8 %. Our annotation agent is an
  ensemble-of-evidence for the same reason.
- **[InternVid](https://arxiv.org/abs/2307.06942)** — 7 M videos → 234 M clips
  with LLM-generated descriptions; the template for LLM-in-the-loop corpus
  building.
- **[NVIDIA NeMo Curator](https://github.com/NVIDIA-NeMo/Curator)** and the
  Cosmos video pipeline — GPU-accelerated load/filter/dedupe/annotate at
  world-model scale; the Cosmos pipeline extracts ~100 M clips of 2–60 s from a
  20 M-hour collection.

**Where we differ.** Those are throughput-optimised heuristic filters over a
corpus the operator already holds. This system runs an *agentic* loop where each
verdict is a Thought → Action → Observation trace with the frames it looked at,
and where the decisive filters are asymmetric: a wrong-viewpoint clip or a clip
with no hands in frame is **dropped**, not ranked low. Throughput is not the
objective function; defensible hours are.

---

## 4. World-model and physical-AI stacks

- **[NVIDIA Cosmos](https://arxiv.org/abs/2501.03575)** — a platform of
  generative world foundation models with tokenizers, guardrails, Curator for
  data, Transfer for domain adaptation, and Reason/Evaluator for scoring. The
  2026 line (Cosmos 3, and the Physical AI Data Factory blueprint announced at
  GTC 2026) folds world modelling, multimodal understanding, action and
  reasoning into one family.

**Relationship.** Cosmos *generates and evaluates* data; this repo *sources*
it. They are complementary, and the seam is the interesting part: Cosmos Curator
presupposes a 20 M-hour archive. Internet2EgoExo is how a team without one gets
to its first defensible thousand hours — real, licensed, provenance-tracked —
which is exactly the input a synthetic-augmentation stack needs before it can
multiply anything.

---

## 5. Retrieval as the substrate — and the gap it leaves

Indexing footage once and querying it many times is the backbone of this
pipeline (`Memories.ai Video Datalake` tools in the README).

- **[OmniRetriever](https://arxiv.org/abs/2605.26641)** (Memories.ai Research) —
  any-to-any audio–video–text retrieval via fusion-as-teacher distillation, with
  a Tuple-InfoNCE term supervising the fused embedding. OmniRetriever-7B beats
  closed-source Gemini Embedding 2 by 13.3–18.0 R@1 on Clotho and SoundDescs.
- **[S-EMBER](https://arxiv.org/pdf/2607.02689)** — streaming egocentric memory
  retrieval, the benchmark form of the same problem.

**The gap this project fills.** "Any-to-any" is any-to-any *across modalities* —
text, video, audio. But the axes that decide whether a clip is usable **training
data** are not modalities:

| Decision axis | In the embedding space? |
|---|---|
| Egocentric vs. exocentric | No — must be asserted |
| Hands in frame | No — must be checked on frames |
| Licence / reuse rights | No — metadata, off-pixel |
| Usable clip length after trimming | No — a property of the cut |
| Provenance and consent posture | No — external record |

None of these fall out of a similarity search, however good the encoder. They
have to be **asserted by an agent, justified with evidence, and written back as
metadata** — which is what the viewpoint classifier, the hands gate, the
annotation tree and the four hour measures (worn / delivered / accepted /
accepted_labeled) exist to do. Retrieval finds candidates; it does not certify
them.

---

## 6. Rights, provenance and the licence problem

Web-mined video corpora typically ship URLs rather than pixels and leave reuse
rights to the downstream user. For training footage intended to be *delivered*
to someone, that is not sufficient. This repo filters Creative-Commons material
through the YouTube API at search time, records the licence per clip in the
manifest, and treats unmeasured rights checks as **excluded from the score
rather than assumed to pass** — the same posture the quality gates take
generally.

---

# Part II — The open-source pipeline

Part I is about what the literature *claims*. This part is about what is
downloadable. The chain this repo implements — crawl → decide viewpoint → clip →
annotate — exists in open source stage by stage, at a higher level of maturity
than most teams assume. What does *not* exist is the assembly, the requirement
layer on the front, and the rights discipline running through it.

## 7. Crawl: URL → video

| Project | What it gives you |
|---|---|
| [`iejMac/video2dataset`](https://github.com/iejMac/video2dataset) (LAION) | The de-facto standard. yt-dlp backend, clipping, scene detection, optical flow, FPS/resolution downsampling, webdataset out. Reported at 10 M videos in ~12 h. |
| [`LAION-AI/BVD`](https://github.com/LAION-AI/BVD) | ~1.3 B video URLs mined from CommonCrawl, ~80 M already downloaded (~10 M hours). The URL list, pre-made. |
| [`NotJoeMartinez/yt-fts`](https://github.com/NotJoeMartinez/yt-fts) | Channel subtitles into SQLite for full-text and semantic search, returning **timestamped** URLs. Finds the minute, not the video. |
| [`luc-pimentel/YT_crawler`](https://github.com/luc-pimentel/YT_crawler) | Keyword search with upload-date / duration / sort filters. |

**The gap.** `video2dataset` consumes a URL list; it does not search. There is no
authoritative open implementation of the keyword-search-to-URL-manifest layer —
teams glue yt-dlp search or a scraper to a parquet file and move on.

**That gap is stage 0 of this repo.** The multi-source search (YouTube API, Exa
neural search, Apify, the open web), the slot extraction that turns a sentence
into a query, and the volume goal that says when to stop are precisely the layer
the OSS chain leaves to the reader. Downstream of it, `video2dataset` remains the
sane choice for bulk fetch.

## 8. Viewpoint: the exo → ego question, answered three ways

This is where intuition misleads. **Generative exo → ego conversion does not work
at internet scale.** [`Exo2Ego-V`](https://github.com/showlab/Exo2Ego-V)
(NeurIPS 2024) requires **four synchronised 360°-surround exocentric views** to
synthesise the egocentric one. That is a capture-rig setting. YouTube does not
contain its input.

Two approaches do work:

**(a) Filter, don't convert.**
[`RynnVLA-001`](https://github.com/alibaba-damo-academy/RynnVLA-001)
([arXiv 2509.15212](https://arxiv.org/pdf/2509.15212), ICRA 2026) states the rule
plainly: run pose estimation per frame; **facial landmarks present → discard**
(a visible face strongly implies third-person); **wrist/hand keypoints present →
keep** (hands near the camera strongly imply egocentric manipulation). One pose
model turns a web crawl into an ego manipulation corpus.

This is independent corroboration of the two hardest rules in this repo — the
viewpoint gate and the hands gate — arrived at by a different group solving a
different problem. Where we differ: RynnVLA uses it as a silent preprocessing
filter, while here each verdict carries the cues behind it into the manifest,
because a delivered dataset has to defend its inclusions, not just make them.

**(b) Lift to 4D, then re-render any view.**
[`EgoInfinity`](https://github.com/Rice-RobotPI-Lab/EgoInfinity)
([arXiv 2606.17385](https://arxiv.org/abs/2606.17385), Rice University) is the
technically correct form of "third-person to first-person": not generating
pixels, but recovering geometry and reprojecting. A modular engine lifts
in-the-wild YouTube video into metric 4D hand–object interaction — hand
trajectories, 6-DoF object poses, contact states — then retargets to arbitrary
robot morphologies from arbitrary viewpoints. Reported at **142 M clips /
14.6 years** of video. The stack is off-the-shelf throughout (MoGe-2 for metric
depth, GeoCalib for gravity, YOLO + WiLoR for MANO hand reconstruction, MEMFOF
for flow, HaWoR for gap filling, SAM 3.1 / SAM2 / SAM 3D Objects for objects), it
runs from a CLI (`python -m egoinfinity process <clip_dir>`), and it ships an
`action100m_filter/` stage that pre-selects static-camera, visible-hands
candidates — the same job as our candidate filter, one level lower.

## 9. Clip

- [`Panda-70M`](https://github.com/snap-research/Panda-70M) `splitting/` —
  **PySceneDetect + ImageBind**, i.e. semantically coherent cuts rather than raw
  shot boundaries. Validated at 70.8 M clips, 720p, ~8.5 s mean.
- [`nvidia-cosmos/cosmos-curate`](https://github.com/nvidia-cosmos/cosmos-curate) —
  split, annotate, filter, dedupe, embed, emit dataset, on a Ray / cosmos-xenna
  distributed GPU pipeline. **Code is Apache 2.0** (models under the NVIDIA Open
  Model License). The only industrial-strength skeleton on offer, and the layer
  underneath the Cosmos platform discussed in §4.

## 10. Annotate

- **Panda-70M's three-stage design is the one to copy**, and the reason is
  subtle: multiple cross-modality teachers each produce a caption (video,
  subtitle, image), a small human-labelled set picks winners, and a retrieval
  model is trained to **select** the best caption at scale. Selection, not
  generation. This is the right treatment for a low-confidence annotation rate:
  a clip the primary annotator is unsure about is not discarded, it is put to a
  vote and adjudicated by retrieval.
- [`Action100M`](https://arxiv.org/html/2601.10592v1) — 100 M action instances
  from a fully automatic pipeline with **hierarchical open-vocabulary labels**
  (brief action → detailed action → caption). The same shape as this repo's
  task → action → event tree, at a scale that proves the shape survives
  automation.
- [VLM-Video-Action-Localization](https://microsoft.github.io/VLM-Video-Action-Localization/)
  (Microsoft) — **learning-free, open-vocabulary** temporal action localisation
  by iterative VLM querying. Zero training cost, which makes it the honest
  baseline any trained localiser has to beat.

## 11. The licence trap

This is the finding with the sharpest practical edge, and it is the reason a
"just use the open pipeline" plan can quietly become unshippable.

**EgoInfinity's own code is MIT. Its dependencies are not.** The repository says
so directly: *commercial use of the repo as a whole is restricted by the WiLoR
(CC-BY-NC-ND) and MANO (non-commercial) terms.*

| Component | Licence | Consequence |
|---|---|---|
| WiLoR (hand reconstruction) | CC-BY-NC-ND | Research only, **no derivatives** |
| Ultralytics YOLO (detection) | AGPL-3.0 | Network copyleft if served over a network |
| MANO (hand model) | Non-commercial research only | Registration-gated |
| SAM2 | Apache 2.0 | Fine |
| SAM 3.1 / SAM 3D Objects | Per upstream | Gated weights |
| MoGe-2 / GeoCalib / HaWoR / MEMFOF | Per upstream | Check individually |

Swapping the hand reconstructor and the detector is tractable engineering, but
it is engineering, and it belongs on the schedule rather than in the assumptions.

**Why this belongs in a Related Work document.** This repo already treats
licence as a first-class, per-clip field rather than a footnote — CC filtering at
search time, licence recorded in the manifest, unmeasured rights checks
*excluded* from the score rather than assumed to pass. §11 is the same
discipline pointed at the toolchain instead of the footage. A dataset assembled
by a non-commercial pipeline inherits the restriction no matter how clean the
clips are. Rights are a property of the *whole* provenance chain.

## 12. Free hours, and what they do to the moat

**Build AI released [Egocentric-10K](https://www.humanoidsdaily.com/news/build-ai-open-sources-10-000-hours-of-factory-worker-video-to-scale-robot-learning)
— 10,000 hours of real factory first-person video under Apache 2.0.**
1.08 B frames, **2,138 workers**, 16.4 TB, 1080p at 30 fps, WebDataset shards
with paired JSON metadata, streamable from Hugging Face without a full download.
Head-mounted, so hands, tools and workpieces are all in frame. It is the first
large egocentric set collected exclusively in real factories — Ego4D's 3,670 h
are daily life, not production lines.

There is already an annotation pipeline built on it:
[`fit-alessandro-berti/annotated-egocentric-10k-dataset`](https://github.com/fit-alessandro-berti/annotated-egocentric-10k-dataset)
(Apache 2.0) — transcribe → per-worker summary → per-factory summary →
**CSV event log constrained by a factory-specific vocabulary** → merged temporal
log. That last step is process mining, and it is the closest public analogue to
this repo's annotation tree.

**Three honest limits before anyone plans around it:** ten thousand hours is not
fifty thousand; a single-source corpus caps environment and process diversity;
and Apache 2.0 is a licence on the *data artefact* — it is not a warranty that
the portrait rights and consent chain for 2,138 identifiable workers have been
cleared for your use. That third one is exactly the sort of unmeasured check
this repo refuses to score as passing.

**The structural read.** This is the second time in short order that a large
egocentric corpus has been given away, and the pattern matters more than the
gift: **nominal hours are being commoditised**. A collection system whose value
proposition is "we can get you N hours" is building on ground that keeps
disappearing. What does not commoditise is whether an hour is *provably* the
right viewpoint, provably hands-visible, provably licensed, and annotated deeply
enough to train on. Retrieval proposes; pixels decide. The moat is in the
deciding.

## 13. Build vs. reuse, per stage

| Stage | Best open option | What this repo does |
|---|---|---|
| Requirement → query | *(none)* | Slot extraction, volume goals, binding-constraint reporting |
| Search → URL manifest | *(gap; ad-hoc)* | Multi-source: YouTube API, Exa, Apify, open web |
| Bulk fetch | `video2dataset`, LAION BVD | yt-dlp path, per-clip provenance retained |
| Viewpoint decision | RynnVLA-001 face/hand rule | Same rule, plus cited cues written to the manifest |
| Any-view / 4D | EgoInfinity (licence-encumbered) | Out of scope today; the upgrade path if deps are swapped |
| Clipping | Panda-70M `splitting/`, cosmos-curate | Agentic cleaning + clipping with frame-level evidence |
| Annotation | Panda-70M select-not-generate, Action100M | task → action → event tree, L0–L3 gates |
| Curation / scoring | cosmos-curate filters | Quality gates as code, four hour measures, cost per hour |
| Rights | *(mostly ignored)* | Licence per clip; unmeasured ⇒ excluded, not assumed |

The short version: **skeleton from `cosmos-curate`, clipping from Panda-70M,
viewpoint rule from RynnVLA-001, 4D as a later upgrade with the non-commercial
dependencies replaced — and the front and back of the chain, requirement in and
provenance out, are the parts that have to be built.**

---

## Positioning, in one table

| | Commissioned capture (Ego-Exo4D, EgoDex) | Web-scale corpora (Panda-70M, InternVid, HumanNet) | World-model stacks (Cosmos) | **Internet2EgoExo** |
|---|---|---|---|---|
| Where footage comes from | Recorded for the dataset | Scraped at scale, then filtered | Owned archive + synthesis | Searched on demand, per requirement |
| Selection signal | Protocol compliance | Heuristics, captionability | Dynamics / visual quality | Viewpoint → duration → licence |
| Wrong viewpoint | Cannot happen | Down-ranked | Not modelled | **Dropped** |
| No hands in frame | Rare by design | Kept | Kept | **Dropped, no override** |
| Rights | Consented at capture | Deferred to user | Owned | Filtered and recorded per clip |
| Unit of output | A dataset release | A corpus | Synthetic hours | A manifest + a cost per hour |
| Auditability | Annotation guidelines | Pipeline code | Evaluator scores | Per-clip Thought → Action → Observation trace |

---

## References

- Grauman et al. *Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives.* CVPR 2024. https://arxiv.org/abs/2311.18259
- Grauman et al. *Ego4D: Around the World in 3,000 Hours of Egocentric Video.* https://ego4d-data.org/
- Damen et al. *Scaling Egocentric Vision: The EPIC-KITCHENS Dataset.* https://arxiv.org/pdf/1804.02748
- Huang et al. *EgoExoLearn.* CVPR 2024. https://github.com/OpenGVLab/EgoExoLearn
- *EgoDex: Learning Dexterous Manipulation from Large-Scale Egocentric Video.* https://arxiv.org/html/2505.11709v1
- Deng, Zhou et al. *HumanNet: Scaling Human-centric Video Learning to One Million Hours.* https://arxiv.org/abs/2605.06747
- *EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data.* https://rpl.cs.utexas.edu/publications/2026/02/18/zheng-arxiv26-egoscale/
- *Ego2Robot: Scalable Robot Data Synthesis from Egocentric Human Data.* https://arxiv.org/html/2608.02580
- *From Human Videos to Robot Manipulation: A Survey on Scalable Vision-Language-Action Learning with Human-Centric Data.* https://arxiv.org/html/2606.00054v1
- *SiMDex: Mining Similar Egocentric Videos for Cross-Embodiment Dexterous Manipulation.* https://arxiv.org/abs/2608.04196
- Chen et al. *Panda-70M: Captioning 70M Videos with Multiple Cross-Modality Teachers.* CVPR 2024. https://github.com/snap-research/Panda-70M
- Wang et al. *InternVid.* https://arxiv.org/abs/2307.06942
- NVIDIA. *Cosmos World Foundation Model Platform for Physical AI.* https://arxiv.org/abs/2501.03575
- NVIDIA. *NeMo Curator.* https://github.com/NVIDIA-NeMo/Curator
- Memories.ai Research. *OmniRetriever: Any-to-Any Audio-Video-Text Retrieval via Fusion-as-Teacher Distillation.* https://arxiv.org/abs/2605.26641
- *S-EMBER: A Large-Scale Benchmark for Streaming Egocentric Memory Retrieval.* https://arxiv.org/pdf/2607.02689

### Part II — pipeline and tooling

- LAION. *video2dataset.* https://github.com/iejMac/video2dataset · https://laion.ai/blog/video2dataset/
- LAION. *BVD — Billion Video Dataset (CommonCrawl URLs).* https://github.com/LAION-AI/BVD
- *yt-fts — YouTube full-text search.* https://github.com/NotJoeMartinez/yt-fts
- *YT_crawler.* https://github.com/luc-pimentel/YT_crawler
- Luo et al. *Exo2Ego-V.* NeurIPS 2024. https://github.com/showlab/Exo2Ego-V
- Alibaba DAMO Academy. *RynnVLA-001: Using Human Demonstrations to Improve Robot Manipulation.* ICRA 2026. https://github.com/alibaba-damo-academy/RynnVLA-001 · https://arxiv.org/pdf/2509.15212
- Wang et al. *EgoInfinity: A Web-Scale 4D Hand-Object Interaction Data Engine for Any-View Robot Retargeting and Video-to-Action Robot Learning.* Rice University. https://arxiv.org/abs/2606.17385 · https://github.com/Rice-RobotPI-Lab/EgoInfinity
- *Panda-70M splitting module.* https://github.com/snap-research/Panda-70M/blob/main/splitting/README.md
- NVIDIA. *cosmos-curate.* https://github.com/nvidia-cosmos/cosmos-curate
- *Action100M.* https://arxiv.org/html/2601.10592v1
- Microsoft. *VLM-Video-Action-Localization.* https://microsoft.github.io/VLM-Video-Action-Localization/
- Build AI. *Egocentric-10K.* https://www.humanoidsdaily.com/news/build-ai-open-sources-10-000-hours-of-factory-worker-video-to-scale-robot-learning · subset mirror: https://huggingface.co/datasets/Voxel51/Egocentric_10K_subset
- *annotated-egocentric-10k-dataset.* https://github.com/fit-alessandro-berti/annotated-egocentric-10k-dataset
- *EgoVid-5M.* https://github.com/JeffWang987/EgoVid
- *awesome-egocentric-vision.* https://github.com/Sid2697/awesome-egocentric-vision
- *awesome-temporal-action-segmentation.* https://github.com/nus-cvml/awesome-temporal-action-segmentation
