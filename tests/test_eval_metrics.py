"""The arithmetic the scorecard is quoted from.

A yield number and a cost-per-clip number are the two things somebody will
repeat in a meeting without the run in front of them, so the two properties
that make them trustworthy are pinned here: the cost attribution adds up, and
nothing that was not measured is quietly counted as zero.
"""

from __future__ import annotations

import pytest

from video_searching_agent.curation.cost import (
    DERIVED_READ_PER_CALL,
    INDEX_PER_VIDEO_MINUTE,
    MOMENT_PER_CALL,
    SEARCH_PER_CALL,
)
from video_searching_agent.evaluation.metrics import (
    UNMEASURED_TERMS,
    ClipOutcome,
    QueryOutcome,
    contradictions,
    outcome_as_dict,
    outcome_from_dict,
    score_run,
)
from video_searching_agent.evaluation.scorecard import render


def _clip(video_id: str, grade: str, **overrides) -> ClipOutcome:
    base = {
        "query_id": "q",
        "video_id": video_id,
        "grade": grade,
        "score": {"A": 90, "B": 75, "C": 60, "D": 40}[grade],
        "accepted": grade != "D",
        "annotation_level": "L2",
        "duration_seconds": 600,
        "usable_seconds": 540,
        "idle_seconds": 60,
        "action_anchors": 6,
        "total_anchors": 7,
        "annotations": 7,
        "indexed_minutes": 10.0,
        "moment_search_calls": 1,
        "moment_read_calls": 6,
        "derived_reads": 3,
    }
    return ClipOutcome(**{**base, **overrides})


def _run() -> list[QueryOutcome]:
    return [
        QueryOutcome(
            query_id="q1",
            query="someone folding cloth",
            task_family="Laundry & Clothing Care",
            difficulty="medium",
            candidates=9,
            attempted=2,
            indexed=2,
            discovery_usd=0.04,
            clips=[_clip("v1", "A"), _clip("v2", "D")],
        ),
        QueryOutcome(
            query_id="q2",
            query="someone assembling the chair",
            task_family="Assembly & Fastening",
            difficulty="hard",
            candidates=3,
            attempted=1,
            indexed=1,
            discovery_usd=0.03,
            clips=[_clip("v3", "C")],
        ),
        QueryOutcome(
            query_id="q3",
            query="someone glassblowing",
            task_family="Other",
            difficulty="hard",
            candidates=0,
            attempted=0,
            indexed=0,
            discovery_usd=0.02,
            error="search returned no candidates",
        ),
    ]


def test_the_funnel_counts_every_step() -> None:
    chain = score_run(_run()).chain

    assert chain.queries == 3
    assert chain.queries_with_candidates == 2
    assert chain.queries_with_an_accepted_clip == 2
    assert chain.queries_errored == 1
    assert (chain.candidates, chain.attempted, chain.indexed, chain.graded) == (12, 3, 3, 3)
    assert chain.accepted == 2  # the D is not accepted
    assert chain.high_quality == 1  # only the A; a C is not high-quality hours
    assert chain.action_anchors == 18
    # Only the accepted clips' anchors count toward the per-clip yield.
    assert chain.accepted_action_anchors == 12
    assert chain.anchors_per_accepted_clip == pytest.approx(6.0)
    assert chain.acceptance_rate == pytest.approx(2 / 3)
    assert chain.high_quality_rate == pytest.approx(1 / 3)
    assert chain.usable_time_ratio == pytest.approx(0.9)


def test_a_clips_direct_cost_is_its_own_billable_units() -> None:
    clip = _clip("v1", "A")
    expected = (
        10.0 * INDEX_PER_VIDEO_MINUTE
        + SEARCH_PER_CALL
        + 6 * MOMENT_PER_CALL
        + 3 * DERIVED_READ_PER_CALL
    )
    assert clip.direct_usd == pytest.approx(expected)


