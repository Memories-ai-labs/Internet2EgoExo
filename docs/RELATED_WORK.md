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
  - [Ego4D](#ego4d)
  - [Ego-Exo4D](#ego-exo4d)
  - [EgoExoLearn](#egoexolearn)
  - [HOI4D](#hoi4d)
  - [HoloAssist](#holoassist)
  - [Ego-1K](#ego-1k)
  - [ENIGMA-360](#enigma-360)
  - [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
  - [Ego-OSCAR](#ego-oscar--capture-at-200-and-a-fifth-licence-shape)
- [2. Scaling human video for robot learning](#2-scaling-human-video-for-robot-learning)
  - [The robot-native denominator](#the-robot-native-denominator)
  - [EgoDex](#egodex)
  - [EgoScale](#egoscale)
  - [EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)
  - [HumanNet](#humannet)
  - [Ego2Robot](#ego2robot)
  - [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)
  - [EgoEngine](#egoengine)
  - [EgoMimic](#egomimic)
  - [EgoAVFlow](#egoavflow--no-robot-demonstrations-still-means-a-board-in-every-scene)
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
  - [LAION-BVD](#laion-bvd)
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
> and the derived artefact is the one with 30,436 downloads. **This is now the
> second fully traced case of a permissive stamp sitting on top of four
> non-permissive parents**, and unlike ViTRA's it has *zero* permissive parents
> rather than merely unstated ones.

### Ego4D

**[ego4d-data.org](https://ego4d-data.org/)** — 3,670+ hours of daily-life egocentric
video with a benchmark suite (episodic memory, forecasting, hand–object
interaction). Still the default pretraining corpus, and the base that
[EgoVid-5M](#egovid-5m) and much else is derived from.

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
card carries **`fair-noncommercial-research-license`**, ungated, **49,612
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

**Approximately 100 hours** of in-store footage, collected across *multiple*
real grocery stores — the paper says "multiple" and never gives a count.
Dual-stream capture: **ego on a head-mounted GoPro recording at 480p**, worn by
the primary actors; **exo on a DreamVu ALIA omnidirectional camera**, one fixed
unit supplying "six calibrated and synchronized wide-angle views that span the
full surround environment." Actors perform the full shopping and stocking
workflow — stocking shelves, retrieving items, navigating aisles — in
operational stores, with no robot hardware present during collection.

What ships is not hours but retargeted action: **44.8 K training samples** in
three streams — **25 K** LAPA-style latent action sequences, **18.6 K**
dexterous hand-pose trajectories retargeted to robot joint space via
Dex-Retargeting, and **1.2 K** whole-body SMPL sequences retargeted to a
humanoid. Post-trained into GR00T N1.6, it reports a **29.3% mean success rate
across ten retail manipulation tasks against a 13.4% fine-tuning baseline**,
about 2.19×.

**Licence — and the split that matters.** "A 10K-sample subset of SABER is
released publicly under a CC BY-NC 4.0 license" on Hugging Face
(`DreamVu/SABER-10K`); the full corpus is reachable only through the vendor's
own page. So: **less than a quarter of the samples, non-commercial, and the
rest behind a vendor gate.** A fourth shape for [§11](#11-the-licence-trap) —
not merely restrictive, unstated, or unreleased, but *partially* released, with
the restrictive licence attached to the part you can actually have.

**The catch, and it is the one this document keeps finding.** Grocery stocking
and shelf retrieval are among the most abundantly filmed activities on the open
internet — retail training footage, shift vlogs, body-cam and helmet-cam uploads.
A team that needed a hundred hours of it **sent actors into stores with GoPros
anyway**. The exocentric half explains part of that: a synchronised 360° view
from a calibrated fixed unit is not something found footage ever supplies. But
the egocentric half is ordinary head-mounted video, and it was still staged.

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

### The robot-native denominator

Several entries below argue that an hour of human video is worth more than an
hour of robot data. That claim is meaningless without knowing how big the robot
side actually is, and the answer is smaller than the rhetoric suggests.

| Corpus | Scale | How it was made | Licence |
|---|---|---|---|
| **[DROID](https://droid-dataset.github.io/)** | **350 hours**, 76,000 trajectories, 564 scenes, 86 tasks, 1,417 camera viewpoints | Teleoperation on a standardised rig (Franka Panda 7-DoF, two Zed 2 stereo + wrist Zed Mini, Quest 2 controllers), **13 institutions, 50 collectors, 12 months** | Open dataset; terms not stated on the project page |
| **[AgiBotWorld-Beta](https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta)** | **2,976.4 hours**, 1 M+ trajectories, 200+ task types, 87 atomic skills | **100 robots** — mobile dual-arm, 6-DoF dexterous hands, visual-tactile sensors; video, depth, joint positions/velocities/forces, end-effector state, odometry | 🔴 **CC BY-NC-SA 4.0**, **click-through gated (auto-approved)** — 86,157 downloads |
| **[Open X-Embodiment](https://robotics-transformer-x.github.io/)** | 1 M+ trajectories, **22 embodiments**, 527 skills, 160,266 tasks — **hours not stated** | **60 existing datasets pooled** from 34 labs across 21 institutions; single arms through bimanual robots and quadrupeds | 🔴 **No overall licence stated on the project page**, and no statement of whether the 60 components retain their own |
| Human ego, for scale | [Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) 100,405 h · [DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) 44,711 h | Crowdsourced / commissioned capture | Apache 2.0 / unstated |

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
**86,157 downloads** have passed through it. The distinction matters here more
than usual, because this is the document's own
[licence-versus-access](#11-the-licence-trap) grid: AgiBot sits in
*most-restrictive licence, near-frictionless access* — the same cell as
Egocentric-10K, whose terms are Apache 2.0. **The gate tells you nothing about
the terms in either direction.** *(A small staleness in their record, since this
document collects them: the agreement text on the **Beta** release is headed
"AgiBot World **Alpha** Release Date: December 30, 2024".)*

🔴 **DROID states its data terms nowhere — and a third-party copy states them
for it, to 149,039 downloads.** The project page has no licence. Neither does
the documentation site. The data repository `droid-dataset/droid` has **no
`LICENSE` file**; only the separate `droid_policy_learning` repo carries one,
**MIT**, and that governs *code*. Meanwhile
[`cadene/droid`](https://huggingface.co/datasets/cadene/droid) — a LeRobot
conversion in a **personal** namespace, tagged `openx` — is stamped
**`license: apache-2.0`**, ungated, and has been pulled **149,039 times**;
`lerobot/droid_1.0.1` repeats the Apache-2.0 at 16,640. **That is the fourth
instance of an uploader's licence field standing in for a publisher's silence**,
after `simon055/EgoVid_frames`, `jxu124/OpenX-Embodiment` and
`easpeeder/Egocentric-1M` — and by download count it is larger than the other
three together. *No non-compliance is alleged; Apache-2.0 may well be what DROID
intends.* **The point is that nobody downloading it can tell**, and the artefact
that answers loudest is the one whose author had no standing to answer.

**The ratios are the point.** Egocentric-100K is roughly **287× DROID** and **34×
AgiBotWorld-Beta**. The flagship open teleoperated dataset — thirteen
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
> *"[GitHub (Coming Soon!)]"* as of **9 Sep 2026**: **roughly seven months**, across
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
> EgoScaler's is released, Apache-2.0, and has been pulled 30,436 times.** A
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

**Terms.** `Biscue5/egoscaler-v2` is **Apache-2.0**, ungated, **30,436
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
**MIT**, **ungated**, 2,745 downloads; the model
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
> a pipeline they could swap — **they parse it**, and 2,745 downloads a month have.
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

**Licence.** **Code Apache 2.0**, stated plainly. **Dataset terms are not
stated**; a sample dataset sits on Hugging Face under the same name, split into
robot and human subsets, with no scale figure given anywhere in the
documentation. The same shape as [EgoExoLearn](#egoexolearn): a clear code
licence doing double duty as an implied data licence it does not actually grant.

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
did not have. SABER's released quarter at least carries CC BY-NC 4.0. Here the
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

**[arXiv 2512.24310v3](https://arxiv.org/html/2512.24310v3)** — the most heavily
instrumented human-manipulation capture effort in this document, and useful here
as the upper bound on what *recording* can buy that *finding* cannot.

**Scale.** **1,045 hours**, **125,400 clips**, **over 100 human skills**, **over
40 tasks** across **10 scenarios** — banquet, laundry, logistics, hotel,
department, office, supermarket, industry, cleaning, candlelight.

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

**Licence — and a correction to how this is being summarised.** Secondary
coverage describes the dataset as research-only with commercial use restricted.
**The paper states no licence.** What it says is *"All data and hardware design
will be open-source"* — a promise, not a grant, and the arXiv listing carries
only the standard arXiv perpetual non-exclusive licence, which governs the
*paper*. This document therefore records WIYH under [§11](#11-the-licence-trap)'s
second failure mode — **terms unstated** — and not under the first. Anyone
planning against it should get the actual dataset licence in writing.

🔴 **And the promise has now been checked, twice, and has not landed.** A later
sweep looked for the release: **no repository, no Hugging Face dataset, no
download location and no licence** surfaced for WIYH or the Oracle Suite, months
after the paper. The only findable artefact remains the arXiv entry. As with
[Egocentric-1M](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost), this
document does not claim the release will not happen — it claims the narrower,
checkable thing: **"will be open-source" has not yet become anything a reader
can obtain, and the gap is now measured in months rather than asserted.** That
is the difference between the second failure mode and the third, and WIYH is
drifting from one to the other.

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
> **201,019 monthly pulls** against
> [Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost)'s
> **124,711** — so the single most-pulled corpus in this document is one whose
> terms **nobody can read without first accepting them**, and its lead has
> *widened* from 1.4× to **1.6×** while the Apache-2.0 corpus fell 14.5%.
> Stereo-550 also rose in absolute terms (199,055 → 201,019) in a fortnight where
> both Build AI corpora fell, which is the one clean counter-example to reading
> the Build AI decline as a whole-category effect.

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
better.** Those citations include **[Ego4D](#ego4d)** (signed agreement, terms
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
| Egocentric-1M | Apache 2.0 *(reported only; absent from the publisher's complete API index, five attempts)* | ⚠️ confirm the release exists before relying on it — and note that an **empty third-party repo of the same name** now carries an `mit` tag |
| **Action100M** | 🔴 **`fair-noncommercial-research-license`** on `facebook/action100m-preview` — Meta FAIR's own terms. *(This document recorded **CC BY 4.0**, which is the **arXiv listing's** licence.)* Note also it is a **preview** subset | ❌ **non-commercial** — the document previously told readers the opposite |
| **Open-AoE** | 🔴 **`license: other`, `license_name: open-aoe-dataset-license`** on `inclusionAI/OpenAoE-2000h` — **bespoke**, with a staged *"Release Roadmap"*. *(Recorded here as **CC BY 4.0**, which is the **arXiv listing's**.)* **560,619 downloads a month** (re-read this sweep; 562,935 a fortnight ago) | ⚠️ **unclassifiable** — a one-publisher licence, read it in full |
| **EgoLive** | 🔴 **no dataset licence stated anywhere** — the only licence string in the paper is the **arXiv listing's CC BY 4.0**, and distribution runs through a commercial data marketplace (`robotdata-market.jdcloud.com`) whose terms are not the paper's | ⚠️ **unresolved** — previously recorded here as CC BY 4.0 |
| **MobileEgo Anywhere** — `fpvlabs/stera-10m` | **`license: other`**, gated, **401 unauthenticated** — the same bespoke posture as its sibling Stereo-550 *(this document previously recorded **CC BY 4.0**, which is the **arXiv paper's** licence)* | ⚠️ **unclassifiable** — unreadable before agreeing |
| NeMo Curator | Apache 2.0 | ✅ |
| **Ropedia Xperience-10M** | **"other" — gated, DocuSign, research only** | ❌ non-commercial |
| EgoKit | toolkit only, no dataset | n/a — paper carries the arXiv licence |
| VLM-Video-Action-Localization | MIT | ✅ |
| **InternVid** | **CC BY-NC-SA 4.0**, gated *(resolved on re-check; previously recorded as unstated)* | ❌ non-commercial **and** share-alike |
| cosmos-curate (code) | Apache 2.0 | ✅ (models separate) |
| video2dataset | MIT | ✅ |
| Exo2Ego-V | Apache 2.0 | ✅ |
| **EgoDex** | **CC-BY-NC-ND** | ❌ non-commercial, no derivatives |
| **EPIC-KITCHENS-100** | **CC BY-NC 4.0** | ❌ (commercial terms by email to Bristol) |
| **HOI4D** | **CC BY-NC 4.0** | ❌ non-commercial |
| **ENIGMA-360** | 🔴 **no dataset licence stated** — only the **arXiv listing's CC BY 4.0**, and its project page has now failed **six**, the last four with an identical 403 | ⚠️ **unresolved** — previously recorded here as CC BY 4.0 |
| **SABER** | **CC BY-NC 4.0 — on a 10 K-sample subset only; the full corpus is vendor-gated** | ❌ non-commercial, and partial |
| **Ego-OSCAR** — hardware + software | **Apache 2.0** (verified at the repo's `LICENSE`) | ✅ |
| **Ego-OSCAR** — Stereo-550 dataset | **`fpvlabs-license`**, bespoke: "research use", but "commercial usage allowed"; gated, **and the licence text itself is behind the gate** | ⚠️ **unclassifiable** — the one thing a custom licence needs is a reading, and it cannot be read before agreeing |
| **EgoCS-400K** | 🔴 **no dataset licence stated** — only the **arXiv listing's CC BY 4.0**; no repository, no card, no download location named in the paper | ⚠️ **unresolved** — previously recorded here as CC BY 4.0 (rendered gameplay, not real-world footage) |
| **World In Your Hands** | **none stated in the paper; "will be open-source"** | ⚠️ unresolved — get the dataset licence in writing |
| **EgoTactile** | **CC BY-NC 4.0**, ungated (plus `EgoTactile-OXT` on the same terms) | ❌ non-commercial — but stated, which neither EgoTac nor H-Tac manages |
| **EgoTac** | **nothing released** — no repo, no card, no project page, and no *"we release"* anywhere in the body | 🔴 reclassified from *terms unstated* to **not released**: there is nothing to attach terms to |
| 🔴 **H-Tac / TTP** (BeingBeyond) | **partially released** — the printed project page `beingbeyond.github.io/TTP/` still returns **404**, but `BeingBeyond/H-Tac_Sample` on Hugging Face holds **98 episodes / 35,982 frames / 98 videos** under a **MIT** `LICENSE`, ungated, 234 downloads | 🔴 **corrected again**: this table said *not released* for several sweeps. The release was in a namespace neither the paper nor the project URL points at. **HOI-Tac — the 106 h over eleven other datasets — is still not in it** |
| ⚠️ **Open X-Embodiment, third-party mirror** | `jxu124/OpenX-Embodiment` self-describes as *"an unofficial Dataset Repo"* and carries **`license: cc-by-4.0`** over a 55-in-1 aggregation whose official position states **no overall licence**. **16,909 monthly pulls, up ~41% since it was first recorded here** | 🔴 **do not rely on it** — an uploader's licence field is an assertion, not a finding, and this one is being relied on more each month |
| **LAION-BVD** | **research only** | ❌ |
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
| **ENIGMA-360** | CC BY 4.0 | 🔴 **nothing** — and its project page has now failed **six**, the last four with an identical 403 |
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

**What the version audit found this sweep, run over all 47 arXiv IDs cited
here.** Every ID resolved. Exactly **one pinned citation is behind its current
version** — EgoDex at v1 against v3 — and that one is deliberate, for the reason
above. **Twelve IDs are cited bare against papers that now have two or more
versions**, which is the hole this audit had until it was widened to cover
unpinned citations: a bare citation silently tracks whatever the paper says
today. Most of that movement is harmless. One instance was not:
[S-EMBER](#s-ember) **changed its headline finding between v1 and v2** — a
*localisation paradox* became a *grounded recall gap* — on identical data. A bare
citation of a claim that has been reframed is not stale, exactly; it is
**quietly correct about a different sentence than the one you read**, which is
harder to notice than being wrong.

✅ **Re-run in full 15 Sep 2026 — the whole staleness pass, not just versions —
and here is what a clean result looks like, stated so a later sweep can tell
movement from drift.** All **47** arXiv IDs resolved, **34 at their cited
version**, **12 bare against multi-version papers**, **1 deliberately pinned
behind**. **136 URLs** checked; **32 non-2xx**, of which **30 are the proxy's
blanket 403 on `github.com`** and **2 are real**:
[H-Tac's printed `beingbeyond.github.io/TTP/`](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual)
(404, sixth consecutive) and **ENIGMA-360's project page** — **403 for the fourth
time running**, while `iplab.dmi.unict.it/` itself returns **200**. Six failures,
the last four identical: that entry is reclassified from *unstable* to **gone**.
Every licence re-read this pass was **unchanged** — Open-AoE's bespoke terms,
both Meta FAIR non-commercial cards, the two third-party stamps — so the
corrections made against them hold. `yt-fts` still says, in its own README,
*"This project is **abandoned** until unemployment inevitably finds me again."*
*(One ID was added after that pass: **HD-EPIC's `2502.04144`**, verified at the
abs page — title and author list match — and cited bare while the paper is at
**v2**. So the next staleness pass runs over **48** IDs with **13** bare
multi-version citations, and this note exists so the count is not mistaken for
drift.)*

> **The drift, which is the part worth recording.** Download counters moved
> where licences did not: Open-AoE **562,935 → 560,619**, Ego-1K **46,489 →
> 49,612**, `simon055/EgoVid_frames` **5,987 → 5,736**, and
> `jxu124/OpenX-Embodiment` — the unofficial `cc-by-4.0` stamp over a pool that
> states no licence — **up ~41% to 16,909**. **The one artefact here that a
> reader should trust least is the one gaining readers fastest**, which is the
> whole argument for recording terms per clip rather than hoping the ecosystem
> converges on the right answer.

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
> | Card | 1st | 2nd | 3rd | 4th | **5th** | Resolution |
> |---|---|---|---|---|---|---|
> | Egocentric-100K | **164,868** | **158,934** | **156,632** | **145,830** | **124,711** | 456×256 |
> | Egocentric-10K | **34,519** | **30,087** | **34,587** | **40,875** | **39,248** | 1080p |
> | *ratio* | *4.8:1* | *5.3:1* | *4.5:1* | *3.6:1* | ***3.2:1*** | |
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

🔴 **It is not free hours.** The card's licence field reads **"other"**: access
is **gated behind manual review**, restricted to **research and non-commercial
use**, and requires completing a **DocuSign agreement**. On consent it states the
data "was collected and processed under appropriate consent and review
procedures", names privacy and downstream misuse as open questions, and
prohibits identity recognition, person re-identification, biometric profiling
and surveillance. That is a markedly more careful posture than Egocentric-10K's —
and a markedly less available dataset.

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
| 🔴 `Nexdata-AI/10000-Hour-Egocentric-Video-Dataset` | 10,000 hours | **three files.** `.gitattributes`, `README.md`, and a `meta.json` describing **one 59.68-second recording** — whose video file is **not in the repo**. No licence field. Ungated, 60 downloads |
| `UniDataPro/egocentric-video` | a dataset | one `.mp4`, one `.csv`, one tracking `.txt` — and **`CC BY-ND 4.0`** |
| `humyn-labs/APAC-Egocentric-Stereo-Labeled` | labelled stereo | annotation JSONLs, `n<1K`, **CC BY 4.0** — a genuine, tiny sample |
| `Worlddatalabs/egocentric-manufacturing` | manufacturing footage | `license: other`, **manually gated**, scene-segmentation JSON |
| `egxodata/egxo-household-egocentric-video-evaluation` | a household evaluation set | `license_name:` **`egxo-controlled-commercial-access`**, manually gated, shipping an `ACCESS_TERMS.md` and a catalogue CSV |

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

🔴 **This section has now narrowed three times, and the third one is the
serious one. Read the narrowings before the argument.**

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
staging what the web already holds*: [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
needed about a hundred hours of grocery stocking and shelf retrieval — one of the
more abundantly filmed activity classes on the open internet — and sent actors
into real stores with head-mounted GoPros. *By calling something in-the-wild that
isn't*: [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) reports that
world-action-model co-training "scales more effectively with in-the-wild
egocentric human data," and its in-the-wild data is EgoVerse, captured on Project
Aria glasses, with its 3D flow derived from the glasses' own VIO poses. The
phrase, in this literature, means *outside the robot's lab* — never *off the
open web*. **A survey that read those titles at face value would conclude the
opposite of what this section finds.**

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
| Bulk fetch | `video2dataset` (MIT) | **Reuse** | yt-dlp path with per-clip provenance retained |
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
| **"in the wild"** | found on the internet | *outside the robot's lab* — captured by the authors on their own hardware, **or lifted from existing research corpora**, **or captured from 264 recruited participants under signed consent**, **or — in one sentence of [Being-H0.5](#being-h05--the-mano-action-space-at-35000-hours-and-a-preview-subset-with-no-terms) — *"in-the-wild egocentric videos from large-scale public repositories, including Ego4D, EPIC-KITCHENS, Egocentric-10K"***, where the phrase and its denial share a clause | [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) (EgoVerse on Aria), [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild) (own wearable suit), and the term's general use across [§2](#2-scaling-human-video-for-robot-learning). 🔴 **And a variant that is not authors' own capture at all**: [ViTRA](#vitra--12-m-episodes-of-mano-over-four-other-peoples-corpora-stamped-mit)'s *"'in-the-wild' egocentric human videos without any annotations"* are **Ego4D, EPIC-KITCHENS, Ego-Exo4D and Something-Something V2** — the phrase covering both *not-a-lab-capture* and *not-ours* in one document. ✅ **One honest exception**: [EgoTac](#egotac--tactile-predicted-from-ordinary-video-and-a-ceiling-that-moved)'s in-the-wild inference really does run on found corpora |
| **"from existing web sources"** | crawled from the internet | *from existing public research datasets* — Ego4D, EPIC-KITCHENS, HowTo100M, Something-Something | [RynnVLA-001](#rynnvla-001--filter-dont-convert) |
| **a licence on the paper / the code / the repo** | the terms of the **data** | the terms of that adjacent artefact only — the dataset's terms are separate, and often absent | [EgoScale](#egoscale) (arXiv CC BY 4.0), [NIMBLE](#wilor--the-chokepoint-read-at-source) (repo MIT, paper CC BY), [EgoExoLearn](#egoexolearn) and [EgoHumanoid](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator) (code MIT / Apache 2.0), and — **committed by this document itself** — [MobileEgo Anywhere](#mobileego-anywhere), recorded as CC BY 4.0 for dozens of sweeps when that was the arXiv listing's licence and the dataset is gated `license: other` |
| **a dataset named for its size** | that many hours of the thing you want | often a different unit, a different viewpoint, a different corpus entirely — or no corpus at all | [Ego-1K](#ego-1k) — 956 clips of 8–10 s, not 1,000 hours; [Ego-Exo4D](#ego-exo4d) — 1,286 h of which **221 are egocentric**; **`easpeeder/Egocentric-1M`** — a public, MIT-tagged repo containing [two files and no data](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost); and **`Nexdata-AI/10000-Hour-Egocentric-Video-Dataset`** — three files, one of them the metadata of a [59-second recording it does not contain](#the-other-thing-that-happened-to-hours-they-went-on-sale) |
| **two projects one suffix apart** | distinct work, distinctly findable | the search engine silently picks one — **EgoTac** (2608.15060) vs **EgoTactile** (2606.09243); and worse, 🔴 **EgoScale** (2602.16710, NVIDIA GEAR, artefact *"Coming Soon"* for seven months) vs **[EgoScaler](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb)** (2509.21986, Kyoto/NII/Sony), whose dataset is **Apache-2.0, ungated and pulled 30,436 times**. **The missing artefact of one project is impersonated by the present artefact of another** | [EgoTactile](#egotactile--tactile-measured-and-a-rig-that-keeps-the-glove-out-of-frame) |
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
index, not a summary, and each row links to the working. **Twenty-six of them are
this document's own errors** — marked *(this document…)* in the left column and
counted honestly, because an earlier revision of this preamble said "three" long
after the count had passed it, which is the same failure the table exists to
record. They are kept visible rather than quietly amended: a
survey that silently fixes itself gives a reader no way to calibrate how much to
trust the rest of it.

> **Two of the four newest own-errors are not misreadings, and that is the
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
| **EgoScaler's Apache-2.0 set is built on permissively licensed sources** | **None of its four parents is permissive.** Ego4D and Ego-Exo4D are signed-agreement corpora; **HD-EPIC and Nymeria are both CC BY-NC 4.0**, the latter email-gated. The Apache-2.0 correctly covers the authors' own extracted trajectories, but the card states none of this — and **the derived artefact is the one with 30,436 downloads**. Second fully traced case of a permissive stamp over non-permissive parents, after ViTRA, and the first with *zero* permissive parents | [§1](#hd-epic--41-hours-and-the-densest-annotation-in-this-document), [§2](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb) |
| **Nymeria is 3,600 hours** | **300 hours of daily activity**; 3,600 is *camera*-hours across synchronised streams of the same wall-clock time. Both figures sit on one page. Even *worn* hours multiply by the number of sensors pointed at them | [§1](#nymeria--264-consented-participants-called-in-the-wild) |
| **Adding human video to robot post-training helps** | **Only if you choose which.** [ReWeight](#reweight--the-control-simdex-did-not-run) runs the control SiMDex did not: π₀.₅ post-trained on **robot data only 39%**, **robot + randomly mixed human data 44%**, **robot + selected human data 57%**. Random mixing buys 5 points; selection buys 18. Its paper is explicit that naive mixing *"can **degrade** policy performance"* — so delivering hours without an argument for them is not merely inefficient | [§4](#reweight--the-control-simdex-did-not-run) |
| **A paper that says "we release X" has released X** | [MINT](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address) states *"We release the model, training and inference code, labeling pipeline, and a curated 1,021-hour egocentric trajectory dataset"* and **contains no URL anywhere, in v1 or v2** — no repo, no project page, no card, and nothing findable on Hugging Face. **A new shape: a release in the present tense with nowhere to go.** Recorded as *not locatable*, which is not the same as *not released* | [§4](#mint--camera-alignment-at-scale-and-a-release-sentence-with-no-address), [§11](#11-the-licence-trap) |
| **"Open" in a project's name never survives checking** *(the shape this survey had caught three times)* | ✅ [OpenWAM](#openwam--the-first-project-here-whose-open-survives-being-checked) survives it: **20 Apache-2.0 model repos, 6 datasets, Apache-2.0 code, and all three surfaces its paper names resolve.** The control row the trap catalogue needed — though **3 of its 6 datasets carry no licence tag**, and **its ~6,400 h pretraining corpus is not among them** | [§2](#openwam--the-first-project-here-whose-open-survives-being-checked) |
| **H-Tac has nothing released** *(this document, which reclassified it there on purpose)* | `BeingBeyond/H-Tac_Sample` has existed since **6 July 2026**: **98 episodes, 35,982 frames, 98 videos**, a **MIT `LICENSE`**, ungated, 234 downloads. The checks that produced *not released* were run against the paper and its printed project page — both still say nothing, and the page still 404s. **The release was in a namespace neither points at.** An absence of evidence in the two places a paper sends you is not evidence of absence | [§2](#h-tac--tactile-derived-rather-than-predicted-and-the-openego-counterfactual) |
| **A search for EgoScale's missing dataset finds EgoScale's dataset** | It finds **EgoScaler's** — a different paper by different authors at different institutions (2509.21986 vs 2602.16710). EgoScale's artefact has been *"Coming Soon"* for seven months; `Biscue5/egoscaler-v2` is **Apache-2.0, ungated, 30,436 downloads**. The only thing tying that card to its own paper is an `arxiv:` tag | [§2](#egoscaler--one-letter-from-the-entry-above-and-the-first-route-that-needs-only-rgb) |
| **DreamDojo's model terms are unstated** | The *video* terms still are. The **weights** carry **`nvidia-open-model-license`** on `nvidia/DreamDojo` — a bespoke licence, found at the artefact after the paper had been read three times | [§11](#11-the-licence-trap) |
| **DROID is an open dataset with terms you can look up** | **It states none.** Not the project page, not the documentation site, and the data repo `droid-dataset/droid` has **no `LICENSE`** — only the separate `droid_policy_learning` repo does, **MIT**, over code. The loudest answer is a third party's: [`cadene/droid`](https://huggingface.co/datasets/cadene/droid), a LeRobot conversion in a personal namespace, stamped **`apache-2.0`**, ungated, **149,039 downloads**. **Fourth instance of an uploader's licence field standing in for a publisher's silence — and larger than the other three together** | [§1](#the-robot-native-denominator) |
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
| World In Your Hands is research-only, commercial restricted | **No dataset licence is stated.** "Will be open-source" is a promise, not a grant | [§2](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild) |
| EgoExoLearn / EgoHumanoid are openly licensed datasets | Their **MIT and Apache 2.0 licences cover the code**; neither states dataset terms | [§1](#egoexolearn), [§2](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator) |
| Ego-1K is ~1,000 hours of egocentric video | **956 videos of ~8–10 seconds** from a 16-camera rig, for novel-view synthesis | [§1](#ego-1k) |
| Open X-Embodiment is an openly licensed pooled corpus | **No overall licence stated**, and no position on whether its 60 components keep their own | [§2](#the-robot-native-denominator) |
| The high-fidelity corpora are free too | Xperience-10M **gated, non-commercial**; AgiBotWorld-Beta **CC BY-NC-SA**; EgoScale **unreleased**; SABER **a quarter released, CC BY-NC** | [§11](#11-the-licence-trap) |
| EgoInfinity processed 142 M clips / 14.6 years | Its abstract makes **no** scale claim; those are Action100M's figures, and EgoInfinity's curated set is **106 videos** | [§8](#egoinfinity--lift-to-4d-then-reproject) |
| HumanNet: 1,000 h ego video *beat* 100 h robot data | "**matched or modestly surpassed**" — and that 100 h is ~a third of all of DROID | [§2](#humannet) |
| LAION-BVD is a ready 1.3 B-URL pool | **Research use only**, downloads still marked *coming soon* | [§7](#laion-bvd) |
| Action100M has 100 M instances | **147 M** temporally localised segments from 1.2 M instructional videos | [§10](#action100m) |
| cosmos-curate and NeMo Curator are rival tools | Cosmos-Xenna is **NeMo Curator's production executor** | [§9](#cosmos-curate) |
| A tracker lists Egocentric-10K as gated, so it isn't Apache 2.0 | Both are true — **licence and access are separate axes** | [§11](#11-the-licence-trap) |

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
- *EgoTactile: Learning Grasp Pressure for Everyday Objects from Egocentric Video.* ICML 2026 Spotlight, arXiv:2606.09243. (dataset **CC BY-NC 4.0**, ungated) https://arxiv.org/abs/2606.09243 · https://egotactile.github.io/ · https://huggingface.co/datasets/HustleHard/EgoTactile
- *ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios.* (**dataset terms not stated anywhere** — the CC BY 4.0 is the arXiv listing's, covering the manuscript) https://arxiv.org/html/2603.09741v2 · project page https://iplab.dmi.unict.it/ENIGMA-360 **has now failed six checks — HTTP 500, a connection failure, then HTTP 403 four times running (latest 15 Sep 2026, with and without a trailing slash) — while the lab host root returns 200 each time. Four identical 403s in a row is not a flapping server; it is a settled block on that path, and the entry is reclassified from *unstable* to **gone**. Cite the arXiv HTML**
- *SABER: A Scalable Action-Based Embodied Dataset for Real-World VLA Adaptation.* DreamVu. (10 K-sample subset CC BY-NC 4.0; full corpus vendor-gated) https://arxiv.org/html/2605.09613v1 · https://huggingface.co/datasets/DreamVu/SABER-10K
- *EgoDex: Learning Dexterous Manipulation from Large-Scale Egocentric Video.* (CC-BY-NC-ND) https://arxiv.org/abs/2505.11709 — **current version is v3 (9 Mar 2026); the `v1` link is cited deliberately where the licence is quoted**, because v3 no longer states it: https://arxiv.org/html/2505.11709v1
- Yoshida, Kurita, Nishimura, Mori (Kyoto Univ. / NII / Inst. of Science Tokyo / Sony Interactive Entertainment). *Developing Vision-Language-Action Model from Egocentric Videos* (**EgoScaler**, **not** EgoScale). arXiv:2509.21986. (dataset and model both **Apache-2.0**, ungated, 30,436 downloads; built from Ego4D / Ego-Exo4D / HD-EPIC / Nymeria, whose terms the card does not state) https://arxiv.org/abs/2509.21986 · https://huggingface.co/datasets/Biscue5/egoscaler-v2
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
- *World In Your Hands: A Large-Scale and Open-Source Ecosystem for Learning Human-Centric Manipulation in the Wild.* (1,045 h; Oracle Suite wearable; **no dataset licence stated — "will be open-source"**) https://arxiv.org/html/2512.24310v3
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
- Wang, Huang, Li et al. *OpenWAM: An Open, Modular Exploration Towards Systematic World-Action Model Pretraining.* arXiv:2609.07398. (✅ **20 Apache-2.0 model repos, 6 datasets, Apache-2.0 code — all three named surfaces resolve**; the ~6,400 h pretraining corpus is not among them, and 3 of 6 datasets carry no licence tag) https://arxiv.org/abs/2609.07398 · https://github.com/OpenWAM-Official/OpenWAM · https://huggingface.co/OpenWAM · https://openwam-official.github.io/
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
- *DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset.* https://droid-dataset.github.io/
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
- Nexdata. *10000-Hour Egocentric Full-Body Multimodal Dataset.* (**no licence field**; the Hugging Face repo holds three files and no video — *"available upon request"*) https://huggingface.co/datasets/Nexdata-AI/10000-Hour-Egocentric-Video-Dataset · https://www.nexdata.ai/datasets/embodied-ai/2145
- UniDataPro. *Egocentric video dataset.* (**CC BY-ND 4.0** — commercial use permitted, **derivatives forbidden**) https://huggingface.co/datasets/UniDataPro/egocentric-video
- Humyn Labs. *APAC/LATAM Egocentric sample sets.* (CC BY 4.0, ungated, `n<1K`) https://huggingface.co/datasets/humyn-labs/APAC-Egocentric-Stereo-Labeled
- World Data Labs. *Egocentric Manufacturing.* (`license: other`, manually gated) https://huggingface.co/datasets/Worlddatalabs/egocentric-manufacturing
- Build AI. *Egocentric-10K.* (Apache 2.0) https://www.humanoidsdaily.com/news/build-ai-open-sources-10-000-hours-of-factory-worker-video-to-scale-robot-learning · subset: https://huggingface.co/datasets/Voxel51/Egocentric_10K_subset
- *annotated-egocentric-10k-dataset.* (Apache 2.0) https://github.com/fit-alessandro-berti/annotated-egocentric-10k-dataset
- *EgoVid-5M: A Large-Scale Video-Action Dataset for Egocentric Video Generation.* (inherits Ego4D terms) https://arxiv.org/abs/2411.08380 · https://github.com/JeffWang987/EgoVid
- *awesome-egocentric-vision.* https://github.com/Sid2697/awesome-egocentric-vision
- *awesome-temporal-action-segmentation.* https://github.com/nus-cvml/awesome-temporal-action-segmentation
