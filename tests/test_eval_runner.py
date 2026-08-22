"""Reading the pipeline's own payloads into the eval's record.

This is the seam where a metric goes silently wrong. Every number in a
scorecard is read out of a `clip_done` or `complete` payload by key, so a
renamed field does not raise — it reads as zero, and a zero looks like a
measurement. These cases pin the mapping against payloads shaped like the real
ones.
"""

from __future__ import annotations

from video_searching_agent.evaluation.runner import DERIVED_READS_PER_CLIP, clip_outcome

# Shaped after a real `complete` payload from /api/v1/curate/stream.
CURATED = {
    "video_id": "vid_anwuyaqa2sd36zlxnivub36lum",
    "accepted": True,
    "grade": "B",
    "score": 74,
    "annotation_level": "L2",
    "duration_seconds": 417,
    "usable_seconds": 400,
    "idle_seconds": 17,
    "blocking_failures": [],
    "cleaning": {
        "segments": [
            {"hier_level": "task", "span_start": 0, "span_end": 417},
            {"hier_level": "action", "span_start": 0, "span_end": 60},
            {"hier_level": "action", "span_start": 60, "span_end": 120},
        ]
    },
    "annotation": {
        "annotations": [{"label": "load machine"}, {"label": "fold shirt"}],
        "spans_considered": 6,
        "look_cost_usd": 0.031,
    },
}


def test_a_curated_clip_is_read_into_the_record() -> None:
    clip = clip_outcome("q1", CURATED)

    assert clip.video_id == "vid_anwuyaqa2sd36zlxnivub36lum"
    assert (clip.grade, clip.score, clip.accepted) == ("B", 74, True)
    assert clip.annotation_level == "L2"
    assert (clip.duration_seconds, clip.usable_seconds, clip.idle_seconds) == (417, 400, 17)


def test_only_action_level_anchors_count_as_anchors() -> None:
    """The task-level anchor is the whole video, not a labelled span."""
    clip = clip_outcome("q1", CURATED)
    assert clip.action_anchors == 2
    assert clip.total_anchors == 3
    assert clip.annotations == 2


def test_the_billable_units_come_from_what_the_pipeline_reported() -> None:
    clip = clip_outcome("q1", CURATED)

    assert clip.indexed_minutes == 417 / 60
    # One moment search per video, then one read per span it shortlisted.
    assert clip.moment_search_calls == 1
    assert clip.moment_read_calls == 6
    assert clip.derived_reads == DERIVED_READS_PER_CLIP
    assert clip.look_usd == 0.031
    assert clip.direct_usd > 0


def test_a_clip_that_never_got_annotated_is_not_billed_for_annotation() -> None:
    clip = clip_outcome("q1", {**CURATED, "annotation": None})
    assert clip.moment_search_calls == 0
    assert clip.moment_read_calls == 0
    assert clip.annotations == 0
    assert clip.look_usd == 0.0


def test_a_payload_missing_everything_optional_still_reads() -> None:
    """A clip that died early streams almost nothing; it must not raise."""
    clip = clip_outcome("q1", {"video_id": "vid_x"})
    assert clip.grade == "D"
    assert clip.accepted is False
    assert clip.annotation_level == "L0"
    assert (clip.duration_seconds, clip.action_anchors, clip.total_anchors) == (0, 0, 0)


def test_a_blocking_failure_is_carried_through_because_it_vetoes_the_clip() -> None:
    clip = clip_outcome("q1", {**CURATED, "blocking_failures": ["G1-HAND"]})
    assert clip.blocking_failures == ["G1-HAND"]
