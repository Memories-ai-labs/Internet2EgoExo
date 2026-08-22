# Architecture: one pipeline, six packages, N agents working at once

This document exists to answer one question: **how do we let six or ten agents
improve different parts of this system at the same time, without them tripping
over each other, and still have the parts fit together at the end?**

The answer is not "more agents". It is a set of boundaries sharp enough that an
agent can be handed one box, one metric, and one test command, and be trusted to
work alone for a day.

---

## 1. Why parallel work collides today

Everything lives in one distribution, `src/video_searching_agent`, and the
sub-packages import each other in both directions. Measured on `main`:

| edge | count | what causes it |
|---|---|---|
| `agent` → `curation` | 12 | quality gates, scoring, viewpoint |
| `curation` → `agent` | 2 | `parse_json_object` from `agent/react.py` |
| `models` → `curation` | 5 | `Viewpoint`, `CostBreakdown`, `is_reusable_license` |
| `pipeline` → `agent` | 2 | cleaning + annotation agents |
| `agent` → `pipeline` | 1 | `read_mp4_dimensions` from `media_probe` |
| `router` → `agent` | 1 | `CLASSIFICATION_PROMPT` |
| `agent` → `router` | 1 | `QueryParser` |
| `tools` → `curation` | 4 | `Viewpoint`, `score_candidate` |

Read the right-hand column again. Every cycle is a **utility** sitting in a
domain package: a JSON parser, an enum, a prompt constant, an mp4 header reader.
None of them is a real dependency between two stages of the pipeline.

That is the good news. But the consequences today are real:

- **Blast radius.** A change to `curation/viewpoint.py` can break the search
  tools, the models, and the cleaning agent. No agent can be told "you own
  curation" and be believed.
- **Merge collisions on hot files.** Two agents that touch nothing in common
  still both edit `README.md` (60k, one file), `pyproject.toml`, and `uv.lock`.
- **No stage can be evaluated alone.** To measure the labeling agent you must
  first run search, download, upload and indexing. So one agent's experiment
  costs another agent's money and an hour of wall clock, and a regression
  anywhere shows up as a regression everywhere.
- **One concurrency knob for four different bottlenecks.**
  `tool_execution_concurrency = 4` governs downloads (bandwidth-bound),
  indexing (provider rate-limited) and labeling (token-bound) alike.

The third point is the one that actually blocks parallelism. Fix it and the rest
follows.

---

## 2. The shape

Nine distributions in one repository, in a `uv` workspace. Dependencies point
one way only: **every stage package depends on `core` and on nothing else.**

```
                        ┌─────────────────────────────────┐
                        │            i2e-core             │
                        │  contracts · ports · react loop │
                        │  llm client · cost · settings   │
                        └─────────────────────────────────┘
                          ▲    ▲     ▲     ▲     ▲     ▲
             ┌────────────┘    │     │     │     │     └────────────┐
             │                 │     │     │     │                  │
      ┌──────┴─────┐  ┌────────┴──┐ ┌┴─────┴──┐ ┌┴───────────┐ ┌────┴──────┐
      │ i2e-       │  │ i2e-      │ │ i2e-    │ │ i2e-       │ │ i2e-      │
      │ sourcing   │  │ acquire   │ │ lake    │ │ labeling   │ │ curation  │
      │            │  │           │ │         │ │            │ │           │
      │ search the │  │ probe,    │ │ upload, │ │ clean +    │ │ grade the │
      │ internet,  │  │ screen,   │ │ index,  │ │ segment +  │ │ set, dedup│
      │ rank, dedup│  │ download  │ │ tag I/O │ │ annotate   │ │ , manifest│
      └────────────┘  └───────────┘ └─────────┘ └────────────┘ └───────────┘
             ▲               ▲           ▲            ▲              ▲
             └───────────────┴─────┬─────┴────────────┴──────────────┘
                                   │
                        ┌──────────┴──────────┐        ┌──────────────┐
                        │  i2e-orchestrator   │◀───────│  i2e-eval    │
                        │  compose · budget · │        │  harness +   │
                        │  ledger · resume    │        │  scorecards  │
                        └──────────┬──────────┘        └──────────────┘
                                   │
                          ┌────────┴────────┐
                          │   i2e-service   │
                          │  FastAPI · SSE  │
                          └─────────────────┘
```

