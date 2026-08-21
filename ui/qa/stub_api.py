"""A stub API that serves the built UI, for browser QA that spends nothing.

Every response here is canned: no Datalake calls, no downloads, no model calls.
It exists so the UI can be driven through the whole flow — search, select,
collect, gate, grade — against payloads shaped exactly like the real ones,
including the awkward cases (a rejected clip, an unmeasured gate, a caption that
never states which hand).

    uv run python ui/qa/stub_api.py 8821
    node ui/qa/flow.mjs ui/qa/shots
"""

import asyncio
import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

# The committed build output, as FastAPI serves it.
STATIC = Path(__file__).resolve().parents[2] / "src" / "video_searching_agent" / "web" / "static"

app = FastAPI()


def clip(url, title, viewpoint="egocentric", annotations=None, **extra):
    payload = {
        "video_id": url[-4:],
        "url": url,
        "title": title,
        "platform": "youtube",
        "creator": "Cooking POV",
        "thumbnail_url": None,
        "relevance_note": "Head-mounted, continuous take, both hands in frame.",
        "duration_seconds": 900,
        "duration": "15:00",
        "viewpoint": viewpoint,
        "viewpoint_confidence": 0.82,
        "viewpoint_evidence": ["ego:first person view", "capture:gopro"],
        "license": "creativeCommon",
        "usability_score": 0.71,
        "datalake_video_id": "vid_1",
        "annotations": annotations or [],
    }
    payload.update(extra)
    return payload


