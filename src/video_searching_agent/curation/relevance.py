"""Score anchors against what was actually asked for.

Anchor discovery is exhaustive by design: the cleaning agent walks every caption
segment of a video and marks every run where work is happening. That is the
right way to build a *complete* set of anchors, and it is the wrong way to
answer "which of these is what I asked for" — because it never sees the request.
A query for someone folding laundry and a query for someone soldering produce
the same anchors on the same video.

The Datalake answers the other half directly. `search(query, targets=["caption"])`
is semantic retrieval over the *visual* captions, and it returns timed spans with
scores:

    [  9.0– 20.0] caption 0.452  A power drill screws…
    [205.0–213.0] caption 0.447  A person's hand places…

So the two are complementary, not alternatives: the walk says *where the actions
are*, the search says *which of them the request meant*. This module joins them
by overlap and attaches a relevance score, leaving the anchor set intact.

Nothing here drops an anchor. An unscored anchor means the search did not reach
that part of the video, which is not evidence that nothing happens there — and
top-k retrieval always leaves most of a long video unscored. Scoring is for
ordering and for telling a caller what its query actually matched.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)

logger = logging.getLogger(__name__)

# One search call, priced by the Datalake at $0.008, covers a whole video.
SEARCH_COST_USD = 0.008

# Retrieval returns the best matches, so asking for more than the anchors that
# exist is waste, and asking for fewer leaves obvious matches unscored.
DEFAULT_TOP_K = 25


@dataclass
class ScoredMoment:
    """One span the search returned, with what it matched on."""

    start: float
    end: float
    score: float
    snippet: str = ""

    def overlap_with(self, start: float, end: float) -> float:
        """Seconds this moment and a span share."""

        return max(0.0, min(self.end, end) - max(self.start, start))


@dataclass
class RelevanceReport:
    """What a query matched, and what it cost to ask."""

    query: str
    moments: list[ScoredMoment] = field(default_factory=list)
    scored_anchors: int = 0
    cost_usd: float = 0.0
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "moments_found": len(self.moments),
            "scored_anchors": self.scored_anchors,
            "cost_usd": round(self.cost_usd, 4),
            "error": self.error,
        }


async def score_anchors(
    video_id: str,
    query: str,
    anchors: list[dict[str, Any]],
    *,
    client: MemoriesDatalakeClient | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> RelevanceReport:
    """Attach a relevance score to each anchor that the query reached.

    Each anchor gains ``relevance`` (0.0-1.0) and ``relevance_evidence`` (the
    caption text that matched) in place. Anchors the search did not reach are
    left alone rather than scored zero: absence of retrieval is not evidence of
    irrelevance, and a zero would sort them below genuinely poor matches.

    Args:
        video_id: The indexed video the anchors belong to.
        query: What the collection was looking for, in the words it was asked in.
        anchors: Anchor dicts with `span_start` and `span_end`.
        client: Datalake client. Created on first use when omitted.
        top_k: How many moments to retrieve.

    Returns:
        A RelevanceReport. `error` set means nothing was scored.
    """
    report = RelevanceReport(query=query)
    if not query.strip() or not anchors:
        return report

    lake = client or MemoriesDatalakeClient()
    try:
        payload = await lake.search(query, targets=["caption"], top_k=top_k)
    except MemoriesDatalakeError as exc:
        report.error = str(exc)[:200]
        logger.info("relevance search failed for %s: %s", video_id, exc)
        return report
    report.cost_usd = SEARCH_COST_USD

    for hit in payload.get("results") or []:
        if not isinstance(hit, dict) or hit.get("video_id") != video_id:
            continue
        start, end = _as_float(hit.get("start")), _as_float(hit.get("end"))
        score = _as_float(hit.get("score"))
        if start is None or end is None or score is None:
            continue
        report.moments.append(
            ScoredMoment(
                start=start,
                end=end,
                score=max(0.0, min(1.0, score)),
                snippet=str(hit.get("snippet") or "").strip()[:200],
            )
        )

    if not report.moments:
        return report

    for anchor in anchors:
        start = _as_float(anchor.get("span_start"))
        end = _as_float(anchor.get("span_end"))
        if start is None or end is None or end <= start:
            continue
        # The best-matching moment that actually overlaps the anchor. Overlap,
        # not proximity: a strong match forty seconds away says nothing about
        # this span.
        overlapping = [moment for moment in report.moments if moment.overlap_with(start, end) > 0]
        if not overlapping:
            continue
        best = max(overlapping, key=lambda moment: moment.score)
        anchor["relevance"] = round(best.score, 4)
        if best.snippet:
            anchor["relevance_evidence"] = best.snippet
        report.scored_anchors += 1

    return report


def rank_anchors(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anchors best-match first, with unscored ones after the scored.

    An unscored anchor is not a bad match, it is an unknown one, so it sorts
    after everything scored rather than being treated as a zero — and among
    themselves the unscored keep the order the walk found them in, which is
    chronological.
    """
    scored = [a for a in anchors if isinstance(a.get("relevance"), int | float)]
    unscored = [a for a in anchors if not isinstance(a.get("relevance"), int | float)]
    scored.sort(key=lambda a: float(a["relevance"]), reverse=True)
    return [*scored, *unscored]


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
