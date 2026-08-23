# Auto-research

## Why this exists

This project has one hard problem — deciding which web video is worth keeping —
and no ground truth to check the decision against. Every threshold in it was
either guessed or measured, and the guessed ones have been wrong every single
time (`LEARNINGS.md` L3). So the improvement process cannot be "have a good idea
and ship it". It has to be a loop that measures, changes one thing, measures
again, and writes down which way the number went.

Auto-research is that loop, run by a fresh session on a schedule. It starts from
nothing every time — no memory of the last run, no context beyond this folder.
That constraint is the design, not a limitation: anything worth knowing has to be
*written down here* or it does not survive to the next iteration. A loop that
depends on remembering is a loop that quietly stops working.

What it produces, over iterations: modules whose behaviour is verifiable, a
metric set with real numbers behind it, an architecture that got there for
stated reasons, and a record of every idea tried — including the ones that
failed, which are the expensive ones to rediscover.

## What is in here

| file | what it is for |
|---|---|
| `README.md` (this) | why the loop exists, the method, the hard rules, the promotion rule |
| `ARCHITECTURE.md` | what the system actually is today, and what it gets wrong |
| `MODULES.md` | the architecture *target*: module contracts, core types, the package split |
| `INSPIRATION.md` | the idea bank — things worth trying, each with the measurement that would settle it, refilled from related work and past learnings |
| `LEARNINGS.md` | what the experiments taught us, distilled: the things that generalised |
| `experiments/<date>.md` | one file per day, the objective record: what was run, what the numbers did, where it improved and where it did not |

Read them in that order on a first pass. On an ordinary iteration read
`LEARNINGS.md`, the newest `experiments/` file, and `INSPIRATION.md` — those
three are enough to pick work.

The distinction between the last three matters and is easy to blur:

- **`experiments/<date>.md` is objective.** What was run, before and after, no
  interpretation. Every day gets a file whether or not anything worked.
- **`LEARNINGS.md` is the distillation.** Only what generalised beyond the one
  experiment, each entry naming the experiment it came from.
- **`INSPIRATION.md` is forward-looking.** Untested ideas, each with its
  falsifier. Entries leave it by being tested, and leave a verdict behind.

## The goal, in one sentence

**Valid clips out the other end.** A clip is valid when the hands are in frame,
the manipulation is legible, and there is a tree over it whose atomic actions
name what the left hand did, what the right hand did, and to which objects.
That is the deliverable and the only thing worth optimising.

Explicitly **out of scope**, and not to be reintroduced: depth annotation,
skeletons or pose keypoints as an output, and annotation *depth for its own
sake* — the L0/L1/L2/L3 ladder is a description, not a target. A clip at L2 that
says what both hands did is worth more than an L3 that does not.

Two things follow, both already applied:

- **Licence is out of the grade.** A clip is exactly as trainable whether or not
  its uploader ticked Creative Commons. It was worth 7 points, which was exactly
  the C/B boundary, so it capped every non-CC clip at a C; it now scores nothing
  and only blocks when commercial use is explicitly required.
- **`valid` is the headline metric**, in scorecard section 0, above the grade
  bands. Compare runs on **valid clips per query asked** — per query *asked*, so
  a run cannot improve by failing to search.

## The objective is the scoreboard

The first iterations aimed at making modules verifiable, and that groundwork is
largely in place. From here an iteration exists to move a measured number in the
newest `eval/results/*.scorecard.md` — acceptance rate, A/B share, usable hours
per query, anchors per usable hour, cost per accepted clip — or to establish with
evidence why a number *cannot* move. Verifiability is the means now, not the end:
make a module verifiable when that is what blocks a measurement.

One corollary, because it is the tempting shortcut: **never move a threshold, a
gate weight or a grade band to make a number look better.** Improving the
pipeline is in scope; improving the instrument's flattery is not. A metric that
is genuinely wrong gets fixed with an argument in the log and old records
re-scored via `--score-only`, so history stays comparable.

Outside this folder: `eval/README.md` has the metric definitions (yield funnel,
A/B/C/D bands, cost attributed two ways, stratified by difficulty and family),
and `qa/run_qa.py` is the recurring health sweep — a separate cadence, and not
to be merged into this loop.

## Where the loop actually runs — current state, 2026-08-22

Honest, because a fresh session will otherwise assume the schedule is working.
Both scheduled loops are **stopped**, for the reasons in `experiments/2026-08-22.md`
experiment 8 and `LEARNINGS.md` L13-L14:

