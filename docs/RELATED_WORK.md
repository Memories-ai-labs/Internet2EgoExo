# Related Work

This project is not a model and not a dataset. It is the step in between: a way to
turn the open internet into **ego/exo training footage that a team can actually
use** — viewpoint-labelled, licence-checked, hands-verified, annotated to a
task → action → event tree, and priced per delivered hour.

That framing is what separates it from most of the literature it sits next to.
Almost everything below either *commissions* footage, or *consumes* a corpus
somebody else already owns. Very little of it is about acquisition against a
stated requirement.

Two halves: **Part I** is the datasets and systems this work is positioned
against; **Part II** is the crawl → viewpoint → clip → annotate chain as
downloadable code, stage by stage, with what is safe to reuse and what is not.

> ⚠️ **On the star counts, which are the weakest numbers here.** Every scale and
> licence figure below was read at its source and is re-read on a schedule. The
> **GitHub star counts are the exception**: they were read once, they are the
> fastest-moving value in the document, and as of **9 Sep 2026** they **cannot be
> refreshed from the environment these sweeps run in** — third-party repositories
> are outside its access scope, so both the HTML pages and the API refuse. They
> are left in place because relative magnitude (6 stars versus 1.8 k) still
> carries the signal they are cited for, and removed from any load-bearing role:
> **no claim in this document should rest on a star count**, and any that appears
> to is a defect. Treat each as *"roughly this, at some earlier point"*. This is
> recorded rather than quietly tolerated for the same reason as the
> [⚠️-marker note in §11](#11-the-licence-trap): a figure the survey cannot
> currently verify is a fact about the survey.

<details>
<summary><strong>Contents</strong></summary>

**[Part I — The literature](#part-i--the-literature)**

- [1. Commissioned egocentric and ego–exo capture](#1-commissioned-egocentric-and-egoexo-capture)
  - [EPIC-KITCHENS-100](#epic-kitchens-100)
  - [HD-EPIC](#hd-epic--41-hours-and-the-densest-annotation-in-this-document)
  - [Nymeria](#nymeria--264-consented-participants-called-in-the-wild)
  - [Ego4D — sixty mentions, and the access design that manufactures re-uploads](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads)
  - [Ego-Exo4D](#ego-exo4d)
  - [EgoExoLearn](#egoexolearn)
  - [HOI4D](#hoi4d)
  - [HoloAssist](#holoassist)
  - [Ego-1K](#ego-1k)
  - [ENIGMA-360](#enigma-360)
  - [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
  - [Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape)
- [2. Scaling human video for robot learning](#2-scaling-human-video-for-robot-learning)
  - [DROID — the denominator, and the eleven answers other people give for it](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it)
  - [The robot-native denominator](#the-robot-native-denominator)
  - [AgiBotWorld — twenty-three mentions, and the licence is inside the gate](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate)
  - [EgoDex](#egodex)
  - [EgoScale](#egoscale)
  - [EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)
  - [HumanNet](#humannet)
  - [Ego2Robot](#ego2robot)
  - [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)
  - [EgoEngine](#egoengine)
  - [EgoMimic](#egomimic)
  - [EgoAVFlow](#egoavflow--no-robot-demonstrations-still-means-a-board-in-every-scene)
  - [Zeva-Ego — the first published exchange rate](#zeva-ego--the-first-published-exchange-rate-and-a-named-consumer-of-the-free-ten-thousand-hours)
  - [EgoSteer and EgoSmith — the annotate stage, released](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table)
  - [EgoWild2Dex — a ninth "in the wild"](#egowild2dex--a-ninth-in-the-wild-and-the-first-measured-number-for-why-it-is-hard)
  - [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean)
  - [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)
  - [EgoHumanoid](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator)
  - [EgoVLA](#egovla--mano-as-the-action-space-not-just-the-annotation)
  - [Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms)
  - [OpenMMEgo](#openmmego--open-weights-and-data-half-kept)
  - [Being-H0.7](#being-h07--one-corpus-three-products-and-a-second-vendor-doing-it)
  - [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)
  - [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved)
  - [EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame)
  - [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
  - [The wristband](#the-wristband--tactile-measured-without-instrumenting-the-hand-and-a-fourth-position)
  - [TouchSight and HumanTouch — a fifth tactile position](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform)
  - [AtomEgo — a provenance table that restates four corpora at once](#atomego--a-provenance-table-that-restates-four-corpora-at-once)
  - [The UMI family](#the-umi-family--capture-without-a-robot-and-the-blind-spot-this-survey-had)
  - [OmniViTac](#omnivitac--tactile-on-the-robot-side-27810-downloads-and-a-card-that-says-only-its-licence)
  - [Open-AoE](#open-aoe)
  - [EgoVerse](#egoverse)
  - [MobileEgo Anywhere](#mobileego-anywhere)
  - [EgoKit](#egokit)
  - [EgoLive](#egolive)
  - [ACE-Ego-0](#ace-ego-0)
- [3. Selection is the hard part, not collection](#3-selection-is-the-hard-part-not-collection)
  - [SiMDex](#simdex)
  - [ReWeight](#reweight--the-control-simdex-did-not-run)
  - [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)
  - [Panda-70M](#panda-70m)
  - [InternVid](#internvid)
  - [NeMo Curator](#nemo-curator)
- [4. World-model and physical-AI stacks](#4-world-model-and-physical-ai-stacks)
  - [DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13)
- [5. Retrieval as the substrate — and the gap it leaves](#5-retrieval-as-the-substrate--and-the-gap-it-leaves)
  - [OmniRetriever](#omniretriever)
  - [S-EMBER](#s-ember)
  - [The gap this project fills](#the-gap-this-project-fills)
- [6. Rights, provenance and the licence problem](#6-rights-provenance-and-the-licence-problem)

**[Part II — The open-source pipeline](#part-ii--the-open-source-pipeline)**

- [7. Crawl: URL → video](#7-crawl-url--video)
  - [video2dataset](#video2dataset)
  - [LAION-BVD — it shipped, and this document said it hadn't](#laion-bvd--it-shipped-and-this-document-said-it-hadnt)
  - [yt-fts](#yt-fts)
  - [YT_crawler](#yt_crawler)
  - [HowTo100M and HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago)
  - [The gap](#the-gap)
- [8. Viewpoint: the exo → ego question, answered three ways](#8-viewpoint-the-exo--ego-question-answered-three-ways)
  - [Exo2Ego-V](#exo2ego-v--why-generative-conversion-does-not-apply)
  - [RynnVLA-001](#rynnvla-001--filter-dont-convert)
  - [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject)
- [9. Clip](#9-clip)
  - [Panda-70M splitting](#panda-70m-splitting)
  - [cosmos-curate](#cosmos-curate)
- [10. Annotate](#10-annotate)
  - [Panda-70M's select-don't-generate design](#panda-70ms-select-dont-generate-design)
  - [Action100M](#action100m)
  - [VLM-Video-Action-Localization](#vlm-video-action-localization)
- [11. The licence trap](#11-the-licence-trap)
  - [WiLoR — the chokepoint, read at source](#wilor--the-chokepoint-read-at-source)
  - [Awesome Egocentric Atlas — the index somebody else is keeping](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five)
  - [The second index, queried at last](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet)
  - [OpenEgo — somebody does this properly](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
  - [Who feeds whom — the derivation map](#who-feeds-whom--the-derivation-map)
- [12. Free hours, and what they do to the moat](#12-free-hours-and-what-they-do-to-the-moat)
  - [Egocentric-10K](#egocentric-10k)
  - [Egocentric-100K and Egocentric-1M](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)
  - [Ropedia Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)
  - [Consent is a design choice, not a casualty of scale](#consent-is-a-design-choice-not-a-casualty-of-scale)
  - [annotated-egocentric-10k-dataset](#annotated-egocentric-10k-dataset)
  - [EgoVid-5M](#egovid-5m)
  - [EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it)
  - [The structural read](#the-structural-read)
  - [A third way to get hours: manufacture them](#a-third-way-to-get-hours-manufacture-them)
  - [BinoGen — twenty million synthetic binocular frames](#binogen--twenty-million-synthetic-binocular-frames-and-a-release-conditioned-on-an-event)
  - [The other thing that happened to hours: they went on sale](#the-other-thing-that-happened-to-hours-they-went-on-sale)
- [13. Why no open-source project does exactly this](#13-why-no-open-source-project-does-exactly-this)
  - [Where the effort actually went](#where-the-effort-actually-went)
  - [Six reasons the hole persists](#six-reasons-the-hole-persists)
  - [What this does and does not license us to claim](#what-this-does-and-does-not-license-us-to-claim)
- [14. Build vs. reuse, per stage](#14-build-vs-reuse-per-stage)
- [The vocabulary problem](#the-vocabulary-problem--six-ways-a-name-misleads)
- [Corrections, in one table](#corrections-in-one-table)
- [Positioning, in one table](#positioning-in-one-table)
- [References](#references)
  - [Part I](#part-i--datasets-and-models)
  - [Part II](#part-ii--pipeline-and-tooling)

</details>

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

### EPIC-KITCHENS-100

**[arXiv 1804.02748](https://arxiv.org/pdf/1804.02748)** — 100 hours, 45 kitchen
environments, 89,977 action clips, head-mounted, dense verb/noun action labels.
The original proof that a single domain captured deeply beats a broad shallow
sweep for action recognition. **Licence: CC BY-NC 4.0 — commercial use
prohibited**, with commercial terms available only by writing to the Bristol
team.

### HD-EPIC — 41 hours, and the densest annotation in this document

**[hd-epic.github.io](https://hd-epic.github.io/site)** (CVPR 2025) — named three
times in this survey as a source of
[EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)'s
pretraining set and never given an entry, which is the gap
[ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)
occupied two sweeps ago. From the same Bristol-led team as EPIC-KITCHENS, and
announced by them as *"a new large-scale highly-detailed **validation**
dataset."*

**41 hours** of unscripted multi-day recording — and then the annotation, which
is the point:

| | |
|---|---|
| 4.4 M frames · **59,454 actions** (mean **2.0 s**, ±3.4) | 69 recipes · 558 ingredients |
| **7.7 M hand masks** · 19.9 K object tracks | 50.9 K audio events |
| **Digital twins of each scene** — annotation grounded in 3D | SLAM and **gaze** |
| 26.6 K VQA questions | *"How"* and *"Why"* descriptions, recipe step pairs |

**Licence: CC BY-NC 4.0**, stated on HD-EPIC's own page — *"All datasets and
benchmarks on this page are copyright by us and published under the Creative
Commons Attribution-NonCommercial 4.0 International License… You may not use the
material for commercial purposes."* Commercial terms by writing to the team, as
with EPIC-KITCHENS-100. ✅ **Read at the dataset's own surface, not an adjacent
one** — the discipline this document adopted after finding six of its own
permissive claims came off arXiv listings.

🔴 **And an independent user of it files a qualification this document should
carry beside the praise.** [Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms), assembling 16,000 hours of human
video and explaining why it had to build its own rig, writes: *"benchmarks like
**HD-EPIC** and HOI4D rely on **offline calibration to approximate camera
poses**, and their interaction labels are typically **aligned to clip boundaries**
or a hand…"* — set against what they say they needed, *"accurate depth, stable
camera alignment, and temporally precise interaction events."* **So the densest
annotation in this survey is dense in the axes it chose and approximate in two
that a downstream VLA team found load-bearing.** Nothing here is a defect
claim — HD-EPIC's camera poses are recovered, not measured, which its own SLAM
files make plain — but it is worth knowing that *"grounded in 3D"* and *"metric
camera pose per frame"* are not the same sentence, and that the team who tried to
use it at scale ran into the difference.

> **Bearing here, and it is the counter-example to this repo's own pitch worth
> keeping in view.** 41 hours is nothing — a twentieth of EPIC-KITCHENS-100, a
> ten-thousandth of Egocentric-100K. **And it is more useful per hour than any
> corpus in this survey**, because every second of it is grounded: masks, gaze,
> 3D scene geometry, audio events, causal descriptions. The storage split says it
> plainly — **1.9 TB of raw VRS against 115.5 GB of mp4**, with the annotations
> (349 GB of SLAM-and-gaze, 27 GB of audio, 1.95 GB of hand masks) shipped
> separately. **The whole §12 argument — that nominal hours commoditise and
> legibility does not — is an argument someone else already ran to its
> conclusion, at 41 hours.** The difference is that they got there by *capturing*
> forty-one hours under total control, which is the one thing a found-footage
> pipeline cannot do, and why this repo's answer has to be evidence per clip
> rather than instrumentation per scene.

### Nymeria — 264 consented participants, called "in the wild"

**[projectaria.com/datasets/nymeria](https://www.projectaria.com/datasets/nymeria/)**
(Meta, Project Aria) — the fourth parent of EgoScaler's set, and the other one
this document had never opened. **The largest body-motion corpus here.**

- **300 hours of daily activity**, across **1,200 sequences** and **264
  participants**, in **50 indoor and outdoor locations** over **20 scenarios**.
- **3,600 hours of *video data*** — the same 300 hours seen through multiple
  synchronised streams. ⚠️ **Two hour-counts, twelve-fold apart, on one page.**
  A reader quoting "3,600 hours" is quoting *camera*-hours; a reader quoting
  "300" is quoting wall-clock. This document's
  [hour axes](#12-free-hours-and-what-they-do-to-the-moat) already separate worn,
  delivered, accepted and accepted-labeled hours; Nymeria adds the reminder that
  even *worn* hours multiply by the number of sensors pointed at them.
- **230 hours of motion with natural-language description** — 310.5 K sentences,
  8.64 M words, annotated coarse-to-fine by watching synchronised ego, exo and
  motion-rendered playback.
- **400 km of travelling trajectory, 1,053 km of wrist motion.**

**Licence: CC BY-NC 4.0**, behind an **email gate** — *"By submitting your email
and accessing the Nymeria dataset, you agree to abide by the license and to
receive emails in relation to the dataset."* ⚠️ **NymeriaPlus now supersedes it**,
so anything citing "Nymeria" is citing a version with a named successor.

🟢 **And it is the consent exemplar this document has been saying the field
lacks.** Quoted: *"consent obtained from participants **and home owners**
regarding data recording and usage. Data was collected and stored with
de-identification. **EgoBlur was used to blur faces and license plates for all
videos.**"* Set that beside
[Egocentric-10K](#egocentric-10k)'s 10,000 factory hours, which carry **no
consent documentation** while warning against surveillance uses. **Consent is a
design choice, not a casualty of scale** — and Nymeria is what the choice looks
like when it is made: consent from the people recorded *and* the people whose
homes were recorded in, plus automated de-identification applied before release.

> 🔴 **A fifth "in the wild", and the purest of them.** The dataset is subtitled
> *"A massive dataset of multimodal egocentric daily motion **in the wild**"* and
> describes itself as *"the world's largest dataset of human motion in the
> wild"*. It is **264 recruited participants wearing Project Aria glasses under
> signed consent in fifty chosen locations.** Nothing about that is
> misrepresentation — *in the wild* here means *not in a motion-capture studio*,
> which is the honest and useful sense in the motion-understanding literature.
> But it is the fifth distinct project in this survey where the phrase, read by
> someone asking *did this come off the open internet*, means the opposite of
> what they would take it to mean. See
> [the vocabulary table](#the-vocabulary-problem--six-ways-a-name-misleads).

> 🔴 **What the two entries above finish.** EgoScaler's pretraining set is
> **Apache-2.0**. Its four parents are now all read at source: **Ego4D** (signed
> agreement, terms unpublished), **Ego-Exo4D** (signed agreement), **HD-EPIC**
> (**CC BY-NC 4.0**) and **Nymeria** (**CC BY-NC 4.0**, email-gated). **Not one
> of the four is permissively licensed. Two are explicitly non-commercial.** The
> Apache-2.0 covers the authors' own extracted trajectories — the same correctly
> scoped posture as ViTRA and EgoVid-5M — but **the card states none of this**,
> and the derived artefact is the one with 27,912 downloads. **This is now the
> second fully traced case of a permissive stamp sitting on top of four
> non-permissive parents**, and unlike ViTRA's it has *zero* permissive parents
> rather than merely unstated ones.

### Ego4D — sixty mentions, and the access design that manufactures re-uploads

**[ego4d-data.org](https://ego4d-data.org/)** — 🔴 **named sixty times in this
document and, until sweep 87, given five lines.** It is the parent of
[EgoVid-5M](#egovid-5m), **77.6% of [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)'s
input**, a component of [EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)
and [OpenMMEgo](#openmmego--open-weights-and-data-half-kept)'s OME10M, and the corpus this survey calls a
*"signed-agreement"* source every time a licence chain bottoms out. **A survey
should not describe an instrument sixty times without reading it**, which is the
same gap [DROID](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it)
had at thirty.

⚠️ **And the CLI it tells you to install is itself static.** The start-here page's
flow is *"Download the CLI … `pip install ego4d`"*; PyPI gives **`ego4d` v1.7.3,
last uploaded 8 June 2024** — over two years. Not a criticism of a released
corpus, whose bytes do not rot; **it is a fact about the tool a new user is sent
to**, and one that pairs badly with credentials that expire in fourteen days.

**Scale, read at the project page 22 Sep 2026.** **3,670 hours** of daily-life
egocentric video from **923 unique participants** across **74 worldwide
locations in 9 countries**, assembled by **88 researchers** in an international
consortium, with a benchmark suite spanning episodic memory, forecasting and
hand–object interaction. **v2.0** is the current release. Still the default
pretraining corpus in this literature by a wide margin.

**Consent, stated and better than most here.** *"The collecting partner holds
consent forms and/or release forms for all videos. Only when consent has been
collected from participants, the data will contain faces and other identifying
information. For the majority of videos, data has been de-identified
pre-release."* That is a two-tier posture — consent gates whether faces survive
at all — and it belongs beside [Nymeria](#nymeria--264-consented-participants-called-in-the-wild)
and [Open-AoE](#open-aoe) in the short list of corpora that say anything about
this.

⚠️ **The licence, more precisely than this document has been putting it.** The
survey's shorthand has been *"unpublished agreement."* Checked at source that is
**not quite right and the difference matters**: there is a named instrument, the
**Ego4D License Agreement**, the page offers *"a draft of the licenses"* to
**review before signing**, and execution happens at a separate site
(`ego4d.dev/request/ego4d`) with approval in **~48 hours**. You may sign **as an
individual or on behalf of an institution**, and the page notes that
institutional signature *"typically"* requires a **director- or
executive-level signatory** — a real barrier for a team that wants organisational
cover rather than one researcher's personal undertaking. *(The signing site
itself returned **HTTP 429** from this environment on 22 Sep, so the executed
text was not read this pass; that is stated rather than glossed.)* **So: terms
previewable in draft, binding text executed elsewhere, per-signatory.** Closer to
[Xperience-10M's two-instrument gate](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)
than to anything with a `license:` field.

🔴 **And the access design is the finding, because it explains a pattern this
document has been cataloguing without a cause.** From the same page:

> *"once approved your access credentials will **expire in 14 days** — you're
> expected to **download the data locally, not to consume it from AWS**."*

**Access to Ego4D is time-boxed, and the publisher explicitly instructs you to
take a local copy.** Renewal is available, but the steady state the design
produces is thousands of individually-signed researchers each holding their own
copy of a 3,670-hour corpus, with no technical tie back to the agreement they
signed.

> **That is a re-upload generator, and the survey's re-upload findings are
> downstream of it.** [`simon055/EgoVid_frames`](#egovid-5m) — 722 shards of
> extracted Ego4D-derived frames, no card, no licence, no attribution — is what
> this design makes easy, and the [EgoDex](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet)
> and [DROID](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it)
> re-upload clusters are the same shape around corpora with the same friction.
> **This document has been treating third-party copies as a failure of
> uploader diligence. At least part of it is a predictable response to an
> official route that expires.** *No criticism of the consent design is intended
> — expiring credentials are a reasonable control for a corpus of consented
> faces.* The point is narrower and it is the one the manifest cares about:
> **when the authoritative copy is hard to hold, the copy people actually use
> will be one whose terms nobody recorded** — which is exactly why provenance has
> to travel with the clip rather than live at the publisher.

**Bearing here.** Ego4D is the single largest reason this survey's licence chains
bottom out in *"signed agreement, terms not reproducible."* Its footage cannot be
redistributed, so everything built on it must ship annotations only — which
[OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly),
[EgoVid-5M](#egovid-5m) and [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)
all do correctly and none of their cards explains. **For a found-footage pipeline
the lesson is the inverse of the usual one: Ego4D is not a competitor, it is the
reason the competitor's outputs are encumbered.**

### Ego-Exo4D

**[arXiv 2311.18259](https://arxiv.org/abs/2311.18259)** (CVPR 2024) — the reference
work for this project's problem statement. 1,286 hours, **more than 800
participants across 13 cities and 131 natural scene contexts** — re-read at the
official docs this sweep; the widely-cited **740 / 123** are the CVPR paper's
figures and this document carried them for forty-odd sweeps — and over
**200,000 hours of annotator
effort**. Its distinguishing property is *simultaneous* capture: a head-mounted
Aria view plus multiple surrounding exocentric cameras of the same skilled
activity (sports, music, dance, bike repair). Two years of work by FAIR, Project
Aria and 15 university partners.

⚠️ **Two things to keep straight.** The 1,286 h is the *combined* ego + exo
total, and the egocentric portion is far smaller. The official documentation
states it exactly: *"Ego-Exo4D V2 is released which includes **1286.30** video
hours (**221.26 ego-hours**) across **5035 takes**."* So the dataset most often
cited as ~1,300 hours of ego-exo footage carries about **17% egocentric video**.
Anyone sizing an ego corpus off the headline number is out by roughly 6×. And
both Ego4D
and Ego-Exo4D are distributed under a **signed licence agreement whose terms are
not published on the public pages** — you request access, wait for approval, and
read the agreement then. Neither site states whether commercial use is permitted.
For a project that scores rights per clip, "the terms are behind a form" is
itself the finding: it cannot be assumed permissive.

⚠️ **A third thing, found on re-reading the same page.** The docs give the
V2 figure as **1,286.30 hours** in the release note and **1,422 hours** of
combined video in the narrative section. This document uses **1,286.30**,
because that is the number attached to a stated version and a take count, and
records the other rather than silently picking. **Even the source of the
document's most-cited correction disagrees with itself by 136 hours** — which is
the argument for citing a figure *with the sentence it came from*, not as a bare
number.

> **Bearing here.** Ego-Exo4D is the clearest argument that the two viewpoints
> are worth pairing, and its annotation depth is the bar the `L0–L3` gates in this
> repo are written against. It is also the reason exo→ego *generation* research
> exists at all (§8) — and the reason that research does not transfer to web
> video, since Ego-Exo4D's rig is its input assumption.

### EgoExoLearn

**[OpenGVLab/EgoExoLearn](https://github.com/OpenGVLab/EgoExoLearn)** (CVPR 2024) — 120
hours plus gaze, modelling demonstration-following: a person watches an
exocentric demo, then performs the task while recording egocentrically.
Benchmarks for cross-view association, cross-view action segmentation /
anticipation / planning, cross-view referenced skill assessment, and cross-view
referenced captioning. The closest existing formalisation of "the exo video
teaches, the ego video executes."

**Licence — checked at the repository this sweep, and the usual split applies.**
The repo carries an **MIT** `LICENSE` file (*"MIT License / Copyright (c) 2024
OpenGVLab"*). That governs the **code**. No separate dataset terms are stated
anywhere on the repository page, and the video is offered as direct downloads —
Google Drive, BaiduYun and Hugging Face — with no access form.

✅ **Resolved this sweep, by looking at the Hugging Face mirror instead of the
repository.** **[hyf015/EgoExoLearn](https://huggingface.co/datasets/hyf015/EgoExoLearn)**
— published under the first author's own handle — carries **`license: mit`** in
its card metadata, is ungated, and serves **3,932 downloads a month**. So the
dataset is MIT too, not merely the code. The record moves from *"code MIT, data
unresolved"* to **MIT throughout**. (The card also notes the HF copies are
*"unprocessed, full-size videos"*; the processed 25 fps versions used for the
benchmarks live on the GitHub page — an access distinction, not a licence one.)

> **That is three for three.** Panda-70M's *"⚠️ check upstream"* resolved to
> O-UDA, EgoVid-5M's to a correctly scoped Apache 2.0, and now EgoExoLearn's to
> MIT on the data. Every long-standing unresolved marker that has actually been
> chased has come back **more permissive than the marker implied**, and in this
> case the answer was one surface away the whole time. The
> [note in §11](#11-the-licence-trap) about unresolved fields being facts about
> the survey rather than the source is now carried by three data points instead
> of two.

### HOI4D

**[arXiv 2404.09933](https://arxiv.org/pdf/2404.09933)** — 2.4 M RGB-D egocentric frames
across 4,000 sequences, **9 participants**, **800 object instances** in 16
categories, 610 indoor rooms. Frame-wise it ships panoptic segmentation, motion
segmentation, action segmentation, 3D hand pose, category-level object pose,
reconstructed object meshes and scene point clouds, benchmarked on 4D
point-cloud semantic segmentation, category-level pose tracking and egocentric
action segmentation. **Licence CC BY-NC 4.0.** Depth-equipped, so it is the
geometric ground truth that monocular pipelines like
[EgoInfinity](#egoinfinity--lift-to-4d-then-reproject) are trying to approximate
from RGB — and, being non-commercial, another entry for
[§11](#11-the-licence-trap).

### HoloAssist

**[holoassist.github.io](https://holoassist.github.io/)** — 169 hours from **350
unique instructor–performer pairs**, and the only dataset here that captures a
*second person's judgement* alongside the footage. The performer wears a
mixed-reality headset streaming **seven synchronised channels** (RGB, depth,
hand pose, eye gaze, head pose, IMU); a remote instructor watches that egocentric
feed live and talks them through the task. Annotations cover actions,
conversation, and how the instructor corrects errors, intervenes and grounds
instructions in the scene. Benchmarks: mistake detection, intervention-type
prediction, hand forecasting, action recognition and anticipation. **Licence
CDLA v2**, permissive.

> **Bearing here.** Mistake detection is the label almost nobody else ships, and
> it is the one a curation pipeline would most like to have: a corpus where
> *"this attempt went wrong, and here is where"* is annotated is the natural
> training signal for judging whether a found clip shows a task done competently.
> Our quality gates currently judge legibility and rights, not competence; this
> is where a competence gate would come from if one is ever wanted.
>
> **And it is no longer alone, which makes the case stronger rather than
> weaker.** **CaptainCook4D** — *"A Dataset for Understanding Errors in
> Procedural Activities"* (NeurIPS 2024 D&B, UT Dallas + Florida) — annotates
> error in procedural cooking under **permissive terms**,
> where HoloAssist's CDLA v2 is permissive but its domain is instructor-guided
> repair. Two independent corpora, two domains, the same label. A competence gate
> trained on both would have something HoloAssist alone could not give it:
> evidence that "wrong" transfers across task families rather than encoding one
> annotation protocol.
>
> ✅ **Read at its own project page this sweep, and two things came of it.**
> First a correction of ours: the dataset is **384 recordings, 94.5 hours** —
> *"we collected a new egocentric 4D dataset CaptainCook4D comprising 384
> recordings (94.5 hrs) of people performing recipes in real kitchen
> environments"* — in two activity types, one following the recipe and one
> departing from it. **This document had it as a "54-hour" dataset, which is not
> its size but [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)'s
> slice of it.** The OpenEgo composition table is right to say 54; the sentence
> that turned that into the dataset's own scale was not. Same species as the
> [Ego-Exo4D](#ego-exo4d) trap — 1,286 total hours against 221 egocentric ones —
> where a number is true of a subset and false of the thing it gets attached to.
>
> Second, a check that came out well. The **Apache 2.0** licence had been taken
> second-hand from OpenEgo's `ATTRIBUTION.md` rather than from the source.
> Verified now at the project page — *"We provide the data under the Apache
> license 2.0"* — it is exactly right. **A small but real audit of the one
> project this document praises for provenance: its attribution file is
> accurate.** Praise for record-keeping is worth little unless somebody checks
> the records, so this is that check.

### Ego-1K

**[arXiv 2603.13741](https://arxiv.org/html/2603.13741v1)** (Meta Reality Labs) —
🔴 **not what the name suggests, and worth stating plainly because the name
invites the wrong reading: it is not 1,000 hours.** It is **956 videos of roughly
8–10 seconds each**, about **514,000 frames**, captured on a rig of **16
hardware-synchronised 60 Hz global-shutter cameras** — 12 fisheye surrounding a
Meta Quest 3 plus its 4 forward-facing — all moving with the wearer's head.
Activities are hand–object interaction: gestures, simulated typing, object
manipulation. Metadata covers lighting, scene type, actions, objects held, head
motion, clothing. Benchmarks are stereo consistency, per-frame 3D Gaussian
splatting and **4D dynamic novel-view synthesis**. **CC BY 4.0**; 17.5 TB research
version on Hugging Face, 88 TB raw on request.

🔴 **Licence — corrected this sweep, and it is the second Meta FAIR dataset here
to be wrong the same way.** The entry recorded **CC BY 4.0**; that is the arXiv
listing's, governing the paper. The dataset is named in the paper itself —
*"available at `https://huggingface.co/datasets/facebook/ego-1k`"* — and that
card carries **`fair-noncommercial-research-license`**, ungated, **60,268
downloads a month**. **Non-commercial**, like
[Action100M](#action100m), the other Meta FAIR release in this survey. Both were
recorded here as CC BY 4.0; both are their publisher's house licence. See
[the permissive-claims audit](#11-the-licence-trap).

> **Why it sits in this document.** It is a *view-synthesis* dataset, not a
> manipulation corpus — but it is exactly the rig-captured multiview input that
> [Exo2Ego-V](#exo2ego-v--why-generative-conversion-does-not-apply)-style methods
> require and the web cannot supply, and it is an unusual middle case: the
> surrounding views are head-mounted rather than fixed in the room. Its own
> stated difficulty is instructive too — large disparities and image motion from
> close dynamic objects and rig egomotion, which is to say that even with sixteen
> synchronised cameras, hands moving near the face remain the hard part.

### ENIGMA-360

**[arXiv 2603.09741](https://arxiv.org/html/2603.09741v2)** — the industrial
ego-exo dataset, and the sharpest available contrast with
[Egocentric-10K](#egocentric-10k), because the two target the same domain by
opposite means.

**111.54 hours**, **34 participants** aged 20–70 with mixed experience, on two
designed maintenance procedures (high- and low-voltage electrical board repair),
each with four variations by component (resistor / capacitor / transformer) and
tool (manual or electric screwdriver). **360 videos: 180 egocentric + 180
exocentric, temporally synchronised** — ego on **HoloLens 2** at 2272×1278 / 30
fps, exo on a **ZED** at 672×376 / 15 fps, aligned using a lamp as the temporal
reference.

The annotation density is the point: 14,556 keysteps across 68 types with
temporal boundaries, 14,036 interaction keyframes, 275,135 object annotations
over 25 classes, 56,473 hand boxes with handedness, hand contact states, plus
197,814 hand masks and 1,435,006 object masks, per-frame 1024-d DINOv2 features,
and 3D lab and object models for synthetic generation. Benchmarks: temporal
action segmentation, keystep recognition, egocentric hand–object interaction
detection. **Licence CC BY 4.0.**

Its stated limitation is refreshingly blunt — one laboratory, fixed layout,
controlled lighting, limited procedural variation, constrained participant
diversity — and it frames the trade this document keeps circling:

| | ENIGMA-360 | Egocentric-10K |
|---|---|---|
| Hours | 111.54 | 10,000 |
| Setting | one lab, designed procedures | real factories, whatever happened |
| Ego + exo | both, synchronised | ego only |
| Annotation | dense, six kinds, hand-checked | none shipped |
| Consent | 34 recruited participants | not documented |
| Licence | CC BY 4.0 | Apache 2.0 |
| Fails at | generalising past one room | telling you what is in it |

Neither is wrong. But a team that needs *industrial procedural data it can
defend* is choosing between a hundred annotated hours from one room and ten
thousand unannotated hours of undocumented provenance. That gap is what a
requirement-driven collector exists to close.

### SABER — commissioned ego–exo capture in a domain the internet is full of

**[arXiv 2605.09613](https://arxiv.org/html/2605.09613v1)** (DreamVu) — the
most recent commissioned ego–exo corpus in this document, and the one whose
domain most sharply raises the question §13 answers.

✅ **All nine figures below re-verified at the source on 19 Sep 2026**, against
`arXiv:2605.09613v1` — still the only version. ~100 h, multiple stores, 480p
GoPro ego, six calibrated ALIA views, 44.8 K samples split 25 K / 18.6 K / 1.2 K,
GR00T N1.6, 29.3% against 13.4%, ≈2.19×: **every one holds.** What did not hold
was a sentence this document wrapped around them, and the three release claims
it took from the paper rather than from the artefacts.

**Approximately 100 hours** of in-store footage, collected across *multiple*
real grocery stores — the paper says "multiple" and never gives a count, though
**its sibling does**: see the DreamVu programme note below. Dual-stream capture:
**ego on a head-mounted GoPro recording at 480p**, worn by the primary actors;
**exo on a DreamVu ALIA omnidirectional camera**, one fixed unit supplying "six
calibrated and synchronized wide-angle views that span the full surround
environment." The wearers perform the full shopping and stocking workflow —
stocking shelves, retrieving items, navigating aisles — in operational stores,
with no robot hardware present during collection.

What ships is not hours but retargeted action: **44.8 K training samples** in
three streams — **25 K** LAPA-style latent action sequences, **18.6 K**
dexterous hand-pose trajectories retargeted to robot joint space via
Dex-Retargeting, and **1.2 K** whole-body SMPL sequences retargeted to a
humanoid. Post-trained into GR00T N1.6, it reports a **29.3% mean success rate
across ten retail manipulation tasks against a 13.4% fine-tuning baseline**,
about 2.19×.

🔴 **This document said the footage was staged. The source says the opposite,
and this document never had evidence for it.** The paper: SABER records *"human
workers performing everyday retail tasks — stocking shelves, retrieving items,
navigating aisles — in fully operational store conditions"*, *"all captured
without staging, scripting, or teleoperation overhead"*, *"during natural
shopping activity."* The vendor's own Robot Data page says the same in its own
words — *"Every clip was recorded in a working environment"*, *"A head-mounted
camera on the worker"*, *"Customer names are withheld by agreement."* **The word
this document tripped on is "primary actors"**, which the paper uses throughout
in the scene sense, not the hired-performer one: the ALIA *"simultaneously
captures all people present, including the primary actor(s)."* Recruitment,
casting, scripting and compensation appear nowhere in the paper. Workers do.

**And the correction costs something, which is why it is worth being exact
about.** Staging is the expensive half of commissioned capture — you pay for the
performance, the venue and the schedule. Instrumenting people already doing the
work removes all three, and what is left is a GoPro, one fixed rig, and the
annotation bill. So SABER is a **cheaper** counter-example than this document was
treating it as, and the cost gap [§13](#13-why-no-open-source-project-does-exactly-this)
argues from narrows again — the same direction [Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape)
pushed it, from the other end.

**What survives is the part that was never about cost.** Grocery stocking and
shelf retrieval are among the most abundantly filmed activities on the open
internet — retail training footage, shift vlogs, body-cam and helmet-cam uploads —
and a team that needed a hundred hours of it put its own cameras in stores
anyway. But the thing bought was not the footage. The ego stream alone is
ordinary head-mounted video the web has in quantity; what found footage cannot
supply is that stream **synchronised frame-for-frame with a fixed 360° stereo
unit standing in the same room**. The paper's own framing agrees — it describes
the input as *"unpaired human shopping video"* that the pipeline then enriches.
**The purchase was the second viewpoint and the registration between the two**,
which is the claim §13 actually rests on, now stated without the staging error
attached to it.

🔴 **"Released publicly" is gated, the full corpus is under NDA, and the address
the paper prints for it is a redirect to a marketing page.** Three routes are
named; none of them is open, and only one of them is even about SABER:

| Route | What it resolves to, checked 19 Sep 2026 |
|---|---|
| `https://dreamvu.ai/saber` — *"The dataset can be accessed via the following link"* | **308 → `www.dreamvu.ai/saber` → `www.dreamvu.ai/`.** The path does not exist and the site redirects unknown paths to its homepage, which is about **Liberty3D**, a different 360°-world-model corpus. SABER appears there exactly once, in a Research list, as a link back to the arXiv paper. **HTTP 200, and nothing about the dataset** |
| [`DreamVu/SABER-10K`](https://huggingface.co/datasets/DreamVu/SABER-10K) — *"released publicly under a CC BY-NC 4.0 license"* | Real, and the licence is exactly as stated. But **`gated: auto`** behind four fields (full name, institutional or corporate email, organisation, description of intended use); the **README itself is unreadable unauthenticated** and files return **401**. Three configs matching the three streams. **19 downloads, 0 likes** since 2 Apr 2026 |
| The vendor's Robot Data page | Describes this corpus by name of task — *"Stocking and replenishment · Grocery · ego + exo + wrist"* — under **"Full dataset available under NDA."** It also lists a **wrist camera** in that capture stack, which the paper never mentions |

**So the fourth licence shape is worse than this document recorded it.**
*Partially released* implied one gate around the part you cannot have and an open
door to the part you can. There are **two gates at different strengths** — an
access request for the tenth, an NDA for the rest — and the route printed for the
rest leads to a homepage. **A 404 would have been more informative**: it would
have said the route was gone. A 200 on the front page says nothing is wrong.

**The nineteen downloads are recorded, and this time the discriminating test was
available immediately.** Nineteen in five and a half months is the smallest
counter in this survey by two orders of magnitude, and the tempting reading is
demand for commissioned retail data. A gated counter cannot carry that: it
measures **completed access requests**, not interest. The control is the same
publisher's [`DreamVu/PRISM-100K`](https://huggingface.co/datasets/DreamVu/PRISM-100K)
— created eleven days earlier, **same CC BY-NC 4.0, same `gated: auto`, same
retail domain, same ego/exo tags** — and it reads **360 downloads and 7 likes**.
Same friction, ~19× the pulls. **The gate is ruled out as the explanation**; what
is left is the audience, not the paperwork, and a VLM corpus has a much larger one
than a GR00T-N1.6 post-training set. Two single readings, so the *size* of the gap
is not yet evidence — only the elimination is.

**One control worth recording, because the survey's most common trap did not
fire here.** The arXiv listing for SABER is **CC BY-NC-SA 4.0**; the dataset is
**CC BY-NC 4.0**. Two different licences, one paragraph apart, in the exact
configuration that produced the adjacent-artefact error for Action100M, Ego-1K,
S-EMBER, NIMBLE and MobileEgo Anywhere. It did not fire because **the paper
states the dataset's licence in its own body text**, with the URL beside it. That
is the whole fix, it costs one sentence, and almost nothing else in this survey
does it.

**The DreamVu programme, which is two corpora and not one.** The same vendor
published [`PRISM`](https://arxiv.org/abs/2603.29281) (arXiv 2603.29281v1) — a
**270 K-sample multi-view retail video SFT corpus for embodied VLMs**, captured
from *"egocentric, exocentric and 360° viewpoints across five supermarket
locations"*, ~11.8 M frames at 4 fps and ~730 M tokens. So **the store count
SABER withholds, its sibling prints: five.** Not provably the same five — the
papers never cross-reference — but it is the only number either publication
gives, and the two HF releases are eleven days apart from one account. Worth
noting for [§13](#13-why-no-open-source-project-does-exactly-this): the
commissioned-capture entrants in this survey increasingly ship **a programme**
rather than a dataset, which is a different thing to compete with than a corpus.
One asymmetry between the two: PRISM-100K carries an `arxiv:` tag pointing at its
paper and **SABER-10K carries none**, so the link the paper makes to the artefact
is not made back.

**And the resolution is the tell.** The paper does not say which GoPro model or
why the setting was chosen, but no GoPro's native ceiling is anywhere near
480p — and SABER's ego stream is **480p**. In a corpus whose declared payload is *dexterous hand-pose
trajectories*, the first-person view of the hands was recorded at a resolution
below the one Build AI was criticised for dropping to
([§12](#12-free-hours-and-what-they-do-to-the-moat)). Two independent teams,
opposite provenance, same decision: hours over pixels. That is now a pattern
rather than a Build AI idiosyncrasy — and it makes the counter-position
legibility is what a manipulation corpus is *for* a lonelier but better-evidenced
place to stand.

### Ego-OSCAR — capture at $200, and a fifth licence shape

**[arXiv 2608.08285](https://arxiv.org/html/2608.08285v2)** ·
[hardware + software](https://github.com/fpv-labs/ego-oscar) ·
[dataset](https://huggingface.co/datasets/fpvlabs/stereo-550) — the entry that
puts a number on what commissioned capture now costs, and the one this document
should least like to find, because it narrows the economic gap it argues from.

**The rig.** A hardware-synchronised **global-shutter stereo camera** plus a
6-axis IMU, an embedded Linux SBC doing on-device encoding, and a realtime
microcontroller for feedback and watchdog — from **commercially available parts
and 3D-printed housings**, at a complete bill of materials of about **USD 200**.
Hardware designs, capture software and the corpus are all open-sourced.

**The corpus (Stereo-550).** **~550 hours per camera** — roughly **1,100 stereo
camera-hours** — across **1,462 sessions** from **25 contributors** in **40+
indoor environments**, kitchen-centric plus textile work, laundry, cleaning and
organising. Shipped with **209,315 labelled action segments** (460 verbs, 32,630
object phrases, free-form captions with timestamps), **per-session stereo
calibration**, **IMU synchronised in 1,271 of 1,462 sessions (86.9%)**, and
corpus-wide 3D hand reconstructions.

✅ **Re-read at v2 this sweep, and the rule behind that 86.9% is worth more than
the number.** Every figure above held unchanged from v1. What v2 states plainly
is the *policy*: *"Sessions failing calibration or lacking a usable synchronized
trace are **excluded rather than shipped with caveats**"*, and the sessions
without inertial data are *"released **without** an inertial stream rather than
with an unverified one"* — yielding a stated **96% usable-session** rate. **That
is a per-session acceptance decision, published as a rule and reported as a
count**, which is exactly the field this repo's manifest calls *acceptance
status*. Two things follow. First, a dataset can tell you **which** of its
sessions lack a modality instead of averaging the gap away, and almost none do.
Second, it is a third distinct kind of good practice, after
[OpenEgo's per-source attribution](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
and [the pointers-only releases](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago):
**provenance about *rights*, provenance about *distribution*, and now provenance
about *quality*** — three different things a release can be honest about, from
three different projects, and no project in this document does all three.

🔴 **And the licensing is a shape [§11](#11-the-licence-trap) has not seen:
bespoke, and split.** The **hardware and capture software are Apache 2.0** —
verified at the repository's own `LICENSE` file this sweep. The **dataset is
not**. Its card shows **`fpvlabs-license`** — *"released by FPV Labs for research
use under the FPV Labs dataset license"*, with a note that **commercial usage
allowed**. Those two clauses sit oddly together, and that is the point: **a
custom licence string tells a reader nothing by name.** Apache, CC BY-NC-SA, MIT
— each is a known quantity you can reason about without opening it. A
one-publisher licence has to be read in full, every time, and cannot be compared
across a corpus of datasets or checked by a script.

⚠️ **Except that here it cannot be read at all before you agree to it.** The
dataset is gated — *"Request controlled access to Stereo-550"* — and this sweep
found the licence text nowhere public: the card's files return **401**
unauthenticated, and the project essay names no terms, pointing only at Hugging
Face, GitHub and Google Drive. **So the terms you are being asked to accept are
themselves behind the acceptance.** That is not unusual for gated corpora, and
nothing improper is alleged. But it defeats the one thing a bespoke licence
requires — reading it — and it is the reason this document records the field as
*unclassifiable* rather than guessing from the summary line.

> **The honest consequence for this document's economics.** §12 and §13 argue
> from a cost asymmetry: commissioned hours are expensive, found hours are
> cheap. **Ego-OSCAR narrows that gap and says so out loud** — a rig anyone can
> build for the price of a phone, an open capture stack, and eleven hundred
> camera-hours to show it works. It is the strongest instance in this document
> of §13's finding that *open source went hard at capture*, and it should be
> read as a genuine reduction in the advantage found footage has on price.
>
> **What it does not narrow** is everything downstream of price. Those 550 hours
> are 25 people in 40-odd indoor rooms doing kitchen and household work — the
> coverage you get is the coverage you funded, which is the same trade
> [ENIGMA-360](#enigma-360) and [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
> make. A requirement for *industrial assembly in humid conditions*, or *left-handed
> tool use*, or *any of the long tail*, is not answered by a cheaper rig; it is
> answered by finding footage that already exists or by funding a new shoot. And
> the bespoke licence is a reminder that cheap to *make* is not the same as
> simple to *use*.

**Where we differ.** Commissioned capture buys control and pays in cost and
coverage: you get exactly the 123 scenes you funded. This system inverts the
trade — the footage already exists, so the budget goes into *verification* rather
than recording. The failure modes invert too: a staged dataset never has a
licence problem and never has to prove a clip is first-person; ours must prove
both, per clip, with evidence.

## 2. Scaling human video for robot learning

The current wave treats human video as a substitute for teleoperated robot data.
The scaling numbers have moved fast; the licences have not kept up.

**Three strategies for crossing the embodiment gap**, worth naming up front
because the doc keeps returning to them:

| Strategy | Representative | How the gap is closed | What it needs from the footage |
|---|---|---|---|
| **Retarget** | [Ego2Robot](#ego2robot) | Hand pose → end-effector, human arm inpainted out and a robot rendered in | Hand-visible ego video, at scale |
| **Reconstruct** | [EgoEngine](#egoengine), [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject) | Rebuild the scene in 3D/sim, re-render any embodiment | Object meshes, calibration, or a static camera |
| **Match at capture** | [EgoMimic](#egomimic) | Never open a gap — same sensor, kinematically similar robot, co-trained | Aria glasses on the demonstrator |

Only the first is even in principle compatible with footage found rather than
shot — and even Ego2Robot's published corpus is built from curated sets.

### DROID — the denominator this survey leans on, and the eleven answers other people give for it

**[arXiv 2403.12945](https://arxiv.org/abs/2403.12945)** (v2, 22 Apr 2025) ·
[project page](https://droid-dataset.github.io/) ·
[code](https://github.com/droid-dataset/droid) — 🔴 **named thirty times in this
document and never given an entry.** It is the number the whole scarcity argument
divides by: *"an hour of human video is worth more than an hour of robot data"*
is empty without it, and *"the scarcity claim survives at 23× rather than 287×"*
is arithmetic with DROID on the bottom. **A survey should not run its central
comparison against a corpus it never wrote up**, so this is the entry, read at
source on 20 Sep 2026.

**Mechanism.** *Distributed* robot interaction: **the same hardware in every
lab**, so the corpus is a sum of identical rigs rather than a merge of
incompatible ones. Each station is a **Franka Panda 7-DoF arm, two adjustable
Zed 2 stereo cameras, a wrist-mounted Zed Mini, and an Oculus Quest 2 headset
with controllers for teleoperation**, all on a **portable height-adjustable
desk** — the last detail being the design decision, because it is what lets one
rig produce 564 scenes instead of one.

**Numbers, verified.** **76 k demonstration trajectories / 350 hours**, **564
scenes**, **50 data collectors across North America, Asia and Europe**, **12
months**, **13 institutions**, **1,417 camera viewpoints** with intrinsic and
extrinsic stereo calibration. Language: **three natural-language annotations for
95% of all successful episodes**, and the page puts successful episodes at
**75 k of 76 k** — a ~98.7% success rate, which is itself a fact about
teleoperated capture that found footage cannot match.

⚠️ **One figure in this document was the project page's rather than the
paper's.** The **paper says 84 tasks at both v1 and v2**; **the project page says
86**; this document carried **86**. Small in magnitude and exactly the shape
[Ego-Exo4D](#ego-exo4d) already taught — *cite the figure with its sentence* —
except that here the two sentences are the same team's, on surfaces published a
year apart. Corrected to 84 with the discrepancy kept visible rather than
silently picking one.

🔴 **The rights position: it open-sources everything except the terms.** The
abstract says *"We open source the full dataset, policy learning code, and a
detailed guide for reproducing our robot hardware setup"* — and:

- the **project page states no licence**, re-checked this sweep;
- the **documentation site states none**;
- **`droid-dataset/droid` has no `LICENSE` file at all** — the raw URL returns
  **404**, verified directly;
- only **`droid_policy_learning`** carries one (**MIT**), and it governs *code*.

**So the most-cited open robot corpus in this survey has never stated what may be
done with its data.** That is not an accusation of restriction; it is the absence
of any statement either way, on a corpus whose whole framing is openness.

🔴 **And into that silence, eleven other parties have answered — with at least
five different licences.** Read across both hubs on 20 Sep:

| Copy | Licence stated | Downloads |
|---|---|---|
| `cadene/droid` — a LeRobot conversion in a **personal** namespace | **apache-2.0** | **91,575** (HF) |
| `lerobot/droid_1.0.1` | **apache-2.0** | 17,502 (HF) · **68,184** (MS) |
| 🔴 **`lerobot/droid_100`** | **`mit` on Hugging Face**, **`Apache License 2.0` on ModelScope** | 3,062 · **27,325** |
| `nvidia/Cosmos3-DROID` | **`openmdw-1.1`** — the Linux Foundation's Open Model, Data & Weights licence, a family that appears nowhere else in this survey | 20,226 (HF) · **113,846** (MS) |
| `Salesforce/3d_optical_flow_droid` | **mit** | 86,562 (MS) |
| `allenai/MolmoAct2-DROID-Dataset` | **apache-2.0** | 17,399 (MS) |
| `nv-community/PointWorld-DROID` | **other** | 454 (MS) |
| `lerobot-raw/droid_raw`, `lerobot-raw/droid_100_raw`, `EDiRobotics/droid_low_resolution`, `youliangtan/droid_100_to_hg` | 🔴 **no licence field** | 10,977 · 435 · 285 · 26 |

> 🔴 **`lerobot/droid_100` is the finding, and it is the second instance of a
> pattern this survey named one sweep ago.** Same organisation, same repository
> name, **MIT on one hub and Apache-2.0 on the other** — and the ModelScope
> record is again **`CreatedBy: Cherrytest`**, the platform mirroring account that
> also produced
> [`OpenGVLab/InternVid-Full`'s Apache-2.0 against its CC-BY-NC-SA-4.0 sibling](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet).
> **One occurrence was an anecdote; two make it a behaviour of the mirroring
> path**, and the behaviour is that a licence field gets re-typed by whoever
> moves the bytes. Both divergences here are between *permissive* licences, so
> nothing restrictive is being dropped — **which is precisely why it is worth
> recording now**: the mechanism is visible in a harmless case, and the
> [EgoDex re-uploads](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet)
> show what it does in a harmful one.

**Bearing here.** DROID is the strongest case for the *opposite* of this repo's
bet, and it should be stated that way: **it is what disciplined, standardised,
consented, fully-documented capture looks like**, with calibration, near-total
task success, and language annotation on 95% of it — every quality axis where
found footage is weak. What it cost was **thirteen institutions, fifty people and
a year**, for **350 hours**. That ratio is the argument, and it is the argument
whether or not the licence is ever stated. **But the licence is the part this
survey is about**, and DROID makes the cleanest possible case for storing the
*resolved source URL* beside the terms: a team that pulls "DROID" gets one of
five different licences depending on which of eleven artefacts they happened to
click, and **the publisher has said nothing that would settle it.**

### The robot-native denominator

Several entries below argue that an hour of human video is worth more than an
hour of robot data. That claim is meaningless without knowing how big the robot
side actually is, and the answer is smaller than the rhetoric suggests.

| Corpus | Scale | How it was made | Licence |
|---|---|---|---|
| **[DROID](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it)** | **350 hours**, 76,000 trajectories, 564 scenes, **84 tasks** *(the paper, at both versions; **the project page says 86**, and this document carried 86)*, 1,417 camera viewpoints | Teleoperation on a standardised rig (Franka Panda 7-DoF, two Zed 2 stereo + wrist Zed Mini, Quest 2 controllers), **13 institutions, 50 collectors, 12 months** | Open dataset; terms not stated on the project page |
| **[AgiBotWorld-Beta](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate)** | **2,976.4 hours** *(not re-verifiable 22 Sep — card 401s)*, **1 M+ trajectories, 217 tasks**, 87 atomic skills | **100 robots** — mobile dual-arm, 6-DoF dexterous hands, visual-tactile sensors; video, depth, joint positions/velocities/forces, end-effector state, odometry | 🔴 **CC BY-NC-SA 4.0**, **click-through gated (auto-approved)** — **102,027** downloads |
| **[Open X-Embodiment](https://robotics-transformer-x.github.io/)** | 1 M+ trajectories, **22 embodiments**, 527 skills, 160,266 tasks — **hours not stated** | **60 existing datasets pooled** from 34 labs across 21 institutions; single arms through bimanual robots and quadrupeds | 🔴 **No overall licence stated on the project page**, and no statement of whether the 60 components retain their own |
| **[RoboCOIN](https://huggingface.co/RoboCOIN)** *(Wu et al., arXiv:2511.17441)* | **956 hours**, **15 embodiments** — 2.7× DROID | Real-robot teleoperation, shipped as **100+ separate per-task Hugging Face datasets**, every one `gated: auto`; **59,642 monthly downloads in aggregate** | ⚠️ **`license: apache-2.0` — plus obligations the gate adds** (see below) |
| **[RoboMIND](https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND)** *(Wu et al., arXiv:2412.13877)* | **107,000 trajectories**, 479 tasks, 96 object classes, **four embodiments** (Franka Panda, UR5e, AgileX dual-arm, a dual-dexterous-hand humanoid), plus **5,000 failure demonstrations with stated causes** — 🔴 **hours are not stated by the publisher**; [AtomEgo](#atomego--a-provenance-table-that-restates-four-corpora-at-once) counts **221.7 h across 83,152 of those episodes**, which extrapolates to **~285 h** *(derived here, not published — flagged as such)* | Human teleoperation on a unified platform and standardised protocol, plus an Isaac Sim digital twin | 🟢 **Apache-2.0**, `gated: auto`, 57,305 downloads — **the largest permissively-licensed real-robot corpus in this table**, and it was missing from it until sweep 86 |
| **[InternData-A1](https://huggingface.co/datasets/InternRobotics/InternData-A1)** *(Tian et al., arXiv:2511.16651)* | **2,904 hours**, 4 embodiments — **simulation** | Synthetic manipulation across single-arm and bimanual skills under environmental variation | 🔴 **CC BY-NC-SA 4.0 — stated *only inside the gate prompt*.** The card carries **no `license:` tag**; 90,872 downloads |
| 🔴 **[FastUMI-100K](#the-umi-family--capture-without-a-robot-and-the-blind-spot-this-survey-had)** *(UMI-style, no robot)* | **100 K+ trajectories**, 54 tasks — **more trajectories than DROID** | A **hand-held gripper with a GoPro**; multi-view wrist fisheye plus high-frequency end-effector states, LeRobot v2.1 | 🔴 **none stated** — ungated, **269,342 downloads** |
| Human ego, for scale | [Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) 100,405 h · [DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) 44,711 h | Crowdsourced / commissioned capture | Apache 2.0 / unstated |

⚠️ **One number in that table is restated elsewhere at 3.7× and it is worth
knowing before you compare anything.** [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)'s pretraining table lists
**DROID at 1,285 hours**; DROID's own page says **350**. The likely cause is
camera-hours against wall-clock — DROID records two Zed 2 stereo cameras plus a
wrist Zed Mini — and it is the same multiplication
[Nymeria](#nymeria--264-consented-participants-called-in-the-wild) performs on
one page (300 activity-hours, 3,600 video-hours). **The difference here is that
it is two publications disagreeing about one corpus, with neither stating its
unit.** This document uses **350**, because that is what the publisher states.
**A reader comparing hour-counts across papers is, silently, comparing different
units** — which is the strongest argument in this section for the manifest
recording *what was counted*, not just how much.

✅ **Every figure in that table was verified at its own source this sweep, and
every one holds.** DROID's page: *"76k demonstration trajectories or 350h of
interaction data, collected across 564 scenes and 86 tasks by 50 data collectors
… over the course of 12 months"*, *"1417 camera viewpoints"*, *"the same hardware
setup across all 13 institutions"*. AgiBot's card: *"1 million+ trajectories from
100 robots, with a total duration of 2976.4 hours"*, *"200+ types of tasks"*,
*"87 types of Atomic Skills"*. OpenX's page: *"1M+ real robot trajectories
spanning 22 robot embodiments"*, *"pooling 60 existing robot datasets from 34
robotic research labs"*, *"21 institutions, demonstrating 527 skills (160266
tasks)"* — **and no hours figure and no licence anywhere on it.** These numbers
carry the document's central economic claim, and they had never been checked.

🟢 **One figure worth adding while there**: DROID ships **language annotations
for 95% of its successful episodes (75 k)** — so the flagship open teleoperated
corpus is not merely small, it is *annotated*, which is exactly the axis on which
[§12](#12-free-hours-and-what-they-do-to-the-moat) says free egocentric hours
arrive empty. 350 annotated hours against 10,000 raw ones is the trade the whole
substitution literature is arguing about.

⚠️ **Two refinements the re-read produced, both about access rather than scale.**

**AgiBot is not contact-gated, as this entry said — it is a click-through.** The
card's gate is `auto`: fill in first name, last name and affiliation, accept the
*AgiBot World Community License Agreement*, and access is granted immediately.
**102,027 downloads** have passed through it (86,157 a fortnight ago). The distinction matters here more
than usual, because this is the document's own
[licence-versus-access](#11-the-licence-trap) grid: AgiBot sits in
*most-restrictive licence, near-frictionless access* — the same cell as
Egocentric-10K, whose terms are Apache 2.0. **The gate tells you nothing about
the terms in either direction.** *(A small staleness in their record, since this
document collects them: the agreement text on the **Beta** release is headed
"AgiBot World **Alpha** Release Date: December 30, 2024".)*

🔴 **DROID states its data terms nowhere — and a third-party copy states them
for it, to 104,783 downloads.** The project page has no licence. Neither does
the documentation site. The data repository `droid-dataset/droid` has **no
`LICENSE` file**; only the separate `droid_policy_learning` repo carries one,
**MIT**, and that governs *code*. Meanwhile
[`cadene/droid`](https://huggingface.co/datasets/cadene/droid) — a LeRobot
conversion in a **personal** namespace, tagged `openx` — is stamped
**`license: apache-2.0`**, ungated, and has been pulled **104,783 times**, 91,575 at the latest reading;
`lerobot/droid_1.0.1` repeats the Apache-2.0 at 16,640. **That is the fourth
instance of an uploader's licence field standing in for a publisher's silence**,
after `simon055/EgoVid_frames`, `jxu124/OpenX-Embodiment` and
`easpeeder/Egocentric-1M` — with a **fifth** found on ModelScope
([`AQUAbyssteus/egoverse-mirror-…`](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet),
Apache-2.0 over EgoVerse's silence, 149,576 downloads) and, in the same pass, the
first cases where a stamp **contradicts** a publisher who did speak — and by download count it is larger than the other
three together. *No non-compliance is alleged; Apache-2.0 may well be what DROID
intends.* **The point is that nobody downloading it can tell**, and the artefact
that answers loudest is the one whose author had no standing to answer.

🟢 **The bottom two rows were added this sweep, from [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)'s pretraining
table — two robot corpora this document had never opened, and the denominator is
better for having them.** They do not rescue the robot side: the open real-robot
total is now roughly **350 + 2,976 + 956 ≈ 4,300 hours**, against
Egocentric-100K's 100,405. **The scarcity claim survives at 23× rather than
287×**, which is the honest number to argue from, and stating it that way is
worth more than the larger one.

🟢 **The denominator grew a fourth time at sweep 86, and the claim held — which
is the point of recomputing rather than defending.** [AtomEgo](#atomego--a-provenance-table-that-restates-four-corpora-at-once)'s
mixture named **RoboMIND**, a **107,000-trajectory, four-embodiment, Apache-2.0**
real-robot corpus this document had never opened — **the largest permissively
licensed one in the table.** 🔴 **Its publisher states no hours at all**, so it
cannot be added to an hours-based denominator without inventing a number:
AtomEgo counts **221.7 h across 83,152 of its episodes**, which extrapolates to
**~285 h for the full 107 k** *(derived here, and flagged as derived)*. On that
estimate the open real-robot total is **≈ 4,585 h** and Egocentric-100K is
**≈ 22×** it, against 23×. **The multiple has now survived two enlargements of
its own denominator**, having collapsed from 287× on the first. *And the fact
that the newest, largest, most permissive entrant reports trajectories and not
hours is itself the [unit problem](#atomego--a-provenance-table-that-restates-four-corpora-at-once)
arriving inside the denominator.*

⚠️ **RoboCOIN carries a licence shape this document has not recorded: a
permissive tag with obligations bolted on at the gate.** The card says
`license: apache-2.0`. The gate you must accept before downloading says: *"By
accessing this dataset, you agree to **cite the associated paper** in your
research/publications… You agree to **not use the dataset to conduct experiments
that cause harm to human subjects**."* **Apache-2.0 requires neither.** So the
artefact carries two instruments that do not agree about what you owe, and a user
who downloads has accepted both. **This document's grid treats licence and access
as independent axes — RoboCOIN shows the gate can *add terms*, not merely control
who passes**, which means "what may I do with it" is not answerable from the
licence field alone even when the licence field is a standard one.

🔴 **And InternData-A1 inverts the third-party-stamp pattern.** Its official card
has **no `license:` tag at all**; the terms — **CC BY-NC-SA 4.0** — appear only
inside a gate prompt behind **nine fields** including phone number, job title and
country. Meanwhile
[`griffinlabs/InternData-A1-LeRobot-v3.0-by-embodiment`](https://huggingface.co/datasets/griffinlabs/InternData-A1-LeRobot-v3.0-by-embodiment),
a third-party conversion, is **ungated**, has **24,586 downloads**, and is tagged
**`cc-by-nc-sa-4.0`** — correctly. **Fifth instance of an uploader's licence
field standing in for a publisher's, and the first where the uploader is the one
telling the truth in public.** With `cadene/droid` a third party asserted
Apache-2.0 over a publisher's silence, too permissively. Here a third party
states the *restrictive* terms the publisher put behind a form. **Same pattern,
opposite direction, and in both cases the searchable, ungated copy is the one
shaping what readers believe.**

**The ratios are the point.** Egocentric-100K is roughly **287× DROID**, **34×
AgiBotWorld-Beta**, and **23× the open real-robot corpora combined**. The flagship open teleoperated dataset — thirteen
institutions, fifty people, a year — is **350 hours**. That is why the
substitution arguments matter economically at all: robot data is not merely
expensive per hour, there is *almost none of it* by comparison.

It also recalibrates a result quoted earlier. [HumanNet](#humannet)'s baseline of
**100 h of real-robot data** sounds modest until you notice it is **close to a
third of the whole of DROID**. "1,000 h of ego video matched or modestly
surpassed 100 h of robot data" is a comparison against a meaningful fraction of
the field's open robot corpus, not against a toy.

🔴 **And the licence pattern extends to this side — in both of its forms.**
AgiBotWorld-Beta is **CC BY-NC-SA 4.0**: non-commercial *and* share-alike, so
derivatives must carry the same terms. That is the most restrictive combination
anywhere in this document, and it sits on the corpus a team is most likely to
want as its robot-side anchor.

Open X-Embodiment is the other failure mode, and the cleaner illustration of
[§11](#11-the-licence-trap)'s thesis: it is **60 datasets pooled from 34 labs**,
and its project page states **no overall licence and no position on whether the
components keep their own**. You cannot know what you may do with the pooled
corpus without tracing sixty upstream terms yourself. A provenance chain that
long, undocumented at the join, is not a licensing footnote — it is the reason
per-clip rights have to be recorded at collection time rather than reconstructed
later.

> **One more thing OpenX does not report: hours.** It gives trajectories, skills
> and tasks. Trajectory counts and hour counts are not interchangeable, and the
> largest pooled robot corpus declines to state the figure that every
> human-video corpus leads with — which is the same problem the
> [Xperience-10M critique](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)
> identifies from the other direction. **A unit count means nothing until you say
> what a unit contains.**

### AgiBotWorld — twenty-three mentions, and the licence is inside the gate

**[arXiv 2503.06669](https://arxiv.org/abs/2503.06669)** (*AgiBot World Colosseo*,
v4) · [`agibot-world`](https://huggingface.co/agibot-world) — 🔴 **named
twenty-three times here and never written up**, the third case a mention-count
scan has surfaced after [DROID](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it)
at thirty and [Ego4D](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads)
at sixty. It carries two of this survey's standing examples — *the most
restrictive licence in the denominator* and *the near-frictionless gate* — and
**checked at source, the second one is wrong and the first is not where this
document said it was.**

**Mechanism and scale, from the paper.** *"Over **1 million trajectories** across
**217 tasks** in five deployment scenarios"*, on a standardized collection
pipeline with **human-in-the-loop verification**, on a platform *"extensible from
grippers to **dexterous hands and visuo-tactile sensors**."* The 2026 release is
collected on the **AGIBOT G2** platform in a **free-form collection mode**, and a
**1:1 digital twin** of each scene is built in simulation and open-sourced
separately as **GenieSim**. ⚠️ *This document records **217 tasks** from here on;
it had **"200+"**. And its **2,976.4 hours** stands from an earlier reading and
**could not be re-verified this pass** — the Beta card returns **401** to an
unauthenticated fetch, so the figure is flagged rather than re-confirmed.*

🔴 **The licence is not in the licence field. It is inside the gate agreement.**
`agibot-world/AgiBotWorld-Beta` has **no `license:` tag at all** — not in its
Hub tags, not in `cardData` — so the Hub's licence facet files the most-cited
restrictive corpus in this survey as **unlicensed**. The CC BY-NC-SA 4.0 that
this document has quoted for dozens of sweeps lives in **`extra_gated_prompt`**:

> *"### AgiBot World COMMUNITY LICENSE AGREEMENT — AgiBot World **Alpha** Release
> Date: December 30, 2024. All the data and code within this repo are under
> [CC BY-NC-SA 4.0]."*

**Two things about that.** The terms are *readable* — a gate prompt is shown
before you accept — so this is not a *terms unstated* case; it is a **terms
mislocated** one, and the difference matters to anyone filtering a hub by
licence rather than opening cards. And the agreement inside the **Beta** repo is
headed with the **Alpha** release date: **the instrument was copied forward and
not re-dated**, which is the same template-reuse this document found in the
[RoboCOIN and InternVid gate texts](#the-robot-native-denominator), here applied
by a publisher to itself.

🔴 **And the gate is not "name, affiliation, immediate access."** This document
has used AgiBotWorld-Beta as its example of *most-restrictive licence, minimal
friction*. The actual `extra_gated_fields` are **First Name, Last Name, Email,
Country, Affiliation, Phone, Job title** (a select: Student / Research Graduate /
AI researcher / AI developer-engineer / Reporter / Other), **Research interest**,
and a geo field. **A telephone number is the most intrusive thing any gate in
this survey asks for**, and no other card here requests one. It remains
`gated: auto` — nobody reviews it — so access is still immediate; **what was
wrong was calling it minimal.** *Automatic is not the same as light.*

🟢 **The sibling nobody here had noticed, and it inverts the pair.**
[`agibot-world/AgiBotWorld2026`](https://huggingface.co/datasets/agibot-world/AgiBotWorld2026)
— created 11 Mar 2026, **ungated**, **`license: cc-by-nc-sa-4.0` properly
tagged**, **256,104 downloads** against Beta's **104,421**:

| | AgiBotWorld-Beta | AgiBotWorld2026 |
|---|---|---|
| Licence field | 🔴 **none** — terms only inside the gate prompt | ✅ `cc-by-nc-sa-4.0` |
| Access | `gated: auto`, **nine fields including a phone number** | **ungated** |
| Scale on the card | *(card is 401 unauthenticated)* | 🔴 **none stated anywhere** — the README is a format and download guide |
| Downloads | 104,421 | **256,104** |

> **One sibling has the terms and not the scale; the other has the scale and not
> the terms.** That is the [half-a-card pattern](#omnivitac--tactile-on-the-robot-side-27810-downloads-and-a-card-that-says-only-its-licence)
> appearing **within a single publisher's own namespace**, which is a stronger
> version of it than two unrelated publishers each shipping a different half.
> **And the ungated, properly-labelled, scale-less one is pulled 2.5× more.**

**Across the org, eight of twelve datasets carry no `license:` tag** — including
both flagship corpora, Alpha and Beta. The four that do are the 2026 release,
EWMBench, and the 2025 and 2026 challenge sets.

**Bearing here.** AgiBotWorld is the largest real-robot corpus in the
[denominator](#the-robot-native-denominator) and the one whose terms propagate
hardest: **CC BY-NC-SA is non-commercial *and* share-alike**, so anything trained
on it inherits both, and [OpenWAM's 18.6% mixture share](#openwam--the-first-project-here-whose-open-survives-being-checked)
carries that into Apache-2.0-stamped weights. **The lesson this entry adds is
about where to look**: a pipeline that reads licence metadata would mark the most
propagating licence in this survey as absent, and a pipeline that reads gate
prompts would find it. **The manifest field has to be "terms, and where they were
found" — because on the corpus that matters most, the answer is "in the
agreement, not the metadata."**

### EgoDex

**[arXiv 2505.11709](https://arxiv.org/abs/2505.11709)** (**v3, 9 Mar 2026** —
the version matters here, see below) — 829 hours, **90 M
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
- 🔴 **Licence: CC-BY-NC-ND** — non-commercial **and no derivatives**. This is the
  single most-cited "hands are the payload" dataset in the field and it cannot be
  used commercially, nor can derivative datasets be redistributed. **The terms are
  unchanged. Where they are stated is not** — see the version note below.
- ⚠️ **The access side runs the other way, which is worth knowing.** The Hugging
  Face mirror is gated — an unauthenticated fetch returns **401**. But the zips
  are served straight from **Apple's own CDN**
  (`ml-site.cdn-apple.com/datasets/egodex/…`), and a request there this sweep
  returned **HTTP 200, a 17.3 GB body, no authentication**. So the most
  restrictively *licensed* corpus in this document is also among the most openly
  *accessible*. Splits: ~725 h train, 7 h test, 97 h added after the split was
  frozen — a figure that now survives only in the repo README and the superseded
  paper versions.
- **Limits**: tabletop only; annotation degrades under heavy occlusion and fast
  motion; embodiment gap.

🔴 **The licence statement was removed from the paper. The licence was not.**
Read across all three arXiv versions this sweep:

| Version | Date | Terms stated in the paper? | Appendix A.4 |
|---|---|---|---|
| **v1** | 16 May 2025 | ✅ twice — *"publicly available under a CC-by-NC-ND license"* and *"The dataset is licensed under CC-by-NC-ND terms"* | **Dataset Access** — the 725/7/97 split and the download URL |
| **v2** | 20 Aug 2025 | ✅ the same two sentences | **Dataset Access** |
| **v3** | **9 Mar 2026** | ❌ **zero occurrences of "NC-ND", "non-commercial" or any dataset licence sentence in the body** | **Training Details** — the access appendix is gone |

The scale figures survived the revision untouched — 829 h, 90 M frames, 338,000
episodes, 194 tasks, 2.0 TB on disk, *"over 500 TB"* raw, identical strings in v1
and v3. The rights statement did not. **The terms remain in force**, and they now
survive in exactly two places, both mutable and neither versioned:

- **`github.com/apple/ml-egodex`** README: *"The code in this repository is
  released under the terms detailed in LICENSE. The dataset is available under
  CC-by-NC-ND terms."*
- **`ml-site.cdn-apple.com/datasets/egodex/README.md`**, final line: *"The dataset
  is licensed under CC-by-NC-ND terms."*

> **Why this is worse than it sounds.** arXiv is the archival artefact: immutable,
> version-pinned, and still fetchable at the exact revision a reader cites. A
> README on a CDN is none of those — it can be rewritten with no diff and no
> earlier version to compare against. Between August 2025 and March 2026 the only
> *citable* statement of EgoDex's terms was deleted, leaving the field's
> most-reused hand corpus ([derivation map](#who-feeds-whom--the-derivation-map))
> governed by a sentence at the bottom of a file that carries no history. **Anyone
> citing `2505.11709` for the licence — as this document did — is citing a
> version, not a paper.** Cite `v1` or `v2` for the terms, or cite the README with
> the date you read it.

⚠️ **And the two surviving statements disagree about the size.** The repo README
says **829 hours** across **194** tasks, matching the paper. The CDN README says
**"800+ hours"** across **"~200 diverse tasks"**. One vendor, one dataset, two
files, two renderings of the same two numbers — the second sighting in two sweeps
of a source disagreeing with itself, after
[Ego-Exo4D's 1,286 vs 1,422](#ego-exo4d).

⚠️ **The repo's own `LICENSE` is not CC either.** `apple/ml-egodex` ships a
**bespoke Apple grant** — *"Copyright (C) 2025 Apple Inc… Apple grants you a
personal, non-exclusive license…"* — not an OSI-standard licence. So this one
entry touches three different licences at once: a bespoke Apple grant on the
code, CC-BY-NC-ND on the data, and arXiv's perpetual non-exclusive licence on the
paper. It is the [adjacent-artefact trap](#11-the-licence-trap) with all three
artefacts sitting in the same repository, and the only one of the three a reader
is likely to check by reflex — the file called `LICENSE` — is the one that does
not govern the data.

> **Bearing here.** EgoDex is why the hands gate has no override — 25 joints per
> hand is the payload, and a clip without hands carries none of it. It is also
> exhibit A for §11: the field's favourite reference dataset is one you cannot
> ship a product on.

### EgoScale

**[arXiv 2602.16710](https://arxiv.org/abs/2602.16710)** ·
[project: GEAR @ NVIDIA Research](https://research.nvidia.com/labs/gear/egoscale/)
— a VLA trained on **20,854 hours of action-labelled egocentric human video**,
described as 20× prior efforts. A flow-based VLA: VLM backbone plus a DiT action
expert over a common wrist-level action representation. Two-stage recipe:
large-scale human pretraining, then lightweight aligned human–robot mid-training.
Transfers to a **22-DoF dexterous hand** and down to lower-DoF hands. **+54%
average success rate over a no-pretraining baseline.**

> ⚠️ **Attribution corrected.** An earlier revision of this document credited
> EgoScale to UT Austin RPL on the strength of a lab publication listing. The
> project page sits under **GEAR @ NVIDIA Research**, with a sixteen-author list
> spanning several institutions. Recorded here rather than silently amended,
> because getting provenance right is the thing this document keeps asking of
> everyone else.
>
> **Code is marked "Coming Soon"** — re-verified again this sweep at the GEAR
> project page, which is dated **19 Feb 2026** and still shows
> *"[GitHub (Coming Soon!)]"* — the page is dated **19 Feb 2026** and was re-checked **21 Sep 2026**, so **214 days**, across
> repeated checks. Recorded as a dated observation rather than a prediction — the
> release may still come, but a plan cannot be built on it. The page has shown
> the same thing at every check: no active link, no
> data download, and no terms — and **no dataset licence is stated anywhere**. The arXiv listing carries CC BY 4.0, which governs the *paper* —
> the same trap as [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)
> and [EgoHumanoid](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator),
> where a real licence on an adjacent artefact reads as terms for the data. So
> the largest action-labelled ego corpus in this section is, at time of writing,
> not obtainable and carries no stated terms.

🔴 **EgoScale and DreamDojo appear to be reporting the same corpus, and neither
paper says so.** Read side by side, at source, this sweep:

| | EgoScale | [DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) |
|---|---|---|
| Ego hours claimed | 20,854 | 43,827 crowdsourced (of 44,711 total) |
| Scenes / tasks / objects | **9,869 / 6,015 / 43,237** | **9,869 / 6,015 / 43,237** |
| EgoDex included | **829 h** | **829 h** |
| Environments named | household, industrial, retail, educational | household, industrial, retail, educational, administrative |
| Cites the other | **no** | **no** |

Identical scene, task and object counts, the same 829-hour EgoDex component, and
overlapping environment vocabulary, in two papers from the same lab that do not
reference each other. **The inference — stated as an inference — is that these
are one crowdsourced corpus feeding two products, not two independent
acquisitions.** The hour counts differ, so EgoScale's 20,854 h is most likely a
labelled subset of the pool DreamDojo reports at 43,827 h; nothing in either
paper confirms or denies it.

**Why this matters beyond bookkeeping.** It changes the arithmetic of
[the one-vendor read](#4-world-model-and-physical-ai-stacks): NVIDIA's position
is *not* four independently sourced assets. It is one act of paid acquisition,
amortised across a world model and a VLA. That makes the §13 evidence
*stronger*, not weaker — the field's best-resourced actor did not merely buy its
hours once, it built its entire ego stack on a single purchase, because there
was no second way to get them. And it is a live example of the provenance
problem this document argues for solving per clip: two public artefacts, one
undisclosed shared source, and no way to tell from either paper that using both
does not double your evidence.

Its most useful result for a collection system is methodological: a **log-linear
scaling law between human-data scale and validation loss**, with validation loss
strongly correlated to downstream real-robot performance. That is a defensible
reason to buy hours — and, read carefully, also a reason to care about which
hours, since a log-linear curve is exactly the regime where marginal
undifferentiated hours get expensive.

### EgoScaler — one letter from the entry above, and the first route that needs only RGB

**[arXiv 2509.21986](https://arxiv.org/abs/2509.21986)** (Yoshida, Kurita,
Nishimura, Mori — Kyoto University, NII, Institute of Science Tokyo, Sony
Interactive Entertainment). **This is not [EgoScale](#egoscale).** Different
authors, different country, different arXiv number, different method — and one
character apart in a subfield where both names mean *"scale up egocentric video
for VLAs"*. It is the fourth naming trap in this document and by some distance
the worst, for a reason that has nothing to do with either project:

> 🔴 **EgoScale's artefact has been *"[GitHub (Coming Soon!)]"* for seven months.
> EgoScaler's is released, Apache-2.0, and has been pulled 27,912 times.** A
> reader who half-remembers the name, searches, and finds
> [`Biscue5/egoscaler-v2`](https://huggingface.co/datasets/Biscue5/egoscaler-v2)
> — permissive, ungated, LeRobot format, five figures of traffic — will
> reasonably conclude the debt was paid. **The missing artefact of one project is
> impersonated by the present artefact of another.** What ties that card to *this*
> paper and not the other is one piece of metadata: the `arxiv:2509.21986` tag,
> the same mechanism that tied [OmniRetriever](#omniretriever)'s cards to its
> paper. **Resolve to the identifier.**

**Mechanism — four stages, and what matters is what is absent from them.** Given
a clip: (1) **GPT-4o** identifies the action's start and end timestamps and names
the manipulated object; (2) an open-vocabulary segmentation model (**Grounding
DINO + SAM**) plus a **dense 3D point tracker** extract the object's position
sequence; (3) **point cloud registration** projects that sequence into the
camera frame of the action-start frame, *"eliminating the camera-wearer's
movement"*; (4) **SVD** between consecutive object point clouds yields rotation.
The output is a **6DoF trajectory of the manipulated object**, treated as the
end-effector state of a robot, gripper excluded.

**No depth sensor. No multi-camera rig. No hand-pose recording. No MANO.** The
paper is explicit about why that is the point: prior approaches *"depend on dense
auxiliary recordings, such as hand poses and action start/end timestamps"*, and
*"obtaining these dense auxiliary recordings requires specialized hardware, such
as multi-camera systems or depth sensors, as well as extensive manual
annotation."*

> 🟢 **This narrows **the document's first structural claim** — that every published route across the embodiment gap needs capture conditions somebody controlled — the first narrowing
> that came from the method rather than the corpus.** Every other route across
> the embodiment gap in this document needs capture conditions somebody
> controlled: a calibration board, a headset, object meshes, matched kinematics,
> a tracked wrist. EgoScaler needs **RGB frames and a language description of the
> action**. That is a specification a found clip can meet.
>
> **And it routes around the chokepoint.** By tracking the *object* rather than
> the hand, it never touches MANO — so the licence encumbrance this document
> traces through four layers (annotator, action space, contact mesh, file format)
> simply does not attach. **The most promising known escape from MANO is not a
> better hand model. It is not modelling the hand.**
>
> ⚠️ **What it substitutes is not free either.** **GPT-4o sits in stage one**, so
> a closed commercial API occupies the position that [WiLoR](#wilor--the-chokepoint-read-at-source)'s
> CC-BY-NC-ND model occupies elsewhere — different encumbrance, not less of it,
> and one whose terms govern *outputs* rather than weights. An annotation path is
> a licence surface wherever it runs.

**Scale, and the discard rate.** Applied to **four existing egocentric corpora —
Ego4D, Ego-Exo4D, HD-EPIC and Nymeria** — it produced **124,559 episodes**, of
which rule-based filters (a travel-distance test and a re-projection-error test)
kept **45,157**. 🔴 **A 64% discard rate on automatically extracted
trajectories**, stated plainly, is one of the more honest quality numbers in this
survey — and the closest published analogue to what this repo's acceptance gates
are for.

**The result worth carrying is its diversity table, not its success rate**, and
it belongs beside [the denominator](#the-robot-native-denominator):

| Dataset | Episodes | Verbs | Objects |
|---|---|---|---|
| BridgeData V2 | 53,192 | 270 | 749 |
| Fractal | 87,212 | 6 | 13 |
| **DROID** | **92,233** | **194** | **907** |
| **EgoScaler's set** | **45,157** | **313** | **1,217** |

**Half of DROID's episodes, 1.6× its verbs and 1.3× its objects.** Pre-training
on it improves task success by **over 20% against training from scratch**, is
*"competitive with that achieved using real-robot datasets"*, and **combines with
real-robot data for further gains** — the same complementarity
[HumanNet](#humannet) and [EgoMimic](#egomimic) report, arrived at without any
hand annotation at all.

**Terms.** `Biscue5/egoscaler-v2` is **Apache-2.0**, ungated, **27,912
downloads**, in a **personal** namespace — tied to the paper only by its arXiv
tag, with the model `Biscue5/pi0-egoscaler-v2` alongside. The four source corpora
keep their own terms, which the card does not state — and all four have now been
read at source: **Ego4D** and **Ego-Exo4D** behind signed agreements,
**[HD-EPIC](#hd-epic--41-hours-and-the-densest-annotation-in-this-document)** and **[Nymeria](#nymeria--264-consented-participants-called-in-the-wild)** both **CC BY-NC 4.0**. 🔴 **Not one of
the four is permissively licensed; two are explicitly non-commercial.** The same
gap as [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit),
and worse in one respect: ViTRA's parents include unstated terms, EgoScaler's
include none that are permissive at all.

> **Bearing here, and it cuts both ways.** This is the strongest evidence in the
> document that found footage can be turned into VLA training data by a pipeline
> that needs nothing from the capture — which is the bet this repo is making.
> **But it was applied to Ego4D, Ego-Exo4D, HD-EPIC and Nymeria, not to the open
> web**, so [§13](#13-why-no-open-source-project-does-exactly-this) is untouched:
> the method is found-footage-compatible, the *acquisition* still isn't public.
> The gap between "this could run on web video" and "somebody ran it on web video
> and published how they got the video" is the whole of this repository.

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

🔴 **And this is the strongest counterexample in the document to
[§13](#13-why-no-open-source-project-does-exactly-this) — one that was sitting
inside this entry the whole time.** Re-read at source this sweep, the collection
stage is not "crawling" as a footnote. The paper *"coupled keyword discovery with
content search and retrieval"* and drew candidates from **"video-platform
search, general web search engines, directly crawled videos, open-source
datasets, and self-collection"** — with self-collection described as what
*"complements web-scale acquisition"*, i.e. the web is the primary channel and
the capture is the supplement. **That is requirement-driven mining of the open
internet for real-world human video, at a million hours.** It is a far larger
challenge to §13 than [EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it),
because the footage is real, not rendered, and §13 is narrowed again to account
for it — see [that section](#13-why-no-open-source-project-does-exactly-this)
for what survives and what does not.

**What HumanNet does *not* do is the part that matters here.** It publishes **no
breakdown of the million hours by source**, and **no split between egocentric and
exocentric**. So a reader cannot tell how many of those hours were crawled versus
licensed versus recorded, nor how many are first-person at all. On rights, the
paper says only that *"privacy-sensitive content, unsafe material, and license
constraints are reviewed within the same release pipeline"* — the review is
asserted, the outcomes are not published, and **no dataset licence or public
release strategy appears anywhere in the preprint**. A corpus assembled from
platform search and direct crawling, with per-clip provenance unpublished, is
precisely the artefact this repo's manifest exists to be the opposite of.

**A stronger follow-up result, from the same group.**
[HumanScale](https://arxiv.org/html/2606.20521) (arXiv 2606.20521) curates
**5,000 hours** from HumanNet's egocentric portion and pits it against **5,000
hours of real-robot teleoperation at matched scale**, post-training on 15 AgiBot
manipulation tasks with 100 demonstrations each, against a no-pretraining
baseline and a 20 K-hour robot-pretrained one. Egocentric pretraining reaches
*"a 24% lower validation loss on real-robot action prediction, as well as 52.5%
and 90% higher success rates on in-distribution and out-of-distribution
real-robot task execution."* **At matched hours, that is outperforming, not
matching** — a materially stronger claim than the 1,000 h result above, and it
does not retract the correction beside it, because the two are different
experiments. Code is promised (*"will be released"*); no data licence is stated.

Its four stated limitations are worth reading in full because three of them apply
to any web-collection system, this one included: embodiment gap; irreducible
label noise at scale; uneven geographic / socioeconomic / occupational / body-type
coverage; and **privacy — first-person recordings capture bystanders and
sensitive spaces, third-person recordings capture identifiable people who never
consented.**

### Ego2Robot

**[arXiv 2608.02580](https://arxiv.org/html/2608.02580)** ·
[project page](https://www-ye.github.io/ego2robot_blog/) (HTTP 200, checked) —
converts egocentric human video into robot training data in three stages:

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
UR10e, ViperX, WidowX, Piper, YAM, Aloha-Agilex).

✅ **Every figure above re-verified at the paper this sweep**, quoted: *"ANT (7h,
our in-house pick-and-place dataset with hand pose annotations), EgoDex (732h),
ViTRA (249h), and EgoVerse (954h), totaling ∼1,940 hours of annotated ego
data"*, *"producing 18,561 hours of robot training data spanning 15 robot
morphologies"*, and *"supports both curated datasets and in-the-wild videos."*
These feed the [derivation map](#who-feeds-whom--the-derivation-map)'s
licence-inheritance arithmetic, so they were overdue a check; all hold.

🟢 **And re-reading produced a finding the entry did not have — a per-source
*speed* correction.** Quoted: *"Egocentric hand manipulation exhibits
significantly higher action speeds than robot teleoperation data. To align the
speed distributions, we apply per-source frame subsampling during training: **ANT
and EgoDex are downsampled to 60%** of their original frame rate (~1.7× slower),
**EgoVerse to 45%** (~2.2× slower), and **ViTRA to 25%** (~4× slower)."*

> **Two things follow, and the second is the useful one.** First, **human hands
> move faster than teleoperated robots**, consistently enough to need correcting
> in every source. Second, **the correction factor is not a constant — it ranges
> from 1.7× to 4× depending on which corpus the footage came from.** That is a
> four-fold spread in how much robot-equivalent time an hour of human video is
> worth, decided by capture conditions rather than content.
>
> **For this repo that is a per-clip property, not a per-corpus one.** It is the
> same lesson as
> [OpenX's missing hour count](#the-robot-native-denominator) — *a unit count
> means nothing until you say what a unit contains* — arriving from the time axis
> instead of the content axis. An hour delivered is not an hour trained on, the
> conversion rate varies by source, and **a manifest that records delivered hours
> without recording action speed is quoting a number its buyer has to discount by
> an unknown factor.** The [four hour measures](#12-free-hours-and-what-they-do-to-the-moat)
> this document already keeps are about *what fraction survives filtering*; this
> is a fifth axis about *how fast what survives actually moves*.
with disentangled visual / scene / embodiment / task perturbations, 1:1 mixing
reaches 53.5% (+2.6 pts), with the largest gains in visual robustness (+8%
lighting, +6% colour) and task semantics (+11% unseen objects).

> **Note for anyone reusing this output.** Roughly 38% of its input hours are
> EgoDex, which is CC-BY-NC-ND — non-commercial, no derivatives. Nothing here is
> a claim about the authors' compliance; it is a reminder that **derived corpora
> carry the licence of their inputs**, and that the provenance chain has to be
> checked at the point of *reuse*, which is the posture §11 argues for.

🔴 **And the 38% was the wrong number to worry about, because one of the other
three inputs had never been read.** ViTRA sat in that list as a bare name and a
figure for dozens of sweeps. Reading it (below) closes the chain: **of Ego2Robot's
~1,940 input hours, 7 come from a source with unambiguous terms** — its authors'
own in-house ANT. The rest is EgoDex's CC-BY-NC-ND, EgoVerse's silence, and
ViTRA's four upstream corpora. **0.36%, not 62%, is the fraction that is clearly
clear.**

### ViTRA — 1.2 M episodes of MANO over four other people's corpora, stamped MIT

**[arXiv 2510.21571](https://arxiv.org/abs/2510.21571)** (Microsoft) — named in
this document's [derivation map](#who-feeds-whom--the-derivation-map) as
*"ViTRA 249 h"* since the [Ego2Robot](#ego2robot) entry was written, and never
opened. It is the largest release in this survey that nobody here had read.

**Mechanism.** A fully-automated pipeline turns unannotated egocentric video into
VLA-format training data: atomic hand-activity segments with language
descriptions, framewise **3D hand motion** and **camera motion**, treating the
human hand as a dexterous end-effector so the output aligns with existing robot
VLA data in task granularity and labels. A 3B dexterous-hand VLA is pretrained on
it, shows zero-shot transfer to unseen real observations, and improves with
fine-tuning on a small amount of real robot action data.

**Scale, and a discrepancy worth carrying.** The paper says **1 M episodes and
26 M frames**; the dataset card says **1.2 million short episodes**, and its
per-source table sums to **1,222,918**:

| Source | Episodes | Share |
|---|---|---|
| `ego4d_cooking_and_cleaning` | 454,244 | 37.1% |
| `ego4d_other` | 494,439 | 40.4% |
| `epic` | 154,464 | 12.6% |
| `egoexo4d` | 67,053 | 5.5% |
| `ssv2` | 52,718 | 4.3% |
| **total** | **1,222,918** | **Ego4D alone is 77.6%** |

⚠️ **So "ViTRA 249 h" is not ViTRA's own figure.** ViTRA states episodes and
frames, never hours; 26 M frames at ~29 fps is ~249 h, which is what Ego2Robot
appears to have converted. Nothing is wrong with the number — but a corpus that
publishes frames and is cited in hours is one derivation step further from its
source than it looks, and the fps used to convert is stated nowhere.

🔴 **"In-the-wild… without any annotations" means Ego4D, EPIC-KITCHENS,
Ego-Exo4D and Something-Something V2.** The abstract calls its input *"unscripted
real-life video recordings"* and *"'in-the-wild' egocentric human videos without
any annotations"*; every sample clip on the project page is named
`Ego4D_<uuid>_ep_NNNNNN`, and the card's own `datasets:` field names the four.
The phrase is accurate in its subfield — these are not staged robot-lab captures
— and it is the [second](#the-vocabulary-problem--six-ways-a-name-misleads)
reading a reader of this document would get wrong. **No frame of it came off the
open web.**

**Terms, and the reason this entry matters more than its size.** The dataset
[`VITRA-VLA/VITRA-1M`](https://huggingface.co/datasets/VITRA-VLA/VITRA-1M) is
**MIT**, **ungated**, 2,526 downloads; the model
[`VITRA-VLA/VITRA-VLA-3B`](https://huggingface.co/VITRA-VLA/VITRA-VLA-3B) is
**MIT** too. The MIT is stated twice — YAML front-matter and a *"## License"*
section reading *"This dataset is released under the MIT License."*

✅ **The posture is legitimate and it is the right one**: what ships is
**annotations only**, one `.npy` per episode — MANO shape and pose, per-frame
joints in camera and world space, camera intrinsics and extrinsics, per-hand text
with frame spans, GPT-4 rephrasings, and `video_name` plus `video_decode_frame`
**indices into the original raw video**. ~91 GB of metadata and **not one pixel**.
That is the same arrangement as [EgoVid-5M](#egovid-5m) and
[OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly):
the licence attaches to the authors' own work, and the footage stays under its
own terms.

⚠️ **What is missing is the sentence that makes that legible.** The card names its
sources three times — the `datasets:` field, the per-source episode table, and an
acknowledgement thanking *"Ego4D, Epic-Kitchens, EgoExo4D, and Something-Something
V2 for raw video data"* — and **never states what those sources require**. Two of
them, [Ego4D and Ego-Exo4D](#ego-exo4d), are signed-agreement corpora whose terms
are *not published*; [EPIC-KITCHENS-100](#epic-kitchens-100) is **CC BY-NC 4.0**.
The annotations index into raw video by name and frame number, so they are inert
without those corpora — **a reader who pulls an MIT-stamped 91 GB download has
acquired something they cannot use until they have signed for 77.6% of it**, and
nothing on the page says so. Compare OpenEgo, which ships an `ATTRIBUTION.md`
carrying each source's licence text. *No non-compliance is alleged; the gap is in
the record, not the release.*

> 🔴 **A fourth layer for the MANO chokepoint, and the widest-reaching one.**
> [§11](#wilor--the-chokepoint-read-at-source) tracks MANO at three layers —
> annotator, action space, contact mesh. VITRA-1M adds a fourth: **the
> distributed annotation format itself.** `beta` is *"(10) MANO hand shape
> parameters"*, `hand_pose` is *"(Tx15x3x3) … based on the MANO_RIGHT model"*.
> The file format is MANO. A downstream user does not merely pass through MANO in
> a pipeline they could swap — **they parse it**, and 2,526 downloads a month have.
> A registration-gated hand model is now the schema of an ungated MIT corpus.

> **Two of the three honesties, and the two OpenEgo lacks are not the two ViTRA
> lacks.** [§11](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
> argues no project is honest about **rights**, **distribution** and **quality**
> at once. ViTRA is strong on *distribution* (annotations-only, sources named
> with per-source counts) and — unusually — on **quality**: the card states
> *"metadata has been manually inspected with an estimated annotation accuracy of
> around 90%. Future versions will improve metadata quality."* A stated,
> falsifiable accuracy figure on the annotations themselves is something only
> [Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape) otherwise does here. Where it is weakest is *rights* —
> the exact axis OpenEgo is strongest on. **Two projects, complementary
> two-of-three, and still nobody with all three.** The claim survives, and it
> survives on better evidence: it is now a pattern across two exemplars rather
> than an absence noted once.

🟢 **And ViTRA has a second artefact this document had not opened either —
`microsoft/VITRA-TeleData`, the robot half.** Found on the ModelScope pass of
20 Sep and confirmed on both hubs: **MIT, ungated**, *"real-world robot
teleoperation demonstrations collected using a **7-DoF robotic arm equipped with
a dexterous hand and a head-mounted RGB camera**,"* each episode carrying
synchronised numeric state alongside the video. **It is the one artefact in this
survey whose licence field reads identically on both indexes** — MIT on Hugging
Face and MIT on ModelScope — which after the three contradictions found the same
morning is worth recording as the control rather than as the unremarkable case.

> **Why it matters beyond the licence.** VITRA-1M is 1.2 M episodes of *human*
> hand motion lifted from four other corpora; VITRA-TeleData is *robot*
> teleoperation **with a head-mounted RGB camera on the operator**. The same
> group published both halves of the pairing this section is about — human
> egocentric video on one side, robot demonstrations recorded from an egocentric
> viewpoint on the other — and **the MIT on the robot half is the authors' own
> capture, so unlike VITRA-1M's it is unqualified by anyone else's terms.** The
> download split is its own small fact: **687 on Hugging Face against 34,750 on
> ModelScope**, on counters that are not comparable, but not in a direction this
> document would have guessed.

### EgoEngine

**[arXiv 2606.12604](https://arxiv.org/html/2606.12604v1)** — the fidelity-first
answer to [Ego2Robot](#ego2robot)'s scale-first one, and a useful contrast in
what each gives up. Four stages:

1. **Digital twin reconstruction** — FoundationStereo for depth, SAM2 +
   FoundationPose for object masks and tracking, producing a simulation
   environment aligned to the real camera geometry and object trajectory.
2. **Action generation** — inverse kinematics (MINK) retargets hand poses to
   robot joints, then object-centric trajectory optimisation refines against the
   demonstrated object motion, with **MCTS-style escalation: replay → MPC → RL
   (PPO)** as feasibility demands.
3. **Visual generation** — inpaint the human arms out (Inpaint-Anything v2) and
   render the robot back into the egocentric viewpoint with occlusion-aware
   differential blending.
4. **Policy distillation** — an HPT visuomotor policy with a flow-matching
   decoder trained on the synthetic demonstrations.

**Results.** Simulation success 83% on TACO and 90% on Aria against a replay
baseline's 17% / 10%. On a real RB-Y1 humanoid with a 12-DoF XHand, four tasks
reach 40 / 35 / 70 / 60%, matching or beating real teleoperation on two of them.
Generation runs at 2.88 demos/hour.

> **The ablation is the transferable finding — read from the table this sweep,
> and it does not say quite what this document said it said.** Table 4, averaged
> over the four Aria tasks:
>
> | Setting | Success rate |
> |---|---|
> | Human videos | **0.03** |
> | + visual branch only | **0.05** |
> | + action branch only | **0.43** |
> | **Full EgoEngine** | **0.51** |
>
> The action branch is clearly the dominant term — 0.05 against 0.43 is the
> comparison worth carrying, and it is the one an earlier revision here quoted
> correctly. **What that revision left out is the last row.** Going from the
> action branch alone to the full system is **0.43 → 0.51**, about a **19%
> relative gain** from visual generation, and the paper's own sentence is
> *"Executable action generation provides the primary improvement, **while visual
> generation provides an additional gain**."* This document glossed that as
> *"photorealism is decoration"*, which is a stronger claim than the source
> supports and which happened to flatter the argument being made around it.
> **Corrected: the trajectory is the payload; appearance is a real but secondary
> term, worth roughly a fifth on top.** The direction still favours spending on
> trajectory quality over pixels — it is just not a free choice, and the entry
> should not have implied it was.

🔴 **Its input requirement is the disqualifier for web footage**: it needs
**object meshes and camera calibration** (AprilTag-based for the Aria captures,
heuristic for TACO), plus Aria Gen2 glasses for the self-collected half. Its own
limitations section names digital-twin reconstruction as the bottleneck, with
occluded objects and deformables unresolved. Licence: the paper carries only the
arXiv licence; no code-availability statement, project page at
egoengine.github.io.

> **And the pattern this completes.** Both published routes for turning human
> video into robot data by *reconstruction* — [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject)
> and EgoEngine — carry input requirements the open web structurally cannot
> satisfy: a roughly static camera in one case, object meshes and calibrated
> cameras in the other. That is not a coincidence to note in passing; it is why
> [§8](#8-viewpoint-the-exo--ego-question-answered-three-ways)'s conclusion holds
> generally rather than for one paper. Reconstruction pipelines are built for
> footage whose capture conditions you controlled. For footage you found, the
> viable operations remain **filter, clip and annotate** — which is exactly the
> chain this repo implements.

### EgoMimic

**[arXiv 2410.24221](https://arxiv.org/abs/2410.24221)** — the third strategy,
and the one that solves the embodiment gap by refusing to have one. Rather than
retargeting ([Ego2Robot](#ego2robot)) or reconstructing
([EgoEngine](#egoengine)), it makes the two observation spaces match at capture
time: the human wears **Project Aria glasses** with 3D hand tracking, and the
robot is a low-cost bimanual manipulator *chosen to minimise kinematic difference
from human morphology*. Human and robot demonstrations are then treated as
equally valid embodied data and **co-trained in one imitation-learning
architecture**, instead of mining human video only for high-level intent.

> **The claim worth remembering**: *adding one hour of additional hand data is
> significantly more valuable than one hour of additional robot data.* Read
> beside [HumanNet](#humannet)'s more careful "matched or modestly surpassed",
> the two bracket the same economic case from different setups — which is why
> human-video collection is worth doing at all.

Its footage is self-captured through Aria, not sourced from the web, and its
premise — matched sensors, matched kinematics — is precisely what internet
footage cannot offer. So it belongs in the same column as the reconstruction
pipelines when asking what the open web can feed: **nothing here consumes found
footage**; the strategies differ only in how they arrange the capture they
control.

**Terms, checked at the artefacts** (this entry carried none for sixty-two
sweeps; see [the note on that omission](#corrections-in-one-table)). The code at
[SimarKareer/EgoMimic](https://github.com/SimarKareer/EgoMimic) ships a **MIT**
`LICENSE` — whose copyright line reads *"Copyright (c) 2023 Chen Wang"*, i.e.
inherited from the MimicPlay/robomimic lineage it builds on rather than written
for this release. The data sits at
[`gatech/EgoMimic`](https://huggingface.co/datasets/gatech/EgoMimic): public,
**ungated**, 1,258 downloads, last touched 1 Nov 2024 — and carrying **no
dataset card whatsoever**. The API returns `cardData: null` and a single tag,
`region:us`. There is no licence field, no terms, no README.

> ⚠️ **Two things are true at once here, and the second is easy to miss.** The
> repo's own README labels the link a **"Sample Dataset"**, and the artefact
> matches: six HDF5 files — human and robot for each of *groceries*,
> *smallclothfold* and *bowlplace*. So EgoMimic is simultaneously **partially
> released** (three tasks of the paper's set, as a sample) and **terms
> unstated** (an ungated public download with nothing attached saying what may
> be done with it). It is the cleanest instance in this document of a dataset
> that is *maximally easy to obtain and entirely unspecified to use* — the
> opposite corner from a gated permissive release, and the corner readers
> misread most often, because frictionless download reads as permission.

### EgoAVFlow — "no robot demonstrations" still means a board in every scene

**[arXiv 2602.22461](https://arxiv.org/html/2602.22461v1)** (CC BY 4.0) — the
cleanest single refutation in this document of the idea that a method
advertising freedom from robot data is therefore compatible with found footage.

**Mechanism.** A shared **3D flow** representation carries manipulation and
*active vision* together: diffusion models predict robot actions, future 3D
flow, and camera trajectories, then refine the viewpoint at test time by
reward-maximising denoising under a visibility-aware reward computed from
predicted motion and scene geometry. It "transfers without robot
demonstrations." Its three reported findings are worth having: fixed viewpoints
cannot reliably maintain visibility during manipulation; directly imitating
human viewpoints is insufficient for visibility-aware adjustment; conditioning
on 3D flow is strongest under actively varying viewpoints.

**What it demands of the video, which is the whole point here.** Not RGB —
**RGBD**, from a **head-mounted RealSense D435**. 2D pixels are tracked with
CoTracker3, unprojected using the depth channel, and camera poses recovered with
DROID-SLAM. And then, verbatim:

> "Egocentric human videos exhibit diverse initial states, which leads SLAM to
> produce a different world coordinate frame for each demonstration. To express
> trajectories in a consistent reference frame, we convert all 3D quantities
> into a marker coordinate system defined by a **ChArUco board**."

**Scale and release.** **150 egocentric human videos per task, across 4
manipulation tasks.** No dataset release stated; a project page is referenced
without a code or data availability statement.

**Why it matters here.** Every prior entry in this section needed something at
capture time — meshes and calibration, an approximately static camera, the
demonstrator wearing your glasses. EgoAVFlow needs a **depth sensor on the head
and a printed calibration target physically present in the scene**. A YouTube
video has neither and can never be made to have them retroactively. The
strategy list in this section is now four deep and the conclusion has not
moved: for footage you found rather than shot, the viable operations remain
filter, clip, annotate.

### Zeva-Ego — the first published exchange rate, and a named consumer of the free ten thousand hours

**[arXiv 2609.24411](https://arxiv.org/abs/2609.24411)** (v2, 22 Sep 2026;
CC BY 4.0 listing; AIR @ Tsinghua + Z-Trans AI) ·
[project page](https://air-embodied-brain.github.io/Zeva-Ego/) — read three days
after posting, and it supplies the number every entry in this section has been
circling without stating.

🟢 **An ego-to-robot exchange rate, published as a ratio.** *"Scaling Ego data to
10K hours improves RoboTwin success from **63.8% to 75.3%**, matching **2K hours
of robot demonstrations (74.7%)**, corresponding to an empirical data ratio of
roughly **4–5 : 1**."* Same π₀.₅ initialisation on both arms of the comparison.

> **Nothing else in this survey states one.** [HumanNet](#humannet) gives 1,000 h
> ego against 100 h robot, [HumanScale](#humannet) gives 5,000 against 5,000 at
> matched scale, [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)
> fixes a 600-hour budget and splits it, [ReWeight](#reweight--the-control-simdex-did-not-run)
> and [UMI-Bridge](#simdex) compare mixtures, and
> [AtomEgo](#atomego--a-provenance-table-that-restates-four-corpora-at-once)
> gives a product with no units. **Zeva-Ego prices the substitution**, and a
> price is what a found-footage pipeline actually needs: it converts "an hour of
> web video is worth something" into **"you need four to five of them to stand in
> for one teleoperated hour."** ⚠️ *Read it at its own scope — one benchmark
> (RoboTwin), one initialisation, one mixture. It is a measurement, not a law,
> and this document has been burned by treating a single well-constructed number
> as one.*

**And the second result is the one that changes deployment economics.**
**In-Context Causal Learning** encodes executed actions and their observed
effects as causal evidence, retrieves phase-relevant prior experience, and
conditions low-level generation on it — *"parameter-free adaptation from
action-effect feedback at deployment."* Reported: **58% → 89% within four
attempts, with model parameters frozen.** If the offline prior is what hours buy,
this is the argument that the *last* few points are bought at runtime instead.

🔴 **Now the part that belongs to [§12](#12-free-hours-and-what-they-do-to-the-moat):
Zeva-Ego is a named, published consumer of [Egocentric-10K](#egocentric-10k), and
it threw away more than half of it.** The paper's data section:

> *"Egocentric-10K records real factory work through wearable monocular cameras.
> The public release totals **10,000 hours, 192,900 clips, and 1.08 billion
> frames at 30 Hz** … **We use 4,439 hours selected through task-stratified
> sampling.** The source release does not include **frame-aligned hand poses or
> action trajectories**."

**A 55.6% discard on a corpus that cost nothing.** This document's §12 has argued
that free hours set the floor price of an undifferentiated hour at zero and that
selection is where the value sits; **here is a team doing exactly that, in
print, on the specific corpus the section is about** — and stating, in one
clause, precisely what the free release lacks. That last sentence is the
**acceptance specification written by a consumer**, the third this survey has
found after [Being-H0.5's](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms) *"accurate depth, stable camera alignment,
temporally precise interaction events"* and
[ReWeight's](#reweight--the-control-simdex-did-not-run) selection result.
*(Note the arithmetic that follows from it: if 4–5 ego hours substitute for one
robot hour and 55.6% of a free corpus is discarded before use, then **ten free
hours buy roughly one robot hour** — which is the honest version of the moat
argument, and a weaker one than "hours are abundant" implies.)*

🔴 **Read that arithmetic as Zeva's, not as a constant — the next entry breaks
the discard term.** [EgoSmith](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table)
keeps **288 of the same 10,000 hours (2.9%)** where Zeva keeps 4,439 (44.4%) —
**a fifteen-fold difference on identical input**, and the publisher says why:
*"to filter out highly repetitive videos, we subsample."* **The usable fraction
of a free corpus is a property of the selection objective, not of the corpus**,
so *ten free hours per robot hour* is one lab's exchange rate under one lab's
objective and this document should not have printed it as though it were the
field's.

⚠️ **Release**: the project page names
[`github.com/air-embodied-brain/Zeva`](https://github.com/air-embodied-brain/Zeva)
— unreadable from this environment, which 403s `github.com` — and **no dataset**;
the mixture is other people's corpora. Both standing artefact checks (the
`arxiv:`-tag query on Hugging Face, and ModelScope) **return nothing** for
`2609.24411`.

### EgoSteer and EgoSmith — the annotate stage, released, with a per-source licence table

🔴 **This is the most directly relevant project in the survey and it had no entry
until the ninety-fifth sweep.** The paper is three months old, the artefacts are
Apache-2.0 and ungated, and every standing check this document runs would have
found them; none was pointed here. Recorded first, because the finding about the
survey is larger than any single number below.

**[arXiv 2607.09701](https://arxiv.org/abs/2607.09701)** (v1, 21 Jun 2026) —
*EgoSteer: A Full-Stack System Towards Steerable Dexterous Manipulation from
Egocentric Videos*, from PKU's Institute for AI and the PKU–PsiBot Joint Lab.
Project page [`egosteer.github.io`](https://egosteer.github.io/). **It
open-sources the pipeline, the labels, the real-robot data, the models and the
training code** — the combination [§13](#13-why-no-open-source-project-does-exactly-this)
keeps reporting that nobody ships.

**What exists, all read at the artefact:**

| Artefact | What | Licence | Access | Counter |
|---|---|---|---|---|
| [`EgoSteer/EgoSteer-Egocentric`](https://huggingface.co/datasets/EgoSteer/EgoSteer-Egocentric) | **labels only** — wrist pose, fingertips, camera pose over 8 source corpora; **no images, no video** | 🟢 **per-source, tabulated** (see below) | **ungated** | 285 |
| [`EgoSteer/EgoSteer-RealWorld`](https://huggingface.co/datasets/EgoSteer/EgoSteer-RealWorld) | **54,454 teleoperated episodes, 192 h, 20.75 M frames, 193 tasks**, bimanual RealMan + two dexterous hands, head and chest RGB-D, free-form English per episode, LeRobot v3 | 🟢 **Apache-2.0** | **ungated** | **7,527**, 8 likes |
| [`EgoSteer/EgoSteer-3B-Base`](https://huggingface.co/EgoSteer/EgoSteer-3B-Base) | world-model-enhanced VLA on Qwen3-VL-2B + DINOv3, pre-trained on the 9.6 K egocentric hours | 🟢 **Apache-2.0** | ungated | 23, 9 likes |
| `EgoSteer/EgoSteer-3B-RealMan` | the same model grounded on the real-robot set | 🟢 **Apache-2.0** | ungated | 23 |
| `github.com/egosteer/{egosmith, robot-stack, egosteer}` | pipeline, teleop/deploy stack, model and training | — | ⚠️ **unreadable here** — the proxy 403s `github.com` | — |

🟢 **The licence table is the thing this document has been asking for, and
somebody shipped it.** `EgoSteer-Egocentric` carries `license: other`,
`license_name: per-dataset-see-readme`, and then a README table with **two
licence columns** — the source's and the labels' — plus a vendored
`LICENSES/<source>/LICENSE.txt` and `NOTICE.txt` in every folder:

| folder | source licence | labels licence | episodes | frames |
|---|---|---|---|---|
| `taco/` | CC-BY-SA-4.0 | CC-BY-SA-4.0 | 1,977 | 304,054 |
| `oakink2/` | CC-BY-SA-4.0 | CC-BY-SA-4.0 | 887 | 169,881 |
| `egodex/` | **CC-BY-NC-ND-4.0** | **CC-BY-NC-4.0** | 147,588 | 37,061,953 |
| `holoassist/` | CDLA-Permissive-2.0 | CC-BY-4.0 | 11,426 | 1,148,545 |
| `epic_kitchens/` | CC-BY-NC-4.0 | CC-BY-NC-4.0 | 108,077 | 4,936,621 |
| `ego4d/` | custom (signed agreement) | CC-BY-NC-4.0 | 584,042 | 13,770,599 |
| `egocentric_10k/` | Apache-2.0 | **CC-BY-4.0** | 194,225 | 47,860,714 |
| `egocentric_100k/` | Apache-2.0 | **CC-BY-4.0** | 496,357 | 237,603,974 |
| **total** | | | **1,544,579** | **342,856,341** |

**Compare that with every other row in [§11](#11-the-licence-trap).**
ShareAlike propagates where it should, on both CC-BY-SA sources; **both
non-commercial sources keep NC**; and the Ego4D labels are released **NC even
though Ego4D's licence is a bilateral agreement that says nothing at all about
derived labels** — the one row where the publisher had the most room to claim
whatever it liked, and took the narrow reading.

⚠️ **One cell is a claim rather than a reading, and it is the interesting one:
`egodex/` drops the ND.** [EgoDex](#egodex) is **CC-BY-NC-ND-4.0** — *No
Derivatives* — and 37.1 M frames of hand poses estimated from that video are
released as **CC-BY-NC-4.0**, which permits derivatives. Either estimated pose
labels are not a derivative work of the video, or the relicensing does not
follow. **This document does not resolve that** — it is a question for a lawyer,
not a sweep — but it records that the most carefully licensed artefact in the
survey still contains one step that has to be argued rather than read. *A
provenance table is not a permission.*

🟢 **And the pixels are re-attachable, with a shipped tool rather than a
promise.** Every frame names its source recording and frame number, and
`rehydrate.py` (20 KB, in the repo) lists the source files a folder needs, pulls
the indexed frames from **your** copy of the source dataset, applies the
undistortion and resize, and writes a complete LeRobot dataset. The README is
blunt about why it cannot do more: *"The source datasets need registration or a
signed agreement, so they cannot be fetched automatically."* **This is the
URLs-only pattern applied to annotations** — the shape
[LAION-BVD](#laion-bvd--it-shipped-and-this-document-said-it-hadnt) and [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
use for video, here used for labels, and it is the correct answer to the rights
problem [§11](#11-the-licence-trap) spends a section on.

> ⚠️ **One detail in that tool is worth lifting out**, because it is the kind of
> thing that silently corrupts a corpus: `source_frame_index` is *"frame number
> counted in decode order from the start of the media; **never convert it from
> time**."* HoloAssist's media is variable-frame-rate at 27.5–30 fps, and
> EPIC-KITCHENS is native 50/59.94. **Anyone building this stage themselves will
> reach for a timestamp**, and on two of these eight sources that silently
> misaligns the labels. It is recorded here as a build-vs-reuse argument of its
> own.

🔴 **The composition of the 9.6 K hours is the strongest number
[§12](#12-free-hours-and-what-they-do-to-the-moat) has, and it is not close.**
The paper tabulates all twelve sources:

| Source | Hours | % | Episodes |
|---|---|---|---|
| **[Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)** | **8,049** | **83.8** | 1,795,731 |
| [EgoVerse](#egowam--and-what-in-the-wild-turns-out-to-mean) | 690 | 7.2 | 35,175 |
| [EgoDex](#egodex) | 370 | 3.9 | 147,588 |
| **[Egocentric-10K](#egocentric-10k)** | **288** | **3.0** | 194,915 |
| [Ego4D](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads) | 138 | 1.4 | 74,505 |
| EPIC-KITCHENS | 49 | 0.5 | 26,454 |
| HoloAssist | 11.5 | 0.1 | 11,426 |
| HOT3D | 4.5 | 0.05 | 1,105 |
| TACO | 3.0 | 0.03 | 1,558 |
| OakInk-v2 | 1.7 | 0.02 | 891 |
| H2O | 1.0 | 0.01 | 935 |
| FPHA | 0.5 | 0.01 | 578 |
| **Total** | **9,606** | 100 | **2,290,861** |

**86.8% of the hours that pre-trained this model are Build AI's two free
Apache-2.0 corpora.** Not a supplement, not a control — **the corpus is the free
hours, and everything else is the remaining 13%.** And the scaling curve is
published: models pre-trained on **3 K / 6 K / 9.6 K hours** plus a
from-scratch baseline, post-trained identically and evaluated on ten real-robot
tasks, show pre-training loss converging lower and real-world success and
progress rising monotonically with the free hours, *"with expanding pre-training
data, the policy exhibits the emergence of failure recovery, enhanced
instruction-following."* [Zeva-Ego](#zeva-ego--the-first-published-exchange-rate-and-a-named-consumer-of-the-free-ten-thousand-hours)
gave one point and a ratio. **This gives four points and a direction**, and it is
the second named consumer of the free corpus in three sweeps.

🔴 **Which forces a correction to a number this document derived.** §12 says, from
Zeva-Ego, that *ten free hours buy roughly one robot hour*, computed on
Zeva's **55.6% discard** of Egocentric-10K. **EgoSmith keeps 288 of the same
10,000 hours — 2.9%** — and **8,049 of Egocentric-100K's 100,405 — 8.0%.** Two
published cuts of the same free corpus, **44.4% and 2.9% retained, a fifteen-fold
difference.** The cause is stated by the publisher and is not quality:
*"to filter out highly repetitive videos, we subsample Egocentric-10K and
Egocentric-100K."* **So the usable fraction of a free corpus is not a property of
the corpus.** It is a property of what you are selecting for, and this document's
ten-to-one figure should be read as *Zeva's* exchange rate under *Zeva's*
objective, not as a constant. The moat argument survives — it gets stronger, not
weaker, when 8% of a free corpus trains a working VLA — but the tidy number does
not.

⚠️ **The released labels are not the paper's corpus, and nothing says so.** Put
the two tables side by side and they disagree on every shared row but two:

| Source | paper's corpus (episodes) | released labels (episodes) |
|---|---|---|
| Egocentric-100K | 1,795,731 | **496,357** |
| Ego4D | 74,505 | **584,042** |
| EPIC-KITCHENS | 26,454 | **108,077** |
| Egocentric-10K | 194,915 | 194,225 |
| EgoDex | 147,588 | 147,588 ✅ |
| HoloAssist | 11,426 | 11,426 ✅ |
| TACO | 1,558 | 1,977 |
| OakInk-v2 | 891 | 887 |

**Ego4D is nearly 8× larger in the release; Egocentric-100K is a quarter the
size; EgoVerse, HOT3D, H2O and FPHA are absent from the release entirely.** The
paper reports **1.04 B frames**; the release holds **342.9 M**. Neither artefact
claims to be the other, and this is not alleged as an error — **but a reader who
downloads `EgoSteer-Egocentric` expecting "the 9.6 K-hour corpus" has a different
cut in their hands**, heavier on the corpus with the strictest access terms and
lighter on the one that supplied five sixths of the hours. **Count artefacts, not
papers** is the same rule [EgoWild2Dex](#egowild2dex--a-ninth-in-the-wild-and-the-first-measured-number-for-why-it-is-hard)
produced, applied to a project that did release.

⚠️ **Two internal figures disagree, in the paper and across the card.** The paper's
prose says the pipeline *"yields a fully-annotated egocentric dataset comprising
9.60 K hours, **2.09 M episodes**, and 1.04 B frames"*; its own composition table
totals **2,290,861 episodes** — a 200 K gap between a sentence and the table two
pages later. And the real-robot set is **187 hours** in the paper's contribution
list and **192 hours** on the Hugging Face card, at the same 193 tasks. Both are
small; both are recorded, because this survey's standing finding is that the
circulating number and the artefact's number differ more often than not, and it
holds even for the most carefully documented release in it.

📌 **A tenth "in the wild", and for once the meaning is pinned by the publisher
rather than inferred.** EgoSmith *"curates in-the-wild egocentric videos"* — and
because the labels release enumerates its sources with frame counts, the phrase
can be resolved exactly: **twelve existing research and vendor corpora, zero
found footage.** Same answer as the previous nine, arrived at from the artefact
instead of from a reading of the prose.

**Bearing on this repo, and it is the sharpest yet.** EgoSteer is what the
*annotate* stage looks like when somebody finishes it: an open pipeline, 342.9 M
frames of labels with per-source rights, a rehydration tool, and an Apache-2.0
model that demonstrably improves as the free hours scale. **What it is not is a
route from internet video to egocentric video** — EgoSmith's input is already
egocentric and already curated, twelve datasets that somebody else recorded. So
[§13](#13-why-no-open-source-project-does-exactly-this) survives, narrowed for
the fourth time: **the crawl stage is solved and permissively licensed
([LAION-BVD](#laion-bvd--it-shipped-and-this-document-said-it-hadnt)); the annotate stage is now solved and permissively
licensed (EgoSteer); what is still missing is the middle — deciding which
internet video is egocentric, and clearing the rights on it clip by clip.** That
middle is smaller than it was three sweeps ago, and it is still the whole
proposition.

### EgoWild2Dex — a ninth "in the wild", and the first measured number for why it is hard

**[arXiv 2609.23755](https://arxiv.org/abs/2609.23755)** (v1, 20 Sep 2026;
HKU MMLab + Kinetix AI) ·
[project page](https://mmlab.hk/egowild2dex/) — the title makes the claim this
document tests every time it appears, and **the answer is the same for the ninth
time.**

**What its *in the wild* means.** *"Unlike prior approaches that often collect
such data in constrained or specially constructed environments, we collect
in-the-wild egocentric demonstrations in real-world settings, including **homes,
factories, and pharmacies**, etc., where **people perform their ordinary tasks
while wearing head-mounted cameras**."* So: **commissioned capture, of ordinary
work, in venues nobody controlled.** A real and useful axis — and **not found
footage.** [§13](#13-why-no-open-source-project-does-exactly-this) survives a
ninth naming test, and the sense is the same one
[SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
turned out to have after its own correction: *instrument the people already doing
the job.*

🟢 **And it supplies something this survey has wanted and never had: a measured
number for why uncontrolled egocentric video is hard.** *"Visually challenging
observations due to scene clutter and head-motion-induced viewpoint changes (**a
mean cumulative rotation of 15.93°/s**)."* Every entry here that addresses camera
instability — [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)'s
alignment, [MEgoVista](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)'s
metric depth, EgoWAM's reliance on Aria VIO poses — addresses it qualitatively.
**15.93°/s is the first figure putting a size on the problem**, and it is the
kind of number a viewpoint-acceptance gate can be calibrated against.

**Mechanism.** **GeoFormer**, a differentiable geometric transformer that *warps
noisy human observations toward robot observations*, plus a progressive
human→robot training scheme. Reported **96.7% average success across three
long-horizon bimanual dexterous tasks.**

**The corpus, and one figure in it is an outlier.** *"We release **EgoWild**, a
**538.9-hour** in-the-wild egocentric human dataset comprising **179,049
episodes**, **125,961 unique task descriptions**, and **1,282 object
categories**."* 🔴 **125,961 unique task descriptions is, by a wide margin, the
largest task vocabulary in this survey** — against
[DreamDojo's GPT-estimated 6,015](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13),
[AgiBotWorld's 217](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate)
and [DROID's 84](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it).
⚠️ **Treat it as a different unit rather than a bigger number**: 125,961
*descriptions* across 179,049 *episodes* is roughly **0.7 per episode**, which is
a free-text caption count, not an enumerated task taxonomy. **It is the
[unit problem](#atomego--a-provenance-table-that-restates-four-corpora-at-once)
again, and this time the unit is the interesting part** — a long-tailed
description space is exactly what a found-footage corpus would also produce, and
exactly what a 217-task taxonomy cannot represent.

🔴 **Release: a present-tense claim, a live page, and no artefact.** The paper
says *"we release EgoWild."* The project page **resolves** and describes the
dataset — *"538.9 hours of unscripted ego-human behaviour in homes,
factories…"* — and links to the arXiv PDF, the lab and the company, **and to no
download anywhere**. Both standing checks come back empty: **no Hugging Face
artefact tagged `arxiv:2609.23755`, nothing under the name on either hub, nothing
on ModelScope.** **No licence is stated for the data anywhere**, and the arXiv
listing carries the bare *"perpetual non-exclusive license"*, not CC BY.

> **This is the [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)
> shape with one part added.** MINT said *"we release"* and named **no URL at
> all**. EgoWild2Dex says *"we release"* and names **a page that exists, loads,
> and describes the thing — without carrying it.** A reader who checks whether
> the paper names a surface gets *yes*; a reader who follows it gets nothing.
> **For §13's prospective tally that is the sharpest argument yet for counting
> *"does the artefact exist"* rather than *"is a surface named"***, because the
> two now come apart in a case where the surface is real.

### EgoWAM — and what "in-the-wild" turns out to mean

**[arXiv 2607.08436](https://arxiv.org/abs/2607.08436)** (CC BY 4.0, Georgia
Tech RL²) — a **naming trap of the same family as
[Ego-1K](#ego-1k)**, and worth recording for exactly that reason.

The title promises "World Action Models Beyond Pixels with **In-the-Wild**
Egocentric Human Data," and the headline result is that "WAM co-training scales
more effectively with in-the-wild egocentric human data than behavior cloning."
A reader scanning §13 would flag it immediately: has someone finally trained on
found footage?

No. **The in-the-wild human data is [EgoVerse](#egoverse)** — the "full
EgoVerse-A flagship split per task," at roughly **10:1 against robot data**,
with an in-domain human regime at 1:1 (matched to 300–360 robot demos per task)
as the comparison. EgoVerse is captured on **Project Aria glasses**. And the
dependency runs deeper than provenance: EgoWAM's 3D flow is obtained by feeding
a pretrained point tracker **"with Aria VIO camera poses, so the returned point
positions share a consistent world frame."** The method's world-frame
consistency is supplied by the capture device's own visual-inertial odometry.

**So "in-the-wild" here means *outside the robot's lab*, not *off the open
web*.** That is a legitimate and useful axis — unmatched viewpoints, unmatched
behaviour, scenes the robot never saw — and the paper is not overclaiming
within its own field's usage. But the phrase does not survive translation into
this document's vocabulary, and a survey that took it at face value would
report the opposite of what §13 finds.

**The methodological result is still worth stealing.** Holding backbone, action
head and data mixture constant and varying *only* the world-prediction target,
DINO-based prediction gave up to **4× out-of-distribution generalisation** and
3D flow gave **20–30% in-domain**. Predicting scene evolution, not just actions,
is where the human-video gain lives — which is an argument for annotating what
happens next in a clip, not only what is in it.

### OpenWAM — the first project here whose "Open" survives being checked

**[arXiv 2609.07398](https://arxiv.org/abs/2609.07398)** (7 Sep 2026, 24
authors) — a world-action model stack in the same family as
[EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) and
[Being-H0.7](#being-h07--one-corpus-three-products-and-a-second-vendor-doing-it),
and this document's **positive control** for a trap it has caught three times.

**The premise is methodological, not scalar.** Existing world-action systems are
*"monolithic: the generative backbone, visual representation, architecture,
information flow, inference procedure, and training data are tightly coupled,
obscuring which design choices matter and why."* **OpenWAM-Infra** factorises
that design space into composable modules with unified training, inference,
deployment and evaluation; **OpenWAM-Study** then runs controlled experiments
over it. Three stated principles: upstream knowledge transfers through a
*"sufficiently capable generative backbone and a compact, information-rich latent
space"*; world–action synergy needs *"dedicated action capacity, explicit
world-to-action information flow, and synchronized joint denoising"*; and
embodied pretraining *"principally improves out-of-domain generalization"*, with
one-stage co-training over egocentric and robot data. **OpenWAM-α** is pretrained
on roughly **6,400 hours** of egocentric human and robot data.

**Its pretraining mixture, read off Table 4 of the PDF** — *"Full"* is each
source's raw size, *"Curated + Sampled"* what actually trained the model, and
*"Share"* its per-epoch sample share:

| Source | Type | FPS | Full frames / hours | Used frames / hours | Share |
|---|---|---|---|---|---|
| **Egocentric data (theirs)** | human video | 30 | 744.9 M / **6,897 h** | 155.7 M / **1,442 h** | **30.1%** |
| **AgiBotWorld-Beta** | real robot | 15 | 124.5 M / 2,306 h | 96.9 M / 1,794 h | **18.6%** |
| **RoboCOIN** | real robot | 30 | 104.5 M / 956 h | 74.1 M / 686 h | 14.3% |
| **DROID** | real robot | 10 | 46.3 M / **1,285 h** | 36.3 M / 1,007 h | 7.0% |
| **InternData-A1** | simulation | 30 | 313.7 M / 2,904 h | 155.5 M / 1,440 h | 30.0% |
| **Total** | 21 robot + human | | 1,333.9 M / **14,348 h** | **518.5 M / 6,369 h** | 100% |

**Three things fall out of that table, and each matters to a different part of
this document.**

🔴 **1. The egocentric 30% is the lab's own unreleased corpus.** The row is
headed *"Egocentric data (**ours**)"*, and the text describes *"a dataset we
carefully constructed for manipulation-centric world modeling — 71.6 K long-form
first-person recordings… covering **3,006 everyday manipulation tasks**"*. So the
most open release in this survey is pretrained on **6,897 hours nobody else can
have**. **That is §13 arriving in its most favourable case**: a team publishes
twenty checkpoints, the code, the benchmarks and the evaluation harness, and the
one thing that stays in-house is the corpus. *(The paper also gives a
per-recording duration that this document's PDF text extraction renders
ambiguously and which does not reconcile with 6,897 h on either reading, so it is
not quoted here — 71.6 K recordings and 3,006 tasks are the figures that
verified.)*

🔴 **2. AgiBotWorld-Beta is 18.6% of the mixture — and it is CC BY-NC-SA 4.0.**
Non-commercial **and share-alike**, the most restrictive combination in this
survey, feeding **Apache-2.0** checkpoints. **This is the third fully traced case
of a permissive stamp over non-permissive parents**, after
[ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)
and [EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb),
and it is the one where the terms are designed to propagate: ShareAlike exists
precisely to travel into derivatives. *Nothing improper is alleged — weights
trained on data are not obviously a derivative work of it, and that question is
unsettled everywhere. The point is narrower: **the mixture table is in the paper,
and the licence consequence is in neither the paper nor the model cards.***

⚠️ **3. DROID appears here as 1,285 hours. Its own page says 350.** A **3.7×**
restatement of the corpus this document uses as
[the denominator](#the-robot-native-denominator). The likely reason is the
[Nymeria pattern](#nymeria--264-consented-participants-called-in-the-wild) —
DROID records **two Zed 2 stereo cameras plus a wrist Zed Mini**, so camera-hours
multiply wall-clock hours — but **neither paper says which unit it is using.**
This is the first case in this survey of **the same corpus counted differently by
two publications**, and it is worse than a project overstating its own scale:
**a reader comparing hour-counts across papers is silently comparing different
units.** The denominator section states 350 h because that is what DROID's own
page states; the 1,285 is recorded here as unexplained rather than used.

🟢 **And the ablation is the most carefully controlled substitution experiment in
this document, because the budget is fixed.** Under *"an identical **600-hour
data budget**"*, drawing egocentric human video from **[EgoDex](#egodex)** and
robot trajectories from RoboCOIN: robot-only spends all 600 h on robot data; the
two mixed variants spend **350 h egocentric + 250 h robot**, either two-stage
(ego then robot) or one-stage co-training. Result, quoted: embodied pretraining
*"yields modest gains for in-domain performance, but… strong performance gains in
OOD evaluation"*, and **"robot-only pretraining yields the strongest ID
performance, while both mixed strategies generalize better OOD."**

> **That is a trade-off, not a win, and it is more useful than a win.**
> [HumanNet](#humannet) compared 1,000 human hours against 100 robot hours —
> unequal budgets. [ReWeight](#reweight--the-control-simdex-did-not-run) showed
> that *which* human hours you pick is worth 13 points. OpenWAM asks the third
> question: **at a fixed budget, how should the hours be split** — and answers
> that robot hours buy in-domain fit while egocentric hours buy generalisation.
> **For a collection system that means the product is not "hours" and not even
> "good hours", but hours whose contribution can be predicted**: a buyer with 600
> hours of budget needs to know which axis they are short on before they know
> what to buy.
>
> **And note what the egocentric data is allowed to do.** Because it *"carries no
> robot action labels… its action and proprioception channels remain fully masked
> and it supervises only the world stream."* **Unlabelled egocentric video trains
> the model's picture of how the world moves, not its picture of what to do.**
> That is the cleanest statement in this survey of the ceiling on raw hours — and
> the precise reason [§12](#12-free-hours-and-what-they-do-to-the-moat)'s free
> corpora are worth less than their size suggests.

✅ **And then it ships, which is the finding.** Checked at the artefacts this
sweep: **20 model repositories in the `OpenWAM` organisation, every one
Apache-2.0 and ungated** — the pretrain foundation model plus per-platform
checkpoints (Franka, ARX-X5, Piper, a dexterous hand) and per-benchmark ones
(LIBERO, RoboCasa365, RoboCasa-GR1, RoboTwin, VLABench, EBench) — **six
datasets**, and an **Apache-2.0 `LICENSE`** on the code repository. The paper's
own comments field names three surfaces — project page, code, *"Model & Data"* —
and **all three resolve**.

> **Why this belongs in the document rather than in a footnote.** This survey has
> now caught the openness claim failing three times:
> [OpenMMEgo](#openmmego--open-weights-and-data-half-kept)'s title promises *"Open
> Weights and Data"* over a year-old *"we will release our code and data soon"*;
> [Open-AoE](#open-aoe) is *"Open"* under a bespoke one-publisher licence;
> [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)
> says *"we release"* and gives no address. **A trap catalogue with no control row
> is just a complaint.** OpenWAM is the control: **the same word in the same
> position in the title, and the artefacts are there.** It is the counterpart to
> [HoloAssist](#holoassist) in the licence audit — the entry that was right, kept
> visible so the failures mean something.

⚠️ **Two qualifications, because the control has to be read as carefully as the
failures.** First, **three of the six datasets carry no licence tag at all**
(`RoboCasa365`, `RoboCasa_GR1`, `wuji_teleop_data_subset`); the other three are
MIT or Apache-2.0. **Even the best release in this survey has unstated terms on
half its data.** Second, and more to the point of
[§13](#13-why-no-open-source-project-does-exactly-this): **the six datasets are
benchmarks, assets and a teleoperation *subset*. The ~6,400-hour pretraining
corpus is not among them.** Twenty checkpoints ship; the thing they were trained
on does not. **That is the document's standing observation arriving in its most
favourable possible case** — when a team does everything else right, the
acquisition layer is *still* the last thing published.

### EgoHumanoid — whole-body transfer, and a VR rig on the demonstrator

**[arXiv 2602.10106](https://arxiv.org/abs/2602.10106)** (v2, 4 Jun 2026) ·
**[OpenDriveLab/EgoHumanoid](https://github.com/OpenDriveLab/EgoHumanoid)**
(RSS 2026) — *"the first framework to co-train a vision-language-action policy
using abundant egocentric human demonstrations together with a limited amount of
robot data."* ⚠️ **The paper is cited here for the first time this sweep**: the
entry had stood on the repository alone, so its headline number had never been
read at a primary source. It extends this section's question from hands
to the whole body: not just what the demonstrator grasped, but where they walked
to do it.

**Mechanism.** A vision-language-action policy co-trained on abundant egocentric
human data plus limited robot teleoperation, bridged by two explicit steps —
**view alignment**, via depth-based warping and inpainting, and **action
alignment**, with navigation velocities derived from body pose and discretised
into commands.

✅ **Reported gain, now quoted rather than paraphrased: *"incorporating
robot-free egocentric data significantly outperforms robot-only baselines by
**51%**, particularly **in unseen environments**."*** The figure is confirmed —
and the entry had been dropping the qualifier, which is the clause that says
where the gain lives. Worth flagging for one more reason: **51%** is also
[EgoEngine](#egoengine)'s full-system ablation score (0.51), and the two are
unrelated. Checked precisely because the coincidence looked like
cross-contamination; it is not.

**What it demands of the demonstrator.** A **PICO VR headset carrying five body
trackers** for full-body pose, a **ZED Mini depth camera** mounted on that
headset recording `.svo2`, and a Linux workstation to receive it. The view
alignment is *depth-based*, so the depth stream is not optional decoration —
it is what makes the human view transformable into the robot's.

🔴 **Licence — and this document's sharpest own-error yet, because the artefact
was found, named, and then not read.** The entry said: *"Dataset terms are not
stated; a sample dataset sits on Hugging Face under the same name, split into
robot and human subsets, with no scale figure given anywhere in the
documentation."* Checked at the card on 19 Sep 2026,
[`OpenDriveLab/EgoHumanoid`](https://huggingface.co/datasets/OpenDriveLab/EgoHumanoid)
carries **`license: apache-2.0`** in its YAML front matter *and* as a Hub tag, is
**ungated**, has **504 downloads**, and its README opens with a scale table. The
card was last modified **6 Jun 2026**; the sentence claiming otherwise was written
**1 Sep 2026**, so nothing moved — **the field was there to read the whole time.**

> **This is a different failure from the one [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
> produced, and a worse one.** There the release sat in a namespace neither the
> paper nor the project page pointed at, so the checks that returned *not
> released* were at least looking in the places a reader is sent. Here the
> document **had already located the artefact and written a sentence about it** —
> and recorded *terms not stated* and *no scale figure* without opening the card
> that states both. **Finding an artefact and reading it are two steps, and only
> the first leaves a trace in the prose.**

**What the card actually says, and it is the interesting part.** The sample is
**50 robot teleoperation episodes** (Unitree G1) and **one** egocentric human
episode:

| Subset | Content | Episodes |
|---|---|---|
| `example/robot/` | Robot teleoperation (Unitree G1) | **50** |
| `example/human/` | Egocentric human demonstration (PICO VR + ZED) | **1** |

🔴 **The released sample of a paper titled *"Robot-Free Egocentric
Demonstration"* is fifty-to-one robot-to-human.** No dishonesty is alleged — the
card calls itself a sample for smoke-testing the co-training pipeline, and says
so plainly. But a reader who takes the release as a proxy for the method gets the
thesis exactly inverted, and **the ratio in the artefact is the opposite of the
ratio in the argument.**

**And the paper promises less than the artefact delivers.** Its Appendix F is a
**License of Assets** section — a genuinely rare and good thing, listing MIT for
the latent-diffusion and MoGe components, Apache 2.0 for DINOv2 and openpi, and
the **NVIDIA non-commercial licence for GR00T-WholeBodyControl**, which the system
integrates. Its closing sentence is *"We will open-source our assets, including
**code and models**, under the Apache 2.0 License"* — code and models, not data.
The supplementary separately says *"We will open-source our **code and data**."*
**Two promises, one licence between them, and the licence is attached to the one
that does not include the data.** The Hub card then grants Apache 2.0 over the
data anyway. **The most conscientious licence appendix in this survey is the one
that omits the licence a downloader needs**, and the artefact is more permissive
than the paper it belongs to.

⚠️ **Neither surface a reader is sent to points at the release.** The paper
contains **zero occurrences of "Hugging Face"**; the project page at
`opendrivelab.com/EgoHumanoid/` links to **arXiv and GitHub only** and contains
the words *dataset*, *download* and *licence* **not once**. The card links
*forward* to all three. **The link is one-directional, and it points the way a
reader never travels.** (The third surface, the GitHub README, is unreadable from
this environment — the proxy 403s `github.com` — so this is two of three checked,
both silent, and that limit is stated rather than glossed.)

**Three copies, two of them nobody's job.** Besides OpenDriveLab's 504-download
original there is **`SII-JinChen/EgoHumanoid`** (151 downloads, Apache-2.0 — the
Shanghai Innovation Institute co-author's own namespace) and
**`introvoyz042/EgoHumanoid`** (67, Apache-2.0), a personal account that also
mirrors `awesome-egocentric-atlas` and `egoengine-repro-artifacts`. All three
carry the same licence, so nothing is lost here — but it is the same structure
that produced the survey's four **uploader-stamp** cases, and it is one card edit
away from producing a fifth.

**Bearing here.** This is the fifth published route in this section, and it
moves the input requirement in the *opposite* direction from what found footage
could ever satisfy — from a head-mounted camera to a head-mounted camera **plus
five tracked body segments plus depth**. Whole-body transfer needs whole-body
ground truth. Internet video gives you a viewport and nothing else, which is
why the operations available to it stay filter, clip, annotate — and why the
manifest has to record what a clip *cannot* support as carefully as what it can.

### EgoVLA — MANO as the action space, not just the annotation

**[arXiv 2507.12440](https://arxiv.org/pdf/2507.12440)** ·
[project](https://rchalyang.github.io/EgoVLA/) ·
[code](https://github.com/RchalYang/EgoVLA_Release) (181 stars) — the sixth
published route in this section, and the one that shows how deep the
[MANO dependency](#wilor--the-chokepoint-read-at-source) actually goes.

**Mechanism, quoted.** *"MANO hand parameters are used as a shared action space
for humans and robots"*, with human and robot aligned *"through a unified
representation based on wrist pose and MANO hand parameters"*, then inverse
kinematics and retargeting onto the robot. Trained on **TACO, HOT3D, HOI4D and
HoloAssist** — existing commissioned corpora, not found footage. Evaluated on
the **Ego Humanoid Manipulation Benchmark** built in NVIDIA Isaac Lab: 12 tasks,
a Unitree H1 with Inspire dexterous hands, outperforming a no-pretraining
baseline across all of them, *"with especially strong gains on long-horizon and
fine-grained manipulation tasks."*

🔴 **And the install instructions say the quiet part.** The repository requires
you to *"Register at the MANO website and download the models"* and place them
in the repo directory. Not a citation — a registration wall in the setup steps.

> **This changes the shape of the chokepoint finding.** Sweeps 33–34 established
> that MANO sits under the *annotation* path — WiLoR, HaMeR, HandOS all route
> through it. EgoVLA shows it also sits under the *transfer* path: it is the
> representation in which a human hand and a robot hand are made commensurable
> at all. So MANO is not a preprocessing dependency that a better reconstructor
> would remove. **It is the interlingua**, and a non-commercial,
> registration-gated one. Anything that wants to translate between human and
> robot hands currently borrows someone else's vocabulary for doing so — which
> is a far more structural fact than "one popular model has an awkward licence",
> and it is why [NIMBLE's unresolved status](#wilor--the-chokepoint-read-at-source)
> matters beyond a dependency swap.
>
> **For this repo**, the practical read is unchanged but better grounded: found
> footage supports filter, clip, annotate. The moment a pipeline tries to emit
> *actions* in a space a robot can consume, it lands on MANO, and the rights
> question arrives with it.

### Being-H0.5 — the MANO action space at 35,000 hours, and a preview subset with no terms

**[arXiv 2601.12993](https://arxiv.org/html/2601.12993v1)** (v1, 19 Jan 2026,
BeingBeyond; project page `research.beingbeyond.com/being-h05`) — the largest
instance in this document of the [shared-action-space route](#egovla--mano-as-the-action-space-not-just-the-annotation),
and the one that makes the MANO finding hardest to dismiss as a quirk of one
paper.

**Mechanism.** A cross-embodiment VLA built on the premise that *"human
interaction traces"* are a universal *"mother tongue"* for physical interaction.
A **Unified Action Space** maps heterogeneous robot controls into semantically
aligned slots so *"low-resource robots"* can bootstrap from human data; a
Mixture-of-Transformers with a **Mixture-of-Flow** design separates shared motor
primitives from embodiment-specific experts. **LIBERO 98.9%, RoboCasa 53.9%**,
with real-robot results on **five platforms**.

**Scale, quoted.** **UniHand-2.0**, *"the largest embodied pre-training recipe to
date"*: **35,000+ hours**, **120 billion tokens**, **400 M+ samples**, across
**30 distinct robotic embodiments**. The split is the interesting part —
**16,000 h egocentric human video, 14,000 h robot manipulation, 5,000 h
visual-language** — and the human half yields *"134 million human data
samples… a 100× increase over UniHand-1.0"*.

✅ **All fourteen figures in this entry were audited against the paper's HTML
this sweep, and every one holds exactly** — *"an expansive corpus comprising
35,000+ hours of data and 120 billion tokens, totaling more than 400 million
samples"*, *"16,000 hours of egocentric human video, 14,000 hours of robot
manipulation, and 5,000 hours of general visual-language understanding data"*,
*"30 distinct robotic platforms"*, *"134 million human data samples… a 100×
increase"*, and *"LIBERO (98.9%) and RoboCasa (53.9%)… on five robotic
platforms"*. This is the largest hour-figure attributed to a single corpus in
this survey after HumanNet's million, it is quoted in the README, and it feeds
the [derivation map](#who-feeds-whom--the-derivation-map) — it was overdue a
check, and it passed. *(One sharpening: UniCraftor's set is **43 tabletop
tasks**, not 43 tasks.)*

🔴 **It builds directly on Egocentric-10K, which gives the derivation map its
first downstream consumer of the Build AI corpus.** The human-video half
integrates *"in-the-wild egocentric videos from large-scale public repositories,
including Ego4D, EPIC-KITCHENS, Egocentric-10K, etc."* — ⚠️ **a sixth instance of
[the "in the wild" trap](#the-vocabulary-problem--six-ways-a-name-misleads), and the most self-contained: the phrase and its
denial sit in the same sentence.** *In-the-wild* here modifies videos that the
same clause identifies as coming from *public repositories*, by name. A reader
who takes the adjective at face value and stops before the comma has the
opposite of the fact. So the free-hours corpus
of [§12](#egocentric-10k) is no longer only a thing that exists — it is a thing
something at 35,000 hours was built on.

🟢 **And they specify, in one clause, what annotation has to deliver.** The
three things they say their sources lacked are *"accurate depth, stable camera
alignment, and temporally precise interaction events."* **That is an acceptance
specification written by the consumer**, and it is the most directly usable
sentence in this survey for anyone building the gates in
[§10](#10-annotate): not *"is it annotated"* but *is the depth metric, is the
camera pose stable across the clip, and does the label boundary sit on the event
rather than on the cut.* A pipeline that records those three per clip is
answering the question a 35,000-hour pre-training team actually asked.

⚠️ **And their own assessment of it is this document's argument, in someone
else's words.** *"Egocentric-10K features 10,000 hours of in-the-wild industrial
footage but provides only raw RGB streams without annotation."* Ego4D and
Ego-Exo4D *"provide rich semantic descriptions but lack geometric depth"*. That
is an independent team, having actually used the corpora, reaching §12's
conclusion: **the hours are free and the annotation is the cost.** Their response
is [§1](#1-commissioned-egocentric-and-egoexo-capture)'s: **UniCraftor**, a *"portable,
extensible, and affordable"* rig capturing depth, keyframe events and camera
extrinsics, yielding **200+ hours across 43 tasks** — a second instance, after
[Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape), of a 2026 team
deciding that cheap purpose-built capture beats annotating what is already free.

🔴 **MANO again, at the action-space layer, independently.** The paper's own
lineage puts it beyond doubt: *"EgoVLA constructs a shared action space using
MANO hand-model parameters"*, and *"Being-H0 scales this paradigm by introducing
a motion tokenizer that discretizes continuous **MANO** trajectories into tokens
for large-scale instruction tuning."* Being-H0.5 extends that line. So the
[MANO chokepoint](#wilor--the-chokepoint-read-at-source) is not one team's
choice — **two independent groups, asked to make a human hand and a robot hand
commensurable, both reached for MANO**, and the second then scaled it to 16,000
hours of human video.

🔴 **Rights: Apache 2.0 code, and a released dataset with no licence at all.**
Three artefacts, three positions:

| Artefact | Status | Terms |
|---|---|---|
| `BeingBeyond/Being-H` code | released | **Apache-2.0**, stated in the repo README and `LICENSE` |
| **`BeingBeyond/UniHand_Preview`** | **released, ungated, 13,377 monthly downloads** | 🔴 **none** — the card carries `task_categories` and `tags` and **no `license` field**; its entire prose is one line plus two BibTeX blocks |
| UniHand-2.0, the full 35,000 h | **not released** | not stated |

**The middle row is the one that matters**, and it is the fourth licence shape —
*partially released* — with a twist [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
did not have. SABER's released quarter at least carries CC BY-NC 4.0 (*though it
is gated too, which this document did not check until sweep 79*). Here the
released subset carries nothing, and **the card does not say what is in it**:
*"This data is a subset of the pretraining data for Being-H0.5."* Since the
mixture it is drawn from includes **Ego4D** (unpublished agreement) and
**EPIC-KITCHENS** (non-commercial), a reader cannot determine from the artefact
whether the subset contains material governed by those terms, or only the team's
own UniCraftor and in-house recordings. *No non-compliance is alleged —* the
point is precisely that **it cannot be determined from what is published**, by
anyone, including its 13,000 monthly downloaders.

> **The OpenEgo comparison, made twice now.**
> [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
> aggregates six corpora and ships `ATTRIBUTION.md` with per-source licence text
> and an annotations-only redistribution rule.
> [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
> aggregates eleven and states nothing — but it also releases nothing, so the
> question stays theoretical. **UniHand_Preview is the same omission on an
> artefact people are actually downloading**, which makes it the stronger
> counterfactual of the two. The distance between best and worst practice here is
> one file that OpenEgo wrote and nobody else did.
>
> **For this repo**: the entry earns its place twice over. It is the strongest
> outside confirmation of §12's free-hours-cost-annotation argument, and it is
> the cleanest demonstration of why §14 keeps the *rights record format* on the
> build side. A 35,000-hour recipe, an Apache-2.0 codebase, state-of-the-art
> numbers — and the released data still cannot be traced to its sources.

### OpenMMEgo — "Open Weights and Data", half kept

**[BeingBeyond/OpenMMEgo](https://github.com/BeingBeyond/OpenMMEgo)** (NeurIPS
2025) — the **fifth BeingBeyond artefact** in this survey, and the sharpest
instance anywhere in it of the gap between a promise and a grant, because **the
promise is in the paper's title**.

**What it claims.** *"OpenMMEgo: Enhancing Egocentric Understanding for LMMs with
**Open Weights and Data**."* The contribution is three-part: **OME10M**, *"a
large-scale, high-quality dataset… comprising **over 8.2 M egocentric video QA
pairs synthesised from Ego4D series**"*; **OMEBench**, a benchmark for egocentric
understanding; and semantic-aware visual token compression with curriculum
learning. Qwen2.5-VL tuned with it *"substantially outperforms other models of
the same size in egocentric video understanding."*

🔴 **What the repository says, a year on.** The entire `## Code` section, quoted
in full:

> *"We will release our code and data soon."*

That is the whole section. The repo carries an **MIT `LICENSE`** — governing a
repository whose substantive content is a README — and **neither OME10M nor
OMEBench is findable on Hugging Face**, searched by both names this sweep.

⚖️ **The fair version, because half of the title is kept.** BeingBeyond publishes
**13 public model repositories** — the Being-H0 family at 1B/8B/14B, the BeingVL
tokenisers, the Being-H05 variants including LIBERO and RoboCasa fine-tunes. **The
"Open Weights" half is real and shipped.** It is the **"and Data"** half that is
a year-old *soon*. So this is not a project that promised nothing and delivered
nothing; it is one that delivered exactly the half that costs least to give away.

> **Why this outranks [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)
> as the document's example of a promise.** WIYH says *"all data and hardware
> design will be open-source"* in its body — a sentence a reader has to go and
> find. **OpenMMEgo says it in the title**, which is the one string that
> propagates into every citation, every listing and every search result that
> mentions the work. A claim in a title is the most-copied claim a paper makes and
> the least-checked. Added to
> [the vocabulary table](#the-vocabulary-problem--six-ways-a-name-misleads)
> as a sixth trap: **a name or title that asserts openness is a claim about
> intent, not a licence** — and `Open` in a project name is not evidence of
> anything.
>
> ⚠️ **Two corrections to the paragraph above, both this document's.** WIYH's
> v3 title was *"A Large-Scale **and Open-Source Ecosystem** for…"*, so it said it
> in the title too and the contrast as drawn was too clean. And **v4 has since
> removed it from both** — title and body — which is the strongest possible
> demonstration of the asymmetry this note was reaching for: *OpenMMEgo cannot
> take its claim back without renaming the project; WIYH did it in one
> resubmission.* The ranking survives; the reason given for it did not.
>
> ⚠️ **And note what was available to release cheaply and was not.** OME10M is
> **8.2 M QA pairs synthesised from Ego4D** — that is *annotations over someone
> else's video*, the exact shape [EgoVid-5M](#egovid-5m) and
> [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
> ship without redistributing a single frame, and which carries no obligation to
> re-host Ego4D's footage. The annotations-only route was open and was not taken.
> **For this repo** the lesson is the one §14 already encodes: a release posture
> is a decision made once and then either honoured or not, and **the only
> evidence that distinguishes the two is a file you can fetch.**

### Being-H0.7 — one corpus, three products, and a second vendor doing it

**[arXiv 2605.00078](https://arxiv.org/html/2605.00078v1)** (v1, 30 Apr 2026,
BeingBeyond) — a **Latent World-Action Model**, and the reason it belongs here is
not the architecture but what sits underneath it.

**Mechanism, briefly.** It puts *future-aware reasoning* into a VLA **without
generating future frames**: a set of learnable latent queries forms a prior
branch, jointly aligned during training with a **future-informed posterior
branch**, so at deployment the prior infers a compact predictive state from
current context alone. A dual-branch implementation with hidden-state alignment
and anti-collapse regularisers keeps the latent from degenerating. Results
include **LIBERO-plus 82.1% zero-shot**, rising to **84.8%** after finetuning,
and **49.2%** average on the GR1 bimanual humanoid suite.

🔴 **It is pretrained on the same corpus as [Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms).**
Quoted: *"we pretrain the model on mixed human and robot manipulation data
following the unified sequence format of **UniHand 2.0**."* So the 35,000-hour
mixture — 16,000 h of it egocentric human video drawn from Ego4D,
EPIC-KITCHENS and [Egocentric-10K](#egocentric-10k) — now backs **Being-H0,
Being-H0.5 and Being-H0.7**.

> **This is the NVIDIA pattern again, at a second vendor, and that changes it
> from an anecdote into a shape.** §2 records
> [EgoScale and DreamDojo](#egoscale) as almost certainly one crowdsourced pool
> feeding two products, inferred from identical scene/task/object counts. Here
> there is nothing to infer: **BeingBeyond says outright that its models share
> UniHand 2.0.** Two organisations, same economics — *acquire the corpus once,
> amortise it across a model family* — which is the clearest statement yet of why
> [§13](#13-why-no-open-source-project-does-exactly-this)'s gap persists. **If
> the corpus is the asset that pays for three products, the acquisition layer is
> the last thing you publish.** That is §13's reason 2 (*where it is commercially
> valuable, the pipeline is the product*), now with a named example on each side
> of the Pacific rather than one inferred one.
>
> ⚠️ **Rights position: inherited, and no better.** The paper states **no licence
> for code or data** — the only licence string in it is arXiv's own — and the
> word *"release"* does not appear anywhere in the body. What is downloadable is
> what Being-H0.5 published: **`UniHand_Preview`, ungated, with no `license`
> field**. A third model on the same undocumented mixture does not add a third
> rights problem; it multiplies the reach of the one already there.

### World In Your Hands — the instrumentation ceiling, and a third "in the wild"

**[arXiv 2512.24310](https://arxiv.org/abs/2512.24310)** (**v4, 21 Sep 2026**;
this document had cited **[v3](https://arxiv.org/html/2512.24310v3)** since this
entry was written) — the most heavily instrumented human-manipulation capture effort in this
document, and useful here as the upper bound on what *recording* can buy that
*finding* cannot.

🔴 **v4 landed three days ago and it is a retreat, which is not the direction a
new version is assumed to go.** Read side by side against v3, the paper did not
announce a release — **it deleted the promise of one**:

| | **v3** (15 Mar 2026) | **v4** (21 Sep 2026) |
|---|---|---|
| Title | *"A Large-Scale **and Open-Source Ecosystem** for Learning Human-Centric Manipulation in the Wild"* | *"A Large-scale **Ego-centric Dataset** for Learning Robotic Manipulation In the Wild"* |
| `open-source` in the body | **6** — of which **4 are the project's own claims** | **1**, and it is a bibliography entry for OpenVLA |
| *"All data and hardware design will be open-source"* | present, in the abstract | **gone** |
| *"we will open-source the whole dataset and hardware design"* | present, in the conclusion | **gone** |
| Project Page URL on the title page | `https://wiyh.tars-ai.com` | **gone** |
| Code URL on the title page | `https://github.com/tars-robotics/World-In-Your-Hands` | **gone** |

**Every sentence in which this project promised to open-source itself has been
removed from the paper, along with both of the URLs where that would have
happened.** The word *open-source* survives in the work only as the name of
somebody else's model in the reference list.

⚠️ **And the arXiv listing has not caught up, so the promise is still on the
abstract page.** `arxiv.org/abs/2512.24310` today serves **v3's title and v3's
abstract** — *"a large-scale open-source ecosystem… All data and hardware design
will be open-source"* — above a submission history whose newest entry is v4.
Metadata and source are updated separately on arXiv and these authors updated
only the source. **A reader who checks the landing page sees a commitment the
paper no longer makes**, and this document is one of the places that quoted it
from there.

**Scale.** **1,045 hours**, **125,400 clips**, **over 100 human skills**, **over
40 tasks** across **10 scenarios** — banquet, laundry, logistics, hotel,
department, office, supermarket, industry, cleaning, candlelight.

🔴 **And a second number, new in v4, that the headline hides: the annotation
covers 600 of those hours.** *"We provide a multi-stage annotation and validation
pipeline that produces **600 hours, or 100K episodes**, of atomic action
instructions."* Against 1,045 hours captured, that is **57%** — and v4's own
comparison table marks WIYH's VLM-annotation column **`Subset`**, the same mark
it gives Ego4D. The hours that carry the language supervision this document cares
about are **600, not 1,045**, and the difference is not stated as a limitation
anywhere; it has to be got by subtracting one section from another. Filed beside
[AtomEgo](#atomego--a-provenance-table-that-restates-four-corpora-at-once), which
made the same point about other people's corpora: **a corpus can restate *itself*
at two sizes without ever contradicting itself.**

📐 **What it costs to record, in the paper's own figures** — worth having
because [§14](#14-build-vs-reuse-per-stage) prices commissioned capture mostly from
[SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of) and
[Zeva-Ego](#zeva-ego--the-first-published-exchange-rate-and-a-named-consumer-of-the-free-ten-thousand-hours).
WIYH reports
**a single collector at 8 hours/day producing ≈1.8 TB of valid multimodal data**,
and **100 collectors over 30 days yielding ≈5.4 PB raw**. Its throughput
comparison, on the rose-insertion task at a fixed 8 hours of collection time:
**teleoperation ≈150 clips, DexUMI-style UMI ≈400, Oracle Suite 720, VR ≈800.**
⚠️ **Read as a ranking, not a rate** — it is the vendor of the third option
scoring all four, and VR beats it on the very axis being measured, with the
paper's answer being quality (VR gives 2D skeletons only) rather than speed.

**The instrument, which is the contribution.** The **Oracle Suite**, a wearable
rig in three parts: **H-FPVHive**, chest-mounted, with two fisheye cameras, two
pinhole cameras and four infrared lenses; **H-Gloves**, carrying six IMUs per
glove, five fingertip pressure sensors (5 mN resolution, 0.2–50 N range) and
three fisheye cameras per glove; and **H-Backpack** for storage, compute
(NVIDIA Orin) and power. What comes off it: multi-view RGB, IMU localisation,
**tactile** readings, and 6-DoF wrist trajectories at **under 5 mm**
translational accuracy.

**Results.** Pre-training a VLA on WIYH moved two real-world tasks — rose
insertion, gift packing — from **15% to 70%**; separately, co-training a
robot-only policy with human data took cluttered-scene success from **8% to
60%**.

🔴 **Licence — and this document had it wrong, because it did not read far
enough.** Since it was written this entry has said: *secondary coverage describes the
dataset as research-only with commercial use restricted; **the paper states no
licence***. The first half is right. **The second half is not, and the refutation
is in the paper — it was in v3 as well, so this was never a v4 change.**
Appendix E, *Ethics and Privacy Statement*, under the heading **Data Usage and
Licensing**:

> *"The released dataset is intended **exclusively for research** on embodied AI,
> manipulation, perception, and VLA learning. **Redistribution or commercial use
> is restricted** according to the licence accompanying the dataset."*

and, two sentences later, *"a licence that explicitly forbids re-identification,
face recognition, or surveillance-related uses."* **That is precisely what the
secondary coverage said**, and this document treated the coverage as unsourced
embellishment when it was a faithful summary of an appendix the document had not
opened. The correction is method, not wording: **this survey's licence checks
read the abstract, the front matter and the card — and this paper put its terms
in the ethics appendix**, which is a place nothing in the pipeline was looking.
Whether that is a pattern or one paper is not yet known; it is recorded as a
place to look, not as a trend, because one instance is one instance.

⚠️ **What survives of the original reading, stated precisely.** The paper states
**terms** and names no **instrument**: no CC, no Apache, no bespoke text — only
*"the licence accompanying the dataset"*, a licence that is not reproduced in the
paper, not linked from it, and not attached to anything a stranger can download.
So WIYH stays under [§11](#11-the-licence-trap)'s second failure mode, but for a
narrower reason than before: **not *terms unstated* — terms stated and the
instrument deferred to an artefact.** It is a near relative of the
[cross-platform pointer](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform)
found two sweeps ago, and worse in one respect: HumanTouch points at another
platform where the licence **is**; WIYH points at a file that accompanies a
download most readers cannot yet obtain. **Anyone planning against it still needs
the instrument in writing** — but they should ask for it knowing the publisher
has already written down what it intends the terms to be.

🔴 **"No repository, no download location" — this document said that four times,
and the URLs were on the paper's own title page the whole time.** Earlier sweeps
recorded: *no repository, no Hugging Face dataset, no download location and no
licence surfaced for WIYH or the Oracle Suite; the only findable artefact remains
the arXiv entry.* **v3's title page carries, directly under the author list:**

> *"† Project Page: `https://wiyh.tars-ai.com` · Code:
> `https://github.com/tars-robotics/World-In-Your-Hands` · Affiliation: TARS
> Robotics"*

**Four looks for a release location, and the release location was in the header
block of the document being looked at.** The failure is legible in hindsight: the
searches went to the hubs and to the paper's *body*, and a dagger footnote
rendered between the author list and the abstract is exactly the region a
keyword-driven read skips. It is the same lesson as the last three sweeps in a
new costume — *ask a different index* — except that here **the index not being
asked was the source itself**.

⚠️ **The GitHub URL cannot be checked from here and is not claimed to resolve.**
This environment's proxy returns **403 for every `github.com` URL** — 37 of them
in this document's own link check this morning, all 403 — so whether
`tars-robotics/World-In-Your-Hands` exists, is empty, or is private is **unknown
to this survey**, exactly as [§14's maintenance blind spot](#14-build-vs-reuse-per-stage)
was until PyPI was queried. What is verified is that **the paper cites it**, and
that **v4 removed the citation from the body while the arXiv metadata comment
still carries it** (*"Github: this https URL"*).

🟢 **The project page resolves, and it settles the candidate this document has
been declining to accept.** `https://wiyh.tars-ai.com` returns
**200** — a single-page app whose `<title>` still reads *"Large-Scale and
Open-source Ecosystem…"*, months after the paper stopped saying it, and whose
favicon is `/tarslogo.svg`. Its bundle names three outside links —
`arxiv.org/abs/2512.24310`, `github.com/tars-robotics/World-In-Your-Hands`, and
`github.com/OpenDriveLab/Agibot-World` — **and no Hugging Face URL at all**, so
the page does not hand over the tie directly. **Its API does.** The public
preview endpoint `/api/v1/dp/wiyh/sampelDate/list` returns records keyed
`worldcodeName`, the first of them:

> `worldcode_HS-2-1423225026718_2025-10-29-16-08-42_4_s0_vlta_reorg_sample_1-2`

**The Hugging Face card's worked example is the same string with different
digits** — `worldcode_HS-2-1420125020208_2025-10-21-14-50-09_3_s0_vlta_reorg_sample_1-2.json`
— same prefix, same `HS-2` site code, same timestamp slot, same
`_s0_vlta_reorg_sample_1-2` tail. And `vlta` is **the paper's own coinage**, from
the arXiv comment field: *"vision, language, tactile sensing, and action
(VLTA)"*. Three further agreements point the same way: the HF README's camera
names, `lf_chest_fisheye` and `ldr_hand_fisheye`, are the Oracle Suite's
chest-mounted and per-glove fisheyes; the schema it specifies — `worldcode_name`,
`subtasks`, `camera_calibration`, per-frame `chest_poses` and `hand_states` — is
the schema the publisher's own service emits; and the account name matches the
repository the paper cites.

**So `tars-robotics/WIYH` is WIYH, and this document now says so.** The rule it
was held against — *one tag is the difference between an artefact and a
coincidence*, applied to [ACE-Ego-0](#ace-ego-0) — was the right rule and is
kept. What it asked for was *a tag, a README sentence, or a link from the paper*;
what settled it was none of the three, but **the publisher's own API emitting the
bespoke identifier format the card documents**. The lesson is not that the bar was
too high. It is that **the bar was set in terms of three specific signals, and
the evidence arrived as a fourth** — so the bar should be stated as what it was
always for: *evidence the publisher couldn't have produced by accident.*

📌 **Current state of the artefact, read today:**
[`tars-robotics/WIYH`](https://huggingface.co/datasets/tars-robotics/WIYH) —
**CC BY-NC 4.0**, ungated, `size_categories: n>1T`, **14,807 downloads, 3 likes**,
created 25 Mar 2026, **last modified 5 May 2026**, still **no `arxiv:` tag**.
So the instrument the paper deferred to *does* exist, on Hugging Face, and it is
**CC BY-NC 4.0** — consistent with Appendix E's *research-only, commercial use
restricted*, and the first time this entry has had a licence to name.

🔴 **The catch, and it is a real one: the exported schema zeroes the paper's
headline contribution.** WIYH's central claim is **wrist pose at under 5 mm**.
The HF card's field table says, of `wrist_poses`: ***"Placeholder zero poses for
the left and right end-effectors."*** The pose information is carried instead by
`chest_poses` — *"poses of the left and right end-effectors in the current
frame's `chest` coordinate system"* — so the data is not missing, it is in a
different frame under a different key, **and the field a reader would reach for
first contains zeros.** Anyone pulling this corpus and reading `wrist_poses`
literally gets a silent, well-formed, entirely wrong answer.

⚠️ **And the download is gated — by an account, which no sweep had recorded.**
The project page ships a two-tier download UI: **`Mini`**, listed, and
**`Full`**, whose description is the string **`"Coming soon"`**. Downloading runs
through `/api/v1/auth/register` and `/api/v1/auth/login`, stores a
`dataset_license_accepted` flag, and fails closed — `/api/v1/dp/wiyh/downloadDate/list`
answers **`{"code":401,"msg":"未授权"}`** to an anonymous request, while the
preview endpoint beside it answers 200. So the access shape is: **previews open,
bulk download behind registration plus a licence click, full corpus not yet
released.** One detail is worth *not* over-reading: the page probes an
Alibaba-internal OSS host (`…oss-cn-shanghai-internal.aliyuncs.com`) with a
500 ms timeout and, on failure, **rewrites the hostname to the public
`oss-cn-shanghai.aliyuncs.com`**. That is a cache optimisation for users inside
the publisher's VPC, **not** a private distribution path — checked, because the
interesting reading was the wrong one.

**Net, after all of that.** WIYH is no longer *a promise with nothing behind it*.
It is **a partially released, account-gated, CC BY-NC 4.0 corpus whose public
tier is a `Mini` subset, whose full 1,045 hours are "Coming soon", and whose
paper has just deleted the word "open-source" from its title.** As with
[Egocentric-1M](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost), this
document does not claim the full release will not happen. It claims the narrower,
checkable thing — and the narrow claim has now changed twice in one sweep, in
both directions, which is the honest outcome of looking properly rather than
again.

⚠️ **And its publisher shows the shape at scale.** `tars-robotics` ships **four
datasets — WIYH, OmniViTac, OmniViTac_Samples and Libero — every one CC BY-NC
4.0, every one ungated, 44,789 combined monthly downloads** — and the two largest
have **no descriptive card**: one is an internal field spec, the other is
**licence front-matter and nothing else**. **The terms are stated and the
identity is not**, which is the exact inverse of the failure this document
usually records, and just as hard to build on.

**And "in the wild" means what it always means here.** Third instance, after
[EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) and the phrase's usage
throughout this section: the paper's *in-the-wild* is *"collected in diverse
real-world scenarios"* rather than a lab — homes, workplaces, commercial spaces —
all of it **self-collected by operators wearing the suit**, none of it sourced
from existing video. The term is now reliable enough to read as a signal in the
opposite direction: in this literature, a title advertising in-the-wild data is
advertising *where the capture happened*, and is weak evidence that no found
footage was involved.

**Bearing here.** Tactile at 5 mN and wrist pose under 5 mm are things found
footage will never *carry*, and it would be dishonest to pretend otherwise: for
contact-rich dexterity there is a measurement ceiling on internet video that no
amount of verification lifts.

🟡 **But "never have" was too strong, and the next entry is why.** Measured
tactile and *estimated* tactile are different things, and
[EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved)
now predicts the second from ordinary egocentric RGB — zero-shot on Ego4D,
EPIC-KITCHENS and EgoDex, none of which was recorded with a sensor. The ceiling
on what found footage can be *annotated with* is lower than the ceiling on what
it can be *measured to*, and it is moving. What 1,045 instrumented hours cost —
a custom glove, a backpack computer, an operator per hour — is the other half of
the trade, and it is why the two supplies are complements rather than rivals.
The manifest discipline this repo applies exists precisely so a trainer can tell
which kind of hour it is holding.

### EgoTac — tactile predicted from ordinary video, and a ceiling that moved

**[arXiv 2608.15060](https://arxiv.org/html/2608.15060)** — the entry that forced
the qualification above, and the most directly useful result in this section for
a pipeline that only ever has pixels.

**Mechanism.** It predicts *"dense continuous tactile values"* and *"contact
classification labels from temporal vision input"* — continuous **force fields**
and discrete contact states, anchored to hand-mesh vertices, **from egocentric
RGB clips**. Ground truth comes from the authors' own **EgoTac-SC**, captured on
custom wearable gloves carrying **264 force sensors** across fingers and palm
measuring pressure in newtons, supplemented by eight existing datasets — some
contributing mesh-based analytical contact labels derived from geometry rather
than sensor readings.

**The number that matters here.** It performs *"zero-shot tactile predictions on
unconstrained real-world videos"* including **EgoDex, EPIC-KITCHENS and Ego4D** —
corpora recorded with no tactile hardware whatsoever. In-domain force prediction
reaches **MAE below 0.06 N**; out-of-domain contact estimation reaches **F1 above
0.70**, beating prior contact estimators on OAKINK2 and FPHA.

🔴 **Licence re-checked at the paper this sweep, and "unstated" was too generous.**
The body contains **no occurrence of *"we release"*, *"will be released"*,
*"publicly available"* or *"available at"***; there is no repository, no dataset
card and no project page; and the only licence string anywhere is arXiv's own.
So the field should not read *terms unstated* — **there is nothing released to
attach terms to.** Reclassified from the second licence failure mode to the
third. ⚠️ And note the search hazard recorded at
[EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame):
looking for "EgoTac" on Hugging Face returns *EgoTactile's* card, licence
included, which is how a blank field gets filled with the wrong project's terms.

🟢 **And EgoTac names, in its own limitations, the problem EgoTactile's rig
solves.** Its appendix carries a section titled **"Visual-domain gap introduced
by tactile gloves"** — the observation that a model trained on instrumented
capture learns to read pressure off a glove that found footage never shows.
EgoTac raises it as a limitation of the training data available to it;
[EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame)
answers it at capture time by filming a bare hand while an off-camera gloved one
supplies the reference. **Neither paper cites the other, and read together they
are a problem statement and its solution** — which is the argument for reading a
subfield as a set rather than a list.

**Licence.** The listing carries only the arXiv perpetual non-exclusive licence
— the *paper's* — with **no code, data or release statement** in the document.
The [fifth instance](#the-vocabulary-problem--six-ways-a-name-misleads)
of the trap, so worth saying plainly: nothing here is obtainable yet.

> **What this does to the argument, honestly stated.** It does **not** mean
> found footage has tactile. It means the *instrumented* corpora — [World In
> Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild),
> EgoTac-SC — are turning into something other than a rival supply: **they are
> the calibration set for estimators that then run on the cheap supply.** That
> is the same shape as the hands gate one level up, where a model trained on
> annotated data is applied to unannotated found clips, and it argues that the
> two supplies are complements in a stronger sense than this document had it —
> not "both useful for different jobs" but "one exists to make the other
> legible."
>
> **And it lowers a bar for this repo specifically.** A clip's *contact* state —
> is the hand actually touching the object, or hovering — is exactly the kind of
> per-clip verdict the quality gates exist to record, and an F1 above 0.70
> zero-shot on Ego4D-class footage is well past useless. It is not a licence to
> claim a clip carries force measurements. It is a reason to expect the
> annotation tree to grow a contact field before it grows anything else.
>
> ⚠️ **One usage note, since this document keeps track.** EgoTac's *"in the
> wild"* means uncontrolled real-world environments — but unlike the other
> instances catalogued in §15, its inference set genuinely *does* include found
> corpora. The phrase misleads less here than elsewhere, which is worth
> recording precisely because the pattern is not universal.

### EgoTactile — tactile *measured*, and a rig that keeps the glove out of frame

**[arXiv 2606.09243](https://arxiv.org/abs/2606.09243)** (ICML 2026 Spotlight) ·
🟢 **A second artefact this sweep**, from the same publisher and consistent with
the first: [`HustleHard/EgoTactile-OXT`](https://huggingface.co/datasets/HustleHard/EgoTactile-OXT),
created **4 September 2026**, **CC BY-NC 4.0**, ungated, 92 downloads, tagged
`open-x-tactile` — the corpus re-expressed in **Open X-Embodiment format**. The
one *measured* tactile release in this document is the one that also shows up in
the robot-data interchange format, which is how supervision reaches the models
that need it. Terms unchanged across both artefacts, which is itself worth
recording: this publisher is now the only one here to have shipped twice and said
the same thing twice.

**[HustleHard/EgoTactile](https://huggingface.co/datasets/HustleHard/EgoTactile)**
— *"Learning Grasp Pressure for Everyday Objects from Egocentric Video."*

⚠️ **First, the trap, because it nearly cost this document a false entry.**
**EgoTactile is not [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved).**
Two different 2026 papers, both on tactile from egocentric video, with names one
suffix apart: **EgoTac is arXiv 2608.15060; EgoTactile is arXiv 2606.09243.** A
Hugging Face search for `EgoTac` returns *EgoTactile's* dataset card first, and
that card carries a licence — so a sweep checking EgoTac's unresolved licence
field, which is exactly what this one was doing, is one careless step from
recording **CC BY-NC 4.0** against the wrong project. Caught by comparing arXiv
IDs rather than names. Added to
[the vocabulary table](#the-vocabulary-problem--six-ways-a-name-misleads)
as a fifth trap: **near-identical names in the same subfield, where the search
engine resolves the ambiguity for you and does not tell you it did.**

**Mechanism and scale, read at the card.** Egocentric RGB at **1280×720, 15 FPS**,
paired with **full-hand pressure from 162 sensing locations** over a **0–350 N**
range, synchronised at 15 Hz. **12 participants, 63 everyday objects, 7
categories.** Two methods ship with it: **EgoPressureFormer** (discriminative)
and **EgoPressureDiff**, a conditional diffusion model adapting a pretrained
video-diffusion backbone *"for pressure estimation under partial visual
observations and physical ambiguity."*

🟢 **The Bare-Hand Set is the idea worth stealing, and it answers a problem this
document raises against
[World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild).**
Instrumented tactile capture has an inherent flaw as training data for found
footage: **the glove is in frame**, so a model learns to read pressure off a
sensor that internet video will never show. EgoTactile's answer is a two-hand
protocol — **the hand the camera sees is bare, while a synchronised *off-camera*
gloved hand performs the same grasp and supplies the pressure reference**, the
two coordinated by **metronome**. The measurement comes from the instrumented
hand; the pixels come from an uninstrumented one.

> **Where it sits in the tactile picture, which now has three positions rather
> than two.** [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
> *derives* contact geometrically, needing per-frame object meshes, and is closed
> to found footage by construction. [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved)
> *predicts* it from pixels alone, and is open. **EgoTactile *measures* it** —
> which is neither, and is the thing the other two are respectively approximating
> and needing. It is the supervision that makes prediction from pixels trainable
> at all, and the bare-hand protocol is what stops that supervision carrying the
> instrument into the training distribution.
>
> ✅ **And it is released with terms, which the other two are not.**
> **CC BY-NC 4.0**, ungated, **1,614 downloads a month**, with a companion
> `EgoTactile-OXT` set on the same licence. Non-commercial, so not shippable —
> but it is the only one of the three tactile corpora here whose rights position
> is a fact rather than a blank. **For this repo** the read is unchanged in
> direction and sharper in detail: found footage will never *carry* pressure,
> estimators that annotate it need measured pairs to learn from, and the useful
> measured pairs are the ones captured without the instrument in shot.

### H-Tac — tactile *derived* rather than predicted, and the OpenEgo counterfactual

**[arXiv 2607.01067](https://arxiv.org/html/2607.01067)** — read immediately after
[EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved),
because the pair draws the line this repo actually has to work with.

🔴 **Two things this document had not noticed, found on a licence re-check.**
First, **H-Tac is BeingBeyond's** — the same lab as
[Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms)
and [Being-H0.7](#being-h07--one-corpus-three-products-and-a-second-vendor-doing-it),
which the survey had been treating as unrelated projects. The paper's own name
for the method is **TTP** (*Transferable Tactile Pre-training*), which is the
`TTP (ours)` column in [its results table](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) —
and the baseline it is measured against, **BeingH-0.5, is the same group's
previous model.** Nothing improper in that; it is ordinary practice. But a
reader comparing *"their method against the strongest baseline"* should know the
baseline is in-house, and the document should have said so. **That makes four
BeingBeyond artefacts here**, which is a concentration worth seeing on the
[derivation map](#who-feeds-whom--the-derivation-map) rather than scattered.

Second, **its printed project page does not exist.** The paper prints
`https://beingbeyond.github.io/TTP/`; fetched this sweep it returns **HTTP 404 —
*"There isn't a GitHub Pages site here."*** That is the **third** broken printed
project URL in this survey, after ACE-Ego-0's 404 and ENIGMA-360's four failures.
Combined with a body containing **no occurrence of *"we release"*, *"publicly
available"* or *"available at"***, the honest classification moves: H-Tac is not
*"terms unstated"*, it is **not released**, with an advertised page that was
never published.

🔴 **That reclassification was wrong, and finding out how it was wrong is worth
more than the correction.** A release exists:
[`BeingBeyond/H-Tac_Sample`](https://huggingface.co/datasets/BeingBeyond/H-Tac_Sample),
in the authors' **own** namespace, created **6 July 2026**, ungated, **234
downloads** — and it is not a stub. Its README tabulates **98 complete episodes,
35,982 frames and 98 top-view videos** across four subsets, in a LeRobot v2.1
episode layout with H-Tac metadata:

| Directory | What it is | Episodes | Frames |
|---|---|---|---|
| `DeskTaskTac/RawHandPip` | human hand desk tasks with tactile data | 10 | 10,974 |
| `DeskTaskTac/AprilTagPip` | AprilTag-assisted desk tasks with tactile data | 4 | 11,104 |
| `InternDataTac/curated__genie1_mano_tactile` | robot MANO tactile data | 49 | 7,553 |
| `InternDataTac/curated__lift2_mano_tactile` | robot MANO tactile data | 35 | 6,351 |

**And it carries terms**: a `LICENSE` file reading **MIT**, *"Copyright (c) 2026
H-Tac dataset authors"*, alongside `CITATION.md` and a `SCHEMA.md`. So H-Tac is
neither *not released* nor *terms unstated* — it is **partially released, MIT on
the part released**, the same shape as [EgoMimic](#egomimic)'s sample. The two
components shipped are the *measured* ones (DeskTask-Tac) and the robot ones;
**HOI-Tac, the 106-hour aggregation over eleven other people's datasets, is not
in it** — which is the component whose licence question was the interesting one.

> ⚠️ **How the error happened, because the method failed in a way worth naming.**
> Every check that produced *"not released"* was run against the paper and the
> printed project page: no *"we release"* in the body, a 404 at the URL the
> authors chose to print. All of that is still true. **The release was somewhere
> nobody looked** — a Hugging Face namespace, discoverable by a search this
> document only started running against *this* project's name three sweeps ago,
> after the permissive-licence audit made "go to the artefact" a rule. **An
> absence of evidence in the two places a paper points you is not evidence of
> absence**, and that is precisely the inference this entry drew. The
> [licence-shapes table](#11-the-licence-trap) now records H-Tac under *partially
> released* rather than *not released*.
>
> *(One detail for the collection: the `LICENSE` is the stock **MIT software**
> text, whose operative sentence grants rights to "deal in the **Software**". It
> is applied here to 35,982 frames of video and tactile readings. Standard
> practice, and nobody's error — but a reminder that a licence **file** is a
> template someone chose, and the thing it describes may not be the thing in the
> repository.)*

**Scale.** ~**160 hours**, **300+ tasks**, **135 k+ episodes**, in three parts:

| Component | Scale | What it is |
|---|---|---|
| **HOI-Tac** | 11.5 M frames, ~**106 h** | **11 public hand–object datasets** — ARCTIC, DexYCB, H2O, H2O3D, HO3D, HOCap, HOI4D, HOT3D, InterHand2.6M, OakInk-v1/v2 |
| **DeskTask-Tac** | 37.2 h, 947 episodes | Bimanual desktop manipulation, **real sensors** — *"a tactile glove to record the tactility on the human hands"* |
| **InternData-Tac** | 17.8 h, 9,563 episodes | Three robot configurations |

**The mechanism, and the whole reason it sits here.** For its largest component,
tactile is **not measured** — it is computed from geometry: *"For each frame, we
generate per-vertex binary contact labels on the 778-vertex MANO hand mesh by
thresholding the distance between the hand surface and object meshes."*

> **So the two tactile routes are not interchangeable, and only one reaches found
> footage.**
>
> | | H-Tac's HOI-Tac | [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved) |
> |---|---|---|
> | Tactile from | **object meshes + hand mesh distance** | **RGB pixels** |
> | Needs | per-frame object geometry | nothing but video |
> | Runs on found footage | **no** | **yes** — zero-shot on Ego4D, EPIC, EgoDex |
>
> Internet video does not come with object meshes, so the *derived* route is
> closed to it by construction — the same shape as every other entry in
> [§2](#2-scaling-human-video-for-robot-learning). The *predicted* route is open.
> That distinction is what a pipeline needs in order to know which tactile-ish
> field it may honestly record, and this document would have blurred the two had
> it read only one of the papers.

**Its results are the strongest argument in the document for bothering at all —
read off the table this sweep, with the row labels the arrows had been hiding.**

| Task category | π₀.₅ | π₀.₅ + tactile | **BeingH-0.5** | TTP *w/o pre-train* | **TTP (theirs)** |
|---|---|---|---|---|---|
| Fine-grained | 43.2% | 48.3% | 57.3% | 71.0% | **96.7%** |
| Contact-rich & fragile | 3.3% | 8.0% | 9.2% | **49.7%** | **79.2%** |
| Vision defect | 17.8% | 17.8% | 15.6% | 26.7% | **37.8%** |

An earlier revision here wrote these as *"57.3% → 96.7%"*, *"9.2% → 79.2%"*,
*"15.6% → 37.8%"*. The numbers are all real, but the arrow implies a before-and-
after of one system when it is **their method against a baseline** — and the
baseline chosen was [BeingH-0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms),
which is not uniformly the strongest one: on **vision defect, π₀.₅ scores 17.8%
against BeingH-0.5's 15.6%**, so that particular arrow started from the weaker
of the two. Corrected to a table, which is what a five-column comparison needed
in the first place.

⚠️ **And the column this document should have been quoting is the fourth.**
*TTP without pre-training* is **49.7%** on contact-rich, against **79.2%** with
it. That is the ablation isolating what the tactile pre-training actually buys —
**+29.5 points, a ~59% relative gain, from the data rather than the
architecture** — which is precisely the question a collection project asks and
the baseline comparison cannot answer. The 9.2%-to-79.2% span is the more
dramatic number; **49.7% to 79.2% is the one that argues for building the
corpus.** Contact-rich manipulation going from half to four-fifths on
pre-training alone is why a contact field is worth having even when estimated
rather than measured.

🔴 **And MANO appears a third time.** Not as annotator ([WiLoR](#wilor--the-chokepoint-read-at-source)),
not as action space ([EgoVLA](#egovla--mano-as-the-action-space-not-just-the-annotation)),
but as **the mesh on which contact itself is defined** — the 778-vertex hand.
Three independent layers of the stack, one non-commercial, registration-gated
model.

⚠️ **Read against [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly), this is the counterfactual.** Both
aggregate many public corpora — OpenEgo six, H-Tac **eleven**, the largest
aggregation in this document. OpenEgo ships per-source licences, attribution
strings and an annotations-only redistribution rule. H-Tac's paper **states no
licence for H-Tac**, describes its inputs only as *"public datasets"*, and gives
no release timeline or repository. Same move, opposite hygiene, and the
difference is not scale or sophistication — it is a file somebody chose to write.
*Nothing improper is alleged*; the paper may simply predate its own release
process.

### The wristband — tactile *measured without instrumenting the hand*, and a fourth position

**[arXiv 2609.16518](https://arxiv.org/abs/2609.16518)** (16 Sep 2026; Kolev,
Ma, Goesele, De Nardi, Engel — the Project Aria side of Meta Reality Labs) —
this document has spent four entries building a three-way taxonomy of where
tactile comes from. **There is a fourth position, and it dissolves the problem
the other three work around.**

**Mechanism.** **Flexible capacitive sensor arrays around the wrist**, requiring
**no electrical skin contact**, feeding a recurrent network that maps the
pressure signal to hand state. The insight is anatomical rather than
computational: *"muscle contraction and tendon displacement produce pressure
patterns, which correlate strongly with hand pose and interaction force."*
Validated against synchronised optical mocap for pose and a **tactile glove** for
force, across isolated finger motion, fingertip-force stress tests and natural
hand–object manipulation.

**Numbers**: **4.6° mean finger-joint MAE** on isolated single-user motion; and
across four users manipulating everyday objects, per-finger contact force at
**R² = 0.57**, rising to **0.75** when an external pose signal is supplied.

> 🟢 **Why this is a fourth position and not a variant of the third.** The
> taxonomy so far divides on *what a found clip can supply*:
> [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
> **derives** contact from object meshes (closed to found footage),
> [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved)
> **predicts** it from RGB (open), and
> [EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame)
> **measures** it with a glove (the supervision that makes prediction trainable).
> **The wristband measures it too — but off the hand.** EgoTactile's whole rig
> design exists to solve one problem: *the glove is in the training pixels*. Its
> answer was to film a **bare** hand while a synchronised **off-camera gloved**
> hand supplied the reference — two hands, one protocol. **The wristband gets
> both from one hand**, because the sensor sits proximal to everything the camera
> cares about. **The visual-domain gap EgoTac names as its limitation and
> EgoTactile solves by choreography, this makes structurally impossible.**

⚠️ **Read the R² honestly, though.** **0.57 across four users on natural
manipulation** is a correlation, not a measurement — and it needs **an external
pose signal to reach 0.75**, which means the wristband alone is weaker than the
glove it is validated against. This is a *supervision* instrument for building
corpora, not a replacement for contact sensing in a benchmark.

> **The sentence that matters for this repo is the authors' own framing**: the
> wristband is *"one node in a constellation of everyday wearables — e.g. paired
> with an egocentric camera — **adding the contact force that vision cannot
> observe and taking over when the hand is occluded**."* That is a two-clause
> statement of what an egocentric corpus structurally cannot contain, from the
> lab that builds the cameras. **Occlusion is the failure mode this repo's hands
> gate exists to detect and discard; here it is the failure mode a second sensor
> is designed to cover.** A collection system that only filters cannot recover
> those frames — which is the honest limit on found footage, stated by someone
> building the alternative.

🔴 **No repository, no dataset, no project page, and no licence** — nothing named
anywhere in the paper.

### TouchSight and HumanTouch — a fifth position, and a licence that lives on another platform

**[arXiv 2609.20414](https://arxiv.org/abs/2609.20414)** (v1, 17 Sep 2026;
Tsinghua + SparkLab@Xspark AI) · project page
[`xsparkai.com/sparklab/humantouch`](https://xsparkai.com/sparklab/humantouch/) ·
[`chuqiaoLyu/Xspark-HumanTouch`](https://huggingface.co/datasets/chuqiaoLyu/Xspark-HumanTouch)
· [the same corpus on ModelScope](https://www.modelscope.cn/datasets/chuqiaoLyu/Xspark-HumanTouch)
— found by the recency pass on 20 Sep, three days after posting, and it lands on
two of this document's open questions at once.

🟢 **The fifth human-side position, and it attacks the constraint this document
had called structural.** The taxonomy above divides on what a found clip can
supply: H-Tac **derives** contact from meshes, EgoTac **predicts** it from RGB,
EgoTactile **measures** it with a glove, the wristband **measures it off the
hand**. TouchSight adds a fifth: **measure with the glove, then remove the glove
from the pixels.** It trains on **500 hours of pressure-glove recordings**, then
builds **TwinTouch-20H — 20 hours of paired video in which generative models
re-render the gloved footage as bare-hand observations against new backgrounds
while preserving the original measured tactile labels.**

> **This is the direct answer to the problem EgoTactile solved by choreography.**
> That rig exists because *the glove is in the training pixels*, and its fix was
> two hands and a protocol — film a bare hand, reference a synchronised gloved one
> off-camera. TouchSight pays the instrumentation cost once and then **edits the
> glove out in post, keeping the labels**. Its closing claim is the one that
> matters here: *"dense tactile signals can be recovered from egocentric vision
> alone, **without tactile instrumentation at capture time**."* If that holds, it
> is the **third RGB-only route** in this survey after
> [EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)
> and [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address),
> and the first one that recovers a channel the camera never saw.

⚠️ **Read at the limits the paper states.** The bare-hand generalisation is
reported as *qualitative* on unseen datasets; the quantitative comparison is on
**OakInk2**, and the scaling claim is that accuracy *"improves consistently as
glove supervision scales"* — which is a statement about how much gloved capture
you need, not about needing none. **The capture requirement has moved from every
hour to the supervision set**, which is a real change in the economics and not
the elimination of it.

**And the corpus underneath it is a capture programme with a dated commitment.**
The project page is **HumanTouch: A Multimodal System for Scalable Human-Hand
Tactile Acquisition** (published 7 Aug 2026). Its released first version is
**~100 hours — ten canonical tasks `X001`–`X010`, about ten hours each, on a
60 Hz unified timeline with all modalities synchronised**, in LeRobot format,
**88,085 files**. The roadmap on the card promises **~1,000 hours** *"within one
to two months"*, and the project page is more specific: ***"expand the public
release to 1,000 hours by the end of September 2026."*** 📅 **That is ten days
out and checkable, so this document will check it** — the same treatment given to
the mid-October download-ratio test, and for the same reason: a dated promise is
worth more than an undated one only if somebody returns on the date.

🔴 **The licence is the finding, and it is a shape this survey has not recorded
before: the terms are on the other platform.** The same corpus, from the same
publisher, sits on both hubs:

| Copy | Licence | Access | Counter |
|---|---|---|---|
| **Hugging Face** `chuqiaoLyu/Xspark-HumanTouch` | 🔴 **none** — `cardData: null`; the only tags are `size_categories`, `modality:video`, `region:us` | ungated | **12,285** |
| **ModelScope** `chuqiaoLyu/Xspark-HumanTouch` | **CC-BY-NC-4.0** | ungated | **2,584,370** |

**The README is identical on both, and its licence section reads, in full:
*"数据集许可以 ModelScope 仓库页标注的许可证为准"* — the dataset licence is governed
by the licence stated on the ModelScope repository page.** So the publisher did
not omit the terms; **it wrote a pointer instead of a licence, and aimed the
pointer at a different platform.** A reader who lands on Hugging Face — where the
Hub's own licence facet will file this corpus as unlicensed — has to know that
ModelScope exists, find the matching repository, and accept that a page on
another service governs bytes pulled from this one.

> **Why this is its own shape and not one of the six.** It is not *terms
> unstated* — they are stated. Not the *adjacent-artefact* trap — no paper or
> code licence is standing in for the data's. Not an *uploader stamp* — **both
> copies are the publisher's own.** It is a **cross-platform licence pointer**,
> and it fails in the way this survey cares about: the artefact you downloaded
> does not carry the terms you accepted, and the manifest field *"licence, as
> read at the artefact"* comes back empty for a corpus that has one.

⚠️ **The two counters are not comparable and the gap is not evidence.** Hugging
Face's is a rolling thirty-day rate; ModelScope's is undocumented on the API
response and may well be cumulative, file-level, or both — over **88,085 files**,
file-level counting alone would inflate it by orders of magnitude. **2.58 M is
recorded as a number this document read, not as a demand measurement**, which is
the rule the download-ratio series exists to enforce.

🔴 **The real finding is about this survey, not about HumanTouch: ModelScope is a
distribution surface it has never checked.** Every artefact-level verification in
this document — eighty sweeps of them — has queried Hugging Face, GitHub, or a
project page. The `arxiv:`-tag query installed [last sweep](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five)
searches the Hub and would not have found this corpus either. **Two sweeps
running, the fix has been *query a different index* — and both times the index
the survey was not asking held something it had concluded was absent.** The
honest statement of scope is now: *this survey's negative results are negative
about Hugging Face, GitHub and the paper's own pages, and say nothing about
ModelScope, OpenDataLab, BAAI, or any other hub.* Stated as a limit rather than
fixed in one sweep, because fixing it means re-running every *not released*
classification against a second index, and that is a pass of its own.

### AtomEgo — a provenance table that restates four corpora at once

**[arXiv 2609.21461](https://arxiv.org/abs/2609.21461)** (v1, 18 Sep 2026) —
*"a systematic study of ego–robot co-training supported by a curated corpus of
approximately 2,659 hours and a scalable data processing pipeline."* Read three
days after posting, and it lands on three threads at once.

**Mechanism.** Three co-training paradigms compared under matched data and
compute: **Atom-DH** (joint co-training with domain-specific action heads),
**Atom-CL** (progressive ego-to-robot transfer through explicit embodiment
alignment), and **Atom-WAM** (joint video–action modelling). Everything maps into
a single **80-dimensional state–action space** covering both arms, both
end-effectors, grippers, **twelve hand joints per hand**, leg joints, head and
waist — whole-body, and wide enough that the ego and robot sides are literally
the same vector with different slots filled.

🟢 **Its headline is the fourth independent statement of this survey's mixing
result, and the most compact.** *"Data Scale × Alignment Quality → Capability
Gain"*, with **Takeaway 1: "Effective alignment requires more than direct data
mixing."** [ReWeight](#reweight--the-control-simdex-did-not-run) showed it with
selection (39% → 44% → 57%), [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)
at a fixed hour budget, [UMI-Bridge](#simdex) with an intermediate domain, and
AtomEgo now states it as a product rather than a comparison: **scale that is not
aligned does not multiply into anything.**

🔴 **But Table 1 is the reason this entry exists, and it is the strongest
evidence in this document that an hour is not a fixed unit.** The paper prints a
full provenance table — source, episodes, hours, proportion — for a corpus this
survey already knows every row of:

| Group | Source | Episodes | Hours **as AtomEgo counts them** | The publisher's own figure |
|---|---|---|---|---|
| Robot | Piper (in-house) | 5,829 | 25.5 | — |
| Robot | [AgiBot World Beta](#the-robot-native-denominator) | 21,837 | **314.0** | **2,976.4** |
| Robot | [DROID](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it) | 64,124 | **343.0** | **350** *(and 1,285 in OpenWAM)* |
| Robot | [RoboCOIN](#the-robot-native-denominator) | 93,352 | **655.7** | **956** |
| Robot | **RoboMIND** *(new to this document)* | 83,152 | 221.7 | **hours not stated** |
| Ego | [EgoVerse](#egoverse) | 64,464 | **1,079.5** | **1,362** *(v2; 954 as Ego2Robot cites it)* |
| Alignment | in-house aligned ego–robot | 1,296 | ~20.0 | — |
| **Total** | | **334,054** | **~2,659.5** | |

> 🔴 **Four corpora, four restatements, and you cannot tell from the numbers
> which kind each is.** DROID at **343.0** against its own **350** looks like
> light filtering. AgiBotWorld-Beta at **314.0** against **2,976.4** is a **9.5×
> gap** and must be a subset. RoboCOIN at **655.7** against **956** is 69%.
> EgoVerse at **1,079.5** is a *third* value for a corpus already carrying two.
> And [OpenWAM's DROID at 1,285](#the-robot-native-denominator) is a restatement
> in the other direction, almost certainly camera-hours. **Same corpus, same
> field, and the printed hour-count can be smaller because of filtering, smaller
> because of subsetting, or larger because of a different unit — with nothing in
> the table distinguishing the three.** This is the survey's cleanest case for
> the rule it keeps arriving at: **a corpus name plus an hour-count is not a
> citation. The citation is the name, the count, and what was counted.**

⚠️ **The ego side is one corpus, and it is the one with no stated licence.**
EgoVerse supplies **all** of AtomEgo's egocentric data — 19.3% of episodes but
**40.6% of the hours** — and [EgoVerse states no dataset terms anywhere](#egoverse),
re-verified at v2, with access running through the authors' own EgoDB/S3 sync. So
a systematic, carefully controlled study of ego–robot co-training rests, on the
ego side, **entirely on a corpus whose terms cannot be read.** The robot side is
better: AgiBotWorld-Beta is CC BY-NC-SA 4.0, RoboMIND is **Apache-2.0**, RoboCOIN
Apache-2.0 behind a gate that adds obligations, and DROID says nothing at all.
**Of six external sources, exactly one — RoboMIND — is permissively licensed and
says so plainly.**

✅ **A stated acceptance rate, which this document collects.** *"Starting from
approximately **3,033 hours** of robot and egocentric data, our quality filtering
pipeline retains about **2,659 hours**"* — a **12.3% discard**, against three
state–action consistency checks adapted from Qwen-Manip. Far gentler than
[EgoScaler's 64%](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb),
which is what you would expect: filtering already-curated robot corpora for
corruption is a different job from deciding whether a found clip is usable at
all.

⚠️ **Release status, stated precisely.** The paper contains **one** external URL,
[`github.com/Agentic-Intelligence-Lab/Atom-0`](https://github.com/Agentic-Intelligence-Lab/Atom-0),
and **no sentence beginning "we release" or "we will release" anywhere** — every
occurrence of *"open-source"* in the text refers to **other people's** data. So
it names a surface without making a release claim, and **the 2,659-hour recipe
and the "scalable data processing pipeline" are not said to be published**. The
repo could not be read from this environment (the proxy 403s `github.com`), so
this is recorded as *a named surface with no release statement*, not as released
or unreleased. **For [§13](#13-why-no-open-source-project-does-exactly-this)'s
prospective count, that is a third distinct outcome** alongside *names a surface
and ships* (TouchSight) and *names nothing* (BinoGen, and the 15–16 September
four).

**Bearing here.** AtomEgo is the closest thing yet to a controlled experiment on
the question this repo exists to serve, and its answer is the one the manifest is
designed around: **hours only convert into capability through alignment, and
alignment is a property you have to know about a clip before you mix it in.**
What it does not do — and says it does not — is source any of those hours from
the open web. Every one of its 2,659 comes from a corpus somebody else already
commissioned.

### The UMI family — capture without a robot, and the blind spot this survey had

**UMI** is named seven times in this document — as
[UMI-Bridge](#simdex)'s intermediate domain — and has never had an entry. It is
not one project but a **capture category**, and it is the cheapest controlled
capture anywhere in this survey.

**[UMI](https://umi-gripper.github.io/)** (Chi et al., Stanford) is a **hand-held
parallel-jaw gripper with a GoPro mounted on it**. A person walks around
squeezing it; what comes out is *"in-the-wild human demonstrations"* that
transfer **directly** to robot policies, with *"latency matching and a
relative-trajectory action representation"* making the learned policies
*"hardware-agnostic and deployable across multiple robot platforms."* Code and
hardware: **MIT**.

| Variant | What it adds | Artefact |
|---|---|---|
| **UMI** | the handheld gripper + GoPro pattern itself | code **MIT** |
| **FastUMI** ([2409.19499](https://arxiv.org/abs/2409.19499)) | hardware-decoupled redesign; **drops the VIO dependency** | `IPEC-COMMUNITY/FastUMI-Data` — **MIT**, gated, 3,034 downloads |
| **FastUMI-100K** ([2510.08022](https://arxiv.org/abs/2510.08022)) | **100 K+ trajectories, 54 tasks**, household environments, multi-view wrist fisheye + high-frequency end-effector states, LeRobot v2.1 | `IPEC-COMMUNITY/FastUMI_100k_lerobot` — ungated, **269,342 downloads**, 🔴 **no licence** |
| **RealDexUMI** ([2606.06033](https://arxiv.org/abs/2606.06033)) | **wearable**: a shared dexterous end-effector with **in-hand vision and fingertip tactile**, plus a palm-side isomorphic glove | none found |
| **TacUMI** ([2601.14550](https://arxiv.org/abs/2601.14550)) | ViTac sensors, force-torque, pose tracker on a robot-compatible gripper | a 2-download repo, no licence |

🔴 **What this does to [the denominator](#the-robot-native-denominator), and it
is the sharpest version of that section's point.** **FastUMI-100K is 100 K+
demonstration trajectories. DROID is 76 k** — thirteen institutions, fifty
collectors, a Franka each, twelve months. **UMI-style collection produced more
trajectories, in robot-compatible action format, without a single robot.** The
scarcity of teleoperated data is not a law about how hard manipulation data is
to get; **it is a consequence of insisting on a robot in the loop**, and a
handheld gripper removes it.

> 🟡 **And what it does to this repo's thesis is less comfortable, which is why
> it belongs here.** UMI does **not** weaken
> [§13](#13-why-no-open-source-project-does-exactly-this): none of this is found
> footage, and UMI scales the way [Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape)
> and UniCraftor scale — **by deploying devices to people**. But it sharpens the
> comparison an hour of found footage has to win. **The competition is no longer
> teleoperation at 350 hours and rising slowly.** It is a **$400-ish handheld
> gripper** producing **robot-compatible end-effector trajectories** — no
> retargeting, no MANO, no embodiment gap to cross — already at **100 K
> trajectories and 269,342 downloads**. Found footage's advantages over UMI are
> real and narrow: **scene and object diversity no device deployment can buy, at
> a volume no capture programme reaches.** Its disadvantage is exactly what this
> document spends five thousand lines on. **Anyone arguing for the found-footage
> route should be arguing against UMI, not against teleoperation** — and this
> survey had not noticed it was there.

> **RealDexUMI is the limit case of "match at capture".**
> [EgoMimic](#egomimic) closed the embodiment gap by choosing a robot that
> minimises kinematic difference from a human hand. RealDexUMI closes it by
> having the human **wear the robot's actual end-effector** — *"a shared
> dexterous end-effector module"* giving *"zero-gap end-effector data, with
> matched in-hand observations, tactile signals, contacts"*. **There is no gap
> to cross because there is one hand.** It is the cleanest answer in this
> document to the retargeting problem, and it is available to precisely nobody
> who did not buy the hardware.

🔴 **A third shape of half-a-card, and it completes the set.**
`FastUMI_100k_lerobot` has **a real 4.3 KB README** — overview, scale figures,
LeRobot install instructions, a link to the paper — and **no YAML front-matter
at all**, so **no licence field**. Set against the other two:

| Artefact | Downloads | Description | Licence |
|---|---|---|---|
| `gatech/EgoMimic` | 1,258 | ❌ | ❌ |
| `tars-robotics/OmniVitac` | 27,810 | ❌ | ✅ CC BY-NC 4.0 |
| **`IPEC-COMMUNITY/FastUMI_100k_lerobot`** | **269,342** | ✅ **thorough** | ❌ **none** |

**Neither half, one half, the other half — and the one with the most downloads in
this survey bar Open-AoE is the one that tells you everything except what you may
do with it.** The same organisation's earlier, smaller FastUMI-Data *is* MIT and
*is* gated; **the big ungated one is the one that lost its terms.**

### OmniViTac — tactile on the robot side, 27,810 downloads, and a card that says only its licence

**[arXiv 2603.19201](https://arxiv.org/abs/2603.19201)** (v3) — the four
positions above are all about *human* hands. This is the robot-side counterpart,
and the largest visuo-tactile corpus in this document: **21,000+ trajectories
across 86 tasks and 100+ objects**.

**Its diagnosis is this document's own, applied to tactile.** Contact-rich tasks
*"require accurate perception of contact forces, friction changes, and state
transitions that cannot be reliably inferred from vision alone"*, and progress is
held back by two things: *"existing datasets are small in scale and narrow in
task coverage"*, and *"current methods treat tactile signals as **passive
observations** rather than using them to model contact dynamics or enable
closed-loop control explicitly."* The second half is the interesting one for a
collection system: **a tactile field recorded but not used to predict what
happens next is an annotation, not a signal.**

**Terms**: [`tars-robotics/OmniVitac`](https://huggingface.co/datasets/tars-robotics/OmniVitac)
is **CC BY-NC 4.0**, **ungated**, **27,810 downloads** — more than
[EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame)
and [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
combined, by a wide margin.

⚠️ **And its entire dataset card is three lines of YAML naming the licence.** No
description, no scale figures, no schema, no link to the paper, no arXiv tag —
the card's whole content is `license: cc-by-nc-4.0`. The scale figures above come
from the *paper*; nothing on the artefact states them. **This is the EgoMimic
shape** — real data, real traffic, a real licence, **and no way to tell from the
download what it is** — except that where EgoMimic omitted the licence and kept
the description, this omits the description and keeps the licence. **Both halves
are needed and publishers keep shipping one.**

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

**[arXiv 2604.07607](https://arxiv.org/abs/2604.07607)** (**v2, 7 Jul 2026**, re-read this sweep) — 1,362 hours, 80,000
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

### MobileEgo Anywhere

**[arXiv 2605.05945](https://arxiv.org/abs/2605.05945)** (**v7, 8 Jul 2026** —
seven revisions, and the figures moved) — quoted at v7: *"The released dataset
contains **584 sessions** totaling **200 hours** from **20 contributors**,
averaging **20.5 minutes** with a maximum of 108 minutes."* Captured on iPhone
Pro devices in head rigs in household environments. The app is hands-free by
voice ("start" / "stop") and writes synchronised RGB, depth, IMU and ARKit 6-DoF
pose into MCAP.

⚠️ **This document had 354 sessions, 16 contributors and 21.2-minute averages** —
figures read at an earlier revision and carried since. The hour count and the
108-minute maximum are unchanged; **the session and contributor counts grew by
roughly 65% and 25%** as the collection continued. A dataset that is still being
gathered has a scale that expires faster than a finished one, which is an
argument for pinning the revision a figure was read at even when a paper's own
citation does not.

The **STERA** pipeline behind it:

1. **3D hand trajectory** — WiLoR produces MANO hand poses, unprojected into 3D
   with ARKit depth and transformed into a global frame.
2. **Atomic action labels** — a VLM writes captions with object modifiers and
   spatial prepositions ("transfer dough from metal bowl to large plate").
3. **Hierarchical instructions** — an LLM organises those into a **three-level
   tree**: a session-level goal, sub-goals, and episodes, with three invariants
   enforced — *"unique span assignment, exact timestamp boundaries, and full
   session coverage"*. ⚠️ **The counts this document carried — 45,415 atomic
   spans, 5,570 episodes, 1,298 sub-goals — do not appear in v7 at all.** They are
   retained here marked as **read at an earlier revision and not re-verifiable at
   the current one**, which is the honest state: not withdrawn, not confirmed.

🔴 **Licence — this document had it wrong, and wrong in the way it warns others
about.** The entry said **"Licence CC BY 4.0."** That is the string
`License: CC BY 4.0` on the **arXiv listing**, which governs the *paper*. The
dataset is **[fpvlabs/stera-10m](https://huggingface.co/datasets/fpvlabs/stera-10m)**,
whose card metadata says **`license: other`**, is **gated**, and returns **401 to
an unauthenticated fetch** — so, as with its sibling below, **the licence text
cannot be read before agreeing to it.** This is the
[adjacent-artefact trap](#the-vocabulary-problem--six-ways-a-name-misleads)
that §11 catalogues, committed by the document that catalogues it. Reclassified
from *permissive* to **bespoke, unreadable** — the fifth licence shape, not the
first.

🔴 **And the sibling is the point: `fpvlabs` publishes both this and
[Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape).** The
organisation's Hugging Face account holds exactly two datasets —
**`stera-10m`** (MobileEgo Anywhere, 7,043 monthly downloads) and
**`stereo-550`** (Ego-OSCAR's Stereo-550, **199,055 monthly downloads**) — both
`license: other`, both gated. This survey had written them up as unrelated
projects across two sections. **They are one lab, with one bespoke licence
posture applied to both**, which is why Ego-OSCAR's `fpvlabs-license` and this
`other` are the same thing seen twice. It is the third time the survey has found
two entries that were really one group, after
[NVIDIA's DreamDojo/EgoScale](#egoscale) and
[BeingBeyond's five](#being-h07--one-corpus-three-products-and-a-second-vendor-doing-it).

> **Worth noting the download figure, re-read this sweep.** Stereo-550 is now at
> **242,618 monthly pulls** against
> [Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)'s
> **124,711** — so the single most-pulled corpus in this document is one whose
> terms **nobody can read without first accepting them**, and its lead has
> *widened* from 1.4× to **1.6×** while the Apache-2.0 corpus fell 14.5%.
> Stereo-550 has risen at every reading — **199,055 → 201,019 → 242,412 → 242,618** — and
> its lead over Egocentric-100K is now **2.0×**. **The most-pulled corpus in this
> document has been the one whose terms nobody can read without first accepting
> them, at every single reading.**

**Also released, and not previously recorded here:** a `stera-sdk`, the
`stera-10m` Hugging Face dataset, and a hosted visualisation platform — so the
tooling side is genuinely shipped, whatever the terms say.

Quality reporting is unusually candid: 87% of sessions
passed all structural checks, 46 needed automatic correction, hand-pose
consistency was evaluated on 98 of 354 sessions, human validation on 50 — ⚠️ all
four figures **read at the earlier revision and absent from v7**, so they are
kept on the same footing as the annotation counts above: recorded, not
re-confirmed. Note that "98 of 354" is now "98 of 584" if the denominator moved
with the corpus.

> **Bearing here — the third independent convergence on the same shape.** This
> repo's task → action → event tree, [Action100M](#action100m)'s brief action →
> detailed action → caption, and MobileEgo's atomic step → sub-goal → session
> plan are the same three-level structure, arrived at by three groups who were
> not talking to each other. That is about as much external validation as an
> annotation schema ever gets. Note also which axis they agree on: **temporal
> scope**, not semantic category — the levels differ by how much time they
> cover, not by what kind of thing they name.
>
> [Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)
> is a fourth, and it goes deeper: task → subtask → action → interaction →
> objects. The last two levels leave the time axis for the object axis, which is
> the natural extension once you have hand and object tracks to hang labels on —
> and a reasonable sketch of where an `L4` would go if this repo's gates ever
> need one.

### EgoKit

**[arXiv 2605.16797](https://arxiv.org/pdf/2605.16797)** — not a dataset at all,
which is the point: a toolkit for capturing your own, across Android phones,
iPhones, iPads, Project Aria, Apple Vision Pro, Meta Quest 3 and PICO 4 Ultra.
Platform-native apps (Kotlin / Swift / Unity) share one recording interaction and
one log format; XR headsets additionally log head pose and OpenXR 26-joint hand
tracking aligned to the video. Output is H.264 MP4 with per-frame timestamps.

It exists because "each candidate host device exposes a different SDK, a
different policy on raw camera access" — and its limitations are a good map of
where consumer ego capture actually breaks: Apple Vision Pro lacks the
enterprise entitlements for raw camera access, cross-device time sync is hard,
wrist mounts occlude and collide with desks, and battery caps session length. No
dataset is released and no data licence applies; the paper carries only the
arXiv licence.

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

### ACE-Ego-0

**[arXiv 2606.17200](https://arxiv.org/html/2606.17200v1)** — unifies egocentric
human demonstrations and robot trajectories into a single VLA pretraining
framework rather than treating them as separate stages. (The project URL printed
in the paper, `acerobotics-vla.github.io/ACE-Ego/`, returns 404 as of this
writing; the arXiv HTML is the working source.)

⚠️ **A candidate artefact appeared this sweep, and it is recorded as a candidate
rather than a finding.** [`acerobotics2025/ACE-Ego-0`](https://huggingface.co/acerobotics2025/ACE-Ego-0)
is a model repository created 8 September and updated 14 September 2026, tagged
**`apache-2.0`**, holding `checkpoints/pretrain` and `checkpoints/robocasa24`,
with **zero downloads**. Its entire `README.md` is 28 bytes — the YAML licence
key and nothing else. **No arXiv tag, no description, no author statement, no
link back.** The namespace is plausible and the checkpoint names fit, and that is
all that can be said. Contrast [OmniRetriever](#omniretriever), whose cards in a
personal namespace *were* accepted as the paper's release — because they carry
`arxiv:2605.26641`. **One tag is the difference between an artefact and a
coincidence**, which is why this document keeps asking for identifiers instead of
names. Until something ties it, ACE-Ego-0's terms stay unresolved.

**Scale, quoted from the paper**: *"4.53K hours of robot and simulation data,
together with 1.48K hours of pseudo-action-labeled egocentric human data."*

Two mechanisms carry it, and both are worth reading closely because they are the
modelling-side answers to problems this repo solves on the data side.

**1. A unified action representation**, aligning heterogeneous sources on three
axes: **spatial** — actions expressed in the head-camera frame, so no
platform-specific transform is needed; **structural** — cross-embodiment
morphology conditioning, URDF encoding for robots and *learned surrogate
embeddings for humans*; **temporal** — action chunking indexed by **physical
duration rather than frame count**, so sources at different control frequencies
stay comparable.

**2. A reliability-aware training objective**, which is the important one. Robot
data gets a primary flow-matching loss on sensor-logged trajectories. Human data
gets an *auxiliary* loss: weighted supervision concentrated on the reliable
position channels, Huber regression to absorb noisy pseudo-actions, and — the
detail that matters here — **step-level *and* dataset-level quality estimates**.

> **Bearing here, and it is direct.** ACE-Ego-0 wants a per-source *and*
> per-timestep confidence on every human-derived label, because pseudo-actions
> recovered from video are not equally trustworthy across clips or across
> moments within a clip. That is exactly what a manifest carrying per-clip
> viewpoint confidence, hands evidence and annotation depth provides — and it is
> information that **only exists if it was recorded at collection time**. A
> corpus shipped as undifferentiated hours forces the trainer to estimate
> reliability from the pixels; a corpus shipped with the evidence lets it read
> reliability off the metadata. Our four hour measures and L0–L3 depth grades are
> the right shape for the second.

Results: **72.8%** average success on RoboCasa GR1 TableTop, **91.12% / 90.62%**
Easy/Hard on RoboTwin 2.0, and **78.3%** across six tasks on a real ARX bimanual
platform.

⚠️ **On the mixture ratio.** Roughly **3:1 robot-and-sim to human** — the reverse
of what "an hour of hand data beats an hour of robot data" might lead you to
expect. Note the "and simulation" though: 4.53K hours dwarfs
[DROID's 350 real teleoperated hours](#the-robot-native-denominator), so most of
that side is simulated or proprietary rather than real-robot. One recipe's
proportions, not a law — but a concrete data point on a question the rest of this
section leaves open.

**Its pretraining pool is Ego4D + EPIC-KITCHENS + Ego-Exo4D + EgoDex + EgoScale**,
alongside robot datasets. Set that against [§11](#11-the-licence-trap):

| Component | Terms |
|---|---|
| EPIC-KITCHENS-100 | CC BY-NC 4.0 — non-commercial |
| EgoDex | CC-BY-NC-ND — non-commercial, **no derivatives** |
| Ego4D / Ego-Exo4D | signed agreement, **terms not published publicly** |
| EgoScale | **not yet released** — code "coming soon", no licence stated |

> **Why this belongs in the document.** [Open X-Embodiment](#the-robot-native-denominator)
> pools 60 datasets whose terms are *unstated*. ACE-Ego-0 pools five whose terms
> are individually **stated and restrictive**. Those are different problems and
> both land on the same person: whoever wants to ship something built on the
> resulting model. Nothing here alleges non-compliance — research pretraining and
> commercial deployment are different questions, and the paper is doing the
> former. The point is that **the provenance chain has now appeared at the model
> layer, not just the dataset layer**: by the time a checkpoint is public, the
> restrictions of five upstream corpora are baked into it and are no longer
> visible from the artefact. Recording rights per clip at collection time is the
> only place that information survives.

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

🔴 **Nothing is released, and the project page is built so that you would not
notice.** [lin-nie.github.io/SiMDex](https://lin-nie.github.io/SiMDex/) presents
four buttons in a row — *Paper*, *Demo*, **Code**, **🤗 Hugging Face**. The first
two work. The last two are `<a href="#" class="disabled">`: styled as links,
inert on click, with no "coming soon" label next to them even though the page's
stylesheet defines a `.soon` class for exactly that purpose. There is no
repository, no dataset, and **no licence stated anywhere** — paper, page or
artefact. Cited at v1, the only version.

> **Why this one stings.** SiMDex is the nearest published neighbour to this
> repo's usability ranking, and the part worth having is not the 13.4-point
> result — it is the recall→ranking→re-ranking machinery that produced it. That
> is precisely what is not available. Read the entry as a *finding to reproduce*,
> not a component to adopt.
>
> And note the presentation pattern, which is new to this document's
> [naming and framing traps](#the-vocabulary-problem--six-ways-a-name-misleads):
> earlier entries were undone by a word — "in the wild", "open", a licence on the
> wrong artefact. This one is undone by **a dead link that looks like a live
> one**. A reader skimming the header counts four affordances and infers four
> things exist; nothing on the page is false, because nothing on the page is a
> claim.

### ReWeight — the control SiMDex did not run

**[arXiv 2609.13851](https://arxiv.org/abs/2609.13851)** (12 Sep 2026; Wang,
Huang, Ko, Bai, Jiang) — the same problem as [SiMDex](#simdex), attacked
independently three weeks later, and with the one comparison that turns the
result into an argument.

**Mechanism.** A **cross-embodiment visuomotor representation** combining visual
observations with *future actions* measures behavioural similarity between human
and robot demonstrations. **Optimal transport** then retrieves the human
demonstrations relevant to the target robot data, and a sample-level weighting
gives more weight to samples with smaller cross-embodiment discrepancy. So:
retrieval at the demonstration level, weighting at the sample level, over π₀.₅.

🟢 **The numbers, and why the middle column is the whole point.** In simulation,
across eight tasks:

| Post-training data | Average success |
|---|---|
| **robot data only** | **39%** |
| **robot + randomly mixed human data** | **44%** |
| **robot + ReWeight-selected human data** | **57%** |

**Adding human data at random buys 5 points. Choosing which human data buys 18.**
Real-world, across four tasks: **68.8%**, beating those two baselines by **28.8**
and **13.8** points.

> **This is the cleanest statement of "selection, not volume" in the document,
> and it is cleaner than SiMDex's** — because SiMDex compared its mined subset
> against *an equal quantity of randomly sampled human data*, while ReWeight puts
> **robot-only, random-mix and selected-mix in one table**. That third baseline is
> what shows the failure mode: *"directly mixing human and robot data can
> introduce cross-embodiment discrepancies and **degrade** policy performance."*
> A collection system that delivers hours without an argument for them is not
> merely inefficient — **it can make the downstream model worse**, and the gap
> between 44% and 57% is the price of the argument.

🟢 **A third independent measurement of the same thing, four days later.**
**[UMI-Bridge](https://arxiv.org/abs/2609.18232)** (16 Sep 2026) uses the
handheld **UMI** gripper as an *intermediate domain*, aligning human and robot
representations *"according to action equivalence rather than pixel
similarity"* — UMI's action supervision anchors the latent to end-effector
motion and gripper behaviour, with synchronised head–wrist observations and
paired ego–UMI clips bridging the viewpoints. It trains a dual-view latent
action model **on human data with no robot demonstrations at all**, then freezes
it to regularise VLA post-training. **91.7% mean success against 73.3% for naive
co-training on matched data**, and on two data-efficiency tasks it **beats a
full-data robot-only baseline using 25% of the robot demonstrations.**

> **Three papers in one fortnight, three mechanisms, one finding.** ReWeight
> selects by cross-embodiment discrepancy;
> [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)
> splits a fixed budget; UMI-Bridge aligns through a shared physical interface.
> **All three report that the naive version — mix human and robot data and
> train — is the one that underperforms.** The disagreement in this literature
> is no longer *whether* human video substitutes for robot data. It is
> **what you have to know about a clip before it helps**, which is the question
> a manifest answers and an hour count does not. 🔴 *No repository, dataset,
> project page or licence named in the paper.*

🔴 **Nothing is released, and the project page has an unusual defect worth
recording.** [reweight-vla.github.io](https://reweight-vla.github.io/) carries no
code, no data, no checkpoints, and **no licence**. Its only outbound artefact
link points at a **Hugging Face collection belonging to a different project
entirely** — `furonghuang-lab`'s TraceVLA — almost certainly unedited boilerplate
from the page template the authors started from. **A new variant for the
[trap list](#the-vocabulary-problem--six-ways-a-name-misleads):** SiMDex's links
were dead, EgoScale's name collided with a live project's, and this one is a
**live link to the wrong project's artefacts.** A reader who follows it lands
somewhere real, which is the worst case of the three.

### MINT — camera alignment at scale, and a release sentence with no address

**[arXiv 2609.04958](https://arxiv.org/abs/2609.04958)** (v2) — *"Minting
IN-the-Wild Trajectories"*. It answers, directly, the middle term of the
[acceptance specification](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms)
a 35,000-hour pre-training team wrote: *accurate depth, **stable camera
alignment**, temporally precise interaction events.*

**Mechanism.** From one shared spatiotemporal video representation over **RGB
alone**, MINT jointly predicts **camera trajectory, field of view, camera-frame
hand states, and per-frame hand observability**, then produces world-space hand
motion by explicit coordinate transformation — replacing the usual stack of
separate camera-motion, depth, hand-reconstruction and trajectory-refinement
stages. Supervision comes from **EgoPipeline**, a labelling pipeline that
annotates **1,021 hours** of public egocentric video drawn from **Ego4D,
EPIC-KITCHENS and [EgoDex](#egodex)** with camera trajectories and **bimanual
MANO states**; MINT pretrains on those pseudo-labels, then fine-tunes on a small
high-quality set.

**Results**, zero-shot on benchmarks it never trained on: **0.945 frame accuracy,
13.646 mm PA-MPJPE-p, 55.058 px EPE-p** for camera-frame bimanual reconstruction
on HOT3D; **4.690 mm RPE-T and 0.284° RPE-R** for camera trajectory; and **a
3.67× end-to-end speedup over the labelling pipeline that supervises it** —
i.e. the student is cheaper than the teacher, which is what makes it usable as a
gate rather than an offline annotation job.

> 🟢 **Two things here matter more than the accuracy numbers.** First,
> **per-frame hand observability** is a *hands gate* — a learned, per-frame
> answer to "are the hands actually visible here", which is one of the checks
> this repo asserts per clip and which has so far had no published foundation
> model behind it. Second, the whole thing runs on **RGB alone**, joining
> [EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)
> as work compatible with footage you did not capture. **The difference is
> instructive: EgoScaler escapes MANO by tracking objects; MINT goes through
> MANO and gets the hands.** You can have found-footage compatibility or a
> MANO-free chain, and nobody has yet shown both with hands.

🔴 **Two encumbrances, and the second is a shape this document has not recorded
before.**

1. **EgoDex is one of its three sources.** A 1,021-hour derived trajectory corpus
   built partly on a **CC-BY-NC-ND** dataset would carry those terms — making
   this the **sixth** downstream artefact resting on EgoDex, the document's
   most-reused chokepoint. And the labels are **MANO states**, so the corpus is
   MANO-shaped at the level of the file, as
   [ViTRA's](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)
   is.
2. 🔴 **The paper says *"We release the model, training and inference code,
   labeling pipeline, and a curated 1,021-hour egocentric trajectory dataset"* —
   and gives no address for any of it.** There is **no URL anywhere in the
   paper**: no repository, no project page, no dataset card, in v1 or v2. A
   Hugging Face search for the model and for EgoPipeline returns nothing.
   **This is a new failure shape for the [licence-and-release
   table](#11-the-licence-trap): not *"coming soon"*, not a title asserting
   openness, not a dead button — a release stated in the present tense with
   nowhere to go.** Recorded as **not locatable**, which is distinct from *not
   released*: the artefacts may well exist somewhere this document cannot find.

⚠️ **And a seventh *"in the wild"*, this one inside an acronym.** *Minting
IN-the-Wild Trajectories* — the trajectories are minted from Ego4D, EPIC-KITCHENS
and EgoDex.

🟢 **And a week later, the *first* term of the same specification gets an
answer.** **[MEgoVista](https://arxiv.org/abs/2609.16684)** (15 Sep 2026) turns a
single **unprepared** head-worn recording into **metric** two-hand and head
motion in one gravity-aligned world frame. Its diagnosis of the status quo is
the one this document has been circling: today's metric hand labels come from
studio rigs and instrumented headsets, and *"neither leaves a prepared setting,
and neither is checked against an independent reference."* Three properties it
claims against that:

- it **takes its metric gauge from calibrated stereo rather than a monocular
  prior**, *"installing scale at initialisation so policies receive physical
  units, not arbitrary coordinates"* — which is the acceptance spec's **accurate
  depth**, where [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)
  answered **stable camera alignment**;
- it **settles hand ownership at detection so bystander hands stay out of the
  wearer's trajectory** — 🟢 **a per-clip gate nobody else in this survey
  states**, and one a found-footage pipeline needs badly, since crowded scenes
  are exactly where web video differs from a lab;
- it is **scored inside a motion-capture volume against independent Chingmu
  optical capture**, *"under a protocol that audits its own reference and charges
  what a method declines to predict"* — i.e. abstention is penalised rather than
  quietly excluded, which is the evaluation discipline this document's
  [acceptance rate](#12-free-hours-and-what-they-do-to-the-moat) argument needs.

⚠️ **An eighth *"in the wild"*, in its subtitle** — *"Metric 4D Hands and Head in
the Wild"* — where *in the wild* means **unprepared settings recorded by the
wearer**, a fifth distinct sense in this survey. 🔴 **And no repository, dataset,
project page or licence is named in the paper.**

### Panda-70M

**[CVPR 2024](https://github.com/snap-research/Panda-70M)** — 70.7 M
video–caption samples from 3.78 M source videos (~36 TB), with 10.47 M (8 TB) and
2.4 M (1.6 TB) subsets and 6,000-sample validation and test splits. 703 stars.

✅ **Audited at the repo's own table this sweep; every figure holds exactly** —
70,723,513 samples from 3,779,763 videos, 10,473,922 from 3,755,240, 2,400,000
from **800,000**, validation and test 6,000 each. 🟢 **And it publishes the
column this document cares about and had never recorded: hours.** The full set is
**167,000 hours** (37,000 for the 10 M subset, 7,560 for the 2 M, 18.5 for each
eval split). **That is 167× DROID and larger than
[Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)'s
100,405 h** — a reminder that the web-video corpora this pipeline's *tooling*
comes from operate an order of magnitude above the egocentric ones its *subject
matter* does. None of those hours are egocentric, which is the whole of §13 in
one row. Its licence file also instructs, in a sentence: *"Users must follow the
related license to use these video samples"*, pointing at **HD-VILA-100M's**
— the inheritance the [derivation map](#who-feeds-whom--the-derivation-map)
credits it for, stated by the publisher rather than inferred by a reader.

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
for generation, and 85% run under 10 seconds.

**Terms, read at the artefact this sweep — the entry had never stated them, and
the claim they support is repeated four times elsewhere in this document.**
[`OpenGVLab/InternVid`](https://huggingface.co/datasets/OpenGVLab/InternVid)
carries **`cc-by-nc-sa-4.0`** ✅ — **non-commercial *and* share-alike**, as the
[derivation map](#who-feeds-whom--the-derivation-map) has been saying. So the
claim holds; it was simply being asserted from a table rather than from the card.

⚠️ **And the card carries the shape found one sweep ago at
[RoboCOIN](#the-robot-native-denominator): a gate that adds an obligation the
licence does not contain.** InternVid's `extra_gated_prompt` reads *"You agree to
not use the data to conduct experiments that cause harm to human subjects."*
RoboCOIN's reads *"You agree to not use the dataset to conduct experiments that
cause harm to human subjects."* **Near-verbatim, across two unrelated publishers
in different subfields.** Two instances make it a pattern rather than an oddity,
and the near-identical wording says what the pattern is: **the gate text itself
is a circulating artefact**, copied between release templates the way a `LICENSE`
file is. **Nobody wrote a bespoke clause; somebody reused one** — which is worth
knowing, because it means the added obligation should be expected on the *next*
card too, and read rather than assumed absent.

🔴 **A third instance of one corpus in two access cells, and the first where both
copies are the publisher's own.** `OpenGVLab/InternVid` is **gated (auto)**;
`OpenGVLab/InternVid-Full` is **ungated**. Same organisation, same
**CC BY-NC-SA 4.0**. [S-EMBER](#s-ember)'s ungated copy was a leftover review
mirror and `InternData-A1`'s was a third party's conversion — **here the
publisher maintains both**, so a reader's experience of how open InternVid is
depends entirely on which of two sibling cards they land on. **The access axis is
not single-valued per dataset, and this time nobody else is to blame for it.**

🔴 **Licence — resolved on re-check, and it moved category.** An earlier revision
of this entry recorded *no licence stated on either surface*. Re-read at the
Hugging Face dataset page this sweep, the card carries **`cc-by-nc-sa-4.0`**,
and access is **gated**: *"agree to share your contact information to access this
dataset"*, with a further condition that users *"not use the data to conduct
experiments that cause harm to human subjects."* Whether the card changed or the
earlier check missed it, the current state is unambiguous — and it is the
**most restrictive combination in this document**, non-commercial *and*
share-alike, the same terms as [AgiBotWorld-Beta](#the-robot-native-denominator).
A derivative built on InternVid inherits both clauses.

> **Two lessons, and the second is the one that costs.** An "unresolved" field is
> a *snapshot*, not a property — the same discipline the [470:1
> correction](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) forced
> on live numbers now applies to licences, which change quietly and without
> announcement. And the direction of this one is worth noticing: the field's
> unstated terms are not defaulting to permissive when they finally get stated.

### NeMo Curator

**[NVIDIA-NeMo/Curator](https://github.com/NVIDIA-NeMo/Curator)** — GPU-accelerated
load / filter / dedupe / transform across text, image, video and audio, **Apache
2.0**, 1.7 k stars, actively released (26.04 shipping Cosmos-Xenna 0.2.0). For
video the documented stages are **scene detection, clip extraction, motion
filtering and deduplication**; no throughput figures are published.

⚠️ **A relationship worth stating precisely**, because the two names are easy to
treat as rivals: **Cosmos-Xenna is NeMo Curator's production execution layer**,
not a competing tool. NeMo Curator is the high-level pipeline framework; the same
pipeline definitions run under different executors, with XennaExecutor as the
production default. [cosmos-curate](#cosmos-curate) sits on the same substrate.
Choosing between them is a question of which pre-built pipeline you want, not
which engine.

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

> **One vendor now occupies four positions in this document.** NVIDIA ships the
> world-model platform ([Cosmos](#4-world-model-and-physical-ai-stacks)), the
> curation substrate ([NeMo Curator](#nemo-curator) and
> [cosmos-curate](#cosmos-curate)), the largest crowdsourced egocentric corpus
> ([DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13),
> 44,711 h), and the largest action-labelled ego VLA ([EgoScale](#egoscale),
> 20,854 h). Generation, curation, corpus and policy, in one house. That is worth
> noticing for two reasons: it explains why the *tooling* layer is unusually
> well-served by open source here — a GPU vendor benefits when anyone runs a
> large pipeline on anything — and it sharpens
> [§13](#13-why-no-open-source-project-does-exactly-this)'s point that the
> **acquisition** layer stayed closed even so. The company with the most complete
> stack in the field still bought its hours rather than mining them.
>
> 🔴 **And the four positions rest on fewer than four acquisitions.** DreamDojo
> and EgoScale report **identical scene, task and object counts** and the same
> 829-hour EgoDex component, without citing each other — evidence set out
> [in EgoScale's entry](#egoscale) — so the corpus behind the world model and
> the corpus behind the VLA are, on the face of it, one corpus. Read that way
> the position is *more* concentrated than it first looks and the §13 reading
> gets sharper still: the best-resourced actor in the field did not buy its
> hours repeatedly. It bought them **once**, and built everything downstream on
> that single purchase, because there was no second way to get them.

### DreamDojo — and the strongest evidence in this document for §13

**[arXiv 2602.06949](https://arxiv.org/html/2602.06949)** (NVIDIA, ICML 2026;
code [Apache 2.0](https://github.com/NVIDIA/DreamDojo), 2B and 14B checkpoints
released Feb 2026) — a generalist robot world model trained on **44,711 hours of
egocentric human video**, reported as 15× the duration, 96× the skills and
2,000× the scenes of the previously largest world-model training set.

The composition is the part that matters here:

| Source | Hours | How obtained |
|---|---|---|
| **DreamDojo-HV** | **43,827** | **Crowdsourced** — loco-manipulation across household, industrial, retail, educational and administrative settings |
| [EgoDex](#egodex) | 829 | Existing public dataset (**CC-BY-NC-ND**) |
| In-lab | 55 | Self-captured, Manus gloves + Vive Ultimate Tracker |

> **Read that first row again.** The largest egocentric corpus ever assembled for
> a world model — by NVIDIA, a company with every incentive and every resource to
> scrape the web instead — was **paid for and crowdsourced**. Not one of the
> 44,711 hours is described as found footage. If the acquisition layer
> ([§13](#13-why-no-open-source-project-does-exactly-this)) were easy, or even
> merely tractable, this is the project that would have used it.

✅ **Every figure in this entry re-verified at the paper, 23 Sep 2026** — 44,711 h,
43,827 h crowdsourced, 829 h EgoDex, 55 h in-lab, 9,869 scenes, 6,015 tasks,
43,237 objects, Manus gloves with Vive Ultimate Tracker retargeted to **GR-1**
robot actions, 15×/96×/2,000×. **All present as stated.** And both of this
entry's *what-it-does-not-say* claims verified exactly: the string **"filter"
appears zero times** in the body, and **"licen" appears zero times** — the
CC BY 4.0 on the listing covers the manuscript. *(Two artefacts of the check
worth keeping: the paper's own numbers turned out to need the reading below, and
the 96× skills figure is **not reproducible from Table 1** against either
baseline the paper names — 6,015 against DROID's 86 or AgiBot-World's 87 is ~70×.
Recorded as unreproduced rather than wrong.)*

🔴 **But the headline diversity claim is computed on a scene count the same paper
replaces one page later with a number 115× smaller.** Table 1 lists DreamDojo-HV
at **1,135k trajectories and 1,135k scenes** — *identical*, i.e. **every
trajectory counted as its own scene.** The prose says *"more than **9,869 unique
scenes**."* The caption's **"2,000× more scenes than the previously largest
dataset"** only works with the first: **1,135,000 ÷ DROID's 564 = 2,013×**. Using
the paper's own *unique* count gives **9,869 ÷ 564 = 17.5×.**

> **Both numbers are in the paper and it never reconciles them.** *No error is
> alleged* — "scene" plausibly means the recording context for the table and a
> deduplicated location in the prose. **The point is that the 2,000× is the
> per-clip count and the 9,869 is the deduplicated one, and the paper prints the
> large one in the comparison and the small one in the description.** That is
> exactly the objection this document endorses against
> [Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability):
> *a count of hours, frames or streams is a vanity metric unless you say what
> each unit contains.* **Found here, in the paper this document calls its
> strongest evidence for §13** — which is where the objection is worth the most,
> because it costs something to make it.

⚠️ **And the 6,015 tasks carry a dagger this entry had not reproduced: *"†
Estimated by GPT based on the global language annotations."*** The skill count —
which feeds the 96× claim **and** the double-count inference below — is
**LLM-estimated, not enumerated**. That is not a reason to discard it; it is a
reason to label it. *It also strengthens the inference it feeds:* two papers
independently reporting **the same GPT-estimated 6,015** is less likely to be
coincidence than two papers reporting the same counted integer.

📌 **One more row worth lifting out of Table 1**, because this document is
collecting them: DreamDojo cites **DROID at 350 hours, 76k trajectories, 86
skills, 564 scenes** — the **86** being the *project page's* figure, where
[DROID's own paper says 84](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it).
**A third publication has now propagated the page's number rather than the
paper's**, which is how a figure becomes consensus without ever being re-derived.

🔴 **And a third thing it does not say: that [EgoScale](#egoscale) is reporting
the same corpus.** Both papers give **9,869 scenes, 6,015 tasks and 43,237
objects**, both include the same **829 hours of EgoDex**, both name the same
environment vocabulary — and neither cites the other. The full comparison is
[in EgoScale's entry](#egoscale). Taking the two at face value would double-count
one act of acquisition; nothing on either paper's surface warns you.

Two further observations, both about what the paper does *not* say:

- **No filtering or quality-control pipeline is described.** For a corpus of this
  size that is a striking omission, and it is the same gap this repo's cleaning
  and curation agents fill. Scale was reported; selection was not.
- 🔴 **Nothing is said about data licensing, redistribution, or dataset
  availability.** The code is Apache 2.0 and the checkpoints are on Hugging Face;
  the 43,827 crowdsourced hours have no stated terms. Note also that 829 of the
  hours are EgoDex, which is CC-BY-NC-ND — no-derivatives and non-commercial.
  Nothing here alleges non-compliance; as with the [WiLoR pattern](#11-the-licence-trap),
  the point is that the provenance chain has to be checked at the point of reuse,
  and here it currently cannot be, because the terms are unpublished.

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
- **Terms, checked at the artefacts.** Both are on Hugging Face, both **ungated**,
  both **Apache-2.0** on the card:
  [`YunzeLiu/OmniRetriever-Bench`](https://huggingface.co/datasets/YunzeLiu/OmniRetriever-Bench)
  (a single CSV, 61 downloads) and
  [`YunzeLiu/OmniRetriever-7B`](https://huggingface.co/YunzeLiu/OmniRetriever-7B)
  (a **LoRA adapter**, `library_name: peft`, `base_model: WAVE-7B`, 29
  downloads). Both cards carry the `arxiv:2605.26641` tag, which is what ties a
  personal namespace to the paper this document cites — worth stating, because
  the [adjacent-artefact trap](#11-the-licence-trap) runs in this direction too:
  a plausible name in a personal namespace is not by itself the paper's release.
  Two consequences follow from the model being an adapter rather than weights:
  the **base model's** terms govern alongside Apache-2.0, and what is published
  is the benchmark and the delta, **not the training corpus** — the 12-direction
  AVT data behind the result is not part of either artefact.

### S-EMBER

**[arXiv 2607.02689](https://arxiv.org/abs/2607.02689)** (FAIR, Meta) — the first
benchmark for **streaming** egocentric memory retrieval: **3,141 videos totalling
388 hours** of organic activity captured on **Ray-Ban Meta smart glasses**, with
**9,448 QA pairs**, each requiring manual visual proof through precise temporal
localisation.

The distinction it draws is the one that matters for an indexed corpus: standard
video retrieval searches pre-segmented clips, whereas streaming memory retrieval
must find the relevant moment in a continuous feed **without knowing the temporal
boundaries in advance**.

🔴 **Three corrections, and the first is this document's own and the largest of
them.** For sixty-two sweeps this entry read *"15 hours of first-person video"*
and concluded *"the 15-hour benchmark is small, but the framing is the useful
part."* **The paper says 388 hours, at both v1 and v2** — so the number cannot
have come from the source at any version, which is the part worth admitting: the
stated method of this document is that every entry was read at the source, and
this one was not. 388 hours is not small. It is larger than
[EPIC-KITCHENS-100](#epic-kitchens-100)'s 100, and larger than
[Ego-Exo4D](#ego-exo4d)'s 221.26 egocentric hours. The dismissal was
load-bearing and it was wrong.

The other two are smaller and in the same paragraph. **GPT-4o is not a baseline
here** — it appears once, text-only, given the question and temporal anchor
metadata with *all visual input withheld*, as a deliberate "vision-tax"
performance floor. And the Gemini evaluated is **Gemini 3.1 Pro**, not Gemini 3.
The actual model panel is InternVL3.5-38B, Qwen3VL-32B, GPT-5.4,
Llava-OneVision-7B and Gemini 3.1 Pro.

**What the models actually fail at** is worth carrying, because it is a different
claim at v2 than at v1. v1 reported a *localisation paradox*: temporal grounding
precision does not improve with parameter count, resolution or frame density. v2
reframes the headline as a **grounded recall gap** — models answer and localise
with moderate competence *in isolation* yet succeed at both on the same query at
**less than half the human rate**. Same corpus, same numbers, a reframed finding;
the document cites it bare, so it inherits v2.

> **A figure to keep.** Even Gemini 3.1 Pro decays from **50% accuracy for
> immediate recall to 29% for events more than eight minutes prior**. Recall
> quality is a function of temporal distance, not just of model size.

**Terms, checked at the artefacts — and this is a seventh live instance of the
[adjacent-artefact trap](#11-the-licence-trap).** The arXiv HTML is stamped
**CC BY 4.0**; the dataset is not. The code at
[facebookresearch/S-EMBER](https://github.com/facebookresearch/S-EMBER) is
**MIT** (explicitly inherited: *"For the main pipeline structure-related code, we
maintain the original license provided with lm-evaluation-harness"*), while its
README states that *"the majority of S-EMBER is licensed under CC BY-NC 4.0"*
with lmms-eval under separate terms. The data at
[`facebook/S-EMBER`](https://huggingface.co/datasets/facebook/S-EMBER) is
**CC BY-NC 4.0 and gated**, with a click-through requiring full name, affiliation
and agreement to non-commercial use; 4,468 downloads. Three artefacts, three
different licence records, none of them wrong — and a reader who took the number
off the paper would have recorded the one that does not apply. **This is the
third Meta FAIR dataset in this document whose permissive-looking stamp belongs
to the paper rather than the data**, after [Action100M](#action100m) and
[Ego-1K](#ego-1k).

> ⚠️ **And there is a second copy, ungated.**
> [`paper-review-only/S-EMBER`](https://huggingface.co/datasets/paper-review-only/S-EMBER)
> carries the same **CC BY-NC 4.0**, the same two JSONL configs, and **no gate at
> all** — 2,124 downloads against the official copy's 4,468. Its README says what
> it is: *"an anonymized mirror provided for peer review… It contains the
> complete benchmark. Author, institution, and provenance information has been
> intentionally omitted for double-blind review."* The paper is now public and
> attributed; the review mirror is still standing. Its counts — 9,429 questions
> over 3,134 videos — sit nineteen questions and seven videos below the published
> 9,448 / 3,141, which is itself the evidence that it is a **snapshot, not the
> release**.
>
> Record it as a fact, not a shortcut. **The licence is identical on both copies,
> so the ungated one grants nothing extra**: non-commercial either way, and the
> gate exists to record *who took it*, not to change what they may do. Taking the
> mirror to dodge a form means training on a snapshot that is already behind the
> release, under terms that did not move. See
> [§11](#11-the-licence-trap) for why this is an *access* fact and not a licence
> one.

> **Bearing here.** This is the failure mode our clipping stage exists to prevent.
> A pipeline that indexes whole videos and hopes retrieval will find the moment is
> attempting S-EMBER's hard problem at query time; a pipeline that has already cut
> semantically coherent clips and written per-span annotations has converted it
> into ordinary retrieval. At 388 hours on shipping consumer glasses, it is also
> the closest thing in this document to a preview of what wearable footage will
> look like at volume: **consent-constrained rather than designed**, in the
> paper's own words, with everyday routines dominating the distribution — the
> same skew a web-sourced corpus inherits, arriving here from the opposite
> direction.

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

🔴 **And a limit this document never checked, because it never had a way to:
the package has not shipped a release in thirty-one months.** PyPI gives
`video2dataset` **four releases in its whole history** — 1.0.0 (Nov 2022),
1.1.0 (Mar 2023), 1.2.0 (Jul 2023), **1.3.0 on 8 February 2024** — and nothing
since. This entry calls it *"the de-facto standard, and still the right answer
for bulk fetch"*, and [§14](#14-build-vs-reuse-per-stage)'s table says **Reuse**, with no
word about whether it is maintained.

> 🔴 **The contrast that makes it operational rather than cosmetic.** This tool's
> entire reach — *"anything yt-dlp supports — 1000+ sites"* — is inherited from
> **`yt-dlp`, which has shipped 639 releases and was last updated on 16 September
> 2026**, eight days before this reading. Site extractors break continuously;
> that is why yt-dlp ships weekly. **A wrapper pinned to a February-2024
> understanding of that surface is not a stable dependency, it is a stale one**,
> and the 74 open issues recorded above sit against a codebase that has not cut a
> release since. *The recommendation stands — there is still nothing better for
> bulk fetch — but it now reads: **reuse it, expect to patch it, and pin yt-dlp
> yourself.*** 🟢 The rest of the lineage is alive, which is what makes this
> specific: `img2dataset` last shipped **Aug 2025** (89 releases),
> `webdataset` **Jun 2025** (79), and NVIDIA's `nemo-curator` **Jul 2026** (23).

⚠️ **The reason this went unnoticed for ninety-three sweeps is worth recording,
because it is the third instance of the same shape.** The proxy this survey runs
behind **403s `github.com`**, so commits, releases and activity have been
invisible throughout — and the document filled the gap with a **star count read
once**, which it already flags as its weakest number. **PyPI was never queried.**
After [ModelScope](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet)
and the [`arxiv:`-tag Hub query](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five),
**this is the third time the fix has been *ask a different index*** — and the
first where the missing index bears on a **recommendation** rather than a fact.
*PyPI is now part of the staleness pass for every tool this document tells a
reader to reuse.*

### LAION-BVD — it shipped, and this document said it hadn't

**[LAION-AI/BVD](https://github.com/LAION-AI/BVD)** ·
[`laion/BVD-URLs`](https://huggingface.co/datasets/laion/BVD-URLs) — **1.3 billion
video URLs mined from CommonCrawl**, of which **80 M were downloaded (~10 M
hours)**, yielding **55 M scene-level clips with captions and timestamps**,
**300 M keyframes** and **10 M audio clips**, after content-aware scene detection
with synthetic VLM-generated video and audio captions.

🔴 **Two corrections, and the first is the largest miss in this document's §7.**
This entry said *"the paper, project page and download links are marked **coming
soon** — it documents a work in progress… **not a resource a commercial
collection effort can currently build on**."* Checked at the artefacts on 23 Sep
2026, **it has been released since 3 May 2026** — nearly five months — and is
**actively maintained** (`BVD-V-55M` was modified on **20 September**). Nine
artefacts exist, and they are split cleanly in two:

| Artefact | Licence | Access | Scale | Downloads |
|---|---|---|---|---|
| **`laion/BVD-URLs`** | 🟢 **CC BY 4.0** | **ungated** | **1.3 B URLs** | 6,156 |
| `laion/BVD-V-55M-URLs` | 🟢 **CC BY 4.0** | **ungated** | 55 M clips | **18,731** |
| `laion/BVD-A-10M-URLs` | 🟢 **CC BY 4.0** | **ungated** | 10 M audio | 9,056 |
| `laion/BVD-A-1.7M-URLs` | 🟢 **CC BY 4.0** | **ungated** | 1.7 M audio | 2,604 |
| `laion/BVD-V-55M` *(payload)* | 🔴 **none** | **gated: manual** | 55 M clips | 1,562 |
| `laion/BVD-I-300M` *(payload)* | 🔴 **none** | **gated: manual** | 300 M keyframes | 695 |
| `laion/BVD-A-10M`, `BVD-A-1.7M` *(payloads)* | 🔴 **none** | **gated: manual** | — | 54, 72 |
| `laion/BVD-RAW-Index` | — | index only | the ~80 M downloaded videos | *(media by request)* |

🔴 **So the licence claim was wrong in one direction and unsupported in the
other.** *"Research purposes only, not for commercial use"* is **false for the
URL lists** — **CC BY 4.0 permits commercial use** — and **unstated for the
payloads**, whose cards carry **no `license:` field at all**. What the card
actually says is the access rule, not a licence: *"BVD-RAW itself — the raw pool
of 80 M videos totalling 10 M hours — is not distributed through Hugging Face.
The gated subsets and BVD-RAW are available to **academic and non-commercial
researchers** through a single central **access request form**."* **A Google
Form, and no terms on the artefacts it gates.** *The restriction is real; it
simply is not where this document said it was, and it does not reach the part
that matters most.*

🟢 **And the part that matters most is the posture: this is the fourth
URLs-only-under-a-named-licence release in this survey, and by a wide margin the
largest.** After [HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago)
(103 M clips, Open Use of Data Agreement, 2022),
[OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
(per-source attribution) and [EgoVid-5M](#egovid-5m) (three CSVs and poses, no
video) — **LAION-BVD ships 1.3 billion URLs under CC BY 4.0 with no gate.** The
schema is three columns: **`url`, `platform`** (YouTube, Vimeo, Dailymotion) and
**`crawl` — the CommonCrawl snapshot each URL came from.** *That last column is
per-URL provenance*, which is a real piece of what this repo's manifest is for,
shipped by someone else, permissively, at a billion rows.

> 🔴 **Read the download split, because it is the argument.** The four permissive
> URL lists have **36,547 downloads between them**; the four gated payloads have
> **2,383**. **Fifteen times more people take the pointers than the bytes** —
> from the same publisher, on the same day, for the same corpus. That is the
> strongest evidence in this document that **URLs-only-under-a-licence is not a
> compromise release, it is the one people want**, and it is the posture §11 has
> been arguing for on principle.

⚠️ **What this does to [§13](#13-why-no-open-source-project-does-exactly-this),
stated plainly and before anyone else has to.** §7 has said *"the crawl already
happened, twice."* **It happened three times, and the third is a billion URLs you
may use commercially.** But a pool is not the machine: BVD has **no viewpoint
labels, no ego/exo split, no hand-visibility gate, no per-clip rights resolution
beyond the snapshot it came from, and no notion of collecting against a stated
requirement.** Its 10 M hours are *"video"*, not *egocentric* video, and nothing
in the release says which fraction is first-person. **§13 narrows again and
survives** — the same narrowing [HumanNet](#humannet) and HD-VILA-100M forced —
but the honest version is now: *the crawl stage is solved, published and
permissively licensed at web scale; what is missing is everything between a URL
and an accepted clip.* **A survey that had this entry marked "coming soon" for
months was not in a position to say that, which is the real cost of the error.**

**The authors also flag bias and uneven representation across languages, regions
and topics** — which remains true and is more useful now that the thing exists.

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

### HowTo100M and HD-VILA-100M — the crawl already happened, twice, years ago

The four entries above are *tools*. These two are what the crawl produced, and
this document has been citing both in passing — HowTo100M as a
[RynnVLA-001 upstream](#rynnvla-001--filter-dont-convert), HD-VILA-100M as
[Panda-70M's source with a *"⚠️ check upstream"*](#who-feeds-whom--the-derivation-map)
against it — without ever reading either. Read this sweep, they change two of
this document's claims.

| | [HowTo100M](https://www.di.ens.fr/willow/research/howto100m/) (ICCV 2019) | [HD-VILA-100M](https://arxiv.org/abs/2111.10337) (CVPR 2022) |
|---|---|---|
| Scale | **136 M clips** from **1.2 M YouTube videos**, *"15 years of video"*, 23 k activities | **103 M clips** from **3.3 M videos**, **371.5 K hours** |
| Quality | mixed; instructional narration | 🟢 **all 720p**, English subtitles required |
| Selection | narrated instructional video, 23 k wikiHow-style tasks | *"popular YouTube channels"* plus YouTube-8M and YT-Temporal-180M, filtered to 720p + subtitles, across *"15 popular categories"* |
| Redistribution | features and metadata, **not raw video** | 🟢 *"we plan to only release the **URLs** of the videos and the code for preparing data"* |
| **Licence** | 🔴 **none stated** on the project page | 🟢 **Open Use of Data Agreement (O-UDA)** |
| Acquisition code | 🔴 **not released** — see below | partially: *"code for preparing data"* |

🔴 **First: HowTo100M is the cleanest demonstration of §13's shape, and it is
from 2019.** Its repository states exactly what it provides: *"our training
procedure on HowTo100M for learning a joint text-video embedding"*, evaluation
code on MSR-VTT / YouCook2 / LSMDC, *"a pretrain model"*, and *"feature
extraction from raw videos script we used"*. Four things — and **none of them is
how the 1.2 million videos were found and chosen.** The model, the features and
the benchmark are all public; the acquisition layer is not. **So the pattern
this document identified in 2026 papers is not a 2026 phenomenon. It is the
field's default, and it is at least seven years old.** That is a stronger
statement of §13 than the one the section currently makes, and it comes from a
paper the document was already citing.

🔴 **Second, and this one costs us a claim: OpenEgo is not the only project that
handles redistribution properly, and it is not the first.** The
[derivation map](#who-feeds-whom--the-derivation-map) calls OpenEgo *"the only
row that solves it"*. But **HD-VILA-100M released URLs rather than video, under a
named, published data licence — the Open Use of Data Agreement — in 2022**, at
103 M clips and 371.5 K hours, roughly **335×** OpenEgo's hours. Same principle:
do not redistribute other people's video; ship the pointers and the tooling.
This document had it in a table for dozens of sweeps with *"⚠️ check upstream"*
next to it, which was precisely an instruction to go and read the thing, and the
answer to that ⚠️ has been sitting in the abstract the whole time.

> **What survives, stated carefully.** OpenEgo keeps a narrower distinction that
> HD-VILA does not: **per-source licence text with attribution strings**, and
> **explicit author permission** for its CC-BY-NC-ND component. HD-VILA applies
> one blanket licence of its own to a pool assembled from three million
> third-party uploads; that is a cleaner *release* posture than most, and a
> weaker *provenance* posture than OpenEgo's. So the corrected claim is:
> **URLs-only redistribution under a stated licence is well-established prior
> art at 100 M-clip scale; per-source provenance is the part almost nobody
> does.** The praise for OpenEgo stands on the second half only.
>
> **And what this does not change is §13.** Neither corpus is egocentric, and
> neither filters on viewpoint — HD-VILA's axis of selection is *category and
> resolution*, HowTo100M's is *narrated instruction*. The 15 categories are
> YouTube's own. So the acquisition layer these two built is real, large,
> partially published and **viewpoint-blind**, which is the same gap
> [§13](#13-why-no-open-source-project-does-exactly-this) names — reached now
> from prior art rather than from current papers.
>
> **For this repo**, the practical read is that O-UDA-plus-URLs is a
> **precedent to cite, not a thing to invent**: a large, well-known corpus
> established years ago that shipping pointers under a stated licence is a
> workable posture. §14 already puts the redistribution rule on the reuse side;
> this is the older and larger evidence for that call.

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

🔴 **And this document has been under-reading it.** RynnVLA-001 is cited above as
a source of a filtering *rule*. It is also, per its abstract, an
Image-to-Video model trained *"on 12M ego-centric manipulation videos to predict
future frames conditioned on an initial frame and a language instruction"* —
a pretraining corpus of a size that puts it alongside the largest entries here.

**Where those 12 M videos came from — resolved, and it is a fourth naming
trap.** A previous sweep could not confirm the source and recorded it as
unverified rather than repeat secondary coverage calling it "web-sourced". Read
in the paper's HTML this sweep, the phrase is real: *"we design a dedicated data
curation pipeline to filter out 12M ego-centric manipulation videos from
**existing web sources**."* But §4 says what those sources are, by citation:
**EgoVid-5M, Ego4D, HowTo100M, EPIC-KITCHENS (2018, 2021, 2022) and
Something-Something (2017, 2018)**.

**So "web sources" here means *existing public research datasets*, not footage
crawled off the internet.** Same shape as *in-the-wild* meaning "outside the
lab": a phrase that reads, to anyone asking [§13](#13-why-no-open-source-project-does-exactly-this)'s
question, as the opposite of what it denotes. Had this document taken the
secondary summary at face value it would have added a false counterexample to
that section — the third time the same trap has been avoided only by going to
the source.

🔴 **And now that the upstream is nameable, the licensing reads worse, not
better.** Those citations include **[Ego4D](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads)** (signed agreement, terms
not published), **[EPIC-KITCHENS](#epic-kitchens-100)** (CC BY-NC 4.0,
explicitly non-commercial) and **[EgoVid-5M](#egovid-5m)** (inherits Ego4D's
terms). The paper states **no licence for the assembled 12 M-video dataset**,
and the dataset is not released. Meanwhile the code and **two 7B checkpoints are
Apache 2.0** and publicly downloadable.

> **That makes this a sharper exhibit for [§11](#11-the-licence-trap) than
> [ACE-Ego-0](#ace-ego-0), not a weaker one.** Both train on restrictive
> corpora. But ACE-Ego-0's five sources are stated where a reader will find
> them, whereas here the composition is recoverable only by resolving a
> parenthetical citation list in §4 — and nothing on the model card, the
> repository, or the abstract carries it. **Permissive weights, an unpublished
> assembled-dataset licence, and an upstream that includes a non-commercial
> corpus and one behind an unpublished agreement.** Nothing improper is alleged;
> research pretraining and commercial deployment are different questions. The
> structural point is that *"Apache 2.0"* on a checkpoint answers a question
> about the weights and nothing at all about what went into them — which is why
> rights belong where the footage *enters*, not reconstructed later from what
> comes out.
>
> **The corrected pipeline, for the record.** Three stages: **keypoint
> detection** (pose estimation for human keypoints), **ego-centric filtering**
> (*"No facial keypoints"*, *"Presence of hand keypoints"*), and **text
> description annotation** (Qwen2-VL-7B). That is the rule quoted above, in its
> own paper's words.

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

**Which VLM it runs**, resolved: the repository names no model, but requires an
`auth.env` carrying either **Azure OpenAI** credentials (deployment name,
endpoint, key) or an **OpenAI** API key — so it is OpenAI-family, with the actual
model chosen by whoever deploys it. The sample invocation is
`python example.py --credentials auth.env --video sample.mp4 --grid 3 --action
"Grasping the can"`, and it ships Breakfast and THUMOS14 samples. MIT, 26 stars.

> Two consequences worth noting: there is **no pinned model to reproduce
> against**, so published numbers are only as stable as the deployment behind
> them; and cost per clip is set by your own deployment rather than by the
> method. For a floor-setting baseline that is acceptable — but it means "beat
> the learning-free baseline" needs the baseline's model named before the claim
> means anything.

⚠️ **The authors state plainly that it does not surpass current model-based
approaches.** That is exactly what makes it useful: zero training cost and no
labelled data, so it is the honest floor any trained localiser in this pipeline
must clear before it earns its complexity.

## 11. The licence trap

The finding with the sharpest practical edge, and the reason a "just use the open
pipeline" plan can quietly become unshippable.

**The field fails at rights in three distinct ways, and they need different
responses.** *Too restrictive to use* — EgoDex is CC-BY-NC-ND; HOI4D and
EPIC-KITCHENS-100 are CC BY-NC 4.0; AgiBotWorld-Beta is non-commercial *and*
share-alike. *Too unstated to know* — Open X-Embodiment pools 60 datasets from
34 labs and states no overall licence;
DreamDojo's crowdsourced hours have no published terms; Ego4D and Ego-Exo4D sit
behind agreements whose text is not public. *Not released at all* — EgoScale,
the largest action-labelled ego corpus here at 20,854 h, is "code coming soon"
with no licence. The first is a decision, the second is a question you must ask
before building, and the third is a plan you cannot make. **Three further shapes
turned up over the sweeps** — *partially released* and *stated then withdrawn*
below, and *bespoke* in
[§1](#ego-oscar--capture-at-200-and-a-fifth-licence-shape). Six shapes is not a
taxonomy anyone designed; it is what re-reading the same sources every eight
hours produces.

**EgoInfinity's own code is MIT. Its dependencies are not.** The repository says
so directly: *commercial use of the repo as a whole is restricted by the WiLoR
(CC-BY-NC-ND) and MANO (non-commercial) terms.*

### WiLoR — the chokepoint, read at source

This document has invoked WiLoR nine times as one of the two chokepoints on the
[derivation map](#who-feeds-whom--the-derivation-map) without ever giving it an
entry of its own. Fixing that, at
**[rolpotamias/WiLoR](https://github.com/rolpotamias/WiLoR)**:

**Mechanism.** End-to-end 3D hand *localisation and reconstruction* from
unconstrained images — a detector stage plus a reconstruction module estimating
pose and shape through the **MANO** parametric hand model. Recent releases add
half-precision inference and depth pruning for *"up to 1.6× faster inference
with minimal performance degradation"*, costing roughly **0.05 mm MPJPE**. It
reports state-of-the-art results on **FreiHAND** and **HO-3D**, and introduces
its own **WHIM** training set. **661 stars.**

🔴 **Licence, quoted: *"WiLoR models fall under the CC-BY-NC--ND License."*** And
the repo notes its dependence on Ultralytics and MANO, each with terms of their
own — so the stack under it is **AGPL-3.0** and **non-commercial research only**
respectively.

> **Why this is the load-bearing one.** WiLoR is not a component someone chose
> casually; it is state-of-the-art at the exact task — *hands, in the wild* —
> that every pipeline in this document needs and that this repo's hands gate is
> built around. That is precisely what makes it dangerous as a dependency: the
> best available tool for the field's central annotation step is **non-commercial
> and no-derivatives**, and it sits inside [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject),
> [Ego2Robot](#ego2robot) and [MobileEgo Anywhere](#mobileego-anywhere)'s STERA.
> A team that adopts the obvious best option inherits the whole stack's terms
> without ever making a licensing decision.

🔴 **And this document has been calling the wrong thing the chokepoint.** Earlier
sweeps said "replacing WiLoR is tractable engineering" without checking what
replacing it would buy. Checked this sweep, the answer is: **less than it
sounds, because the binding constraint is one layer down.**

| Candidate | Code licence | Still needs MANO? | Status |
|---|---|---|---|
| [WiLoR](https://github.com/rolpotamias/WiLoR) | **CC-BY-NC-ND** (models) | yes | current default |
| [HaMeR](https://github.com/geopavlakos/hamer) | **MIT**, 1.1 k stars | **yes** — *"you also need to download the MANO model… register to get access"* | drop-in-ish |
| [HandOS](https://arxiv.org/html/2412.01537v2) | none stated | **partly** — avoids MANO *parameters* for its representation, but 3D joints still come from *"the joint regressor defined by MANO"* | no code released |
| [NIMBLE](https://github.com/reyuwei/NIMBLE_model) *(a hand **model**, not a reconstructor)* | **MIT** on the repo | ⚠️ **unresolved** — built in *"MANO topology"* and *"reuses part of the great code from manopth"* | model files via Google Drive, no registration stated |

**So swapping WiLoR for HaMeR removes a CC-BY-NC-ND *model* licence and leaves
the non-commercial, registration-gated *hand model* exactly where it was.**
HandOS is the only entry that even tries to leave MANO behind — a unified
keypoint representation, *"instead of MANO parameters"*, reaching 5.0 PA-MPJPE on
FreiHAND and 8.4 on HO3Dv3 — and it still reaches for MANO's joint regressor to
get 3D joints from vertices, and has published neither code nor terms.

> **The correction, stated plainly.** The two chokepoints are not "WiLoR and
> EgoDex". They are **MANO and EgoDex** — a hand *model* and a hand *corpus*,
> both non-commercial, sitting under essentially every hand-annotation and
> hand-learning path in this document. WiLoR is the most visible place MANO
> surfaces, not the constraint itself. That matters for planning: a swap at the
> WiLoR layer is an afternoon and buys a cleaner code licence; the MANO layer is
> the one that decides whether any of it is shippable.

🟡 **And having said "nobody has solved this", the next sweep went looking, which
is the only honest way to hold a claim like that.** The closest candidate is
**[NIMBLE](https://github.com/reyuwei/NIMBLE_model)** — a parametric hand model
with *bones, muscles and skin* rather than skin alone, **MIT on the repo**, model
files served from Google Drive with no registration stated. That is a materially
better licensing position than MANO's, and if it cleared MANO entirely it would
end this problem.

**It does not clearly clear it.** The README describes *"corresponding skin
vertices in MANO topology"*, acknowledges MANO, and states it *"reuses part of
the great code from manopth."* Whether building in another model's **topology**
inherits that model's terms is a genuine legal question this document is not
equipped to answer, and it is exactly the sort of question that has to be
answered *before* a corpus ships rather than after. So the honest status is
**unresolved and worth resolving** — the strongest lead available, not a
solution, and considerably more promising than "nobody has solved this" implied.

> ⚠️ **One more instance of the trap this section is about.** Secondary coverage
> describes NIMBLE as **CC BY 4.0**; the repository says **MIT**. The CC licence
> is the *paper's*. Third time in this document that a licence on an adjacent
> artefact has been reported as the terms of the thing itself, after
> [EgoScale](#egoscale) and [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild).

**EgoInfinity's dependency stack, in full**, as the clearest worked example of
what inheriting that decision costs:

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

**It is not an isolated case, and WiLoR in particular keeps reappearing.** It is
the hand reconstructor in [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject),
in [Ego2Robot](#ego2robot), and in [MobileEgo Anywhere](#mobileego-anywhere)'s
STERA pipeline — three otherwise unrelated projects, two of which publish their
outputs under permissive terms. Whether a CC-BY-NC-ND *model* constrains a
dataset *derived* using it is genuinely unsettled, and nothing here asserts that
any of these projects is out of compliance. The practical point is narrower and
holds regardless: **one non-commercial model has quietly become load-bearing
across the field's hand-annotation stack**, so "what reconstructed these hands,
and under what terms" is a question to ask at the point of reuse, not a footnote.

Reading the licences across this document produces the wider pattern:

| Asset | Licence | Commercial use |
|---|---|---|
| Egocentric-10K / -100K | Apache 2.0 | ✅ (see §12 caveats) |
| Egocentric-1M | Apache 2.0 *(reported only; absent from the publisher's complete API index, **six attempts** — the sixth, 20 Sep 2026, a fresh recency scan of every "egocentric" dataset by last-modified date)* | ⚠️ confirm the release exists before relying on it — and note that an **empty third-party repo of the same name** carries an `mit` tag: `easpeeder/Egocentric-1M` holds **exactly two files**, `.gitattributes` and a README whose entire content is the three-line YAML `license: mit`, with 8 downloads. **Terms without data — the exact inverse of [FastUMI-100K](#the-umi-family--capture-without-a-robot-and-the-blind-spot-this-survey-had)**, which is 265,883 downloads of data without terms |
| **Action100M** | 🔴 **`fair-noncommercial-research-license`** on `facebook/action100m-preview` — Meta FAIR's own terms. *(This document recorded **CC BY 4.0**, which is the **arXiv listing's** licence.)* Note also it is a **preview** subset | ❌ **non-commercial** — the document previously told readers the opposite |
| **Open-AoE** | 🔴 **`license: other`, `license_name: open-aoe-dataset-license`** on `inclusionAI/OpenAoE-2000h` — **bespoke**, with a staged *"Release Roadmap"*. *(Recorded here as **CC BY 4.0**, which is the **arXiv listing's**.)* **564,333 downloads a month** | ⚠️ **unclassifiable** — a one-publisher licence, read it in full |
| **EgoLive** | 🔴 **no dataset licence stated anywhere** — the only licence string in the paper is the **arXiv listing's CC BY 4.0**, and distribution runs through a commercial data marketplace (`robotdata-market.jdcloud.com`) whose terms are not the paper's | ⚠️ **unresolved** — previously recorded here as CC BY 4.0 |
| **MobileEgo Anywhere** — `fpvlabs/stera-10m` | **`license: other`**, gated, **401 unauthenticated** — the same bespoke posture as its sibling Stereo-550 *(this document previously recorded **CC BY 4.0**, which is the **arXiv paper's** licence)* | ⚠️ **unclassifiable** — unreadable before agreeing |
| NeMo Curator | Apache 2.0 | ✅ |
| **Ropedia Xperience-10M** | **"other" — manual review **plus** an off-platform DocuSign signature (requests stay *pending* until signed), research only. 🔴 An **ungated `xperience-10m-sample` under CC BY-NC 4.0** exists beside it, unmentioned here for dozens of sweeps; three further `ropedia-ai` artefacts carry **no licence field** | ❌ non-commercial, and **partially released** |
| EgoKit | toolkit only, no dataset | n/a — paper carries the arXiv licence |
| VLM-Video-Action-Localization | MIT | ✅ |
| **InternVid** | **CC BY-NC-SA 4.0**, gated *(resolved on re-check; previously recorded as unstated)* | ❌ non-commercial **and** share-alike |
| cosmos-curate (code) | Apache 2.0 | ✅ (models separate) |
| video2dataset | MIT | ✅ |
| Exo2Ego-V | Apache 2.0 | ✅ |
| **EgoDex** | **CC-BY-NC-ND** — 🔴 and **two ModelScope re-uploads carry `Apache License 2.0` instead**, at **814,750 combined downloads**, one of them naming Apple's EgoDex in its own card and describing a repack | ❌ non-commercial, no derivatives — **and the copy most people pull says otherwise** |
| **EPIC-KITCHENS-100** | **CC BY-NC 4.0** | ❌ (commercial terms by email to Bristol) |
| **HOI4D** | **CC BY-NC 4.0** | ❌ non-commercial |
| **ENIGMA-360** | 🔴 **no dataset licence stated** — only the **arXiv listing's CC BY 4.0**, and its project page has now failed **eight**, the last six with an identical 403 | ⚠️ **unresolved** — previously recorded here as CC BY 4.0 |
| **SABER** | **CC BY-NC 4.0 — on a 10 K-sample subset only, and that subset is itself `gated: auto` behind four fields (401 unauthenticated, 19 downloads). The rest is *"available under NDA"* per the vendor, and the access URL the paper prints redirects to the vendor's homepage** | ❌ non-commercial, partial, **and both halves gated** |
| **Ego-OSCAR** — hardware + software | **Apache 2.0** (verified at the repo's `LICENSE`) | ✅ |
| **Ego-OSCAR** — Stereo-550 dataset | **`fpvlabs-license`**, bespoke: "research use", but "commercial usage allowed"; gated, **and the licence text itself is behind the gate** | ⚠️ **unclassifiable** — the one thing a custom licence needs is a reading, and it cannot be read before agreeing |
| **EgoCS-400K** | 🔴 **no dataset licence stated** — only the **arXiv listing's CC BY 4.0**; no repository, no card, no download location named in the paper | ⚠️ **unresolved** — previously recorded here as CC BY 4.0 (rendered gameplay, not real-world footage) |
| **World In Your Hands** | **CC BY-NC 4.0**, at the artefact — 🟢 **resolved this sweep.** The paper names no instrument, but Appendix E states the terms (*research only; redistribution and commercial use restricted*) and defers the licence to *"the licence accompanying the dataset"*; that artefact is [`tars-robotics/WIYH`](https://huggingface.co/datasets/tars-robotics/WIYH), tied to the paper by the publisher's own API emitting the card's bespoke `worldcode_…_vlta_reorg_sample` identifier format | ⚠️ **still no `arxiv:` tag**, and the **`Full` tier is *"Coming soon"*** behind account registration — the public tier is `Mini` |
| **EgoTactile** | **CC BY-NC 4.0**, ungated (plus `EgoTactile-OXT` on the same terms) | ❌ non-commercial — but stated, which neither EgoTac nor H-Tac manages |
| **EgoTac** | **nothing released** — no repo, no card, no project page, and no *"we release"* anywhere in the body | 🔴 reclassified from *terms unstated* to **not released**: there is nothing to attach terms to |
| 🔴 **H-Tac / TTP** (BeingBeyond) | **partially released** — the printed project page `beingbeyond.github.io/TTP/` still returns **404**, but `BeingBeyond/H-Tac_Sample` on Hugging Face holds **98 episodes / 35,982 frames / 98 videos** under a **MIT** `LICENSE`, ungated, 234 downloads | 🔴 **corrected again**: this table said *not released* for several sweeps. The release was in a namespace neither the paper nor the project URL points at. **HOI-Tac — the 106 h over eleven other datasets — is still not in it** |
| ⚠️ **Open X-Embodiment, third-party mirror** | `jxu124/OpenX-Embodiment` self-describes as *"an unofficial Dataset Repo"* and carries **`license: cc-by-4.0`** over a 55-in-1 aggregation whose official position states **no overall licence**. **between 12,000 and 20,235 monthly pulls across five readings** — most recently 19,447 | 🔴 **do not rely on it** — an uploader's licence field is an assertion, not a finding, and this one is being relied on more each month |
| **LAION-BVD** | 🟢 **CC BY 4.0, ungated, on the four URL-list artefacts** (1.3 B URLs among them) · 🔴 **no licence field at all** on the four gated payloads, whose card says only that they go to *"academic and non-commercial researchers"* via a Google Form | ✅ **for the pointers**, ⚠️ unstated for the bytes |
| **EgoInfinity (as a whole)** | MIT code, encumbered deps | ❌ until deps are swapped |
| **Ego4D / Ego-Exo4D** | **signed agreement, terms not public** | ⚠️ unknowable until you sign — do not assume |
| EgoVerse | no dataset licence stated (**re-checked at v2, 7 Jul 2026; still none** — zero occurrences of "CC BY" or "Apache" in the body, and the figures 1,362 h / 80 k episodes / 1,965 tasks / 240 scenes / 2,087 demonstrators all hold — only the arXiv listing's, and access runs through the authors' EgoDB/S3 sync) | ⚠️ ask before use |
| Panda-70M (data) | inherits **[HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago)**, whose stated terms are the **Open Use of Data Agreement (O-UDA)** | ✅ resolved — a ⚠️ this document carried for dozens of sweeps, answered by reading the upstream abstract |
| EgoVid-5M | **Apache 2.0 on the release, which is annotations only** — three CSVs and `poses.zip`, **no video**; the footage is fetched from Ego4D under Ego4D's terms | ✅ resolved, and correctly scoped — the **second** "⚠️ check upstream" answered in two sweeps, both of which resolved *better* than the marker implied |

| DreamDojo code | Apache 2.0 | ✅ (the 43,827 crowdsourced hours still have **no stated terms**) |
| 🟢 **DreamDojo weights** | **`license: other` / `nvidia-open-model-license`** on [`nvidia/DreamDojo`](https://huggingface.co/nvidia/DreamDojo), ungated, 143 downloads | ⚠️ **bespoke, and newly found** — a long-standing *unstated* field discharged at the artefact, not the paper. The weights now have terms; **the video behind them still does not** |
| [HoloAssist](#holoassist) | CDLA v2 | ✅ |
| [Ego-1K](#ego-1k) | CC BY 4.0 | ✅ with attribution (17.5 TB research / 88 TB raw on request) |
| [EgoScale](#egoscale) | none stated; code "coming soon" | ⚠️ not obtainable at time of writing |
| **AgiBotWorld-Beta** | **CC BY-NC-SA 4.0**, contact-gated | ❌ non-commercial **and** share-alike — the most restrictive terms here |
| DROID | open dataset; terms not stated on the project page (**re-checked; still silent** — the page says only that the dataset, training code and hardware guide are open-sourced) | ⚠️ unresolved |
| EgoExoLearn | **MIT throughout** — the repo `LICENSE` for the code, and `license: mit` on the author's own Hugging Face dataset card (ungated, 3,932 monthly downloads) | ✅ resolved — the third long-standing ⚠️ to come back permissive |
| **Being-H0.5 / UniHand_Preview** | **Apache-2.0 on the code**; the released dataset subset states **no licence**, ungated, 13,377 monthly downloads | 🔴 released and actively used, provenance undeterminable |
| **Being-H0.7** | **none stated at all** — the paper's only licence string is arXiv's, and the word *"release"* does not appear in the body | 🔴 same undocumented UniHand 2.0 mixture, a third time |
| **OpenMMEgo** (OME10M, OMEBench) | **MIT on a repository containing a README**; the data section reads *"We will release our code and data soon"* and neither dataset is findable | 🔴 **the title says "Open Weights and Data"** — weights shipped (13 public model repos), data not |
| **Open X-Embodiment** | **none stated; 60 pooled components, position unstated** | ⚠️ unknowable without tracing 60 upstream datasets |

🔴 **A systematic audit of this document's own permissive claims — seven checked,
six wrong.** Having caught itself recording
[MobileEgo Anywhere](#mobileego-anywhere)'s *paper* licence as its *dataset*
licence, the obvious question was whether the same error was repeated. It was —
**six times out of seven entries checked**, every one in the direction of *more
permissive than the source supports*:

| Entry | This document said | What the dataset artefact says |
|---|---|---|
| **Action100M** | CC BY 4.0, ✅ with attribution | 🔴 **`fair-noncommercial-research-license`** (Meta FAIR) on `facebook/action100m-preview` — **non-commercial**, and a *preview* subset |
| **Open-AoE** | CC BY 4.0, ✅ with attribution | 🔴 **`open-aoe-dataset-license`** (bespoke) on `inclusionAI/OpenAoE-2000h`, with a staged *"Release Roadmap"* |
| **EgoLive** | CC BY 4.0 | 🔴 **nothing** — distribution runs through a commercial marketplace |
| **ENIGMA-360** | CC BY 4.0 | 🔴 **nothing** — and its project page has now failed **eight**, the last six with an identical 403 |
| **EgoCS-400K** | CC BY 4.0 | 🔴 **nothing** — no repository, card or download location named |

**In all six the only licence string in the paper is the arXiv listing's own
`License: CC BY 4.0`**, which governs the *manuscript*. Three have no dataset
artefact stating terms at all; the three that do state something **less**
permissive — two of them non-commercial.

⚠️ **Two of the six are the same publisher's house licence, missed twice.**
**Action100M** and **Ego-1K** are both Meta FAIR, and both carry
**`fair-noncommercial-research-license`** on their cards. A publisher applying
one non-standard licence across its releases will be got wrong the same way every
time until someone reads a card — and the string `fair-…` appears in neither
paper.

✅ **The control row matters as much as the failures.** **HoloAssist** was
recorded as CDLA v2 and **is** CDLA v2, because its project page says so in a
sentence: *"We release the dataset under the CDLAv2 license, a permissive
license."* That is the whole difference. **Where a publisher states dataset terms
on a dataset surface, this document got it right; where it did not, it filled the
gap with the arXiv listing — six times out of six.**

> **The uncomfortable part is the direction.** This document's standing
> observation about the field is that circulating claims run *freer and larger*
> than sources support. **Its own licence errors run exactly the same way** — five
> entries, five overstatements of permissiveness, none in the other direction.
> That is not a coincidence of sampling: **`License: CC BY 4.0` is the most
> visible string on an arXiv HTML page**, it sits where a reader skimming for
> terms will find it, and it is *true* — of the paper. The failure is not
> credulity about a dubious source; it is **reading the right string off the
> wrong artefact, repeatedly, because that artefact is the one that loads
> first.**
>
> **Two things follow for the rest of this survey.** A permissive licence
> recorded against a dataset now requires a **dataset artefact** — a card, a
> repository `LICENSE`, a terms page — and an arXiv listing is explicitly *not*
> sufficient evidence. And the ✅ marks in the table below mean less than they
> did an hour ago, which is worth saying plainly rather than quietly reissuing
> them.

⚠️ **A note on this document's own ⚠️ markers, prompted by two of them falling in
consecutive sweeps.** Panda-70M's *"⚠️ check upstream"* resolved to **O-UDA**;
EgoVid-5M's resolved to **Apache 2.0 over an annotations-only release**. Both had
stood for dozens of sweeps, and **both resolved better than the marker implied**.
That is not luck, it is a bias: *"⚠️ check upstream"* costs one clause to write
and a real fetch to discharge, so unresolved markers accumulate, and a reader
scanning the table reads them as findings — as evidence the field is careless —
when they are only debts this document had not yet paid. **An unresolved field is
a statement about the survey, not about the source.** Every remaining ⚠️ below
should be read that way until it has a date and a fetch behind it.

Note what the bottom half of that table has in common: the field's **most-cited**
reference datasets are the ones you cannot use commercially, or cannot even read
the terms of without signing first. The permissive corner is occupied almost
entirely by 2026 releases and by tooling.

**And there is a fourth shape, distinct from the three this section opened
with.** Too restrictive, terms unstated, not released — and now *partially*
released, with the restrictive terms attached to the part you can have.
[SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
publishes a **10 K-sample subset under CC BY-NC 4.0** out of 44.8 K, and routes
the rest through the vendor's own page. The failure mode this creates is subtler
than a flat "no": a reader who checks the licence sees a real, quotable licence
on a real, downloadable artefact, and has to notice separately that it covers
under a quarter of what the paper reports. **Record the licence, the access
route, *and* the fraction — three fields, not one.**

🔴 **And "downloadable" was this document's word, not the artefact's.** Checked
at the artefact rather than the paper, `DreamVu/SABER-10K` is **`gated: auto`
behind four fields** and **401s unauthenticated**, so the paper's *"released
publicly"* means *released behind an access request*. The other half is *"available
under NDA"* per the vendor's own page, and the URL the paper prints for it
**redirects to the vendor's homepage** — HTTP 200, no dataset. So the fourth shape
is really **two gates of different strength plus a dead address that does not
announce itself as one**, and the three fields above should have been four:
licence, access route, fraction, **and whether the route resolves to the thing.**

**All four corners of the licence × access grid are occupied** — though the
permissive/open corner was **re-tenanted this sweep**: it used to be held by
EgoCS-400K on a CC BY 4.0 that turned out to be the paper's, and is now held by
two entries whose terms were read at their **dataset cards** (EgoVid-5M's Apache
2.0 and EgoExoLearn's MIT, both ungated). The grid survives on better evidence
than it had. That is the
cleanest way to see why one field cannot carry both. Every cell below was
verified at source:

| | **Access open** | **Access gated** |
|---|---|---|
| **Licence permissive** | [EgoVid-5M](#egovid-5m) — **Apache 2.0, ungated**, verified at its card; [EgoExoLearn](#egoexolearn) — **MIT, ungated**, verified at the author's card | [Egocentric-10K / -100K](#egocentric-10k) — Apache 2.0, but *"agree to share your contact information"* |
| **Licence restrictive** | **[EgoDex](#egodex)** — CC-BY-NC-ND, yet the zips come straight off Apple's CDN, **HTTP 200, no auth** | [InternVid](#internvid) CC BY-NC-SA + gate; [AgiBotWorld-Beta](#the-robot-native-denominator) CC BY-NC-SA + contact gate; [Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability) non-commercial + DocuSign |

The bottom-left cell is the one that catches people. **EgoDex is the most
restrictively licensed corpus in this document and among the easiest to
download** — 17.3 GB over plain HTTPS with nothing to sign. Ease of acquisition
carries no information at all about what you may then do, and a pipeline that
infers permission from a 200 response will be wrong exactly where it matters
most, since EgoDex is also the field's most-reused hand corpus
([derivation map](#who-feeds-whom--the-derivation-map)).

🔴 **A sixth shape, and the one this document did not see coming: stated, then
withdrawn.** The five shapes so far are all properties of a licence at rest — too
restrictive, unstated, unreleased, partly released, bespoke. This one is a
property of the *record*. EgoDex's arXiv **v1** and **v2** state the CC-BY-NC-ND
terms twice each and carry a "Dataset Access" appendix; **v3 (9 Mar 2026) states
no licence at all**, and that appendix has been replaced by "Training Details".
The terms did not change and are still in force — they survive in the GitHub and
CDN READMEs — but **the only version-pinned, immutable statement of them was
deleted**, and the two that remain are files that can be edited without leaving a
diff. Full working in [the EgoDex entry](#egodex).

The practical consequence is narrow and sharp. A rights field that records
*"CC-BY-NC-ND, per arXiv 2505.11709"* was accurate when written and now resolves
to a paper that says no such thing. **So a provenance record needs a fourth field
beside licence, access route and fraction: the artefact and revision the terms
were read at, with a date.** Not the work — the *document*. This document had
three of the four and still got it wrong, which is the argument for the fourth.

**What the version audit found when it was first widened, over the 47 arXiv IDs
cited here then** *(the current run is the ✅ block below; this paragraph is kept
for the one finding it turned up, not for its counts)*. Every ID resolved. Exactly
**one pinned citation was behind its current version** — EgoDex at v1 against v3 —
and that one is deliberate, for the reason above. **Twelve IDs were cited bare
against papers that had two or more
versions**, which is the hole this audit had until it was widened to cover
unpinned citations: a bare citation silently tracks whatever the paper says
today. Most of that movement is harmless. One instance was not:
[S-EMBER](#s-ember) **changed its headline finding between v1 and v2** — a
*localisation paradox* became a *grounded recall gap* — on identical data. A bare
citation of a claim that has been reframed is not stale, exactly; it is
**quietly correct about a different sentence than the one you read**, which is
harder to notice than being wrong.

🔴 **Re-run in full again 24 Sep 2026, and the version audit finally earned its
keep.** **71** arXiv IDs now cited, all resolved — **47 at their cited version**,
**22 bare against multi-version papers**, **zero errors**, and **two pinned
behind** — one of which was not deliberate and should not have been there:
🔴 **World In Your Hands, cited at v3 against a v4 posted three days earlier.**
That is the whole reason this audit exists, and the first time it has caught
something that changed the document's argument rather than its footnotes:
**v4 deletes every open-source promise in the paper**, and this survey had been
quoting one of them as a live commitment. See
[§2](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild).
📌 **Note for the next run**: the entry now cites **both** v3 and v4 on purpose —
v3 for the sentences v4 removed, v4 for the paper as it stands — so this ID will
keep reporting `STALE` and should be read the way [EgoDex](#egodex)'s v1 pin is
read. **Two deliberate pins-behind, zero accidental ones.**
**193 URLs** checked; **42 non-2xx**, of which **36 are the proxy's blanket 403
on `github.com`** and **six are everything else**. Of those six, **two are real**
— [H-Tac's printed page](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
`beingbeyond.github.io/TTP/` at **404, twelfth consecutive**, and **ENIGMA-360**,
now **500 where it was 403** — a third distinct error code across months of
failures, with the classification **gone** unchanged and the reasoning no
stronger than it was when [the threshold was last tightened](#the-other-thing-that-happened-to-hours-they-went-on-sale).
🔴 **The other four were this document's extractor, not the web.** Three URLs
were swept up with the Markdown around them — two trailing backticks and a pair
of strikethrough tildes — and **all three return 200 once the markup is
stripped**; the fourth, a `humanoidsdaily.com` article, refuses `HEAD` and
answers the range-`GET` fallback with 200, which is what that fallback is for.
**A link checker that reports its own quoting as four dead links is manufacturing
findings**, and one of the three — `nexdata.ai/…/2145` — is a page this survey
has already written up once as withdrawn and
[retracted](#the-other-thing-that-happened-to-hours-they-went-on-sale). The
extractor now strips trailing backticks, tildes and emphasis marks — and the
whole check was re-run against it: **196 URLs, 40 non-2xx, 37 of them the
`github.com` 403, and the three remaining are the two real failures above plus
the `HEAD`-refusing article.** ✅ **Zero manufactured findings on the second
pass**, which is the only way to report a fix to one's own instrument.
⚠️ **And a distinction worth fixing in place, because the two look identical in
a results table**: `github.io` **is not** `github.com` here. A 404 from a GitHub
Pages site is served by GitHub and is a genuine reading; a 403 from `github.com`
is served by this environment's proxy and is a reading about the proxy. The
twelve-times-404 above is real precisely because it is a Pages URL.

📅 **The dated commitments, 24 Sep 2026 — six days to go and nothing has moved.**
[HumanTouch](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform)'s
project page still carries the sentence *"We plan to expand the public release to
1,000 hours by the end of September 2026"*, and both copies of the corpus still
carry the badge **`规模-约100小时`**. The Hugging Face copy is **unchanged since
6 Sep**; ModelScope still reads **CC-BY-NC-4.0**. **Not yet due, not yet
delivered, and now recorded twice at the interim** — which is the point of a
dated promise: someone has to be standing there on the date, and the interim
readings are what make the final one mean something.
⚠️ **The two counters behaved as predicted, which is the only useful thing about
them.** ModelScope **2,616,769 → 2,703,845** (**+87,076** in four days) while
Hugging Face went **11,104 → 10,329** (**−775**) — the same corpus, the same
period, one counter adding eighty-seven thousand and the other shedding
seven hundred. Across **88,085 files**, file-level counting still explains it and
nothing else needs to. **Recorded as two numbers this document read, not as
demand.**
[EgoScale](#egoscale)'s *"Coming Soon"* page is now **216 days** old.

✅ **Re-run in full again 22 Sep 2026.** All **69** arXiv IDs resolved — **47 at
their cited version**, **21 bare against multi-version papers**, **1 deliberately
pinned behind** (EgoDex), **zero errors**. **200 URLs** checked; **38 non-2xx**,
of which **36 are the proxy's blanket 403 on `github.com`** and **2 are real**:
[H-Tac's printed page](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
(**404, eleventh consecutive**) and **ENIGMA-360's**.

🔴 **Two corrections to this document's own link findings, both from this pass.**
The **Nexdata 404 has reverted to 200** and is
[retracted in full](#the-other-thing-that-happened-to-hours-they-went-on-sale)
— a transient outage written up, one sweep ago, as a withdrawn listing. And
**ENIGMA-360 now returns 500, not 403**, on two checks. The entry stays
classified **gone** — eleven failures over months, and the lab root still
returns 200 — but **the specific reasoning has weakened and should be said so**:
that classification rested on *"four identical 403s in a row is not a flapping
server; it is a settled block on that path."* **They are no longer identical.**
A 500 is what a flapping server looks like, so the inference this document drew
from the uniformity of the codes no longer holds even though the conclusion it
reached does. *Recorded because a conclusion that survives the loss of its stated
reason is a conclusion now resting on something the document has not written
down.*

*(The previous full pass, 21 Sep:)* All **66** arXiv IDs resolved — **46 at
their cited version**, **19 bare against multi-version papers**, **1 deliberately
pinned behind** (EgoDex). One paper moved and was re-read because of it:
[OmniViTac](#omnivitac--tactile-on-the-robot-side-27810-downloads-and-a-card-that-says-only-its-licence)
is now at **v3** (10 Aug 2026) against a bare citation, and its figures —
**21,000+ trajectories, 86 tasks, 100+ objects** — are **unchanged at v3**. That
is what a bare citation surviving a revision looks like, and it is worth one line
because the [S-EMBER case](#s-ember) shows what it looks like when one does not.
**193 URLs** checked; **38 non-2xx**, of which **35 are the proxy's blanket 403 on
`github.com`** and 🔴 **three are real — up from two, for the first time in five
passes**:
[H-Tac's printed page](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
(**404, tenth consecutive**), **ENIGMA-360's** (**403 for the eighth time
running** — ten failures, last eight identical, stays **gone**), and 🔴 **new this
pass: `nexdata.ai/datasets/embodied-ai/2145`, the vendor catalogue page for the
"10000-Hour Egocentric Full-Body Multimodal Dataset", now returns 404** while the
category page above it and the site root both return 200. **The listing was
withdrawn; the advertisement was not** — see
[§12](#the-other-thing-that-happened-to-hours-they-went-on-sale).

📅 **The dated commitments, checked on schedule.** [EgoScale](#egoscale)'s
*"Coming Soon"* page is now **214 days** old. [HumanTouch](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform)
promised **1,000 hours by the end of September**; nine days out, its scale badge
still reads **~100 小时** and the Hugging Face copy is unchanged since 6 Sep,
though the ModelScope copy was touched on 20 Sep. **Not yet due, not yet
delivered, and recorded at the interim rather than only at the deadline.**

⚠️ **And its ModelScope counter is now evidence rather than a caveat.** That copy
went **2,584,370 → 2,616,769 in about twenty-four hours — +32,399** — while the
*same corpus's* Hugging Face counter **fell, 12,285 → 11,104**, over the same
interval. **A corpus with one like does not acquire thirty-two thousand
downloaders in a day**; across **88,085 files**, file-level counting explains it
and nothing else needs to. The two columns measure different things, and this is
the reading that shows it instead of asserting it.

*(The previous full pass, 19 Sep: 63 IDs, 43 at cited version, 18 bare
multi-version, 1 pinned; 185 URLs, 2 real failures.)* Earlier still, the audit
found **the same two for the fourth pass running**:
[H-Tac's printed `beingbeyond.github.io/TTP/`](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
(**404, ninth consecutive**) and **ENIGMA-360's project page** — **403 for the
seventh time running**, while `iplab.dmi.unict.it/` itself returns **200**. **Nine
failures, the last seven identical**: that entry stays classified **gone**.

⚠️ **And one apparent failure was the checker's, not the document's.** Two lines
came back non-2xx — `beingbeyond.github.io/TTP/\`` at 404 and
`huggingface.co/datasets/facebook/ego-1k\`` at 401 — because the URL extractor
had swallowed a trailing backtick from the Markdown. Refetched clean,
**`facebook/ego-1k` returns 200**; TTP's 404 is real either way. Recorded because
a link checker that reports a live page as dead is the same class of defect as
the document's own: **a tool's output is a claim, and it gets checked like one.**
Every licence re-read this pass was **unchanged** — Open-AoE's bespoke terms,
both Meta FAIR non-commercial cards, the two third-party stamps — so the
corrections made against them hold. **So were the counters**: Egocentric-100K
119,604, Egocentric-10K 71,219, `jxu124/OpenX-Embodiment` 19,447,
AgiBotWorld-Beta 105,552, `cadene/droid` 104,783, OmniViTac 27,749 — every one
identical to the previous sweep's reading eight hours earlier, which is what a
**rolling thirty-day rate refreshed daily** should look like at that interval. No
ninth reading is recorded for the ratio, because re-reading a value the publisher
has not recomputed is not a second observation.

⚠️ **And the new check has a stated scope limit, found one sweep after it was
installed.** It queries **Hugging Face**. The
[HumanTouch corpus](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform)
found on 20 Sep is **CC-BY-NC-4.0 on ModelScope and carries no licence field at
all on the Hub**, and neither copy is tagged with its paper's arXiv ID — so this
check would not have found it, and did not. **Two sweeps running, the fix has
been *query a different index*, and both times the index the survey was not
asking held something it had concluded was absent.** Every *not released* and
*terms unstated* classification in this document should therefore be read as
negative about **Hugging Face, GitHub and the paper's own pages**, and silent
about ModelScope, OpenDataLab, BAAI and the rest. Re-running them against a
second index is a pass of its own and has not been done.

✅ **A new standing check, added the sweep after it would have paid for itself.**
Search the Hugging Face API by **`arxiv:<id>`** for every arXiv ID this document
cites, and diff the result against what the document says exists. Run for the
first time on 19 Sep 2026 over all 63 IDs, it:

- **found three releases recorded here as unreleased or unlicensed** — most
  importantly [`OpenDriveLab/EgoHumanoid`](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator)
  (Apache-2.0, ungated, 504 downloads), plus two further copies of it and a
  licence-less `BeingBeyond/TTP` model repo;
- **found the [Awesome Egocentric Atlas](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five)**,
  which answered to eighteen IDs at once and is the largest single finding of the
  last twenty sweeps;
- 🟢 **and confirmed eight negatives that had been asserted from absence** —
  EgoScale, EgoCS-400K, EgoLive, ENIGMA-360, HumanNet, World In Your Hands,
  SiMDex and EgoTac return **no Hub artefact carrying their arXiv ID**. Those
  entries had been classified *not released* by looking where the paper points;
  they are now classified that way by asking the index what exists. **A negative
  from the right query is worth more than a negative from three page-loads.**
  🔴 **One of the eight has since been overturned, and it is the one this bullet
  singled out.** World In Your Hands was called *"doubly settled"* here on the
  grounds that the [`tars-robotics/WIYH` candidate](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)
  *"still carries no arXiv tag, which is exactly why this query does not find
  it."* **That sentence contains its own refutation and the document printed it
  anyway**: a query keyed on a tag cannot settle anything about a publisher that
  does not tag, and saying so in the same breath as *settled* is the reasoning
  going backwards. The card is WIYH — tied [in §2](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)
  by the publisher's own API — and the corpus is partially released. **The
  `arxiv:`-tag query remains the best instrument this survey has for finding
  artefacts; it is worth nothing as an instrument for concluding they are
  absent**, and the seven other negatives above inherit that caveat.

🔴 **Counters that did move**, re-read the same day: `facebook/ego-1k`
**61,932 → 56,664**, `inclusionAI/OpenAoE-2000h` **539,829 → 520,848**,
`IPEC-COMMUNITY/FastUMI_100k_lerobot` **269,342 → 265,883**,
`BeingBeyond/UniHand_Preview` **13,377 → 11,136**, `fpvlabs/stereo-550`
**242,618 → 241,301**, `fpvlabs/stera-10m` **7,043 → 6,263**, `facebook/S-EMBER`
**4,468 → 4,611**, `Biscue5/egoscaler-v2` **27,912 → 22,274**, `gatech/EgoMimic`
**1,258 → 1,284**, `tars-robotics/WIYH` **15,855 → 13,485**,
`BeingBeyond/H-Tac_Sample` **234 → 199**, and `DreamVu/SABER-10K` **19 → 18**
overnight — which at least establishes that SABER's counter is live rather than
frozen, and that eighteen is a real rate and not a stuck value. **Eleven of
thirteen fell.** No inference is drawn from that: these are single readings eight
hours to a few weeks apart on a rolling window, and this document has already
recorded twice what happens when a direction is read off too few of them.
🔴 **One is not a counter at all and needs fixing in the prose**:
[OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked) is
described here as **20 Apache-2.0 model repos**; the namespace now holds **46**,
alongside the same **6 datasets, 3 of them still with no licence tag**. The
control row for *"open survives checking"* got more open, and the survey was
quoting a five-sweep-old count. `yt-fts` still says, in its own README,
*"This project is **abandoned** until unemployment inevitably finds me again."* 🟢 **Corroborated from a second index on 24 Sep 2026**: PyPI shows `yt-fts` at **v0.1.62, last uploaded 4 July 2025**, after 54 releases — **fourteen months silent**, which is what an abandoned tool looks like from outside its README.
*(The ID count has grown from 45 to **62** over seven sweeps as entries were
added — HD-EPIC, ReWeight, MINT, OpenWAM, ViTRA, EgoScaler, RoboCOIN,
InternData-A1, the Meta wristband, Project Kitchen, MEgoVista, UMI-Bridge,
OmniViTac and the UMI family — so a rising total is growth, not drift.)*

> **The drift, which is the part worth recording.** Download counters moved
> where licences did not. `jxu124/OpenX-Embodiment` — the unofficial `cc-by-4.0`
> stamp over a pool whose official position states **no overall licence** — now
> reads **12,000 → 16,909 → 20,235 → 18,581 → 19,447** across five readings.
>
> 🔴 **The previous revision of this paragraph called that "up about 69%", and
> that was this document making the exact error it had spent the same commit
> warning against.** Three ascending points were written up as a trend in the
> sentence immediately after a passage explaining that three points show variance
> and four show direction. **The fourth point is down 8.2%.** What survives is the
> weaker and still useful statement: **the unofficial mirror has been pulled
> between twelve and twenty thousand times a month at every reading, and that is
> the artefact a reader should trust least** — which remains the argument for
> recording terms per clip rather than hoping the ecosystem converges. *(Kept
> rather than amended, because a document that catches itself in the same commit
> as the sermon should say so.)* The rest of
> the drift, 17 Sep: Open-AoE **539,829**, Ego-1K **61,932**,
> AgiBotWorld-Beta **105,552**, `cadene/droid` **104,783**,
> `egoscaler-v2` **27,912**, ViTRA-1M **2,526**.

⚠️ **Licence and access are separate axes, and collapsing them misleads.** A
third-party [release tracker](https://egxodata.com/resources/robotics-data-release-tracker-2026)
records Egocentric-10K as "gated; terms require review" — true of *access*, and
compatible with the card's Apache 2.0 *licence*: the Build AI sets ask for
contact details before download while granting permissive terms afterwards.
Conversely [Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)
is gated **and** non-commercial. When recording rights per clip, record both:
*can I get it* and *what may I do with it* fail independently.

**The sharpest demonstration is [S-EMBER](#s-ember), because it is the same bytes
in two access cells at once.** The publisher's copy, `facebook/S-EMBER`, is
CC BY-NC 4.0 behind a name-and-affiliation gate. An anonymised mirror the authors
posted for double-blind review, `paper-review-only/S-EMBER`, is CC BY-NC 4.0 with
no gate, and has taken 2,124 downloads to the official copy's 4,468. One licence
cell, two access cells, one dataset — and the second exists because the review
process *requires* an artefact an anonymous stranger can read, and nothing takes
it down at acceptance. Any field that stores a single value for "how open is
this" will record whichever copy it happened to look at. **The access axis is not
even single-valued per dataset**, which is the strongest argument in this
document for storing the resolved URL you actually pulled from beside the terms
you actually accepted.

**Why this belongs in a Related Work document.** This repo already treats licence
as a first-class per-clip field — CC filtering at search time, licence in the
manifest, unmeasured rights checks *excluded* from the score rather than assumed
to pass. §11 is that same discipline pointed at the toolchain. **A dataset
inherits the restrictions of every model and corpus used to build it.** Clean
clips processed by a non-commercial pipeline do not produce a shippable dataset.
Rights are a property of the whole provenance chain, and the chain is only as
free as its most restrictive link.

### Awesome Egocentric Atlas — somebody else is keeping this index, and its licence column is empty four times in five

🔴 **The single most useful thing found in eighty sweeps, and it was found by a
check this document should have been running from the start.** Searching Hugging
Face by the **`arxiv:` tag** of every paper cited here — rather than by project
name — returned
[`cy0307/awesome-egocentric-atlas`](https://huggingface.co/datasets/cy0307/awesome-egocentric-atlas)
against **eighteen** of them at once. It is **MIT, ungated, 3,333 downloads, 17
likes**, created 16 Jun 2026, last modified 23 Aug 2026, and it is not a paper: it
is a **machine-readable catalogue of 1,044 egocentric resources** as CSV, mirrored
to a [GitHub repo](https://github.com/ChaoYue0307/awesome-egocentric-atlas) and an
interactive site, with a CHANGELOG, a `CITATION.cff`, contribution guidelines and
READMEs in seven languages.

**Its schema is close to the one this document keeps arguing for.** One row per
resource, with `kind` (dataset / benchmark / model / toolkit / collection),
`released`, `venue`, **`license`**, **`status`** — an *access* state, separately
from the licence: `open`, `partial`, `request`, `benchmark`, or `watch` — plus
`scale`, `tasks`, `modalities`, and three URL columns. **It models licence and
access as independent axes**, which is the distinction this survey spent a dozen
sweeps arriving at, and it ships the result as data rather than prose.

🔴 **And then the columns are empty.**

| Column | What it holds across 1,044 rows |
|---|---|
| `license` | **blank in 859 — 82.3%.** A further 35 read *"not specified"*, so **85.6% carry no usable term** |
| `status` | **`watch` in 726 — 69.5%** (catalogued but not obtainable). **`open` in 232 — 22.2%** |
| spelling | the populated 15% does not group: **`MIT` (11) and `mit` (5)**, **`Apache-2.0` (7) and `apache-2.0` (21)**, **`CC BY-NC 4.0` (2) and `cc-by-nc-4.0` (26)**, **`CC BY-NC-SA 4.0` (4) and `cc-by-nc-sa-4.0` (2)** — the same instrument under two keys, so even a filter over the filled cells undercounts |

**This is the strongest evidence in this document for [§11](#11-the-licence-trap),
precisely because it is not this document's.** A survey of eighty entries
reporting that terms are usually missing can be dismissed as a biased sample
chosen to make that point. **An independent index built by someone else, over
1,044 resources, with a licence column it wanted to fill, reaches the same
conclusion at thirteen times the sample size**: rights are *unknown* for the large
majority of this literature, and that is a property of the literature, not of who
is looking.

**The scored comparison, on the 21 rows this document can check at an artefact.**
Every verdict below was re-verified at the card or the publisher's page on
19 Sep 2026, not taken from either document's memory:

| Verdict | Rows |
|---|---|
| ✅ **Agrees** (12) | `Ego-1K` → `fair-noncommercial-research-license`; `Egocentric-10K` and `Egocentric-100K` → `apache-2.0` **with `status: request`** — correct on *both* axes; `PRISM` → `cc-by-nc-4.0`, `request`; `Open-AoE` → `other`; and eight blank/`watch` rows that are genuinely nothing-released — EgoScale, EgoCS-400K, EgoLive, ENIGMA-360, HumanNet, World In Your Hands, SiMDex, EgoTac |
| 🔴 **Wrong** (9) | **`FastUMI-100K` → `apache-2.0`**, where the card has **`cardData: null` and no licence tag of any kind** — a licence invented for the survey's flagship *no-licence* artefact. **`Open X-Embodiment` → `cc-by-4.0` at the official project URL**, where that page states **no overall licence** and the `cc-by-4.0` belongs to the unofficial `jxu124` mirror. **`Nymeria` → `CC BY-NC-SA 4.0`**, where `projectaria/Nymeria` is **`cc-by-nc-4.0`** — a share-alike added. **`EgoVid-5M` → `not specified`**, where the release is **Apache 2.0**. **`MobileEgo Anywhere` → `cc-by-nc-4.0`**, where `fpvlabs/stera-10m` is **`license: other`**. **`EgoDex` → blank and `watch`**, where the terms are **CC-BY-NC-ND** and the zips serve **HTTP 200 with no auth**. And three **misses** — `SABER`, `H-Tac / TTP` and `EgoHumanoid` recorded as `watch` with no licence, where `DreamVu/SABER-10K` (CC BY-NC 4.0, gated), `BeingBeyond/H-Tac_Sample` (MIT, ungated) and `OpenDriveLab/EgoHumanoid` (Apache-2.0, ungated) all exist |

> **Read the wrong column and it is a list of this document's own mistakes.**
> The `Open X-Embodiment` row is **the uploader-stamp error** — a third party's
> licence field standing in for a publisher's silence — which this survey has now
> catalogued four times and committed once itself, against MobileEgo Anywhere.
> The three misses are **the H-Tac shape**: a release sitting in the authors' own
> namespace that the paper does not point at, which this document got wrong twice,
> the second time [this sweep](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator).
> **Two independent efforts, the same two failure modes, in some of the same
> places.** That is much better evidence that these are structural than either
> effort's self-diagnosis, and it is the argument for the check below rather than
> for more care.

✅ **So the fix is a query, not a discipline.** Both efforts fail where a human
decides whether to go looking. Neither fails where a machine can ask. **Every
release that this pass found and both documents had missed carries an `arxiv:`
tag naming its own paper** — so *"list the Hub artefacts tagged with this paper's
arXiv ID"* would have found all three, for free, with no judgement involved.
That query is now part of the staleness pass; what it returned the first time it
ran is [recorded below](#12-free-hours-and-what-they-do-to-the-moat). **The
document's recurring lesson has been *check at the artefact*. The sharper version
is: *ask the artefact index, because it is the only party that knows what exists.***

⚠️ **What this does to [§13](#13-why-no-open-source-project-does-exactly-this),
stated before anyone else has to.** §13 claims there is no open, auditable,
reusable **acquisition** infrastructure. The Atlas is not that, and the difference
is not a quibble: it is an **index of corpora**, one row per published resource,
where the thing §13 says is missing is a **machine** that turns open web video
into clips and records provenance **per clip**. The Atlas has 1,044 rows; a week
of one crawl has millions. But it *is* prior art for the narrower claim this
document also makes — *record licence and access as separate fields, per project,
in machine-readable form* — and that claim now has to be stated as **"the field
has one such index, it is one person's side project, and its licence column is
85.6% empty"**, not as "nobody does this." Same narrowing as
[HumanNet](#humannet) and [HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago)
forced, and for the same reason: the document keeps finding that the thing it
says is absent exists in a partial form somebody built and could not finish.

*(A second copy, `introvoyz042/awesome-egocentric-atlas`, 843 downloads, carries
the same MIT and the same content in a personal namespace — the same account that
mirrors `OpenDriveLab/EgoHumanoid` and `egoengine-repro-artifacts`. Nothing is
wrong with any of them today. It is simply worth noticing that the survey's
uploader-stamp failure mode has a standing supply of uploaders.)*

### The second index, queried at last — and the strongest uploader-stamp case yet

Last sweep this document admitted a scope limit and declined to fix it in the
same breath: **every negative result here had been checked against Hugging Face,
GitHub and the paper's own pages, and never against ModelScope**, and re-running
them against a second index was *"a pass of its own."* 🟢 **This is that pass.**
Roughly two dozen project names — every entry classified *not released* or *terms
unstated*, plus the largest released corpora — were queried against ModelScope's
dataset index on 20 Sep 2026.

✅ **The negatives held, which is the result this document least expected and
should say first.** No ModelScope artefact exists for **EgoScale, EgoCS-400K,
EgoLive, World In Your Hands, SiMDex, EgoTac, OpenMMEgo/OME10M, Egocentric-1M,
DreamDojo's video, Project Kitchen, MEgoVista, UMI-Bridge, BinoGen, EgoMimic,
FastUMI, EgoHumanoid, H-Tac, EgoTactile, EgoScaler, ACE-Ego-0, EgoInfinity,
EgoAVFlow or EgoEngine.** **The admitted blind spot was real and the conclusions
drawn through it survive it** — which is worth stating plainly, because a survey
that announces a methodological hole and then never reports what was in it has
made the announcement do the work of the check.

🔴 **Four things were in it, and the first is the sharpest licence finding in
this document.**

**1. EgoDex, re-uploaded under Apache-2.0, at 814,750 downloads.** EgoDex is
**CC-BY-NC-ND** — non-commercial, *no derivatives* — and is already the
[chokepoint inside at least six downstream artefacts](#egodex). Two ModelScope
copies carry a permissive stamp instead:

| Copy | Licence stated | Downloads | What its own card says |
|---|---|---|---|
| `YuhengZhao/EgoDex` | **Apache License 2.0** | **112,959** | *"本数据集是Apple的EgoDex数据集中的训练集部分，包含了Part1到Part5全部内容"* — "this dataset is the training-set portion of **Apple's EgoDex**, containing all of Part 1 to Part 5", repacked into 50 GB-safe archives |
| `luyitas/egosim_egodex_egovid_full` | **Apache License 2.0** | **701,791** | **EgoDex 5,000 clips + EgoVid 5,000 clips**, re-encoded to 16 fps 720p for EgoSim training |

> 🔴 **This is a new category, and a worse one than the four uploader stamps
> already catalogued.** `simon055/EgoVid_frames`, `jxu124/OpenX-Embodiment`,
> `easpeeder/Egocentric-1M` and `cadene/droid` all state terms **where the
> publisher stated none** — an uploader speaking into a silence. **Here the
> publisher spoke, clearly, and the uploader's field says something else.** The
> first card names Apple's EgoDex explicitly and describes a **repack**, which is
> the operation *ND* exists to govern; the second describes a **re-encode and a
> merge with EgoVid**, which is two derivative operations. *No legal conclusion is
> drawn here and none is needed for the point that matters to a pipeline:* **a
> downloader reading the licence field on the copy they actually pulled gets
> "Apache-2.0" for footage whose publisher wrote "NC-ND", and 814,750 pulls have
> gone through that field.** A manifest that records *the terms as read at the
> artefact* would faithfully record the wrong answer. **The only field that
> survives this is one that records the resolved source URL as well**, which is
> the argument this document has been making for the weaker case and now has the
> strong one for.

**2. A platform mirroring account publishing into publishers' namespaces — with
two licences for one corpus.** On ModelScope, `OpenGVLab/InternVid` reads
**`cc-by-nc-sa-4.0`** and `OpenGVLab/InternVid-Full` reads **`Apache License
2.0`**, on near-identical README text (1,925 and 1,918 characters). On Hugging
Face **both** read `cc-by-nc-sa-4.0`. The tell is in the metadata: both
ModelScope records have **`CreatedBy: Cherrytest`** and **`Owner: OpenGVLab`** —
as does `builddotai/Egocentric-10K` — so a **platform-side mirroring account is
creating repositories inside other organisations' namespaces**, and gave two
copies of one corpus two different licences.

> 🔴 **This is the uploader-stamp failure mode wearing the publisher's
> namespace**, which removes the one cue that made the previous four detectable.
> `jxu124/` and `cadene/` are visibly personal; **`OpenGVLab/InternVid-Full` is
> not.** And the divergent field is the permissive one: Apache-2.0 drops both the
> **non-commercial** restriction and the **share-alike** obligation that
> CC-BY-NC-SA-4.0 exists to propagate — on the corpus whose
> [gate text](#internvid) already adds an obligation its licence does not contain.
> **Three instruments now describe InternVid, and they disagree by platform.**

**3. EgoVerse, Apache-2.0, 149,576 downloads — the fifth stamp into a silence.**
`AQUAbyssteus/egoverse-mirror-v2-aria-all-mono` says *mirror* in its own name,
carries the platform's **default card** with no description, and is stamped
**Apache License 2.0**. [EgoVerse's own terms are not stated anywhere](#egoverse)
— re-verified at v2, zero occurrences of "CC BY" or "Apache" in the paper — and
access runs through the authors' EgoDB/S3 sync. **So the loudest published
answer about EgoVerse's terms is again a third party's**, exactly as with DROID,
and this one has been pulled 149,576 times.

**4. Where this data actually gets pulled from.** The same artefacts, both hubs,
read on the same day:

| Corpus | Hugging Face | ModelScope |
|---|---|---|
| `microsoft/VITRA-TeleData` (**MIT on both** — the one row where the two indexes agree) | **687** | **34,750** |
| Open-AoE 2000h | 520,848 | **7,849,250** |
| Egocentric-10K | 71,219 | **1,106,046** |
| Xperience-10M | *(gated, DocuSign)* | **1,012,177** |

⚠️ **The two columns are not comparable and no ratio is claimed.** Hugging Face's
counter is a rolling thirty-day rate; ModelScope's is undocumented on its API
response and may be cumulative, file-level, or both. **What the table supports is
only that these corpora have substantial ModelScope presence** — which is the
thing a survey that never queried ModelScope could not have known, and is enough
on its own to justify the pass.

✅ **The check is now standing**, alongside the `arxiv:`-tag Hub query: every new
*not released* or *terms unstated* classification is queried against both
indexes before it is written. **Two sweeps in a row the fix was *ask a different
index*; this is the sweep that stopped discovering that and started doing it.**

### OpenEgo — somebody does this properly, and it should be said plainly

**[arXiv 2509.05513](https://arxiv.org/html/2509.05513v1)** — this section has
spent a lot of words on how the field mishandles provenance. Here is the
counterexample, and it is worth more than the criticism.

OpenEgo unifies **six public egocentric datasets into 1,107 hours** with
standardised hand-pose layouts and intention-aligned, timestamped action
primitives, across **290 manipulation tasks in 600+ environments**.

✅ **The composition was audited at Table 1 this sweep, and it adds up.**

| Source | Hours | Frames | Tasks | Recordings |
|---|---|---|---|---|
| EgoDex | 829 | 90 M | 194 | 338 k |
| HoloAssist | 166 | 17.9 M | 20 | 2.2 k |
| CaptainCook4D | 54 | 5.6 M | 24 | 200 |
| HOI4D | 44 | 2.4 M | 16 | 4 k |
| HOT3D | 13.3 | 3.7 M | 33 | 19 |
| HO-Cap | 0.67 | 73 k | 3 | 64 |
| **OpenEgo** | **1107** | **119.6 M** | **290** | **344.5 k** |

The six components sum to **1,106.97** — the stated total is not rounded up from
a looser figure, it is the arithmetic. These are the numbers the
[derivation map](#who-feeds-whom--the-derivation-map) uses to argue licence
inheritance, so they were overdue a check.

⚠️ **And the table explains an error this document made, which is worth saying
because the error was ours and the cause is structural.** Last sweep recorded
that the survey had called CaptainCook4D *"a 54-hour dataset"* when its own page
says **384 recordings, 94.5 hours**. **This is where the 54 comes from.** The row
above is headed *"Egocentric datasets combined to form OpenEgo"* — every figure
in it is *what OpenEgo ingested*, not what the source contains. Read against
CaptainCook4D's own page, OpenEgo takes **200 of 384 recordings** and **54 of
94.5 hours**, about 55% either way: internally consistent, and nowhere stated as
partial.

> **Compare the EgoDex row, which is the tell.** 829 h / 90 M frames / 194 tasks
> / 338 k recordings are *exactly* EgoDex's own published figures — **OpenEgo
> takes all of it.** So the table mixes full ingestion and partial ingestion in
> adjacent rows with no column distinguishing them, and **the mix is itself
> information a reader needs**: it is the difference between "this corpus is
> inside OpenEgo" and "some of this corpus is". Nothing is misstated; a
> composition table is a fair thing to publish. But it is a good reminder that
> **the fix for the subset-versus-total trap is not distrust, it is a second
> fetch** — the source's own page, which is the only place the denominator
> lives. **For this repo**, that is an argument for the manifest carrying the
> fraction ingested alongside the hours, which §11 already asks for on licences
> and this extends to scale.

The
composition is published per source rather than as a total:

| Source | Hours |
|---|---|
| [EgoDex](#egodex) | **829** |
| [HoloAssist](#holoassist) | 166 |
| CaptainCook4D | 54 |
| [HOI4D](#hoi4d) | 44 |
| HOT3D | 13.3 |
| HO-Cap | 0.67 |

**And then it does the thing nobody else in this document does.** Appendix A
states the rights posture explicitly: *"OpenEgo combines six publicly available
egocentric datasets. We respect the license terms of each source."* Processed
annotations are released *"under the original license with attribution"* for
sources permitting redistribution. For EgoDex specifically — CC-BY-NC-ND, the
no-derivatives chokepoint — *"our annotation files will be made available with
permission from the authors."* And *"all releases include license texts and
attribution statements."*

**The mechanism that makes it work is the one worth copying: it redistributes
annotations, not video.** Users *"must first retrieve the underlying EgoDex data
from the official source under its license terms."* That single design choice
dissolves most of [the derivation map](#who-feeds-whom--the-derivation-map)'s
problem — the restrictive licence never has to be re-granted, because the
restricted bytes are never re-shipped, and the terms travel with an attached
licence text rather than being reconstructed by a reader later.

> **Two things this changes.** First, the honest verdict on the field is not
> "nobody handles provenance" but **"it is clearly possible, and almost nobody
> does"** — a sharper and more useful claim, because it removes the excuse that
> the problem is intractable. Second, note the concentration it exposes:
> **829 of OpenEgo's 1,107 hours — 75% — are EgoDex**, which makes it the fifth
> artefact on the derivation map depending on that one corpus, and the only one
> that says out loud what depending on it entails.
>
**Release status, checked at source.** The project site resolves (HTTP 200) and
leads to **[ahadjawaid/openego](https://github.com/ahadjawaid/openego)**, a
Python package — `OpenEgoDataProvider`, annotation classes, projection utilities,
tests — under the **MIT** licence. The annotation files themselves are **not in
the repository yet**: *"We will be releasing all the data throughout the coming
weeks. A download script will be added soon,"* with an interim Box link in the
meantime. So: **tooling shipped, data pending.**

🟢 **And the rights posture is not just an appendix promise — it is a file.**
`ATTRIBUTION.md` is live in the repo (fetched this sweep, last updated
2025-09-10). It gives, per source, the authors, the paper, the project URL, the
licence *with its canonical URL*, and a **ready-to-paste attribution string**:

> "CaptainCook4D © Peddi et al. Licensed under Apache-2.0."
>
> "HOI4D © Liu et al. Licensed under CC BY-NC 4.0 (non-commercial)."

The README adds that *"the datasets included in OpenEgo retain their original
licenses"* and points at a `licenses/` directory alongside it. **That is the
artefact this document has been describing in the abstract for thirty sweeps**,
implemented: not a claim that rights were considered, but a machine-readable,
per-source record a downstream user can act on without re-deriving anything.

> ⚠️ One thing still not asserted. The arXiv listing's CC-BY-4.0 governs the
> *paper*; the annotation releases carry each source's own terms instead, which
> is the more careful arrangement and not the same as a blanket licence.

### Who feeds whom — the derivation map

§11 argues the chain matters. This is the chain, assembled from what the entries
above already establish. Every edge is stated by the downstream project itself,
except the one marked as an inference.

| Downstream artefact | Built from | Restriction inherited |
|---|---|---|
| [EgoScale](#egoscale) (20,854 h VLA) | crowdsourced pool + **EgoDex 829 h** | **CC-BY-NC-ND** rides along |
| [DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) (44,711 h world model) | crowdsourced pool + **EgoDex 829 h** + 55 h in-lab | **CC-BY-NC-ND** rides along |
| *…and those two pools* | ⚠️ **inferred to be the same pool** — identical scenes/tasks/objects, neither paper cites the other | one acquisition, counted twice by a careless reader |
| [ACE-Ego-0](#ace-ego-0) (VLA) | Ego4D + EPIC-KITCHENS + Ego-Exo4D + **EgoDex** + EgoScale | five sets of terms, none visible in the checkpoint |
| 🔴 [Ego2Robot](#ego2robot) (18,561 h synthetic) | **EgoDex 732 h** + EgoVerse 954 h + **[ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit) 249 h** + 7 h in-house | ~38% is **CC-BY-NC-ND**, 49% is EgoVerse's silence, and the ViTRA 13% is **four further corpora deep**. **7 hours of 1,940 — 0.36% — come from a source with unambiguous terms** |
| 🔴 [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit) (1.22 M episodes, MIT) | **Ego4D 77.6%** + EPIC 12.6% + Ego-Exo4D 5.5% + SSv2 4.3% | **Annotations only, no pixels — so the MIT is the authors' own work and correctly scoped.** But two parents are signed-agreement corpora and one is CC BY-NC, and **the card states none of their terms**. The chain's most restrictive link is invisible from the artefact you download |
| [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) | **EgoVerse** (Aria) | EgoVerse's terms — which are not stated |
| [EgoVid-5M](#egovid-5m) (5 M clips) | **Ego4D** annotations; video fetched from Ego4D | Ego4D's unpublished agreement — but the release itself is **annotations only, Apache 2.0**, so the terms attach where they should |
| 🔴 `simon055/EgoVid_frames` (722 shards, 10–100 M images) | **third-party extraction** of frames named for EgoVid | **No card, no licence, no attribution**, ungated, ~5,736 downloads/month. The annotations-only arrangement above, undone by a copy |
| [Panda-70M](#panda-70m) (70 M clips) | **[HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago)** (103 M clips, 371.5 K h) | inherits upstream, stated — and the upstream's own terms are **O-UDA**, read at last |
| [annotated-egocentric-10k](#annotated-egocentric-10k-dataset) | **Egocentric-10K** | Apache 2.0 — a clean chain |
| 🔴 [Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms) / UniHand-2.0 (35,000 h) | Ego4D + EPIC-KITCHENS + **Egocentric-10K** + in-house UniCraftor 200 h | Ego4D's agreement and EPIC's non-commercial terms enter a mixture whose **released preview subset states no licence and does not say what is in it** |
| 🔴 [Being-H0.7](#being-h07--one-corpus-three-products-and-a-second-vendor-doing-it) (and Being-H0) | **the same UniHand 2.0**, stated outright rather than inferred | **One acquisition, three products.** The same undocumented mixture, three times the reach |
| 🔴 [H-Tac / TTP](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) (BeingBeyond) | **11 public datasets**, and benchmarked against **BeingH-0.5 — the same group's own model** | **A fourth BeingBeyond artefact.** Not a separate lab, as this survey had assumed: one group across a VLA family, a world-action model and the tactile work |
| 🔴 [OpenMMEgo](#openmmego--open-weights-and-data-half-kept) / OME10M (8.2 M QA pairs) | **Ego4D**, synthesised into QA pairs | **A fifth.** Annotations over someone else's video — the one shape that could have been released without redistributing a frame, and was not |
| 🔴 [H-Tac](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) (HOI-Tac, ~106 h) | **11 public datasets** — ARCTIC, DexYCB, H2O, H2O3D, HO3D, HOCap, HOI4D, HOT3D, InterHand2.6M, OakInk-v1/v2 | **The largest aggregation here and the least documented**: no licence stated for H-Tac, inputs described only as "public datasets", no release. HOI4D alone is CC BY-NC |
| ✅ [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly) (1,107 h) | **EgoDex 829 h** *(all of it)* + HoloAssist 166 + CaptainCook4D 54 *(of 94.5)* + HOI4D 44 + HOT3D 13.3 + HO-Cap 0.67 — **audited at its Table 1; the six sum to 1,106.97** | **The only row with full per-source provenance**: annotations only, no video redistributed, each source's licence text shipped with attribution, and explicit author permission for the CC-BY-NC-ND component. *(Not the only pointers-only release, and not the first: **HD-VILA-100M** below did it in 2022, and **[EgoVid-5M](#egovid-5m)** ships annotations-only under Apache 2.0. Three instances now — the posture is common; the per-source attribution is not)* |
| ✅ [HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago) (103 M clips, 371.5 K h) | **3.3 M YouTube uploads**, selected by channel popularity + 720p + English subtitles | **URLs only, under a named licence (O-UDA), in 2022** — the release posture OpenEgo is praised for, at ~335× the hours and four years earlier. What it lacks is per-source provenance: one blanket licence over three million third-party uploads |
| 🔴 [OpenWAM-α](#openwam--the-first-project-here-whose-open-survives-being-checked) (46 Apache-2.0 checkpoints) | **their own unreleased 6,897 h egocentric corpus** (30.1% share) + **AgiBotWorld-Beta 18.6%** + RoboCOIN 14.3% + DROID 7.0% + InternData-A1 30.0% | **CC BY-NC-SA 4.0 at 18.6% of the mixture** — non-commercial *and* share-alike, the terms designed to propagate — under Apache-2.0 weights. **Third traced case of a permissive stamp over non-permissive parents.** The mixture table is in the paper; the licence consequence is in neither the paper nor the cards |
| [Open X-Embodiment](#the-robot-native-denominator) | **60 datasets, 34 labs** | unknowable without tracing sixty |
| [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject), Ego2Robot, [MobileEgo](#mobileego-anywhere) | **WiLoR** (+ MANO, YOLO) | **CC-BY-NC-ND** *model* in the annotation path |
| 🔴 [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit) (1.22 M episodes, **ungated, MIT**) | **MANO — as the file format**, not the pipeline | `beta`, `hand_pose` and every joint array are MANO-shaped. Downstream users do not pass through it, they **parse** it |

**Two chokepoints carry most of the risk, and one of them is not the one this
document used to name.** **EgoDex** is inside at least **five** downstream
artefacts on this list — supplying 75% of OpenEgo's hours alone; and the second
is **[MANO](#wilor--the-chokepoint-read-at-source)**, not WiLoR — **at four
layers now, the newest being the one that reaches furthest: the *file format* of
an ungated, MIT-stamped, 1.22 M-episode corpus** ([ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)). WiLoR is where
MANO is most visible, but the permissive alternative (HaMeR, MIT) still requires
MANO, and the one method that tries to drop it still uses MANO's joint
regressor. A CC-BY-NC-ND model can be swapped; a non-commercial,
registration-gated *hand model* under the whole field is harder — the best lead,
**NIMBLE (MIT)**, is built in MANO's own topology, so whether it escapes those
terms is unresolved. Meanwhile,
**WiLoR** — the most-used route *into* MANO — is inside at least three
annotation pipelines. None of the three is obscure, and none is optional in the
way a swappable dependency is: they are the field's default hand-annotated
corpus, default hand model, and default hand reconstructor. **Non-commercial
terms sitting at junctions that this much routes through are the single most
consequential licensing fact in this document** — and the deepest of them,
MANO's, is the one with no published escape route. *Nothing here
alleges non-compliance by anyone*; research use and commercial deployment are
different questions, and several of these projects may well have separate
arrangements. The point is what a reader can determine from the public
artefacts, which is: not much.

⚠️ **And the hour counts for the same corpus disagree.** EgoScale and DreamDojo
each take **829 h** of EgoDex; Ego2Robot takes **732 h**. Different subsets,
different versions, or different accounting — no source says which. When the
same named corpus enters three pipelines at two different sizes, "we used
EgoDex" is not a provenance record.

> **What this map is for.** Read top to bottom, it is an argument for the shape
> of this repo's manifest. Every row is a place where terms, scale or identity
> got lost in one hop — and every one of them would have been a non-issue if the
> upstream unit had carried its source, its licence and its date *per clip*
> rather than per corpus. A dataset that cannot tell you which of its hours came
> from where has already lost the information its users need most.

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
| Egocentric-1M | Apr 2026 (reported) | ~1,000,000 (reported) | **not verified, five attempts** | Apache 2.0 (reported) |

**Egocentric-100K, verified at the dataset card**: 100,405 hours, **10.8 billion
frames**, 2,010,759 clips, 24.79 TB, 30 fps H.265, monocular head-mounted
**fisheye** Build AI Gen 1, per-worker calibrated camera intrinsics, mean 7.06
hours per worker, Apache 2.0, access gated behind sharing contact information.

🔴 **And as of this sweep it has a named consumer that used it as the whole
corpus.** [EgoSmith](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table)
curated a **9,606-hour** egocentric pre-training set across twelve datasets, and
**8,049 of those hours — 83.8% — are Egocentric-100K**, with Egocentric-10K
supplying another 288. **86.8% of the corpus behind an open, Apache-2.0
dexterous VLA is Build AI's free hours**, and the paper publishes the scaling
curve: models pre-trained on 3 K, 6 K and 9.6 K of them, post-trained
identically, improve monotonically on ten real-robot tasks against a
from-scratch baseline. **This is the clearest evidence in the document that the
free drop functions as a pre-training corpus and not merely as a headline** —
and the conversion rate is the other half of it: **8,049 hours kept from
100,405, or 8.0%.** *A hundred thousand free hours bought eight thousand usable
ones, and eight thousand usable ones were enough.*

🔴 **Egocentric-1M could not be found at the publisher, across five separate
attempts.** In order: its Hugging Face card returns 401 to an unauthenticated
fetch; it does not surface in dataset search, where the 100K and 10K-Evaluation
cards do; **Build AI's own Hugging Face organisation page lists exactly four
datasets, and Egocentric-1M is not among them**; a fourth attempt, run
months later against Hugging Face's `egocentric` dataset search, returned
**Egocentric-10K, Egocentric-10K-Evaluation, Egocentric-100K and
Egocentric-100K-Evaluation — all four under `builddotai`, and no
Egocentric-1M**; and a fifth, this sweep, replaced searching with the
publisher's **complete machine-readable index** —
`GET /api/datasets?author=builddotai&full=true` returns **exactly four records**,
listed below, and Egocentric-1M is not one of them. That is a stronger negative
than the four before it: a search can miss a thing, but an exhaustive author
listing that returns four is a claim about all of them. **Note also the
last-modified dates: both headline sets were last touched 2026-02-16**, roughly
two months *before* the release date the secondary coverage gives, so nothing
moved at the publisher around the date in question either.

⚠️ **And the first of those five attempts was never evidence, which this document
should have caught earlier.** The 401 was read as "the card exists but is
gated". Tested this sweep with a control, it means nothing: `builddotai/Egocentric-1M`,
`builddotai/Egocentric-1000K` and an **invented** `build-ai/Egocentric-1M` all
return the *identical* 401 — the same response `apple/EgoDex` gives for a real
gated card. **Hugging Face answers "does not exist" and "exists but you may not
see it" with the same status code**, so a 401 distinguishes nothing and never
did. Four real attempts, then, plus one that proved nothing and was counted
anyway.

🔴 **Meanwhile the name is now occupied — by an empty repository.** Full-text
search for `Egocentric-1M` returns exactly one hit, and it is not Build AI's:
**`easpeeder/Egocentric-1M`**, created 3 Aug 2026, ungated, public, **two files**
— `.gitattributes` and a `README.md` whose *entire contents* are 21 bytes of
front matter:

```yaml
---
license: mit
---
```

No data, no description, no card, seven downloads. **An automated licence or
availability scraper pointed at that name would record "Egocentric-1M — MIT,
ungated, public" and be wrong in every way that matters.** It is the
[size-named-dataset trap](#the-vocabulary-problem--six-ways-a-name-misleads)
in its purest form: the name asserts a million hours, the artefact is a
licence tag. Nothing here suggests bad faith by its uploader — a placeholder is
a perfectly ordinary thing to push — but it is a good demonstration that **a
name plus a licence field is not an artefact**, and that the checks in this
document have to be run against contents, not identifiers.

Five routes, one publisher, nothing:

| Dataset | Last modified | Org listing, first reading | Org listing, later | **API, this sweep** | Likes |
|---|---|---|---|---|---|
| Egocentric-10K | **2026-02-16** | 343 | 34.5 k | **34,587** | 349 |
| **Egocentric-100K** | **2026-02-16** | **161,000** | **1.95 M** | **156,632** | 138 |
| Egocentric-100K-Evaluation | 2025-12-09 | 198 | 30 k | **214** | 7 |
| Egocentric-10K-Evaluation | 2025-11-10 | 158 | 30 k | **382** | 17 |

The counter is a **rolling monthly rate**, not a lifetime total. ⚠️ **And the
last column settles which surface to trust.** This document has recorded for
several sweeps that the organisation listing and the dataset cards disagree,
without being able to say which was anomalous. Queried directly, the API returns
**156,632 and 34,587 — matching the cards exactly**, and **214 and 382 against
the listing's "30 k" for both evaluation sets**. Two independent surfaces agree
against the third, so the **organisation listing is the outlier** and the
card-to-card comparison used [below](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)
is the right one. A discrepancy noted three times finally has an answer, and it
came from asking a third source rather than re-reading the first two.

This document does not claim the release does not exist — it may be private,
gated below the listing, or planned. What it claims is narrower and checkable:
**the ~1 M hours, the April 2026 date and the Apache 2.0 terms rest entirely on
secondary coverage — which still repeats them, in fresh articles, with the date
sharpened to 8 April 2026 — and five attempts at the publisher's own surfaces,
spread over months and ending in an exhaustive index rather than a search, found
nothing.** Anyone sizing a plan against it should get it confirmed first. **The
confidence of the secondary coverage has gone up while the evidence has stayed at
zero**, which is the specific pattern this document exists to interrupt.

**The argument in this section does not depend on that row.** The verified step —
10,000 h at 1080p to 100,405 h at 456×256 — is the whole of the point, and it is
read straight off the cards.

> 🔴 **The download counts are their own finding — and this document got them
> wrong twice, so both errors are recorded here rather than quietly fixed.**
>
> An earlier revision of this section said Egocentric-100K "has been pulled
> **161,000 times** against Egocentric-10K's **343** — roughly 470:1." Two things
> were wrong with that. **First, the metric.** Hugging Face's counter is labelled
> *"Downloads last month"* — a rolling 30-day window, not a lifetime total. "Has
> been pulled 161,000 times" describes a figure that does not exist on the page.
> **Second, the ratio has since collapsed.** Re-read at the dataset cards this
> sweep, like for like:
>
> | Card | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th | 8th | 9th | **10th** | Res. |
> |---|---|---|---|---|---|---|---|---|---|---|---|
> | Egocentric-100K | **164,868** | **158,934** | **156,632** | **145,830** | **124,711** | **123,111** | **119,683** | **119,604** | **123,659** | **132,555** | 456×256 |
> | Egocentric-10K | **34,519** | **30,087** | **34,587** | **40,875** | **39,248** | **69,216** | **73,594** | **71,219** | **70,302** | **69,927** | 1080p |
> | *ratio* | *4.8:1* | *5.3:1* | *4.5:1* | *3.6:1* | *3.2:1* | *1.8:1* | *1.6:1* | *1.7:1* | *1.8:1* | ***1.9:1*** | |
>
> That is **single digits**, not 470:1.
>
> 🔴 **And the fourth reading breaks a claim this document made three readings
> ago.** The previous revision said the ratio *"holds in a 4.5:1 to 5.3:1 band"*.
> It does not: **3.6:1 is outside it**, and the movement is not noise in either
> direction. Between the third reading and the fourth the **1080p corpus rose
> ~18%** (34,587 → 40,875) while the **256p corpus fell ~7%** (156,632 →
> 145,830). Both moved the same way the earlier readings hinted at and this
> document declined to commit to. **So the band was the wrong shape of claim: the
> right one is a trend.** Across four readings the ratio runs **4.8 → 5.3 → 4.5 →
> 3.6**, and the 1080p corpus has gone from *"a few hundred monthly pulls"* at
> first sighting to **forty thousand**.
>
> **This is the rule working, and it is worth being precise about how.** A single
> snapshot gave 470:1 and was wrong. Three readings gave a band and were
> *stable-looking* rather than right — a band is what you get when you have
> enough points to see variance but not enough to see direction. **The fourth
> point is what turned a band into a trend**, and the trend says something the
> band actively concealed: **the gap is closing.** For a document whose §12
> argument is *hours are commoditised, pixels are not*, that is the most
> load-bearing live number here — which is exactly when to state it carefully
> rather than gratefully. The 470:1 figure never got any of this treatment, which
> is precisely how it survived as long as it did.
>
> 🔴 **The fifth reading confirms the trend and refutes the explanation this
> document attached to it, which is the more useful half.** The ratio keeps
> falling — **3.2:1**, five readings now running **4.8 → 5.3 → 4.5 → 3.6 → 3.2**,
> monotonic since the second. But the previous revision explained that fall as
> *"demand for the high-resolution corpus is growing and demand for the
> downsampled one is not."* **Between the fourth reading and the fifth, both
> fell**: the 256p corpus **−14.5%** (145,830 → 124,711) and the 1080p corpus
> **−4.0%** (40,875 → 39,248). Nothing is growing. The 256p corpus is simply
> shedding demand **3.6× faster**.
>
> > **A trend can be real while the story told about it is wrong, and the story
> > is the part that gets quoted.** The number — the ratio, and its direction —
> > has survived five readings. The *mechanism* asserted alongside it survived
> > one. This document's standing rule is that live values expire by default;
> > the fifth reading adds the sharper version: **the explanation attached to a
> > live value expires faster than the value does**, because it is inferred from
> > two points while the value is measured. What is defensible is the relative
> > claim — **the field's pull is shifting toward the high-resolution corpus** —
> > not the absolute one. For this repo's bet that is still the right direction,
> > and it is now a weaker reed than the last revision said.
>
> ⚠️ **The sixth reading is large enough that this document is recording it
> rather than using it.** Taken at face value the ratio has collapsed to
> **1.8:1** — but the move is **+76.4% on the 1080p corpus in roughly a day**
> (39,248 → 69,216) while the 256p corpus was flat (−1.3%). **A rolling
> thirty-day rate cannot move three-quarters in a day unless a very large batch
> landed inside the window**, which is a burst, not a trend. Several neighbours
> moved in the same direction over the same interval — `stereo-550` **+20.6%**,
> AgiBotWorld-Beta **+18.4%**, Ego-1K **+21.5%**, the unofficial OpenX mirror
> **+19.7%** — while others fell (`cadene/droid` −5.2%, `egoscaler-v2` −8.3%),
> so it is not a platform-wide counting change either. **The direction is the
> same one the previous four readings showed; the magnitude is not yet
> evidence.** It is flagged here to be re-read before anything rests on it —
> which is the whole point of having written the rule down twice already.
>
> **Re-read eight hours later, as promised — and it did not wash out.** The
> seventh reading is **119,683 / 73,594 = 1.6:1**: the 256p corpus down another
> **2.8%**, the 1080p corpus up a further **6.3%**. **A single batch does not keep
> climbing.** But this still does not settle it, and the reason is worth stating
> because it is the kind of thing that gets skipped: **a rolling thirty-day
> counter holds a burst inside the window for thirty days**, so the *level*
> staying high proves nothing. **The discriminating observation is whether it
> plateaus or keeps rising** — a burst sits flat at its new level and then falls
> off a cliff when it ages out; sustained demand keeps climbing. **Two readings
> in, it is climbing.** The claim this document will make when there are enough
> points is still the one it has made since the fourth reading: the ratio is
> closing. The claim it is *not* making yet is how fast.
>
> 🔴 **The eighth reading ran that test, and it came back against the reading
> this document would have preferred.** The 1080p corpus went **69,216 → 73,594
> → 71,219**: up, then back. **It plateaued.** Three readings now sit in a narrow
> band around seventy thousand after a step from thirty-nine — which is
> **precisely the shape named one sweep ago as the burst signature**: *a burst
> sits flat at its new level and then falls off a cliff when it ages out;
> sustained demand keeps climbing.* **It is not climbing.**
>
> **So the honest position, stated before the evidence is complete rather than
> after:** the jump was a **step change**, the level has held for three readings
> across about a day, and the **sustained-demand hypothesis is disconfirmed** —
> not the trend, the *explanation for the sixth reading*. **The decisive
> observation is still ahead**: if it was a burst, the counter should fall
> sharply around **mid-October**, thirty days after the jump, as the batch ages
> out of the rolling window. Until then the ratio table carries **1.7:1** and
> this document leans on **3.2:1**, the last reading before the discontinuity.
>
> **This is the fourth time the ratio has taught the same lesson and the first
> time it has cost something.** A snapshot gave 470:1 and was wrong. Three
> readings gave a band and were stable-looking rather than right. A fourth turned
> the band into a trend. A sixth offered the best number this repo's argument has
> ever had — **and the test set up to check it said no.**
>
> 🔴 **The tenth reading ends the trend, and the control says it is real.**
> **1.9:1** — and the ratio has now risen for **three consecutive readings**
> (1.6 → 1.7 → 1.8 → 1.9) after falling for five. The minimum was the seventh.
> **The driver is not the 1080p corpus fading; it is the 256p corpus growing.**
> Against a basket of nineteen counters read the same morning, **median −0.9%,
> thirteen of nineteen down**:
>
> | Card | Move | Against the basket |
> |---|---|---|
> | **Egocentric-100K (256p)** | **+7.2%** | 🔴 **third-largest gain of nineteen**, and the second consecutive reading where it rose against a falling field (+3.4% against −1.3% the day before) |
> | Egocentric-10K (1080p) | **−0.5%** | at the median again — **indistinguishable from drift for the second reading running** |
>
> 🔴 **So the directional claim has to be withdrawn, not just qualified.** This
> document has said since the fourth reading that *"the field's pull is shifting
> toward the high-resolution corpus"* and that *"the direction still runs with
> this repo's bet."* **Two readings with a control now say the opposite**: the
> high-resolution corpus is flat-to-drifting and **the low-resolution one is
> gaining, twice, measurably against its own field.** The five-reading fall from
> 4.8 to 1.6 was real and is not being retracted; **what is retracted is the
> present tense.** The ratio stopped closing at the seventh reading and has been
> widening since, and **the control basket — added one sweep ago precisely to
> stop platform drift being read as signal — is what makes the reversal legible
> rather than deniable.** It was built expecting to defend the trend. It did the
> other thing.
>
> *The mid-October test is unaffected in form and more interesting in substance:
> the question was whether the 1080p corpus falls off a cliff when the September
> burst ages out. It is still the question. But the ratio it feeds into is now
> moving for a different reason than this document assumed.*
>
> 🟢 **The ninth reading held the plateau — and came with the thing this series
> had always lacked: a control.** 1080p reads **70,302**, a fourth consecutive
> value in the seventy-thousand band (69,216 → 73,594 → 71,219 → 70,302), so the
> burst signature is now four readings deep rather than three. 256p reads
> **123,659**, and the ratio is **1.8:1**.
>
> **But the useful part of this reading is methodological.** Eighteen counters
> were read the same morning, not two, and **fourteen of the eighteen fell** —
> `facebook/ego-1k` −5.6%, `UniHand_Preview` −27.6%, `egoscaler-v2` −8.8%,
> `Xspark-HumanTouch` −9.6%, `PRISM-100K` −11.8%, `stereo-550` −1.3%,
> `OpenAoE-2000h` −2.1%, and on. **Median movement across the basket: about
> −1.3%.** Against that baseline:
>
> | Card | Move | Against the basket |
> |---|---|---|
> | **Egocentric-100K (256p)** | **+3.4%** | 🔴 **rose while the field fell** — second-largest gain of eighteen |
> | Egocentric-10K (1080p) | −1.3% | exactly at the median: **indistinguishable from platform drift** |
>
> 🔴 **This changes how the mid-October test has to be read, and it is better to
> notice that now than after the number arrives.** The test as stated was *"the
> 1080p counter should fall sharply around mid-October if the jump was a
> burst."* But an **absolute** fall is not evidence when the whole portfolio
> drifts — and this reading shows it drifting. **A ratio is robust to that and a
> level is not**, because platform-wide drift divides out of the numerator and
> denominator together. **So the test is restated: the burst is confirmed only if
> the 1080p counter falls sharply *relative to the basket median*, not merely in
> absolute terms.** The basket is now read every staleness pass for exactly this
> purpose. *(A tenth reading a day apart would have shown 256p up 3.4% and been
> written up as demand; the control is the only reason that sentence is not in
> this document.)*
>
> ⚠️ **And the publisher's two surfaces disagree.** The organisation listing
> shows **1.95 M** for Egocentric-100K against the card's 164,868, while
> reporting 34.5 k for Egocentric-10K — matching *its* card. One number is
> measuring something different from the other three and neither page says what.
> The like-for-like comparison is card-to-card, so 4.8:1 is what this document
> asserts; the 1.95 M is recorded as unexplained rather than used.
>
> **What survives.** The 256p corpus is still pulled several times more often
> than the 1080p one, so the direction of the field's preference is unchanged —
> but "overwhelmingly" was an artefact of one quiet month early in the 1080p
> set's life, and is not supportable now. The honest read is narrower and more
> interesting: **the gap is closing.** Which makes the counter-position — that
> legibility is what a manipulation dataset is *for* — less lonely than it looked,
> not more.
>
> **The general lesson, for a document that scores rights and scale per clip.**
> A download counter is a *rate*, not a *stock*, and a rate read once is a
> snapshot with a date on it. Any figure this document quotes from a live
> dashboard needs the date attached and a re-read on a schedule — which is why
> the sweep now treats every dashboard number as expiring by default.

**The part nobody leads with: hours scaled 10×, and pixels per hour collapsed.**
Egocentric-10K ships 1080p. Egocentric-100K ships **456×256**. That is roughly a
seventeen-fold reduction in pixels per frame, and 256p is marginal precisely
where this domain needs resolution — finger articulation, small tool affordances,
what is actually being grasped. The free hours are real; they are not the same
hours.

**And the field is visibly splitting along that axis.** In the same window,
[EgoLive](#egolive) went the other way: 1,680 hours of **stereo 2160×2160 at
60 fps** with depth, masks and 3D keypoints. Two strategies, both credible:

| | Hours wing (Egocentric-100K) | Fidelity wing (EgoLive) | Fidelity, taken further ([Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)) |
|---|---|---|---|
| Hours | 100,405 | 1,680 | 10,000 |
| Per-frame | 456×256 mono | 2160×2160 **stereo**, 60 fps | **six streams** (4 fisheye + 2 stereo) |
| Extra signal | none (no audio either) | depth, hand/object masks, 3D keypoints, 6-DoF trajectories | + audio, SLAM pose, two-hand MANO **and full-body mocap**, IMU |
| Total size | 24.79 TB | — | **~1 PB** |
| Licence | Apache 2.0 | CC BY 4.0 | **gated, non-commercial** |
| Bet | scale washes out noise | fidelity is what the model actually needs | capture everything, sort it out later |

No wing is buying **provenance-carrying hours sourced against a stated
requirement**, which is the axis this repo competes on. That is the useful read:
the free corpora are not converging on one thing you have to beat — they are
diverging, and the gap between them is where a requirement-driven collector
lives. Note also that the further right you go in that table, the less *usable*
the corpus becomes commercially: the most instrumented one is the one you cannot
ship on.

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

### Ropedia Xperience-10M — the fidelity wing's extreme, and a caution about reading press releases as availability

**[ropedia-ai/xperience-10m](https://huggingface.co/datasets/ropedia-ai/xperience-10m)**
(March 2026) — the most instrumented egocentric corpus in this document, and the
clearest case of why "released" and "usable" are different words.

Per the dataset card: **10 million experiences, 10,000 hours**, 2.88 B RGB
frames, 720 M depth frames, 7.2 B IMU frames, **~1 PB**, and 16 M caption
sentences over a 6 K vocabulary. **Six synchronised video streams** — four
fisheye plus two rectified stereo — with audio, stereo depth and confidence
maps, SLAM camera pose, two-hand MANO mocap, **full-body mocap**, IMU, and
hierarchical language annotations at five levels: task → subtask → action →
interaction → objects.

✅ **All eleven figures above re-verified at the card, 21 Sep 2026** — 10 M
experiences, 10,000 h, 2.88 B RGB frames, 720 M depth frames, 7.2 B IMU frames,
~1 PB, 16 M caption sentences, 6 K vocabulary, six streams, five annotation
levels, two-hand MANO plus full-body mocap: **every one holds.** Three further
figures the entry did not carry: **576 M pose-and-mocap frames**, **200 M caption
words**, and **350 K objects**. The episode layout confirms the stream count
concretely — `fisheye_cam0..3.mp4` plus the two rectified stereo views — and the
mocap fields are explicitly MANO (`left_mano_hand_pose`, `..._global_orient`,
`..._betas`), which puts this corpus inside the
[MANO chokepoint](#wilor--the-chokepoint-read-at-source) as well.

🔴 **It is not free hours.** The card's licence field reads **"other"**: access
is **gated behind manual review**, restricted to **research and non-commercial
use**, and requires completing a **DocuSign agreement** — and the gate is **two
stage**, which the entry had flattened. The card carries its own warning: *"If
you have already submitted an access request but have not completed the required
DocuSign agreement, your request will remain **pending**."* So a Hugging Face
approval is not access; the binding instrument is signed **off-platform**, at a
`docsend.com` URL, and nothing on the Hub records whether you signed it. On
consent it states the data "was collected and processed under appropriate consent
and review procedures", names privacy and downstream misuse as open questions,
and prohibits identity recognition, person re-identification, biometric profiling
and surveillance. That is a markedly more careful posture than Egocentric-10K's —
and a markedly less available dataset.

🔴 **And there is a sample this entry never mentioned, which makes this the sixth
*partially released* case.**
[`ropedia-ai/xperience-10m-sample`](https://huggingface.co/datasets/ropedia-ai/xperience-10m-sample)
is **CC BY-NC 4.0, ungated, eleven files, `n<1K`**, published 16 March 2026 — a
real, standard, quotable licence with no gate at all, beside a parent that is
`other` behind manual review and a signature. **Same structure as
[SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)**
— restrictive-but-stated terms on the part you can have, bespoke terms on the
part you cannot — **except that SABER's subset was itself gated and this one is
not**, which is one more datapoint for licence and access being independent axes.
*(A small inconsistency, since this document collects them: the sample's own tags
read `xperience-10k`, not `-10m`.)* The org holds **five artefacts** in total, and
**three of them — `SpatialBenchmark`, `DA-Next-5M`, `ropedia-data-sample` — carry
no licence field at all.**

🔴 **The finding that generalises beyond this entry: gate strength does not
predict the pull, and within this one publisher it inverts.** Five artefacts read
the same morning:

| Artefact | Gate | Downloads | Likes |
|---|---|---|---|
| **`ropedia-ai/xperience-10m`** | **manual review + off-platform DocuSign** — the strongest gate in this survey | **102,655** | **249** |
| `agibot-world/AgiBotWorld-Beta` | auto click-through | 105,300 | 77 |
| `ropedia-ai/xperience-10m-sample` | **none** | **472** | 14 |
| `OpenGVLab/InternVid` | auto click-through | **206** | 100 |
| [`DreamVu/SABER-10K`](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of) | auto, four fields | **18** | 0 |

> **Two identical auto gates produce 105,300 and 206.** The heaviest gate here
> produces the second-highest count and **the highest like-count of any artefact
> in this document**. And the decisive pair is *within one publisher*:
> **Ropedia's ungated sample is pulled 217× less than its manually-reviewed,
> DocuSign-bound parent.** **Friction is not the variable; wanting the thing
> is.** That settles, on a five-point spread with an inverted within-publisher
> pair, what [sweep 79 could only settle with one sibling control](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of):
> **a low counter on a gated dataset is not explained by the gate**, and this
> document should stop reaching for that explanation — including for SABER's 18.

**The public critique, and why it belongs here.** A
[July 2026 analysis](https://technologies.org/ropedia-raises-30-million-for-physical-ai-training-data-but-the-dataset-math-doesnt-hold-up/)
argues the headline numbers do not hold up, and its central objection is
arithmetic anyone can check: 10,000 hours is 36 million seconds, so 10 million
"episodes" averages **3.6 seconds each** — long enough to pick up a cup, not to
be an episode in the sense the word implies. It further argues that "billions of
frames" merely restates hours × fps × stream count rather than measuring
diversity, that 10,000 h against Ego4D's 3,670 h is ~2.7× rather than an order of
magnitude (and Ego4D is free), and that a claimed 50× collection-cost reduction
comes with no stated baseline. The article reports no response from Ropedia.

The arithmetic is correct as arithmetic; whether "experience" was ever meant to
denote a multi-second episode is the part left open, and this document takes no
position on the company's claims. What matters here is the **shape** of the
objection, because it is this section's argument arriving from outside: a count
of hours, frames or streams is a vanity metric unless you say what each unit
contains and what you can legally do with it. A collector that reports hours
without reporting **viewpoint, legibility, rights and consent per unit** is
inviting exactly this critique — which is why the manifest carries all four.

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
problems, so the released pose annotations are preferred over it.

✅ **Licence, resolved this sweep — and better than this document assumed.** The
row for EgoVid-5M read *"inherits Ego4D — ⚠️ check upstream"* for dozens of
sweeps. Checked at the release itself, the Hugging Face repo
**[Jeff-Wang/EgoVid-5M](https://huggingface.co/datasets/Jeff-Wang/EgoVid-5M)**
carries **`license: apache-2.0`**, is ungated, and contains **six files**:

```
egovid-kinematic.csv   egovid-text.csv   egovid-val.csv   poses.zip
.gitattributes         README.md
```

**No video.** So Apache 2.0 is not an over-claim over Ego4D's footage — it
covers what is actually in the repository, which is captions, kinematic metadata
and poses. The video is left where it belongs, fetched by the user from Ego4D
under Ego4D's own agreement. **That is the annotations-only discipline, applied
correctly and without comment**, and it makes EgoVid-5M the **third** instance
after [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)
and [HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago).

🔴 **And directly beside it, the counterfactual — one upload away.** A
Hugging Face search for `EgoVid` returns the annotations repo above, and also
**`simon055/EgoVid_frames`**: **722 WebDataset shards** of extracted image
frames, tagged `modality:image` and `size_categories:10M<n<100M`, created 29 Apr
2026, **ungated**, and pulled about **5,736 times a month**. It has **no card at
all** — `README.md` returns **404** — and therefore no licence, no description,
no attribution and no statement of what the frames are of.

> **Why this is the sharpest illustration in the document.** The EgoVid authors
> did the careful thing: ship the annotations, leave the footage upstream, let
> Ego4D's agreement govern the pixels. **A third party then extracted the pixels
> and posted them, and that undoes the arrangement for everyone downstream of
> the copy.** Whether those frames derive from Ego4D video cannot be determined
> from what is published — there is nothing published to determine it from —
> which is itself the point, and the reason it belongs here rather than in a
> complaint. *Nothing improper is alleged against anyone; a frame dump is an
> ordinary thing to upload while working.* But it shows the limit of the
> annotations-only rule as a **protection**: it is a discipline observed by
> publishers, and it binds nobody who was not party to the agreement. **For this
> repo**, the consequence is concrete — a rights record has to survive being
> copied, so provenance belongs *in the manifest travelling with each clip*, not
> only in the release posture of whoever published first.

### EgoCS-400K — 10,000 free hours, sourced from the internet, and why §13 survives it

**[arXiv 2606.18180](https://arxiv.org/html/2606.18180v1)** — the nearest thing
in this literature to the machine this repo is, and the entry most likely to be
read as refuting [§13](#13-why-no-open-source-project-does-exactly-this). It
does not, but the reason is precise and worth stating rather than waved at.

**Scale, all verified at source.** **Over 400,000 first-person videos, over
10,000 hours**, from **over 1,000 matches** and **over 40,000 rounds**, across
**13 maps**, at **10 player viewpoints per round**, averaging ~90 seconds per
round-player video. 🔴 **Licence — corrected this sweep: unresolved, not CC BY
4.0.** The paper's only licence string is the **arXiv listing's**, which governs
the manuscript; no repository, dataset card or download location is named
anywhere in it. This entry asserted CC BY 4.0 for dozens of sweeps on that
evidence — see [the permissive-claims audit](#11-the-licence-trap), where it is
one of five.

**Mechanism, and this is the whole point.** The source is the open internet:
*"We collect public professional CS:GO and CS2 match demos from HLTV."* But what
is collected is not video. It is **replay files** — and the video is then
manufactured: *"We generate first-person videos from demos through a
metadata-guided rendering process"* using CS Demo Manager and the Counter-Strike
client. The action labels are not inferred from pixels either; they are read out
of the demo file as ground truth, with rule-based detectors mapping synchronised
raw signals — button states, weapon state changes, game events — to action spans
covering weapon switches, reloads, inspections, grenade usage, scope
transitions, firing and posture changes.

**So the pipeline is: find on the internet → render → label from ground truth.**
Every hard problem this document is about — proving a clip is egocentric,
proving hands are in frame, recovering what the actor did, establishing rights —
is *dissolved* rather than solved, because the domain hands you a deterministic,
machine-readable record of exactly what happened. Viewpoint is a render
parameter. Actions are a field in a file. There is no camera to classify.

**Which is exactly why it does not generalise, and the authors say so.** The
stated domain gaps: *"continuous physical interaction, tactile feedback,
deformable or manipulable objects, and non-combat everyday behavior"* — and the
positioning is explicit, *"an intermediate testbed rather than a direct model of
real-world embodiment."* There is no HLTV for kitchens. Real-world footage ships
pixels and nothing else, which is the entire reason the acquisition layer has to
assert viewpoint, hands and rights *with evidence* instead of reading them off.

**What it does change.** Two things, and this document should own both.
[§13](#13-why-no-open-source-project-does-exactly-this) can no longer be stated
as "nobody sources ego data from the internet at scale" — somebody does, at
10,000 hours. That narrowed the claim to *real-world* footage —
and a later sweep found [HumanNet](#humannet) mining real human video from the
web at a million hours, which narrowed it again, to **open, auditable, reusable
infrastructure**. §13 sets out both narrowings and what survives them. What
EgoCS-400K contributes specifically is the *price* comparison: web sourcing is
nearly free when the domain hands you ground truth, and everything this document
is about is what it costs when it does not. And
[§12](#12-free-hours-and-what-they-do-to-the-moat)'s argument is untouched for a
different reason: 10,000 hours of rendered Counter-Strike does not commoditise
an hour of real hands manipulating real objects, whatever the licence says.

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

### A third way to get hours: manufacture them

**[arXiv 2609.18650](https://arxiv.org/abs/2609.18650)** (16 Sep 2026) — this
section has treated hours as something you either **capture** (§1) or **find**
(§13). **Project Kitchen** is a third thing: a **VR-based gamified egocentric
data-collection platform** that *"turns data collection into an engaging gameplay
experience"* and then transfers the result to real robots.

**Mechanism.** The platform is deliberately **independent of robot embodiment and
hardware**, which is the point — it is what makes crowdsourcing possible where a
teleoperation rig does not. **Game2Policy** then extracts **embodiment-invariant
affordance cues — contact points and sub-goal states — from gameplay
trajectories**; an affordance model pre-trained on game-collected data is jointly
fine-tuned with downstream policies using *"only a handful of real-robot
demonstrations."* Reported: **+10.0 points in simulation and +18.3 points on real
robots** in the few-shot setting.

> **This is the second gameplay entry in this document, and the two are
> opposites.** [EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it)
> **harvested** 10,000 hours of Counter-Strike demos that existed anyway — the
> cheapest possible acquisition, because the domain hands you ground truth for
> free. Project Kitchen **induces** the hours: it builds a game whose purpose is
> to produce the data. **Harvesting scales with what people already did;
> manufacturing scales with how many people you can persuade to play.** Both
> sidestep the licence problem entirely, which is worth saying plainly — **data
> you caused to exist has no upstream terms to inherit.**
>
> **And that is the sharpest framing of what this repo is betting against.** The
> three routes to an hour are now: *commission it* (expensive, clean, small),
> *manufacture it* (novel, clean, unproven at scale), or *find it* (abundant,
> cheap, and encumbered in exactly the ways this document catalogues). **§13's
> claim was never that finding is the only way — it is that finding is the one
> nobody has published the machinery for.** A gamified platform is a new answer
> to the first half of the question and no answer at all to the second: its
> hours are as unavailable to anyone else as EgoScale's.

🔴 **No repository, no dataset, no project page, no licence** — nothing named in
the paper.

### BinoGen — twenty million synthetic binocular frames, and a release conditioned on an event

**[arXiv 2609.19881](https://arxiv.org/abs/2609.19881)** (v1, 17 Sep 2026) — a
**fourth** way to get hours, and the first that needs no people at all.

**Mechanism.** An automated generator for *"embodiment-aware egocentric binocular
visual experiences in indoor environments"*: generative scene synthesis,
probabilistic object instantiation, appearance randomisation, stochastic
trajectory generation, and **configurable binocular camera rigs** — so the
observer's *viewing height, field of view, binocular geometry and motion* are
parameters rather than properties of whoever wore the camera. Output is
**40,000 synchronised binocular videos × 500 frames at 10 FPS = over 20 million
annotated images**, each with *"perfectly aligned depth maps, optical flow,
surface normals, segmentation masks, object coordinates, and camera poses."*
Reported to improve real-world depth estimation, object detection and video
object tracking when mixed in.

> **Where it sits among the four routes.** *Commission* an hour (expensive,
> clean, small); *manufacture* it by inducing human play
> ([Project Kitchen](#a-third-way-to-get-hours-manufacture-them)); *harvest*
> manufactured hours somebody already produced
> ([EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it));
> or **synthesise it outright**, which is BinoGen. All three of the non-capture
> routes share the property this section keeps returning to — **data you caused
> to exist has no upstream terms to inherit** — and BinoGen is the purest case,
> because there is no recording of any person anywhere in it.

⚠️ **And that purity is exactly its limit for this repo.** The annotations are
*"perfectly aligned"* because the renderer knows the answer; found footage is
hard precisely where synthesis is trivial, and easy — scene, object and
behaviour diversity drawn from the actual world — precisely where synthesis is
hard. BinoGen's own framing is **augmentation** (*"incorporating BinoGen data
consistently improves real-world visual perception"*), not replacement. It is a
strong argument that the **perception** layers can be pre-trained synthetically,
and no argument at all about the **manipulation** payload this survey is about.
A renderer cannot tell you what people do with objects it was told to place.

🔴 **Nothing is released, and the promise is the weakest form this document has
catalogued.** The paper contains **zero external URLs**. Its Appendix B, *"Code
and dataset release"*, reads in full: *"We will release the complete BinoGen
framework **upon publication**, including the data generation pipeline and the
complete binocular video dataset with annotations."* The arXiv listing is
**CC BY-NC-SA 4.0**, which covers the manuscript. **"Upon publication" is a
condition the reader cannot observe and cannot date, and a preprint that is never
accepted has never broken it** — see
[§13](#13-why-no-open-source-project-does-exactly-this) for why that makes it the
only one of five release-promise shapes that cannot be falsified.

### The other thing that happened to hours: they went on sale

The sweep that produced this section has been watching for a *third* giveaway.
What arrived instead was a market. **Of the forty most recently updated Hugging
Face datasets matching "egocentric" (24 July – 10 September 2026), nineteen are
vendor sample or catalogue cards, from about fifteen distinct company accounts** —
Nexdata, humyn-labs, UniDataPro, Worlddatalabs, SmartDeer, ExylosAi, sovrano-ai,
origindatalab, psdn-ai, RunCam, inhandplus, thordata, Digital-Divide-Data and
others, most with *"sample"* in the name. Five were read in full:

| Card | What the name says | What is in it |
|---|---|---|
| 🔴 `Nexdata-AI/10000-Hour-Egocentric-Video-Dataset` | 10,000 hours | **three files.** `.gitattributes`, `README.md`, and a `meta.json` describing **one 59.68-second recording** — whose video file is **not in the repo**. No licence field. Ungated, 60 downloads (**46** at the 21 Sep reading) — and its **vendor catalogue page now 404s** |
| `UniDataPro/egocentric-video` | a dataset | one `.mp4`, one `.csv`, one tracking `.txt` — and **`CC BY-ND 4.0`** |
| `humyn-labs/APAC-Egocentric-Stereo-Labeled` | labelled stereo | annotation JSONLs, `n<1K`, **CC BY 4.0** — a genuine, tiny sample |
| `Worlddatalabs/egocentric-manufacturing` | manufacturing footage | `license: other`, **manually gated**, scene-segmentation JSON |
| `egxodata/egxo-household-egocentric-video-evaluation` | a household evaluation set | `license_name:` **`egxo-controlled-commercial-access`**, manually gated, shipping an `ACCESS_TERMS.md` and a catalogue CSV |

📌 **Re-run 24 Sep 2026: the market is still arriving, and the licence field is
where it shows.** Three more vendor cards were created in the thirteen days to
23 September, **each under a bespoke licence that exists nowhere outside its own
repository**:

| Card | Created | What is actually in it | Licence | Counter |
|---|---|---|---|---|
| `ExylosAi/egocentric-vr-capture-20h-multimodal-sample` | 22 Sep | **195 episodes, 2,283,482 frames, 21.14 "delivered hours"** — consumer-VR egocentric RGB + audio with head, body and hand tracking, LeRobot v3-style, genuinely substantial | `license_name:` **`exylos-proprietary-evaluation`** | **744 in two days** |
| `60base/korea-household-egocentric-samples` | 20 Sep | **16 clips × 20 s — five minutes twenty seconds, ~94 MB.** Korean household tasks, bilingual metadata, per-file SHA-256 | `license_name:` **`60base-sample-evaluation-1.0`** | 108 |
| 🔴 `Nexdata-kr/1000-Segments-6-camera-Egocentric-Embodied-AI-Dataset` | 10 Sep | 32 files, one scene folder — calibration JSONs, SLAM trajectories, `states.hdf5`, a gesture preview | 🔴 **none — `cardData: null`, no tags but `region:us`** | 101 |

⚠️ **Three vendors, three licence names, zero standard instruments** — and this
is now the dominant licence shape in the vendor tier, not an exception. The two
that name terms are candid about the purpose: Exylos's sample exists *"before a
larger commercial delivery"*, 60BASE's *"to discuss a full-recording request or
a custom collection brief"*. ✅ **And credit where it is due: neither inflates.**
60BASE's card says five minutes twenty seconds and means it; Exylos publishes a
frame count that checks out against its file list. **The naming problem this
section documents is Nexdata's, not the tier's** — which matters, because a
survey that files every vendor under *advertisement* stops being able to see the
one that is lying. 🔴 The Nexdata copy is the one with **no licence at all**,
in a second national namespace, two sweeps after the first was written up.

🔴 **The Nexdata card is the sharpest instance in this document of a dataset
named for its size.** Its README is a good one: PICO 4 Ultra head-mounted stereo,
4096×1536, 76-point full-body pose (24 torso + 52 hand joints), wrist and ankle
IMU, step-level annotations, residential/retail/office coverage. Then: *"The
complete dataset is available upon request."* **The repository is the
advertisement.** It beats
[`easpeeder/Egocentric-1M`](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)'s
two-files-no-data not because it is emptier but because it is *deliberate*: a
stub is an abandonment, a listing is a product. *(A small internal
inconsistency, since this document collects them: the README advertises 30 fps;
the single `meta.json` records 24.999.)*

🔴❌ **A retraction, one sweep old.** On 21 Sep the vendor catalogue page this
entry cites — `nexdata.ai/datasets/embodied-ai/2145` — returned **404** on two
checks, while the category page above it and the site root returned **200**.
This document wrote that up as *"a withdrawn listing rather than a site
outage"*, and built a framing on it: *the advertisement outlived the product.*
**On 22 Sep it returns 200, twice. It was a transient outage and the framing was
wrong.**

> **The mistake was not the reading; it was the threshold.** This survey has a
> stated standard for calling a URL dead, set on
> [ENIGMA-360](#enigma-360): *"four identical 403s in a row is not a flapping
> server; it is a settled block on that path"* — and even then it took **ten
> failures over months** before the entry was reclassified. **Nexdata got two
> checks inside one day and a conclusion.** The difference between the two cases
> is not the evidence, it is that the Nexdata reading produced an interesting
> sentence and the ENIGMA one did not. **A survey that sets an evidentiary bar
> and then clears a lower one for its better findings is not applying a
> standard, it is decorating one** — and that is worth more attention than the
>404 ever was. *The standing rule is now explicit: no link is reclassified on
> fewer than three failures spanning more than one sweep.*

**What survives is the part that never depended on the 404**: the Hugging Face
repo is untouched — same three files, no video, **no licence field**, last
modified 12 Aug, still named `10000-Hour-Egocentric-Video-Dataset` — and the
vendor page it points to has always been the only place terms could have been
found.

> **The one claim that stands.** A reader arriving at the Hub sees a live
> repository named for ten thousand hours, with **no licence field** and nothing
> but *"available upon request"* to act on, and must go to the vendor's site to
> learn anything about terms. That was true before the outage and is true after
> it. **The 404 added nothing except a sentence this document liked too much.**

⚠️ **One licence in that table deserves separate notice, because it is a shape
this document has not recorded before: `CC BY-ND 4.0`.** Every restrictive
licence tracked here so far has been **NC** — non-commercial — sometimes with ND
attached, as EgoDex's CC-BY-NC-ND is. A bare **BY-ND** permits commercial use and
forbids **derivatives**, which for a training pipeline is the *worse* half:
clipping, re-encoding, annotating and training arguably all produce derivative
works, while selling the result would have been fine. **A reader scanning for
"NC" as the danger signal reads BY-ND as permissive and gets it exactly
backwards.**

⚠️ **And one publisher is now on both sides of the table.** This document cites
[`egxodata`](https://egxodata.com/resources/robotics-data-release-tracker-2026)'s
Robotics Data Release Tracker as a third-party monitoring source, with the
standing caveat that it collapses licence and access. It is now also **selling
egocentric data under a bespoke licence it wrote and named** —
`egxo-controlled-commercial-access`. The tracker may still be useful; it is no
longer disinterested, and a survey that cites a tracker owes its readers that
fact. **Verify at the publisher, as the caveat already said — and now also verify
who the tracker's publisher competes with.**

> **What this does to the section's argument: it sharpens it rather than
> denting it.** Nominal hours are being commoditised *and* monetised at the same
> time, which is not a contradiction — it is what a commodity market looks like
> when it forms. Free 10,000-hour drops set the floor price of an undifferentiated
> hour at zero; fifteen vendors selling *"available upon request"* corpora above
> that floor are pricing exactly the things the free drops lack, which they
> advertise in their READMEs: **pose annotations, step-level labels, calibrated
> stereo, quality control.** Both halves of the market agree with this document
> about where the value sits. **Neither of them sells the one thing §13 is
> about** — an auditable account of where a clip came from and what may be done
> with it. Nexdata's ten thousand hours arrive with 76-point body pose and **no
> licence field at all.**

## 13. Why no open-source project does exactly this

The obvious question, having read all of the above: internet-scale video →
ego/exo training footage is a clearly valuable, clearly defined problem, and
almost every individual piece of it is open. So why is there no open-source
project that does the whole thing?

The answer is not that people tried and failed. **Open source went hard at the
two adjacent problems and skipped this one.**

⚠️ **And the skipping is much older than this document assumed.** Every example
below is from 2025–2026, which made the pattern look like a property of the
current wave. It is not.
[HowTo100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago)
mined **1.2 M YouTube videos** in 2019 and released the training procedure, the
evaluation code, a pretrained model and a feature-extraction script — **and
nothing about how those videos were found or chosen**. HD-VILA-100M repeated the
exercise at **3.3 M videos and 371.5 K hours** in 2022. **The acquisition layer
has been the reliably unpublished part of web-scale video work for at least
seven years**, across two research generations and both sides of the
industry/academia line. That makes the gap less a coincidence of the current
moment and more a standing property of how these corpora get built.

It also reweights the six reasons below. **Reason 1** — *the citable unit is a
corpus, not a machine* — is exactly what HowTo100M did: corpus, model, benchmark,
features, all published; the machine, not. **Reason 6**, that *the demand is
barely older than the tooling*, is the one that comes off worse: whatever else
explains a seven-year-old pattern, novelty does not. It is kept below, weakened
rather than deleted, because it still holds for the *egocentric* demand
specifically — which is genuinely recent — and not for web-video acquisition in
general.

🔴 **This section has now narrowed four times. Read the narrowings before the
argument.**

**Round one** claimed nobody sources ego data from the internet at scale.
[EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it)
broke that — 10,000+ hours from HLTV — so the claim narrowed to *real-world*
footage, since EgoCS-400K renders video from replay files.

**Round two is [HumanNet](#humannet), and it was inside this document the whole
time.** Its collection stage draws on *"video-platform search, general web search
engines, directly crawled videos, open-source datasets, and self-collection"*,
with self-collection described as complementing *"web-scale acquisition"*. That
is real-world human video, mined from the open internet, at **one million
hours** — by a university group, published, with a follow-up
([HumanScale](#humannet)) showing 5,000 curated egocentric hours beating 5,000
hours of real-robot teleoperation at matched scale. **The flat claim that the
acquisition layer does not exist is false, and this document asserted it for
twenty-five sweeps while carrying the refutation in §2.** That is recorded here
rather than quietly repaired, because how a survey handles its own strongest
counterexample is the only real test of it.

🔴 **Round four is [EgoSteer](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table),
and it takes the *annotate* stage off the table.** A June 2026 paper from PKU
open-sources **EgoSmith**, a pipeline that turns egocentric video into
fully-annotated training data; **342.9 M frames of the labels it produced, with a
per-source licence table and a rehydration script**; **192 hours of Apache-2.0
real-robot teleoperation**; and **two Apache-2.0 VLA checkpoints** whose
real-robot success rises monotonically with the volume of pre-training hours.
Pipeline, data, models and training code, all released under permissive terms.
**Whatever reason 1 says about the citable unit being a corpus rather than a
machine, this group published the machine.**

> **What that leaves, stated precisely, because the temptation is to over-concede.**
> EgoSmith's *input* is twelve existing egocentric corpora — Ego4D,
> EPIC-KITCHENS, Egocentric-10K/100K, EgoDex and eight more — recorded by other
> people and already known to be first-person. **Nothing in it decides whether an
> arbitrary internet video is egocentric, and nothing in it resolves rights on a
> clip nobody has licensed.** Combined with [LAION-BVD](#laion-bvd--it-shipped-and-this-document-said-it-hadnt)
> at the crawl end, the shape of the gap is now unusually legible: **the two ends
> are solved, published and permissively licensed, and the join is not.** That is
> a much smaller claim than this section opened with, and it is the one that is
> still true.

🔴 **One week's worth of evidence, gathered without looking for it.** The sweep
of 18 Sep read **four** papers posted 15–16 Sep 2026 — [the Meta wristband](#the-wristband--tactile-measured-without-instrumenting-the-hand-and-a-fourth-position),
[Project Kitchen](#a-third-way-to-get-hours-manufacture-them), [MEgoVista](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)
and [UMI-Bridge](#simdex) — every one of them proposing **data-collection or
data-conversion machinery**, which is precisely the layer this section is about.
**Not one of the four names a repository, a dataset, a project page or a
licence. Anywhere in the paper.** That is not a curated list; it is everything
matching the query in a single week. **§13 is usually argued retrospectively,
from projects whose release status settled years ago. This is the same
observation made prospectively, on work published the day before it was read** —
and the base rate, in the week it was measured, was four out of four.

🔴 **The next cohort broke it, which is the point of measuring prospectively.**
The sweep of 20 Sep read the **17 September** papers under the same query. Two
propose data machinery, and they split:

| 17 Sep paper | What it proposes | Release surface named |
|---|---|---|
| **[BinoGen](#binogen--twenty-million-synthetic-binocular-frames-and-a-release-conditioned-on-an-event)** (2609.19881) | a generator for egocentric **binocular** experience — 40,000 synthetic videos × 500 frames = **20 M annotated images** with depth, flow, normals, semantics, poses | 🔴 **none.** The paper contains **zero external URLs**. Its Appendix B is titled *"Code and dataset release"* and reads, in full: *"We will release the complete BinoGen framework **upon publication**, including the data generation pipeline and the complete binocular video dataset with annotations."* |
| **[TouchSight](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform)** (2609.20414) | glove-supervised dense contact force, with the glove **generatively removed** from the training pixels | ✅ **a project page that resolves, and a corpus that is actually downloadable** — ~100 hours on two hubs, ungated, today |

**So this week is one out of two, and the streak is over at five out of six.**
🟢 **And the 18 September reading adds a third outcome the two-way count could
not express.** [AtomEgo](#atomego--a-provenance-table-that-restates-four-corpora-at-once)
— a curated 2,659-hour ego–robot corpus **and a "scalable data processing
pipeline"**, which is precisely this section's layer — **names exactly one
external URL** (`github.com/Agentic-Intelligence-Lab/Atom-0`) and contains **no
sentence beginning "we release" or "we will release" anywhere**; every use of
*"open-source"* in it refers to other people's data. **That is neither *ships*
nor *names nothing*: it is a surface with no release claim attached**, and the
repo could not be read from this environment to settle which. The count is
therefore recorded as **three outcomes, not two** — ships (TouchSight), names
nothing (BinoGen and the 15–16 September four), and **names a surface without
claiming a release** (AtomEgo) — because collapsing the third into either of the
others is how a base rate starts flattering whoever keeps it.
That is recorded prominently rather than buried, because **a prospective test
whose reported base rate only ever goes one way is not being run, it is being
quoted.** The counter-example is also the strongest kind: not a paper that
promised better, but one that **shipped** — and shipped, as it happens, on a hub
this survey had never looked at.

🔴 **BinoGen supplies a fifth shape for the release-promise family, and it is the
one with the least purchase on it.** *"Soon"* (OpenMMEgo) is undated. *"Coming
Soon"* (EgoScale) is undated and has now run 211 days. A present-tense *"we
release"* with no address (MINT) at least asserts the thing exists. *"Will be
open-source"* (World In Your Hands) is a commitment without a date. **"Upon
publication"** is different from all four: it is a condition the reader **cannot
observe, cannot date, and which may never occur** — a preprint that is never
accepted has, on its own terms, never broken the promise. **Of the five, it is
the only one that cannot be falsified**, and it is worth saying that a reader
should treat it as the weakest available assurance rather than the most
procedural-sounding one.

🔴 **A sixth shape arrived on 21 September 2026, and it is the one none of the
five anticipated: the promise can be *withdrawn*.** This passage has used
[World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)'s
*"will be open-source"* as the undated-commitment case since it was written.
**v4 of that paper deletes the sentence, deletes the matching sentence in the
conclusion, deletes "Open-Source Ecosystem" from the title, and deletes both the
project-page and code URLs from the title page.** Nothing was broken: an undated
promise that is removed was never due. **The whole family — *soon*, *coming
soon*, *we release*, *will be open-source*, *upon publication* — shares an
assumption this document had not noticed it was making, that the promise stays
put long enough to be checked against.** A reader tracking a release has to pin
the version they are tracking, because **the text they are holding the publisher
to can stop existing while the arXiv landing page still shows it** — which, for
this paper today, is exactly what has happened.

**So what actually survives, stated as narrowly as the evidence allows.** Not
*nobody built one* — somebody did. What is missing is the layer as **open,
auditable, reusable infrastructure**:

- **HumanNet is not released.** No dataset licence, no public release strategy,
  no code beyond a promise. You cannot obtain it, extend it, or run it.
  ⚠️ **Re-checked at the artefact this sweep, since three other unreleased
  entries turned out to have quiet Hugging Face releases.** A repository named
  [`DAGroup-PKU/HumanNet`](https://huggingface.co/datasets/DAGroup-PKU/HumanNet)
  exists, created 6 May 2026 — and contains **exactly one file, `.gitattributes`**.
  No README, no card, no data, 36 downloads. **It is not a release, and nothing
  in it establishes it is even this HumanNet.** Recorded here so the next sweep
  does not mistake a name for a discharge — the same control this document
  applied to `easpeeder/Egocentric-1M`.
- **It is not auditable.** No breakdown of the million hours by source, no
  ego/exo split, no per-clip provenance. Rights review is asserted — *"license
  constraints are reviewed within the same release pipeline"* — and its outcomes
  are unpublished.
- **It is a corpus, not a machine.** It answers "here are a million hours," not
  "here are the hours matching this requirement, with evidence."

**That is a much weaker claim than the one this section opened with, and it
should be.** The interesting question was never whether web mining is possible —
HumanNet settles that, and in this repo's favour, since it is the largest
demonstration anywhere that the supply is real. It is whether the *result* can be
checked: which hours, from where, under what terms, meeting whose requirement.
On that, the field's answer is still nothing you can download.

**And the older evidence still stands for the tooling gap.**
[EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it)
does source ego data from the open internet at scale — 10,000+ hours, CC BY 4.0,
from public match demos on HLTV — and it remains instructive for a different
reason than it first appeared. It works because Counter-Strike ships a
deterministic replay format: the video is *rendered* rather than downloaded, and
the action labels are *read out of the file* rather than recovered from pixels.
Viewpoint is a render parameter; there is no camera to classify, no hands to
verify, no rights to trace. **So it shows what web sourcing costs when the
domain hands you ground truth — nearly nothing — and by contrast what it costs
when the domain does not**, which is every real-world domain, and which is why
HumanNet needed a million hours and a filtering stack to get where it got.

**The rest of this section is about the tooling, and that gap is unchanged.**
Whatever HumanNet built internally, none of it is downloadable, and the public
tools that touch the internet remain viewpoint-blind by construction.

### Where the effort actually went

**Capture.** A substantial and *accelerating* open effort exists for *recording
new* egocentric video, and it now ships pipelines, not just datasets:
[EgoKit](#egokit) unifies collection across seven classes of consumer and XR
device; [MobileEgo Anywhere](#mobileego-anywhere) ships a voice-driven phone app
plus the open STERA pipeline so a lab can generate VLA-ready data on commodity
hardware; [Open-AoE](#open-aoe) releases a
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

**And the scale case is settled the same way.** When NVIDIA needed the largest
egocentric corpus ever assembled for a world model, it **crowdsourced 43,827
hours** ([DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13))
rather than mine the web. That is the strongest available evidence that the
acquisition layer is genuinely absent rather than merely unfashionable: the
best-resourced actor in the field paid for capture instead.

**And the newest work keeps confirming it, in two different ways.** *By
instrumenting what the web already holds*: [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
needed about a hundred hours of grocery stocking and shelf retrieval — one of the
more abundantly filmed activity classes on the open internet — and put its own
cameras on workers in real stores instead. 🔴 *(This document said "sent actors
into real stores" for dozens of sweeps. The paper says the capture was of workers
at work, **"without staging, scripting, or teleoperation overhead"** — corrected
in the entry, and it makes commissioned capture **cheaper** than recorded here,
not more expensive. What the money bought was the synchronised second viewpoint,
which is the part found footage cannot supply.)* *By calling something in-the-wild
that isn't*: [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) reports that
world-action-model co-training "scales more effectively with in-the-wild
egocentric human data," and its in-the-wild data is EgoVerse, captured on Project
Aria glasses, with its 3D flow derived from the glasses' own VIO poses. The
phrase, in this literature, means *outside the robot's lab* — never *off the
open web*. **A survey that read those titles at face value would conclude the
opposite of what this section finds.**

**Acquisition from the web is the hole between them.** The tools that touch the
internet — [video2dataset](#video2dataset), [LAION-BVD](#laion-bvd--it-shipped-and-this-document-said-it-hadnt) — are
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

**And the pattern is not only commercial, which is the stronger form of this
reason.** [HumanNet](#humannet) is a university project that built exactly this
machine — keyword discovery, platform and web-engine search, direct crawling,
filtering, annotation — at a million hours, and released **neither the corpus
nor the stack**: no dataset licence, no release strategy, no code beyond a
promise. Whatever the incentive is, it is not confined to firms protecting a
margin. A pipeline that touches platform terms of service and third-party
footage is awkward to hand out even when nobody is selling anything, which
folds back into reason 3.

**3. Legal exposure lands on the maintainer, and it is asymmetric.** A dataset
release can be framed as research, and that was this document's reading of
LAION-BVD until sweep 92 — 🔴 **wrongly: its 1.3 B-URL list is CC BY 4.0 and
ungated**, and only the derived payloads are restricted to *"academic and
non-commercial researchers"*, with no licence stated on them at all. **The
asymmetry argument survives the correction and is sharpened by it**: LAION split
the release precisely along this line, putting the permissive licence on the
*pointers* and the access form on the *bytes*. A general-purpose tool that automates *search → download →
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

⚠️ **This is the weakest of the six, and re-reading the prior art is what
weakened it.** It explains why nobody built an *egocentric* acquisition layer
before 2025. It does not explain
[HowTo100M and HD-VILA-100M](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago),
which had both the demand and the tooling in 2019 and 2022, mined the web at
100 M-clip scale, and still did not publish the acquisition layer. **Reasons 1
and 2 cover those; reason 6 does not**, and a reason that only covers the recent
half of a seven-year pattern is doing less work than its position in this list
suggests.

### What this does and does not license us to claim

Not "nobody has solved this" — [HumanNet](#humannet) did, at a million hours,
and this section spent twenty-five sweeps asserting otherwise before catching
it. The honest statement is narrower and more useful:

> Every individual stage of the chain is open, and at least one group has
> assembled the whole thing privately. What is missing from **open source** is
> the **acquisition layer** as something you can obtain, inspect and re-run —
> requirement → search → viewpoint proof → rights proof → manifest — and it is
> missing for structural reasons, not because it is technically hard.

**What would falsify that**, stated so a reader can check rather than take it on
trust: a public release, under terms permitting reuse, of a system that takes a
stated requirement and returns clips with per-clip viewpoint evidence, rights
provenance and acceptance status. Not a corpus — corpora exist, several are
enormous, and HumanNet's is the largest. A **machine**, with its outputs
auditable back to their sources. If that appears, this section is finished, and
it should be edited to say so rather than defended.

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
| Bulk fetch | `video2dataset` (MIT) | **Reuse — with a maintenance caveat** | yt-dlp path with per-clip provenance retained. 🔴 **No PyPI release since 1.3.0, 8 Feb 2024 (four releases ever)**, while its own `yt-dlp` dependency has shipped **639** and was last updated **16 Sep 2026**. Reuse it, expect to patch it, **pin yt-dlp yourself** |
| Viewpoint decision | RynnVLA-001 face/hand rule | **Reuse the rule** | Same rule, plus cited cues written to the manifest |
| Exo → ego conversion | Exo2Ego-V | **Reject** | Needs a 4-view 360° rig; the web has none |
| 4D lift / any-view | EgoInfinity, EgoEngine | **Defer** | Both need capture conditions you controlled — a static camera, or object meshes plus calibration |
| Clipping | Panda-70M `splitting/` | **Reuse the design** | Agentic cleaning + clipping with frame-level evidence |
| Orchestration at scale | `cosmos-curate` (Apache 2.0 code) | **Reuse** | — |
| Annotation | Panda-70M select-not-generate; Action100M hierarchy | **Reuse both patterns** | task → action → event tree, L0–L3 gates, refuse-to-label floor |
| Localisation baseline | VLM-Video-Action-Localization | **Use as floor** | Any trained localiser must beat learning-free |
| Curation / scoring | cosmos-curate filters | **Build** | Quality gates as code, four hour measures, cost per hour |
| Rights — deciding | *(mostly ignored)* | **Build** | Licence per clip; unmeasured ⇒ excluded, not assumed |
| Rights — recording | **[OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly)'s `ATTRIBUTION.md`** | **Reuse the format** | Per-source authors, paper, licence *with canonical URL*, and a ready-to-paste attribution line — shipped as a file, not asserted in prose |
| Rights — redistributing | **OpenEgo's annotations-only rule** | **Reuse the rule** | Never re-ship restricted bytes; point at the official source and carry the terms alongside |

**The short version:** skeleton from `cosmos-curate`; clipping design from
Panda-70M; viewpoint rule from RynnVLA-001, independently corroborated;
annotation hierarchy from Action100M with Panda-70M's selection discipline; 4D as
a later upgrade only after the non-commercial dependencies are replaced *and*
the static-camera assumption is dealt with. **The front and the back of the chain
— requirement in, provenance out — are the parts that have to be built, and they
are the parts that are worth owning.**

**One correction to that, earned by the last two sweeps.** The provenance *back*
end is no longer wholly a build. The *judgement* is — deciding whether a found
clip's licence holds is per-clip adjudication nobody ships. But the *record
format* and the *redistribution rule* are solved, publicly, by
[OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly),
and reinventing either would be exactly the mistake this table exists to prevent.
Ship the terms as a file with a canonical licence URL and a paste-ready
attribution line per source; never re-ship bytes you did not receive permission
to re-ship. Those are two afternoons of work borrowed from someone who already
did them, not a research problem.

---

## The vocabulary problem — six ways a name misleads

Separate sweeps found the same class of error independently, which makes it worth
naming as a class. **None of these is a project misrepresenting itself.** Each
phrase is standard usage inside its own subfield. They mislead only when read by
someone asking this document's question — *did this footage come off the open
internet, and may I use it?* — and every one of them, taken at face value, would
have put a false claim into this survey.

⚠️ **The heading used to say "four phrases" while the table held six rows, two of
which are not phrases** — an inconsistency that survived several sweeps of the
rows themselves, because the rows were what each sweep came to edit. It is fixed
here, and it is the same shape as the reference-list failure recorded below: **a
correction applied to the part you were looking at.**

Four rows are phrases. The other two are not — one is two projects whose names
differ by one suffix, where the failure happens in the search box rather than in
the reading; the other is a claim of openness carried in a project's own name or
title, where the failure is that the claim travels further than anything that
could verify it. Both are kept here because the consequence is identical: a fact
about one artefact recorded against another. The
defence is also identical, and it is the only one that works for all six —
**resolve to an identifier, not a name.** An arXiv ID, a repo path, a dataset
card URL. Every row below is a case where the human-readable label was the thing
that failed.

| The phrase | What a reader assumes | What it denotes | Where |
|---|---|---|---|
| **"in the wild"** | found on the internet | *outside the robot's lab* — captured by the authors on their own hardware, **or lifted from existing research corpora**, **or captured from 264 recruited participants under signed consent**, **or — in one sentence of [Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms) — *"in-the-wild egocentric videos from large-scale public repositories, including Ego4D, EPIC-KITCHENS, Egocentric-10K"***, where the phrase and its denial share a clause | [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) (EgoVerse on Aria), [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild) (own wearable suit), and the term's general use across [§2](#2-scaling-human-video-for-robot-learning). 🔴 **And a variant that is not authors' own capture at all**: [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)'s *"'in-the-wild' egocentric human videos without any annotations"* are **Ego4D, EPIC-KITCHENS, Ego-Exo4D and Something-Something V2** — the phrase covering both *not-a-lab-capture* and *not-ours* in one document. ✅ **One honest exception**: [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved)'s in-the-wild inference really does run on found corpora. 📌 **And a tenth instance where the meaning is pinned rather than inferred**: [EgoSmith](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table) *"curates in-the-wild egocentric videos"*, and because its labels release enumerates every source with frame counts, the phrase resolves to **twelve existing research and vendor corpora, zero found footage** — the same answer as the nine before it, reached from the artefact instead of the prose |
| **"from existing web sources"** | crawled from the internet | *from existing public research datasets* — Ego4D, EPIC-KITCHENS, HowTo100M, Something-Something | [RynnVLA-001](#rynnvla-001--filter-dont-convert) |
| **a licence on the paper / the code / the repo** | the terms of the **data** | the terms of that adjacent artefact only — the dataset's terms are separate, and often absent | [EgoScale](#egoscale) (arXiv CC BY 4.0), [NIMBLE](#wilor--the-chokepoint-read-at-source) (repo MIT, paper CC BY), [EgoExoLearn](#egoexolearn) and [EgoHumanoid](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator) (code MIT / Apache 2.0), and — **committed by this document itself** — [MobileEgo Anywhere](#mobileego-anywhere), recorded as CC BY 4.0 for dozens of sweeps when that was the arXiv listing's licence and the dataset is gated `license: other` |
| **a dataset named for its size** | that many hours of the thing you want | often a different unit, a different viewpoint, a different corpus entirely — or no corpus at all | [Ego-1K](#ego-1k) — 956 clips of 8–10 s, not 1,000 hours; [Ego-Exo4D](#ego-exo4d) — 1,286 h of which **221 are egocentric**; **`easpeeder/Egocentric-1M`** — a public, MIT-tagged repo containing [two files and no data](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost); and **`Nexdata-AI/10000-Hour-Egocentric-Video-Dataset`** — three files, one of them the metadata of a [59-second recording it does not contain](#the-other-thing-that-happened-to-hours-they-went-on-sale) |
| **two projects one suffix apart** | distinct work, distinctly findable | the search engine silently picks one — **EgoTac** (2608.15060) vs **EgoTactile** (2606.09243); and worse, 🔴 **EgoScale** (2602.16710, NVIDIA GEAR, artefact *"Coming Soon"* for seven months) vs **[EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)** (2509.21986, Kyoto/NII/Sony), whose dataset is **Apache-2.0, ungated and pulled 27,912 times**. **The missing artefact of one project is impersonated by the present artefact of another** | [EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame) |
| **a name or title that asserts openness** | released, and released under terms | a statement of intent that propagates into every citation — **OpenMMEgo**'s title promises *"Open Weights and Data"*; a year on the weights are public and the repository's data section reads *"We will release our code and data soon"* | [OpenMMEgo](#openmmego--open-weights-and-data-half-kept) |

> **The operational lesson, and it is the same one every time.** Every entry in
> the right-hand column was recovered by opening the source and reading a
> sentence. Every entry in the second column is what a competent reader gets
> from a title, an abstract, or a summary written by someone else. **The gap
> between those two columns is the entire justification for this document's
> read-at-source rule** — and, one level up, for recording provenance per clip
> rather than trusting a corpus-level description. A phrase that means one thing
> to its authors and another to its users is not a lie; it is exactly the kind
> of ambiguity a metadata field resolves and prose does not.

**A seventh case belongs beside these without belonging in the table, because it
is not a label at all.** [SiMDex](#simdex)'s project page offers *Paper · Demo ·
Code · 🤗 Hugging Face* as four buttons in a row; the last two are
`<a href="#" class="disabled">` — inert, unlabelled, with the page's own
stylesheet carrying an unused `.soon` class. Nothing there is false, because
nothing there is a claim: the misleading is done by an **affordance** rather than
a word, and no amount of careful reading catches it, only clicking. The defence
is the same one — resolve to an identifier — but the failure mode is worth
separating, because every row above can be caught by a reader who is paying
attention to the text, and this one cannot.

## Corrections, in one table

Every correction below is argued in place in the entry it belongs to; this is an
index, not a summary, and each row links to the working. **Sixty-three of them are
this document's own errors** *(counted by the marker itself every sweep rather than
by eye: an earlier revision said twenty-nine, which was one short even before
that round's four were added — the count of the count was also drifting)* — marked *(this document…)* in the left column and
counted honestly, because an earlier revision of this preamble said "three" long
after the count had passed it, which is the same failure the table exists to
record. They are kept visible rather than quietly amended: a
survey that silently fixes itself gives a reader no way to calibrate how much to
trust the rest of it.

> 🔴 **The newest own-error is the one that should worry a reader most, because
> the discipline that was supposed to prevent it had already run.** The standing
> rule since the H-Tac miss has been *check at the artefact, not the paper*. The
> EgoHumanoid entry **named the artefact in its own sentence** and still recorded
> *terms not stated*, three months after the card had published them. **A rule
> only binds where someone applies it, and a survey has no way to notice the
> places it did not.** What fixed it was not more care but a query — see the
> [`arxiv:` tag check](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five),
> which found the same class of miss in an independent index built by someone
> else.

> 🔴 **And this sweep supplies a shape none of the above covers: the
> counterexample that was never cited at all.**
> [EgoSteer](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table)
> was posted in **June 2026** and open-sources the pipeline, the labels, the
> real-robot data and the models — the exact combination
> [§13](#13-why-no-open-source-project-does-exactly-this) spends a section saying
> nobody ships. It appears **nowhere in ninety-four sweeps**: not in the body,
> not in the references, not in a table row. **Every other own-error in this
> table was a source read wrongly, read partially, or read once and left to go
> stale — all of them recoverable by re-reading something the document already
> held.** This one is not: there was nothing to re-read. It was found by asking a
> hub for artefacts created in the last fortnight, which is a search the rotation
> runs as *check 4* and which had not, until now, turned up anything that moved
> the argument. **A survey's own pages cannot tell it what it never looked for**,
> and the only defence is a query whose results the survey does not choose.

> **Two of the four earlier own-errors are not misreadings, and that is the
> interesting part.** One entry stated a number that appears in no version of its
> source; four entries stated no terms at all, against a preamble promising terms
> per project; and a whole sweep's corrections landed in the body while the
> reference list went on repeating what had just been disproved. A survey
> accumulates these three shapes — **the unsourced figure, the silent omission,
> and the partially-applied fix** — and only the first is the kind of error that
> re-reading a source catches. The other two are found by auditing the document
> against itself, which is why that is now a standing check rather than an
> occasional one.

| Claim in circulation | What the source says | Where |
|---|---|---|
| The 256p corpus outdownloads the 1080p one **470:1**, and later that the ratio **holds in a 4.5–5.3:1 band** *(this document — two successive errors, one snapshot and one premature generalisation)* | The counter reads **"Downloads last month"**, a rate not a total. And the band broke: five readings run **4.8 → 5.3 → 4.5 → 3.6 → 3.2**, monotonic since the second — **a trend, not a band.** Three points show variance; it takes a fourth to show direction | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **The ratio is closing because demand for the 1080p corpus is growing** *(this document, at the fourth reading)* | The **trend is right and the mechanism was wrong.** At the fifth reading **both corpora fell** — 256p **−14.5%** (145,830 → 124,711), 1080p **−4.0%** (40,875 → 39,248). Nothing is growing; the downsampled corpus is shedding demand **3.6× faster**. **The explanation attached to a live value expires faster than the value does**, because it is inferred from two points while the value is measured | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **Nobody** sources ego data from the internet at scale *(this document, earlier)* | **EgoCS-400K does** — 10,000+ h from public HLTV match demos (⚠️ **its terms are unresolved**, not CC BY 4.0 as this document long recorded — see the permissive-claims audit in §11). Narrowed to *real-world* footage, since EgoCS-400K renders video from replay files and reads actions out of them | [§12](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it), [§13](#13-why-no-open-source-project-does-exactly-this) |
| **Nobody** mines the web for *real-world* human video at scale *(this document, for twenty-five sweeps, while carrying the refutation in §2)* | **HumanNet does**, at one million hours, from *"video-platform search, general web search engines, directly crawled videos, open-source datasets, and self-collection."* What is missing is not the act but the artefact: no release, no licence, no source breakdown, no ego/exo split, no per-clip provenance. §13 narrows to **open, auditable, reusable infrastructure** | [§2](#humannet), [§13](#13-why-no-open-source-project-does-exactly-this) |
| HumanNet's headline is the 1,000 h vs 100 h result | Its follow-up **HumanScale** is stronger and newer: **5,000 h egocentric vs 5,000 h real-robot at matched scale** → 24% lower validation loss, **52.5% / 90%** higher in- and out-of-distribution success. At matched hours that is outperforming, not matching | [§2](#humannet) |
| EgoScale is a UT Austin RPL project *(this document, earlier)* | **GEAR @ NVIDIA Research**, sixteen authors across several institutions | [§2](#egoscale) |
| EgoScale's 20,854 h and DreamDojo's 43,827 h are two independent corpora | Both papers report **9,869 scenes / 6,015 tasks / 43,237 objects** and the same **829 h of EgoDex**, and neither cites the other. Almost certainly one corpus feeding two products; taking both at face value double-counts one acquisition | [§2](#egoscale), [§4](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) |
| EgoScale is CC BY 4.0 | That is the **arXiv listing's licence, covering the paper**. No dataset licence is stated anywhere, and the code is "coming soon" | [§2](#egoscale) |
| The hand-annotation chokepoint is **WiLoR**, and swapping it is tractable engineering *(this document, earlier)* | The chokepoint is **MANO**. The permissive alternative, **HaMeR (MIT)**, still requires MANO — *"register to get access"*; **HandOS**, which avoids MANO parameters, still uses *"the joint regressor defined by MANO"* and has released neither code nor terms. Swapping WiLoR buys a cleaner code licence and nothing more. The best lead out of MANO is **NIMBLE (MIT)**, but it is built in *"MANO topology"* and reuses manopth, so whether it clears those terms is unresolved | [§11](#wilor--the-chokepoint-read-at-source) |
| NIMBLE is CC BY 4.0 | That is the **paper's** licence. The repository says **MIT** — the third case in this document of an adjacent artefact's terms being reported as the thing's own | [§11](#wilor--the-chokepoint-read-at-source) |
| RynnVLA-001 is a source of a viewpoint filtering rule *(this document, earlier — true but incomplete)* | It is also an I2V model pretrained on **12 M egocentric manipulation videos**, with **Apache 2.0** code and two 7B checkpoints released and the corpus not | [§8](#rynnvla-001--filter-dont-convert) |
| RynnVLA-001's 12 M videos are **web-sourced** *(secondary coverage; this document recorded it as unverified rather than repeat it)* | The paper does say *"from existing web sources"* — but §4's citations name **EgoVid-5M, Ego4D, HowTo100M, EPIC-KITCHENS and Something-Something**. "Web sources" means *existing public datasets*, not crawled footage — a fourth naming trap, and one that would have put a false counterexample into §13 | [§8](#rynnvla-001--filter-dont-convert) |
| InternVid states no licence *(this document, earlier)* | The dataset card carries **`cc-by-nc-sa-4.0`** and is gated. Non-commercial **and** share-alike — the most restrictive combination here. An "unresolved" field is a snapshot, not a property | [§3](#internvid) |
| Ego-Exo4D is ~1,286 h of egocentric video | Official docs: **1286.30 video hours, 221.26 ego-hours, 5035 takes** — about **17%** egocentric. The same page also says **1,422 h** in its narrative, so cite the figure *with its sentence* | [§1](#ego-exo4d) |
| Ego-Exo4D has **740 participants across 123 scene contexts** *(the CVPR paper's figures — this document carried them for forty sweeps)* | The official docs now say **more than 800 participants** across **131** natural settings | [§1](#ego-exo4d) |
| EgoDex's CC-BY-NC-ND terms are stated in the paper *(this document, re-verified and recorded as "unchanged" for forty-four sweeps)* | Stated in **v1 and v2**; **v3 (9 Mar 2026) states no licence at all** and drops the "Dataset Access" appendix. The terms are still in force but survive only in two unversioned READMEs. The scale figures came through the revision untouched — **it was the rights statement that moved, not the numbers** | [§2](#egodex), [§11](#11-the-licence-trap) |
| **OpenEgo is the only project that redistributes properly** *(this document, in the derivation map, for dozens of sweeps)* | **HD-VILA-100M did URLs-only release under a named licence — the Open Use of Data Agreement — in 2022**, at 103 M clips and 371.5 K hours, ~335× OpenEgo's. The document cited it the whole time as "Panda-70M's upstream" with a **"⚠️ check upstream"** beside it, which was an instruction to read it. Narrowed: OpenEgo is the only one with **per-source provenance**; URLs-only-under-a-licence is well-established prior art | [§7](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago), [§11](#11-the-licence-trap) |
| The acquisition layer goes unpublished — a pattern in recent work | **It is at least seven years old.** HowTo100M (ICCV 2019) mined 1.2 M YouTube videos and released the training procedure, the evaluation code, a pretrained model and a feature-extraction script — **and nothing about how the videos were found or chosen** | [§7](#howto100m-and-hd-vila-100m--the-crawl-already-happened-twice-years-ago), [§13](#13-why-no-open-source-project-does-exactly-this) |
| **EgoVid-5M's terms are unresolved — "inherits Ego4D, ⚠️ check upstream"** *(this document, for dozens of sweeps)* | Its release carries **Apache 2.0** and contains **three CSVs and `poses.zip` — no video**. The licence is correctly scoped to the annotations; Ego4D's footage stays under Ego4D's agreement. **The third project found doing annotations-only properly**, after OpenEgo and HD-VILA-100M | [§12](#egovid-5m), [§11](#11-the-licence-trap) |
| **EgoEngine shows the action branch supplies essentially all the gain, so photorealism is "decoration"** *(this document, editorialising past its source)* | Table 4 is **0.03 / 0.05 / 0.43 / 0.51** — human videos, visual branch, action branch, full system. The 0.05-vs-0.43 comparison was quoted correctly; **the last row was dropped**. Visual generation adds **0.43 → 0.51**, ~19% relative, and the paper says it *"provides an additional gain"*. The trajectory is the payload; appearance is a real but secondary term | [§2](#egoengine) |
| **H-Tac's contact-rich result is "9.2% → 79.2%"** *(this document, compressing a five-column table into an arrow)* | Both figures are real, but they are **BeingH-0.5's score and theirs**, not a before/after of one system — and on vision defect the arrow started from the weaker of two baselines (π₀.₅ scores 17.8% against the 15.6% quoted). **The informative column is the pre-training ablation: 49.7% → 79.2%**, which isolates what the data buys | [§2](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) |
| **CaptainCook4D is a 54-hour dataset** *(this document, attaching OpenEgo's slice to the source)* | Its own page says **384 recordings, 94.5 hours**. 54 h is what **OpenEgo ingests** (**200 of 384 recordings**, ~55% either way) — the same subset-versus-total trap as Ego-Exo4D's 1,286 h against 221 ego-hours. Traced this sweep to OpenEgo's Table 1, which lists ingested figures beside fully-ingested ones (**EgoDex's 829 h is all of it**) with no column distinguishing the two. Its **Apache 2.0**, previously taken second-hand from OpenEgo's `ATTRIBUTION.md`, verifies at the project page | [§1](#holoassist), [§11](#openego--somebody-does-this-properly-and-it-should-be-said-plainly) |
| **H-Tac and the Being-H models are unrelated projects** *(this document, treating them separately for dozens of sweeps)* | **H-Tac is BeingBeyond's**, its method is named **TTP**, and the baseline in its headline table — **BeingH-0.5** — is the same group's own prior model. Four BeingBeyond artefacts in this survey, not three | [§2](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) |
| **MobileEgo Anywhere is CC BY 4.0** *(this document, for dozens of sweeps — the adjacent-artefact trap it catalogues, committed by itself)* | That is the **arXiv listing's** licence, covering the paper. The dataset `fpvlabs/stera-10m` carries **`license: other`**, is gated, and **401s unauthenticated** — the same bespoke, unreadable posture as its sibling Stereo-550 | [§2](#mobileego-anywhere), [§11](#11-the-licence-trap) |
| **MobileEgo Anywhere and Ego-OSCAR are unrelated projects** *(this document, writing them up in two sections)* | Both are **`fpvlabs`**. The org's Hugging Face account holds exactly two datasets — `stera-10m` and `stereo-550` — both `license: other`, both gated. **Third time the survey has found two entries that were one group**, after NVIDIA's and BeingBeyond's | [§2](#mobileego-anywhere) |
| **EgoScaler's Apache-2.0 set is built on permissively licensed sources** | **None of its four parents is permissive.** Ego4D and Ego-Exo4D are signed-agreement corpora; **HD-EPIC and Nymeria are both CC BY-NC 4.0**, the latter email-gated. The Apache-2.0 correctly covers the authors' own extracted trajectories, but the card states none of this — and **the derived artefact is the one with 27,912 downloads**. Second fully traced case of a permissive stamp over non-permissive parents, after ViTRA, and the first with *zero* permissive parents | [§1](#hd-epic--41-hours-and-the-densest-annotation-in-this-document), [§2](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb) |
| **Nymeria is 3,600 hours** | **300 hours of daily activity**; 3,600 is *camera*-hours across synchronised streams of the same wall-clock time. Both figures sit on one page. Even *worn* hours multiply by the number of sensors pointed at them | [§1](#nymeria--264-consented-participants-called-in-the-wild) |
| **Robot-format manipulation data is scarce because robots are expensive** | **Scarce because of the robot in the loop, which a handheld gripper removes.** [FastUMI-100K](#the-umi-family--capture-without-a-robot-and-the-blind-spot-this-survey-had) is **100 K+ demonstration trajectories in robot-compatible end-effector format, collected with no robot at all** — against DROID's 76 k from thirteen institutions and fifty collectors over twelve months. **The competition for an hour of found footage is no longer teleoperation; it is a $400-ish gripper already at 269,342 downloads** | [§1](#the-robot-native-denominator), [§2](#the-umi-family--capture-without-a-robot-and-the-blind-spot-this-survey-had) |
| **A dataset card either documents the data or it does not exist** | **Publishers ship half a card, and which half varies.** `gatech/EgoMimic` is ungated with **no card at all** — description absent, licence absent. `tars-robotics/OmniVitac` has **27,810 downloads and a card whose entire content is `license: cc-by-nc-4.0`** — terms stated, identity absent; its 21,000 trajectories and 86 tasks are stated only in the paper. **Both halves are needed and publishers keep shipping one** | [§2](#omnivitac--tactile-on-the-robot-side-27810-downloads-and-a-card-that-says-only-its-licence), [§1](#egomimic) |
| **A gate only controls who gets in** | **Two publishers' gates add an obligation their licence does not contain, in near-identical words** — RoboCOIN (`apache-2.0`): *"You agree to not use the dataset to conduct experiments that cause harm to human subjects"*; InternVid (`cc-by-nc-sa-4.0`): *"You agree to not use the data to conduct experiments that cause harm to human subjects."* **The gate text is itself a circulating artefact**, copied between release templates — so expect the added clause on the next card and read it rather than assume it absent | [§1](#the-robot-native-denominator), [§9](#internvid) |
| **A permissive licence tag tells you what you may do** | Not when the gate adds terms. **RoboCOIN's card says `license: apache-2.0`; its gate makes you agree to cite the paper and to avoid experiments harming human subjects** — neither of which Apache-2.0 requires. Two instruments, no statement of which governs, and a downloader has accepted both. **The access gate can add obligations, not merely control who passes** | [§1](#the-robot-native-denominator) |
| **The publisher's copy is the authoritative one to read terms from** | **InternData-A1's official card carries no `license:` tag at all** — its CC BY-NC-SA 4.0 sits inside a gate prompt behind nine fields. A **third-party ungated conversion with 24,586 downloads tags it correctly**. Fifth uploader-stamp instance and the first where the uploader is the one stating the terms in public — the inverse of `cadene/droid`, which asserted Apache-2.0 over a publisher's silence | [§1](#the-robot-native-denominator) |
| **The unofficial OpenX mirror is "up ~69%"** *(this document, in the same commit as a passage warning against exactly this)* | Three ascending readings were written up as a trend one paragraph after explaining that **three points show variance and four show direction**. **The fourth reading is down 8.2%** — 12,000 → 16,909 → 20,235 → **18,581**. What survives is weaker and still useful: the mirror has been pulled **between twelve and twenty thousand times a month at every reading** | [§11](#11-the-licence-trap) |
| **The ratio collapsed to 1.8:1, so the argument is stronger than it looked** *(what the sixth reading invited)* | **The test set up to check it said no.** A burst sits flat at its new level; sustained demand keeps climbing. The 1080p corpus went **69,216 → 73,594 → 71,219** — **it plateaued.** The sustained-demand explanation is **disconfirmed**; the decisive check is whether the counter falls sharply around **mid-October**, thirty days after the jump. **This document leans on 3.2:1, the last reading before the discontinuity** | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **The 256p/1080p download ratio is 3.2:1 and falling steadily** | **A sixth reading gives 1.8:1** — but via a **+76.4% jump on the 1080p corpus in about a day** (39,248 → 69,216) against a flat 256p corpus. A rolling thirty-day rate cannot move three-quarters in a day unless a large batch landed inside the window. **Recorded, not used**: the direction matches the previous four readings, the magnitude is not yet evidence. Neighbours moved +18% to +21% over the same interval while others fell, so it is not a platform-wide counting change either | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **Hours are hours, so corpora can be compared across papers** | **DROID is 350 hours on its own page and 1,285 in [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked)'s pretraining table — a 3.7× restatement of the same corpus, with neither publication stating its unit.** Multi-camera rigs multiply wall-clock into camera-hours ([Nymeria](#nymeria--264-consented-participants-called-in-the-wild) prints 300 and 3,600 on one page). **The first case here of one corpus counted differently by two publications** | [§1](#the-robot-native-denominator) |
| **Adding human video to robot post-training helps** | **Only if you choose which.** [ReWeight](#reweight--the-control-simdex-did-not-run) runs the control SiMDex did not: π₀.₅ post-trained on **robot data only 39%**, **robot + randomly mixed human data 44%**, **robot + selected human data 57%**. Random mixing buys 5 points; selection buys 18. Its paper is explicit that naive mixing *"can **degrade** policy performance"* — so delivering hours without an argument for them is not merely inefficient | [§4](#reweight--the-control-simdex-did-not-run) |
| **A paper that says "we release X" has released X** | [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address) states *"We release the model, training and inference code, labeling pipeline, and a curated 1,021-hour egocentric trajectory dataset"* and **contains no URL anywhere, in v1 or v2** — no repo, no project page, no card, and nothing findable on Hugging Face. **A new shape: a release in the present tense with nowhere to go.** Recorded as *not locatable*, which is not the same as *not released* | [§4](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address), [§11](#11-the-licence-trap) |
| **"Open" in a project's name never survives checking** *(the shape this survey had caught three times)* | ✅ [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked) survives it: **46 Apache-2.0 model repos (20 when first counted, re-counted 19 Sep 2026), 6 datasets, Apache-2.0 code, and all three surfaces its paper names resolve.** The control row the trap catalogue needed — though **3 of its 6 datasets carry no licence tag**, and **its ~6,400 h pretraining corpus is not among them** | [§2](#openwam--the-first-project-here-whose-open-survives-being-checked) |
| **H-Tac has nothing released** *(this document, which reclassified it there on purpose)* | `BeingBeyond/H-Tac_Sample` has existed since **6 July 2026**: **98 episodes, 35,982 frames, 98 videos**, a **MIT `LICENSE`**, ungated, 234 downloads. The checks that produced *not released* were run against the paper and its printed project page — both still say nothing, and the page still 404s. **The release was in a namespace neither points at.** An absence of evidence in the two places a paper sends you is not evidence of absence | [§2](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) |
| **A search for EgoScale's missing dataset finds EgoScale's dataset** | It finds **EgoScaler's** — a different paper by different authors at different institutions (2509.21986 vs 2602.16710). EgoScale's artefact has been *"Coming Soon"* for **214 days**; `Biscue5/egoscaler-v2` is **Apache-2.0, ungated, 27,912 downloads (20,313 at the 21 Sep reading)**. The only thing tying that card to its own paper is an `arxiv:` tag | [§2](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb) |
| **DreamDojo's model terms are unstated** | The *video* terms still are. The **weights** carry **`nvidia-open-model-license`** on `nvidia/DreamDojo` — a bespoke licence, found at the artefact after the paper had been read three times | [§11](#11-the-licence-trap) |
| **DROID is an open dataset with terms you can look up** | **It states none.** Not the project page, not the documentation site, and the data repo `droid-dataset/droid` has **no `LICENSE`** — only the separate `droid_policy_learning` repo does, **MIT**, over code. The loudest answer is a third party's: [`cadene/droid`](https://huggingface.co/datasets/cadene/droid), a LeRobot conversion in a personal namespace, stamped **`apache-2.0`**, ungated, **104,783 downloads** (91,575 at the 20 Sep reading). **Fourth instance of an uploader's licence field standing in for a publisher's silence — and larger than the other three together** | [§1](#the-robot-native-denominator) |
| **AgiBotWorld-Beta is contact-gated** *(this document)* | It is a **click-through**, `gated: auto` — name, affiliation, accept the agreement, immediate access; **86,157 downloads**. Its CC BY-NC-SA 4.0 is still the most restrictive combination in this survey, which is the point: **most-restrictive licence, near-frictionless access**, the same access cell as Apache-2.0 Egocentric-10K | [§1](#the-robot-native-denominator) |
| **A Hugging Face repo named `10000-Hour-Egocentric-Video-Dataset` holds 10,000 hours** | It holds **three files**: `.gitattributes`, a README, and a `meta.json` for **one 59.68-second PICO 4 Ultra recording whose video is not in the repo**. No licence field, ungated. *"The complete dataset is available upon request."* **The repository is the advertisement** — and it is one of nineteen vendor sample or catalogue cards among the forty most recently updated "egocentric" datasets | [§12](#the-other-thing-that-happened-to-hours-they-went-on-sale) |
| **A bare `CC BY-ND 4.0` is a permissive licence** | It permits commercial use and forbids **derivatives** — for a training pipeline the worse half, since clipping, re-encoding, annotating and training all plausibly derive. Every other restrictive licence tracked here is **NC**, so a reader scanning for "NC" as the danger signal reads **BY-ND** as safe and has it backwards. Found on `UniDataPro/egocentric-video` | [§12](#the-other-thing-that-happened-to-hours-they-went-on-sale) |
| **Ego2Robot's reuse risk is "roughly 38% CC-BY-NC-ND"** *(this document, from a name it never opened)* | True and beside the point. **ViTRA, 249 of its 1,940 input hours, had sat in the derivation map as a bare name for dozens of sweeps.** It is Microsoft's, and it is built from **Ego4D (77.6%), EPIC-KITCHENS, Ego-Exo4D and Something-Something V2**. Counting all four parents, **7 hours of 1,940 — 0.36% — come from a source with unambiguous terms** | [§2](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit), [§11](#who-feeds-whom--the-derivation-map) |
| **"ViTRA 249 h"** | Not ViTRA's figure. ViTRA states **1.2 M episodes / 26 M frames** and **never states hours**; 249 h is ~26 M frames at ~29 fps, converted by a downstream paper at an fps stated nowhere. Its own card and paper also disagree on episode count — **1 M** in the abstract, **1,222,918** in the card's per-source table | [§2](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit) |
| **A dataset card that names its sources has recorded its provenance** | `VITRA-VLA/VITRA-1M` names them three times — a `datasets:` field, a per-source episode table, and an acknowledgement — and **states none of their terms**, while stamping the release **MIT**. The MIT is correctly scoped (annotations only, no pixels), but two parents are **signed-agreement** corpora and one is **CC BY-NC 4.0**, so the download is inert until you have signed for 77.6% of it. **Naming a source is not recording its licence** | [§2](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit), [§11](#11-the-licence-trap) |
| **S-EMBER is "15 hours of first-person video"** *(this document, for sixty-two sweeps)* | The paper says **3,141 videos totalling 388 hours** on Ray-Ban Meta glasses, with **9,448 QA pairs** — and says it at **both v1 and v2**, so the figure cannot have come from the source at any version. The entry went on to dismiss it as *"small"*; 388 h is larger than EPIC-KITCHENS-100's 100 and than Ego-Exo4D's 221.26 ego-hours. **The largest single error this document has made about a number** | [§5](#s-ember) |
| **S-EMBER's baselines are GPT-4o and Gemini 3** *(this document)* | **GPT-4o is not a baseline** — it appears once, text-only, with all visual input withheld, as a deliberate "vision-tax" floor. The Gemini is **3.1 Pro**. The panel is InternVL3.5-38B, Qwen3VL-32B, GPT-5.4, Llava-OneVision-7B and Gemini 3.1 Pro. v2 also **reframes the headline** from v1's *localisation paradox* to a **grounded recall gap** (both must hold on the same query: under half the human rate) | [§5](#s-ember) |
| **S-EMBER is CC BY 4.0** | That is the **arXiv HTML's** stamp. The dataset `facebook/S-EMBER` is **CC BY-NC 4.0 and gated** behind name + affiliation; the code repo is **MIT**, inherited from lm-evaluation-harness, while its README states *"the majority of S-EMBER is licensed under CC BY-NC 4.0"*. Three artefacts, three records. **Third Meta FAIR dataset** whose permissive stamp belongs to the paper, after Action100M and Ego-1K. An **ungated anonymised review mirror** also exists, under the *same* CC BY-NC 4.0 — it grants nothing extra | [§5](#s-ember), [§11](#11-the-licence-trap) |
| **Four entries stated no licence or access terms at all** — EgoMimic, SiMDex, OmniRetriever, S-EMBER *(this document, against its own stated method)* | The preamble promises that licence and scale *"are stated explicitly per project"*. For these four, neither was, anywhere in the document. Checked at source this sweep: EgoMimic **MIT code / ungated data with no card whatsoever**, SiMDex **nothing released** (its page's Code and 🤗 buttons are `href="#"`), OmniRetriever **Apache-2.0 bench + LoRA adapter**, S-EMBER as above. **An omission, not a misreading — which is why nothing flagged it for sixty-two sweeps** | [§1](#egomimic), [§4](#simdex), [§5](#omniretriever) |
| **The References section still carried the six corrected CC BY 4.0 claims** *(this document)* | Last sweep's audit rewrote the six entries in the body and **left the reference list untouched**, so the document's own index contradicted its own corrections table for a full sweep. Fixed here. The lesson generalises: a correction is not applied until **every place the claim appears** is changed, and a survey that repeats each figure in a body entry, a table and a reference line has three | [References](#references) |
| **Six entries recorded as dataset CC BY 4.0** — Action100M, Open-AoE, EgoLive, ENIGMA-360, EgoCS-400K, Ego-1K *(this document, systematically)* | In all six the only licence string is the **arXiv listing's**, which governs the manuscript. Three have **no dataset artefact stating terms at all**; the three that do state something **less** permissive — **Action100M and Ego-1K both carry Meta FAIR's `fair-noncommercial-research-license`** and **Open-AoE a bespoke `open-aoe-dataset-license`**. **Six of seven entries checked, all wrong the same direction.** The seventh, **HoloAssist**, was right — because its project page states the dataset's terms in a sentence | [§11](#11-the-licence-trap) |
| Build AI released ~1 M hours (Egocentric-1M) | **Not findable at the publisher across five attempts** spread over months, the last being the complete API index rather than a search. The only artefact of that name anywhere is an **empty third-party repo** — two files, a 21-byte README, no data | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| EgoWAM trains on in-the-wild internet video | Its in-the-wild data is **EgoVerse on Project Aria**, flow from Aria VIO poses | [§2](#egowam--and-what-in-the-wild-turns-out-to-mean) |
| EgoAVFlow needs no special capture, since it needs no robot demos | **Head-mounted RealSense D435 RGBD, plus a ChArUco board in every scene** | [§2](#egoavflow--no-robot-demonstrations-still-means-a-board-in-every-scene) |
| ~~World In Your Hands is research-only, commercial restricted~~ → **this document's own correction of that, which was itself wrong** | 🔴 **Retracted.** This row said *"no dataset licence is stated; 'will be open-source' is a promise, not a grant"* and treated the secondary coverage as embellishment. **The paper's Appendix E says, in v3 and v4 alike: *"intended exclusively for research… redistribution or commercial use is restricted."*** The coverage was a faithful summary of an appendix this survey had not opened. What survives is narrower: the paper states **terms** and names no **instrument**, deferring to *"the licence accompanying the dataset"* — which turns out to be **CC BY-NC 4.0** at the artefact | [§2](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild) |
| EgoExoLearn / EgoHumanoid are openly licensed datasets | Their **MIT and Apache 2.0 licences cover the code**; neither states dataset terms | [§1](#egoexolearn), [§2](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator) |
| Ego-1K is ~1,000 hours of egocentric video | **956 videos of ~8–10 seconds** from a 16-camera rig, for novel-view synthesis | [§1](#ego-1k) |
| Open X-Embodiment is an openly licensed pooled corpus | **No overall licence stated**, and no position on whether its 60 components keep their own | [§2](#the-robot-native-denominator) |
| The high-fidelity corpora are free too | Xperience-10M **manual-gated + DocuSign, non-commercial** (with an ungated CC BY-NC 4.0 sample beside it); AgiBotWorld-Beta **CC BY-NC-SA**; EgoScale **unreleased**; SABER **a quarter released, CC BY-NC, and that quarter gated** | [§11](#11-the-licence-trap) |
| EgoInfinity processed 142 M clips / 14.6 years | Its abstract makes **no** scale claim; those are Action100M's figures, and EgoInfinity's curated set is **106 videos** | [§8](#egoinfinity--lift-to-4d-then-reproject) |
| HumanNet: 1,000 h ego video *beat* 100 h robot data | "**matched or modestly surpassed**" — and that 100 h is ~a third of all of DROID | [§2](#humannet) |
| **LAION-BVD is unreleased — downloads marked *coming soon* — and research-use-only** *(this document, for months)* | 🔴 **Wrong twice.** It has been **released since 3 May 2026** and is actively maintained (`BVD-V-55M` modified **20 Sep**). And the terms split: the **four URL lists are `cc-by-4.0` and ungated** — **CC BY 4.0 permits commercial use** — while the **four payloads carry no `license:` field at all** and go to *"academic and non-commercial researchers"* through a Google Form. 🟢 It is the **fourth and largest URLs-only-under-a-named-licence release** here, after HD-VILA-100M, OpenEgo and EgoVid-5M — **1.3 billion URLs, three columns, one of them the CommonCrawl snapshot each came from.** And **the pointers are pulled 15× more than the bytes** (36,547 vs 2,383), which is the strongest evidence here that URLs-only is **not a compromise release** | [§7](#laion-bvd--it-shipped-and-this-document-said-it-hadnt) |
| Action100M has 100 M instances | **147 M** temporally localised segments from 1.2 M instructional videos | [§10](#action100m) |
| cosmos-curate and NeMo Curator are rival tools | Cosmos-Xenna is **NeMo Curator's production executor** | [§9](#cosmos-curate) |
| A tracker lists Egocentric-10K as gated, so it isn't Apache 2.0 | Both are true — **licence and access are separate axes** | [§11](#11-the-licence-trap) |
| **`video2dataset` is "the de-facto standard, and still the right answer for bulk fetch"** *(this document, recommending **Reuse** in §14 with no maintenance note)* | **It has not shipped a release in thirty-one months** — four releases ever, the last **1.3.0 on 8 Feb 2024** — while the `yt-dlp` it wraps has shipped **639** and was last updated **16 Sep 2026**. Site extractors break continuously; **a wrapper pinned to a February-2024 view of that surface is stale, not stable.** The recommendation stands and now reads *reuse it, expect to patch it, pin yt-dlp yourself*. 🟢 The lineage is otherwise alive — `img2dataset` Aug 2025, `webdataset` Jun 2025, `nemo-curator` Jul 2026 — which is what makes this specific | [§7](#video2dataset), [§14](#14-build-vs-reuse-per-stage) |
| **This survey can see whether the tools it recommends are maintained** *(implicitly, for ninety-three sweeps)* | **It could not, and never said so.** The proxy **403s `github.com`**, so commits, releases and activity have been invisible throughout, and the gap was filled with a **star count read once** — already flagged as the document's weakest number. **PyPI was never queried.** After ModelScope and the `arxiv:`-tag Hub query, **this is the third time the fix is *ask a different index*** — and **the first where the missing index bears on a recommendation rather than a fact** | [§7](#video2dataset) |
| **`ego4d`, the CLI Ego4D's own start-here page sends you to, is current** | **v1.7.3, last uploaded 8 June 2024** — over two years. The corpus does not rot, but **the tool a new user is told to `pip install` does**, and it pairs badly with credentials that expire in fourteen days | [§1](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads) |
| **Human video substitutes for robot data, but nobody has priced it** | [Zeva-Ego](#zeva-ego--the-first-published-exchange-rate-and-a-named-consumer-of-the-free-ten-thousand-hours) **prices it: roughly 4–5 ego hours per robot hour.** 10K ego hours take RoboTwin from **63.8% → 75.3%**, against **74.7% from 2K robot hours**, same π₀.₅ initialisation. Nothing else here states a ratio — HumanNet, HumanScale, OpenWAM, ReWeight, UMI-Bridge and AtomEgo all compare mixtures without converting. ⚠️ One benchmark, one initialisation: **a measurement, not a law** | [§2](#zeva-ego--the-first-published-exchange-rate-and-a-named-consumer-of-the-free-ten-thousand-hours) |
| **The free 10,000-hour drop is a corpus with no named consumers** *(this document, tracking its download counter for ten readings without finding one)* | **Zeva-Ego is one, in print — and it discarded 55.6% of it.** *"The public release totals 10,000 hours, 192,900 clips, and 1.08 billion frames at 30 Hz … **We use 4,439 hours selected through task-stratified sampling.** The source release does not include frame-aligned hand poses or action trajectories."* **A published acceptance rate on the specific corpus §12 is about**, plus a one-clause statement of what it lacks — the third consumer-written acceptance specification here. *And the arithmetic that follows is the honest version of the moat argument: at 4–5:1 with 55.6% discarded, **ten free hours buy about one robot hour*** | [§12](#egocentric-10k), [§2](#zeva-ego--the-first-published-exchange-rate-and-a-named-consumer-of-the-free-ten-thousand-hours) |
| **"In the wild" in this literature never means off the open web** *(this document, across eight senses)* | ✅ **Ninth test, same answer.** [EgoWild2Dex](#egowild2dex--a-ninth-in-the-wild-and-the-first-measured-number-for-why-it-is-hard)'s is *"homes, factories, and pharmacies… where people perform their ordinary tasks while wearing head-mounted cameras"* — **commissioned capture of ordinary work in venues nobody controlled.** The same sense SABER turned out to have after its own correction. 🟢 It also supplies the first **measured** number for why uncontrolled ego video is hard: **a mean cumulative rotation of 15.93°/s** — where MINT, MEgoVista and EgoWAM all address camera instability qualitatively | [§2](#egowild2dex--a-ninth-in-the-wild-and-the-first-measured-number-for-why-it-is-hard) |
| **Checking whether a paper names a release surface is a good proxy for whether the artefact exists** *(the test §13's prospective tally has been running)* | **The two come apart, and EgoWild2Dex is the clean case.** It says *"we release EgoWild"* (538.9 h, 179,049 episodes), its project page **resolves and describes the dataset** — and links to the PDF, the lab and the company, **and to no download**. Both standing checks return nothing: **no Hugging Face artefact tagged `arxiv:2609.23755`, nothing under the name, nothing on ModelScope**, no licence stated. **A reader who asks "is a surface named" gets yes; a reader who follows it gets nothing** — so the tally should count *does the artefact exist* | [§13](#13-why-no-open-source-project-does-exactly-this), [§2](#egowild2dex--a-ninth-in-the-wild-and-the-first-measured-number-for-why-it-is-hard) |
| **DreamDojo has 2,000× more scenes than the previously largest world-model dataset** | **That multiple uses a scene count the same paper replaces one page later.** Table 1 lists DreamDojo-HV at **1,135k trajectories and 1,135k scenes — identical**, i.e. every trajectory counted as its own scene; **1,135,000 ÷ DROID's 564 = 2,013×.** The prose says *"more than **9,869 unique scenes**"*, which gives **17.5×**. Both are in the paper and it never reconciles them. *No error alleged* — but **the large number is printed in the comparison and the small one in the description**, which is precisely the vanity-metric objection this document endorses against Xperience-10M, **found here in the paper it calls its strongest §13 evidence** | [§4](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) |
| **DreamDojo's 6,015 tasks is a counted figure** *(this document, reproducing it without its footnote)* | The table marks it **"† Estimated by GPT based on the global language annotations."** **LLM-estimated, not enumerated** — a reason to label it, not to discard it. *And it strengthens the EgoScale double-count inference it feeds*: two papers independently reporting **the same GPT-estimated 6,015** is less likely to be coincidence than two reporting the same counted integer | [§4](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13), [§2](#egoscale) |
| **DROID has 86 skills** *(DreamDojo's Table 1, and a third publication to say so)* | **DROID's own paper says 84 tasks at both versions**; 86 is the *project page's* figure. DreamDojo, this document, and the page all carry 86; the paper carries 84. **This is how a figure becomes consensus without ever being re-derived** — and it is the same corpus already appearing at 343, 350 and 1,285 hours across three publications | [§1](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it), [§4](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) |
| **The field's pull is shifting toward the high-resolution corpus** *(this document, since the fourth reading, in the present tense)* | 🔴 **Withdrawn.** The ratio stopped closing at the seventh reading and has **widened for three consecutive readings** — 1.6 → 1.7 → 1.8 → **1.9** — and the control basket says the driver is real: **256p rose +3.4% then +7.2% against basket medians of −1.3% and −0.9%**, while **1080p sat at the median both times**. **The low-resolution corpus is gaining; the high-resolution one is drifting.** The five-reading fall from 4.8 to 1.6 was real and stands; **what is retracted is the present tense**. *The basket was added one sweep earlier to stop drift being read as signal, and expecting to defend the trend. It did the other thing* | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **Nexdata's vendor listing was withdrawn while its advertisement stayed up** *(this document, one sweep ago, on two checks inside a single day)* | 🔴 **Retracted — it returns 200 again.** A transient outage written up as a withdrawal, with a framing built on top of it. **The mistake was the threshold, not the reading.** This survey's stated bar, set on ENIGMA-360, is *"four identical 403s in a row is not a flapping server"* — and even that entry took **ten failures over months**. Nexdata got two checks and a conclusion, because the reading produced an interesting sentence. **A survey that sets an evidentiary bar and clears a lower one for its better findings is decorating a standard, not applying one.** New rule: **no link is reclassified on fewer than three failures spanning more than one sweep** | [§12](#the-other-thing-that-happened-to-hours-they-went-on-sale) |
| **ENIGMA-360 is gone, because four identical 403s are a settled block rather than a flapping server** *(this document's stated reasoning)* | **The conclusion holds; the reason does not.** On 22 Sep it returns **500**, twice — **the codes are no longer identical**, and a 500 is what a flapping server looks like. Eleven failures over months, and the lab root still returns 200, so the entry stays **gone** — but **it now rests on something this document has not written down**, which is worth saying rather than leaving the old sentence in place | [§1](#enigma-360) |
| **AgiBotWorld-Beta's licence field says CC BY-NC-SA 4.0** *(this document, quoting it for dozens of sweeps as the denominator's most restrictive licence)* | **It has no `license:` tag at all** — not in its Hub tags, not in `cardData` — so the hub files the most-propagating licence in this survey as **unlicensed**. The CC BY-NC-SA 4.0 lives inside **`extra_gated_prompt`**. Not *terms unstated* (a gate prompt is readable before you accept) but **terms mislocated**, which defeats anyone filtering a hub by licence rather than opening cards. 🔴 And the agreement inside the **Beta** repo is headed *"AgiBot World **Alpha** Release Date: December 30, 2024"* — **copied forward and not re-dated** | [§1](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate) |
| **AgiBotWorld-Beta is the example of most-restrictive-licence, near-frictionless access** *(this document's standing illustration that the two axes are independent)* | **The axes point is right; the illustration was wrong.** Its `extra_gated_fields` are **First Name, Last Name, Email, Country, Affiliation, Phone, Job title, Research interest and geo** — **a telephone number, which no other card in this survey asks for.** Still `gated: auto`, so access is immediate and unreviewed. **Automatic is not the same as light**, and this document had been conflating them | [§1](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate) |
| **A publisher ships half a card; which half varies between publishers** | **It varies *within* one publisher.** `AgiBotWorld-Beta` has the terms (inside its gate) and no readable scale; `AgiBotWorld2026` — **ungated, `cc-by-nc-sa-4.0` correctly tagged, 256,104 downloads against Beta's 104,421** — has the licence and **states no scale anywhere**, its README being a format and download guide. **Two halves, one namespace, and the ungated scale-less one is pulled 2.5× more.** Across the org, **eight of twelve datasets carry no `license:` tag**, including both flagship corpora | [§1](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate) |
| **AgiBotWorld is "200+ task types"** *(this document)* | **217 tasks**, per the paper, across five deployment scenarios and over 1 M trajectories. Small, and corrected because the survey's own rule is to cite the figure the source states | [§1](#agibotworld--twenty-three-mentions-and-the-licence-is-inside-the-gate) |
| **Ego4D's terms are an "unpublished agreement"** *(this document's shorthand across sixty mentions)* | **Not quite.** There is a named **Ego4D License Agreement**, the project page offers **a draft to review before signing**, execution happens at a separate site with **~48 h approval**, and you sign **as an individual or — needing a director-level signatory — for an institution**. **Terms previewable in draft, binding text executed elsewhere, per-signatory** — closer to Xperience-10M's two-instrument gate than to anything with a `license:` field. *(The signing site returned **429** from this environment, so the executed text was not read.)* | [§1](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads) |
| **Third-party re-uploads are a failure of uploader diligence** *(this document's framing across five catalogued uploader-stamp cases)* | **At least partly they are a predictable response to an official route that expires.** Ego4D's own page: *"once approved your access credentials will **expire in 14 days** — you're expected to **download the data locally**, not to consume it from AWS."* The steady state that produces is thousands of individually-signed holders of private copies, with **no technical tie back to the agreement they signed** — and `simon055/EgoVid_frames` (722 shards, no card, no licence, no attribution) is what it makes easy. *No criticism of the consent design is intended; expiring credentials are reasonable for a corpus of consented faces.* **The narrow point is that when the authoritative copy is hard to hold, the copy people use is one whose terms nobody recorded** | [§1](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads), [§11](#11-the-licence-trap) |
| **The corpus underneath most of this literature has an entry** *(this document, for eighty-six sweeps)* | **It had five lines.** Ego4D is named **sixty times**, is EgoVid-5M's parent, **77.6% of ViTRA's input** and a component of EgoScaler and OME10M — and carried no licence, no participant count and no access description. Now written up from source: **3,670 h, 923 participants, 74 locations, 9 countries, 88 researchers, v2.0**, with a stated two-tier consent posture. **Second time a scan by mention count has found the survey's own foundations unread**, after DROID at thirty | [§1](#ego4d--sixty-mentions-and-the-access-design-that-manufactures-re-uploads) |
| **Two publications disagreeing on a corpus's hours means one of them changed the unit** *(this document's reading of DROID at 350 vs OpenWAM's 1,285)* | **There are at least three causes and the number cannot tell you which.** [AtomEgo](#atomego--a-provenance-table-that-restates-four-corpora-at-once)'s Table 1 restates **four corpora at once**: DROID at **343.0** against **350** (filtering), AgiBotWorld-Beta at **314.0** against **2,976.4** (a **9.5×** subset), RoboCOIN at **655.7** against **956**, EgoVerse at **1,079.5** against a paper that says **1,362** and a citation that says 954. Add OpenWAM's DROID at **1,285** and the same corpus appears at 343, 350 and 1,285. **Smaller by filtering, smaller by subsetting, larger by unit — and nothing in any table distinguishes them.** A corpus name plus an hour-count is not a citation | [§2](#atomego--a-provenance-table-that-restates-four-corpora-at-once), [§1](#the-robot-native-denominator) |
| **The open real-robot denominator is ~4,300 h, so the multiple is 23×** | **A fourth corpus was missing: RoboMIND** — 107,000 trajectories, 479 tasks, four embodiments, **Apache-2.0**, 57,305 downloads, **the largest permissively licensed real-robot set in this survey** — found inside AtomEgo's mixture, never opened here. 🔴 **Its publisher states no hours at all**, so adding it requires deriving one (~285 h on AtomEgo's per-episode rate, flagged as derived): total **≈4,585 h**, multiple **≈22×**. **The claim has now survived two enlargements of its own denominator**, having collapsed from 287× at the first | [§1](#the-robot-native-denominator) |
| **A paper either names a release surface or it does not** *(the two-way count §13's prospective base rate was keeping)* | **AtomEgo is a third thing.** It names **one** external URL and contains **no sentence beginning "we release" or "we will release"** — every *"open-source"* in it describes **other people's** data — so its 2,659-hour recipe and its *"scalable data processing pipeline"* are neither claimed as published nor said to be withheld. **Recorded as a third outcome rather than folded into either**, because collapsing it is how a base rate starts flattering whoever keeps it | [§13](#13-why-no-open-source-project-does-exactly-this) |
| **A gated dataset's low download count is explained by the gate** *(the reading this document reached for at SABER, then ruled out with a single sibling control)* | **Ruled out properly now, on five points with an inverted within-publisher pair.** `ropedia-ai/xperience-10m` has the **strongest gate in this survey — manual review plus an off-platform DocuSign** — and **102,655 downloads with 249 likes**, the highest like-count here. Two *identical* auto gates give **105,300** (AgiBotWorld-Beta) and **206** (InternVid). And Ropedia's **ungated** sample is pulled **472 times against its gated parent's 102,655 — 217× less.** **Friction is not the variable; wanting the thing is** — including for SABER's 18 | [§12](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability) |
| **Xperience-10M is gated, full stop** *(this document, for dozens of sweeps)* | **It is *partially released*, the sixth such case, and the entry never said so.** [`ropedia-ai/xperience-10m-sample`](https://huggingface.co/datasets/ropedia-ai/xperience-10m-sample) is **CC BY-NC 4.0, ungated, eleven files** — a standard, quotable licence beside a parent that is `other` behind manual review and a signature. Same structure as SABER, **except SABER's subset was itself gated and this one is not.** The org holds five artefacts and **three carry no licence field at all** | [§12](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability) |
| **Xperience-10M's gate is a manual review** *(this document, flattening two steps into one)* | **Two instruments, one off-platform.** The card warns that an approved Hugging Face request *"will remain **pending**"* until a **DocuSign agreement** is signed at a `docsend.com` URL. **The binding document is not on the Hub and the Hub records nothing about it** — so "gated: manual" understates by one whole instrument, and a manifest field that records only the platform's gate state would be wrong | [§12](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability) |
| **The mid-October test is "does the 1080p counter fall sharply"** *(this document, setting its own test three sweeps ago)* | **An absolute fall is not evidence, because the whole portfolio drifts.** Eighteen counters read the same morning: **fourteen fell**, median about **−1.3%**. Against that basket the 1080p corpus moved **−1.3% — exactly the median, indistinguishable from platform drift** — while **256p rose +3.4%**, second-largest gain of eighteen. **A ratio survives platform-wide drift; a level does not.** The test is restated: the burst is confirmed only if 1080p falls sharply **relative to the basket median**. *A tenth reading a day apart would have shown 256p up 3.4% and been written up as demand; the control is the only reason that sentence is not in this document* | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **A vendor's advertisement outlives its documentation** *(the survey's standing complaint — stale cards, dead project pages)* | **Here it inverted.** `nexdata.ai/datasets/embodied-ai/2145`, the catalogue listing for the "10000-Hour Egocentric Full-Body Multimodal Dataset", now **404s** while the category page above it and the site root return **200** — a withdrawn listing, not an outage. **The Hugging Face repo is untouched**: three files, no video, **no licence field**, still named for ten thousand hours. **The one surface that could have said what the hours cost and on what terms is the one that vanished** | [§12](#the-other-thing-that-happened-to-hours-they-went-on-sale) |
| **Two hub counters can be compared if you caveat them** | **They cannot, and here is the reading that shows it rather than asserting it.** `Xspark-HumanTouch` on ModelScope went **2,584,370 → 2,616,769 in about twenty-four hours (+32,399)** while the **same corpus's** Hugging Face counter **fell, 12,285 → 11,104**, over the same interval. A corpus with **one like** does not gain thirty-two thousand downloaders in a day; across **88,085 files**, file-level counting explains it and nothing else needs to | [§2](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform) |
| **DROID has 86 tasks** *(this document, from the project page)* | **The paper says 84, at both v1 and v2.** The project page says 86. Same team, two surfaces published a year apart, and this document took the one that was not the paper. Small in magnitude and exactly the *cite the figure with its sentence* discipline [Ego-Exo4D](#ego-exo4d) already forced — corrected to 84 with the discrepancy left visible rather than one silently chosen | [§1](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it) |
| **The most-cited robot corpus in this survey has an entry** *(this document, for eighty-two sweeps)* | **It had a table row.** DROID is named **thirty times**, is the denominator the 23× scarcity claim divides by, and had no write-up at all. **A survey should not run its central comparison against a corpus it never opened** — now written up from source: 76 k trajectories / 350 h, 564 scenes, 50 collectors, 13 institutions, 12 months, 1,417 calibrated viewpoints, language on **95% of successful episodes** where successful is **75 k of 76 k** | [§1](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it) |
| **DROID states no terms, so the field is simply empty** | **Eleven other parties have filled it, with at least five different licences** — `apache-2.0` (`cadene/droid` 91,575; `lerobot/droid_1.0.1`; `allenai/MolmoAct2-DROID-Dataset`), `mit` (`Salesforce/3d_optical_flow_droid`, 86,562), **`openmdw-1.1`** (`nvidia/Cosmos3-DROID`, a licence family appearing nowhere else here), `other`, and **four copies with no licence field at all**. `droid-dataset/droid` has **no `LICENSE`** — the raw URL 404s. **A team that pulls "DROID" gets one of five licences depending which of eleven artefacts they clicked** | [§1](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it) |
| **The `Cherrytest` licence divergence was a one-off** *(what a single instance supported)* | **Second instance, same mechanism.** `lerobot/droid_100` is **`mit` on Hugging Face and `Apache License 2.0` on ModelScope** — same org, same repository name, and the ModelScope record is again `CreatedBy: Cherrytest`. **One occurrence is an anecdote; two make it a behaviour of the mirroring path**, which is that the licence field gets re-typed by whoever moves the bytes. Both DROID divergences are permissive-to-permissive, so nothing restrictive is dropped — **which is why it is worth recording here**: the mechanism is visible in the harmless case, and the EgoDex re-uploads show it in the harmful one | [§1](#droid--the-denominator-this-survey-leans-on-and-the-eleven-answers-other-people-give-for-it), [§11](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet) |
| **An uploader's licence field is a problem because publishers stay silent** *(this document's framing across four catalogued cases)* | **It is worse than that: a stamp can contradict a publisher who spoke clearly.** EgoDex is **CC-BY-NC-ND** — non-commercial, *no derivatives* — and two ModelScope copies carry **`Apache License 2.0`** at **814,750 combined downloads**. One names *"Apple's EgoDex"* in its own card and describes a **repack**; the other a **re-encode merged with EgoVid**. *No legal conclusion is drawn.* The pipeline consequence is the point: **a manifest recording "the terms as read at the artefact" faithfully records the wrong answer**, and only a field that also stores the resolved source URL survives it | [§11](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet) |
| **A personal namespace is the tell that a licence field is an uploader's** | **Not on a platform that lets a mirroring account publish into an organisation's namespace.** On ModelScope `OpenGVLab/InternVid` reads **`cc-by-nc-sa-4.0`** and `OpenGVLab/InternVid-Full` reads **`Apache License 2.0`**, on near-identical READMEs — while **both read `cc-by-nc-sa-4.0` on Hugging Face**. Both ModelScope records were **`CreatedBy: Cherrytest`**, as was `builddotai/Egocentric-10K`. **The cue that made the previous four detectable is absent, and the divergent field is the permissive one** — Apache-2.0 drops the non-commercial restriction *and* the share-alike obligation | [§11](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet) |
| **The survey's negatives are negative about one hub** *(this document, stating the limit last sweep and declining to fix it)* | 🟢 **Fixed, and they held.** Roughly two dozen names queried against ModelScope: **no artefact exists** for EgoScale, EgoCS-400K, EgoLive, World In Your Hands, SiMDex, EgoTac, OpenMMEgo, Egocentric-1M, DreamDojo's video, Project Kitchen, MEgoVista, UMI-Bridge, BinoGen, EgoMimic, FastUMI, EgoHumanoid, H-Tac, EgoTactile, EgoScaler, ACE-Ego-0, EgoInfinity, EgoAVFlow or EgoEngine. **The blind spot was real and the conclusions drawn through it survive it** — reported because a survey that announces a hole and never says what was in it has made the announcement do the check's work | [§11](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet) |
| **The prospective §13 base rate is four out of four** *(this document, from one week)* | **The next cohort broke it.** Of the two 17 Sep papers proposing data machinery, **BinoGen names no surface at all** (zero external URLs; *"we will release… upon publication"*) but **[TouchSight](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform) ships** — a project page that resolves and **~100 hours downloadable today**. **One out of two; the streak ends at five out of six.** Recorded prominently, because **a prospective test whose base rate only ever goes one way is not being run, it is being quoted** | [§13](#13-why-no-open-source-project-does-exactly-this) |
| **A publisher either states its dataset's terms or does not** | **It can state them on a different platform.** `chuqiaoLyu/Xspark-HumanTouch` is **CC-BY-NC-4.0 on ModelScope** and has **`cardData: null`, no licence field, on Hugging Face** — same publisher, same corpus, same README, whose licence section reads only *"the dataset licence is governed by the licence stated on the ModelScope repository page."* **A pointer instead of a licence, aimed at another hub.** Not *terms unstated*, not the adjacent-artefact trap, not an uploader stamp — **a seventh shape: the cross-platform licence pointer**, where the artefact you downloaded does not carry the terms you accepted | [§2](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform), [§11](#11-the-licence-trap) |
| **This survey's "not released" findings are findings about the world** *(this document, eighty sweeps of artefact checks)* | They are findings about **three surfaces** — Hugging Face, GitHub, and the paper's own pages. **ModelScope has never been queried**, and the first time it was, it held a ~100-hour tactile corpus with **2,584,370 recorded downloads** and a licence the Hub copy does not carry. Even the `arxiv:`-tag query installed the sweep before would not have found it. **Stated as a scope limit rather than fixed**, because fixing it means re-running every negative against a second index | [§11](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five) |
| **Tactile from ordinary video needs the glove out of the training pixels** — solved by choreography (EgoTactile's two-hand rig) | **Or by editing it out afterwards.** [TouchSight](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform) trains on **500 h of pressure-glove recordings**, then generatively **re-renders the gloved footage as bare-hand video while keeping the measured labels** (TwinTouch-20H, 20 h). **A fifth human-side tactile position**, and a claim of dense force *"from egocentric vision alone, without tactile instrumentation at capture time"* — ⚠️ with bare-hand generalisation reported as **qualitative**, and accuracy that *"improves consistently as glove supervision scales"*. The capture requirement moved to the supervision set; it did not vanish | [§2](#touchsight-and-humantouch--a-fifth-position-and-a-licence-that-lives-on-another-platform) |
| **EgoHumanoid's dataset terms are not stated, and its sample gives no scale figure** *(this document, 1 Sep 2026, in a sentence that names the artefact)* | [`OpenDriveLab/EgoHumanoid`](https://huggingface.co/datasets/OpenDriveLab/EgoHumanoid) carries **`license: apache-2.0`** in its YAML and as a Hub tag, is **ungated**, has **504 downloads**, and its README opens with an episode table. The card was last modified **6 Jun 2026** — three months before the sentence — so nothing moved. **A worse failure than the H-Tac miss**: there the artefact was never found; here it was found, named, and not opened. **Finding an artefact and reading it are two steps, and only the first leaves a trace in the prose** | [§2](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator) |
| **A release is a fair proxy for what a paper is about** | EgoHumanoid is titled *"…with **Robot-Free** Egocentric Demonstration"*; its released sample is **50 robot teleoperation episodes and 1 human episode**. The card is honest — it calls itself a smoke-test sample — but **the ratio in the artefact is the inverse of the ratio in the argument.** Its paper promises *"code and models"* under Apache 2.0 and its supplementary promises *"code and data"*; **the licence is attached to the promise that excludes the data**, and the card grants it anyway | [§2](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator) |
| **Nobody keeps a machine-readable index of this literature's licences and access states** *(this document's §11, implicitly, for eighty sweeps)* | **[`cy0307/awesome-egocentric-atlas`](https://huggingface.co/datasets/cy0307/awesome-egocentric-atlas) does** — MIT, ungated, **1,044 resources** as CSV with separate `license` and `status` columns, 3,333 downloads. Narrowed rather than dropped, because **the columns are empty**: licence blank or *"not specified"* in **85.6%**, `status: watch` in **69.5%**, and the filled 15% does not group (`MIT`/`mit`, `Apache-2.0`/`apache-2.0`). **The strongest §11 evidence here, precisely because it is not this document's own sample** | [§11](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five) |
| **An independent index would catch what one survey misses** | On the 21 rows this document can check at an artefact, the Atlas **agrees on 12 and is wrong on 9** — and the nine are **this document's own two failure modes**. It puts `cc-by-4.0` on **Open X-Embodiment's official page**, where the publisher states nothing and that stamp belongs to the `jxu124` mirror (**the uploader-stamp error**), and it records `watch`/no-licence for **SABER, H-Tac and EgoHumanoid**, whose releases sit in their authors' own namespaces (**the H-Tac shape**). It also invents **`apache-2.0` for `FastUMI-100K`**, whose card has `cardData: null`. **Two independent efforts, the same two failure modes, in some of the same places** — which is better evidence that they are structural than either effort's self-diagnosis | [§11](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five) |
| **Checking at the artefact is the discipline that catches missing releases** *(this document's standing rule since the H-Tac miss)* | It is not enough, because it still requires a human to decide where to look — and both this document and the Atlas failed exactly there. **Every release both had missed carries an `arxiv:` tag naming its own paper**, so the query *"list Hub artefacts tagged with this arXiv ID"* finds them with no judgement involved. Run over all 63 IDs it found three releases, the Atlas itself, and **confirmed eight not-released classifications that had been asserted from absence**. **The sharper rule: ask the artefact index, because it is the only party that knows what exists** | [§11](#awesome-egocentric-atlas--somebody-else-is-keeping-this-index-and-its-licence-column-is-empty-four-times-in-five) |
| **OpenWAM ships 20 Apache-2.0 model repos** *(this document, five sweeps stale)* | **46**, re-counted at the namespace 19 Sep 2026, alongside the same 6 datasets, **3 still with no licence tag**. The control row for *"open survives checking"* got more open while the survey quoted an old count — **a live value in a claim that reads like a property** | [§2](#openwam--the-first-project-here-whose-open-survives-being-checked) |
| **SABER's grocery footage was staged — a team "sent actors into stores with GoPros"** *(this document, for dozens of sweeps, as a load-bearing §13 example)* | The paper says the opposite and says it three times: *"human workers performing everyday retail tasks… in fully operational store conditions"*, *"all captured **without staging, scripting**, or teleoperation overhead"*, *"during natural shopping activity"* — and the vendor's page agrees (*"Every clip was recorded in a working environment"*, *"a head-mounted camera on the worker"*). The trigger was the paper's **"primary actors"**, used in the scene sense throughout. **The correction cuts against this document**: instrumenting people already doing the work is far cheaper than staging, so commissioned capture is cheaper than recorded here. What survives is the part that was never about cost — the purchase was the **synchronised second viewpoint**, not the footage | [§1](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of), [§13](#13-why-no-open-source-project-does-exactly-this) |
| **SABER's 10 K subset is "released publicly", so the restrictive licence is at least on something you can have** *(this document, quoting the paper rather than checking the artefact)* | `DreamVu/SABER-10K` is **`gated: auto`** behind four fields, its README is unreadable unauthenticated and its files **401**. **19 downloads, 0 likes** in five and a half months. The control rules the gate out as the cause: the same publisher's `PRISM-100K`, created eleven days earlier with the **same licence, same gate and same domain**, reads **360 downloads and 7 likes**. Both halves of a "partially released" corpus were gated, at different strengths | [§1](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of), [§11](#11-the-licence-trap) |
| **A paper that prints a URL for its dataset has told you where the dataset is** | SABER's *"The dataset can be accessed via the following link"* points at `dreamvu.ai/saber`, which **308s to a path that does not exist and lands on the vendor's homepage** — a page about a different corpus, where SABER appears once as a link back to the arXiv paper. **HTTP 200 throughout.** A 404 would have said the route was gone; a 200 on the front page says nothing is wrong. The corpus it was meant to reach is *"available under NDA"*. New shape, adjacent to [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address)'s release sentence with no address: **an address that resolves, to the wrong thing** | [§1](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of), [§11](#11-the-licence-trap) |
| **World In Your Hands has no repository and no download location; the only findable artefact is the arXiv entry** *(this document, four separate looks)* | 🔴 **Both URLs were on the paper's own title page.** v3 prints, under the author list: *"Project Page: `wiyh.tars-ai.com` · Code: `github.com/tars-robotics/World-In-Your-Hands`"*. The searches went to the hubs and to the paper's **body**; a `\thanks` footnote between the authors and the abstract is exactly what a keyword-driven read skips. **The index not being asked was the source itself** | [§2](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild) |
| **`tars-robotics/WIYH` is an untied candidate — one arXiv tag, one README sentence or one link from the paper would settle it** *(this document's ACE-Ego-0 rule, held for three sweeps)* | 🟢 **Settled by a fourth thing the rule did not list.** The publisher's own public API returns records named `worldcode_HS-2-…_s0_vlta_reorg_sample_1-2`; the Hugging Face card's worked example is that string with different digits, and `vlta` is the paper's own coinage. Add the camera names (`lf_chest_fisheye`, `ldr_hand_fisheye` — the Oracle Suite's optics) and the account matching the repo the paper cites. **The bar was right; it was written as three signals when what it is for is evidence a publisher could not have produced by accident** | [§2](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild) |
| **World In Your Hands is "doubly settled" as not-released, because the `arxiv:`-tag query finds nothing and the candidate card carries no tag** *(this document, sweep 80)* | 🔴 **That sentence contains its own refutation and was printed anyway.** A query keyed on a tag cannot establish absence for a publisher that does not tag. The corpus is partially released and the card is its. **The tag query stays the best instrument here for *finding* artefacts and is worth nothing for concluding they are absent** — a caveat the other seven negatives in that bullet now inherit | [§11](#the-second-index-queried-at-last--and-the-strongest-uploader-stamp-case-yet) |
| **A release promise is a fixed thing you can come back and check against** *(assumed by all five shapes in §13's promise family)* | 🔴 **It can be withdrawn.** WIYH **v4 (21 Sep 2026)** deletes *"All data and hardware design will be open-source"*, deletes the matching conclusion sentence, deletes **"Open-Source Ecosystem" from the title**, and deletes both URLs from the title page. Nothing was broken — an undated promise that is removed was never due. ⚠️ **And arXiv still serves v3's title and abstract on the landing page**, so the commitment is visible at the address a reader checks and absent from the paper | [§13](#13-why-no-open-source-project-does-exactly-this) |
| **OpenMMEgo outranks WIYH as the promise example because WIYH said it in the body and OpenMMEgo said it in the title** *(this document)* | **WIYH said it in the title too** — v3 was *"A Large-Scale **and Open-Source Ecosystem** for…"*. The ranking survives on a better reason than the one given: **OpenMMEgo cannot retract without renaming the project; WIYH did it in one resubmission** | [§2](#openmmego--open-weights-and-data-half-kept) |
| **Four dead links found this pass** *(this document's own link checker, 24 Sep)* | **Three were its own quoting** — two trailing backticks and a pair of strikethrough tildes swept into the URL, all 200 once stripped — and the fourth refuses `HEAD` and answers the range-`GET` fallback 200. **Two real failures, not six.** One of the three, `nexdata.ai/…/2145`, is a page this survey already wrote up once as withdrawn and retracted. The extractor now strips trailing markup | [§11](#11-the-licence-trap) |
| **The acquisition-and-annotation layer for egocentric data is not published** *(this section's claim, narrowed three times and still standing)* | 🔴 **Round four: [EgoSteer](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table) published the annotate stage in June 2026 and this survey found it in September.** EgoSmith the pipeline, **342.9 M frames of labels with a per-source licence table and a rehydration script**, **192 h of Apache-2.0 real-robot teleoperation**, and **two Apache-2.0 VLA checkpoints**. Every standing check would have found it; none was pointed there. What survives is the join: EgoSmith's input is twelve corpora *already known to be egocentric* | [§13](#13-why-no-open-source-project-does-exactly-this) |
| **Ten free hours buy about one robot hour** *(this document, deriving a constant from Zeva-Ego's single cut)* | 🔴 **The discard term is not a constant.** EgoSmith keeps **288 of the same 10,000 hours (2.9%)** where Zeva keeps **4,439 (44.4%)** — **fifteen-fold**, on identical input, because the objectives differ (*"to filter out highly repetitive videos, we subsample"*). **The usable fraction of a free corpus is a property of the selection, not the corpus**, and this figure should have been printed as Zeva's exchange rate rather than the field's | [§12](#egocentric-10k), [§2](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table) |
| **A per-source licence column is what a derived corpus ought to ship, and nobody does** *(this document's §11, implicitly, across seven catalogued failure modes)* | 🟢 **`EgoSteer/EgoSteer-Egocentric` ships two** — source licence *and* labels licence, per folder, with `LICENSES/<source>/LICENSE.txt` and `NOTICE.txt` vendored alongside. ShareAlike propagates, both NC sources stay NC, and Ego4D-derived labels are NC against a source licence that is a bilateral agreement. **The first artefact here that answers §11 rather than illustrating it** — ⚠️ with one cell that is an argument, not a reading: `egodex/` releases **CC-BY-NC-4.0** labels estimated from **CC-BY-NC-ND-4.0** video | [§11](#11-the-licence-trap), [§2](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table) |
| **A project's released artefact is the corpus its paper describes** | **Not here, and neither document says otherwise.** EgoSteer's paper reports **1.04 B frames** over 12 sources; its labels release holds **342.9 M** over 8, with **Ego4D nearly 8× larger** in the release and **Egocentric-100K a quarter the size**. Not alleged as an error — recorded because *"count artefacts, not papers"* applies to projects that **did** release, not only to ones that did not | [§2](#egosteer-and-egosmith--the-annotate-stage-released-with-a-per-source-licence-table) |

> **The pattern in the left column is worth naming.** Almost every row is a
> *scale* or a *licence* claim, and almost every one fails in the same
> direction: the circulating number is larger, freer or more available than the
> source supports. Nobody is lying; headline figures travel and caveats do not.
> Which is the argument for recording provenance per clip rather than per
> corpus — a manifest that carries the source, the terms and the date is the
> only thing that survives this kind of drift.

## Positioning, in one table

| | Commissioned capture (Ego-Exo4D, EgoDex) | Web-scale corpora (Panda-70M, InternVid, HumanNet) | World-model stacks (Cosmos) | **Internet2EgoExo** |
|---|---|---|---|---|
| Where footage comes from | Recorded for the dataset | Scraped at scale, then filtered | Owned archive + synthesis | Searched on demand, per requirement |
| Selection signal | Protocol compliance | Heuristics, captionability | Dynamics / visual quality | Viewpoint → duration → licence |
| Wrong viewpoint | Cannot happen | Down-ranked | Not modelled | **Dropped** |
| No hands in frame | Rare by design | Kept | Kept | **Dropped, no override** |
| Rights | Consented at capture | Deferred to the user | Owned | Filtered and recorded per clip |
| Unit of output | A dataset release | A corpus | Synthetic hours | A manifest + a cost per hour |
| Auditability | Annotation guidelines | Pipeline code — for Panda-70M and InternVid, though InternVid's terms are CC BY-NC-SA. **HumanNet released none**, nor a source breakdown or ego/exo split | Evaluator scores | Per-clip Thought → Action → Observation trace |

> **The middle column is where the real comparison sits now**, and
> [HumanNet](#humannet) is the entry to read it against rather than Panda-70M.
> It is the one project that has done what this repo does — mine the open web
> for human video against a requirement, at a million hours — and the row that
> separates them is not scale, ambition or method. It is the last one. A
> manifest that traces each clip to its source, its terms and the evidence for
> its viewpoint is the whole difference between a corpus someone assembled and a
> corpus someone else can check.

---

## References

### Part I — datasets and models

- Grauman et al. *Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives.* CVPR 2024. https://arxiv.org/abs/2311.18259
- *HD-EPIC: A Highly-Detailed Egocentric Video Dataset.* CVPR 2025. (41 h, 59,454 actions, 7.7 M hand masks, digital twins; **CC BY-NC 4.0**, stated on the dataset's own page) https://hd-epic.github.io/site · https://arxiv.org/abs/2502.04144
- Meta / Project Aria. *Nymeria: A Massive Collection of Multimodal Egocentric Daily Motion in the Wild.* (300 h activity / 3,600 h video / 264 participants; **CC BY-NC 4.0**, email-gated; superseded by **NymeriaPlus**; EgoBlur applied to faces and licence plates, consent from participants and home owners) https://www.projectaria.com/datasets/nymeria/
- Grauman et al. *Ego4D.* https://ego4d-data.org/
- Damen et al. *Scaling Egocentric Vision: The EPIC-KITCHENS Dataset.* https://arxiv.org/pdf/1804.02748
- Huang et al. *EgoExoLearn.* CVPR 2024. https://github.com/OpenGVLab/EgoExoLearn
- *HOI4D.* (CC BY-NC 4.0) https://arxiv.org/pdf/2404.09933 · https://hoi4d.github.io/
- Shi et al. (OpenDriveLab). *EgoHumanoid: Unlocking In-the-Wild Loco-Manipulation with Robot-Free Egocentric Demonstration.* RSS 2026, arXiv:2602.10106 (v2, 4 Jun 2026). (Apache 2.0 on the code; **no dataset licence stated**) https://arxiv.org/abs/2602.10106 · https://github.com/OpenDriveLab/EgoHumanoid
- Kolev, Ma, Goesele, De Nardi, Engel (Meta Reality Labs). *Beyond Gestures: Estimating Full Hand Pose and Contact Forces from Wrist-Worn Pressure Sensor Array.* arXiv:2609.16518. (4.6° finger-joint MAE; per-finger force R²=0.57, 0.75 with external pose; **no repository, dataset, project page or licence named**) https://arxiv.org/abs/2609.16518
- Li, Zhu, Wang, Chen, Liu. *From Gameplay to Policy: Towards Scalable Robot Data Collection via Gamified Robot-Free Interaction* (**Project Kitchen / Game2Policy**). arXiv:2609.18650. (+10.0 pts sim, +18.3 pts real, few-shot; **nothing named**) https://arxiv.org/abs/2609.18650
- Xiao, Zhang, Dong, Ma, Jin. *MEgoVista: Multi-view Ego-aware Motion Estimation for Metric 4D Hands and Head in the Wild.* arXiv:2609.16684. (metric gauge from calibrated stereo; hand ownership settled at detection; scored against independent Chingmu optical capture; **nothing named**) https://arxiv.org/abs/2609.16684
- Liu, Ma, Rui, Wei, Ma. *UMI-Bridge: Action-Anchored Latent Alignment across Human and Robot Manipulation Data.* arXiv:2609.18232. (**91.7% vs 73.3%** against naive co-training; beats full-data robot-only with 25% of robot demos; **nothing named**) https://arxiv.org/abs/2609.18232
- *OmniVTA / OmniViTac: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation.* arXiv:2603.19201 (v3). (21,000+ trajectories, 86 tasks, 100+ objects; dataset **CC BY-NC 4.0**, ungated, 27,810 downloads — **card is licence front-matter and nothing else**) https://arxiv.org/abs/2603.19201 · https://huggingface.co/datasets/tars-robotics/OmniVitac
- *EgoTactile: Learning Grasp Pressure for Everyday Objects from Egocentric Video.* ICML 2026 Spotlight, arXiv:2606.09243. (dataset **CC BY-NC 4.0**, ungated) https://arxiv.org/abs/2606.09243 · https://egotactile.github.io/ · https://huggingface.co/datasets/HustleHard/EgoTactile
- *ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios.* (**dataset terms not stated anywhere** — the CC BY 4.0 is the arXiv listing's, covering the manuscript) https://arxiv.org/html/2603.09741v2 · project page https://iplab.dmi.unict.it/ENIGMA-360 **has now failed six checks — HTTP 500, a connection failure, then HTTP 403 four times running (latest 15 Sep 2026, with and without a trailing slash) — while the lab host root returns 200 each time. Four identical 403s in a row is not a flapping server; it is a settled block on that path, and the entry is reclassified from *unstable* to **gone**. Cite the arXiv HTML**
- *SABER: A Scalable Action-Based Embodied Dataset for Real-World VLA Adaptation.* DreamVu. (10 K-sample subset **CC BY-NC 4.0 and `gated: auto`, 19 downloads**; full corpus **"available under NDA"**; the paper's `dreamvu.ai/saber` access URL **redirects to the vendor homepage**) https://arxiv.org/html/2605.09613v1 · https://huggingface.co/datasets/DreamVu/SABER-10K
- Rouhi & Sakurikar et al. *PRISM: A Multi-View Multi-Capability Retail Video Dataset for Embodied Vision-Language Models.* DreamVu. (270 K samples, ego + exo + 360° across **five supermarket locations**, ~11.8 M frames; `DreamVu/PRISM-100K` **CC BY-NC 4.0, `gated: auto`, 360 downloads**) https://arxiv.org/abs/2603.29281 · https://huggingface.co/datasets/DreamVu/PRISM-100K
- *EgoDex: Learning Dexterous Manipulation from Large-Scale Egocentric Video.* (CC-BY-NC-ND) https://arxiv.org/abs/2505.11709 — **current version is v3 (9 Mar 2026); the `v1` link is cited deliberately where the licence is quoted**, because v3 no longer states it: https://arxiv.org/html/2505.11709v1
- Yoshida, Kurita, Nishimura, Mori (Kyoto Univ. / NII / Inst. of Science Tokyo / Sony Interactive Entertainment). *Developing Vision-Language-Action Model from Egocentric Videos* (**EgoScaler**, **not** EgoScale). arXiv:2509.21986. (dataset and model both **Apache-2.0**, ungated, 27,912 downloads; built from Ego4D / Ego-Exo4D / HD-EPIC / Nymeria, whose terms the card does not state) https://arxiv.org/abs/2509.21986 · https://huggingface.co/datasets/Biscue5/egoscaler-v2
- *EgoTactile-OXT.* (CC BY-NC 4.0, ungated — EgoTactile in Open X-Embodiment format) https://huggingface.co/datasets/HustleHard/EgoTactile-OXT
- *H-Tac release sample.* (**MIT** `LICENSE`, ungated — 98 episodes / 35,982 frames; HOI-Tac not included) https://huggingface.co/datasets/BeingBeyond/H-Tac_Sample
- *EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data.* GEAR @ NVIDIA Research. (code "coming soon"; no licence stated) https://arxiv.org/abs/2602.16710 · https://research.nvidia.com/labs/gear/egoscale/
- Deng, Zhou et al. *HumanNet: Scaling Human-centric Video Learning to One Million Hours.* https://arxiv.org/abs/2605.06747
- *Ego2Robot: Scalable Robot Data Synthesis from Egocentric Human Data.* https://arxiv.org/html/2608.02580
- Li, Deng, Liang et al. (Microsoft). *Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos* (**ViTRA**). arXiv:2510.21571. (dataset and model both **MIT**, ungated — **annotations only, no video**; built from Ego4D / EPIC-KITCHENS / Ego-Exo4D / Something-Something V2, whose terms the card does not state) https://arxiv.org/abs/2510.21571 · https://microsoft.github.io/VITRA/ · https://huggingface.co/datasets/VITRA-VLA/VITRA-1M · https://github.com/microsoft/VITRA
- *EgoEngine: From Egocentric Human Videos to High-Fidelity Dexterous Robot Demonstrations.* https://arxiv.org/html/2606.12604v1 · https://egoengine.github.io
- *EgoMimic: Scaling Imitation Learning via Egocentric Video.* (code **MIT**; the HF *sample* dataset is ungated with **no card and no stated terms**) https://arxiv.org/abs/2410.24221 · https://github.com/SimarKareer/EgoMimic · https://huggingface.co/datasets/gatech/EgoMimic
- *EgoAVFlow: Robot Policy Learning with Active Vision from Human Egocentric Videos via 3D Flow.* (CC BY 4.0; head-mounted RealSense D435 RGBD plus a ChArUco board per scene; 150 videos × 4 tasks; no dataset release stated) https://arxiv.org/html/2602.22461v1
- *EgoWAM: World Action Models Beyond Pixels with In-the-Wild Egocentric Human Data.* (CC BY 4.0; "in-the-wild" = EgoVerse on Project Aria, flow from Aria VIO poses) https://arxiv.org/abs/2607.08436
- *EgoHumanoid: humanoid loco-manipulation from egocentric human demonstrations.* RSS 2026. (code **Apache 2.0**; dataset terms not stated; PICO VR headset + 5 body trackers + ZED Mini depth) https://github.com/OpenDriveLab/EgoHumanoid
- *EgoSteer: A Full-Stack System Towards Steerable Dexterous Manipulation from Egocentric Videos.* (v1, 21 Jun 2026; PKU Institute for AI + PKU–PsiBot Joint Lab. **EgoSmith** pipeline → **9,606 h / 2,290,861 episodes / 1.04 B frames** across 12 corpora, **83.8% Egocentric-100K, 86.8% Build AI's free hours**; 🟢 **everything permissive and ungated** — labels `EgoSteer/EgoSteer-Egocentric` under a **per-source licence table**, real-robot `EgoSteer/EgoSteer-RealWorld` **Apache-2.0, 192 h / 54,454 episodes / 193 tasks**, models `EgoSteer-3B-Base` and `-3B-RealMan` **Apache-2.0**; ⚠️ the released labels are a **different cut** from the paper's corpus, and `egodex/` labels drop the source's **ND**) https://arxiv.org/abs/2607.09701 · https://egosteer.github.io/
- *World In Your Hands: A Large-scale Ego-centric Dataset for Learning Robotic Manipulation In the Wild.* (1,045 h captured, **600 h annotated**; Oracle Suite wearable; paper states **terms** — research only, commercial use restricted, Appendix E — and **no instrument**; artefact `tars-robotics/WIYH`, **CC BY-NC 4.0**, ungated, **tied to the paper this sweep**; project page gated by registration, `Full` tier *"Coming soon"*) https://arxiv.org/abs/2512.24310 — **current version is v4 (21 Sep 2026), which dropped "Open-Source Ecosystem" from the title and every open-source promise from the body; the arXiv metadata still serves v3's title and abstract**: https://arxiv.org/html/2512.24310v4
- *OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation.* (1,107 h unifying six public datasets; **annotations only, per-source licence and attribution shipped as `ATTRIBUTION.md`**; code MIT, data release in progress) https://arxiv.org/html/2509.05513v1 · https://www.openegocentric.com · https://github.com/ahadjawaid/openego
- *EgoCS-400K: An Egocentric Gameplay Dataset for World Models.* (**dataset terms not stated** — CC BY 4.0 is the arXiv listing's; 400 K+ videos / 10,000+ h rendered from public HLTV match demos) https://arxiv.org/html/2606.18180v1 · https://EgoCS-400K.github.io
- *ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretraining.* https://arxiv.org/html/2606.17200v1 (the project URL printed in the paper 404s)
- *Open-AoE: An Open Egocentric Manipulation Dataset and Toolchain for Embodied Learning.* (dataset **`license: other` / `open-aoe-dataset-license`** — bespoke, on `inclusionAI/OpenAoE-2000h`; the CC BY 4.0 is the arXiv listing's) https://arxiv.org/abs/2607.14183 · https://huggingface.co/datasets/inclusionAI/OpenAoE-2000h
- *EgoVerse: An Egocentric Human Dataset for Robot Learning from Around the World.* https://arxiv.org/abs/2604.07607
- *EgoKit: Towards Unified Low-Cost Egocentric Data Collection with Heterogeneous Devices.* (toolkit; no dataset) https://arxiv.org/pdf/2605.16797
- *MobileEgo Anywhere: Open Infrastructure for long-horizon egocentric data on commodity hardware.* (CC BY 4.0) https://arxiv.org/pdf/2605.05945
- Ego-Exo4D documentation (source of the 1286.30 h / 221.26 ego-h / 5035 takes figures). https://docs.ego-exo4d-data.org/
- *EgoLive: A Large-Scale Egocentric Dataset from Real-World Human Tasks.* (**dataset terms not stated anywhere**; the CC BY 4.0 once recorded here is the arXiv listing's) https://arxiv.org/html/2604.23570v1
- *From Human Videos to Robot Manipulation: A Survey.* https://arxiv.org/html/2606.00054v1
- Wang, Huang, Ko, Bai, Jiang. *ReWeight: Leveraging Human Data for VLA Post-Training via Demonstration Retrieval and Sample Weighting.* arXiv:2609.13851. (**nothing released**; the project page's only artefact link points at another project's Hugging Face collection) https://arxiv.org/abs/2609.13851 · https://reweight-vla.github.io/
- Zhu, Cai, Wang et al. *MINT: A Unified Model for World-Space Camera and Hand Motion Estimation from Scalable Egocentric Pipeline Supervision.* arXiv:2609.04958 (v2). (**states "we release the model, training and inference code, labeling pipeline, and a curated 1,021-hour egocentric trajectory dataset" and gives no URL anywhere in the paper** — recorded as *not locatable*) https://arxiv.org/abs/2609.04958
- Wang, Huang, Li et al. *OpenWAM: An Open, Modular Exploration Towards Systematic World-Action Model Pretraining.* arXiv:2609.07398. (✅ **46 Apache-2.0 model repos — 20 when first counted, re-counted 19 Sep 2026 — 6 datasets, Apache-2.0 code; all three named surfaces resolve**; the ~6,400 h pretraining corpus is not among them, and 3 of 6 datasets carry no licence tag) https://arxiv.org/abs/2609.07398 · https://github.com/OpenWAM-Official/OpenWAM · https://huggingface.co/OpenWAM · https://openwam-official.github.io/
- *SiMDex: Mining Similar Egocentric Videos for Cross-Embodiment Dexterous Manipulation.* (**nothing released** — the project page's Code and Hugging Face buttons are inert `href="#"` links; no licence stated) https://arxiv.org/abs/2608.04196 · https://lin-nie.github.io/SiMDex/
- Chen et al. *Panda-70M: Captioning 70M Videos with Multiple Cross-Modality Teachers.* CVPR 2024. https://github.com/snap-research/Panda-70M
- Wang et al. *InternVid.* https://arxiv.org/abs/2307.06942
- NVIDIA. *Cosmos World Foundation Model Platform for Physical AI.* https://arxiv.org/abs/2501.03575
- NVIDIA. *NeMo Curator.* https://github.com/NVIDIA-NeMo/Curator
- NVIDIA. *DreamDojo: A Generalist Robot World Model from Large-Scale Human Videos.* ICML 2026. (code Apache 2.0; **weights `nvidia-open-model-license`** at https://huggingface.co/nvidia/DreamDojo; video terms still unstated) https://arxiv.org/html/2602.06949 · https://github.com/NVIDIA/DreamDojo
- Luo, Yue, Zhang, Feng, Zheng, Ye, Lu (BeingBeyond). *OpenMMEgo: Enhancing Egocentric Understanding for LMMs with Open Weights and Data.* NeurIPS 2025. (repo **MIT**; **OME10M and OMEBench not released** — *"We will release our code and data soon"*) https://github.com/BeingBeyond/OpenMMEgo
- BeingBeyond Team. *Being-H0.7: A Latent World-Action Model from Egocentric Videos.* arXiv:2605.00078 (v1, 30 Apr 2026). (**no code or dataset licence stated in the paper**; pretrained on UniHand 2.0) https://arxiv.org/html/2605.00078v1 · https://research.beingbeyond.com/being-h07
- Luo et al. (BeingBeyond). *Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization.* arXiv:2601.12993, 19 Jan 2026. (code Apache-2.0; UniHand_Preview released with **no stated licence**; full UniHand-2.0 unreleased) https://arxiv.org/html/2601.12993v1 · https://github.com/BeingBeyond/Being-H · https://huggingface.co/datasets/BeingBeyond/UniHand_Preview
- Meta Reality Labs. *Ego-1K: A Large-Scale Multiview Video Dataset for Egocentric Vision.* (dataset **`fair-noncommercial-research-license`**, ungated, on `facebook/ego-1k`; the CC BY 4.0 is the arXiv listing's) https://arxiv.org/html/2603.13741v1 · https://huggingface.co/datasets/facebook/ego-1k
- *HoloAssist.* (CDLA v2) https://holoassist.github.io/
- Chi et al. *Universal Manipulation Interface (UMI).* (hand-held gripper + GoPro; code and hardware **MIT**) https://umi-gripper.github.io/ · https://github.com/real-stanford/universal_manipulation_interface
- *FastUMI: A Scalable and Hardware-Independent Universal Manipulation Interface with Dataset.* arXiv:2409.19499. (dataset **MIT**, gated, 3,034 downloads) https://arxiv.org/abs/2409.19499 · https://huggingface.co/datasets/IPEC-COMMUNITY/FastUMI-Data
- *FastUMI-100K: Advancing Data-Driven Robotic Manipulation with a Large-Scale UMI-Style Dataset.* arXiv:2510.08022. (**100 K+ trajectories, 54 tasks**; ungated, **269,342 downloads**, 🔴 **no licence field** — a thorough README with no YAML front-matter) https://arxiv.org/abs/2510.08022 · https://huggingface.co/datasets/IPEC-COMMUNITY/FastUMI_100k_lerobot
- *RealDexUMI: A Wearable Universal Manipulation Interface for Dexterous Robot Learning.* arXiv:2606.06033 (v2). (**"zero-gap end-effector data"** — shared dexterous hand, in-hand vision, fingertip tactile; no artefact found) https://arxiv.org/abs/2606.06033
- *TacUMI: A Multi-Modal Universal Manipulation Interface for Contact-Rich Tasks.* arXiv:2601.14550. (ViTac + force-torque + pose tracker; no licence) https://arxiv.org/abs/2601.14550
- *DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset.* https://droid-dataset.github.io/
- Wu et al. *RoboCOIN.* arXiv:2511.17441. (**956 h, 15 embodiments**; `license: apache-2.0` **plus gate obligations Apache-2.0 does not contain** — citation required, no experiments harming human subjects; shipped as 100+ per-task datasets, all `gated: auto`, 59,642 monthly downloads in aggregate) https://huggingface.co/RoboCOIN
- Tian et al. *InternData-A1.* arXiv:2511.16651. (**2,904 h simulation**; **CC BY-NC-SA 4.0 stated only inside the gate prompt** — the card carries no `license:` tag; 90,872 downloads. An ungated third-party LeRobot conversion tags the terms correctly at 24,586 downloads) https://huggingface.co/datasets/InternRobotics/InternData-A1 · https://huggingface.co/datasets/griffinlabs/InternData-A1-LeRobot-v3.0-by-embodiment
- *AgiBotWorld-Beta.* (CC BY-NC-SA 4.0, gated) https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta
- *Open X-Embodiment.* (no licence stated on the project page) https://robotics-transformer-x.github.io/
- EGXO Data. *Robotics Data Release Tracker 2026.* (third-party tracker, v1.1.1, last updated 2026-07-25 — useful for monitoring, but it collapses licence and access; verify at the publisher. ⚠️ **Also a data vendor**: `egxodata/egxo-household-egocentric-video-evaluation` is gated under a bespoke `egxo-controlled-commercial-access` licence — the tracker is not a disinterested source) https://egxodata.com/resources/robotics-data-release-tracker-2026
- Memories.ai Research. *OmniRetriever: Any-to-Any Audio-Video-Text Retrieval via Fusion-as-Teacher Distillation.* (bench and LoRA adapter both **Apache-2.0**, ungated; training corpus not released) https://arxiv.org/abs/2605.26641 · https://huggingface.co/datasets/YunzeLiu/OmniRetriever-Bench · https://huggingface.co/YunzeLiu/OmniRetriever-7B
- *S-EMBER: A Large-Scale Benchmark for Streaming Egocentric Memory Retrieval.* FAIR, Meta. (3,141 videos / **388 h** / 9,448 QA pairs; dataset **CC BY-NC 4.0, gated**; code **MIT**; the arXiv HTML's CC BY 4.0 covers the manuscript only) https://arxiv.org/abs/2607.02689 · https://github.com/facebookresearch/S-EMBER · https://huggingface.co/datasets/facebook/S-EMBER
- Ropedia. *Xperience-10M.* (gated, non-commercial) https://huggingface.co/datasets/ropedia-ai/xperience-10m · release note: https://ropedia.com/blog/20260316_xperience_10m · critique: https://technologies.org/ropedia-raises-30-million-for-physical-ai-training-data-but-the-dataset-math-doesnt-hold-up/

### Part II — pipeline and tooling

- LAION. *video2dataset.* (MIT) https://github.com/iejMac/video2dataset · https://laion.ai/blog/video2dataset/
- LAION. *BVD.* (research only) https://github.com/LAION-AI/BVD
- *yt-fts.* (Unlicense; abandoned) https://github.com/NotJoeMartinez/yt-fts
- *YT_crawler.* (MIT) https://github.com/luc-pimentel/YT_crawler
- Miech et al. *HowTo100M: Learning a Text-Video Embedding by Watching Hundred Million Narrated Video Clips.* ICCV 2019. (136 M clips / 1.2 M YouTube videos; **no dataset licence stated**; repo releases training, evaluation, a pretrained model and feature extraction — **not the acquisition pipeline**) https://www.di.ens.fr/willow/research/howto100m/ · https://github.com/antoine77340/howto100m
- Xue et al. (Microsoft). *Advancing High-Resolution Video-Language Representation with Large-Scale Video Transcriptions (HD-VILA-100M).* CVPR 2022. (103 M clips / 3.3 M videos / 371.5 K h, all 720p; **URLs only**, under the **Open Use of Data Agreement**) https://arxiv.org/abs/2111.10337
- Luo et al. *Exocentric-to-Egocentric Video Generation (Exo2Ego-V).* NeurIPS 2024. https://github.com/showlab/Exo2Ego-V · https://proceedings.neurips.cc/paper_files/paper/2024/hash/f5a8b5e5d007e66c929b971c2bc21d76-Abstract-Conference.html
- Alibaba DAMO Academy. *RynnVLA-001.* ICRA 2026. https://github.com/alibaba-damo-academy/RynnVLA-001 · https://arxiv.org/pdf/2509.15212
- Wang et al. *EgoInfinity: A Web-Scale 4D Hand-Object Interaction Data Engine.* Rice University. https://arxiv.org/abs/2606.17385 · https://github.com/Rice-RobotPI-Lab/EgoInfinity
- *Panda-70M splitting module.* https://github.com/snap-research/Panda-70M/blob/main/splitting/README.md
- NVIDIA. *cosmos-curate.* (code Apache 2.0) https://github.com/nvidia-cosmos/cosmos-curate
- *Action100M.* (dataset **`fair-noncommercial-research-license`** on `facebook/action100m-preview`, a *preview* subset; the CC BY 4.0 is the arXiv listing's) https://arxiv.org/html/2601.10592v1
- Microsoft. *VLM-Video-Action-Localization.* https://microsoft.github.io/VLM-Video-Action-Localization/
- Nexdata. *10000-Hour Egocentric Full-Body Multimodal Dataset.* (**no licence field**; the Hugging Face repo holds three files and no video — *"available upon request"* — and 🔴 **the vendor catalogue page below now returns 404 as of 21 Sep 2026**, while the category page above it and the site root return 200) https://huggingface.co/datasets/Nexdata-AI/10000-Hour-Egocentric-Video-Dataset · ~~https://www.nexdata.ai/datasets/embodied-ai/2145~~
- UniDataPro. *Egocentric video dataset.* (**CC BY-ND 4.0** — commercial use permitted, **derivatives forbidden**) https://huggingface.co/datasets/UniDataPro/egocentric-video
- Humyn Labs. *APAC/LATAM Egocentric sample sets.* (CC BY 4.0, ungated, `n<1K`) https://huggingface.co/datasets/humyn-labs/APAC-Egocentric-Stereo-Labeled
- World Data Labs. *Egocentric Manufacturing.* (`license: other`, manually gated) https://huggingface.co/datasets/Worlddatalabs/egocentric-manufacturing
- Build AI. *Egocentric-10K.* (Apache 2.0) https://www.humanoidsdaily.com/news/build-ai-open-sources-10-000-hours-of-factory-worker-video-to-scale-robot-learning · subset: https://huggingface.co/datasets/Voxel51/Egocentric_10K_subset
- *annotated-egocentric-10k-dataset.* (Apache 2.0) https://github.com/fit-alessandro-berti/annotated-egocentric-10k-dataset
- *EgoVid-5M: A Large-Scale Video-Action Dataset for Egocentric Video Generation.* (inherits Ego4D terms) https://arxiv.org/abs/2411.08380 · https://github.com/JeffWang987/EgoVid
- *awesome-egocentric-vision.* https://github.com/Sid2697/awesome-egocentric-vision
- *awesome-temporal-action-segmentation.* https://github.com/nus-cvml/awesome-temporal-action-segmentation
