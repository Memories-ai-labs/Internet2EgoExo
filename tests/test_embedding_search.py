"""Searching the video's own index instead of the words written about it.

These tests pin the three things that make this safe to build on: the scoping
uses the only form the endpoint honours, nothing anywhere turns a score into a
verdict, and a failed search leaves the caller with what it already knew.
"""

from __future__ import annotations

import pytest

from video_searching_agent.curation.embedding_search import (
    FILTER_LEAVES,
    SEARCH_COST_USD,
    VISUAL_TARGET,
    FrameHit,
    VisualEvidence,
    hits_within,
    search_frames,
    snippets_within,
    visual_evidence_for,
)


def _row(video_id: str, start: float, score: float, snippet: str = "hands") -> dict:
    return {
        "ref": f"{video_id}@{start}-{start + 1}",
        "video_id": video_id,
        "target": VISUAL_TARGET,
        "score": score,
        "start": start,
        "end": start + 1.0,
        "snippet": snippet,
        "thumbnail_url": f"https://example.test/{video_id}/{int(start)}.jpg",
    }


class _FakeLake:
    """Records the request body, because the body is the thing under test."""

    def __init__(self, rows: list[dict] | None = None, fail: Exception | None = None):
        self.rows = rows if rows is not None else []
        self.fail = fail
        self.bodies: list[dict] = []

    async def ensure_collection(self) -> str:
        return "col_test"

    async def _request(self, method: str, path: str, json: dict) -> dict:
        self.bodies.append(json)
        if self.fail:
            raise self.fail
        return {"results": self.rows}


@pytest.mark.asyncio
async def test_scoping_uses_the_only_form_the_endpoint_honours() -> None:
    """`video_id` at the top level is accepted and ignored, which is worse than
    rejected: it returns hits from every other video while looking scoped."""

    lake = _FakeLake([_row("vid_a", 10, 0.4)])
    await search_frames(lake, "hands in the frame", video_ids=["vid_a"])

    body = lake.bodies[0]
    assert body["filter"] == {"video_ids": ["vid_a"]}
    assert "video_id" not in body
    assert "video_ids" not in body, "the top-level form is the one that is ignored"
    assert "scope" not in body
    assert body["targets"] == [VISUAL_TARGET]
    # And the leaves are documented, so a caller reaching for the wrong one
    # finds out from a name rather than from a silently wrong measurement.
    assert "video_ids" in FILTER_LEAVES


@pytest.mark.asyncio
async def test_an_unscoped_search_sends_no_filter_at_all() -> None:
    lake = _FakeLake([_row("vid_a", 1, 0.4)])
    await search_frames(lake, "hands")
    assert "filter" not in lake.bodies[0]


@pytest.mark.asyncio
async def test_hits_come_back_ranked_and_priced() -> None:
    lake = _FakeLake([_row("vid_a", 10, 0.31), _row("vid_a", 20, 0.42), _row("vid_a", 30, 0.37)])
    evidence = await search_frames(lake, "hands", video_ids=["vid_a"])

    assert [hit.start for hit in evidence.hits] == [20, 30, 10]
    assert evidence.cost_usd == SEARCH_COST_USD
    assert evidence.looked is True
    assert evidence.hits[0].thumbnail_url.endswith("/20.jpg")


@pytest.mark.asyncio
async def test_a_stray_video_is_dropped_even_though_the_server_scoped_it() -> None:
    """Costs nothing to enforce, and the alternative is a per-clip number
    computed over somebody else's footage."""

    lake = _FakeLake([_row("vid_a", 1, 0.4), _row("vid_b", 2, 0.9)])
    evidence = await search_frames(lake, "hands", video_ids=["vid_a"])

    assert [hit.video_id for hit in evidence.hits] == ["vid_a"]


@pytest.mark.asyncio
async def test_a_failed_search_decides_nothing_and_is_not_charged_for() -> None:
    lake = _FakeLake(fail=RuntimeError("429 rate limited"))
    evidence = await search_frames(lake, "hands", video_ids=["vid_a"])

    assert evidence.looked is False
    assert evidence.hits == []
    assert evidence.cost_usd == 0.0
    assert "429" in (evidence.error or "")


@pytest.mark.asyncio
async def test_an_empty_query_does_not_reach_the_network() -> None:
    lake = _FakeLake([_row("vid_a", 1, 0.4)])
    evidence = await search_frames(lake, "   ", video_ids=["vid_a"])

    assert lake.bodies == []
    assert evidence.error == "no query"
    assert evidence.cost_usd == 0.0


@pytest.mark.asyncio
async def test_malformed_rows_are_skipped_rather_than_crashing_the_look() -> None:
    lake = _FakeLake(
        [
            {"video_id": "vid_a"},  # no timings
            {"video_id": "vid_a", "start": "x", "end": "y"},
            _row("vid_a", 5, 0.4),
            "not a dict",  # type: ignore[list-item]
        ]
    )
    evidence = await search_frames(lake, "hands", video_ids=["vid_a"])
    assert [hit.start for hit in evidence.hits] == [5]


