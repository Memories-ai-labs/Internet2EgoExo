"""Tests for training-data curation: viewpoint, scoring, manifest and cost."""

import pytest

from video_searching_agent.curation.cost import (
    DEFAULT_FRAME_CHECK_YIELD,
    estimate_collection_cost,
)
from video_searching_agent.curation.manifest import curate_references
from video_searching_agent.curation.scoring import (
    LicenseFilter,
    is_reusable_license,
    score_candidate,
)
from video_searching_agent.curation.viewpoint import (
    Viewpoint,
    ViewpointVerdict,
    classify_viewpoint,
)
from video_searching_agent.models.query import MetricType, ParsedQuery
from video_searching_agent.models.result import VideoReference


class TestViewpointClassification:
    """Camera viewpoint from the text a candidate carries."""

    @pytest.mark.parametrize(
        "title",
        [
            "Egocentric recording of a kitchen shift",
            "Head-mounted camera: full bike build",
            "Ego4D style first-person view of assembly",
            "Body-worn camera walkthrough of the warehouse",
            "第一人称视角 做饭全程",
        ],
    )
    def test_strong_egocentric_cues(self, title):
        verdict = classify_viewpoint(title=title)
        assert verdict.viewpoint == Viewpoint.EGOCENTRIC
        assert verdict.confidence >= 0.7
        assert verdict.evidence

    @pytest.mark.parametrize(
        "title",
        [
            "Exocentric multi-view capture of the same task",
            "Fixed camera observing the operator",
            "CCTV footage of the loading bay",
            "固定机位 记录装配过程",
        ],
    )
    def test_strong_exocentric_cues(self, title):
        verdict = classify_viewpoint(title=title)
        assert verdict.viewpoint == Viewpoint.EXOCENTRIC
        assert verdict.confidence >= 0.7

    def test_pov_meme_pattern_is_held_at_low_confidence(self):
        """"POV: <scenario>" is a caption device, not a camera rig."""
        verdict = classify_viewpoint(title="POV: you woke up as the last person on earth")
        assert verdict.confidence <= 0.2
        assert any("penalty" in cue for cue in verdict.evidence)

    def test_pov_with_a_capture_cue_is_corroborated(self):
        verdict = classify_viewpoint(title="GoPro POV assembling a bike in the workshop")
        assert verdict.viewpoint == Viewpoint.EGOCENTRIC
        assert verdict.confidence > 0.4

    def test_no_cues_is_unknown_not_a_guess(self):
        verdict = classify_viewpoint(title="Cat compilation 2026")
        assert verdict.viewpoint == Viewpoint.UNKNOWN
        assert verdict.confidence == 0.0
        assert verdict.evidence == []

    def test_empty_text_is_unknown(self):
        assert classify_viewpoint().viewpoint == Viewpoint.UNKNOWN

    def test_contradictory_cues_stay_unknown_when_balanced(self):
        verdict = classify_viewpoint(title="First person view and third person view side by side")
        assert verdict.viewpoint == Viewpoint.UNKNOWN
        assert any("conflict" in cue for cue in verdict.evidence)

    def test_captions_are_used_as_evidence(self):
        """Indexed captions describe the frame, so they carry the verdict."""
        verdict = classify_viewpoint(
            title="Untitled clip",
            captions="egocentric view, the wearer's hands enter frame holding a wrench",
        )
        assert verdict.viewpoint == Viewpoint.EGOCENTRIC

    def test_matches_treats_unknown_as_acceptable(self):
        unknown = ViewpointVerdict(Viewpoint.UNKNOWN, 0.0)
        assert unknown.matches(Viewpoint.EGOCENTRIC) is True
        assert unknown.matches(None) is True
        ego = ViewpointVerdict(Viewpoint.EGOCENTRIC, 0.9)
        assert ego.matches(Viewpoint.EXOCENTRIC) is False


