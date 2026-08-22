# Related Work

This project is not a model and not a dataset. It is the step in between: a way to
turn the open internet into **ego/exo training footage that a team can actually
use** — viewpoint-labelled, licence-checked, hands-verified, annotated to a
task → action → event tree, and priced per delivered hour.

That framing is what separates it from most of the literature it sits next to.
Almost everything below either *commissions* footage, or *consumes* a corpus
somebody else already owns. Very little of it is about acquisition against a
stated requirement.

---

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
