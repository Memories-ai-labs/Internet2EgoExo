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

<details>
<summary><strong>Contents</strong></summary>

**[Part I — The literature](#part-i--the-literature)**

- [1. Commissioned egocentric and ego–exo capture](#1-commissioned-egocentric-and-egoexo-capture)
  - [EPIC-KITCHENS-100](#epic-kitchens-100)
  - [Ego4D](#ego4d)
  - [Ego-Exo4D](#ego-exo4d)
  - [EgoExoLearn](#egoexolearn)
  - [HOI4D](#hoi4d)
  - [HoloAssist](#holoassist)
  - [Ego-1K](#ego-1k)
  - [ENIGMA-360](#enigma-360)
  - [SABER](#saber--commissioned-egoexo-capture-in-a-domain-the-internet-is-full-of)
- [2. Scaling human video for robot learning](#2-scaling-human-video-for-robot-learning)
  - [The robot-native denominator](#the-robot-native-denominator)
  - [EgoDex](#egodex)
  - [EgoScale](#egoscale)
  - [HumanNet](#humannet)
  - [Ego2Robot](#ego2robot)
  - [EgoEngine](#egoengine)
  - [EgoMimic](#egomimic)
  - [EgoAVFlow](#egoavflow--no-robot-demonstrations-still-means-a-board-in-every-scene)
  - [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean)
  - [EgoHumanoid](#egohumanoid--whole-body-transfer-and-a-vr-rig-on-the-demonstrator)
  - [World In Your Hands](#world-in-your-hands--the-instrumentation-ceiling-and-a-third-in-the-wild)
  - [Open-AoE](#open-aoe)
  - [EgoVerse](#egoverse)
  - [MobileEgo Anywhere](#mobileego-anywhere)
  - [EgoKit](#egokit)
  - [EgoLive](#egolive)
  - [ACE-Ego-0](#ace-ego-0)
- [3. Selection is the hard part, not collection](#3-selection-is-the-hard-part-not-collection)
  - [SiMDex](#simdex)
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
- [13. Why no open-source project does exactly this](#13-why-no-open-source-project-does-exactly-this)
  - [Where the effort actually went](#where-the-effort-actually-went)
  - [Six reasons the hole persists](#six-reasons-the-hole-persists)
  - [What this does and does not license us to claim](#what-this-does-and-does-not-license-us-to-claim)
- [14. Build vs. reuse, per stage](#14-build-vs-reuse-per-stage)
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

### Ego4D

**[ego4d-data.org](https://ego4d-data.org/)** — 3,670+ hours of daily-life egocentric
video with a benchmark suite (episodic memory, forecasting, hand–object
interaction). Still the default pretraining corpus, and the base that
[EgoVid-5M](#egovid-5m) and much else is derived from.

### Ego-Exo4D

**[arXiv 2311.18259](https://arxiv.org/abs/2311.18259)** (CVPR 2024) — the reference
work for this project's problem statement. 1,286 hours, **740 participants across
13 cities and 123 natural scene contexts**, and over **200,000 hours of annotator
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
Google Drive, BaiduYun and Hugging Face — with no access form. So the honest
record is: **code MIT, dataset terms unstated but access unrestricted** — the
mirror image of [Egocentric-10K](#egocentric-10k), which gates access while
granting permissive terms. Two more reasons to keep licence and access in
separate fields.

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

> **Why it sits in this document.** It is a *view-synthesis* dataset, not a
> manipulation corpus — but it is exactly the rig-captured multiview input that
> [Exo2Ego-V](#exo2ego-v--why-generative-conversion-does-not-apply)-style methods
> require and the web cannot supply, and it is an unusual middle case: the
> surrounding views are head-mounted rather than fixed in the room. Its own
> stated difficulty is instructive too — large disparities and image motion from
> close dynamic objects and rig egomotion, which is to say that even with sixteen
> synchronised cameras, hands moving near the face remain the hard part.

### ENIGMA-360

**[arXiv 2603.09741](https://arxiv.org/html/2603.09741v1)** — the industrial
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
| **[AgiBotWorld-Beta](https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta)** | **2,976.4 hours**, 1 M+ trajectories, 200+ task types, 87 atomic skills | **100 robots** — mobile dual-arm, 6-DoF dexterous hands, visual-tactile sensors; video, depth, joint positions/velocities/forces, end-effector state, odometry | 🔴 **CC BY-NC-SA 4.0**, contact-gated |
| **[Open X-Embodiment](https://robotics-transformer-x.github.io/)** | 1 M+ trajectories, **22 embodiments**, 527 skills, 160,266 tasks — **hours not stated** | **60 existing datasets pooled** from 34 labs across 21 institutions; single arms through bimanual robots and quadrupeds | 🔴 **No overall licence stated on the project page**, and no statement of whether the 60 components retain their own |
| Human ego, for scale | [Egocentric-100K](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) 100,405 h · [DreamDojo](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) 44,711 h | Crowdsourced / commissioned capture | Apache 2.0 / unstated |

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
- 🔴 **Licence: CC-BY-NC-ND** — the paper states the data is *"licensed under
  CC-by-NC-ND terms"*. Non-commercial **and no derivatives**. This is the single
  most-cited "hands are the payload" dataset in the field and it cannot be used
  commercially, nor can derivative datasets be redistributed. Re-verified at the
  paper this sweep; unchanged.
- ⚠️ **The access side runs the other way, which is worth knowing.** The Hugging
  Face mirror is gated — an unauthenticated fetch returns **401**. But the zips
  are served straight from **Apple's own CDN**
  (`ml-site.cdn-apple.com/datasets/egodex/…`), and a request there this sweep
  returned **HTTP 200, a 17.3 GB body, no authentication**. So the most
  restrictively *licensed* corpus in this document is also among the most openly
  *accessible*. Splits: ~725 h train, 7 h test, 97 h added after the split was
  frozen.
- **Limits**: tabletop only; annotation degrades under heavy occlusion and fast
  motion; embodiment gap.

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
> **Code is marked "Coming Soon"**, and **no dataset licence is stated
> anywhere**. The arXiv listing carries CC BY 4.0, which governs the *paper* —
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

> **The ablation is the transferable finding.** The action branch supplies
> essentially all the gain — **43% with it against 5% for visual-only**. For a
> collection pipeline deciding where to spend, that says the *trajectory* is the
> payload and photorealism is decoration, which is the same conclusion the hands
> gate encodes from the other direction.

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

### EgoHumanoid — whole-body transfer, and a VR rig on the demonstrator

**[OpenDriveLab/EgoHumanoid](https://github.com/OpenDriveLab/EgoHumanoid)**
(RSS 2026) — *"the first framework enabling humanoid loco-manipulation with
egocentric human demonstrations."* It extends this section's question from hands
to the whole body: not just what the demonstrator grasped, but where they walked
to do it.

**Mechanism.** A vision-language-action policy co-trained on abundant egocentric
human data plus limited robot teleoperation, bridged by two explicit steps —
**view alignment**, via depth-based warping and inpainting, and **action
alignment**, with navigation velocities derived from body pose and discretised
into commands. Reported gain: **51% over robot-only baselines**.

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
footage will never have, at any scale, and it would be dishonest to pretend
otherwise: for contact-rich dexterity there is a fidelity ceiling on internet
video that no amount of verification lifts. What 1,045 instrumented hours cost —
a custom glove, a backpack computer, an operator per hour — is the other half of
the trade, and it is why the two supplies are complements rather than rivals.
The manifest discipline this repo applies exists precisely so a trainer can tell
which kind of hour it is holding.

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

### MobileEgo Anywhere

**[arXiv 2605.05945](https://arxiv.org/pdf/2605.05945)** — 200 hours across 354
sessions from **16 contributors**, captured on iPhone Pro devices in head rigs in
household environments. Average session 21.2 minutes, longest ~108. The app is
hands-free by voice ("start" / "stop") and writes synchronised RGB, depth, IMU
and ARKit 6-DoF pose into MCAP.

The **STERA** pipeline behind it:

1. **3D hand trajectory** — WiLoR produces MANO hand poses, unprojected into 3D
   with ARKit depth and transformed into a global frame.
2. **Atomic action labels** — a VLM writes captions with object modifiers and
   spatial prepositions ("transfer dough from metal bowl to large plate").
3. **Hierarchical instructions** — an LLM organises those into a **three-level
   tree**: 5-second manipulation steps → minute-scale sub-goals → full session
   plans. 45,415 atomic spans, 5,570 episodes, 1,298 sub-goals.

**Licence CC BY 4.0.** Quality reporting is unusually candid: 87% of sessions
passed all structural checks, 46 needed automatic correction, hand-pose
consistency was evaluated on 98 of 354 sessions, human validation on 50.

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

### S-EMBER

**[arXiv 2607.02689](https://arxiv.org/pdf/2607.02689)** — the first benchmark
for **streaming** egocentric memory retrieval, 15 hours of first-person video
with multiple queries per sequence, released on Hugging Face and GitHub.

The distinction it draws is the one that matters for an indexed corpus: standard
video retrieval searches pre-segmented clips, whereas streaming memory retrieval
must find the relevant moment in a continuous feed **without knowing the temporal
boundaries in advance**. Baselines with GPT-4o and Gemini 3 leave large gaps.

> **Bearing here.** This is the failure mode our clipping stage exists to prevent.
> A pipeline that indexes whole videos and hopes retrieval will find the moment is
> attempting S-EMBER's hard problem at query time; a pipeline that has already cut
> semantically coherent clips and written per-span annotations has converted it
> into ordinary retrieval. The 15-hour benchmark is small, but the framing is the
> useful part.

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
before building, and the third is a plan you cannot make. A fourth shape appears
below.

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
| Egocentric-1M | Apache 2.0 *(reported only; absent from the publisher's own dataset listing)* | ⚠️ confirm the release exists before relying on it |
| Action100M | CC BY 4.0 | ✅ with attribution |
| Open-AoE | CC BY 4.0 | ✅ with attribution |
| EgoLive | CC BY 4.0 | ✅ with attribution (distributed via JD Cloud) |
| MobileEgo Anywhere | CC BY 4.0 | ✅ with attribution |
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
| ENIGMA-360 | CC BY 4.0 | ✅ with attribution |
| **SABER** | **CC BY-NC 4.0 — on a 10 K-sample subset only; the full corpus is vendor-gated** | ❌ non-commercial, and partial |
| EgoCS-400K | CC BY 4.0 | ✅ with attribution (rendered gameplay, not real-world footage) |
| **World In Your Hands** | **none stated in the paper; "will be open-source"** | ⚠️ unresolved — get the dataset licence in writing |
| **LAION-BVD** | **research only** | ❌ |
| **EgoInfinity (as a whole)** | MIT code, encumbered deps | ❌ until deps are swapped |
| **Ego4D / Ego-Exo4D** | **signed agreement, terms not public** | ⚠️ unknowable until you sign — do not assume |
| EgoVerse | no dataset licence stated (**re-checked at the paper this sweep; still none** — only the arXiv listing's, and access runs through the authors' EgoDB/S3 sync) | ⚠️ ask before use |
| Panda-70M (data) | inherits HD-VILA-100M | ⚠️ check upstream |
| EgoVid-5M | inherits Ego4D | ⚠️ check upstream |

| DreamDojo code | Apache 2.0 | ✅ (the 43,827 crowdsourced hours have **no stated terms**) |
| [HoloAssist](#holoassist) | CDLA v2 | ✅ |
| [Ego-1K](#ego-1k) | CC BY 4.0 | ✅ with attribution (17.5 TB research / 88 TB raw on request) |
| [EgoScale](#egoscale) | none stated; code "coming soon" | ⚠️ not obtainable at time of writing |
| **AgiBotWorld-Beta** | **CC BY-NC-SA 4.0**, contact-gated | ❌ non-commercial **and** share-alike — the most restrictive terms here |
| DROID | open dataset; terms not stated on the project page (**re-checked; still silent** — the page says only that the dataset, training code and hardware guide are open-sourced) | ⚠️ unresolved |
| EgoExoLearn | **MIT on the code**; dataset terms not separately stated, access unrestricted | ⚠️ code clear, data unresolved |
| **Open X-Embodiment** | **none stated; 60 pooled components, position unstated** | ⚠️ unknowable without tracing 60 upstream datasets |

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

**All four corners of the licence × access grid are now occupied**, which is the
cleanest way to see why one field cannot carry both. Every cell below was
verified at source:

| | **Access open** | **Access gated** |
|---|---|---|
| **Licence permissive** | [EgoCS-400K](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it) — CC BY 4.0, ungated | [Egocentric-10K / -100K](#egocentric-10k) — Apache 2.0, but *"agree to share your contact information"* |
| **Licence restrictive** | **[EgoDex](#egodex)** — CC-BY-NC-ND, yet the zips come straight off Apple's CDN, **HTTP 200, no auth** | [InternVid](#internvid) CC BY-NC-SA + gate; [AgiBotWorld-Beta](#the-robot-native-denominator) CC BY-NC-SA + contact gate; [Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability) non-commercial + DocuSign |

The bottom-left cell is the one that catches people. **EgoDex is the most
restrictively licensed corpus in this document and among the easiest to
download** — 17.3 GB over plain HTTPS with nothing to sign. Ease of acquisition
carries no information at all about what you may then do, and a pipeline that
infers permission from a 200 response will be wrong exactly where it matters
most, since EgoDex is also the field's most-reused hand corpus
([derivation map](#who-feeds-whom--the-derivation-map)).

⚠️ **Licence and access are separate axes, and collapsing them misleads.** A
third-party [release tracker](https://egxodata.com/resources/robotics-data-release-tracker-2026)
records Egocentric-10K as "gated; terms require review" — true of *access*, and
compatible with the card's Apache 2.0 *licence*: the Build AI sets ask for
contact details before download while granting permissive terms afterwards.
Conversely [Xperience-10M](#ropedia-xperience-10m--the-fidelity-wings-extreme-and-a-caution-about-reading-press-releases-as-availability)
is gated **and** non-commercial. When recording rights per clip, record both:
*can I get it* and *what may I do with it* fail independently.

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
primitives, across **290 manipulation tasks in 600+ environments**. The
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
> ⚠️ Two things not asserted here. The arXiv listing's CC-BY-4.0 governs the
> *paper*; the annotation releases are described as carrying each source's terms,
> which is a different and more careful arrangement than a single blanket
> licence. And the resources are stated as *"will be released"* at
> `openegocentric.com` — this document has not verified that the release landed.

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
| [Ego2Robot](#ego2robot) (18,561 h synthetic) | **EgoDex 732 h** + EgoVerse 954 h + ViTRA 249 h + 7 h in-house | ~38% of input hours are **CC-BY-NC-ND** |
| [EgoWAM](#egowam--and-what-in-the-wild-turns-out-to-mean) | **EgoVerse** (Aria) | EgoVerse's terms — which are not stated |
| [EgoVid-5M](#egovid-5m) (5 M clips) | **Ego4D** annotations; video fetched from Ego4D | Ego4D's unpublished agreement |
| [Panda-70M](#panda-70m) (70 M clips) | **HD-VILA-100M** | inherits upstream, stated |
| [annotated-egocentric-10k](#annotated-egocentric-10k-dataset) | **Egocentric-10K** | Apache 2.0 — a clean chain |
| ✅ [OpenEgo](#openego--somebody-does-this-properly-and-it-should-be-said-plainly) (1,107 h) | **EgoDex 829 h** + HoloAssist 166 + CaptainCook4D 54 + HOI4D 44 + HOT3D 13.3 + HO-Cap 0.67 | **The only row that solves it**: annotations only, no video redistributed, each source's licence text shipped with attribution, and explicit author permission for the CC-BY-NC-ND component |
| [Open X-Embodiment](#the-robot-native-denominator) | **60 datasets, 34 labs** | unknowable without tracing sixty |
| [EgoInfinity](#egoinfinity--lift-to-4d-then-reproject), Ego2Robot, [MobileEgo](#mobileego-anywhere) | **WiLoR** (+ MANO, YOLO) | **CC-BY-NC-ND** *model* in the annotation path |

**Two chokepoints carry most of the risk, and both are CC-BY-NC-ND.**
**EgoDex** is inside at least **five** downstream artefacts on this list —
supplying 75% of OpenEgo's hours alone;
**WiLoR** is inside at least three annotation pipelines. Neither is obscure and
neither is optional in the way a swappable dependency is — they are the
field's default hand-annotated corpus and default hand reconstructor. A
no-derivatives clause sitting at a chokepoint that many things route through is
the single most consequential licensing fact in this document. *Nothing here
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
| Egocentric-1M | Apr 2026 | ~1,000,000 (reported) | not verified | Apache 2.0 (reported) |

**Egocentric-100K, verified at the dataset card**: 100,405 hours, **10.8 billion
frames**, 2,010,759 clips, 24.79 TB, 30 fps H.265, monocular head-mounted
**fisheye** Build AI Gen 1, per-worker calibrated camera intrinsics, mean 7.06
hours per worker, Apache 2.0, access gated behind sharing contact information.

🔴 **Egocentric-1M could not be found at the publisher, across four separate
attempts.** In order: its Hugging Face card returns 401 to an unauthenticated
fetch; it does not surface in dataset search, where the 100K and 10K-Evaluation
cards do; **Build AI's own Hugging Face organisation page lists exactly four
datasets, and Egocentric-1M is not among them**; and a fourth attempt, run
months later against Hugging Face's `egocentric` dataset search, returned
**Egocentric-10K, Egocentric-10K-Evaluation, Egocentric-100K and
Egocentric-100K-Evaluation — all four under `builddotai`, and no
Egocentric-1M**. Four routes, one publisher, nothing:

| Dataset | Last updated | Downloads, first reading | Downloads, this sweep |
|---|---|---|---|
| Egocentric-10K | Feb 16 | 343 | **34.5 k** |
| **Egocentric-100K** | Feb 16 | **161,000** | **1.95 M** *(the cards say 164,868 — see below)* |
| Egocentric-100K-Evaluation | Dec 9, 2025 | 198 | 30 k |
| Egocentric-10K-Evaluation | Nov 10, 2025 | 158 | 30 k |

Both columns are the organisation listing's own figures at two readings months
apart. The counter is a **rolling monthly rate**, not a lifetime total, and the
two surfaces do not agree for Egocentric-100K — both problems are worked through
where the ratio is used, [below](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost).

This document does not claim the release does not exist — it may be private,
gated below the listing, or planned. What it claims is narrower and checkable:
**the ~1 M hours, the April 2026 date and the Apache 2.0 terms rest entirely on
secondary coverage — which still repeats them — and four attempts at the
publisher's own surfaces, spread over months, found nothing.** Anyone sizing a plan against it should get it confirmed first.

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
> | Card | Downloads last month | Resolution |
> |---|---|---|
> | Egocentric-100K | **164,868** | 456×256 |
> | Egocentric-10K | **34,519** | 1080p |
>
> That is **roughly 4.8:1**, not 470:1. The 1080p corpus went from a few hundred
> monthly pulls to thirty-four thousand while the 256p corpus barely moved.
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
problems, so the released pose annotations are preferred over it. Licence follows
Ego4D's terms.

### EgoCS-400K — 10,000 free hours, sourced from the internet, and why §13 survives it

**[arXiv 2606.18180](https://arxiv.org/html/2606.18180v1)** — the nearest thing
in this literature to the machine this repo is, and the entry most likely to be
read as refuting [§13](#13-why-no-open-source-project-does-exactly-this). It
does not, but the reason is precise and worth stating rather than waved at.

**Scale, all verified at source.** **Over 400,000 first-person videos, over
10,000 hours**, from **over 1,000 matches** and **over 40,000 rounds**, across
**13 maps**, at **10 player viewpoints per round**, averaging ~90 seconds per
round-player video. **Licence CC BY 4.0.**

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
10,000 hours, under CC BY 4.0. That narrowed the claim to *real-world* footage —
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

## 13. Why no open-source project does exactly this

The obvious question, having read all of the above: internet-scale video →
ego/exo training footage is a clearly valuable, clearly defined problem, and
almost every individual piece of it is open. So why is there no open-source
project that does the whole thing?

The answer is not that people tried and failed. **Open source went hard at the
two adjacent problems and skipped this one.**

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
| Rights | *(mostly ignored)* | **Build** | Licence per clip; unmeasured ⇒ excluded, not assumed |

**The short version:** skeleton from `cosmos-curate`; clipping design from
Panda-70M; viewpoint rule from RynnVLA-001, independently corroborated;
annotation hierarchy from Action100M with Panda-70M's selection discipline; 4D as
a later upgrade only after the non-commercial dependencies are replaced *and*
the static-camera assumption is dealt with. **The front and the back of the chain
— requirement in, provenance out — are the parts that have to be built, and they
are the parts that are worth owning.**

---

## Corrections, in one table

Every correction below is argued in place in the entry it belongs to; this is an
index, not a summary, and each row links to the working. **Three of them are
this document's own errors**, kept visible rather than quietly amended — a
survey that silently fixes itself gives a reader no way to calibrate how much to
trust the rest of it.

| Claim in circulation | What the source says | Where |
|---|---|---|
| The 256p corpus outdownloads the 1080p one **470:1** *(this document, earlier)* | Wrong twice: the counter reads **"Downloads last month"**, a rate not a total, and re-read at both cards it is **164,868 vs 34,519 — roughly 4.8:1**. The gap is closing | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
| **Nobody** sources ego data from the internet at scale *(this document, earlier)* | **EgoCS-400K does** — 10,000+ h, CC BY 4.0, from public HLTV match demos. Narrowed to *real-world* footage, since EgoCS-400K renders video from replay files and reads actions out of them | [§12](#egocs-400k--10000-free-hours-sourced-from-the-internet-and-why-13-survives-it), [§13](#13-why-no-open-source-project-does-exactly-this) |
| **Nobody** mines the web for *real-world* human video at scale *(this document, for twenty-five sweeps, while carrying the refutation in §2)* | **HumanNet does**, at one million hours, from *"video-platform search, general web search engines, directly crawled videos, open-source datasets, and self-collection."* What is missing is not the act but the artefact: no release, no licence, no source breakdown, no ego/exo split, no per-clip provenance. §13 narrows to **open, auditable, reusable infrastructure** | [§2](#humannet), [§13](#13-why-no-open-source-project-does-exactly-this) |
| HumanNet's headline is the 1,000 h vs 100 h result | Its follow-up **HumanScale** is stronger and newer: **5,000 h egocentric vs 5,000 h real-robot at matched scale** → 24% lower validation loss, **52.5% / 90%** higher in- and out-of-distribution success. At matched hours that is outperforming, not matching | [§2](#humannet) |
| EgoScale is a UT Austin RPL project *(this document, earlier)* | **GEAR @ NVIDIA Research**, sixteen authors across several institutions | [§2](#egoscale) |
| EgoScale's 20,854 h and DreamDojo's 43,827 h are two independent corpora | Both papers report **9,869 scenes / 6,015 tasks / 43,237 objects** and the same **829 h of EgoDex**, and neither cites the other. Almost certainly one corpus feeding two products; taking both at face value double-counts one acquisition | [§2](#egoscale), [§4](#dreamdojo--and-the-strongest-evidence-in-this-document-for-13) |
| EgoScale is CC BY 4.0 | That is the **arXiv listing's licence, covering the paper**. No dataset licence is stated anywhere, and the code is "coming soon" | [§2](#egoscale) |
| InternVid states no licence *(this document, earlier)* | The dataset card carries **`cc-by-nc-sa-4.0`** and is gated. Non-commercial **and** share-alike — the most restrictive combination here. An "unresolved" field is a snapshot, not a property | [§3](#internvid) |
| Ego-Exo4D is ~1,286 h of egocentric video | Official docs: **1286.30 video hours, 221.26 ego-hours, 5035 takes** — about **17%** egocentric | [§1](#ego-exo4d) |
| Build AI released ~1 M hours (Egocentric-1M) | **Not findable at the publisher across four attempts** spread over months | [§12](#egocentric-100k-and-egocentric-1m--and-what-scaling-cost) |
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
- Grauman et al. *Ego4D.* https://ego4d-data.org/
- Damen et al. *Scaling Egocentric Vision: The EPIC-KITCHENS Dataset.* https://arxiv.org/pdf/1804.02748
- Huang et al. *EgoExoLearn.* CVPR 2024. https://github.com/OpenGVLab/EgoExoLearn
- *HOI4D.* (CC BY-NC 4.0) https://arxiv.org/pdf/2404.09933 · https://hoi4d.github.io/
- *ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios.* (CC BY 4.0) https://arxiv.org/html/2603.09741v1 · project page https://iplab.dmi.unict.it/ENIGMA-360 **returns HTTP 500 as of this sweep — cite the arXiv HTML**
- *SABER: A Scalable Action-Based Embodied Dataset for Real-World VLA Adaptation.* DreamVu. (10 K-sample subset CC BY-NC 4.0; full corpus vendor-gated) https://arxiv.org/html/2605.09613v1 · https://huggingface.co/datasets/DreamVu/SABER-10K
- *EgoDex: Learning Dexterous Manipulation from Large-Scale Egocentric Video.* (CC-BY-NC-ND) https://arxiv.org/html/2505.11709v1
- *EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data.* GEAR @ NVIDIA Research. (code "coming soon"; no licence stated) https://arxiv.org/abs/2602.16710 · https://research.nvidia.com/labs/gear/egoscale/
- Deng, Zhou et al. *HumanNet: Scaling Human-centric Video Learning to One Million Hours.* https://arxiv.org/abs/2605.06747
- *Ego2Robot: Scalable Robot Data Synthesis from Egocentric Human Data.* https://arxiv.org/html/2608.02580
- *EgoEngine: From Egocentric Human Videos to High-Fidelity Dexterous Robot Demonstrations.* https://arxiv.org/html/2606.12604v1 · https://egoengine.github.io
- *EgoMimic: Scaling Imitation Learning via Egocentric Video.* https://arxiv.org/abs/2410.24221
- *EgoAVFlow: Robot Policy Learning with Active Vision from Human Egocentric Videos via 3D Flow.* (CC BY 4.0; head-mounted RealSense D435 RGBD plus a ChArUco board per scene; 150 videos × 4 tasks; no dataset release stated) https://arxiv.org/html/2602.22461v1
- *EgoWAM: World Action Models Beyond Pixels with In-the-Wild Egocentric Human Data.* (CC BY 4.0; "in-the-wild" = EgoVerse on Project Aria, flow from Aria VIO poses) https://arxiv.org/abs/2607.08436
- *EgoHumanoid: humanoid loco-manipulation from egocentric human demonstrations.* RSS 2026. (code **Apache 2.0**; dataset terms not stated; PICO VR headset + 5 body trackers + ZED Mini depth) https://github.com/OpenDriveLab/EgoHumanoid
- *World In Your Hands: A Large-Scale and Open-Source Ecosystem for Learning Human-Centric Manipulation in the Wild.* (1,045 h; Oracle Suite wearable; **no dataset licence stated — "will be open-source"**) https://arxiv.org/html/2512.24310v3
- *OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation.* (1,107 h unifying six public datasets; **annotations only, each source's licence text shipped with attribution**) https://arxiv.org/html/2509.05513v1 · https://www.openegocentric.com
- *EgoCS-400K: An Egocentric Gameplay Dataset for World Models.* (CC BY 4.0; 400 K+ videos / 10,000+ h rendered from public HLTV match demos) https://arxiv.org/html/2606.18180v1 · https://EgoCS-400K.github.io
- *ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretraining.* https://arxiv.org/html/2606.17200v1 (the project URL printed in the paper 404s)
- *Open-AoE: An Open Egocentric Manipulation Dataset and Toolchain for Embodied Learning.* (CC BY 4.0) https://arxiv.org/abs/2607.14183
- *EgoVerse: An Egocentric Human Dataset for Robot Learning from Around the World.* https://arxiv.org/abs/2604.07607
- *EgoKit: Towards Unified Low-Cost Egocentric Data Collection with Heterogeneous Devices.* (toolkit; no dataset) https://arxiv.org/pdf/2605.16797
- *MobileEgo Anywhere: Open Infrastructure for long-horizon egocentric data on commodity hardware.* (CC BY 4.0) https://arxiv.org/pdf/2605.05945
- Ego-Exo4D documentation (source of the 1286.30 h / 221.26 ego-h / 5035 takes figures). https://docs.ego-exo4d-data.org/
- *EgoLive: A Large-Scale Egocentric Dataset from Real-World Human Tasks.* https://arxiv.org/html/2604.23570v1
- *From Human Videos to Robot Manipulation: A Survey.* https://arxiv.org/html/2606.00054v1
- *SiMDex: Mining Similar Egocentric Videos for Cross-Embodiment Dexterous Manipulation.* https://arxiv.org/abs/2608.04196
- Chen et al. *Panda-70M: Captioning 70M Videos with Multiple Cross-Modality Teachers.* CVPR 2024. https://github.com/snap-research/Panda-70M
- Wang et al. *InternVid.* https://arxiv.org/abs/2307.06942
- NVIDIA. *Cosmos World Foundation Model Platform for Physical AI.* https://arxiv.org/abs/2501.03575
- NVIDIA. *NeMo Curator.* https://github.com/NVIDIA-NeMo/Curator
- NVIDIA. *DreamDojo: A Generalist Robot World Model from Large-Scale Human Videos.* ICML 2026. (code Apache 2.0; video terms unstated) https://arxiv.org/html/2602.06949 · https://github.com/NVIDIA/DreamDojo
- Meta Reality Labs. *Ego-1K: A Large-Scale Multiview Video Dataset for Egocentric Vision.* (CC BY 4.0) https://arxiv.org/html/2603.13741v1
- *HoloAssist.* (CDLA v2) https://holoassist.github.io/
- *DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset.* https://droid-dataset.github.io/
- *AgiBotWorld-Beta.* (CC BY-NC-SA 4.0, gated) https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta
- *Open X-Embodiment.* (no licence stated on the project page) https://robotics-transformer-x.github.io/
- EGXO Data. *Robotics Data Release Tracker 2026.* (third-party tracker, v1.1.1, last updated 2026-07-25 — useful for monitoring, but it collapses licence and access; verify at the publisher) https://egxodata.com/resources/robotics-data-release-tracker-2026
- Memories.ai Research. *OmniRetriever: Any-to-Any Audio-Video-Text Retrieval via Fusion-as-Teacher Distillation.* https://arxiv.org/abs/2605.26641
- *S-EMBER: A Large-Scale Benchmark for Streaming Egocentric Memory Retrieval.* https://arxiv.org/pdf/2607.02689
- Ropedia. *Xperience-10M.* (gated, non-commercial) https://huggingface.co/datasets/ropedia-ai/xperience-10m · release note: https://ropedia.com/blog/20260316_xperience_10m · critique: https://technologies.org/ropedia-raises-30-million-for-physical-ai-training-data-but-the-dataset-math-doesnt-hold-up/

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
- *EgoVid-5M: A Large-Scale Video-Action Dataset for Egocentric Video Generation.* (inherits Ego4D terms) https://arxiv.org/abs/2411.08380 · https://github.com/JeffWang987/EgoVid
- *awesome-egocentric-vision.* https://github.com/Sid2697/awesome-egocentric-vision
- *awesome-temporal-action-segmentation.* https://github.com/nus-cvml/awesome-temporal-action-segmentation
