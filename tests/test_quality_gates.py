"""Tests for the first-person data quality gates."""

import pytest

from video_searching_agent.curation.quality_gates import (
    AnnotationLevel,
    Grade,
    build_hours_ledger,
    evaluate_clip,
    evaluate_dataset,
    grade_annotation_level,
    hand_frame_ratio,
    mentions_idle,
    permits_commercial_use,
    structural_checks,
)


def _tree(**overrides):
    """A minimal well-formed task → action → event tree."""
    task = {
        "segment_id": "t1",
        "parent_segment_id": None,
        "hier_level": "task",
        "span_start": 0.0,
        "span_end": 60.0,
        "label": "replace-inner-tube",
        "narration": "A punctured tube is swapped for a new one.",
    }
    action = {
        "segment_id": "t1.a1",
        "parent_segment_id": "t1",
        "hier_level": "action",
        "span_start": 0.0,
        "span_end": 30.0,
        "label": "lever-tyre-off",
        "narration": "Two levers walk the tyre bead off the rim.",
        "objects": ["tyre lever", "rim"],
        "left_hand": "holds the wheel",
    }
    event = {
        "segment_id": "t1.a1.e1",
        "parent_segment_id": "t1.a1",
        "hier_level": "event",
        "span_start": 12.0,
        "span_end": 14.0,
        "label": "lever-slips",
        "narration": "The second lever slips out of the bead.",
    }
    tree = [task, action, event]
    for entry in tree:
        entry.update(overrides.get(entry["segment_id"], {}))
    return tree


