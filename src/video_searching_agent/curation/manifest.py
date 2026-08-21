"""Turn a run's candidate references into a dataset manifest.

Shared by the streaming and non-streaming agents so both produce the same
deliverable: clips annotated with viewpoint, duration and licence, ranked by
usability, with the totals that say whether the collection goal was met.
"""

from __future__ import annotations

from video_searching_agent.curation.cost import estimate_collection_cost
from video_searching_agent.curation.scoring import score_candidate
from video_searching_agent.curation.viewpoint import Viewpoint, classify_viewpoint
from video_searching_agent.models.dataset import DatasetClip, DatasetManifest
from video_searching_agent.models.query import MetricType, ParsedQuery
from video_searching_agent.models.result import VideoReference


def curate_references(
    references: list[VideoReference],
    parsed_query: ParsedQuery | None,
    query: str = "",
    discovery_usd: float = 0.0,
) -> tuple[list[VideoReference], DatasetManifest]:
    """Classify, filter and rank candidates, and build the manifest.

    Each kept reference is annotated in place with its viewpoint verdict and
    usability score, so the answer and the UI show the same numbers as the
    manifest.

    Args:
        references: Candidate references extracted from tool results.
        parsed_query: The run's slots; None means no requirements at all.
        query: Original query text, recorded on the manifest.
        discovery_usd: What the run already spent finding these candidates, so
            the manifest can report a real cost per hour.

    Returns:
        (kept references ranked best-first, manifest).
    """
    wanted = parsed_query.viewpoint if parsed_query else None
    min_duration = parsed_query.min_duration_seconds if parsed_query else None
    license_filter = parsed_query.license_filter if parsed_query else "any"
    metric = parsed_query.metric if parsed_query else MetricType.USABILITY

    kept: list[VideoReference] = []
    exclusion_reasons: dict[str, int] = {}

    for reference in references:
        verdict = classify_viewpoint(
            title=reference.title,
            description=reference.relevance_note,
        )
        score = score_candidate(
            verdict,
            reference.duration_seconds,
            reference.license,
            wanted_viewpoint=wanted,
            min_duration_seconds=min_duration,
            license_filter=license_filter,
        )

        if not score.usable:
            reason = score.excluded_reason or "excluded"
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            continue

        reference.viewpoint = verdict.viewpoint
        reference.viewpoint_confidence = verdict.confidence
        reference.viewpoint_evidence = verdict.evidence
        reference.usability_score = score.total
        kept.append(reference)

    if metric == MetricType.LONGEST:
        kept.sort(key=lambda r: r.duration_seconds or 0, reverse=True)
    elif metric == MetricType.USABILITY:
        kept.sort(key=lambda r: r.usability_score, reverse=True)

    manifest = DatasetManifest(
        query=query or (parsed_query.original_query if parsed_query else ""),
        requested_viewpoint=wanted,
        target_hours=parsed_query.target_hours if parsed_query else None,
        excluded_clips=sum(exclusion_reasons.values()),
        exclusion_reasons=exclusion_reasons,
        clips=[_to_clip(reference) for reference in kept],
    ).recompute_totals()

    manifest.cost = estimate_collection_cost(
        manifest.total_hours,
        discovery_usd=discovery_usd,
    )

    return kept, manifest


def _to_clip(reference: VideoReference) -> DatasetClip:
    """Project a reference onto its manifest row."""
    return DatasetClip(
        url=reference.url,
        platform=reference.platform,
        platform_id=reference.video_id or None,
        title=reference.title,
        creator=reference.creator,
        duration_seconds=reference.duration_seconds,
        published_at=reference.published_at,
        viewpoint=reference.viewpoint if isinstance(reference.viewpoint, Viewpoint)
        else Viewpoint.UNKNOWN,
        viewpoint_confidence=reference.viewpoint_confidence,
        viewpoint_evidence=reference.viewpoint_evidence,
        license=reference.license,
        usability_score=reference.usability_score,
        thumbnail_url=reference.thumbnail_url,
        notes=reference.relevance_note,
    )