TREE = [
    {
        "span_start": 0.0, "span_end": 540.0, "ref": None, "segment_id": "t1",
        "parent_segment_id": None, "hier_level": "task",
        "narration": "A mirepoix is prepped and softened in a pan.",
        "label": "prep-mirepoix", "left_hand": None, "right_hand": None,
        "objects": [], "tags": ["task_family/cooking"], "source": "agent",
        "confidence": 0.8, "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
    {
        "span_start": 12.0, "span_end": 180.0, "ref": None, "segment_id": "t1.a1",
        "parent_segment_id": "t1", "hier_level": "action",
        "narration": "The knife works through an onion held against the board.",
        "label": "chop-vegetables", "left_hand": "holds the onion steady",
        "right_hand": "moves the knife through it",
        "objects": ["onion", "knife", "cutting board"],
        "tags": ["hoi/chop-vegetables/right/move-knife", "hands_visible"],
        "source": "agent", "confidence": 0.72,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
    {
        "span_start": 96.0, "span_end": 101.0, "ref": None, "segment_id": "t1.a1.e1",
        "parent_segment_id": "t1.a1", "hier_level": "event",
        "narration": "The left hand shifts back from the blade.",
        "label": "reposition-grip", "left_hand": None, "right_hand": None,
        "objects": [], "tags": [], "source": "agent", "confidence": None,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
    {
        "span_start": 220.0, "span_end": 540.0, "ref": None, "segment_id": "t1.a2",
        "parent_segment_id": "t1", "hier_level": "action",
        "narration": "The pan is stirred while the vegetables soften.",
        "label": "saute-vegetables", "left_hand": None, "right_hand": None,
        "objects": ["pan", "wooden spoon"],
        "tags": ["hoi/saute-vegetables/right/stir-pan", "hands_visible"],
        "source": "agent", "confidence": 0.64,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
]

CHECKS = [
    {"id": "G0-LIC", "name": "Licence permits commercial training use", "passed": True,
     "measured": True, "blocking": False, "value": "creativeCommon",
     "threshold": "explicit commercial-use permission", "detail": None},
    {"id": "G1-HAND", "name": "Wearer's own hands in frame", "passed": True, "measured": True,
     "blocking": True, "value": 0.78, "threshold": ">=60% of caption segments", "detail": None},
    {"id": "G1-RES", "name": "Resolution", "passed": True, "measured": True, "blocking": False,
     "value": "1080p", "threshold": ">=1080p for grade A, >=720p to pass", "detail": "A (>=1080p)"},
    {"id": "G1-OTHERFACE", "name": "No one else's face in frame", "passed": True, "measured": True,
     "blocking": True, "value": "none seen", "threshold": "no other person in frame", "detail": None},
    {"id": "G1-IDLE", "name": "Idle share", "passed": False, "measured": True, "blocking": False,
     "value": 0.18, "threshold": "<=15%, and marked", "detail": None},
    {"id": "G3-DUP", "name": "Overlap with public corpora", "passed": False, "measured": False,
     "blocking": False, "value": None, "threshold": "<=10%, cosine >=0.95 counts as duplicate",
     "detail": "needs OmniRetriever embeddings against the Egocentric-10K base"},
]


async def frames(events):
    for name, payload, delay in events:
        await asyncio.sleep(delay)
        yield {"event": name, "data": json.dumps(payload)}


@app.post("/api/v1/queries/stream")
async def queries(body: dict):
    manifest_clips = [
        clip("https://www.youtube.com/watch?v=aaa1", "POV: prepping a mirepoix (GoPro)", annotations=TREE,
             quality_grade="B", quality_score=75, annotation_level="L3", usable_seconds=740,
             idle_seconds=160, commercial_use_ok=True, task_family="cooking"),
        clip("https://www.youtube.com/watch?v=bbb2", "First person: knife skills drill"),
        clip("https://www.youtube.com/watch?v=ccc3", "Kitchen tour, fixed camera", viewpoint="exocentric",
             license=None),
    ]
    manifest = {
        "query": body.get("query", ""),
        "requested_viewpoint": "egocentric",
        "target_hours": float(body.get("target_hours") or 2),
        "total_clips": 3,
        "total_hours": 0.75,
        "clips_with_known_duration": 3,
        "hours": {"worn_hours": 0.0, "delivered_hours": 0.75, "accepted_hours": 0.42,
                  "accepted_labeled_hours": 0.21, "idle_hours": 0.04, "media_yield": 0.56},
        "accepted_clips": 2,
        "grades": {"B": 1, "C": 1, "D": 1},
        "annotation_levels": {"L3": 1, "L1": 2},
        "dataset_checks": CHECKS[-1:],
        "by_viewpoint": {"egocentric": 2, "exocentric": 1},
        "by_platform": {"youtube": 3},
        "reusable_license_clips": 2,
        "excluded_clips": 4,
        "exclusion_reasons": {"wrong viewpoint": 3, "too short": 1},
        "cost": {"hours": 0.75, "total_usd": 2.31, "discovery_usd": 0.06, "download_usd": 0.0,
                 "indexing_usd": 2.25, "annotation_usd": 0.0,
                 "usd_per_collected_hour": 3.08, "usd_per_delivered_hour": 7.0,
                 "assumed_yield": 0.44,
                 "notes": ["download cost not measured; reported as zero"]},
        "clips": manifest_clips,
    }
    response = {
        "session_id": "sess-abcdef123456", "query": body.get("query", ""),
        "answer": "Three candidates match. Two read as first-person with capture cues; the third is "
                  "a fixed-camera kitchen tour and is excluded from the manifest totals.",
        "video_references": manifest_clips,
        "dataset": manifest,
        "platforms_searched": ["youtube"], "total_videos_analyzed": 7, "steps_taken": 4,
        "tools_used": ["video_search", "youtube_search"], "execution_time_seconds": 6.4,
        "usage_metrics": {"total_cost_usd": 0.06},
        "needs_clarification": False, "clarification_question": None,
    }
    return EventSourceResponse(frames([
        ("started", {"session_id": "sess-abcdef123456", "query": body.get("query", "")}, 0.05),
        ("progress", {"step": 1, "max_steps": 8, "message": "Parsing the collection request"}, 0.15),
        ("tool_call", {"tool": "video_search", "input": {}}, 0.15),
        ("tool_result", {"tool": "video_search", "success": True, "videos_found": 7}, 0.2),
        ("tool_result", {"tool": "youtube_search", "success": False, "error": "quota exceeded"}, 0.1),
        ("complete", response, 0.2),
    ]))


@app.post("/api/v1/collect/stream")
async def collect(body: dict):
    url = body["urls"][0]
    base = {
        "url": url, "stage": "probing", "accepted": False, "video_id": None,
        "duration_seconds": 900, "size_mb": None, "title": "POV: prepping a mirepoix (GoPro)",
        "tags_written": [], "rejection_reason": None, "error": None, "notes": [],
        "annotation_level": None,
        "screening": {"accepted": True, "reasons": [], "viewpoint": "egocentric",
                      "commercial_use_ok": True, "checks": CHECKS[:1]},
    }
    stages = []
    for stage, extra, delay in [
        ("probing", {}, 0.1),
        ("downloading", {}, 0.2),
        ("uploading", {"size_mb": 148.2}, 0.2),
        ("indexing", {"video_id": "vid_1"}, 0.25),
        ("cleaning", {}, 0.2),
        ("annotating", {
            "quality": {"score": 75, "grade": "B", "accepted": True, "commercial_use_ok": True,
                        "annotation_level": "L3", "usable_seconds": 740, "idle_seconds": 160,
                        "blocking_failures": [], "unmeasured": ["G3-DUP"],
                        "notes": ["Gate 3 (diversity/dedup) is scored per dataset, not per clip"],
                        "checks": CHECKS},
            "frame_check": {"hands_visible": True, "hands_confidence": 0.95,
                            "hand_evidence": ["hand:left hand", "manipulation:chops"],
                            "viewpoint": "egocentric", "is_footage": True},
            "segments": [
                {"segment_id": "t1", "parent_segment_id": None, "hier_level": "task",
                 "span_start": 12.0, "span_end": 540.0, "duration": 528.0, "label": None,
                 "hands_visible": True, "evidence": ["2 action anchors"]},
                {"segment_id": "t1.a1", "parent_segment_id": "t1", "hier_level": "action",
                 "span_start": 12.0, "span_end": 180.0, "duration": 168.0, "label": None,
                 "hands_visible": True, "evidence": ["hand:left hand"]},
            ],
            "tags_written": ["clean_pass", "hands_visible", "first_person_view"],
        }, 0.3),
        ("accepted", {
            "accepted": True, "annotation_level": "L3",
            "tags_written": ["clean_pass", "hands_visible", "first_person_view",
                             "hoi/chop-vegetables/right/move-knife"],
            "annotation": {"annotations": TREE, "annotation_level": "L3", "survival_rate": 0.5,
                           "spans_considered": 4, "spans_rejected": 2, "task_family": "cooking",
                           "trace": [], "errors": [],
                           "caveat": "read from caption wording, not a hand-tracking or pose model"},
        }, 0.2),
    ]:
        base = {**base, **extra, "stage": stage}
        stages.append(("clip_stage", {"index": 1, "total": 1, "clip": dict(base)}, delay))

    final = dict(base)
    rejected = {**base, "url": body["urls"][-1] if len(body["urls"]) > 1 else url + "&x=2",
                "stage": "rejected", "accepted": False,
                "rejection_reason": "no hands visible in the captions",
                "annotation": None, "annotation_level": None,
                "frame_check": {"hands_visible": False, "hands_confidence": 0.0,
                                "hand_evidence": [], "viewpoint": "unknown", "is_footage": True}}
    return EventSourceResponse(frames(stages + [
        ("clip_done", {"index": 1, "total": 2, "clip": final}, 0.1),
        ("clip_stage", {"index": 2, "total": 2, "clip": rejected}, 0.15),
        ("clip_done", {"index": 2, "total": 2, "clip": rejected}, 0.1),
        ("complete", {"accepted": [final], "rejected": [rejected], "accepted_count": 1,
                      "rejected_count": 1, "video_ids": ["vid_1"]}, 0.1),
    ]))


@app.post("/api/v1/curate/stream")
async def curate(body: dict):
    curated = {
        "video_id": "vid_1", "accepted": True, "rejection_reason": None, "grade": "B",
        "score": 75, "annotation_level": "L3", "duration_seconds": 900, "usable_seconds": 740,
        "idle_seconds": 160, "labeled": True, "commercial_use_ok": True, "uploader": "Cooking POV",
        "task_family": "cooking", "error_sample": False, "dup_group_id": None,
        "blocking_failures": [], "cleaning": None, "annotation": None,
    }
    report = {
        "query": body.get("query") or "", "clips": [curated],
        "hours": {"worn_hours": 0.0, "delivered_hours": 0.25, "accepted_hours": 0.21,
                  "accepted_labeled_hours": 0.21, "idle_hours": 0.04, "media_yield": 0.84},
        "accepted_clips": 1, "total_clips": 2, "batch_grade": "B",
        "grades": {"B": 1, "D": 1}, "annotation_levels": {"L3": 1, "L0": 1},
        "duplicate_groups": 1, "dataset_checks": CHECKS[-3:], "trace": [],
        "errors": ["caption unavailable for vid_9: not ready"],
    }
    return EventSourceResponse(frames([
        ("started", {"tag": body.get("tag"), "video_ids": body.get("video_ids") or []}, 0.05),
        ("clip_done", {"clip": curated}, 0.2),
        ("complete", report, 0.2),
    ]))


app.mount("/ui", StaticFiles(directory=STATIC, html=True), name="ui")


@app.get("/")
async def root():
    return RedirectResponse("/ui/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8821)