```
packages/
  core/          i2e_core          contracts, ports, ReAct loop, LLM client, cost, settings
  sourcing/      i2e_sourcing      query → Candidate[]            (search, rank, dedup)
  acquire/       i2e_acquire       Candidate → LocalClip          (probe, screen, download)
  lake/          i2e_lake          LocalClip → LakeVideo          (upload, index, tags, moments)
  labeling/      i2e_labeling      LakeVideo → ClipLabels         (clean, segment, annotate)
  curation/      i2e_curation      ClipLabels[] → DatasetManifest (grade, dedup, ledger, export)
  orchestrator/  i2e_orchestrator  composition, budgets, run ledger, resume
  service/       i2e_service       HTTP + SSE, thin
  eval/          i2e_eval          shared harness; suites live inside each package
scripts/         rollup_scorecards.py, check_layering.py, …
docs/            this file, per-boundary contract notes
```

`video_searching_agent` stays as a shim package that re-exports the new
locations, so the deployed API, the QA scripts and the existing eval harness
keep working through the migration. It is deleted when nothing imports it.

### Why these five stages and not others

The boundaries are drawn where the **failure modes, the cost model, and the
unit of work** all change at once:

| stage | unit of work | dominant cost | how it fails | fix loop |
|---|---|---|---|---|
| sourcing | a query | search API calls | returns junk / nothing | prompt + ranking |
| acquire | a URL | bandwidth, disk | platform blocks, no media | extractor + screen |
| lake | a file | $ per hour indexed | timeout, partial upload | retry + resumable |
| labeling | a video | tokens per minute | wrong verdict, bad spans | model + prompt |
| curation | a set | almost nothing | wrong grade, missed dup | gates + thresholds |

An agent optimizing "tokens per labeled minute" and an agent optimizing
"download success rate on Instagram" have nothing to say to each other. That is
exactly what we want.

---

## 3. Contracts: the only thing that is shared

Five models and one envelope. They live in `i2e_core/contracts.py` and nowhere
else. A stage reads one and writes the next; it never imports a sibling stage.

```python
# packages/core/src/i2e_core/contracts.py

CONTRACT_VERSION = "1.0.0"


class Candidate(BaseModel):
    """sourcing → acquire. A URL we think is worth spending a download on."""
    url: str
    platform: str
    platform_id: str | None = None
    title: str | None = None
    creator: str | None = None
    duration_seconds: int | None = None
    published_at: str | None = None

    viewpoint: Viewpoint = Viewpoint.UNKNOWN
    viewpoint_confidence: float = 0.0
    viewpoint_evidence: list[str] = Field(default_factory=list)
    viewpoint_verified: bool = False        # frames were looked at, not just words
    relevance: float = 0.0
    found_by: str | None = None             # which search backend, for attribution


class LocalClip(BaseModel):
    """acquire → lake. Bytes on disk, plus what only the download knows."""
    candidate: Candidate
    path: Path
    size_mb: float
    duration_seconds: int | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    container: str | None = None
    uploader: str | None = None
    license_note: str | None = None


class LakeVideo(BaseModel):
    """lake → labeling. Indexed footage, addressable and searchable."""
    video_id: str
    source: Candidate
    media: MediaFacts
    indexed: bool
    captions_available: bool
    transcript_available: bool


class ClipLabels(BaseModel):
    """labeling → curation. One clip's verdict and its annotation tree."""
    video_id: str
    accepted: bool
    rejection_reason: str | None = None
    frame_check: FrameCheck | None = None
    segments: list[Segment] = Field(default_factory=list)
    annotations: list[ClipAnnotation] = Field(default_factory=list)
    annotation_level: str = "L0"
    tags_written: list[str] = Field(default_factory=list)


class DatasetManifest(BaseModel):
    """curation → out. The deliverable."""
    query: str
    clips: list[ManifestClip]
    hours: HoursLedger
    grade: str
    dataset_checks: list[GateCheck]
    cost: CostBreakdown
```