class TestGateZero:
    """Rights. A veto, and one that has to be a data field."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Creative Commons", True),
            ("creative_commons", True),
            ("CC-BY", True),
            ("cc0", True),
            ("Standard YouTube License", False),
            ("", False),
            (None, False),
        ],
    )
    def test_commercial_use_detection(self, value, expected):
        assert permits_commercial_use(value) is expected

    def test_unknown_licence_blocks_only_when_the_caller_says_so(self):
        strict = evaluate_clip(license_value=None, require_commercial_use=True)
        assert "G0-LIC" in strict.blocking_failures
        assert strict.accepted is False

        carried = evaluate_clip(license_value=None, require_commercial_use=False)
        assert "G0-LIC" not in carried.blocking_failures

    def test_no_provenance_supplied_is_unmeasured_not_a_failure(self):
        report = evaluate_clip()
        assert "G0-PROV" in report.unmeasured

    def test_partial_provenance_is_a_real_failure(self):
        report = evaluate_clip(source_url="https://example.com/v")
        check = report.check("G0-PROV")
        assert check.measured is True and check.passed is False
        assert "uploader" in check.detail


class TestGateOne:
    """Media usability, run over everything."""

    def test_portrait_footage_fails_orientation(self):
        report = evaluate_clip(width=1080, height=1920)
        assert report.check("G1-ORIENT").passed is False

    def test_low_resolution_fails(self):
        assert evaluate_clip(height=480).check("G1-RES").passed is False
        assert evaluate_clip(height=720).check("G1-RES").passed is True

    def test_frame_rate_floor(self):
        assert evaluate_clip(fps=24).check("G1-FPS").passed is False
        assert evaluate_clip(fps=30).check("G1-FPS").passed is True

    def test_hand_ratio_is_measured_in_segments_and_blocks(self):
        segments = [
            {"text": "the left hand grips the rim"},
            {"text": "the wheel spins"},
            {"text": "fingers seat the bead"},
        ]
        assert hand_frame_ratio(segments) == pytest.approx(0.667, abs=0.001)
        report = evaluate_clip(caption="a", caption_segments=segments)
        assert report.check("G1-HAND").passed is True

        thin = [{"text": "hands"}] + [{"text": "the bench is empty"}] * 4
        blocked = evaluate_clip(caption="a", caption_segments=thin)
        assert blocked.check("G1-HAND").passed is False
        assert "G1-HAND" in blocked.blocking_failures

    def test_no_segments_falls_back_to_the_whole_caption(self):
        report = evaluate_clip(caption="A gloved hand turns the valve.")
        check = report.check("G1-HAND")
        assert check.passed is True
        assert "fallback" in check.detail

    def test_nothing_to_read_leaves_the_hand_check_unmeasured(self):
        assert "G1-HAND" in evaluate_clip().unmeasured

    def test_other_people_and_their_hands_block(self):
        report = evaluate_clip(
            caption="Another person faces the camera while their hands reach in."
        )
        assert {"G1-OTHERHAND", "G1-OTHERFACE"} <= set(report.blocking_failures)

    def test_loose_gloves_and_edits_are_flagged_without_blocking(self):
        report = evaluate_clip(
            caption="A bulky welding glove holds the torch. Quick cuts between shots.",
            caption_segments=[{"text": "a bulky welding glove holds the torch"}],
        )
        assert report.check("G1-GLOVE").passed is False
        assert report.check("G1-WHOLE").passed is False
        assert "G1-GLOVE" not in report.blocking_failures

    def test_idle_time_is_subtracted_not_averaged_in(self):
        segments = [
            {"text": "the hands sand the joint"},
            {"text": "nothing happens, the bench is empty"},
        ]
        report = evaluate_clip(
            caption="hands sand the joint", caption_segments=segments, duration_seconds=100
        )
        assert report.idle_seconds == 50
        assert report.usable_seconds == 50
        assert report.check("G1-IDLE").passed is False

    def test_idle_cue_helper(self):
        assert mentions_idle("nothing happens here")
        assert mentions_idle("the hands work") == []
        assert mentions_idle(None) == []


class TestGateTwo:
    """Annotation depth, and the tree rules that make depth real."""

    def test_no_annotations_is_l0_or_l1(self):
        assert grade_annotation_level(None) is AnnotationLevel.L0
        assert grade_annotation_level(None, caption="a caption") is AnnotationLevel.L1

    def test_a_flat_list_of_actions_is_only_l1(self):
        flat = [entry for entry in _tree() if entry["hier_level"] == "action"]
        assert grade_annotation_level(flat) is AnnotationLevel.L1

    def test_task_plus_anchored_actions_is_l2(self):
        without_events = [e for e in _tree() if e["hier_level"] != "event"]
        for entry in without_events:
            entry.pop("objects", None)
            entry.pop("left_hand", None)
        assert grade_annotation_level(without_events) is AnnotationLevel.L2

    def test_events_with_objects_and_hands_reach_l3(self):
        assert grade_annotation_level(_tree()) is AnnotationLevel.L3

    def test_unanchored_actions_cannot_reach_l2(self):
        unanchored = _tree(**{"t1.a1": {"span_start": None, "span_end": None}})
        assert grade_annotation_level(unanchored) is AnnotationLevel.L1

    def test_a_child_outside_its_parent_fails_the_tree(self):
        broken = _tree(**{"t1.a1.e1": {"span_start": 40.0, "span_end": 50.0}})
        check = next(c for c in structural_checks(broken) if c.check_id == "G2-TREE-1")
        assert check.passed is False

    def test_overlapping_siblings_fail(self):
        tree = _tree()
        tree.append(
            {
                "segment_id": "t1.a2",
                "parent_segment_id": "t1",
                "hier_level": "action",
                "span_start": 20.0,
                "span_end": 45.0,
                "label": "refit-tyre",
                "narration": "The bead is worked back over the rim.",
            }
        )
        check = next(c for c in structural_checks(tree) if c.check_id == "G2-TREE-2")
        assert check.passed is False

    def test_text_copied_down_a_level_fails(self):
        copied = _tree(
            **{
                "t1.a1": {
                    "label": "replace-inner-tube",
                    "narration": "A punctured tube is swapped for a new one.",
                }
            }
        )
        check = next(c for c in structural_checks(copied) if c.check_id == "G2-TREE-3")
        assert check.passed is False

    def test_delivering_cut_files_fails(self):
        cut = _tree(**{"t1.a1": {"clip_file": "a1.mp4"}})
        check = next(c for c in structural_checks(cut) if c.check_id == "G2-TREE-5")
        assert check.passed is False


class TestScorecard:
    """45 annotation / 25 diversity / 20 media / 10 licensing."""

    def test_a_full_record_grades_b_or_better(self):
        report = evaluate_clip(
            license_value="Creative Commons",
            source_url="https://example.com/v",
            uploader="rider",
            width=1920,
            height=1080,
            fps=60,
            duration_seconds=60,
            container="mp4",
            caption="The left hand holds the wheel while fingers seat the bead.",
            caption_segments=[{"text": "the left hand holds the wheel", "start": 0, "end": 60}],
            annotations=_tree(),
        )
        assert report.annotation_level is AnnotationLevel.L3
        assert report.score >= 70
        assert report.grade in (Grade.A, Grade.B)
        assert report.accepted is True

    def test_a_clip_alone_never_reads_as_an_a_on_diversity(self):
        report = evaluate_clip(
            license_value="cc0",
            source_url="https://example.com/v",
            uploader="rider",
            height=1080,
            fps=60,
            caption="Both hands work the bead.",
            annotations=_tree(),
        )
        assert any("Gate 3" in note for note in report.notes)
        assert report.score < 100

    def test_unmeasured_checks_are_excluded_rather_than_assumed(self):
        report = evaluate_clip(annotations=_tree())
        assert "G1-RES" in report.unmeasured
        assert report.check("G1-RES").passed is False  # not credited either way
        assert report.score < 60

    def test_a_blocking_failure_is_never_accepted(self):
        report = evaluate_clip(
            license_value="cc0",
            source_url="https://example.com/v",
            uploader="rider",
            height=1080,
            fps=60,
            caption="Another person faces the camera.",
            annotations=_tree(),
        )
        assert report.accepted is False


class TestHoursLedger:
    """The four measures, kept apart."""

    def test_the_measures_do_not_collapse_into_each_other(self):
        ledger = build_hours_ledger(
            delivered_seconds=3600,
            accepted_seconds=2400,
            idle_seconds=600,
            labeled_seconds=1800,
        )
        assert ledger.delivered_hours == 1.0
        assert ledger.accepted_hours == pytest.approx(0.667, abs=0.001)
        assert ledger.accepted_labeled_hours == 0.5
        assert ledger.as_dict()["media_yield"] == pytest.approx(0.667, abs=0.001)

    def test_nothing_delivered_is_a_zero_yield_not_a_crash(self):
        assert build_hours_ledger(0, 0).as_dict()["media_yield"] == 0.0


class TestGateThree:
    """Diversity, across the set."""

    def _clips(self, n, uploader="one", families=("cooking",)):
        return [
            {
                "uploader": f"{uploader}{index % len(families)}",
                "task_family": families[index % len(families)],
                "error_sample": False,
            }
            for index in range(n)
        ]

    def test_one_creator_is_not_diversity(self):
        checks = evaluate_dataset(self._clips(5))
        assert next(c for c in checks if c.check_id == "G3-OP").passed is False

    def test_ten_task_families_pass_coverage(self):
        families = tuple(f"family-{index}" for index in range(10))
        checks = evaluate_dataset(self._clips(20, uploader="op", families=families))
        assert next(c for c in checks if c.check_id == "G3-SOP").passed is True

    def test_error_samples_are_wanted_at_a_rate(self):
        clips = self._clips(10)
        for clip in clips[:2]:
            clip["error_sample"] = True
        checks = evaluate_dataset(clips)
        assert next(c for c in checks if c.check_id == "G3-ERR").passed is True

    def test_public_corpus_overlap_is_reported_unmeasured(self):
        checks = evaluate_dataset(self._clips(3))
        dup = next(c for c in checks if c.check_id == "G3-DUP")
        assert dup.measured is False and dup.detail

    def test_an_empty_set_has_nothing_to_check(self):
        assert evaluate_dataset([]) == []