def test_looking_at_frames_is_counted_because_the_agent_measured_it() -> None:
    card = score_run(
        [
            QueryOutcome(
                query_id="q",
                query="x",
                clips=[_clip("v1", "A", look_usd=0.25)],
            )
        ]
    )
    assert card.cost.look_usd == pytest.approx(0.25)
    assert card.band("A").attributed_usd >= 0.25


def test_the_attributed_bands_add_up_to_the_run_less_what_nothing_earned() -> None:
    """Every dollar lands on one clip, except what no clip can be blamed for."""
    card = score_run(_run())
    banded = sum(band.attributed_usd for band in card.bands)
    assert banded == pytest.approx(card.cost.total_usd - card.cost.stranded_discovery_usd)


def test_a_search_that_found_nothing_is_still_money_spent() -> None:
    card = score_run(_run())
    assert card.cost.stranded_discovery_usd == pytest.approx(0.02)
    assert card.cost.discovery_usd == pytest.approx(0.09)
    # And it is in the total, so a run that fails half its queries does not
    # look cheaper per clip than one that succeeded on all of them.
    assert card.cost.total_usd > sum(band.attributed_usd for band in card.bands)


def test_cost_to_obtain_is_the_whole_run_over_that_bands_clips() -> None:
    card = score_run(_run())
    band = card.band("A")
    assert band.clips == 1
    assert band.usd_per_clip_obtained == pytest.approx(card.cost.total_usd)
    # ... and is therefore larger than the attributed cost, which is the point.
    assert band.usd_per_clip_obtained > band.usd_per_clip


def test_an_empty_band_reports_zeros_rather_than_dividing_by_none() -> None:
    band = score_run(_run()).band("B")
    assert band.clips == 0
    assert band.usd_per_clip == 0.0
    assert band.usd_per_clip_obtained == 0.0


def test_a_band_with_no_clips_renders_as_a_dash_not_as_free() -> None:
    """`$0.00` and "there were none of these" are different claims."""
    page = render(score_run(_run()))
    empty = next(line for line in page.splitlines() if line.startswith("| **B** |"))
    assert "$0.00 | — | — | —" in empty


def test_what_could_not_be_measured_is_named() -> None:
    card = score_run(_run())
    assert card.cost.unmeasured == list(UNMEASURED_TERMS)
    assert any("model tokens" in term for term in card.cost.unmeasured)


def test_strata_are_scored_separately_and_worst_first() -> None:
    card = score_run(_run())
    names = [stratum.name for stratum in card.by_difficulty]
    assert set(names) == {"medium", "hard"}
    rates = [stratum.acceptance_rate for stratum in card.by_difficulty]
    assert rates == sorted(rates)


@pytest.mark.parametrize(
    ("clip", "expected"),
    [
        (_clip("v", "D", accepted=True), "graded D"),
        (_clip("v", "A", blocking_failures=["G1-HAND"]), "blocking gate failure"),
        (_clip("v", "A", annotation_level="L1"), "below L2"),
    ],
)
def test_an_accepted_clip_the_standard_would_reject_is_reported(
    clip: ClipOutcome, expected: str
) -> None:
    found = contradictions([clip])
    assert found and expected in found[0]


def test_a_clean_run_reports_no_contradictions() -> None:
    assert contradictions([_clip("v1", "A"), _clip("v2", "D")]) == []


def test_a_run_record_round_trips() -> None:
    """A resumed run must be indistinguishable from one that never stopped."""
    for outcome in _run():
        assert outcome_from_dict(outcome_as_dict(outcome)) == outcome


def test_a_dry_run_says_so_where_somebody_will_see_it() -> None:
    card = score_run(
        [QueryOutcome(query_id="q", query="x", candidates=5, dry_run=True)],
        eval_version="v1.0",
    )
    assert card.chain.queries_dry_run == 1
    assert "dry run" in render(card).lower()