### The envelope

`pipeline/ingest.py` already draws the distinction that matters most in this
system, and it should be promoted from one file to the contract layer: a stage
can end in four different ways, and conflating them is how a run reports
"nothing survived collection" with an empty list of reasons.

```python
class Outcome(StrEnum):
    OK       = "ok"        # produced a value
    REJECTED = "rejected"  # a judgement: the clip is not wanted, and why
    PENDING  = "pending"   # ran out of budget/time; resumable, nothing lost
    FAILED   = "failed"    # a fault: our bug or their outage


class StageResult(BaseModel, Generic[T]):
    outcome: Outcome
    value: T | None = None
    reason: str | None = None          # required for REJECTED and PENDING
    error: str | None = None           # required for FAILED
    metrics: StageMetrics              # always
    trace: AgentTrace | None = None    # when a model was in the loop
    notes: list[str] = Field(default_factory=list)


class StageMetrics(BaseModel):
    stage: str
    implementation: str                # "labeling.cleaning@v2" — which code ran
    wall_seconds: float
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    api_calls: dict[str, int] = Field(default_factory=dict)
    retries: int = 0
```

`StageMetrics` is not bookkeeping garnish. It is the thing the per-package
scorecards and the daily README table are computed from, and it is the reason a
stage's cost can be attributed to the stage rather than to the run.

### Ports: how labeling reads frames without depending on the lake

The labeling agent needs frames, captions and tag writes. Those live in the
lake. If `labeling` imports `lake`, we are back to a chain — and labeling's eval
can no longer run without a real, paid, indexed video.

So the *interfaces* live in core and the *adapters* live in the packages that
own the resource:

```python
# packages/core/src/i2e_core/ports.py

class FrameSource(Protocol):
    async def frames(self, video_id: str, at: Sequence[float]) -> list[Frame]: ...

class MomentReader(Protocol):
    async def captions(self, video_id: str) -> list[Caption]: ...
    async def search_moments(self, video_id: str, q: str) -> list[Moment]: ...

class TagWriter(Protocol):
    async def write(self, video_id: str, tags: Sequence[str]) -> None: ...

class SearchBackend(Protocol):
    name: str
    async def search(self, q: SearchQuery) -> list[Candidate]: ...
```

`i2e_lake` ships `LakeFrameSource`, `LakeMomentReader`, `LakeTagWriter`.
`i2e_eval` ships `RecordedFrameSource` and friends, backed by fixtures on disk.
The orchestrator decides which one gets injected. `i2e_labeling` knows about
neither.

This single inversion is what turns "one long serial pipeline" into "five boxes
that can each be worked on and measured alone".

### Implementations are named and versioned

An agent improving a stage does **not** edit the current implementation in
place. It adds one beside it and flips a default in its own package's config:

```python
# packages/labeling/src/i2e_labeling/registry.py
CLEANING: dict[str, type[CleaningStage]] = {
    "captions@v1": CaptionOnlyCleaning,     # cheap, words only
    "frames@v1":   FrameLookingCleaning,    # current default
    "frames@v2":   TwoPassFrameCleaning,    # an agent's experiment
}
DEFAULT = "frames@v1"
```

Consequences worth spelling out: experiments are additive, so two agents can
have two live experiments in the same package without conflicting; every
scorecard says which implementation produced it; and a regression is reverted by
changing one string, not by reverting a diff.

---

## 4. What each package looks like inside

Identical anatomy, so an agent dropped into any of them knows where it is:

```
packages/labeling/
  pyproject.toml            deps: i2e-core only
  README.md                 what this box does, its metric, how to run its eval
  src/i2e_labeling/
    __init__.py             the public surface — the stage class and its result
    stage.py                the one entry point: (LakeVideo, Requirements) -> StageResult[ClipLabels]
    registry.py             named implementations + the default
    cleaning/…              domain code, free to be as messy as it needs
    annotation/…
    prompts/                text, versioned as files, so a prompt diff is reviewable
  tests/                    fast, offline, no network, no keys
    test_contract.py        asserts what it emits validates against i2e-core
  eval/
    suite.py                the measured runs
    fixtures/               recorded inputs — the reason this runs alone
    scorecard.json          last committed result (generated, never hand-edited)
    scorecard.md
```

