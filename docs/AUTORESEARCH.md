# Auto-research — the hourly improvement loop

This file is the working memory of an hourly cycle. Each iteration a fresh
session reads this document and the tree, does **one** well-chosen piece of
work, records what it measured here, and pushes. Eight iterations converge on:
verifiable modules, a defined metric set with an eval report, a settled
architecture, and this methodology itself — plus a final report and a UI that
browser QA has verified.

The companion documents:

- `docs/MODULES.md` — the architecture target: eight stages, core types
  (`Measured`, `Spend`, `Verdict.gated`, `Outcome`), ports with replay
  adapters, calibration fixtures as package contents.
- `eval/README.md` — the metric definitions: yield funnel, A/B/C/D bands, cost
  attributed two ways, stratified by difficulty and family.
- `qa/run_qa.py` — the recurring health sweep (separate cadence, do not merge).

## Method

Each iteration, in order, timeboxed to well under an hour:

1. **Read** — this file's log (below), then the newest code touched since the
   last entry (`git log --since`), then one module chosen by the *worst-measured*
   rule: work on whatever currently has the weakest measurement, not whatever
   is most interesting.
2. **Ask one question that has a measurable answer.** "Is the boundary between
   screening and sourcing right?" is not measurable. "Does the screen's
   wrong-rejection rate change if the frames tier gets hq1 stills?" is.
3. **Measure before changing.** Every constant in this repo that was guessed
   has been wrong (the 8-word query cut, the blur filter, the score cutoff);
   every one derived from footage has held. If the answer needs footage, spend
   up to ~$0.50 getting it; record the spend.
4. **Change the smallest thing the measurement justifies**, with a test that
   would have caught its absence. Run `uv run pytest -q` and `uv run ruff
   check`; for UI work, `npm --prefix ui run build` and the Playwright flow
   (`ui/qa/flow.mjs` against `ui/qa/stub_api.py`).
5. **Log it here** (format below), push to `claude/video-search-agent-opensource-oxticx`
   on origin AND `public HEAD:main`. Scan for secrets first. Never commit
   `.env` or `data/`.
6. **On the eighth entry and after**: stop opening new questions. Write
   `docs/REPORT.md` — the consolidated report (modules and their verification
   status, the metric definitions and the numbers actually measured, the
   architecture as-built vs `MODULES.md`, and this method with what it found
   hour by hour). Verify the UI once more in the browser. Push.

Hard rules, learned the expensive way — do not relearn them:

- **No constant without a fixture.** A threshold nobody measured is a guess
  with a decimal point.
- **Scores rank; they do not measure.** No embedding-score cutoffs, ever
  (gibberish scores 0.354 vs a true query's 0.400).
- **Unmeasured is not zero.** `measured: false` excludes; it never fails.
- **Cost `None` is not cost `0`.** Count unpriced calls separately.
- **The boundary-name rule:** never guess a vendor parameter. The Datalake
  *silently ignores* unknown top-level search params (`video_id=` returns other
  videos' hits while looking scoped); only `filter.video_ids` works. The upload
  endpoint accepts only `title` and `custom` metadata keys and its error says
  "invalid JSON" when it means "unknown key".
- **`self.gemini`, not `self.llm`** in agent classes — the tests replace only
  the former; the latter reaches the real network (bitten twice).
- The eval's frozen query set is immutable (`eval/queries.json` v1.0). Changes
  to metrics may be re-scored over old run records with `--score-only`.

## What "verifiable module" means here

A module counts as verifiable when all four hold:

1. **Typed input and output** at its boundary (the contracts in `MODULES.md`
   §3), with a four-state `Outcome` — ok / rejected / pending / failed.
2. **An offline test path** — replay fixtures or fakes; the suite must not
   spend money or reach the network (`tests/conftest.py` enforces the paid
   switches off).
3. **A calibration or eval set it can be scored against**, with the score
   reproducible by one command.
4. **Its constants derived from fixtures by a test**, so a nudge without new
   evidence fails CI.

Current status (update this table each iteration):

| module | typed I/O | offline tests | scoreable | constants pinned |
|---|---|---|---|---|
| sourcing (search + rewrite) | partial | yes | yes — eval dry run | n/a |
| screening (frames, 2 questions) | partial | yes | yes — 19-candidate set | in docstrings only |
| acquire (probe/download) | partial | yes | no | n/a |
| lake (Datalake client) | no — raw dicts | yes | live contract probes, ad hoc | n/a |
| labeling (ReAct agents) | partial | yes | no — needs cassettes | n/a |
| refine (cut/clean/upload) | yes | yes | yes — 3-clip calibration | in docstrings only |
| curation (gates/scorecard) | partial | yes | yes — validation set | partly |
| audit (quality check) | partial | yes | partial | n/a |
| store + clips API + library UI | yes | yes | browser QA flow | n/a |

## Open questions, ranked by measurement value

1. The screening set is 19 candidates from 5 queries. Grow it to ~50 across
   more task families and re-measure the two-question accuracy; that set then
   becomes `packages/screening/calibration/`.
2. Cassette recording for the labeling agents (`FrameSource` / `MomentReader`
   replay) — the single biggest iteration-speed lever (`MODULES.md` §4).
3. The keyframe-aligned cut: a requested 20.0s span returned 22.0s and 23.0s
   clips. Measure the drift distribution over ~10 cuts; G2-SEG's ±0.3s cannot
   be met by this mechanism and the report must say what can.
4. `frame_embedding` dedup: measure near-duplicate detection on clips cut with
   overlapping spans from one source before writing any dedup code.
5. The five file moves that clear four import cycles (`MODULES.md` §8 step 1),
   plus `scripts/check_layering.py`.
6. Labels are null on the real clips in the store — the annotation pass has
   not run over the clean collection. Wire `label_span` over clean clips and
   store the trees (task #13).

## Iteration log

Newest last. Format: `### N · <UTC time> · <question asked>` then findings —
what was measured, what changed, what it cost, test count. Claims without a
measurement get marked *(unmeasured)*.

### 0 · 2026-08-22 ~11:00 · seed (Opus session, context in the session log)

The state this loop starts from. 982 tests passing; ruff clean; browser QA 14
steps clean. Since 08:00 UTC: query rewriting fixed (dangling-preposition
templates; one retry on unparseable model replies) and wired into the
streaming path it had never been on; the pre-download look asks viewpoint +
activity + world (three-way answers, only "other_kind"/"screen" reject);
`frame_embedding` search built with scoping and score-semantics pinned;
`clip_quality` calibrated on real footage (no blur filter — sharpness measures
texture: usable footage at 96, an end card at 4144); refine cut-clean-upload
proven live into `egoexo-clean-clips` (col_pelhcnsu2avutdnyamgnshohxu);
annotation store + `/api/v1/clips` + Library view built and browser-verified.
Known defects open: the Unity screen-recording clip is in the clean collection
(the `world` question now exists but old clips predate it — re-screen them);
clip labels are null (annotation not yet run over the clean collection); the
eval's 40-query dry run measured 70% of queries finding candidates, $0.05/query
discovery, and a query set with visible simulator noise (`blocks ranking rgb`).