@pytest.mark.asyncio
async def test_a_hit_with_no_score_still_counts_as_a_hit() -> None:
    lake = _FakeLake([{"video_id": "vid_a", "start": 3, "end": 4, "snippet": "hands"}])
    evidence = await search_frames(lake, "hands", video_ids=["vid_a"])
    assert len(evidence.hits) == 1
    assert evidence.hits[0].score == 0.0


class TestNothingTurnsAScoreIntoAVerdict:
    """Measured against one pizza video: `hands manipulating an object` scored
    0.400, an erupting volcano 0.362 and gibberish 0.354. The bands overlap, so
    a cutoff would pass nonsense confidently. Nothing here may grow one."""

    def test_the_evidence_has_no_verdict_field(self) -> None:
        evidence = VisualEvidence(query="hands", video_id="vid_a")
        for forbidden in ("passed", "confident", "present", "detected", "verdict"):
            assert not hasattr(evidence, forbidden), forbidden

    def test_every_result_carries_the_caveat(self) -> None:
        evidence = VisualEvidence(
            query="hands", video_id="vid_a", hits=[FrameHit("vid_a", 1, 2, 0.99)]
        )
        caveat = evidence.as_dict()["caveat"]
        assert "not detection" in caveat
        assert "rank" in caveat

    def test_a_high_score_and_a_low_one_are_treated_the_same_way(self) -> None:
        """Both are hits. The difference is order, and order only."""

        low = VisualEvidence(query="q", hits=[FrameHit("v", 1, 2, 0.05)])
        high = VisualEvidence(query="q", hits=[FrameHit("v", 1, 2, 0.95)])
        assert low.looked == high.looked
        assert low.seconds == high.seconds


class TestSpansRatherThanDots:
    """Several one-second hits together is a stretch of footage doing the thing;
    a lone second is a glimpse. A caller wants the distinction."""

    def test_adjacent_seconds_merge_into_one_run(self) -> None:
        evidence = VisualEvidence(
            query="q",
            hits=[
                FrameHit("v", 10, 11, 0.4),
                FrameHit("v", 11, 12, 0.4),
                FrameHit("v", 12, 13, 0.4),
            ],
        )
        assert evidence.spans() == [(10.0, 13.0)]

    def test_a_distant_second_stays_its_own_run(self) -> None:
        evidence = VisualEvidence(
            query="q",
            hits=[FrameHit("v", 10, 11, 0.4), FrameHit("v", 200, 201, 0.4)],
        )
        assert evidence.spans() == [(10.0, 11.0), (200.0, 201.0)]

    def test_the_gap_is_the_callers_choice(self) -> None:
        evidence = VisualEvidence(
            query="q",
            hits=[FrameHit("v", 10, 11, 0.4), FrameHit("v", 14, 15, 0.4)],
        )
        assert evidence.spans(gap=1.0) == [(10.0, 11.0), (14.0, 15.0)]
        assert evidence.spans(gap=5.0) == [(10.0, 15.0)]

    def test_no_hits_is_no_spans(self) -> None:
        assert VisualEvidence(query="q").spans() == []


class TestReadingASpan:
    def _evidence(self) -> VisualEvidence:
        return VisualEvidence(
            query="hands",
            hits=[
                FrameHit("v", 5, 6, 0.4, "a hand grips the wrench"),
                FrameHit("v", 30, 31, 0.4, "two hands turn the bolt"),
                FrameHit("v", 31, 32, 0.4, "two hands turn the bolt"),
                FrameHit("v", 90, 91, 0.4, "an empty workbench"),
            ],
        )

    def test_overlap_counts_not_containment(self) -> None:
        """A one-second hit at the very edge is still evidence about the span."""

        got = hits_within(self._evidence(), 30.5, 60.0)
        assert [hit.start for hit in got] == [30, 31]

    def test_a_span_reads_as_what_the_index_saw_second_by_second(self) -> None:
        got = snippets_within(self._evidence(), 0.0, 60.0)
        assert got == ["a hand grips the wrench", "two hands turn the bolt"]

    def test_repeated_descriptions_are_said_once(self) -> None:
        got = snippets_within(self._evidence(), 29.0, 40.0)
        assert got == ["two hands turn the bolt"]

    def test_a_span_with_nothing_in_it_reads_as_nothing(self) -> None:
        assert snippets_within(self._evidence(), 200.0, 300.0) == []


