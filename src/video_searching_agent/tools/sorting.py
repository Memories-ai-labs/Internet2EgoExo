"""Sorting utilities for video search results.

Provides functions to sort videos by popularity metrics since most social
platform APIs don't support native popularity sorting.
"""

from datetime import UTC, datetime

from video_searching_agent.curation.viewpoint import Viewpoint
from video_searching_agent.models.video import Video


def sort_videos_by_popularity(
    videos: list[Video],
    sort_by: str = "views",
) -> list[Video]:
    """Sort videos by engagement metric.

    Args:
        videos: List of Video objects to sort.
        sort_by: Sorting criteria - one of:
            - "views": Sort by view count (default), with likes as tiebreaker
            - "likes": Sort by like count
            - "engagement": Sort by engagement rate
            - "recent": Sort by publish date (newest first)

    Returns:
        Sorted list of Video objects (highest/newest first).
    """
    if not videos:
        return videos

    if sort_by == "recent":
        def normalize_datetime(dt: datetime | None) -> datetime:
            """Normalize datetime to be timezone-aware for comparison."""
            if dt is None:
                return datetime.min.replace(tzinfo=UTC)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt

        return sorted(
            videos,
            key=lambda v: normalize_datetime(v.published_at),
            reverse=True,
        )

    if sort_by == "engagement":
        return sorted(
            videos,
            key=lambda v: (
                v.metrics.engagement_rate if v.metrics and v.metrics.engagement_rate else 0
            ),
            reverse=True,
        )

    if sort_by == "likes":
        return sorted(
            videos,
            key=lambda v: (v.metrics.likes if v.metrics and v.metrics.likes else 0),
            reverse=True,
        )

    # Default: views (with likes as tiebreaker)
    return sorted(
        videos,
        key=lambda v: (
            v.metrics.views if v.metrics and v.metrics.views else 0,
            v.metrics.likes if v.metrics and v.metrics.likes else 0,
        ),
        reverse=True,
    )


def rank_videos_for_training_data(
    videos: list["Video"],
    wanted_viewpoint: "Viewpoint | None" = None,
    min_duration_seconds: int | None = None,
    license_filter: str = "any",
) -> tuple[list["Video"], list[tuple["Video", str]]]:
    """Rank candidates by training-data usability and drop unusable ones.

    Every kept video carries its verdict on `relevance_score` (the usability
    score) so downstream reference extraction can surface it.

    Args:
        videos: Candidates to rank.
        wanted_viewpoint: Required viewpoint, or None for any.
        min_duration_seconds: Hard minimum clip length.
        license_filter: "any" or "reusable".

    Returns:
        (kept videos, ranked best-first; dropped [(video, reason)] pairs).
    """
    from video_searching_agent.curation.scoring import score_candidate
    from video_searching_agent.curation.viewpoint import classify_viewpoint

    kept: list[tuple[float, Video]] = []
    dropped: list[tuple[Video, str]] = []

    for video in videos:
        verdict = classify_viewpoint(
            title=video.title,
            description=video.description,
            tags=video.hashtags,
        )
        score = score_candidate(
            verdict,
            video.duration_seconds,
            video.license,
            wanted_viewpoint=wanted_viewpoint,
            min_duration_seconds=min_duration_seconds,
            license_filter=license_filter,
        )
        if not score.usable:
            dropped.append((video, score.excluded_reason or "excluded"))
            continue

        video.relevance_score = min(score.total, 1.0)
        kept.append((score.total, video))

    kept.sort(key=lambda pair: pair[0], reverse=True)
    return [video for _, video in kept], dropped
