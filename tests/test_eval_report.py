"""The recurring report's arithmetic and its honesty.

The report is the thing somebody glances at every morning, which makes two of
its properties load-bearing. It must not let a twelve-clip percentage read like
a measurement — hence the interval, and hence a test that the interval is
actually printed. And it must not pool numbers that are not comparable: a
rolling window that mixes a 12-query tick with a 200-query run is neither, and
the trend it draws would be an artefact of the mixing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from video_searching_agent.evaluation.metrics import ClipOutcome, QueryOutcome, score_run
from video_searching_agent.evaluation.report import (
    README_END,
    README_START,
    Snapshot,
    append_history,
    load_history,
    pool,
    render_readme_block,
    render_report,
    same_slice,
    snapshot_of,
    update_readme,
    wilson,
)


def _snapshot(hours_ago: float = 0.0, **overrides) -> Snapshot:
    moment = datetime(2026, 8, 22, 12, 0, tzinfo=UTC) - timedelta(hours=hours_ago)
    base = {
        "ran_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "eval_version": "v1.0",
        "slice_name": "core",
        "queries": 12,
        "graded": 12,
        "accepted": 6,
        "high_quality": 2,
        "delivered_hours": 1.0,
        "usable_hours": 0.8,
        "total_usd": 6.0,
        "grades": {"A": 1, "B": 1, "C": 4, "D": 6},
        "found": 60,
        "candidates": 15,
    }
    return Snapshot(**{**base, **overrides})


@pytest.mark.parametrize(
    ("successes", "total"),
    [(0, 0), (0, 12), (12, 12), (1, 12), (6, 12), (50, 200)],
)
def test_the_interval_stays_inside_zero_and_one(successes: int, total: int) -> None:
    """The textbook normal interval goes negative at 1 of 12. Wilson does not."""
    low, high = wilson(successes, total)
    assert 0.0 <= low <= high <= 1.0


def test_a_small_sample_gets_a_wide_interval_and_a_large_one_a_narrow_one() -> None:
    small = wilson(6, 12)
    large = wilson(100, 200)
    assert (small[1] - small[0]) > (large[1] - large[0]) > 0
    # The headline claim in the README: twelve clips is about ±25 points.
    assert 0.45 < (small[1] - small[0]) < 0.60


def test_pooling_sums_counts_rather_than_averaging_rates() -> None:
    """Averaging rates weights a 2-clip run like a 100-clip one."""
    window = pool(
        [
            _snapshot(graded=2, accepted=2, high_quality=0),
            _snapshot(graded=100, accepted=10, high_quality=0),
        ]
    )
    assert window.graded == 102
    assert window.accepted == 12
    # Summed: 12%. Averaged, it would have been 55%.
    assert window.acceptance_rate == pytest.approx(12 / 102)


def test_an_empty_window_has_no_rate_rather_than_a_zero_one() -> None:
    window = pool([])
    assert window.ticks == 0
    assert window.acceptance_rate == 0.0


def test_only_ticks_that_ran_the_same_queries_are_compared() -> None:
    history = [
        _snapshot(hours_ago=16, slice_name="core"),
        _snapshot(hours_ago=8, slice_name="all", graded=200, accepted=100),
        _snapshot(hours_ago=0, slice_name="core"),
    ]
    lineage = same_slice(history, "core")
    assert [s.slice_name for s in lineage] == ["core", "core"]
    assert pool(lineage).graded == 24


def test_the_screen_gets_its_own_trend_line() -> None:
    """A change in what the screen lets through is invisible in acceptance."""
    latest = _snapshot()
    assert latest.screen_survival_rate == pytest.approx(15 / 60)

    window = pool([_snapshot(hours_ago=8), latest])
    assert window.found == 120 and window.candidates == 30
    assert window.screen_survival_rate == pytest.approx(0.25)

    block = render_readme_block([latest])
    assert "survived the screen" in block
    assert "(15/60)" in block


def test_a_run_that_never_counted_the_screen_says_so_instead_of_zero() -> None:
    """`66/0` is not a ratio, and 0% would read as "the screen kept nothing"."""
    old = _snapshot(found=0, candidates=66)
    assert old.screen_measured is False

    block = render_readme_block([old])
    row = next(line for line in block.splitlines() if "survived the screen" in line)
    assert "(66/0)" not in row
    assert "0%" not in row
    assert "—" in row


def test_the_readme_block_carries_the_interval_and_the_caveat() -> None:
    block = render_readme_block([_snapshot(hours_ago=24), _snapshot()])

    assert block.startswith(README_START) and block.endswith(README_END)
    assert "**50%** (6/12)" in block  # the rate, with its denominator
    assert "%–" in block  # the interval
    assert "every eight hours" in block
    assert "rather than a tick" in block  # the caveat
    assert "eval/REPORT.md" in block


def test_a_refused_tick_says_so_in_the_readme_not_just_the_report() -> None:
    """The README is what gets read; a warning only in the report is not a warning."""
    refused = _snapshot(blocked=2)
    block = render_readme_block([refused])
    assert "refused by the platform" in block
    assert "not comparable to a clean one" in block

    clean = render_readme_block([_snapshot()])
    assert "refused by the platform" not in clean


def test_the_readme_block_says_so_when_nothing_has_run() -> None:
    block = render_readme_block([])
    assert "No recurring run has reported yet" in block


def test_movement_is_measured_against_the_same_slice_a_day_earlier() -> None:
    history = [
        _snapshot(hours_ago=25, accepted=3),
        _snapshot(hours_ago=8, accepted=4),
        _snapshot(hours_ago=0, accepted=6),
    ]
    block = render_readme_block(history)
    # 3/12 = 25% a day ago, 6/12 = 50% now.
    assert "25%" in block and "**50%** (6/12)" in block


def test_updating_the_readme_touches_only_the_block() -> None:
    original = f"# Title\n\nbefore\n\n{README_START}\nold\n{README_END}\n\nafter\n"
    updated = update_readme(original, f"{README_START}\nnew\n{README_END}")
    assert "before" in updated and "after" in updated
    assert "old" not in updated and "new" in updated


def test_a_readme_without_markers_is_an_error_rather_than_a_silent_no_op() -> None:
    with pytest.raises(ValueError, match="markers"):
        update_readme("# Title\n\nno markers here\n", "block")


def test_the_history_round_trips_through_the_file(tmp_path) -> None:
    path = tmp_path / "history.jsonl"
    first, second = _snapshot(hours_ago=8), _snapshot()
    append_history(path, first)
    append_history(path, second)

    loaded = load_history(path)
    assert [s.ran_at for s in loaded] == [first.ran_at, second.ran_at]
    assert loaded[0].build == {} and loaded[1].grades == second.grades


def test_an_unreadable_line_does_not_lose_the_rest_of_the_history(tmp_path) -> None:
    path = tmp_path / "history.jsonl"
    append_history(path, _snapshot())
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json\n\n")
    append_history(path, _snapshot(hours_ago=-8))
    assert len(load_history(path)) == 2


def test_a_missing_history_is_empty_rather_than_an_error(tmp_path) -> None:
    assert load_history(tmp_path / "nothing.jsonl") == []


def _card():
    return score_run(
        [
            QueryOutcome(
                query_id="q1",
                query="someone folding cloth",
                task_family="Laundry & Clothing Care",
                difficulty="medium",
                candidates=4,
                attempted=1,
                indexed=1,
                discovery_usd=0.03,
                clips=[
                    ClipOutcome(
                        query_id="q1",
                        video_id="v1",
                        grade="B",
                        score=74,
                        accepted=True,
                        annotation_level="L2",
                        duration_seconds=600,
                        usable_seconds=540,
                        action_anchors=6,
                        indexed_minutes=10.0,
                        moment_search_calls=1,
                        moment_read_calls=6,
                        derived_reads=3,
                    )
                ],
            )
        ],
        eval_version="v1.0",
    )


def test_a_snapshot_keeps_what_was_measured_and_what_measured_it() -> None:
    card = _card()
    snapshot = snapshot_of(
        card,
        ran_at=datetime(2026, 8, 22, 8, 0, tzinfo=UTC),
        commit="abc123def456",
        deployment="https://example.test",
        build={"version": "0.1.0", "model": "some-model", "viewpoint_check": "frames"},
    )
    assert snapshot.ran_at == "2026-08-22T08:00:00Z"
    assert snapshot.graded == 1 and snapshot.accepted == 1 and snapshot.high_quality == 1
    assert snapshot.grades == {"A": 0, "B": 1, "C": 0, "D": 0}
    # The build is why a step in the trend can be attributed to something.
    assert snapshot.build["viewpoint_check"] == "frames"
    assert snapshot.commit == "abc123def456"


def test_the_report_shows_the_build_the_interval_and_the_scorecard() -> None:
    card = _card()
    snapshot = snapshot_of(card, build={"version": "0.1.0", "model": "m"})
    page = render_report(card, snapshot, [snapshot])

    assert "# Performance report — " in page
    assert "version `0.1.0`" in page
    assert "95% interval" in page
    assert "not visible in one tick" in page  # the caveat, in words
    for section in ("Headline", "Grades", "Trend", "Full scorecard"):
        assert section in page


def test_a_report_with_nothing_graded_says_undefined_rather_than_zero() -> None:
    card = score_run([QueryOutcome(query_id="q", query="x", error="no candidates")])
    snapshot = snapshot_of(card)
    page = render_report(card, snapshot, [snapshot])
    assert "undefined rather than zero" in page
