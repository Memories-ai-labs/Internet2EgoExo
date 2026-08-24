# The dataset on disk — the process, and the shape of what comes out

The README describes a pipeline. This describes its *product*: the directory a
run leaves behind, what each file in it means, and the exact sequence that
produces one from nothing.

The distinction matters because for most of this project's life the product did
not exist as a thing you could hold. The footage lived in the Datalake behind a
signed URL that expires in a day, the tree lived in a local SQLite store, and
the provenance lived on a third record again. Each was reachable, and together
they were not a dataset — a dataset is a directory that survives being copied to
another machine.

---

## 1. The output structure

```
<out>/
  manifest.json                  every clip in one array, plus the run's totals
  manifest.jsonl                 the same rows, one per line, for an ingest job
  clips/<video_id>.mp4           the footage
  thumbnails/<video_id>.jpg      one still, so the directory is browsable
  annotations/<video_id>.json    the tree, the provenance, the grade
```

**The filename is the join key.** `clips/vid_x.mp4` and
`annotations/vid_x.json` are the same clip, and `vid_x` is the same id the
Datalake and the annotation store know it by. Nothing has to be consulted to
pair them.

**Every clip gets a JSON, including the ones that failed.** A clip whose media
could not be downloaded is still exported, with `clip_file: null`. Dropping it
would quietly reduce the count and make a broken export look like a small one.

### `manifest.json`

```jsonc
{
  "manifest_version": 1,
  "generated_at": "2026-08-23T06:24:30+00:00",
  "collection_id": "",          // empty when the export was not restricted
  "clips": 10,
  "media_written": 0,
  "media_skipped": 10,          // already on disk, not re-fetched
  "media_failed": 0,
  "clips_with_tree": 9,
  "clips_without_tree": 1,      // cut but not annotated — a real state, see §5
  "total_seconds": 319.0,

  // Held back by the egocentric requirement, split by what the frames said.
  // `exocentric` = looked at and wrong; `unchecked` = step four has not looked
  // yet. Different problems, different fixes, never one bare total.
  "withheld_not_egocentric": 5,
  "withheld_by_viewpoint": {"exocentric": 3, "unknown": 2},
  "removed_stale_files": 10,    // written by an earlier export, since withheld
  "errors": [],
  "items": [ /* one row per clip, longest first */ ]
}
```

`items` rows are the summary fields only — id, paths, duration, provenance,
grade, counts. The full tree is in the per-clip JSON, so the manifest stays
readable at a thousand clips.

### `annotations/<video_id>.json`

```jsonc
{
  "video_id": "vid_py4too3ora7wf6tyqykklhybh4",
  "collection_id": "col_pelhcnsu2avutdnyamgnshohxu",

  // Provenance: which source video, and between which two seconds. This is
  // what G0-PROV checks, and the only reason a clip can be defended to whoever
  // receives it.
  "source_video_id": "vid_6lybavinuafdqdogzokcpvx2rm",
  "source_start": 15.0,
  "source_end": 130.0,
  "source_url": "",

  "title": "someone assembling the cabinet",
  "duration_seconds": 115.0,
  "viewpoint": "egocentric",    // confirmed from THIS clip's frames, in step 4
  "grade": "B",                 // A/B/C/D — see the caveat in §6
  "annotation_level": "L2",
  "accepted": true,

  "segment_count": 2,
  "action_count": 1,
  "segments": [ /* the tree */ ],

  "clip_file": "clips/vid_py4too3ora7wf6tyqykklhybh4.mp4",
  "thumbnail_file": "thumbnails/vid_py4too3ora7wf6tyqykklhybh4.jpg",
  "annotation_file": "annotations/vid_py4too3ora7wf6tyqykklhybh4.json"
}
```

Paths are **relative on purpose**: the directory has to survive being moved or
mounted somewhere else, which an absolute path does not.

### A segment

```jsonc
{
  "segment_id": "t1.a1",
  "parent_segment_id": "t1",
  "hier_level": "action",       // task | action | event
  "span_start": 0.023,          // seconds, in the CLIP's time base, not the source's
  "span_end": 81.023,
  "seconds": 81.0,
  "label": "review-assembly-instructions",
  "narration": "A person holds up an assembly manual, pointing to the diagrams…",
  "hands_visible": true,
  "left_hand": "holds the instruction manual steady",
  "right_hand": "points to diagrams on the manual and brings a small plastic bag…",
  "objects": ["instruction manual", "plastic bag of metal parts", "furniture panels"],
  "evidence": []
}
```

**Spans are in the clip's own time base.** A clip cut from `source@15–130s` has
its first frame at `0.0`, not at `15.0`. This is why step four re-annotates
rather than copying the source video's tree across: a tree in the wrong time
base is not a correction away from being right, it is measuring a different
object.

