"""What an hour of collected footage actually costs.

A collection run spends money in four places:

1. **Discovery** — Gemini tokens plus per-call search/scrape fees while finding
   candidates. Already measured per run by `UsageMetrics`, so it is passed in
   rather than estimated.
2. **Download** — pulling the files. On self-hosted infrastructure this is
   egress and disk, not an API fee, so it is a configurable per-hour rate that
   defaults to zero and is reported as zero rather than guessed.
3. **Indexing** — Memories.ai Video Datalake charges per minute of video, so
   this scales linearly with the hours collected and is the dominant term.
4. **Annotation** — the agentic curation loop: a moment search, a moment read,
   and the model tokens for the verdict. Writing the verdict back with
   `update_video` is free.

Rates come from https://docs.memories.ai/datalake/pricing. Anything the run did
not measure is left out of the total rather than filled with a guess.

Retrieval is not the same as usable footage: the vendor deck reports that 44% of
an agent's shortlist survived a frame-level check. `usd_per_delivered_hour`
applies that yield so the number quoted is per hour that actually ships.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Published Datalake rates (USD).
INDEX_PER_VIDEO_MINUTE = 0.05
SEARCH_PER_CALL = 0.008
MOMENT_PER_CALL = 0.008
DERIVED_READ_PER_CALL = 0.001
STORAGE_PER_GB_MONTH = 0.02

# Observed share of an agent's shortlist that survives a frame-level check.
DEFAULT_FRAME_CHECK_YIELD = 0.44


class CostBreakdown(BaseModel):
    """Per-run cost accounting, in USD."""

    hours: float = Field(0.0, description="Hours of footage the run collected")

    discovery_usd: float = Field(0.0, description="Measured search + model spend")
    download_usd: float = Field(0.0, description="Egress/disk at the configured rate")
    indexing_usd: float = Field(0.0, description="Datalake indexing, per video-minute")
    annotation_usd: float = Field(0.0, description="Moment search, reads and model tokens")
    storage_usd_per_month: float = Field(
        0.0,
        description="Recurring storage, excluded from the one-off total",
    )

    total_usd: float = Field(0.0, description="One-off cost of this collection")
    usd_per_collected_hour: float = Field(0.0)
    usd_per_delivered_hour: float = Field(
        0.0,
        description="Cost per hour that survives a frame-level check",
    )
    assumed_yield: float = Field(DEFAULT_FRAME_CHECK_YIELD)

    notes: list[str] = Field(default_factory=list)


def estimate_collection_cost(
    hours: float,
    *,
    discovery_usd: float = 0.0,
    annotated_moments: int = 0,
    annotation_tokens_usd: float = 0.0,
    download_usd_per_hour: float = 0.0,
    average_gb_per_hour: float = 1.8,
    frame_check_yield: float = DEFAULT_FRAME_CHECK_YIELD,
    index_fps: float = 1.0,
) -> CostBreakdown:
    """Cost out a collection run.

    Args:
        hours: Hours of footage collected.
        discovery_usd: Measured spend on finding the footage (model + tools).
        annotated_moments: Moments the curation loop searched, read and labelled.
        annotation_tokens_usd: Model spend attributable to those verdicts.
        download_usd_per_hour: Egress/disk rate; zero on owned infrastructure.
        average_gb_per_hour: Storage estimate for 1080p footage, used only for
            the recurring storage line.
        frame_check_yield: Share of retrieved footage expected to survive a
            frame-level check.
        index_fps: Indexing frame rate; cost scales roughly linearly with it.

    Returns:
        A CostBreakdown. Terms the caller could not measure stay at zero and are
        called out in `notes` rather than being invented.
    """
    hours = max(hours, 0.0)
    notes: list[str] = []

    # Indexing dominates: $0.05/video-minute is $3.00 per hour at fps 1.0.
    indexing = hours * 60 * INDEX_PER_VIDEO_MINUTE * max(index_fps, 0.0)

    # One search + one moment read + tokens per annotated moment; the write back
    # via update_video is free.
    annotation = annotated_moments * (SEARCH_PER_CALL + MOMENT_PER_CALL) + annotation_tokens_usd

    download = hours * max(download_usd_per_hour, 0.0)
    if download_usd_per_hour <= 0:
        notes.append("Download billed at $0/h — set a rate if egress is metered.")

    if not annotated_moments:
        notes.append("No annotation pass costed: run the curation loop to include it.")

    if not discovery_usd:
        notes.append("Discovery spend not supplied by the run.")

    total = round(discovery_usd + download + indexing + annotation, 4)
    per_collected = round(total / hours, 4) if hours > 0 else 0.0

    effective_yield = frame_check_yield if 0 < frame_check_yield <= 1 else 1.0
    per_delivered = round(per_collected / effective_yield, 4) if per_collected else 0.0

    return CostBreakdown(
        hours=round(hours, 4),
        discovery_usd=round(discovery_usd, 4),
        download_usd=round(download, 4),
        indexing_usd=round(indexing, 4),
        annotation_usd=round(annotation, 4),
        storage_usd_per_month=round(hours * average_gb_per_hour * STORAGE_PER_GB_MONTH, 4),
        total_usd=total,
        usd_per_collected_hour=per_collected,
        usd_per_delivered_hour=per_delivered,
        assumed_yield=effective_yield,
        notes=notes,
    )