class TestUsabilityScoring:
    """Hard requirements exclude; everything else only ranks."""

    def test_wrong_viewpoint_is_excluded_with_a_reason(self):
        verdict = ViewpointVerdict(Viewpoint.EXOCENTRIC, 0.8)
        score = score_candidate(verdict, 1800, wanted_viewpoint=Viewpoint.EGOCENTRIC)
        assert not score.usable
        assert "exocentric" in score.excluded_reason

    def test_short_clip_is_excluded(self):
        verdict = ViewpointVerdict(Viewpoint.EGOCENTRIC, 0.9)
        score = score_candidate(verdict, 20, min_duration_seconds=300)
        assert not score.usable
        assert "20s" in score.excluded_reason

    def test_unknown_duration_fails_a_minimum(self):
        verdict = ViewpointVerdict(Viewpoint.EGOCENTRIC, 0.9)
        score = score_candidate(verdict, None, min_duration_seconds=300)
        assert not score.usable
        assert "unknown" in score.excluded_reason

    def test_non_reusable_licence_excluded_when_required(self):
        verdict = ViewpointVerdict(Viewpoint.EGOCENTRIC, 0.9)
        score = score_candidate(
            verdict, 900, "youtube", license_filter=LicenseFilter.REUSABLE
        )
        assert not score.usable
        assert "youtube" in score.excluded_reason

    def test_unknown_viewpoint_is_kept_but_ranked_lower(self):
        matched = score_candidate(
            ViewpointVerdict(Viewpoint.EGOCENTRIC, 0.9), 900,
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
        )
        unknown = score_candidate(
            ViewpointVerdict(Viewpoint.UNKNOWN, 0.0), 900,
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
        )
        assert matched.usable and unknown.usable
        assert matched.total > unknown.total

    def test_popularity_plays_no_part_but_length_and_licence_do(self):
        verdict = ViewpointVerdict(Viewpoint.EGOCENTRIC, 0.9)
        short_clip = score_candidate(verdict, 60, "youtube")
        long_clip = score_candidate(verdict, 3600, "youtube")
        licensed = score_candidate(verdict, 3600, "creativeCommon")
        assert long_clip.total > short_clip.total
        assert licensed.total > long_clip.total

    def test_duration_credit_saturates(self):
        verdict = ViewpointVerdict(Viewpoint.EGOCENTRIC, 1.0)
        at_full = score_candidate(verdict, 600)
        beyond = score_candidate(verdict, 6000)
        assert at_full.duration_score == beyond.duration_score == 1.0

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("creativeCommon", True),
            ("CC-BY", True),
            ("cc0", True),
            ("youtube", False),
            ("", False),
            (None, False),
        ],
    )
    def test_reusable_licence_detection(self, value, expected):
        assert is_reusable_license(value) is expected


class TestManifestCuration:
    """The run's deliverable: kept clips, totals, exclusions and cost."""

    @staticmethod
    def _reference(title, seconds, license_value=None, url=None):
        return VideoReference(
            video_id=title[:6],
            url=url or f"https://example.com/{abs(hash(title)) % 10_000}",
            platform="youtube",
            title=title,
            duration_seconds=seconds,
            license=license_value,
        )

    def test_annotates_ranks_and_excludes(self):
        references = [
            self._reference("POV head-mounted kitchen prep", 1800, "creativeCommon"),
            self._reference("Fixed camera view of the same task", 1500),
            self._reference("POV: you are late for work", 12),
            self._reference("GoPro first-person bike repair", 2400),
        ]
        parsed = ParsedQuery(
            original_query="egocentric kitchen and repair footage",
            viewpoint=Viewpoint.EGOCENTRIC,
            min_duration_seconds=300,
            target_hours=2.0,
        )

        kept, manifest = curate_references(references, parsed, query=parsed.original_query)

        assert [reference.viewpoint for reference in kept] == [
            Viewpoint.EGOCENTRIC,
            Viewpoint.EGOCENTRIC,
        ]
        # Ranked by usability, not by length or order of discovery.
        assert kept[0].usability_score >= kept[1].usability_score
        assert all(reference.viewpoint_evidence for reference in kept)

        assert manifest.total_clips == 2
        assert manifest.total_hours == pytest.approx((1800 + 2400) / 3600, abs=0.01)
        assert manifest.excluded_clips == 2
        assert manifest.by_viewpoint == {"egocentric": 2}
        assert manifest.reusable_license_clips == 1
        assert manifest.target_met is False

    def test_exclusion_reasons_are_reported(self):
        references = [
            self._reference("Fixed camera assembly", 1200),
            self._reference("Tripod shot of the bench", 900),
        ]
        parsed = ParsedQuery(original_query="ego only", viewpoint=Viewpoint.EGOCENTRIC)

        kept, manifest = curate_references(references, parsed)

        assert kept == []
        assert manifest.total_clips == 0
        assert sum(manifest.exclusion_reasons.values()) == 2
        assert any("wanted egocentric" in reason for reason in manifest.exclusion_reasons)

    def test_longest_metric_reorders(self):
        references = [
            self._reference("First person view short take", 400),
            self._reference("First person view long take", 4000),
        ]
        parsed = ParsedQuery(
            original_query="ego footage",
            viewpoint=Viewpoint.EGOCENTRIC,
            metric=MetricType.LONGEST,
        )

        kept, _ = curate_references(references, parsed)
        assert kept[0].duration_seconds == 4000

    def test_target_met_when_hours_reached(self):
        references = [self._reference("Head-mounted long shift", 8000)]
        parsed = ParsedQuery(
            original_query="two hours",
            viewpoint=Viewpoint.EGOCENTRIC,
            target_hours=2.0,
        )
        _, manifest = curate_references(references, parsed)
        assert manifest.target_met is True

    def test_no_requirements_keeps_everything(self):
        references = [
            self._reference("Fixed camera assembly", 1200),
            self._reference("Head-mounted kitchen", 900),
            self._reference("Unlabelled clip", 60),
        ]
        kept, manifest = curate_references(references, None)
        assert len(kept) == 3
        assert manifest.excluded_clips == 0

    def test_cost_rides_on_the_manifest(self):
        references = [self._reference("Head-mounted shift", 3600, "creativeCommon")]
        parsed = ParsedQuery(original_query="one hour", viewpoint=Viewpoint.EGOCENTRIC)

        _, manifest = curate_references(references, parsed, discovery_usd=0.05)

        assert manifest.cost is not None
        # One hour of footage indexes at $0.05/video-minute.
        assert manifest.cost.indexing_usd == pytest.approx(3.0, abs=0.01)
        assert manifest.cost.usd_per_collected_hour == pytest.approx(3.05, abs=0.02)


