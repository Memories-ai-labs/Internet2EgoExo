"""Turn a run's candidate references into a dataset manifest.

Shared by the streaming and non-streaming agents so both produce the same
deliverable: clips annotated with viewpoint, duration and licence, ranked by
usability, with the totals that say whether the collection goal was met.
"""

from __future__ import annotations

import logging
from typing import Any

from video_searching_agent.curation.cost import estimate_collection_cost
from video_searching_agent.curation.scoring import score_candidate
from video_searching_agent.curation.viewpoint import Viewpoint, classify_viewpoint
from video_searching_agent.models.dataset import DatasetClip, DatasetManifest
from video_searching_agent.models.query import MetricType, ParsedQuery
from video_searching_agent.models.result import VideoReference
from video_searching_agent.utils.youtube_urls import youtube_video_id

logger = logging.getLogger(__name__)


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
        viewpoint=reference.viewpoint
        if isinstance(reference.viewpoint, Viewpoint)
        else Viewpoint.UNKNOWN,
        viewpoint_confidence=reference.viewpoint_confidence,
        viewpoint_evidence=reference.viewpoint_evidence,
        license=reference.license,
        usability_score=reference.usability_score,
        thumbnail_url=reference.thumbnail_url,
        notes=reference.relevance_note,
    )


async def verify_viewpoints(
    references: list[VideoReference],
    dataset: DatasetManifest,
    *,
    wanted: Viewpoint | None,
    llm: Any | None = None,
    mode: str | None = None,
) -> list[VideoReference]:
    """Look at the candidates' frames, at search time, and drop the wrong ones.

    Everything in :func:`curate_references` reads words *about* a video — a
    title, a description, tags. That is why a search for first-person cooking
    comes back with "10 Camera Angles and Shots for Cooking Videos": nothing in
    the metadata says the camera is on a tripod.

    Doing this here rather than at collection time is the difference between a
    candidate list you can trust and one where queueing four clips means
    watching all four get skipped. It costs about $0.002 a candidate.

    Only a confident, opposite reading drops anything. Abstention and weak
    readings stay, with whatever the frames did say recorded on the reference,
    because three stills are weaker evidence than the caption pass that runs
    after indexing.

    Returns:
        The references that survived, in the order they came in.
    """
    from video_searching_agent.curation.frame_viewpoint import check_many

    resolved = mode or _configured_sight_mode()
    if resolved == "off" or not references or wanted is None:
        return references

    if llm is None:
        try:
            from video_searching_agent.api.llm import get_llm_client

            llm = get_llm_client()
        except Exception as exc:  # noqa: BLE001 - looking is optional
            logger.info("no model for the search-time frame check: %s", exc)
            return references

    candidates = [
        {
            "video_id": youtube_video_id(ref.url or ""),
            "url": ref.url,
            # Needed to refuse a watch that would cost a third of a dollar.
            "duration_seconds": ref.duration_seconds,
        }
        for ref in references
    ]
    verdicts = await check_many(llm, candidates, mode=resolved)

    kept: list[VideoReference] = []
    spent = 0.0
    for reference, seen in zip(references, verdicts, strict=True):
        spent += seen.cost_usd or 0.0
        if not seen.looked:
            kept.append(reference)
            continue
        if seen.contradicts(wanted):
            dataset.excluded_clips += 1
            reason = f"frames show {seen.viewpoint.value} footage"
            dataset.exclusion_reasons[reason] = dataset.exclusion_reasons.get(reason, 0) + 1
            continue
        if seen.viewpoint is not Viewpoint.UNKNOWN:
            # A checked match is worth more than a guess from a title, so the
            # reading replaces the metadata one rather than averaging with it.
            reference.viewpoint = seen.viewpoint
            reference.viewpoint_confidence = max(
                reference.viewpoint_confidence or 0.0, seen.confidence
            )
            evidence = f"frames: {seen.why}" if seen.why else "frames checked"
            if evidence not in (reference.viewpoint_evidence or []):
                reference.viewpoint_evidence = [*(reference.viewpoint_evidence or []), evidence]
        kept.append(reference)

    dataset.clips = [clip for clip in dataset.clips if clip.url in {r.url for r in kept}]
    dataset.recompute_totals()
    logger.info(
        "frame check: %d of %d candidates kept, $%.4f",
        len(kept),
        len(references),
        spent,
    )
    return kept


def _configured_sight_mode() -> str:
    """How hard to look at a candidate before showing it."""

    try:
        from video_searching_agent.config.settings import get_settings

        return get_settings().viewpoint_check
    except Exception:  # noqa: BLE001 - settings are optional here
        return "frames"
