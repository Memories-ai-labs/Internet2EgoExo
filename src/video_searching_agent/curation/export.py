"""Turn anchors into footage somebody can actually train on.

The dataset is a set of time anchors on whole videos, never cut files, and that
is deliberate — `G2-TREE-5`. Cutting loses the context either side of a boundary,
and a boundary that turns out to be wrong cannot be moved once the file exists.

But an anchor is not something you can hand to a data loader, so a corpus of
anchors and no way to fetch the seconds they name is only half a deliverable.
The Datalake closes that itself: `GET /videos/{id}/clip?start=&end=` cuts the
span on demand and returns a signed URL. The original stays whole, the anchor
stays movable, and the export is a *view* of the corpus rather than the corpus.

That is why this module exists and why it is separate from the agents. Exporting
costs money per clip ($0.005 plus egress), so it is something a caller asks for
once it knows which anchors it wants — never a side effect of curating.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)

logger = logging.getLogger(__name__)

# The Datalake's own price for cutting a span, so a caller can be told what an
# export will cost before it runs rather than after.
CLIP_COST_USD = 0.005


@dataclass
class ExportedClip:
    """One anchor, and the footage it names."""

    video_id: str
    span_start: float
    span_end: float
    url: str | None = None
    segment_id: str | None = None
    label: str | None = None
    error: str | None = None

    @property
    def duration_seconds(self) -> float:
        return round(self.span_end - self.span_start, 3)

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "segment_id": self.segment_id,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "duration_seconds": self.duration_seconds,
            "label": self.label,
            "url": self.url,
            "error": self.error,
        }


@dataclass
class Export:
    """What an export produced, and what it cost."""

    clips: list[ExportedClip] = field(default_factory=list)
    requested: int = 0

    @property
    def delivered(self) -> int:
        return sum(1 for clip in self.clips if clip.url)

    @property
    def hours(self) -> float:
        """Hours of footage actually delivered — not requested, delivered."""

        return round(sum(clip.duration_seconds for clip in self.clips if clip.url) / 3600, 4)

    @property
    def cost_usd(self) -> float:
        """Charged per cut attempted, which is what the bill will say."""

        return round(len(self.clips) * CLIP_COST_USD, 4)

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "delivered": self.delivered,
            "hours": self.hours,
            "cost_usd": self.cost_usd,
            "clips": [clip.as_dict() for clip in self.clips],
        }


def estimate_cost_usd(anchor_count: int) -> float:
    """What exporting this many anchors will cost, before spending it."""

    return round(max(0, anchor_count) * CLIP_COST_USD, 4)


async def export_anchors(
    anchors: list[dict[str, Any]],
    *,
    client: MemoriesDatalakeClient | None = None,
    level: str | None = "action",
    max_clips: int | None = None,
    concurrency: int = 4,
) -> Export:
    """Fetch a signed URL for each anchor.

    Args:
        anchors: Anchor dicts, each with `video_id`, `span_start`, `span_end`,
            and optionally `hier_level`, `segment_id` and `label`.
        client: Datalake client. Created on first use when omitted.
        level: Export only this level. Defaults to ``action``, because a task
            anchor is usually the whole video and an event is a fragment of an
            action — exporting all three levels would deliver the same seconds
            three times and bill for it. None exports everything given.
        max_clips: Stop after this many, so a caller cannot spend more than it
            meant to.
        concurrency: Parallel cuts.

    Returns:
        An Export. A clip with no `url` carries the reason in `error`; a failed
        cut is reported rather than dropped, because a silently short dataset is
        worse than a short one you were told about.
    """
    wanted = [
        anchor
        for anchor in anchors
        if isinstance(anchor, dict)
        and (level is None or str(anchor.get("hier_level") or "") == level)
        and anchor.get("video_id")
        and _as_float(anchor.get("span_start")) is not None
        and _as_float(anchor.get("span_end")) is not None
    ]
    if max_clips is not None:
        wanted = wanted[:max_clips]

    export = Export(requested=len(wanted))
    if not wanted:
        return export

    lake = client or MemoriesDatalakeClient()
    limit = asyncio.Semaphore(max(1, concurrency))

    async def one(anchor: dict[str, Any]) -> ExportedClip:
        start = _as_float(anchor["span_start"]) or 0.0
        end = _as_float(anchor["span_end"]) or 0.0
        clip = ExportedClip(
            video_id=str(anchor["video_id"]),
            span_start=start,
            span_end=end,
            segment_id=anchor.get("segment_id"),
            label=anchor.get("label"),
        )
        async with limit:
            try:
                payload = await lake.get_clip(clip.video_id, start, end)
            except MemoriesDatalakeError as exc:
                clip.error = str(exc)[:200]
                return clip
        url = payload.get("url") if isinstance(payload, dict) else None
        if url:
            clip.url = str(url)
        else:
            clip.error = "the cut returned no URL"
        return clip

    export.clips = list(await asyncio.gather(*(one(anchor) for anchor in wanted)))
    logger.info(
        "exported %d of %d anchors, %.3fh, $%.3f",
        export.delivered,
        export.requested,
        export.hours,
        export.cost_usd,
    )
    return export


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