| loop | state | why |
|---|---|---|
| hourly auto-research routine | **disabled**, not deleted | 7 fires, 0 pushes; its tool grant has no `mcp__*` entries while its first step is an MCP call |
| eval keep-alive routine | **deleted** | an hourly poke cannot carry an 8-hour job in a container reclaimed on idle |
| eval on GitHub Actions | **built, never run** | needs 6 repository secrets, which only Shawn can add |

So an iteration today is a session Shawn starts, not a schedule. Restoring the
schedule needs, in order: the six secrets (`OPENROUTER_API_KEY`,
`GOOGLE_API_KEY`, `YOUTUBE_API_KEY`, `MEMORIES_API_KEY`, `APIFY_API_TOKEN`,
optionally `EXA_API_KEY`, all rotated first) so `eval.yml` can produce a
scoreboard, and then either MCP tools in the routine's grant or a first step that
does not need them. Until a scoreboard exists again the newest complete datapoint
is a 34-query prefix, which L10 says reads pessimistic and is not comparable to
anything.

## Method

Each iteration, in order, timeboxed to well under an hour:

1. **Read** — `LEARNINGS.md` first, so you do not repeat an hour somebody
   already spent. Then the newest code (`git log --since`), then the newest
   `eval/results/*.scorecard.md`, which is the scoreboard.
2. **Pick from `INSPIRATION.md`**, by which entry would move the worst number on
   that scoreboard — not by which is most interesting. If nothing there fits
   what the scorecard is telling you, add an entry rather than improvising: the
   next iteration inherits the file, not your reasoning.
3. **Ask one question that has a measurable answer.** "Is the boundary between
   screening and sourcing right?" is not measurable. "Does the screen's
   wrong-rejection rate change if the frames tier gets hq1 stills?" is.
4. **Measure before changing.** Every constant in this repo that was guessed
   has been wrong (the 8-word query cut, the blur filter, the score cutoff);
   every one derived from footage has held. If the answer needs footage, spend
   up to ~$0.50 getting it; record the spend.
5. **Change the smallest thing the measurement justifies**, with a test that
   would have caught its absence. Run `uv run pytest -q` and `uv run ruff
   check`; for UI work, `npm --prefix ui run build` and the Playwright flow
   (`ui/qa/flow.mjs` against `ui/qa/stub_api.py`).
