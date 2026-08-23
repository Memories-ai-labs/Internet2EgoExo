# Architecture, as built

What exists today, and where the state lives. `MODULES.md` is the *target* — the
module contracts, core types and package split we are moving toward. This file is
the honest description of the thing that currently runs, so an iteration can tell
the two apart and know which one it is reading.

## The one-line shape

A query goes in; clean, annotated, graded clips come out, indexed in the
Datalake with their trees in a local database, browsable in a web UI.

```
query
  │
  ├─ 0 SOURCE ......... rewrite the task into footage-shaped searches,
  │                     fan out to YouTube / Exa / Apify / the open web
  ├─ 1 SCREEN ......... sample stills, ask one VLM look three questions
  │                     (viewpoint, activity, world) — reject on one answer each
  ├─ 2 ACQUIRE ........ probe, then download the survivors
  ├─ 3 INDEX .......... upload to the Datalake, wait for the operation
  ├─ 4 CLEAN .......... propose anchors, mark idle time, measure clip quality
  ├─ 5 ANNOTATE ....... read spans, build the task → action → event tree
  ├─ 6 GRADE .......... four gates, a 0-100 score, an A/B/C/D band
  ├─ 7 REFINE ......... cut the accepted spans, re-clean, upload to the
  │                     clean collection with provenance in `custom`
  └─ 8 STORE .......... tree rows keyed on the clean clip's Datalake video_id
                        │
                        └─ /api/v1/clips → the Library view
```

Stages 0-6 stream over SSE, so the UI shows the funnel as it happens rather than
after it finishes.

## Where the code is

| stage | package | the load-bearing files |
|---|---|---|
| 0 source | `curation/`, `tools/` | `query_rewrite.py`, `relevance.py`, the search tools |
| 1 screen | `curation/` | `frame_viewpoint.py`, `frame_check.py`, `api/gemini_client.py` |
| 2 acquire | `pipeline/` | `media_probe.py`, `download.py`, `youtube_fetch.py` |
| 3 index | `pipeline/`, `api/` | `ingest.py`, `memories_datalake_client.py` |
| 4 clean | `agent/`, `pipeline/` | `cleaning_agent.py`, `clipping_agent.py`, `clip_quality.py` |
| 5 annotate | `agent/` | `annotation_agent.py`, `annotating_agent.py`, `eyes.py` |
| 6 grade | `curation/` | `quality_gates.py`, `scoring.py`, `curation_agent.py` |
| 7 refine | `pipeline/` | `refine.py` |
| 8 store | `store/`, `web/routers/` | `annotations.py`, `clips.py` |
| — search | `curation/` | `embedding_search.py` (`frame_embedding`, per-second) |
| — eval | `evaluation/`, `eval/` | `metrics.py`, `scorecard.py`, `run_eval.py` |
| — web | `web/` | `app.py`, `main.py`, `routers/`, `demo.py` |

The agents are ReAct loops (`agent/react.py`, `react_loop.py`) under a tool
policy (`agent/tool_policy.py`), each verdict carrying its Thought → Action →
Observation trace so an inclusion can be defended later, not just made.

## Where state lives — three stores, deliberately

This is the part most worth understanding, because conflating any two of them
has already caused bugs.

**1. The Datalake holds pixels.** Videos, keyframes, transcripts, embeddings.
It can hand back a signed playback URL and its own auto-tags. It is *not* an
annotation database: there is nowhere in it to put a task → action → event tree,
which is exactly why store 2 exists. Two collections matter — the raw ingest, and
`egoexo-clean-clips` (`col_pelhcnsu2avutdnyamgnshohxu`) which holds only cut,
cleaned, accepted footage.

**2. The annotation store holds trees** (`store/annotations.py`, SQLite). Two
tables, `clips` and `segments`, the latter self-referencing via
`parent_segment_id` so the hierarchy is rows rather than a blob. Keyed on the
clean clip's Datalake `video_id` — **that id is the join**, and it is the whole
reason the Library can answer "find me folding" for a clip whose title never
says so. Falls back to `:memory:` when the host has nowhere writable, and the
API reports `store.persists` so an empty corpus can be told apart from a
forgetful host.

**3. The run records hold measurements** (`eval/results/*.jsonl`). Append-only,
one line per query, scoreable offline with `--score-only`. Never overwritten,
because two scorecards are only comparable if the records behind them survive.

Signed URLs are fetched at read time and never stored — a stored one is a link
that works until it quietly does not.

## The API surface

| route | what it does |
|---|---|
| `POST /api/v1/queries/stream` | the search + screen funnel, SSE |
| `POST /api/v1/collect/stream` | download → index → clean → annotate a URL list |
| `POST /api/v1/curate/stream` | clean, annotate and grade an indexed worklist |
| `GET /api/v1/clips` | search the clean clips (text, viewpoint, grade, hands) |
| `GET /api/v1/clips/facets` | totals plus the label vocabulary actually present |
| `GET /api/v1/clips/{video_id}` | one clip, its whole tree, a playback URL |
| `GET /api/v1/health` | tool-by-tool health, model in use |

`DEMO_MODE=1` serves every route from `web/demo.py` with no keys and no spend,
which is what browser QA runs against.

## What the architecture gets right

- **Asymmetric filters are drops, not low ranks.** Wrong viewpoint, no hands,
  screen capture — these remove a candidate rather than penalising it. That is
  what makes the output defensible instead of merely sorted.
- **One join key.** Everything about a clean clip hangs off its Datalake
  `video_id`, in both directions.
- **Cost is attributed, and unpriced calls are counted separately.** `cost None`
  is never folded into `cost 0`.
- **Demo mode is a real second implementation** of every route, so the UI is
  testable end to end without a cent of spend.

## What it gets wrong, honestly

- **Import cycles.** Four of them; `MODULES.md` §8 step 1 lists the five file
  moves that clear them, plus the `scripts/check_layering.py` that would keep
  them clear. Not done.
- **The Datalake client returns raw dicts**, so its boundary is untyped and its
  contract lives only in probe scripts and this documentation. It is the one
  module with no typed I/O at all.
- **Acceptance and grade are computed in the curation agent**, which is also
  where they were allowed to disagree (see `LEARNINGS.md` L1). The gates should
  own the decision outright.
- **No replay layer for the agents.** `FrameSource` / `MomentReader` cassettes
  are the single biggest iteration-speed lever and do not exist, so every
  annotation-agent question costs real money to answer.
- **Calibration sets are not package contents.** The screening set lives as 19
  ad-hoc candidates and the clip-quality thresholds are justified in a
  docstring rather than re-derived by a test.
- **`clip_embedding` returns nothing** and we do not know why. Not a length
  effect: empty for a 22-second clip and a 400-second video alike.

## Deployment

FastAPI serves both the API and the built UI (`web/static/`). Vercel hosts the
public deployment; the UI is Vite + React on the Memories AI design language,
with three views — search, collect, and the Library over the clean clips.
Browser QA (`ui/qa/flow.mjs`, Playwright) drives the real app in demo mode
across 14 steps.

The eval runs somewhere else, and always through one script. `eval/run.sh` is the
only definition of a measurement — key check, server start, health wait,
`--resume`, scoring — and its three callers are `.github/workflows/eval.yml`
(the daily 20-query slice), `.github/workflows/eval-chunk.yml` (the full 200 in
four chunks, because a GitHub job is capped at 6 hours) and
`deploy/runner/egoexo-eval.service` (an always-on VM, `bootstrap.sh` plus three
systemd units, platform-neutral). A test asserts none of them calls
`run_eval.py` directly again. Run only one host at a time: two would buy the
same daily datapoint twice.
