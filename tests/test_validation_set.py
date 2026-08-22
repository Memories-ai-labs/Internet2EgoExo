"""Score the validation set against the judgement layer.

These are not unit tests of functions; they are the labelled cases in
`tests/validation/gold.py` — four real Datalake recordings and seven cases
distilled from defects that shipped — run through the same code the product
runs, and checked against the verdict a careful human would give.

A failure here means one of two things, and both are worth stopping for: the
change is wrong, or the label was.
"""

from __future__ import annotations

import pytest

from tests.validation.gold import ALL_CASES, GoldCase
from video_searching_agent.agent.cleaning_agent import CleaningAgent
from video_searching_agent.curation.frame_check import check_frames
from video_searching_agent.curation.quality_gates import evaluate_clip, hand_frame_ratio


def _judge(case: GoldCase):
    """Run one case through the frame check, the gates and the clipping."""
    frame = check_frames(caption=case.caption, title=case.title)
    quality = evaluate_clip(
        caption=case.caption,
        caption_segments=case.caption_segments,
        duration_seconds=case.duration_seconds,
        require_commercial_use=False,
        **{
            key: value
            for key, value in case.media.items()
            if key in ("source_url", "uploader", "license", "width", "height", "fps", "container")
        },
    )
    anchors = CleaningAgent().propose_segments(
        case.caption_segments, total_duration=case.duration_seconds
    )
    actions = [a for a in anchors if a.hier_level == "action"]
    rejection = frame.rejection(require_hands=True)
    if rejection is None and quality.blocking_failures:
        rejection = "blocking gate failure: " + ", ".join(quality.blocking_failures)
    return frame, quality, actions, rejection


CASES = [pytest.param(case, id=case.name) for case in ALL_CASES]


@pytest.mark.parametrize("case", CASES)
def test_hands(case: GoldCase):
    if case.hands_visible is None:
        pytest.skip("no hand expectation for this case")
    frame, *_ = _judge(case)
    assert frame.hands_visible is case.hands_visible, case.why


@pytest.mark.parametrize("case", CASES)
def test_viewpoint(case: GoldCase):
    if case.viewpoint is None:
        pytest.skip("no viewpoint expectation for this case")
    frame, *_ = _judge(case)
    assert frame.viewpoint.value == case.viewpoint, case.why


@pytest.mark.parametrize("case", CASES)
def test_is_footage(case: GoldCase):
    if case.is_footage is None:
        pytest.skip("no footage expectation for this case")
    frame, *_ = _judge(case)
    assert frame.is_footage is case.is_footage, case.why


@pytest.mark.parametrize("case", CASES)
def test_acceptance(case: GoldCase):
    if case.accepted is None:
        pytest.skip("no acceptance expectation for this case")
    _, _, _, rejection = _judge(case)
    if case.accepted:
        assert rejection is None, f"{case.why} — but it was rejected: {rejection}"
    else:
        assert rejection is not None, f"{case.why} — but it was accepted"


@pytest.mark.parametrize("case", CASES)
def test_blocking_gates(case: GoldCase):
    if case.blocking_gates is None:
        pytest.skip("no gate expectation for this case")
    _, quality, _, _ = _judge(case)
    if case.blocking_gates:
        for gate in case.blocking_gates:
            assert gate in quality.blocking_failures, f"{case.why} — {gate} did not block"
    else:
        assert quality.blocking_failures == [], case.why


@pytest.mark.parametrize("case", CASES)
def test_anchor_count(case: GoldCase):
    if case.min_anchors is None and case.max_anchors is None:
        pytest.skip("no anchor expectation for this case")
    _, _, actions, _ = _judge(case)
    if case.min_anchors is not None:
        assert len(actions) >= case.min_anchors, f"{case.why} — got {len(actions)} anchors"
    if case.max_anchors is not None:
        assert len(actions) <= case.max_anchors, f"{case.why} — got {len(actions)} anchors"


@pytest.mark.parametrize("case", CASES)
def test_anchor_length(case: GoldCase):
    if case.max_anchor_seconds is None:
        pytest.skip("no anchor length expectation for this case")
    _, _, actions, _ = _judge(case)
    longest = max((a.duration for a in actions), default=0.0)
    assert longest <= case.max_anchor_seconds, (
        f"{case.why} — longest anchor is {longest:.0f}s"
    )


@pytest.mark.parametrize("case", CASES)
def test_anchors_stay_inside_the_video(case: GoldCase):
    _, _, actions, _ = _judge(case)
    for action in actions:
        assert action.span_start >= 0
        if case.duration_seconds:
            assert action.span_end <= case.duration_seconds + 0.001, (
                f"{case.name}: anchor ends at {action.span_end} past "
                f"{case.duration_seconds}s"
            )


@pytest.mark.parametrize("case", CASES)
def test_anchors_do_not_overlap(case: GoldCase):
    """Sibling overlap is G2-TREE-2, and it used to happen by a hair."""
    _, _, actions, _ = _judge(case)
    for earlier, later in zip(actions, actions[1:], strict=False):
        assert later.span_start >= earlier.span_end - 0.001, (
            f"{case.name}: {earlier.segment_id} and {later.segment_id} overlap"
        )


@pytest.mark.parametrize("case", CASES)
def test_hand_ratio(case: GoldCase):
    if case.hand_ratio_at_least is None:
        pytest.skip("no hand ratio expectation for this case")
    ratio = hand_frame_ratio(case.caption_segments)
    assert ratio is not None, f"{case.name}: no ratio could be measured"
    assert ratio >= case.hand_ratio_at_least, f"{case.why} — ratio {ratio}"


@pytest.mark.parametrize("case", CASES)
def test_idle_detection(case: GoldCase):
    if case.idle_detected is None:
        pytest.skip("no idle expectation for this case")
    _, quality, _, _ = _judge(case)
    if case.idle_detected:
        assert quality.idle_seconds > 0, f"{case.why} — no idle time found"
    else:
        assert quality.idle_seconds == 0, case.why


def test_the_set_covers_the_shipped_defects():
    """A regression case that quietly disappears is a regression test lost."""
    regressions = {case.name for case in ALL_CASES if case.regression}
    assert {
        "wrist_camera",
        "ego_harness",
        "medical_tubing",
        "rotating_pot",
        "chop_then_stir",
        "first_segment_at_zero",
        "colleague_in_one_span",
    } <= regressions


def test_every_case_says_why_it_is_here():
    """A case without a stated reason cannot be judged when it fails."""
    for case in ALL_CASES:
        assert case.why.strip().endswith("."), f"{case.name}: {case.why!r}"
        assert len(case.why) > 30, f"{case.name}: reason too thin"