def test_the_rendered_scorecard_carries_the_numbers_and_the_caveats() -> None:
    card = score_run(_run(), eval_version="v1.0")
    page = render(card)

    assert "Eval set `v1.0`" in page
    assert "| **A** |" in page and "| **D** |" in page
    assert "sellable externally" in page  # the disposition, not just the letter
    assert "model tokens" in page  # what was not measured
    for section in ("Yield", "Grade bands", "Cost", "By difficulty", "By task family"):
        assert section in page


def test_an_empty_run_renders_without_dividing_by_zero() -> None:
    page = render(score_run([]))
    assert "—" in page


class TestTheScreeningStage:
    """ "0 candidates" was being used to mean two opposite things.

    A query the search cannot answer and a query whose footage all exists and is
    all shot on a tripod are different findings, and only one of them is about
    this pipeline. Measured on the real set: "someone assembling the cabinet"
    finds 18 videos, 14 of which genuinely show cabinet assembly, and every one
    is exocentric.
    """

    @staticmethod
    def _outcome(**kw):
        from video_searching_agent.evaluation.metrics import QueryOutcome

        base = {"query_id": "q", "query": "someone assembling the cabinet"}
        return QueryOutcome(**{**base, **kw})

    def test_a_query_screened_to_nothing_is_not_a_query_that_found_nothing(self):
        from video_searching_agent.evaluation.metrics import score_run

        card = score_run(
            [
                self._outcome(
                    query_id="screened",
                    found=18,
                    screened_out=18,
                    screen_reasons={"frames show exocentric footage": 18},
                    candidates=0,
                ),
                self._outcome(query_id="empty", found=0, candidates=0),
            ]
        )
        chain = card.chain
        assert chain.found == 18
        assert chain.screened_out == 18
        assert chain.queries_screened_to_nothing == 1, "only the one that found footage"
        assert chain.screen_survival_rate == 0.0
        assert chain.screen_reasons == {"frames show exocentric footage": 18}

    def test_the_survival_rate_is_against_what_was_found(self):
        from video_searching_agent.evaluation.metrics import score_run

        card = score_run(
            [
                self._outcome(found=10, screened_out=6, candidates=4),
                self._outcome(query_id="b", found=10, screened_out=4, candidates=6),
            ]
        )
        chain = card.chain
        assert chain.found == 20
        assert chain.candidates == 10
        assert chain.screen_survival_rate == 0.5
        # Neither query was emptied, so neither is counted as such.
        assert chain.queries_screened_to_nothing == 0

    def test_reasons_add_up_across_queries(self):
        from video_searching_agent.evaluation.metrics import score_run

        card = score_run(
            [
                self._outcome(
                    found=5,
                    screened_out=5,
                    screen_reasons={"frames show exocentric footage": 4, "x": 1},
                ),
                self._outcome(
                    query_id="b",
                    found=3,
                    screened_out=3,
                    screen_reasons={"frames show exocentric footage": 3},
                ),
            ]
        )
        assert card.chain.screen_reasons == {
            "frames show exocentric footage": 7,
            "x": 1,
        }

    def test_the_scorecard_shows_the_screen_and_says_what_it_means(self):
        from video_searching_agent.evaluation.metrics import score_run
        from video_searching_agent.evaluation.scorecard import render

        card = score_run(
            [
                self._outcome(
                    found=18,
                    screened_out=18,
                    screen_reasons={"frames show exocentric footage": 18},
                )
            ]
        )
        text = render(card)
        assert "videos the search found" in text
        assert "survived the pre-download screen" in text
        assert "frames show exocentric footage | 18" in text
        assert "found footage and kept none of it" in text

    def test_a_run_with_no_screening_does_not_grow_an_empty_table(self):
        from video_searching_agent.evaluation.metrics import score_run
        from video_searching_agent.evaluation.scorecard import render

        card = score_run([self._outcome(found=4, screened_out=0, candidates=4)])
        text = render(card)
        assert "screened out before download" not in text
