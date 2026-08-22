"""Frames from an indexed video, so an agent can look instead of inferring.

Every judgement here used to be read off caption *wording*. The failures were
the kind you only find by looking — a vertical phone clip with a burned-in
watermark was rejected on a hand density computed from the words "pours" and
"places". These tests cover the parts that decide whether looking is affordable
and whether a failure to see is visible to the agent.
"""

from __future__ import annotations

from typing import Any

import pytest

from video_searching_agent.agent.eyes import (
    CUT_COST_USD,
    MAX_CUT_SECONDS,
    Eyes,
    Frames,
)
from video_searching_agent.api.memories_datalake_client import MemoriesDatalakeError


class _Lake:
    def __init__(self, fail: bool = False, url: str | None = "https://signed/clip.mp4"):
        self.fail = fail
        self.url = url
        self.cuts: list[tuple[str, float, float]] = []

    async def get_clip(self, video_id: str, start: float, end: float) -> dict[str, Any]:
        self.cuts.append((video_id, start, end))
        if self.fail:
            raise MemoriesDatalakeError("409 video_not_ready")
        return {"url": self.url} if self.url else {}


def _eyes(lake: _Lake, images: list[bytes] | None = None, dims=(854, 480)) -> Eyes:
    eyes = Eyes(client=lake, ffmpeg="/usr/bin/true")

    def extract(url: str, span_seconds: float, count: int):
        return (images if images is not None else [b"jpeg"] * count), dims[0], dims[1]

    eyes._extract = extract  # type: ignore[method-assign]
    return eyes


@pytest.mark.asyncio
async def test_a_look_cuts_the_span_and_returns_frames():
    lake = _Lake()
    frames = await _eyes(lake).look("vid_1", 10.0, 40.0, count=3)
    assert lake.cuts == [("vid_1", 10.0, 40.0)]
    assert len(frames.images) == 3
    assert frames.cost_usd == pytest.approx(CUT_COST_USD)
    assert frames.looked is True


@pytest.mark.asyncio
async def test_the_same_span_is_only_paid_for_once():
    """An agent that reconsiders a span it has seen must not be billed again."""

    lake = _Lake()
    eyes = _eyes(lake)
    first = await eyes.look("vid_1", 10.0, 40.0, count=3)
    second = await eyes.look("vid_1", 10.0, 40.0, count=3)
    assert second is first
    assert len(lake.cuts) == 1
    assert eyes.spent_usd == pytest.approx(CUT_COST_USD)


@pytest.mark.asyncio
async def test_orientation_is_measured_from_the_file():
    """The fact that was going unmeasured, and it is decisive."""

    portrait = await _eyes(_Lake(), dims=(240, 360)).look("vid_1", 0.0, 20.0)
    landscape = await _eyes(_Lake(), dims=(854, 480)).look("vid_1", 0.0, 20.0)
    assert portrait.orientation == "portrait"
    assert landscape.orientation == "landscape"
    assert "portrait" in portrait.describe()


@pytest.mark.asyncio
async def test_a_very_long_span_is_sampled_around_its_middle():
    """Cutting an hour to look at it is slow and large for no benefit."""

    lake = _Lake()
    await _eyes(lake).look("vid_1", 0.0, 3600.0)
    _, start, end = lake.cuts[0]
    assert end - start == pytest.approx(MAX_CUT_SECONDS)
    assert start > 0, "sampled around the middle, not from the front"


@pytest.mark.asyncio
async def test_a_cut_that_fails_says_so_rather_than_returning_nothing():
    """An agent that cannot see must abstain, which it can only do if it knows."""

    frames = await _eyes(_Lake(fail=True)).look("vid_1", 10.0, 40.0)
    assert frames.looked is False
    assert "video_not_ready" in (frames.error or "")
    assert "could not look" in frames.describe()


@pytest.mark.asyncio
async def test_a_cut_with_no_url_is_reported():
    frames = await _eyes(_Lake(url=None)).look("vid_1", 10.0, 40.0)
    assert frames.looked is False
    assert frames.error == "the cut returned no URL"


@pytest.mark.asyncio
async def test_a_clip_that_yields_no_frames_is_reported():
    frames = await _eyes(_Lake(), images=[]).look("vid_1", 10.0, 40.0)
    assert frames.looked is False
    assert frames.error == "the clip yielded no frames"


@pytest.mark.asyncio
async def test_without_ffmpeg_looking_is_unavailable_not_fatal():
    """A deployment that cannot extract frames should say so, not fail to start."""

    eyes = Eyes(client=_Lake(), ffmpeg="")
    assert eyes.available is False
    frames = await eyes.look("vid_1", 10.0, 40.0)
    assert frames.looked is False
    assert "no ffmpeg" in (frames.error or "")
    assert frames.cost_usd == 0.0, "nothing was cut, so nothing was charged"


@pytest.mark.asyncio
async def test_the_frame_count_is_bounded():
    lake = _Lake()
    frames = await _eyes(lake).look("vid_1", 0.0, 60.0, count=99)
    assert len(frames.images) <= 8


def test_an_unmeasured_source_has_no_orientation():
    assert Frames(video_id="v", start=0, end=1).orientation is None
