"""Sorting utilities for video search results.

Provides functions to sort videos by popularity metrics since most social
platform APIs don't support native popularity sorting.
"""

from datetime import UTC, datetime

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
