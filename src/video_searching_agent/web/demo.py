"""Canned payloads for demo mode.

The deployed link has to be clickable by someone with no keys and no budget, so
`DEMO_MODE=1` makes the three streaming endpoints serve these instead of calling
Gemini, the platforms or the Datalake. Nothing is downloaded, indexed or spent.

They are also what the browser QA runs against (`ui/qa/`), which is why the
awkward cases are here on purpose and not just the happy path:

* a clip that is **rejected for having no hands**, with its reason;
* a gate that is **unmeasured** (`G3-DUP`) rather than passed;
* an action whose captions **never say which hand**, so the field stays null;
* an idle share that is **flagged but not blocking**.

Shapes match the real ones exactly — these are the same dicts the pipeline and
the agents produce — so the UI cannot pass here and fail in production.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

# Demo streams are paced so the UI's live states are actually visible; a stream
# that arrives all at once would never show a stage in progress.
STEP_DELAY_SECONDS = 0.15


def _clip(
    url: str,
    title: str,
    viewpoint: str = "egocentric",
    annotations: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """One candidate clip, shaped like a real VideoReference."""
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
        "span_start": 0.0,
        "span_end": 540.0,
        "ref": None,
        "segment_id": "t1",
        "parent_segment_id": None,
        "hier_level": "task",
        "narration": "A mirepoix is prepped and softened in a pan.",
        "label": "prep-mirepoix",
        "left_hand": None,
        "right_hand": None,
        "objects": [],
        "tags": ["task_family/cooking"],
        "source": "agent",
        "confidence": 0.8,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
    {
        "span_start": 12.0,
        "span_end": 180.0,
        "ref": None,
        "segment_id": "t1.a1",
        "parent_segment_id": "t1",
        "hier_level": "action",
        "narration": "The knife works through an onion held against the board.",
        "label": "chop-vegetables",
        "left_hand": "holds the onion steady",
        "right_hand": "moves the knife through it",
        "objects": ["onion", "knife", "cutting board"],
        "tags": ["hoi/chop-vegetables/right/move-knife", "hands_visible"],
        "source": "agent",
        "confidence": 0.72,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
    {
        "span_start": 96.0,
        "span_end": 101.0,
        "ref": None,
        "segment_id": "t1.a1.e1",
        "parent_segment_id": "t1.a1",
        "hier_level": "event",
        "narration": "The left hand shifts back from the blade.",
        "label": "reposition-grip",
        "left_hand": None,
        "right_hand": None,
        "objects": [],
        "tags": [],
        "source": "agent",
        "confidence": None,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
    {
        "span_start": 220.0,
        "span_end": 540.0,
        "ref": None,
        "segment_id": "t1.a2",
        "parent_segment_id": "t1",
        "hier_level": "action",
        "narration": "The pan is stirred while the vegetables soften.",
        "label": "saute-vegetables",
        "left_hand": None,
        "right_hand": None,
        "objects": ["pan", "wooden spoon"],
        "tags": ["hoi/saute-vegetables/right/stir-pan", "hands_visible"],
        "source": "agent",
        "confidence": 0.64,
        "caveat": "read from caption wording, not a hand-tracking or pose model",
    },
]

CAVEAT = "read from caption wording, not a hand-tracking or pose model"

CHECKS = [
    {
        "id": "G0-LIC",
        "name": "Licence permits commercial training use",
        "passed": True,
        "measured": True,
        "blocking": False,
        "value": "creativeCommon",
        "threshold": "explicit commercial-use permission",
        "detail": None,
    },
    {
        "id": "G1-HAND",
        "name": "Wearer's own hands in frame",
        "passed": True,
        "measured": True,
        "blocking": True,
        "value": 0.78,
        "threshold": ">=60% of caption segments",
        "detail": None,
    },
    {
        "id": "G1-RES",
        "name": "Resolution",
        "passed": True,
        "measured": True,
        "blocking": False,
        "value": "1080p",
        "threshold": ">=1080p for grade A, >=720p to pass",
        "detail": "A (>=1080p)",
    },
    {
        "id": "G1-OTHERFACE",
        "name": "No one else's face in frame",
        "passed": True,
        "measured": True,
        "blocking": True,
        "value": "none seen",
        "threshold": "no other person in frame",
        "detail": None,
    },
    {
        "id": "G1-IDLE",
        "name": "Idle share",
        "passed": False,
        "measured": True,
        "blocking": False,
        "value": 0.18,
        "threshold": "<=15%, and marked",
        "detail": None,
    },
    {
        "id": "G3-DUP",
        "name": "Overlap with public corpora",
        "passed": False,
        "measured": False,
        "blocking": False,
        "value": None,
        "threshold": "<=10%, cosine >=0.95 counts as duplicate",
        "detail": "needs OmniRetriever embeddings against the Egocentric-10K base",
    },
]


async def frames(
    events: list[tuple[str, dict[str, Any]]],
) -> AsyncGenerator[dict[str, str], None]:
    """Turn a list of (event, payload) pairs into a paced SSE stream."""
    for name, payload in events:
        await asyncio.sleep(STEP_DELAY_SECONDS)
        yield {"event": name, "data": json.dumps(payload)}


def query_events(body: Any) -> list[tuple[str, dict[str, Any]]]:
    """A search run: activity, then the manifest and the candidates."""
    query = getattr(body, "query", "") or ""
    target = getattr(body, "target_hours", None) or 2.0

    clips = [
        _clip(
            "https://www.youtube.com/watch?v=aaa1",
            "POV: prepping a mirepoix (GoPro)",
            annotations=TREE,
            quality_grade="B",
            quality_score=75,
            annotation_level="L3",
            usable_seconds=740,
            idle_seconds=160,
            commercial_use_ok=True,
            task_family="cooking",
        ),
        _clip("https://www.youtube.com/watch?v=bbb2", "First person: knife skills drill"),
        _clip(
            "https://www.youtube.com/watch?v=ccc3",
            "Kitchen tour, fixed camera",
            viewpoint="exocentric",
            license=None,
        ),
    ]
    manifest = {
        "query": query,
        "requested_viewpoint": "egocentric",
        "target_hours": float(target),
        "total_clips": 3,
        "total_hours": 0.75,
        "clips_with_known_duration": 3,
        "hours": {
            "worn_hours": 0.0,
            "delivered_hours": 0.75,
            "accepted_hours": 0.42,
            "accepted_labeled_hours": 0.21,
            "idle_hours": 0.04,
            "media_yield": 0.56,
        },
        "accepted_clips": 2,
        "grades": {"B": 1, "C": 1, "D": 1},
        "annotation_levels": {"L3": 1, "L1": 2},
        "dataset_checks": CHECKS[-1:],
        "by_viewpoint": {"egocentric": 2, "exocentric": 1},
        "by_platform": {"youtube": 3},
        "reusable_license_clips": 2,
        "excluded_clips": 4,
        "exclusion_reasons": {"wrong viewpoint": 3, "too short": 1},
        "cost": {
            "hours": 0.75,
            "total_usd": 2.31,
            "discovery_usd": 0.06,
            "download_usd": 0.0,
            "indexing_usd": 2.25,
            "annotation_usd": 0.0,
            "usd_per_collected_hour": 3.08,
            "usd_per_delivered_hour": 7.0,
            "assumed_yield": 0.44,
            "notes": [
                "demo data — nothing was searched, indexed or spent",
                "download cost not measured; reported as zero",
            ],
        },
        "clips": clips,
    }
    response = {
        "session_id": "demo-session",
        "query": query,
        "answer": (
            "Demo data. Three candidates: two read as first-person with capture cues, "
            "the third is a fixed-camera kitchen tour and is excluded from the totals. "
            "Set GOOGLE_API_KEY, YOUTUBE_API_KEY and MEMORIES_API_KEY, and turn DEMO_MODE "
            "off, to run this for real."
        ),
        "video_references": clips,
        "dataset": manifest,
        "platforms_searched": ["youtube"],
        "total_videos_analyzed": 7,
        "steps_taken": 4,
        "tools_used": ["video_search", "youtube_search"],
        "execution_time_seconds": 6.4,
        "usage_metrics": {"total_cost_usd": 0.0},
        "needs_clarification": False,
        "clarification_question": None,
    }

    return [
        ("started", {"session_id": "demo-session", "query": query}),
        ("progress", {"step": 1, "max_steps": 8, "message": "Parsing the collection request"}),
        ("tool_call", {"tool": "video_search", "input": {}}),
        ("tool_result", {"tool": "video_search", "success": True, "videos_found": 7}),
        ("tool_result", {"tool": "youtube_search", "success": False, "error": "quota exceeded"}),
        ("complete", response),
    ]


def collect_events(body: Any) -> list[tuple[str, dict[str, Any]]]:
    """A collection run: every stage of an accepted clip, then a rejected one."""
    urls: list[str] = list(getattr(body, "urls", []) or [])
    first = urls[0] if urls else "https://www.youtube.com/watch?v=aaa1"
    second = urls[1] if len(urls) > 1 else None
    total = 2 if second else 1

    base: dict[str, Any] = {
        "url": first,
        "stage": "probing",
        "accepted": False,
        "video_id": None,
        "duration_seconds": 900,
        "size_mb": None,
        "title": "POV: prepping a mirepoix (GoPro)",
        "tags_written": [],
        "rejection_reason": None,
        "error": None,
        "notes": ["demo data — nothing was downloaded or indexed"],
        "annotation_level": None,
        "screening": {
            "accepted": True,
            "reasons": [],
            "viewpoint": "egocentric",
            "commercial_use_ok": True,
            "notes": [],
            "sight": {
                "viewpoint": "egocentric",
                "hands_visible": True,
                "confidence": 0.95,
                "why": "the wearer's own hands come into frame from the bottom",
                "method": "frames",
                "frames_seen": 4,
                "cost_usd": 0.0021,
                "error": None,
            },
            "checks": CHECKS[:1],
        },
    }

    stages: list[tuple[str, dict[str, Any]]] = [
        ("probing", {}),
        (
            "looking",
            {
                "screening": {
                    "accepted": True,
                    "reasons": [],
                    "viewpoint": "egocentric",
                    "commercial_use_ok": True,
                    "notes": [],
                    "sight": {
                        "viewpoint": "egocentric",
                        "hands_visible": True,
                        "confidence": 0.95,
                        "why": "the wearer's own hands come into frame from the bottom",
                        "method": "frames",
                        "frames_seen": 4,
                        "cost_usd": 0.0021,
                        "error": None,
                    },
                    "checks": CHECKS[:1],
                }
            },
        ),
        ("downloading", {}),
        ("uploading", {"size_mb": 148.2}),
        ("indexing", {"video_id": "vid_1"}),
        ("cleaning", {}),
        (
            "annotating",
            {
                "quality": {
                    "score": 75,
                    "grade": "B",
                    "accepted": True,
                    "commercial_use_ok": True,
                    "annotation_level": "L3",
                    "usable_seconds": 740,
                    "idle_seconds": 160,
                    "blocking_failures": [],
                    "unmeasured": ["G3-DUP"],
                    "notes": ["Gate 3 (diversity/dedup) is scored per dataset, not per clip"],
                    "checks": CHECKS,
                },
                "frame_check": {
                    "hands_visible": True,
                    "hands_confidence": 0.95,
                    "hand_evidence": ["hand:left hand", "manipulation:chops"],
                    "viewpoint": "egocentric",
                    "is_footage": True,
                },
                "segments": [
                    {
                        "segment_id": "t1",
                        "parent_segment_id": None,
                        "hier_level": "task",
                        "span_start": 12.0,
                        "span_end": 540.0,
                        "duration": 528.0,
                        "label": None,
                        "hands_visible": True,
                        "evidence": ["2 action anchors"],
                    },
                    {
                        "segment_id": "t1.a1",
                        "parent_segment_id": "t1",
                        "hier_level": "action",
                        "span_start": 12.0,
                        "span_end": 180.0,
                        "duration": 168.0,
                        "label": None,
                        "hands_visible": True,
                        "evidence": ["hand:left hand"],
                    },
                ],
                "tags_written": ["clean_pass", "hands_visible", "first_person_view"],
            },
        ),
        (
            "accepted",
            {
                "accepted": True,
                "annotation_level": "L3",
                "tags_written": [
                    "clean_pass",
                    "hands_visible",
                    "first_person_view",
                    "hoi/chop-vegetables/right/move-knife",
                ],
                "annotation": {
                    "annotations": TREE,
                    "annotation_level": "L3",
                    "survival_rate": 0.5,
                    "spans_considered": 4,
                    "spans_rejected": 2,
                    "task_family": "cooking",
                    "trace": [],
                    "errors": [],
                    "caveat": CAVEAT,
                },
            },
        ),
    ]

    events: list[tuple[str, dict[str, Any]]] = []
    for stage, extra in stages:
        base = {**base, **extra, "stage": stage}
        events.append(("clip_stage", {"index": 1, "total": total, "clip": dict(base)}))

    accepted = dict(base)
    events.append(("clip_done", {"index": 1, "total": total, "clip": accepted}))

    rejected: dict[str, Any] | None = None
    if second:
        # The whole point of the run: a clip with no hands in it is dropped.
        rejected = {
            **base,
            "url": second,
            "title": "Kitchen tour, fixed camera",
            "stage": "rejected",
            "accepted": False,
            "video_id": "vid_2",
            "rejection_reason": "no hands visible in the captions",
            "annotation": None,
            "annotation_level": None,
            "tags_written": ["clean_rejected", "no_hands"],
            # Its own record, not the accepted clip's: no grade, because a clip
            # that fails a blocking gate never gets one.
            "quality": None,
            "segments": [],
            "frame_check": {
                "hands_visible": False,
                "hands_confidence": 0.0,
                "hand_evidence": [],
                "viewpoint": "unknown",
                "is_footage": True,
            },
        }
        events.append(("clip_stage", {"index": 2, "total": total, "clip": rejected}))
        events.append(("clip_done", {"index": 2, "total": total, "clip": rejected}))

    events.append(
        (
            "complete",
            {
                "accepted": [accepted],
                "rejected": [rejected] if rejected else [],
                "accepted_count": 1,
                "rejected_count": 1 if rejected else 0,
                "video_ids": ["vid_1"],
            },
        )
    )
    return events


def curate_events(body: Any) -> list[tuple[str, dict[str, Any]]]:
    """A curation pass: one verdict, then the ledger and the batch grade."""
    curated = {
        "video_id": "vid_1",
        "accepted": True,
        "rejection_reason": None,
        "grade": "B",
        "score": 75,
        "annotation_level": "L3",
        "duration_seconds": 900,
        "usable_seconds": 740,
        "idle_seconds": 160,
        "labeled": True,
        "commercial_use_ok": True,
        "uploader": "Cooking POV",
        "task_family": "cooking",
        "error_sample": False,
        "dup_group_id": None,
        "blocking_failures": [],
        "cleaning": None,
        "annotation": None,
    }
    report = {
        "query": getattr(body, "query", None) or "",
        "clips": [curated],
        "hours": {
            "worn_hours": 0.0,
            "delivered_hours": 0.25,
            "accepted_hours": 0.21,
            "accepted_labeled_hours": 0.21,
            "idle_hours": 0.04,
            "media_yield": 0.84,
        },
        "accepted_clips": 1,
        "total_clips": 2,
        "batch_grade": "B",
        "grades": {"B": 1, "D": 1},
        "annotation_levels": {"L3": 1, "L0": 1},
        "duplicate_groups": 1,
        "dataset_checks": CHECKS[-3:],
        "trace": [],
        "errors": ["demo data — no videos were read or graded"],
    }
    return [
        (
            "started",
            {
                "tag": getattr(body, "tag", None),
                "video_ids": getattr(body, "video_ids", None) or [],
            },
        ),
        ("clip_done", {"clip": curated}),
        ("complete", report),
    ]


# --- the library ----------------------------------------------------------
#
# Demo mode has to populate this too, or browser QA cannot reach the view at all
# and the one screen that shows the *result* of the whole pipeline goes
# unexercised. The shape is exactly what the store returns, including the awkward
# real case: a clip that was cut and cleaned before anything labelled it, whose
# spans are real and whose labels are null.

LIBRARY_CLIPS: list[dict[str, Any]] = [
    {
        "video_id": "vid_demoegocook01",
        "collection_id": "col_demo_clean",
        "source_video_id": "vid_demosource001",
        "source_start": 122.0,
        "source_end": 158.0,
        "source_url": "https://www.youtube.com/watch?v=demo-cook",
        "title": "POV breakfast service — eggs and toasties",
        "duration_seconds": 36.0,
        "viewpoint": "egocentric",
        "grade": "B",
        "annotation_level": "L2",
        "accepted": True,
        "motion_mean": 0.118,
        "sharpness_mean": 1240.0,
        "query": "kitchen tasks — chopping, stirring, washing up",
        "created_at": "2026-08-22T09:04:02Z",
        "segments": [
            {
                "segment_id": "t1",
                "parent_segment_id": None,
                "hier_level": "task",
                "span_start": 0.0,
                "span_end": 36.0,
                "seconds": 36.0,
                "label": "prepare-breakfast-plate",
                "narration": "plating a cooked breakfast to order",
                "hands_visible": True,
                "left_hand": None,
                "right_hand": None,
                "evidence": ["3 action anchors"],
            },
            {
                "segment_id": "t1.a1",
                "parent_segment_id": "t1",
                "hier_level": "action",
                "span_start": 0.0,
                "span_end": 14.0,
                "seconds": 14.0,
                "label": "crack-eggs-into-bowl",
                "narration": "the left hand steadies the bowl while the right cracks two eggs",
                "hands_visible": True,
                "left_hand": "steadies the metal bowl",
                "right_hand": "cracks the eggs against the rim",
                "evidence": ["frames"],
            },
            {
                "segment_id": "t1.a2",
                "parent_segment_id": "t1",
                "hier_level": "action",
                "span_start": 14.0,
                "span_end": 36.0,
                "seconds": 22.0,
                "label": "plate-sausage-and-toast",
                "narration": "tongs lift sausages onto the plate, then toast beside them",
                "hands_visible": True,
                "left_hand": "holds the plate level",
                "right_hand": "works the tongs",
                "evidence": ["frames", "captions"],
            },
        ],
    },
    {
        "video_id": "vid_demounlabelled2",
        "collection_id": "col_demo_clean",
        "source_video_id": "vid_demosource002",
        "source_start": 77.1,
        "source_end": 97.1,
        "source_url": "",
        "title": "HOW TO MOUNT THE IKEA SUNNERSTRA RAIL SYSTEM",
        "duration_seconds": 20.0,
        "viewpoint": "unknown",
        "grade": "",
        "annotation_level": "",
        # Cut and cleaned, never annotated. A real state, and the one that used
        # to render as a row of blanks.
        "accepted": False,
        "motion_mean": 0.042,
        "sharpness_mean": 33.6,
        "query": "mounting a wall rail",
        "created_at": "2026-08-22T08:58:11Z",
        "segments": [
            {
                "segment_id": "t1",
                "parent_segment_id": None,
                "hier_level": "task",
                "span_start": 0.0,
                "span_end": 20.0,
                "seconds": 20.0,
                "label": None,
                "narration": None,
                "hands_visible": True,
                "left_hand": None,
                "right_hand": None,
                "evidence": ["1 action anchors"],
            },
            {
                "segment_id": "t1.a1",
                "parent_segment_id": "t1",
                "hier_level": "action",
                "span_start": 0.0,
                "span_end": 20.0,
                "seconds": 20.0,
                "label": None,
                "narration": None,
                "hands_visible": True,
                "left_hand": None,
                "right_hand": None,
                "evidence": ["hand:hand", "manipulation:holds"],
            },
        ],
    },
]


def library_page(
    q: str = "",
    viewpoint: str = "",
    hands_only: bool = False,
    accepted_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """The demo library, filtered the way the store filters it.

    The filtering is real rather than ignored, because a search box that returns
    the same rows whatever is typed is exactly the bug browser QA exists to
    catch.
    """
    rows = LIBRARY_CLIPS
    if viewpoint:
        rows = [c for c in rows if (c["viewpoint"] or "unknown") == viewpoint]
    if accepted_only:
        rows = [c for c in rows if c["accepted"]]
    if hands_only:
        rows = [c for c in rows if any(s.get("hands_visible") for s in c["segments"])]
    if q:
        needle = q.lower()
        rows = [
            c
            for c in rows
            if needle in (c["title"] or "").lower()
            or any(
                needle in (str(s.get("label") or "") + str(s.get("narration") or "")).lower()
                for s in c["segments"]
            )
        ]
    page = rows[offset : offset + max(1, limit)]
    return {
        "clips": [
            {k: v for k, v in clip.items() if k != "segments"}
            | {
                "segment_count": len(clip["segments"]),
                "action_count": sum(1 for s in clip["segments"] if s["hier_level"] == "action"),
            }
            for clip in page
        ],
        "total": len(rows),
        "limit": limit,
        "offset": offset,
        "store": {"path": "demo", "persists": True},
    }


def library_facets() -> dict[str, Any]:
    labels: dict[str, dict[str, Any]] = {}
    for clip in LIBRARY_CLIPS:
        for segment in clip["segments"]:
            if segment["hier_level"] != "action" or not segment["label"]:
                continue
            row = labels.setdefault(
                segment["label"], {"label": segment["label"], "segments": 0, "clips": 0}
            )
            row["segments"] += 1
            row["clips"] += 1
    seconds = sum(c["duration_seconds"] for c in LIBRARY_CLIPS)
    by_viewpoint: dict[str, int] = {}
    for clip in LIBRARY_CLIPS:
        key = clip["viewpoint"] or "unknown"
        by_viewpoint[key] = by_viewpoint.get(key, 0) + 1
    return {
        "totals": {
            "clips": len(LIBRARY_CLIPS),
            "accepted_clips": sum(1 for c in LIBRARY_CLIPS if c["accepted"]),
            "hours": round(seconds / 3600, 4),
            "action_segments": sum(
                1 for c in LIBRARY_CLIPS for s in c["segments"] if s["hier_level"] == "action"
            ),
            "by_viewpoint": by_viewpoint,
        },
        "action_labels": sorted(labels.values(), key=lambda r: -r["segments"]),
        "task_labels": [],
    }


def library_clip(video_id: str) -> dict[str, Any] | None:
    for clip in LIBRARY_CLIPS:
        if clip["video_id"] == video_id:
            return dict(clip) | {
                "segment_count": len(clip["segments"]),
                "action_count": sum(1 for s in clip["segments"] if s["hier_level"] == "action"),
                "playback": {
                    "url": None,
                    "status": "ready",
                    "tags": ["hand", "bowl", "eggs", "hob", "plate"],
                    "error": "demo mode serves no footage",
                },
            }
    return None