Two rules make this hold:

1. **`__init__.py` is the API.** Anything not exported there is private, and a
   sibling package importing it is a layering violation caught by CI.
2. **`prompts/` is files, not string literals in Python.** A prompt change then
   shows up as a prompt diff, which is the single highest-leverage review
   surface in a system like this.

### Fixtures are the actual unblocker

Every boundary gets a recorded fixture set, committed:

| package | its eval replays | so it does not need |
|---|---|---|
| sourcing | golden query set + recorded search API responses | any download |
| acquire | a URL list per platform, live (bandwidth is cheap) | search, lake |
| lake | small local files + recorded operation polls | search, labeling |
| labeling | recorded frames, captions, moments per `video_id` | search, download, upload |
| curation | `ClipLabels[]` JSON for whole sets | everything upstream |

`labeling`'s eval is the one that pays off most: today measuring a prompt change
means an hour and real dollars of upstream work; with recorded frames it is
seconds and a bounded token bill, which is the difference between an agent
iterating twenty times a day and twice.

Fixtures are recorded by `i2e_eval record --stage labeling --video-id …`, which
runs the real adapter and writes the responses to disk. Recording is a
deliberate, occasional act; replay is the default.

---

## 5. The orchestrator holds no domain logic

Today `pipeline/ingest.py` interleaves the pipeline's shape with deadline
arithmetic, disk cleanup, upload strategy and stage-level decisions. After the
split it keeps only the things that are genuinely about *the run*:

- **Composition.** The stage order, and which named implementation of each.
- **Budgets.** The deadline floors per stage (already a good idea — keep it) and
  the "stop before a stage that cannot finish" rule.
- **Concurrency, per stage.** Separate semaphores, because the bottlenecks
  differ: `acquire=8` (bandwidth), `lake=3` (provider limits), `labeling=4`
  (tokens/min), `sourcing=1` per query.
- **The run ledger.** One JSONL per run, one record per stage attempt, keyed by
  `(run_id, clip_id, stage)`. This is what makes `--resume` work, and it is also
  the raw material for every scorecard.
- **Injection.** Which adapters the stages get — real lake, or recorded.

Every stage must be **idempotent on `clip_id`**, so a re-entered run skips what
the ledger says is done. That requirement is what later allows any stage to be
moved behind a queue without touching its code.

---

## 6. How many agents work at once

### Ownership

One agent, one package, one branch, one worktree:

```bash
git worktree add ../i2e-labeling  agent/labeling/frame-gates
git worktree add ../i2e-sourcing  agent/sourcing/rank-v2
git worktree add ../i2e-acquire   agent/acquire/ig-extractor
```

A PR from `agent/<pkg>/…` may touch `packages/<pkg>/**` and nothing else. CI
enforces it (`scripts/check_paths.py`), and the escape hatch is a label, not a
convention.

### The roster

