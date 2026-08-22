"""Ask the raw video's own index, not the words written about it.

Every judgement in the cleaning, clipping and annotating path has read *caption
text*: a clip-level description, several seconds wide, written about the footage.
`frame_check` says so in its own docstring — "a text judgement about a visual
description". That is why a gate could report *hands visible at 0.95* from words
like "pours" and "places" while the footage was a spinning drum.

The Datalake indexes the video itself, and accepts these search targets:

    title | summary | entity | speaker | event | caption | transcription
    | frame_embedding | clip_embedding

Only `caption` and `transcription` were ever used. `frame_embedding` is the
per-second visual index, and it is a different instrument:

| | caption | frame_embedding |
|---|---|---|
| granularity | 7-15s spans | **1 second** |
| built from | a description of a span | the frames themselves |
| carries | text | text *for that second*, score, thumbnail URL |

On the same visual query the two return almost disjoint moments, which is the
point: one is retrieving over what a describer wrote, the other over what the
camera saw.

**Scoping, and a trap.** A search is narrowed with ``filter: {"video_ids": [...]}``
and nothing else. ``video_id``, ``video_ids``, ``scope``, ``start`` and ``end``
as top-level parameters are *silently accepted and ignored* — they come back
looking like a scoped result while containing hits from every other video in the
collection. Only ``filter`` validates its leaves, and only ``video_ids`` and
``tags`` are leaves. A per-clip measurement built on the ignored form would have
been computed over the whole collection.

**Scores rank; they do not measure.** Measured against one pizza-making video,
ten hits per query:

| query | best score |
|---|---|
| `hands manipulating an object` | 0.400 |
| `a person folding clothes` | 0.403 |
| `aerial drone footage of a volcano erupting` | 0.362 |
| `qwertzuiop asdfghjkl zxcvbnm` | 0.354 |

Gibberish scores 0.354 and an erupting volcano beats it. The bands overlap, so
there is no cutoff at which a score means "this is present" — a `>= 0.35` gate
would pass nonsense confidently. Nothing in this module thresholds a score, and
nothing downstream should either: use the ranking to *find* the seconds worth
looking at, and decide on the evidence those seconds carry.

Which is the useful part. A hit's ``snippet`` is a description of that one
second — "A person's hands are actively pressing down on pizza dough" — so the
judgement moves from a caption about fifteen seconds to a description of one,
chosen by visual similarity rather than by word match.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Same price as any other moment search on the published list.
SEARCH_COST_USD = 0.008

# The only two filter leaves the endpoint accepts. Kept here so a caller that
# reaches for `video_id` finds out from a name rather than from a silent result.
FILTER_LEAVES = ("video_ids", "tags")

VISUAL_TARGET = "frame_embedding"


@dataclass
class FrameHit:
    """One second of footage the visual index returned, and why."""

    video_id: str
    start: float
    end: float
    score: float
    snippet: str = ""
    thumbnail_url: str = ""
    ref: str = ""

    @property
    def midpoint(self) -> float:
        return (self.start + self.end) / 2

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "start": self.start,
            "end": self.end,
            "score": round(self.score, 4),
            "snippet": self.snippet,
            "thumbnail_url": self.thumbnail_url,
        }


@dataclass
class VisualEvidence:
    """What the visual index found for one query, over one video.

    Deliberately has no ``passed`` or ``confident`` field. The scores rank and
    do not measure (see the module docstring), so a verdict cannot be read off
    them — the caller reads :attr:`hits` and their snippets and decides.
    """

    query: str
    video_id: str | None = None
    hits: list[FrameHit] = field(default_factory=list)
    cost_usd: float = 0.0
    error: str | None = None

    @property
    def looked(self) -> bool:
        return self.error is None

    @property
    def seconds(self) -> list[float]:
        """Midpoints of the matched seconds, in time order."""
        return sorted(hit.midpoint for hit in self.hits)

    def spans(self, gap: float = 3.0) -> list[tuple[float, float]]:
        """Matched seconds merged into runs, so a caller sees regions not dots.

        A run is where the index kept matching: several one-second hits close
        together is a stretch of footage doing the thing, where a lone second is
        a glimpse. ``gap`` is how far apart two hits may be and still count as
        one stretch.
        """
        if not self.hits:
            return []
        ordered = sorted((hit.start, hit.end) for hit in self.hits)
        merged: list[list[float]] = [list(ordered[0])]
        for start, end in ordered[1:]:
            if start - merged[-1][1] <= gap:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return [(start, end) for start, end in merged]

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "video_id": self.video_id,
            "hits": [hit.as_dict() for hit in self.hits],
            "spans": self.spans(),
            "cost_usd": round(self.cost_usd, 5),
            "error": self.error,
            # Carried on every result so a reader never mistakes a ranking for a
            # detector. See the score table in the module docstring.
            "caveat": "visual-similarity ranking, not detection; scores rank and do not measure",
        }


def _read_hit(row: dict[str, Any]) -> FrameHit | None:
    """One search result, or None when it is not a usable frame hit."""
    try:
        start = float(row["start"])
        end = float(row["end"])
    except (KeyError, TypeError, ValueError):
        return None
    try:
        score = float(row.get("score") or 0.0)
    except (TypeError, ValueError):
        score = 0.0
    return FrameHit(
        video_id=str(row.get("video_id") or ""),
        start=start,
        end=end,
        score=score,
        snippet=str(row.get("snippet") or "")[:600],
        thumbnail_url=str(row.get("thumbnail_url") or ""),
        ref=str(row.get("ref") or ""),
    )


async def search_frames(
    lake: Any,
    query: str,
    *,
    video_ids: list[str] | None = None,
    top_k: int = 20,
    collection_id: str | None = None,
) -> VisualEvidence:
    """Find the seconds of footage that most look like ``query``.

    Args:
        lake: A Datalake client.
        query: What to look for, in plain words.
        video_ids: Narrow to these videos. Passed as ``filter.video_ids``,
            which is the only form the endpoint honours.
        top_k: How many seconds to return.
        collection_id: Which collection. Defaults to the resolved one.

    Returns:
        A :class:`VisualEvidence`. A failed search returns one with ``error``
        set rather than raising, because looking is never load-bearing: the
        caller keeps whatever it already knew.
    """
    evidence = VisualEvidence(query=query, video_id=(video_ids or [None])[0])
    if not query.strip():
        evidence.error = "no query"
        return evidence

    body: dict[str, Any] = {
        "query": query,
        "targets": [VISUAL_TARGET],
        "mode": "semantic",
        "top_k": max(1, top_k),
    }
    if video_ids:
        body["filter"] = {"video_ids": list(video_ids)}
    try:
        body["collection_id"] = collection_id or await lake.ensure_collection()
        payload = await lake._request("POST", "/search", json=body)
    except Exception as exc:  # noqa: BLE001 - a failed look decides nothing
        logger.info("visual search failed for %r: %s", query[:60], exc)
        evidence.error = str(exc)[:200]
        return evidence

    evidence.cost_usd = SEARCH_COST_USD
    rows = payload.get("results") or []
    if not isinstance(rows, list):
        return evidence
    for row in rows:
        if not isinstance(row, dict):
            continue
        hit = _read_hit(row)
        # A scoped search should only return the videos asked for, but the
        # scoping is server-side and this costs nothing to enforce.
        if hit and (not video_ids or hit.video_id in set(video_ids)):
            evidence.hits.append(hit)
    evidence.hits.sort(key=lambda hit: hit.score, reverse=True)
    return evidence


async def visual_evidence_for(
    lake: Any,
    queries: list[str],
    video_id: str,
    *,
    top_k: int = 12,
    collection_id: str | None = None,
) -> list[VisualEvidence]:
    """Run several visual questions against one video.

    Several rather than one because a single phrasing is a single embedding, and
    the same footage answers "hands in frame" and "close-up of hands working on
    a part" differently. Costs :data:`SEARCH_COST_USD` per query.
    """
    out: list[VisualEvidence] = []
    for query in queries:
        out.append(
            await search_frames(
                lake,
                query,
                video_ids=[video_id],
                top_k=top_k,
                collection_id=collection_id,
            )
        )
    return out


def hits_within(evidence: VisualEvidence, start: float, end: float) -> list[FrameHit]:
    """The matched seconds that fall inside a span.

    Overlap, not containment: a one-second hit at the very edge of a span is
    still evidence about that span.
    """
    return [hit for hit in evidence.hits if hit.end > start and hit.start < end]


def snippets_within(
    evidence: VisualEvidence, start: float, end: float, limit: int = 6
) -> list[str]:
    """What the index says is happening in a span, second by second.

    This is the replacement for reading a clip-level caption: the text still
    comes from a describer, but it describes *one second* that visual similarity
    picked out, rather than fifteen seconds picked out by a word match.
    """
    seen: set[str] = set()
    out: list[str] = []
    for hit in sorted(hits_within(evidence, start, end), key=lambda h: h.start):
        text = hit.snippet.strip()
        key = text.lower()[:80]
        if text and key not in seen:
            seen.add(key)
            out.append(text)
        if len(out) >= limit:
            break
    return out
