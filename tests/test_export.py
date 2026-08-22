"""Turning anchors into footage a data loader can open.

The corpus is anchors, never cut files — cutting loses the context either side
of a boundary and freezes a boundary that may turn out wrong. But an anchor is
not something you can hand to a training run, so the Datalake's own on-demand
cut is what closes the gap: the original stays whole, the anchor stays movable,
and the export is a view rather than the corpus.

It costs $0.005 a clip, which is why these tests care so much about *not*
exporting more than was asked for.
"""

from __future__ import annotations

from typing import Any

import pytest

from video_searching_agent.api.memories_datalake_client import MemoriesDatalakeError
from video_searching_agent.curation.export import (
    CLIP_COST_USD,
    estimate_cost_usd,
    export_anchors,
)


class _Lake:
    """Records every cut asked for, so over-spending is visible."""

    def __init__(self, fail_on: set[float] | None = None) -> None:
        self.cuts: list[tuple[str, float, float]] = []
        self.fail_on = fail_on or set()

    async def get_clip(self, video_id: str, start: float, end: float) -> dict[str, Any]:
        self.cuts.append((video_id, start, end))
        if start in self.fail_on:
            raise MemoriesDatalakeError("409 video_not_ready")
        return {"url": f"https://signed/{video_id}/clip_{start}-{end}.mp4?sig=abc"}


def anchor(start, end, level="action", sid=None, label=None, video_id="vid_1"):
    return {
        "video_id": video_id,
        "segment_id": sid,
        "hier_level": level,
        "span_start": start,
        "span_end": end,
        "label": label,
    }


@pytest.mark.asyncio
async def test_actions_are_exported_and_the_other_levels_are_not():
    """A task anchor is usually the whole video and an event is a slice of an
    action, so exporting every level delivers the same seconds three times and
    bills for all three."""

    lake = _Lake()
    export = await export_anchors(
        [
            anchor(0.0, 1200.0, level="task"),
            anchor(10.0, 40.0),
            anchor(12.0, 18.0, level="event"),
        ],
        client=lake,
    )
    assert [c[1] for c in lake.cuts] == [10.0]
    assert export.requested == 1
    assert export.delivered == 1


@pytest.mark.asyncio
async def test_every_level_can_be_asked_for_explicitly():
    lake = _Lake()
    export = await export_anchors(
        [anchor(0.0, 100.0, level="task"), anchor(10.0, 40.0)], client=lake, level=None
    )
    assert export.delivered == 2


@pytest.mark.asyncio
async def test_the_cap_is_a_spending_limit_not_a_suggestion():
    lake = _Lake()
    await export_anchors([anchor(n * 10.0, n * 10.0 + 5) for n in range(20)],
                         client=lake, max_clips=3)
    assert len(lake.cuts) == 3, "each cut is charged for"


@pytest.mark.asyncio
async def test_a_failed_cut_is_reported_rather_than_dropped():
    """A silently short dataset is worse than a short one you were told about."""

    lake = _Lake(fail_on={20.0})
    export = await export_anchors(
        [anchor(10.0, 20.0), anchor(20.0, 30.0), anchor(30.0, 40.0)], client=lake
    )
    assert export.requested == 3
    assert export.delivered == 2
    failed = [c for c in export.clips if not c.url]
    assert len(failed) == 1
    assert "video_not_ready" in (failed[0].error or "")


@pytest.mark.asyncio
async def test_hours_count_what_was_delivered_not_what_was_asked_for():
    lake = _Lake(fail_on={0.0})
    export = await export_anchors(
        [anchor(0.0, 3600.0), anchor(3600.0, 7200.0)], client=lake
    )
    assert export.hours == pytest.approx(1.0), "the failed hour is not delivered"
    # ...but it is still billed, because the cut was attempted.
    assert export.cost_usd == pytest.approx(2 * CLIP_COST_USD)


@pytest.mark.asyncio
async def test_anchors_with_no_usable_span_are_skipped_before_spending():
    lake = _Lake()
    export = await export_anchors(
        [
            {"video_id": "vid_1", "hier_level": "action"},
            {"video_id": "vid_1", "hier_level": "action", "span_start": 1.0},
            anchor(10.0, 20.0),
        ],
        client=lake,
    )
    assert len(lake.cuts) == 1
    assert export.requested == 1


@pytest.mark.asyncio
async def test_an_anchor_starting_at_zero_is_exportable():
    """A falsy zero has dropped a first segment in this codebase before."""

    lake = _Lake()
    export = await export_anchors([anchor(0.0, 30.0)], client=lake)
    assert export.delivered == 1
    assert lake.cuts == [("vid_1", 0.0, 30.0)]


def test_the_cost_can_be_known_before_it_is_spent():
    assert estimate_cost_usd(27) == pytest.approx(27 * CLIP_COST_USD)
    assert estimate_cost_usd(0) == 0.0
    assert estimate_cost_usd(-5) == 0.0


@pytest.mark.asyncio
async def test_nothing_to_export_spends_nothing():
    lake = _Lake()
    export = await export_anchors([], client=lake)
    assert export.requested == 0
    assert export.cost_usd == 0.0
    assert lake.cuts == []
