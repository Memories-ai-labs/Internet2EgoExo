"""Scoring anchors against the request that asked for them.

Anchor discovery never sees the query — it walks every caption segment and marks
where work happens, which is right for building a complete set and useless for
deciding which anchors the request meant. The Datalake's semantic search over
visual captions answers that half, and these two are joined by overlap.

The care here is all about *not* over-claiming: an anchor the search did not
reach is unknown, not irrelevant, and top-k retrieval leaves most of a long
video unreached.
"""

from __future__ import annotations

from typing import Any

import pytest

from video_searching_agent.api.memories_datalake_client import MemoriesDatalakeError
from video_searching_agent.curation.relevance import (
    SEARCH_COST_USD,
    rank_anchors,
    score_anchors,
)


class _Lake:
    def __init__(self, results: list[dict[str, Any]] | None = None, fail: bool = False):
        self.results = results or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"query": query, **kwargs})
        if self.fail:
            raise MemoriesDatalakeError("503 upstream")
        return {"results": self.results}


def hit(start, end, score, video_id="vid_1", snippet="a hand turns a screwdriver"):
    return {
        "video_id": video_id,
        "start": start,
        "end": end,
        "score": score,
        "snippet": snippet,
    }


def anchor(start, end):
    return {"span_start": start, "span_end": end, "hier_level": "action"}


@pytest.mark.asyncio
async def test_the_visual_captions_are_what_is_searched():
    """Speech is a different modality; a silent video still has captions."""

    lake = _Lake()
    await score_anchors("vid_1", "using a drill", [anchor(0.0, 30.0)], client=lake)
    assert lake.calls[0]["targets"] == ["caption"]


@pytest.mark.asyncio
async def test_an_overlapping_moment_scores_its_anchor():
    lake = _Lake([hit(10.0, 20.0, 0.44)])
    anchors = [anchor(0.0, 30.0)]
    report = await score_anchors("vid_1", "using a drill", anchors, client=lake)

    assert anchors[0]["relevance"] == pytest.approx(0.44)
    assert anchors[0]["relevance_evidence"] == "a hand turns a screwdriver"
    assert report.scored_anchors == 1
    assert report.cost_usd == pytest.approx(SEARCH_COST_USD)


@pytest.mark.asyncio
async def test_a_strong_match_elsewhere_in_the_video_scores_nothing_here():
    """Overlap, not proximity. A match forty seconds away says nothing."""

    lake = _Lake([hit(400.0, 420.0, 0.9)])
    anchors = [anchor(0.0, 30.0)]
    report = await score_anchors("vid_1", "using a drill", anchors, client=lake)

    assert "relevance" not in anchors[0]
    assert report.scored_anchors == 0
    assert report.moments, "the moment was found, it just does not apply"


@pytest.mark.asyncio
async def test_the_best_overlapping_moment_wins():
    lake = _Lake([hit(0.0, 10.0, 0.3), hit(20.0, 30.0, 0.7), hit(5.0, 15.0, 0.5)])
    anchors = [anchor(0.0, 30.0)]
    await score_anchors("vid_1", "using a drill", anchors, client=lake)
    assert anchors[0]["relevance"] == pytest.approx(0.7)


@pytest.mark.asyncio
async def test_hits_from_other_videos_are_ignored():
    """A collection search returns the whole collection."""

    lake = _Lake([hit(0.0, 30.0, 0.9, video_id="vid_other")])
    anchors = [anchor(0.0, 30.0)]
    report = await score_anchors("vid_1", "using a drill", anchors, client=lake)
    assert "relevance" not in anchors[0]
    assert report.moments == []


@pytest.mark.asyncio
async def test_an_unreached_anchor_is_left_unscored_not_zeroed():
    """Absence of retrieval is not evidence of irrelevance, and a zero would
    sort it below genuinely poor matches."""

    lake = _Lake([hit(0.0, 10.0, 0.5)])
    anchors = [anchor(0.0, 20.0), anchor(900.0, 950.0)]
    await score_anchors("vid_1", "using a drill", anchors, client=lake)
    assert anchors[0]["relevance"] == pytest.approx(0.5)
    assert "relevance" not in anchors[1]


@pytest.mark.asyncio
async def test_a_failed_search_scores_nothing_and_says_why():
    lake = _Lake(fail=True)
    anchors = [anchor(0.0, 30.0)]
    report = await score_anchors("vid_1", "using a drill", anchors, client=lake)
    assert report.error and "503" in report.error
    assert report.cost_usd == 0.0
    assert "relevance" not in anchors[0]


@pytest.mark.asyncio
async def test_an_empty_query_spends_nothing():
    lake = _Lake([hit(0.0, 10.0, 0.5)])
    report = await score_anchors("vid_1", "   ", [anchor(0.0, 30.0)], client=lake)
    assert lake.calls == []
    assert report.cost_usd == 0.0


def test_ranking_puts_the_unknown_after_the_scored():
    anchors = [
        {"span_start": 0.0, "span_end": 10.0},
        {"span_start": 10.0, "span_end": 20.0, "relevance": 0.2},
        {"span_start": 20.0, "span_end": 30.0},
        {"span_start": 30.0, "span_end": 40.0, "relevance": 0.8},
    ]
    ranked = rank_anchors(anchors)
    assert [a.get("relevance") for a in ranked] == [0.8, 0.2, None, None]
    # The unscored keep the order the walk found them in, which is chronological.
    assert [a["span_start"] for a in ranked[2:]] == [0.0, 20.0]


def test_a_relevance_of_zero_is_a_score_not_a_gap():
    """0.0 means the search looked and found nothing here; that is information."""

    ranked = rank_anchors(
        [{"span_start": 0.0, "span_end": 1.0, "relevance": 0.0},
         {"span_start": 1.0, "span_end": 2.0}]
    )
    assert ranked[0]["relevance"] == 0.0