**`left_hand` / `right_hand` are frequently null, and that is a real answer.**
They are filled when the evidence supports naming a hand and left empty when it
does not. A hand claimed without evidence is discarded in code, so an empty
field means "not established", never "no hand there".

---

## 2. The process, from nothing to a directory

Five steps. Each one spends money and each one is off unless asked for.

| # | What | How |
|---|------|-----|
| 1–3 | search → collect → curate → refine | `eval/run.sh` |
| 4 | annotate the clean clips | `python -m video_searching_agent.pipeline.annotate_clean` |
| 5 | write the directory | `python -m video_searching_agent.pipeline.dataset` |

### Steps 1–3 — `eval/run.sh`

```bash
set -a && . ./.env && set +a          # the script checks keys from the environment
eval/run.sh --limit 20 --per-query 1 --out eval/results/slice.jsonl
```

This is **the one definition of how a run is taken** — the GitHub workflows, the
always-on VM and a laptop all call it, so that a rule derived in two places
cannot come to disagree. It starts the API if nothing healthy is listening,
runs the frozen query set through search → collect → curate → refine, and
scores the records into a scorecard beside them.

Do not hand-call `/api/v1/queries/stream`, `/collect/stream` and `/curate/stream`
to reproduce this. Refine is **deliberately not an API route** — it needs a
writable directory and a decoder, which a serverless function does not have — so
it runs in-process from `run_eval.py`. A hand-assembled sequence of the three
endpoints silently omits step three and produces a run with no clips at all.

`--resume` skips queries already in the record file rather than paying for them
again. Use it for every continuation.

### Step 4 — the viewpoint gate, then the trees

```bash
python -m video_searching_agent.pipeline.annotate_clean --limit 12 --write-back --yes
```

`--yes` is required: this pass calls paid endpoints. `--limit` caps how many
clips one pass will pay for. Without `--all` it only touches clips that have no
tree yet.

**Before a clip is paid to be annotated, its own frames are looked at, and a
clip that is not confirmed first-person does not get a tree.** This is stricter
than the screen before the download, on purpose:

| | before download (`PRE-SIGHT`) | at delivery (this gate) |
|---|---|---|
| looks at | the candidate's storyboard stills | the cut clip's own frames |
| unknown | kept — the caption pass gets the last word | **refused** — there is no later pass |
| a refusal costs | ~$0.002 | ~$0.002, and stops the annotation spend |

The asymmetry is the point. A candidate kept by mistake is corrected downstream;
one dropped by mistake is gone. At delivery nothing downstream re-examines a
clip, so "not established" and "wrong" have the same consequence and are treated
the same way: **confirmed egocentric, or it does not ship.**

The two are not asking about the same object either. The candidate is a whole
video; the deliverable is a span cut out of it. A source that is egocentric for
four of its twelve minutes passes the first check and can still yield a clip
that is entirely a presenter talking to camera — which is exactly what happened
on `RDT-01198 Installing Smoke Detectors`: 18 of 20 candidates were screened out
before download, the survivor graded C with the hands gate passed, and all three
clips cut from it were presenter footage.

The verdict is recorded on the clip, so a later pass does not pay to look again.
`--no-require-egocentric` turns the gate off, for somebody deliberately building
an exocentric set.

### Step 5 — write the directory

```bash
python -m video_searching_agent.pipeline.dataset --out ~/egoexo-dataset
```

Reads state the earlier steps already paid to produce; calls no model and
indexes nothing. Media already on disk is skipped unless `--refresh-media`, so
re-exporting after a fresh annotation pass costs a few metadata reads and
nothing else. `--no-media` writes the JSON only.

**The egocentric requirement is enforced here too**, because a directory and a
manifest are read by different people. Only clips whose frames were confirmed
first-person are written, and a clip that an *earlier* export wrote and this one
withholds has its files removed — a manifest saying 10 beside a directory
holding 15 mp4s hands the footage over anyway to anyone who opens the folder.
Nothing else in the directory is touched: only ids this pass considered and
refused. `--include-non-egocentric` ships everything.

> **Two things are called "export" in this repo, and they are not the same.**
> `curation/export.py::export_anchors` exports *anchors*: it asks the Datalake
> to cut a span out of a whole source video on demand and returns a signed URL,
> at $0.005 a clip, leaving the corpus a set of movable time anchors
> (`G2-TREE-5`). `pipeline/dataset.py::export_dataset` — this step — writes the
> **clean collection**, whose clips `refine` already cut into files of their
> own, into a directory; there is nothing left to cut and nothing further to
> bill. Reach for the first when you want seconds out of a source video, and
> this one when you want the deliverable on disk.