@pytest.mark.asyncio
async def test_several_questions_are_several_searches_and_several_charges() -> None:
    """One phrasing is one embedding, and the same footage answers two
    phrasings differently."""

    lake = _FakeLake([_row("vid_a", 1, 0.4)])
    got = await visual_evidence_for(
        lake, ["hands in frame", "close-up of hands working on a part"], "vid_a"
    )

    assert len(got) == 2
    assert [body["query"] for body in lake.bodies] == [
        "hands in frame",
        "close-up of hands working on a part",
    ]
    assert all(body["filter"] == {"video_ids": ["vid_a"]} for body in lake.bodies)
    assert sum(evidence.cost_usd for evidence in got) == pytest.approx(2 * SEARCH_COST_USD)


class TestCorroboratingHandsAgainstThePixels:
    """The caption-derived G1-HAND ratio is a text judgement about descriptions
    of multi-second spans. This is a text judgement about descriptions of single
    seconds that visual similarity picked out — the same kind of evidence, one
    step closer to the pixels, and able to disagree.
    """

    @pytest.mark.asyncio
    async def test_hand_like_seconds_that_describe_hands_corroborate(self):
        from video_searching_agent.curation.embedding_search import corroborate_hands

        lake = _FakeLake(
            [
                _row("vid_a", 10, 0.40, "two hands grip the wrench and turn it"),
                _row("vid_a", 11, 0.39, "a hand holds the bolt steady"),
            ]
        )
        got = await corroborate_hands(lake, "vid_a", per_query=2)

        assert got.measured is True
        assert got.examined == 2
        assert got.describing_hands == 2
        assert got.share_of_best_seconds == 1.0
        assert any("wrench" in line for line in got.evidence)

    @pytest.mark.asyncio
    async def test_the_most_hand_like_seconds_showing_no_hands_is_the_strong_signal(self):
        """A spinning drum is exactly the case the caption gate got wrong."""

        from video_searching_agent.curation.embedding_search import corroborate_hands

        lake = _FakeLake(
            [
                _row("vid_a", 5, 0.38, "a washing machine drum rotates behind glass"),
                _row("vid_a", 6, 0.37, "an empty worktop beside a kettle"),
            ]
        )
        got = await corroborate_hands(lake, "vid_a", per_query=2)

        assert got.examined == 2
        assert got.describing_hands == 0
        assert got.share_of_best_seconds == 0.0

    @pytest.mark.asyncio
    async def test_it_asks_more_than_one_phrasing_and_pays_for_each(self):
        from video_searching_agent.curation.embedding_search import (
            HAND_QUERIES,
            corroborate_hands,
        )

        lake = _FakeLake([_row("vid_a", 1, 0.4, "a hand")])
        got = await corroborate_hands(lake, "vid_a", per_query=4)

        assert [body["query"] for body in lake.bodies] == list(HAND_QUERIES)
        assert got.cost_usd == pytest.approx(len(HAND_QUERIES) * SEARCH_COST_USD)

    @pytest.mark.asyncio
    async def test_the_same_second_returned_twice_is_counted_once(self):
        """Two phrasings overlap, and a doubled second would inflate both halves
        of the fraction while looking like more evidence."""

        from video_searching_agent.curation.embedding_search import corroborate_hands

        lake = _FakeLake([_row("vid_a", 30, 0.4, "a hand turns the screw")])
        got = await corroborate_hands(lake, "vid_a", per_query=4)

        assert got.examined == 1
        assert got.describing_hands == 1

    @pytest.mark.asyncio
    async def test_no_seconds_means_unmeasured_rather_than_zero(self):
        from video_searching_agent.curation.embedding_search import corroborate_hands

        got = await corroborate_hands(_FakeLake([]), "vid_a")

        assert got.measured is False
        assert got.share_of_best_seconds is None, "a zero here would read as 'no hands'"
        assert got.error

    @pytest.mark.asyncio
    async def test_a_failed_search_is_unmeasured_not_a_verdict(self):
        from video_searching_agent.curation.embedding_search import corroborate_hands

        got = await corroborate_hands(_FakeLake(fail=RuntimeError("402 no balance")), "vid_a")

        assert got.measured is False
        assert got.share_of_best_seconds is None
        assert "402" in (got.error or "")

    def test_the_result_states_its_own_denominator(self):
        from video_searching_agent.curation.embedding_search import HandCorroboration

        payload = HandCorroboration(examined=8, describing_hands=2).as_dict()
        assert "not the whole" in payload["denominator"]
        assert "strong signal when it is low" in payload["denominator"]

    def test_there_is_no_ratio_over_the_video(self):
        """search_frames returns the top-k, so a fraction of the video has no
        denominator here. A field claiming one would be a lie with a number."""

        from video_searching_agent.curation.embedding_search import HandCorroboration

        got = HandCorroboration(examined=8, describing_hands=8)
        for forbidden in ("hand_ratio", "fraction_of_video", "coverage", "hand_frame_ratio"):
            assert not hasattr(got, forbidden), forbidden