| agent | package | its metric | its command | must not touch |
|---|---|---|---|---|
| **A. Sourcing** | `sourcing` | candidate precision@k (survives acquire's screen), recall on golden queries, $/accepted candidate | `uv run i2e-eval sourcing` | anything downstream |
| **B. Acquire** | `acquire` | download success rate per platform, false-reject rate of the metadata screen, MB/s | `uv run i2e-eval acquire` | search ranking, lake |
| **C. Lake** | `lake` | index success rate, time-to-indexed p50/p95, retry rate, $/hour indexed | `uv run i2e-eval lake` | labeling verdicts |
| **D. Labeling** | `labeling` | gate agreement vs human labels, boundary F1, caption 5-scale, tokens per labeled minute | `uv run i2e-eval labeling` | gates that belong to curation |
| **E. Curation** | `curation` | grade agreement vs human grader, dup precision/recall, ledger invariants | `uv run i2e-eval curation` | per-clip verdicts |
| **F. Integration** | `orchestrator`, `eval` | end-to-end accepted-and-labeled hours per query, $/accepted hour, p95 wall clock, resume correctness | `uv run i2e-eval e2e` | any stage's internals |

Agent F is the one that runs on a schedule, on `main`, and publishes the rolled
up table. Agents A–E never run the end-to-end suite; that is the whole point.

### Changing a contract

The one thing that must not be done in parallel.

- **Additive is free.** A stage may add an *optional* field to the contract it
  emits. Nothing downstream breaks.
- **Anything else is a contract PR**: touches `packages/core/**` only, bumps
  `CONTRACT_VERSION`, updates the golden JSON snapshots in
  `packages/core/tests/golden/`, and lands **alone** before any dependent work.
- Removing or renaming a field is a two-step deprecation across two contract
  PRs, never one.

The golden snapshots are what make this enforceable: a contract change that
forgets to update them fails CI, and a contract change that updates them is
visible in review as a data diff rather than as a class definition diff.

### The files that cause conflicts anyway

Three, and each gets a mechanical fix:

- **`README.md` (60k, one file).** Split: per-package README owns its own box;
  the root README keeps the narrative and a **generated** metrics table.
  `scripts/rollup_scorecards.py` writes it from `packages/*/eval/scorecard.json`,
  and only agent F's scheduled job commits it. No agent hand-edits it.
- **`pyproject.toml`.** Per-package now. The root one is a workspace member list
  that changes once per package, ever.
- **`uv.lock`.** Regenerated only by the scheduled integration job. Conflict
  protocol for everyone else: `git checkout --theirs uv.lock && uv lock`, never
  a hand merge.

### CI

Path-filtered matrix, so a labeling PR does not wait on a sourcing test run:

```
per-package job   ruff · mypy --strict · pytest packages/<pkg>/tests   (only if that path changed)
layering job      scripts/check_layering.py — no stage imports a sibling
contract job      every package's emitted contracts validate against core's goldens
paths guard       an agent/<pkg>/ branch touched only packages/<pkg>/**
e2e job           on main, scheduled — not on PRs
```

`check_layering.py` is twenty lines walking the AST for
`from i2e_<sibling>` and is the single highest-value test in the repo: without
it the boundaries decay back to today's graph within a month.

---

## 7. Runtime parallelism comes free, later

Development parallelism is the goal above. But the same seam gives runtime
parallelism when it is needed, and it is worth being explicit that **we do not
build for that yet**:

- **Now:** in-process `asyncio`, per-stage semaphores, one machine. A run with
  40 candidates already overlaps 8 downloads with 3 indexes with 4 labelings.
- **When it hurts:** each stage is `(contract) -> StageResult`, idempotent on
  `clip_id`, with no shared mutable state — so a stage moves behind a queue by
  replacing the orchestrator's `await stage.run(x)` with an enqueue and a
  ledger-driven continuation. No stage code changes.

Introducing a broker before a single machine is saturated would buy nothing and
cost every agent a local development story. The requirement for now is only that
we do not make the later move impossible, and idempotency is the whole of that
requirement.

---

## 8. Migration, in an order that is itself parallel

**Phase 0 — carve `core`. One PR, no logic changes, everyone waits for it.**
This is the only serial step. It moves the utilities that cause all four cycles
and writes the contracts:

| move | from | to |
|---|---|---|
| `Viewpoint`, `classify_viewpoint` | `curation/viewpoint.py` | `i2e_core/viewpoint.py` |
| `parse_json_object`, ReAct loop, `AgentTrace` | `agent/react.py`, `agent/react_loop.py` | `i2e_core/react/` |
| `CostBreakdown`, pricing, token accounting | `curation/cost.py`, `config/pricing.py` | `i2e_core/cost.py` |
| `read_mp4_dimensions` | `pipeline/media_probe.py` | `i2e_core/media.py` |
| LLM clients | `api/llm.py`, `api/gemini_client.py`, `api/openrouter_client.py` | `i2e_core/llm/` |
| settings | `config/settings.py` | `i2e_core/settings.py` |
| tool base, registry, retry | `tools/{base,registry,retry}.py` | `i2e_core/toolkit/` |
| `Segment`, `FrameCheck`, `ClipAnnotation`, `HoursLedger`, `GateCheck` | `curation/*`, `models/*` | `i2e_core/contracts.py` |
| ports (`FrameSource`, `MomentReader`, `TagWriter`, `SearchBackend`) | — | `i2e_core/ports.py` (new) |

After Phase 0 the import graph is a star, and `check_layering.py` passes.

**Phase 1 — five PRs that can land in any order, one agent each.** Each moves
one stage's files into its package, adds `stage.py` as the single entry point,
and leaves `video_searching_agent` re-exporting from the new home.

| package | absorbs |
|---|---|
| `sourcing` | `tools/{youtube,exa,tiktok_apify,instagram_apify,twitter_apify,video_search,sorting}.py`, `api/apify_client.py`, `router/{query_parser,classifier}.py`, `curation/{query_rewrite,relevance}.py`, the search loop from `agent/core.py`, `agent/clarification.py` |
| `acquire` | `pipeline/{download,youtube_fetch}.py`, the `screen`/`look` passes of `agent/cleaning_agent.py` |
| `lake` | `api/memories_datalake_client.py`, `tools/memories_datalake.py`, the upload/index legs of `pipeline/ingest.py`, the three lake adapters |
| `labeling` | `agent/{cleaning_agent,annotation_agent,clipping_agent,annotating_agent,quality_check_agent,eyes}.py`, `curation/{frame_check,frame_viewpoint}.py` |
| `curation` | `agent/curation_agent.py`, `curation/{quality_gates,scoring,manifest,export}.py`, `models/dataset.py` |

Note that `agent/cleaning_agent.py` (960 lines) splits across two packages:
the metadata screen and the pre-download look belong to `acquire` (they decide
whether to spend the download), the frame gates and segmenting belong to
`labeling` (they decide what the footage is worth). That split is the honest one
even though it is the awkward one — the two halves answer different questions and
are paid for at different times.

**Phase 2 — orchestrator and service.** What is left of `pipeline/ingest.py`
becomes composition, budgets, ledger and injection. `web/` becomes
`i2e_service` and gets thinner: it should compose stages, not know them.

**Phase 3 — per-package evals and fixtures.** The five stage agents each record
their fixtures and write their suite. This is where parallel work actually
starts paying, and it is deliberately last: an eval written before the boundary
exists measures the old tangle.

**Phase 4 — delete the shim.** `video_searching_agent` goes when nothing
imports it. Until then it is what keeps the deployment and the QA scripts alive.

---

## 9. What we are deliberately not doing

- **Not separate repositories.** A monorepo keeps contract changes atomic and
  keeps one command able to run everything. Separate repos would make Phase 0
  and every future contract PR a multi-repo dance for no gain.
- **Not published/versioned packages.** Path dependencies in a `uv` workspace.
  `CONTRACT_VERSION` plus golden snapshots gives the discipline that semver
  would, without the release overhead.
- **Not a message broker, not Celery, not Kafka.** See §7.
- **Not microservices.** These are import boundaries, not network boundaries.
  Nothing here requires a second process, and adding one would cost the local
  development story that makes agent iteration fast.
- **Not one agent per file or per class.** The unit of ownership is a box with
  its own metric. An agent without a number it is trying to move is an agent
  producing diffs nobody can evaluate.

---

## 10. The one-paragraph version

Move the five utilities that cause every import cycle into `i2e-core`, and put
five frozen contracts and four ports beside them. Give each pipeline stage its
own distribution that depends on core and nothing else, its own named and
versioned implementations, its own recorded fixtures, its own eval, and its own
metric. Keep a thin orchestrator that composes stages, spends the budget, and
writes a ledger. Then hand each box to one agent on its own branch in its own
worktree, let CI enforce that the boxes stay boxes, and roll the per-package
scorecards up into one table on a schedule. The parts fit together because the
contracts never move without a PR that does nothing else.
