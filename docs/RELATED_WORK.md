# Related Work

This project is not a model and not a dataset. It is the step in between: a way to
turn the open internet into **ego/exo training footage that a team can actually
use** — viewpoint-labelled, licence-checked, hands-verified, annotated to a
task → action → event tree, and priced per delivered hour.

That framing is what separates it from most of the literature it sits next to.
Almost everything below either *commissions* footage, or *consumes* a corpus
somebody else already owns. Very little of it is about acquisition against a
stated requirement.

Two halves:

- **[Part I — The literature](#part-i--the-literature)**: the datasets and systems
  this work is positioned against.
- **[Part II — The open-source pipeline](#part-ii--the-open-source-pipeline)**:
  crawl → viewpoint → clip → annotate as downloadable code, stage by stage, with
  what is safe to reuse and what is not.

Every entry below was read at the source — repository README, dataset card, or
paper — rather than summarised from memory. Where a widely-repeated number turned
out to be wrong or misattributed, the entry says so. **Licence and scale claims
are the two things most often garbled in second-hand summaries of this area**, so
both are stated explicitly per project, including for the datasets that look free
and are not.

---

# Part I — The literature

## 1. Commissioned egocentric and ego–exo capture

Staged captures: recruited participants, consented sites, a fixed activity
taxonomy, and an annotation budget spent up front.

**[EPIC-KITCHENS-100](https://arxiv.org/pdf/1804.02748)** — 100 hours, 45 kitchen
environments, 89,977 action clips, head-mounted, dense verb/noun action labels.
The original proof that a single domain captured deeply beats a broad shallow
sweep for action recognition. **Licence: CC BY-NC 4.0 — commercial use
prohibited**, with commercial terms available only by writing to the Bristol
team.

**[Ego4D](https://ego4d-data.org/)** — 3,670+ hours of daily-life egocentric
video with a benchmark suite (episodic memory, forecasting, hand–object
interaction). Still the default pretraining corpus, and the base that
[EgoVid-5M](#egovid-5m) and much else is derived from.

**[Ego-Exo4D](https://arxiv.org/abs/2311.18259)** (CVPR 2024) — the reference
work for this project's problem statement. 1,286 hours, **740 participants across
13 cities and 123 natural scene contexts**, and over **200,000 hours of annotator
effort**. Its distinguishing property is *simultaneous* capture: a head-mounted
Aria view plus multiple surrounding exocentric cameras of the same skilled
activity (sports, music, dance, bike repair). Two years of work by FAIR, Project
Aria and 15 university partners.

⚠️ **Two things to keep straight.** The 1,286 h is the *combined* ego + exo
total; the egocentric portion is far smaller — a third-party comparison puts
Ego-Exo4D V2 at **221.26 h of ego video** against 1,286.3 h total. And both Ego4D
and Ego-Exo4D are distributed under a **signed licence agreement whose terms are
not published on the public pages** — you request access, wait for approval, and
read the agreement then. Neither site states whether commercial use is permitted.
For a project that scores rights per clip, "the terms are behind a form" is
itself the finding: it cannot be assumed permissive.

> **Bearing here.** Ego-Exo4D is the clearest argument that the two viewpoints
> are worth pairing, and its annotation depth is the bar the `L0–L3` gates in this
> repo are written against. It is also the reason exo→ego *generation* research
> exists at all (§8) — and the reason that research does not transfer to web
> video, since Ego-Exo4D's rig is its input assumption.

**[EgoExoLearn](https://github.com/OpenGVLab/EgoExoLearn)** (CVPR 2024) — 120
hours plus gaze, modelling demonstration-following: a person watches an
exocentric demo, then performs the task while recording egocentrically.
Benchmarks for cross-view association, cross-view action segmentation /
anticipation / planning, cross-view referenced skill assessment, and cross-view
referenced captioning. The closest existing formalisation of "the exo video
teaches, the ego video executes."

**[HOI4D](https://arxiv.org/pdf/2404.09933)** — 2.4 M RGB-D egocentric frames
across 4,000 sequences in 610 indoor rooms, with category-level 4D hand–object
labels. Depth-equipped, so it is the geometric ground truth that monocular
pipelines like [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject) are trying to approximate from RGB.

**[ENIGMA-360](https://arxiv.org/pdf/2603.09741)** — ego-exo capture in
industrial settings; the nearest published analogue to factory-floor procedural
data, and a useful comparison point for [Egocentric-10K](#egocentric-10k).

**Where we differ.** Commissioned capture buys control and pays in cost and
coverage: you get exactly the 123 scenes you funded. This system inverts the
trade — the footage already exists, so the budget goes into *verification* rather
than recording. The failure modes invert too: a staged dataset never has a
licence problem and never has to prove a clip is first-person; ours must prove
both, per clip, with evidence.

## 2. Scaling human video for robot learning

The current wave treats human video as a substitute for teleoperated robot data.
The scaling numbers have moved fast; the licences have not kept up.

### EgoDex

**[arXiv 2505.11709](https://arxiv.org/html/2505.11709v1)** — 829 hours, **90 M
frames**, **338,000 demonstrations across 194 tabletop manipulation tasks**,
collected on **Apple Vision Pro (visionOS 2)** with production pose tracking, so
demonstrators work bare-handed with no instrumentation. 2.0 TB compressed
(~500 TB raw).

- **Annotations**: 1920×1080 @ 30 Hz egocentric RGB; **SE(3) poses for upper body
  and 25 joints per hand** as 4×4 matrices; camera extrinsics and intrinsics at
  30 Hz; a per-joint confidence value; natural-language task descriptions cleaned
  through GPT-4.
- **Baselines**: 14 models under the X-IL framework (encoder-decoder and
  decoder-only transformers; behaviour cloning, denoising diffusion, flow
  matching). Best 2-second-horizon result 0.038 m mean distance (flow matching,
  K=10); visual goal-conditioning cut final-position error by 53%.
- 🔴 **Licence: CC-BY-NC-ND.** Non-commercial **and no derivatives**. This is the
  single most-cited "hands are the payload" dataset in the field and it cannot be
  used commercially, nor can derivative datasets be redistributed.
- **Limits**: tabletop only; annotation degrades under heavy occlusion and fast
  motion; embodiment gap.

> **Bearing here.** EgoDex is why the hands gate has no override — 25 joints per
> hand is the payload, and a clip without hands carries none of it. It is also
> exhibit A for §11: the field's favourite reference dataset is one you cannot
> ship a product on.

### EgoScale

**[UT Austin RPL, 2026](https://rpl.cs.utexas.edu/publications/2026/02/18/zheng-arxiv26-egoscale/)** —
a VLA trained on **20,854 hours of action-labelled egocentric human video**,
described as 20× prior efforts. Two-stage recipe: large-scale human pretraining,
then lightweight aligned human–robot mid-training. Transfers to a **22-DoF
dexterous hand** and down to lower-DoF hands. **+54% average success rate over a
no-pretraining baseline.**

Its most useful result for a collection system is methodological: a **log-linear
scaling law between human-data scale and validation loss**, with validation loss
strongly correlated to downstream real-robot performance. That is a defensible
reason to buy hours — and, read carefully, also a reason to care about which
hours, since a log-linear curve is exactly the regime where marginal
undifferentiated hours get expensive.

### HumanNet

**[arXiv 2605.06747](https://arxiv.org/abs/2605.06747)** (Peking University) —
**one million hours** of human-centric video spanning first- and third-person.
Three-stage construction:

1. **Collection** — keyword crawling of platforms and search engines, plus
   existing open datasets, plus self-collection for underrepresented activities.
2. **Processing** — dedupe, normalise, content filtering (keep clips with
   meaningful human action), quality filtering, scene splitting, clipping.
3. **Annotation** — 3D hand and body pose, monocular SLAM camera trajectory,
   motion retargeting to a humanoid skeleton **only when error < 15 mm and
   coverage > 60%**, LLM-assisted captioning.

The headline experiment, stated precisely: under identical downstream conditions
(100 tasks, 20 episodes per task, 34 h post-training data), **1,000 h of HumanNet
egocentric video matched or modestly surpassed 100 h of real-robot CoBot data**,
and substantially closed the gap to a 20,000 h real-robot (LingBot) upper bound.

> ⚠️ **A correction to the version of this result that circulates.** It is
> commonly repeated as "1,000 h of ego video *beat* 100 h of robot data." The
> paper's own framing is *matched or modestly surpassed*, against a stated
> 20,000 h upper bound it does not reach. The economic argument survives; the
> triumphalism does not.

Its four stated limitations are worth reading in full because three of them apply
to any web-collection system, this one included: embodiment gap; irreducible
label noise at scale; uneven geographic / socioeconomic / occupational / body-type
coverage; and **privacy — first-person recordings capture bystanders and
sensitive spaces, third-person recordings capture identifiable people who never
consented.**

### Ego2Robot

**[arXiv 2608.02580](https://arxiv.org/html/2608.02580)** — converts egocentric
human video into robot training data in three stages:

1. **Action alignment** — hand pose → end-effector trajectory. A *virtual
   fingertip* is computed as a weighted blend of index and middle fingertips;
   gripper width comes from thumb-to-fingertip distance. WiLoR per-frame,
   DynHaMR for temporal optimisation.
2. **Visual alignment** — segment the human arm (SAM 3), inpaint it out
   (ProPainter), optimise robot base pose by IK (MuJoCo), composite the rendered
   arm back with depth awareness.
3. **Quality curation** — three levels: pipeline-internal (IK failures,
   collisions), statistical outlier detection, and VLM consistency audit
   (Qwen3.5).

**Inputs ~1,940 h** — ANT 7 h (in-house), **EgoDex 732 h**, ViTRA 249 h,
EgoVerse 954 h — though the authors state the pipeline accepts in-the-wild video
as well as curated datasets, making it the one entry in this document that even
gestures at web-sourced input. The reported corpus is built from curated sets. **Output 18,561 h** of synthetic robot data across 15
morphologies (Panda, UR5e, ARX-L5, xArm7, Sawyer, Kinova Gen3, IIWA, Jaco, FR3,
UR10e, ViperX, WidowX, Piper, YAM, Aloha-Agilex). On an extended RoboTwin 2.0
with disentangled visual / scene / embodiment / task perturbations, 1:1 mixing
reaches 53.5% (+2.6 pts), with the largest gains in visual robustness (+8%
lighting, +6% colour) and task semantics (+11% unseen objects).

> **Note for anyone reusing this output.** Roughly 38% of its input hours are
> EgoDex, which is CC-BY-NC-ND — non-commercial, no derivatives. Nothing here is
> a claim about the authors' compliance; it is a reminder that **derived corpora
> carry the licence of their inputs**, and that the provenance chain has to be
> checked at the point of *reuse*, which is the posture §11 argues for.

### Open-AoE

**[arXiv 2607.14183](https://arxiv.org/abs/2607.14183)** — ~2,000 hours of
egocentric manipulation video from **500+ contributors using 400+ consumer
smartphone models**, claimed as the broadest consumer-phone device coverage in
the category. Self-captured, not internet-sourced, and recorded **after explicit
informed consent**.

- **Annotations**: 32,407 distinct natural-language action descriptions;
  MANO 21-joint hand poses; 6-DoF camera trajectories; temporally localised
  atomic actions over 175 verbs, 8,030 objects, 135 scenes.
- **Toolchain**, which is the more interesting half: on-device detection of valid
  hand–object interaction at the edge → offline quality checks including **face
  masking** and integrity validation → camera-trajectory estimation, hand-mesh
  recovery and action segmentation → a three-gate inspection (completeness,
  correctness, consistency). Downstream it ships visualisation with overlaid hand
  meshes, reconstruct-and-retarget to robot trajectories, and training-ready
  action representations.
- **Licence: CC BY 4.0.**

> **Bearing here.** The closest thing in open source to this repo's gate
> structure — an interaction gate, a quality gate, and a three-way consistency
> inspection — except pointed at footage the project itself collected. Its
> existence is the strongest single piece of evidence for [§13](#13-why-no-open-source-project-does-exactly-this):
> when a community builds open pipeline infrastructure for ego video, it builds
> it around **capture**, never around acquisition from the web.

### EgoVerse

**[arXiv 2604.07607](https://arxiv.org/abs/2604.07607)** — 1,362 hours, 80,000
episodes, 1,965 tasks, 240 scenes, **2,087 unique demonstrators**, from a
collaboration spanning Georgia Tech, Stanford, UC San Diego, ETH Zürich, MIT,
Meta Reality Labs, Mecka AI and Scale AI. Split into **EgoVerse-A** (75 h, 5.5%:
academic labs, identical protocols, six flagship tasks, Project Aria glasses) and
**EgoVerse-I** (~1,287 h, 94.5%: industry partners on custom stereo-fisheye rigs),
with a smartphone-on-head-strap path for community contribution. Annotations:
21-keypoint 3D hand poses, calibrated 6-DoF head poses, task descriptions, scene
ids, object labels, demonstrator metadata.

The platform half, **EgoDB**, is the notable part: continuous ingestion,
standardised preprocessing, unified storage, SQL metadata indexing, a web
browsing interface, and local sync for training. That is a data *platform* — and
again, entirely for footage the consortium captures itself.

⚠️ Its dataset licence is not clearly stated; the arXiv entry carries only the
standard arXiv perpetual non-exclusive licence, which is a paper licence, not a
data licence. Note also a scale discrepancy worth tracking: [Ego2Robot](#ego2robot)
cites EgoVerse at 954 h while the v2 paper states 1,362 h — the corpus grew
between versions.

### EgoLive

**[arXiv 2604.23570](https://arxiv.org/html/2604.23570v1)** — the fidelity end of the
market, and the exact opposite design choice from [Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost).
1,680 hours of **stereo video at 60 fps**, 65,866 episodes across 346 real-world
tasks.

- **Capture**: **JoyEgoCam**, a custom head-mounted stereo rig — **2160×2160 per
  camera**, 130° × 130° field of view, IMU at 200 Hz.
- **Automated annotation pipeline**, three stages: HaMeR for hand estimation into
  MANO parameters and **ORB-SLAM3** fusing binocular images with IMU for camera
  ego-motion → detection/tracking, **SAM2** segmentation and a **fine-tuned
  Qwen3-VL-32B** for hand–object interaction descriptions → stereo optimisation
  for 3D keypoints and **FoundationStereo** for depth at 1152×1152.
- **Ships**: stereo RGB, 6-DoF hand and wrist trajectories, 3D hand keypoints,
  depth maps, hand masks, interacted-object masks, sub-task segmentation with
  natural-language descriptions, camera pose.
- **Licence: CC BY 4.0**, distributed through JD Cloud's robotdata-market.

> **Bearing here.** Put EgoLive's 2160×2160 stereo beside Egocentric-100K's
> 456×256 and the field's split is obvious: one wing is buying **hours** at the
> cost of pixels, the other is buying **fidelity** at the cost of hours. Neither
> is buying *provenance-carrying hours sourced against a requirement*, which is
> the axis this repo competes on. Its pipeline is also the most complete public
> answer to "what does a full annotation stack look like" — and, like every other
> one in §13, it runs on footage the authors captured themselves.

**[From Human Videos to Robot Manipulation](https://arxiv.org/html/2606.00054v1)** —
the survey that maps this whole cluster; useful as an index, not as evidence.

**Where we sit.** All of these start from a pool. This repo is the step before
the pool: given a requirement — N hours, this viewpoint, this activity, reusable
licence — find the footage, prove it matches, report what the hour cost.

## 3. Selection is the hard part, not collection

### SiMDex

**[arXiv 2608.04196](https://arxiv.org/abs/2608.04196)** — the most direct
intellectual neighbour to this project's usability ranking, arrived at from the
other end of the pipe. It casts human-data selection for VLA post-training as a
**recommendation problem**: a three-layer **recall → ranking → re-ranking**
pipeline over a pool of ~32 M egocentric human samples, operating in a
morphology-agnostic action space so no VLA architecture or training change is
needed.

**Result: mining ~1.49 M samples — under 5% of the pool — raised overall success
rate from 47.7% to 61.1%** against a strong baseline trained on an equal quantity
of randomly sampled human data. A 13.4-point gain from selection alone, at a
twentieth of the data.

> **Bearing here.** This is the empirical case for the whole premise. If 5% chosen
> well beats 100% chosen randomly, then a collection system's product is not
> hours, it is *the argument for why these hours*. That argument is what the
> manifest, the viewpoint evidence and the quality gates exist to record.

### Panda-70M

**[CVPR 2024](https://github.com/snap-research/Panda-70M)** — 70.7 M
video–caption samples from 3.78 M source videos (~36 TB), with 10.47 M (8 TB) and
2.4 M (1.6 TB) subsets and 6,000-sample validation and test splits. 703 stars.

The construction is a three-step design worth copying wholesale:

1. Split long videos into semantically coherent clips (see
   [§9](#9-clip)).
2. Run **multiple cross-modality teachers** — video, subtitle and image models —
   so each clip gets several candidate captions.
3. Train a **retrieval model to *select* the best caption** at scale, supervised
   by a small human-labelled preference set.

Its most instructive result is negative: **no single captioner produced a good
caption for more than ~35% of videos, while the union of teachers covered 88.8%.**
Desirability filtering keeps 80.5% of candidates.

- **Licence**: dataset use inherits the terms of **HD-VILA-100M**, the source
  corpus — another instance of the provenance-chain rule.

> **Bearing here.** Selection, not generation, is the right treatment for
> low-confidence annotation. A clip the primary annotator is unsure about should
> not be discarded; it should be put to several annotators and adjudicated. Ours
> is an ensemble-of-evidence for the same reason theirs is an
> ensemble-of-teachers.

### InternVid

**[arXiv 2307.06942](https://arxiv.org/abs/2307.06942)** — 7 M videos → 234 M
clips with LLM-generated descriptions totalling 4.1 B words; the template for
LLM-in-the-loop corpus construction. Released as graded subsets rather than one
blob — **InternVid-10M-FLT** (the primary released cut), **10M-DIV**
(diversity-weighted), **Aesthetics-18M**, **200M**, and the full ~230 M
video–text pairs — which is a useful pattern in itself: publish the filtered
tenth that most people should actually use, not only the raw pile.

**ViCLIP**, trained on it, is a plain video CLIP — ViT video encoder plus text
encoder, spatiotemporal attention, video masking during pretraining — with
separate checkpoints per subset, so the subsets double as an ablation over data
quality.

Stated caveats: 15% of clips are only 360P–720P and "may not perform as well"
for generation, and 85% run under 10 seconds. ⚠️ The dataset page does not state
a licence; treat it as unresolved until asked.

**[NVIDIA NeMo Curator](https://github.com/NVIDIA-NeMo/Curator)** — GPU-accelerated
load / filter / dedupe / transform for text, image, video and audio at
world-model scale.

**Where we differ.** These are throughput-optimised heuristic filters over a
corpus the operator already holds. Here each verdict is a Thought → Action →
Observation trace with the frames it looked at, and the decisive filters are
**asymmetric**: a wrong-viewpoint clip, or a clip with no hands in frame, is
*dropped*, not ranked low. Throughput is not the objective function; defensible
hours are.

## 4. World-model and physical-AI stacks

**[NVIDIA Cosmos](https://arxiv.org/abs/2501.03575)** — a platform of generative
world foundation models with tokenizers, guardrails, **Curator** for data,
**Transfer** for domain adaptation, and **Reason / Evaluator** for scoring. Its
video curation pipeline is designed to locate segments with rich dynamics and
high visual quality, and **extracts ~100 M clips of 2–60 s from a 20 M-hour
collection**. The 2026 line (Cosmos 3, and the Physical AI Data Factory blueprint
announced at GTC 2026) folds world modelling, multimodal understanding, action
and reasoning into one family.

**Relationship.** Cosmos *generates and evaluates*; this repo *sources*. The seam
is the interesting part: **Cosmos Curator presupposes the 20 M-hour archive.**
Internet2EgoExo is how a team without one reaches its first defensible thousand
hours — real, licensed, provenance-tracked — which is precisely the input a
synthetic-augmentation stack needs before it can multiply anything.

## 5. Retrieval as the substrate — and the gap it leaves

### OmniRetriever

**[arXiv 2605.26641](https://arxiv.org/abs/2605.26641)** (Memories.ai Research) —
the retrieval model behind the Video DataLake tools this pipeline indexes into.
**Any-to-any audio–video–text retrieval**, supporting **12 AVT retrieval
directions**.

- **Mechanism**: *fusion-as-teacher distillation* — a stop-gradient copy of the
  fused (T,V,A) embedding is used as a teacher signal for the single-modal
  embeddings, so the joint embedding that earlier methods computed and discarded
  becomes supervision. Paired with a **Tuple-InfoNCE** term that supervises the
  fused embedding directly.
- **Results**: OmniRetriever-7B beats closed-source Gemini Embedding 2 by
  **13.3–18.0 R@1** on Clotho and SoundDescs; reaches the contemporary zero-shot
  specialist band of open video-text encoders on MSR-VTT and MSVD; **34.84
  AVG-all on OmniRetriever-Bench** (3,782 triples), +1.72 over Gemini Embedding 2.

**[S-EMBER](https://arxiv.org/pdf/2607.02689)** — streaming egocentric memory
retrieval; the benchmark form of the same problem, over continuous first-person
input rather than a fixed corpus.

### The gap this project fills

"Any-to-any" is any-to-any **across modalities** — text, video, audio. But the
axes that decide whether a clip is usable **training data** are not modalities:

| Decision axis | Recoverable by similarity search? |
|---|---|
| Egocentric vs. exocentric | No — must be asserted, with cues |
| Hands in frame | No — must be checked on pixels |
| Licence / reuse rights | No — metadata, entirely off-pixel |
| Usable length after trimming | No — a property of the cut, not the content |
| Provenance and consent posture | No — an external record |

A better encoder does not move any row in that table. These have to be
**asserted by an agent, justified with evidence, and written back as metadata** —
which is what the viewpoint classifier, the hands gate, the annotation tree and
the four hour measures (worn / delivered / accepted / accepted_labeled) exist to
do. **Retrieval proposes; pixels decide.**

## 6. Rights, provenance and the licence problem

Web-mined corpora typically ship URLs rather than pixels and leave reuse rights
to the downstream user. For footage intended to be *delivered* to someone, that
is not sufficient. This repo filters Creative-Commons material through the
YouTube API at search time, records the licence per clip in the manifest, and
treats unmeasured rights checks as **excluded from the score rather than assumed
to pass**.

Part II shows why that posture has to extend past the footage to the *tools*.

---

# Part II — The open-source pipeline

Part I is what the literature claims. This part is what is downloadable. The
chain this repo implements — crawl → decide viewpoint → clip → annotate — exists
stage by stage in open source, at higher maturity than most teams assume. What
does not exist is the assembly, the requirement layer at the front, and the
rights discipline running through it.

## 7. Crawl: URL → video

### video2dataset

**[iejMac/video2dataset](https://github.com/iejMac/video2dataset)** (LAION) — the
de-facto standard, and still the right answer for bulk fetch.

- **Throughput**: reported at **10 M videos in 12 h on a single 16-core machine**
  (source-dependent; YouTube is markedly slower than direct MP4 links).
- **Inputs**: CSV, TSV, TSV.gz, JSON, Parquet, plain URL lists, and WebDataset
  for reprocessing. Anything yt-dlp supports — 1000+ sites.
- **Stages / subsamplers**: download, subset (reprocess existing tars), resize,
  FPS downsampling, cut detection, clipping, optical flow.
- **Outputs**: files, WebDataset tars, Parquet, TFRecord, or dummy; shards carry
  video + captions + JSON metadata (URL, status, error) with Parquet indexes.
- **Scaling**: multiprocessing, PySpark, SLURM.
- **Licence** MIT. 662 stars, 176 commits, 74 open issues.
- **Limits**: non-tar file output degrades past ~1 M samples on ordinary
  filesystems; TFRecord supports fewer backends (local, HDFS, S3, GCS).

### LAION-BVD

**[LAION-AI/BVD](https://github.com/LAION-AI/BVD)** — **1.3 billion video URLs
mined from CommonCrawl**, of which 80 M are downloaded (~10 M hours), yielding
55 M annotated clips and 300 M extracted frames, with synthetic VLM-generated
video and audio captions after content-aware scene detection.

> 🔴 **Correction to a common reading.** This is frequently cited as "the URL
> list, ready to go." It is released **for research purposes only, not for
> commercial use**, and the paper, project page and download links are marked
> *coming soon* — it documents a work in progress. The authors also flag bias and
> uneven representation across languages, regions and topics. It is a strong
> signal that web-scale video URL mining is tractable; it is not a resource a
> commercial collection effort can currently build on.

### yt-fts

**[NotJoeMartinez/yt-fts](https://github.com/NotJoeMartinez/yt-fts)** — scrapes
channel and playlist subtitles with yt-dlp into **SQLite**, then searches them.

- `search` runs SQLite FTS with enhanced query syntax (AND/OR, wildcards,
  prefix); `vsearch` runs semantic search over **ChromaDB** embeddings generated
  through the OpenAI or Gemini embedding APIs; `llm` is a chat loop grounded on
  semantic hits; `summarize` produces timestamped transcript summaries.
- **Output is timestamped YouTube URLs** — the minute, not the video.
- **Licence** Unlicense. 1.8 k stars. ⚠️ The author marks the project
  **abandoned**; treat it as a pattern to copy rather than a dependency to adopt.

> **Bearing here.** This is the cheapest known way to find *the moment*. For
> ego/exo collection, "the 40 seconds where they actually pick up the tool" is
> the unit of value, and subtitle search over a candidate channel gets there for
> almost nothing before a single video is downloaded.

### YT_crawler

**[luc-pimentel/YT_crawler](https://github.com/luc-pimentel/YT_crawler)** —
keyword search by scraping rather than the Data API. `search`,
`get_video_details`, `get_comments`, `get_transcript`, `get_trending_videos`.
Filters cover upload date (hour → year), duration bands, sort order, and
features including live, 4K, HD, subtitles, 360, 3D, HDR — and **creative
commons**. MIT, 6 stars, 85 commits.

> Small and fragile (it breaks when YouTube's markup changes), but notable for one
> reason: it exposes the **CC filter** as a search-time parameter. This repo gets
> the same filter through the official YouTube Data API, which is the durable way
> to do it — but the fact that the scraping community treats licence as a
> first-class search facet, while the large curation pipelines treat it as a
> downstream footnote, is telling.

### The gap

`video2dataset` consumes a URL list; it does not search. **There is no
authoritative open implementation of the keyword-search → URL-manifest layer** —
teams glue a scraper or yt-dlp search to a Parquet file and move on.

**That gap is stage 0 of this repo.** Multi-source search (YouTube Data API, Exa
neural search, Apify, the open web), slot extraction that turns a sentence into a
query, and volume goals that decide when to stop are exactly the layer the OSS
chain leaves to the reader. Downstream of it, `video2dataset` remains the sane
choice for bulk fetch.

## 8. Viewpoint: the exo → ego question, answered three ways

### Exo2Ego-V — why generative conversion does not apply

**[showlab/Exo2Ego-V](https://github.com/showlab/Exo2Ego-V)**, *Exocentric-to-
Egocentric Video Generation*, NeurIPS 2024. A diffusion method with three parts:
a multi-view exocentric encoder producing dense multi-scale appearance features;
an exo→ego view-translation prior giving spatially aligned egocentric features as
concatenation guidance; and temporal attention layers for cross-frame
consistency. Built on MagicAnimate, Moore-AnimateAnyone and PixelNeRF; trained
and evaluated on Ego-Exo4D at 448 px short side; Apache 2.0, with five pretrained
view-translation priors released.

🔴 **Its input is the disqualifier: sparse 4-view exocentric cameras arranged
360° around the scene, with known poses and intrinsics.** That is a capture rig.
Internet video does not contain it, and no amount of scale changes that. Anyone
planning "we'll just convert third-person footage to first-person" should read
this method's input specification first.

### RynnVLA-001 — filter, don't convert

**[alibaba-damo-academy/RynnVLA-001](https://github.com/alibaba-damo-academy/RynnVLA-001)**,
[arXiv 2509.15212](https://arxiv.org/pdf/2509.15212), ICRA 2026. Its web-video
curation stage states the rule plainly:

1. Run a pose estimation model per frame, extracting facial landmarks, torso
   joints and hand keypoints (wrists, elbows, fingers).
2. **Videos containing facial landmarks are discarded** — a visible face strongly
   indicates third-person.
3. **Keep only frames where wrist and hand keypoints are visible** — hands near
   the camera strongly indicate egocentric manipulation.
4. Caption the survivors with Qwen2-VL-7B in robot-instruction phrasing.

> **Bearing here — the strongest external corroboration in this document.** A
> different group, solving a different problem, independently converged on the
> two rules that are hardest to defend in this repo: the viewpoint gate and the
> hands gate. Where we differ is disposition: RynnVLA uses it as silent
> preprocessing, while here every verdict carries its cues into the manifest. A
> delivered dataset has to defend its **inclusions**, not merely make them.

### EgoInfinity — lift to 4D, then reproject

**[Rice-RobotPI-Lab/EgoInfinity](https://github.com/Rice-RobotPI-Lab/EgoInfinity)**,
[arXiv 2606.17385](https://arxiv.org/abs/2606.17385). The technically correct form
of "third-person to first-person": not generating pixels, but recovering geometry
and reprojecting. Five phases:

| Phase | What runs |
|---|---|
| 1. Hand & metric geometry | WiLoR (MANO hand params), MoGe-2 (metric scale, focal length), Flow3r (dense depth), GeoCalib (gravity vector) |
| 2. Object discovery | SAM-3 (prompted detection) → SAM-2 (temporal mask propagation) → SAM-3D (mesh reconstruction where evidence permits) |
| 3. Pose tracking | FoundationPose++ for 6-DoF object pose in metric camera frame, stabilised for static / weakly-observed frames |
| 4. Interaction-aware refinement | MEMFOF optical flow + hand keypoints classify frames static / grasped / moving; trajectories refined per state |
| 5. Cleanup & reframing | Mask erosion, depth filtering, and **deterministic ego↔exo coordinate reframing in 3D — not generative** |

**Retargeting**: SO(3)-equivariant Vector Neuron layers predict a robot-specific
kinematic root frame from 3D hand trajectories, under a flow-matching formulation
over plausible root poses, then inverse kinematics produces joint trajectories.
The retargeting networks are trained **entirely in MuJoCo** on procedurally
generated trajectories with tracking-noise, occlusion and gravity-noise
augmentation. Tested on Unitree G1, NASA Robonaut2, dual-Franka FR3, and a LEAP
hand for real grasping; IK success 0.821 / 0.774 / 0.706 respectively, position
error 2.86–10.27 cm, orientation error 6.73–12.17°.

🔴 **Two corrections to how this paper is usually cited.**

1. **The "142 M clips / 14.6 years" figure is not EgoInfinity's.** Its abstract
   makes no quantified scale claim at all; it describes an *engine* for web-scale
   generation. The 14.6 years belongs to [Action100M](#action100m), the source
   corpus it draws from, and the clip count is Action100M's segment count
   (**147 M**, not 142 M). The paper's own curated demonstration set is **106
   Action100M videos**. The engine is real and modular; the scale is potential,
   not reported.
2. 🔴 **It assumes approximately static-camera video, and explicitly excludes
   body-mounted and hand-held footage.** For a project collecting *head-mounted*
   material, that is close to fatal: EgoInfinity is a tool for lifting
   third-person static-camera video into 4D, not for processing the egocentric
   clips this pipeline is built to find. Its `action100m_filter/` stage even
   selects for static camera plus visible hands.

Other stated limits: no precise hand–object contact alignment (no fingertip
placement or no-slip guarantee); no tactile signal; the retargeter is
robot-specific and needs retraining per morphology; it targets functional rather
than fine-grained kinematic imitation.

## 9. Clip

### Panda-70M splitting

**[splitting/](https://github.com/snap-research/Panda-70M/blob/main/splitting/README.md)** —
three stages, each a single command:

1. **`cutscene_detect.py`** — PySceneDetect finds shot boundaries and emits frame
   indices. **For segments longer than 7 s with no detected transition** (fades,
   unedited footage), it recursively splits off the first 5 s as its own clip.
   Output: frame ranges, e.g. `[[0,149],[149,298],…]`.
2. **`event_stitching.py`** — **ImageBind** embeddings identify adjacent clips
   that are semantically similar and merge them into coherent events. Output:
   timecode pairs, e.g. `["0:00:00.000","0:00:15.982"]`.
3. **`video_splitting.py`** — ffmpeg extracts the final clips.

The stitching step is the whole point: raw shot detection over-segments edited
footage, and a semantically coherent 16-second event is worth more than four
disconnected 4-second shots. Parameter settings are noted in-code as tuned
empirically.

### cosmos-curate

**[nvidia-cosmos/cosmos-curate](https://github.com/nvidia-cosmos/cosmos-curate)** —
split, annotate, filter, deduplicate, embed, and emit datasets, on
**Cosmos-Xenna**, a GPU-accelerated streaming pipeline built on **Ray**. Runs
locally in Docker, on NVIDIA Cloud Functions, on Slurm, or on cloud platforms.
251 stars, 668 commits.

- **Licence: code Apache 2.0, models under the NVIDIA Open Model License**
  (custom terms available). The split matters — the orchestration is genuinely
  reusable even where specific model weights are not.

This is the only industrial-strength skeleton on offer, and the layer beneath the
Cosmos platform discussed in §4.

## 10. Annotate

### Panda-70M's select-don't-generate design

Covered in §3. The transferable idea: **several teachers propose, a trained
retrieval model disposes.** Low annotator confidence is a reason to widen the
panel, not to drop the clip.

### Action100M

**[arXiv 2601.10592](https://arxiv.org/html/2601.10592v1)** — **147 million
temporally localised segments** from **1.2 million YouTube instructional videos**
spanning **14.6 years** of footage and ~21.3 billion English words. Fully
automatic, three stages:

1. **Temporal segmentation** — **V-JEPA 2** frame representations over
   overlapping 64-frame windows at 8-frame stride, then **hierarchical
   agglomerative clustering** to produce temporally coherent segments at multiple
   scales.
2. **Tree-of-Captions** — two complementary captioners:
   **Llama-3.2-Vision-11B** on mid-frames for fine spatial detail, and
   **Perception-LM-3B** at segment level for temporal dynamics.
3. **LLM aggregation** — **GPT-OSS-120B** runs three iterative rounds of
   Self-Refine, aggregating evidence across the caption hierarchy into structured
   fields.

**Five fields per segment**, with measured average lengths: brief action
(3.2 words), detailed action (27.8), actor, brief caption (19.2), detailed
caption (95.3). Segments under 4 s are discarded; ~3.23% receive `N/A` for
non-action content; **semantic resampling** via k-means over action embeddings
upsamples rare actions and downsamples frequent ones to fight the long tail.
Evaluated across eight action-recognition benchmarks (SSv2, EPIC-KITCHENS-100,
EgoExo4D, Kinetics-400, COIN, CrossTask, …) and eight text-to-video retrieval
benchmarks. **CC BY 4.0.** Training consumed ~1.3 M V100 GPU-hours plus 0.3 M
H100/H200 GPU-hours.

**Limits, stated**: instructional video skews to cooking, DIY and procedural
tasks; strong action-concept imbalance with patterns like "speak to camera"
over-represented; model-generated captions may hallucinate, mitigated but not
eliminated by hierarchical aggregation.

> **Bearing here.** The three-level hierarchy — brief action → detailed action →
> caption — is the same shape as this repo's task → action → event tree, at a
> scale that proves the shape survives full automation. The two design details
> worth stealing outright are the **4-second floor** and the **explicit `N/A`
> class**: both are ways of refusing to label rather than labelling badly, which
> is the same instinct as excluding unmeasured checks from the score.

### VLM-Video-Action-Localization

**[Microsoft](https://microsoft.github.io/VLM-Video-Action-Localization/)** —
learning-free open-vocabulary temporal action localisation. Sample frames at
regular intervals into a **tiled image with frame-index labels**, ask a VLM which
frame is closest to the action's start (or end), narrow the sampling window
around the answer, and repeat — a binary search over the timeline conducted in
natural language. Input: a long video plus an open-vocabulary action query.
Output: start and end timestamps. The tiling is exposed as a single knob —
`--grid N` builds an N×N grid of sampled frames. Published as *Open-vocabulary
action localization with iterative visual prompting*, IEEE Access 2025; **code
MIT**. Evaluated on the Breakfast dataset, and demonstrated qualitatively on a
10-minute first-person cooking video (cutting vegetables, washing vegetables).

⚠️ Which VLM it runs is not stated on either the project page or the repository
front page — worth reading `src/` before quoting a cost or latency figure for it.

⚠️ **The authors state plainly that it does not surpass current model-based
approaches.** That is exactly what makes it useful: zero training cost and no
labelled data, so it is the honest floor any trained localiser in this pipeline
must clear before it earns its complexity.

## 11. The licence trap

The finding with the sharpest practical edge, and the reason a "just use the open
pipeline" plan can quietly become unshippable.

**EgoInfinity's own code is MIT. Its dependencies are not.** The repository says
so directly: *commercial use of the repo as a whole is restricted by the WiLoR
(CC-BY-NC-ND) and MANO (non-commercial) terms.*

| Component | Licence | Consequence |
|---|---|---|
| WiLoR (hand reconstruction) | CC-BY-NC-ND | Research only, **no derivatives** |
| MANO (hand model) | Non-commercial research only | Registration-gated download |
| Ultralytics YOLO (detection) | AGPL-3.0 | Network copyleft if served over a network |
| SAM2 | Apache 2.0 | Clear |
| SAM 3.1 / SAM 3D Objects | Per upstream | Gated weights, HF access required |
| MoGe-2 / GeoCalib / HaWoR / MEMFOF / Flow3r | Per upstream | Check individually |

Replacing the hand reconstructor and the detector is tractable engineering — but
it is engineering, and it belongs on the schedule rather than in the assumptions.

**It is not an isolated case.** Reading the licences across this document
produces a pattern:

| Asset | Licence | Commercial use |
|---|---|---|
| Egocentric-10K / -100K | Apache 2.0 | ✅ (see §12 caveats) |
| Egocentric-1M | Apache 2.0 *(reported; card gated, unverified)* | ⚠️ verify before relying on it |
| Action100M | CC BY 4.0 | ✅ with attribution |
| Open-AoE | CC BY 4.0 | ✅ with attribution |
| EgoLive | CC BY 4.0 | ✅ with attribution (distributed via JD Cloud) |
| VLM-Video-Action-Localization | MIT | ✅ |
| InternVid | **not stated on the dataset page** | ⚠️ unresolved — ask |
| cosmos-curate (code) | Apache 2.0 | ✅ (models separate) |
| video2dataset | MIT | ✅ |
| Exo2Ego-V | Apache 2.0 | ✅ |
| **EgoDex** | **CC-BY-NC-ND** | ❌ non-commercial, no derivatives |
| **EPIC-KITCHENS-100** | **CC BY-NC 4.0** | ❌ (commercial terms by email to Bristol) |
| **LAION-BVD** | **research only** | ❌ |
| **EgoInfinity (as a whole)** | MIT code, encumbered deps | ❌ until deps are swapped |
| **Ego4D / Ego-Exo4D** | **signed agreement, terms not public** | ⚠️ unknowable until you sign — do not assume |
| EgoVerse | dataset licence not clearly stated | ⚠️ ask before use |
| Panda-70M (data) | inherits HD-VILA-100M | ⚠️ check upstream |
| EgoVid-5M | inherits Ego4D | ⚠️ check upstream |

Note what the bottom half of that table has in common: the field's **most-cited**
reference datasets are the ones you cannot use commercially, or cannot even read
the terms of without signing first. The permissive corner is occupied almost
entirely by 2026 releases and by tooling.

**Why this belongs in a Related Work document.** This repo already treats licence
as a first-class per-clip field — CC filtering at search time, licence in the
manifest, unmeasured rights checks *excluded* from the score rather than assumed
to pass. §11 is that same discipline pointed at the toolchain. **A dataset
inherits the restrictions of every model and corpus used to build it.** Clean
clips processed by a non-commercial pipeline do not produce a shippable dataset.
Rights are a property of the whole provenance chain, and the chain is only as
free as its most restrictive link.

## 12. Free hours, and what they do to the moat

### Egocentric-10K

**Build AI released 10,000 hours of real factory first-person video under
Apache 2.0** ([announcement](https://www.humanoidsdaily.com/news/build-ai-open-sources-10-000-hours-of-factory-worker-video-to-scale-robot-learning);
[subset on Hugging Face](https://huggingface.co/datasets/Voxel51/Egocentric_10K_subset)).

- **Scale**: 10,000 h, **1.08 B frames**, **2,138 workers**, 16.4 TB. WebDataset
  shards with paired JSON metadata (`worker_id`, `video_index`, `factory_id`,
  duration, resolution, frame rate, codec), streamable from Hugging Face without
  a full download.
- **Capture**: monocular head-mounted **Build AI Gen 1**, **128° horizontal ×
  67° vertical** field of view, **1920×1080 at 30 fps**, H.265/HEVC in MP4,
  recorded during normal work operations. **No audio.**
- **Domain**: the first large egocentric set collected exclusively in real
  factories. Ego4D's 3,670 h are daily life, not production lines.
- The public Voxel51 subset is Factory 51 only — 8 workers, 51 videos each, 416
  clips, 37.5 GB — which is the cheapest way to sanity-check the domain before
  committing to 16 TB.

🔴 **Read the dataset card before planning around it.** It **explicitly warns
against worker surveillance, performance evaluation, and biometric
identification**, and it carries **no consent documentation or privacy
certification**. Apache 2.0 licenses the *artefact*; it is not a warranty that
2,138 identifiable workers' portrait rights are cleared for your use case. That
is precisely the class of unmeasured check this repo refuses to score as passing —
and note that three of the card's prohibited uses are things a factory-SOP
product could drift into without anyone deciding to.

### Egocentric-100K and Egocentric-1M — and what scaling cost

🔴 **Egocentric-10K was the first release, not the event.** Build AI's
progression, in five months:

| Release | When | Hours | Resolution | Licence |
|---|---|---|---|---|
| Egocentric-10K | Nov 2025 | 10,000 | 1920×1080 | Apache 2.0 |
| [Egocentric-100K](https://huggingface.co/datasets/builddotai/Egocentric-100K) | Dec 2025 | **100,405** | **456×256** | Apache 2.0 |
| Egocentric-1M | Apr 2026 | ~1,000,000 (reported) | not verified | Apache 2.0 (reported) |

**Egocentric-100K, verified at the dataset card**: 100,405 hours, **10.8 billion
frames**, 2,010,759 clips, 24.79 TB, 30 fps H.265, monocular head-mounted
**fisheye** Build AI Gen 1, per-worker calibrated camera intrinsics, mean 7.06
hours per worker, Apache 2.0, access gated behind sharing contact information.

⚠️ **Egocentric-1M is still not source-verified, after two attempts.** Its
Hugging Face card returns 401 to an unauthenticated fetch, and it does not
surface in dataset search either — searching `builddotai` returns
Egocentric-100K and Egocentric-10K-Evaluation but no 1M card. So the ~1 M hours,
the April 2026 date and the Apache 2.0 terms rest entirely on secondary
coverage. Treat them as indicated, not confirmed, and open the card while logged
in before planning around this table's last row. The 100K row, by contrast, is
read straight off the card.

**The part nobody leads with: hours scaled 10×, and pixels per hour collapsed.**
Egocentric-10K ships 1080p. Egocentric-100K ships **456×256**. That is roughly a
seventeen-fold reduction in pixels per frame, and 256p is marginal precisely
where this domain needs resolution — finger articulation, small tool affordances,
what is actually being grasped. The free hours are real; they are not the same
hours.

**And the field is visibly splitting along that axis.** In the same window,
[EgoLive](#egolive) went the other way: 1,680 hours of **stereo 2160×2160 at
60 fps** with depth, masks and 3D keypoints. Two strategies, both credible:

| | Hours wing (Egocentric-100K) | Fidelity wing (EgoLive) |
|---|---|---|
| Hours | 100,405 | 1,680 |
| Per-frame | 456×256 mono | 2160×2160 **stereo**, 60 fps |
| Extra signal | none (no audio either) | depth, hand/object masks, 3D keypoints, 6-DoF trajectories |
| Bet | scale washes out noise | fidelity is what the model actually needs |

Neither wing is buying **provenance-carrying hours sourced against a stated
requirement**, which is the axis this repo competes on. That is the useful read:
the free corpora are not converging on one thing you have to beat — they are
diverging, and the gap between them is where a requirement-driven collector
lives.

> **What this does to §12's argument.** It strengthens it and sharpens it. Any
> pitch of the form "we can get you N hours" is now competing with a million free
> ones. But a pitch of the form "we can get you N hours *at a resolution and
> viewpoint where the hands are legible, with the rights cleared*" is competing
> with far less — because the corpus that won on hours gave up on pixels to get
> there. Retrieval proposes; pixels decide, and at 256p there is less to decide
> with.

Two further limits hold across the whole family: a single-source corpus caps
environment and process diversity no matter how many hours it holds, and the
consent question below does not improve with scale — it multiplies.

### Consent is a design choice, not a casualty of scale

Worth putting side by side. Egocentric-10K's card carries no consent
documentation and warns against surveillance uses.
[Open-AoE](#open-aoe) — 2,000 hours from 500+ contributors — states that
contributors record voluntarily **after explicit informed consent**, and its
pipeline includes **face masking** as an offline quality stage.

Same modality, same year, opposite posture. A collection system cannot retrofit
consent, but it can record which posture a source had, and refuse to score an
unverified one as clean. That is what the manifest's rights field is for.

### annotated-egocentric-10k-dataset

**[fit-alessandro-berti/annotated-egocentric-10k-dataset](https://github.com/fit-alessandro-berti/annotated-egocentric-10k-dataset)**
(Apache 2.0) — a five-stage annotation pipeline over it, and the closest public
analogue to this repo's annotation tree:

1. `01_transcribe_factory.py` — videos → chronological text descriptions per
   worker. (The source has no audio, so this is visual description, not ASR.)
2. `02_summarize_worker_processes.py` — transcriptions → worker-level process
   summaries.
3. `03_summarize_factory_process_mining.py` — worker summaries → factory-level
   report, **plus a factory-specific process-label list and activity-label list**.
4. `04_annotation_to_event_log.py` — annotations → CSV event logs **constrained
   by the vocabulary from stage 3**.
5. `05_merge_event_log_csvs.py` — per-video logs → worker-level ordered logs and
   factory-level logs.

The vocabulary constraint is the interesting mechanism: stage 3 derives a closed
label set per factory, and stage 4 may only emit labels from it, so the event
logs are mineable rather than being 10,000 hours of free-text paraphrase. That is
the same problem the annotation tree solves by fixing task → action → event
levels in advance.

Caveats: it ships **derived annotations only**, not the dataset payload; some
stages call external LLM APIs; it publishes no coverage statistics, so how much
of the 10,000 hours has actually been run through it is unstated.

### EgoVid-5M

**[JeffWang987/EgoVid](https://github.com/JeffWang987/EgoVid)** — 5 M egocentric
clips **derived from Ego4D** (annotations and metadata only; source video is
fetched separately from Ego4D at 1080p / 7.1 TB or 540p / 3.5 TB). Two annotation
layers: high-level action verbs and nouns generated by LLaVA-Video plus Qwen
summarisation, and low-level **kinematic camera parameters** from IMU data and
structure-from-motion pose estimation. Cleaning evaluates frame consistency,
action coherence, optical-flow magnitude, DOVER and CLIP similarity. Targets
egocentric video **generation**, not collection. Known issue: the raw IMU data has
problems, so the released pose annotations are preferred over it. Licence follows
Ego4D's terms.

### The structural read

This is the second time in short order that a large egocentric corpus has been
given away, and the pattern matters more than the gift: **nominal hours are being
commoditised.** A collection system whose pitch is "we can get you N hours" is
building on ground that keeps disappearing.

What does not commoditise is whether an hour is *provably* the right viewpoint,
provably hands-visible, provably licensed at every link of its chain, and
annotated deeply enough to train on. Note that even the free 10,000 hours arrive
with an open question on the one axis that cannot be recovered later — consent —
and no amount of downstream processing fixes it.

**Retrieval proposes; pixels decide. The moat is in the deciding.**

## 13. Why no open-source project does exactly this

The obvious question, having read all of the above: internet-scale video →
ego/exo training footage is a clearly valuable, clearly defined problem, and
almost every individual piece of it is open. So why is there no open-source
project that does the whole thing?

The answer is not that people tried and failed. **Open source went hard at the
two adjacent problems and skipped this one.**

### Where the effort actually went

**Capture.** A substantial and *accelerating* open effort exists for *recording
new* egocentric video, and it now ships pipelines, not just datasets:
[EgoKit](https://arxiv.org/pdf/2605.16797) unifies low-cost collection across
heterogeneous devices; [MobileEgo Anywhere](https://arxiv.org/pdf/2605.05945)
ships a free mobile app plus an open STERA processing pipeline so a lab can
generate VLA-ready data on commodity phones; [Open-AoE](#open-aoe) releases a
full edge-to-training toolchain under CC BY 4.0 around 2,000 hours from 500+
phone-carrying volunteers; [EgoVerse](#egoverse) runs an eight-institution
consortium with its own ingestion-and-indexing platform. All of them answer "how
do we make more footage cheaply, and process what we made." **None of them
touches footage that already exists on the internet.**

**Annotation.** An equally substantial effort exists for *labelling footage you
already hold*: [EgoLive](https://arxiv.org/html/2604.23570v1) releases an
automated pipeline producing language annotations, camera pose, 3D hand
keypoints, depth, hand and object masks and sub-task segmentation;
[Action100M](#action100m) publishes a fully automatic hierarchical labelling
recipe; [annotated-egocentric-10k](#annotated-egocentric-10k-dataset) does
process mining over a corpus someone else released.

**Acquisition from the web is the hole between them.** The tools that touch the
internet — [video2dataset](#video2dataset), [LAION-BVD](#laion-bvd) — are
viewpoint-blind by design: they fetch and package whatever URLs you hand them,
and have no concept of "egocentric," "hands visible," or "licensed for reuse."
Published guidance for sourcing ego footage from the web still describes the
method as *manually searching YouTube and TikTok for phrases like "egocentric
view"*. That is the state of the art for this stage: a person typing queries.

### Six reasons the hole persists

**1. The citable unit is a corpus, not a machine.** Research reputation attaches
to an artefact others can benchmark against — Ego4D, Panda-70M, Action100M,
Egocentric-10K. A pipeline that produces *a different corpus for every
requirement* has no fixed output to cite, so the natural thing to release is the
fish, not the rod. Note who broke that pattern:
[cosmos-curate](#cosmos-curate), from a company that profits when anyone runs a
large pipeline on anything.

**2. Where it is commercially valuable, the pipeline is the product.** Build AI
open-sourced ten thousand *hours* and not the stack that produced them. Data
vendors sell hours and keep the sourcing machinery. The asymmetry — corpus
given away, acquisition layer retained — is what you would expect if the
acquisition layer is where the margin sits.

**3. Legal exposure lands on the maintainer, and it is asymmetric.** A dataset
release can be framed as research; LAION-BVD does exactly that ("research
purposes only"). A general-purpose tool that automates *search → download →
licence filtering → redistribution* invites terms-of-service, portrait-rights
and privacy questions that fall on whoever's name is on the repository.
[YT_crawler](#yt_crawler) is 6 stars with an educational-use disclaimer; that is
roughly the equilibrium.

**4. There is no stable interface to standardise around.** Open infrastructure
crystallises where the contract is fixed: *fetch this URL*, *split this video*,
*embed this clip*. "Collect N hours matching this requirement" has no fixed
contract — the slot vocabulary, the viewpoint definition, the acceptance bar and
the rights posture all change per buyer. Without a stable interface there is
nothing for a library to be.

**5. The hard parts are contested judgement, not deterministic transforms.**
Whether a clip is egocentric, whether the hands are usable, whether the licence
holds — these are decisions with an evidence burden, not functions. Open source
is excellent at transforms and poor at adjudication. And until per-clip VLM
inspection became cheap, the only affordable approach was a heuristic — which is
why [RynnVLA-001](#rynnvla-001--filter-dont-convert) states its ego-filter rule
in a single paragraph of a VLA paper rather than shipping it as a project. As a
heuristic it did not merit one.

**6. The demand is barely older than the tooling.** The scaling results that make
web-sourced human video worth paying for are recent:
[EgoScale](#egoscale)'s log-linear law and [HumanNet](#humannet)'s
1,000 h-vs-100 h comparison are 2026. The models that make per-clip judgement
affordable are about as old. The window in which this is both *worth building*
and *buildable* has been open for roughly a year.

### What this does and does not license us to claim

Not "nobody has solved this." The honest statement is narrower and more useful:

> Every individual stage of the chain is open. What is missing from open source
> is the **acquisition layer** — requirement → search → viewpoint proof → rights
> proof → manifest — and it is missing for structural reasons, not because it is
> technically hard.

Which also sets the bar. If the assembly is the contribution, then the assembly
has to be good at the parts nobody else is doing — the requirement front-end and
the provenance back-end — and should reuse, not reimplement, the stages the
field has already solved. That is what [§14](#14-build-vs-reuse-per-stage)
records.

## 14. Build vs. reuse, per stage

| Stage | Best open option | Verdict | What this repo does |
|---|---|---|---|
| Requirement → query | *(nothing)* | **Build** | Slot extraction, volume goals, binding-constraint reporting |
| Search → URL manifest | *(gap; ad-hoc scrapers)* | **Build** | YouTube Data API, Exa, Apify, open web; CC filter at search time |
| Moment-level targeting | yt-fts pattern (abandoned) | **Copy, don't depend** | Subtitle/caption search before download |
| Bulk fetch | `video2dataset` (MIT) | **Reuse** | yt-dlp path with per-clip provenance retained |
| Viewpoint decision | RynnVLA-001 face/hand rule | **Reuse the rule** | Same rule, plus cited cues written to the manifest |
| Exo → ego conversion | Exo2Ego-V | **Reject** | Needs a 4-view 360° rig; the web has none |
| 4D lift / any-view | EgoInfinity | **Defer** | Licence-encumbered *and* excludes head-mounted footage |
| Clipping | Panda-70M `splitting/` | **Reuse the design** | Agentic cleaning + clipping with frame-level evidence |
| Orchestration at scale | `cosmos-curate` (Apache 2.0 code) | **Reuse** | — |
| Annotation | Panda-70M select-not-generate; Action100M hierarchy | **Reuse both patterns** | task → action → event tree, L0–L3 gates, refuse-to-label floor |
| Localisation baseline | VLM-Video-Action-Localization | **Use as floor** | Any trained localiser must beat learning-free |
| Curation / scoring | cosmos-curate filters | **Build** | Quality gates as code, four hour measures, cost per hour |
| Rights | *(mostly ignored)* | **Build** | Licence per clip; unmeasured ⇒ excluded, not assumed |

**The short version:** skeleton from `cosmos-curate`; clipping design from
Panda-70M; viewpoint rule from RynnVLA-001, independently corroborated;
annotation hierarchy from Action100M with Panda-70M's selection discipline; 4D as
a later upgrade only after the non-commercial dependencies are replaced *and*
the static-camera assumption is dealt with. **The front and the back of the chain
— requirement in, provenance out — are the parts that have to be built, and they
are the parts that are worth owning.**

---

## Positioning, in one table

| | Commissioned capture (Ego-Exo4D, EgoDex) | Web-scale corpora (Panda-70M, InternVid, HumanNet) | World-model stacks (Cosmos) | **Internet2EgoExo** |
|---|---|---|---|---|
| Where footage comes from | Recorded for the dataset | Scraped at scale, then filtered | Owned archive + synthesis | Searched on demand, per requirement |
| Selection signal | Protocol compliance | Heuristics, captionability | Dynamics / visual quality | Viewpoint → duration → licence |
| Wrong viewpoint | Cannot happen | Down-ranked | Not modelled | **Dropped** |
| No hands in frame | Rare by design | Kept | Kept | **Dropped, no override** |
| Rights | Consented at capture | Deferred to the user | Owned | Filtered and recorded per clip |
| Unit of output | A dataset release | A corpus | Synthetic hours | A manifest + a cost per hour |
| Auditability | Annotation guidelines | Pipeline code | Evaluator scores | Per-clip Thought → Action → Observation trace |

---

## References

### Part I — datasets and models

- Grauman et al. *Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives.* CVPR 2024. https://arxiv.org/abs/2311.18259
- Grauman et al. *Ego4D.* https://ego4d-data.org/
- Damen et al. *Scaling Egocentric Vision: The EPIC-KITCHENS Dataset.* https://arxiv.org/pdf/1804.02748
- Huang et al. *EgoExoLearn.* CVPR 2024. https://github.com/OpenGVLab/EgoExoLearn
- *HOI4D.* https://arxiv.org/pdf/2404.09933
- *ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios.* https://arxiv.org/pdf/2603.09741
- *EgoDex: Learning Dexterous Manipulation from Large-Scale Egocentric Video.* (CC-BY-NC-ND) https://arxiv.org/html/2505.11709v1
- *EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data.* https://rpl.cs.utexas.edu/publications/2026/02/18/zheng-arxiv26-egoscale/
- Deng, Zhou et al. *HumanNet: Scaling Human-centric Video Learning to One Million Hours.* https://arxiv.org/abs/2605.06747
- *Ego2Robot: Scalable Robot Data Synthesis from Egocentric Human Data.* https://arxiv.org/html/2608.02580
- *Open-AoE: An Open Egocentric Manipulation Dataset and Toolchain for Embodied Learning.* (CC BY 4.0) https://arxiv.org/abs/2607.14183
- *EgoVerse: An Egocentric Human Dataset for Robot Learning from Around the World.* https://arxiv.org/abs/2604.07607
- *EgoKit: Towards Unified Low-Cost Egocentric Data Collection with Heterogeneous Devices.* https://arxiv.org/pdf/2605.16797
- *MobileEgo Anywhere: Open Infrastructure for long-horizon egocentric data on commodity hardware.* https://arxiv.org/pdf/2605.05945
- *EgoLive: A Large-Scale Egocentric Dataset from Real-World Human Tasks.* https://arxiv.org/html/2604.23570v1
- *From Human Videos to Robot Manipulation: A Survey.* https://arxiv.org/html/2606.00054v1
- *SiMDex: Mining Similar Egocentric Videos for Cross-Embodiment Dexterous Manipulation.* https://arxiv.org/abs/2608.04196
- Chen et al. *Panda-70M: Captioning 70M Videos with Multiple Cross-Modality Teachers.* CVPR 2024. https://github.com/snap-research/Panda-70M
- Wang et al. *InternVid.* https://arxiv.org/abs/2307.06942
- NVIDIA. *Cosmos World Foundation Model Platform for Physical AI.* https://arxiv.org/abs/2501.03575
- NVIDIA. *NeMo Curator.* https://github.com/NVIDIA-NeMo/Curator
- Memories.ai Research. *OmniRetriever: Any-to-Any Audio-Video-Text Retrieval via Fusion-as-Teacher Distillation.* https://arxiv.org/abs/2605.26641
- *S-EMBER: A Large-Scale Benchmark for Streaming Egocentric Memory Retrieval.* https://arxiv.org/pdf/2607.02689

### Part II — pipeline and tooling

- LAION. *video2dataset.* (MIT) https://github.com/iejMac/video2dataset · https://laion.ai/blog/video2dataset/
- LAION. *BVD.* (research only) https://github.com/LAION-AI/BVD
- *yt-fts.* (Unlicense; abandoned) https://github.com/NotJoeMartinez/yt-fts
- *YT_crawler.* (MIT) https://github.com/luc-pimentel/YT_crawler
- Luo et al. *Exocentric-to-Egocentric Video Generation (Exo2Ego-V).* NeurIPS 2024. https://github.com/showlab/Exo2Ego-V · https://proceedings.neurips.cc/paper_files/paper/2024/hash/f5a8b5e5d007e66c929b971c2bc21d76-Abstract-Conference.html
- Alibaba DAMO Academy. *RynnVLA-001.* ICRA 2026. https://github.com/alibaba-damo-academy/RynnVLA-001 · https://arxiv.org/pdf/2509.15212
- Wang et al. *EgoInfinity: A Web-Scale 4D Hand-Object Interaction Data Engine.* Rice University. https://arxiv.org/abs/2606.17385 · https://github.com/Rice-RobotPI-Lab/EgoInfinity
- *Panda-70M splitting module.* https://github.com/snap-research/Panda-70M/blob/main/splitting/README.md
- NVIDIA. *cosmos-curate.* (code Apache 2.0) https://github.com/nvidia-cosmos/cosmos-curate
- *Action100M.* (CC BY 4.0) https://arxiv.org/html/2601.10592v1
- Microsoft. *VLM-Video-Action-Localization.* https://microsoft.github.io/VLM-Video-Action-Localization/
- Build AI. *Egocentric-10K.* (Apache 2.0) https://www.humanoidsdaily.com/news/build-ai-open-sources-10-000-hours-of-factory-worker-video-to-scale-robot-learning · subset: https://huggingface.co/datasets/Voxel51/Egocentric_10K_subset
- *annotated-egocentric-10k-dataset.* (Apache 2.0) https://github.com/fit-alessandro-berti/annotated-egocentric-10k-dataset
- *EgoVid-5M.* (inherits Ego4D terms) https://github.com/JeffWang987/EgoVid
- *awesome-egocentric-vision.* https://github.com/Sid2697/awesome-egocentric-vision
- *awesome-temporal-action-segmentation.* https://github.com/nus-cvml/awesome-temporal-action-segmentation