6. **Record it.** The objective account goes in `experiments/<today>.md`
   (create the file if this is the day's first iteration): what was run, the
   numbers before and after, and **where it did not improve, in the same voice
   as where it did**. Anything that generalised beyond this one experiment gets
   distilled into `LEARNINGS.md`. Strike the `INSPIRATION.md` entry with a
   one-line verdict, including when the answer was no.
7. **Push** to `claude/video-search-agent-opensource-oxticx` on origin AND
   `public HEAD:main`. Scan for secrets first. Never commit `.env` or `data/`.
   Then apply the promotion rule below.
8. **Keep `docs/REPORT.md` current** once it exists — the consolidated report
   (modules and their verification status, the metric definitions and the
   numbers actually measured, the architecture as-built vs `MODULES.md`, and
   this method with what it found hour by hour). It is a checkpoint, not an
   ending: the loop does not stop when it is written.

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

## Promotion — when a change may go to `main`

Shawn's standing instruction: **when a run's results beat the previous run, the
change that produced them may go straight to `main`.** The loop does not need to
ask. What it does need is a definition of "beat", because without one this rule
launders every change into a win.

Promote only when **all five** hold:

1. **Same slice.** The comparison is against the previous datapoint in
   `eval/history.jsonl`, measured over the *same* query slice. Two runs over
   different queries are not comparable and their difference means nothing. A
   slice change starts a new series; it never counts as an improvement.
2. **Same metric definitions.** If a definition changed, re-score the previous
   run's records with `--score-only` and compare the re-scored numbers. Comparing
   across a definition change is the most flattering mistake available.
3. **The primary metric improved** — accepted clips per query. Ties break to
   usable hours per query, then to cost per accepted clip (lower wins).
4. **No guard regressed.** Tests green, `ruff` clean, UI build and Playwright
   clean, and **no new contradiction in scorecard §6**. A new §6 entry blocks
   promotion outright however good the primary metric looks: it means the
   pipeline and the standard disagree, and shipping that is worse than shipping
   nothing.
5. **The delta is not one lucky query.** On a 12-query slice a single clip is
   ~8 points, which is noise wearing a decimal point. Record the per-query diff
   and say in `LEARNINGS.md` how much of the delta one query accounts for. If it
   is all of it, that is a `inconclusive` verdict, not a promotion.

Then: `git fetch origin main`, merge the branch into `main` (never rebase or
force-push a shared branch), push, and log the promotion in `LEARNINGS.md` with
the two datapoints side by side.

**Never promote** on: a metric that improved because a threshold moved (see the
corollary above — that is not an improvement, and the promotion rule is exactly
where that temptation pays off); a run that spent nothing because it stopped
early; a partial run compared against a complete one; or a green suite alone,
with no eval datapoint at all. Absent a comparable measurement the change stays
on the branch, and the entry says why.

**The first landing has happened.** Shawn asked for it directly on 2026-08-22
and `main` was fast-forwarded to the branch (PR #2, 75 commits, merged at
`8a0d4c7`). So there is no longer an "open PR" to merge, and both mains —
`origin/main` and the public mirror — track the branch.

What that changes for an iteration: after pushing the branch, **fast-forward
`origin/main` too** when the promotion rule above is satisfied. `git push origin
HEAD:main` is the whole operation while main stays an ancestor of the branch,
which it does as long as nothing else writes to main. If that push is ever
rejected as non-fast-forward, somebody else has committed to main: stop, do not
force, merge main into the branch and open a fresh PR for the result. PR #2 is
merged and cannot track new work — a merged PR is finished, and reusing it is
not possible even if it looks convenient.

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

## Open questions, and carried work

The ideas live in `INSPIRATION.md`, each with the measurement that would settle it.
Pick from there. What stays here is the work that is *not* a question — known
defects and structural jobs whose answer nobody doubts, only their cost:

- **Licence was the binding constraint on grade, and has been removed from it**
  (`LEARNINGS.md` L8, L11). Nothing to optimise here any more; Q-SRC4 is now
  only about yield, not grade.
- **Annotation is *not* the constraint** — an earlier reading said it was, off a
  single anomalous clip. It is producing L2/L3 with 7–9 annotations. Stage 5 of
  `INSPIRATION.md` still matters for the tail (one clip in five returns nothing
  at all), because a clip with no labelled action is invalid by definition — but
  depth beyond "what did each hand do" is not a goal.
- **Hands and legibility are the validity gates.** Both now reject before
  download. `is_screen_capture()` had no callers for its whole existence, so
  the `world` question was billed and discarded — audit for more of that shape.
- **The five file moves that clear four import cycles** (`MODULES.md` §8 step 1)
  plus `scripts/check_layering.py`. Not a question — a job.
- **Labels are null on the real clips in the store**; the annotation pass has
  never run over the clean collection. Wire `label_span` over clean clips and
  store the trees (task #13). Same defect as the first item, seen from the
  product side.
- **One Unity screen-recording clip sits in the clean collection.** Not because
  it predates the `world` question — that was the earlier explanation and it was
  wrong. The question existed and was never wired (`LEARNINGS.md` L11). It is
  wired now, so re-screening the collection will catch it.
- **The `legibility` gate is uncalibrated** (`INSPIRATION.md` Q-SCR4). It is a
  new reject path on the primary criterion, and an uncalibrated reject path can
  silently throw away the corpus. Highest priority in the file.

Two defects in the measuring instrument, both deliberately unfixed:

- **6% of the frozen query set is un-filmable.** 12 of the 200 name robot
  hardware or render artifacts — `picking cube so100`, `picking cube widow xai`,
  `stacking green cube on yellow cube baked tex in scene`, `blocks ranking rgb`,
  `drawing svg`, `sweeping the target to its goal without touching the forbidden
  object`, plus six alike. They can only ever return zero candidates, so every
  acceptance rate carries a ~6% floor loss concentrated in easy/medium. v1.0 is
  frozen and those 12 must not be edited; the fix is to tighten
  `usable_as_query` in `eval/build_query_set.py` and cut a v1.1, leaving v1.0
  intact so published scorecards stay comparable.
- **`eval/run_eval.py:236` records a missing grade as `"D"`** (`str(clip.get(
  "grade") or "D")`), which is this document's own "unmeasured is not zero" rule
  broken in the one place it is most expensive. Fix it only when no run is in
  flight: a running process holds its launch-time code, so editing mid-run
  desynchronises the code from the records it is writing.

## The log

Split in two, on purpose. `experiments/<date>.md` is the objective per-day
record — what ran, what the numbers did, including the baseline everything is
measured against. `LEARNINGS.md` is what generalised out of those days.