class TestCostModel:
    """Cost per hour, from published rates and measured spend."""

    def test_indexing_dominates_and_scales_linearly(self):
        one = estimate_collection_cost(1.0)
        ten = estimate_collection_cost(10.0)
        assert one.indexing_usd == pytest.approx(3.0, abs=0.01)
        assert ten.indexing_usd == pytest.approx(30.0, abs=0.01)
        assert one.usd_per_collected_hour == pytest.approx(ten.usd_per_collected_hour, abs=0.01)

    def test_delivered_hour_applies_the_frame_check_yield(self):
        cost = estimate_collection_cost(2.0)
        assert cost.assumed_yield == DEFAULT_FRAME_CHECK_YIELD
        assert cost.usd_per_delivered_hour == pytest.approx(
            cost.usd_per_collected_hour / DEFAULT_FRAME_CHECK_YIELD, abs=0.01
        )

    def test_annotation_priced_per_moment_plus_tokens(self):
        without = estimate_collection_cost(1.0)
        with_pass = estimate_collection_cost(
            1.0, annotated_moments=100, annotation_tokens_usd=0.20
        )
        # 100 moments × ($0.008 search + $0.008 moment) + $0.20 tokens
        assert with_pass.annotation_usd == pytest.approx(1.8, abs=0.01)
        assert with_pass.total_usd > without.total_usd

    def test_unmeasured_terms_are_flagged_not_invented(self):
        cost = estimate_collection_cost(1.0)
        assert cost.download_usd == 0.0
        assert any("Download" in note for note in cost.notes)
        assert any("annotation" in note.lower() for note in cost.notes)

    def test_download_rate_is_honoured_when_supplied(self):
        cost = estimate_collection_cost(4.0, download_usd_per_hour=0.25)
        assert cost.download_usd == pytest.approx(1.0, abs=0.001)
        assert not any("Download billed at $0" in note for note in cost.notes)

    def test_zero_hours_does_not_divide_by_zero(self):
        cost = estimate_collection_cost(0.0, discovery_usd=0.02)
        assert cost.usd_per_collected_hour == 0.0
        assert cost.usd_per_delivered_hour == 0.0

    def test_higher_fps_costs_more_to_index(self):
        base = estimate_collection_cost(1.0)
        dense = estimate_collection_cost(1.0, index_fps=2.0)
        assert dense.indexing_usd == pytest.approx(base.indexing_usd * 2, abs=0.01)