---

## 3. When the store and the collection disagree

Step four reconciles against the annotation store before it annotates, and a
clip with **no row in the store is skipped entirely** — reported as
`— no clip row in the store`, with the pass ending `annotated 0 clip(s)`.

That is correct behaviour and an easy thing to misread as a broken pipeline. The
row is written by `record_refined` at cut time; a clip that exists in the
Datalake with no row is a clip whose store was lost, moved, or never shared —
the store is a local file and is not in git.

To recover, seed the rows from what the Datalake still knows, then run step four
normally:

```python
from video_searching_agent.store.annotations import Clip, open_store

# for each video in the clean collection:
store.put(Clip(
    video_id=record["video_id"],
    collection_id=COLLECTION,
    source_video_id=custom.get("source_video_id", ""),
    source_start=custom.get("source_start"),
    source_end=custom.get("source_end"),
    title=metadata.get("title", ""),
    duration_seconds=record.get("duration_seconds"),
))
```

The Datalake is authoritative about whether a clip exists; the store is
authoritative about nothing. Reconstructing rows from it is always safe.

---

## 4. Reading the same dataset in the UI

`3 · Library` is the directory's other face: the same clips, read from the store
and the Datalake rather than from disk, and it answers the question a delivered
clip has to answer — *which video, which seconds, and what is in it.*

Each row carries a still and, under the title, the **whole** source video id and
the span it was cut between — not an abbreviation. Opening one shows a
provenance block that is selectable, so the id can be pasted straight into the
Datalake:

```
CLIP        vid_2sizjtvpsj6b7otz4zigdk5li
CUT FROM    vid_6lybavinuafdqdogzokcpvx2rm
AT          180.0s – 205.0s
COLLECTION  col_pelhcnsu2avutdnyamgnshohxu
```

…then the footage, then the tree in the clip's own time base with each span's
label, narration, hands and objects.

**Stills are rendered, not bought.** The Datalake can return a frame and charges
for it — before the lookup, and not refunded on a miss — so a library page of
two dozen clips would bill two dozen times on every scroll. `GET
/api/v1/clips/{id}/thumbnail` cuts one locally with ffmpeg from the same signed
URL the player uses and caches it (`THUMBNAIL_CACHE_PATH`, else beside the
store): about 3.5s the first time and 7ms after. The export writes the same
frame from the local file, so the directory and the UI show the same picture.

**The library opens on egocentric**, matching the deliverable, and says in words
how many clips are being held out and what the frames called them. The other
viewpoints are one dropdown away — a refused clip is how you check the gate was
right.

## 5. Reading the numbers honestly

**`clips_without_tree` is not noise.** "Cut but not yet annotated" is a real
state and the export shows it rather than filtering it. A high number means run
step four — not that the export is wrong. The Library UI shows these clips too,
for the same reason.

**A clip can be cut and still be junk.** The grade a clip inherits was earned by
its *source* video: a clip cut from an A-graded video can be a title card. Step
four re-grades once the clip's own annotation depth is known, and clips move
both ways — several went D → B on this collection once they had a tree, and one
screen recording of a Unity editor session was refused outright by `G1-HAND`,
which is the junk in the collection being caught rather than labelled.

**Do not read the A/B share as a quality measure.** The bands (85/70/55) were
calibrated for the older four-dimension scale, so a clip can fail a media check
and still score 87. The scorecard's **valid clips** figure — hands in frame, the
manipulation legible, and a tree whose atomic actions name what each hand did
and to what — is the measure that means what it says.

---

## 6. Known gaps in the current output

Recorded here rather than in a commit message, because they change what the
directory is worth:

* **A clip can be first-person and still be a demo.** The gate settles the
  camera, not the content: a wearable-camera video of somebody *presenting* a
  product passes it. `valid clips` — the atomic actions naming what each hand
  did and to what — is still the measure that catches those.
* **Trees are shallow.** Most clips come out `task → action` with the action's
  span identical to the task's. A 115-second assembly summarised as one action
  is an L2 by shape and an L1 in substance.
* **Roughly a fifth of anchored spans return no annotation**, reported as
  `the looking path was off and no anchor carried caption text`. Visible now
  rather than fixed.
* **`source_url` is empty on clips cut by refine.** The Datalake's own signed
  URL is fetched at export time and deliberately not recorded — it expires in a
  day — but the *origin* URL, the page the source video came from, is not
  written back either. `G0-PROV` fails on this, and it is the field a customer
  asks for first.
* **Media and tree can drift.** Nothing stamps the export with the annotation
  pass that produced it, so a directory exported before a re-annotation and one
  exported after are indistinguishable from their contents.
