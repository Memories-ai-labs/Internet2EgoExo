"""Secondary metrics calculations for video analytics."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from video_searching_agent.models.video import Platform, Video


class MetricsCalculator:
    """Calculator for secondary and aggregate metrics per PRD requirements."""

    @staticmethod
    def calculate_average_views(videos: list["Video"]) -> float:
        """
        Calculate average views across a list of videos.

        Args:
            videos: List of Video objects

        Returns:
            Average view count, or 0 if no valid data
        """
        valid_views = [
            v.metrics.views for v in videos if v.metrics and v.metrics.views is not None
        ]
        if not valid_views:
            return 0.0
        return round(sum(valid_views) / len(valid_views), 2)

    @staticmethod
    def calculate_average_likes(videos: list["Video"]) -> float:
        """
        Calculate average likes across a list of videos.

        Args:
            videos: List of Video objects

        Returns:
            Average like count, or 0 if no valid data
        """
        valid_likes = [
            v.metrics.likes for v in videos if v.metrics and v.metrics.likes is not None
        ]
        if not valid_likes:
            return 0.0
        return round(sum(valid_likes) / len(valid_likes), 2)

    @staticmethod
    def calculate_average_comments(videos: list["Video"]) -> float:
        """
        Calculate average comments across a list of videos.

        Args:
            videos: List of Video objects

        Returns:
            Average comment count, or 0 if no valid data
        """
        valid_comments = [
            v.metrics.comments
            for v in videos
            if v.metrics and v.metrics.comments is not None
        ]
        if not valid_comments:
            return 0.0
        return round(sum(valid_comments) / len(valid_comments), 2)

    @staticmethod
    def calculate_average_engagement_rate(
        videos: list["Video"], platform: "Platform | None" = None
    ) -> float:
        """
        Calculate average engagement rate across videos.

        Args:
            videos: List of Video objects
            platform: Platform for engagement rate formula

        Returns:
            Average engagement rate as percentage, or 0 if no valid data
        """
        engagement_rates = []
        for video in videos:
            if video.metrics:
                rate = video.metrics.calculate_engagement_rate(
                    platform=platform or video.platform,
                    creator_followers=(
                        video.creator.followers if video.creator else None
                    ),
                )
                if rate is not None:
                    engagement_rates.append(rate)

        if not engagement_rates:
            return 0.0
        return round(sum(engagement_rates) / len(engagement_rates), 2)

    @staticmethod
    def calculate_growth_rate(current: int, previous: int) -> float:
        """
        Calculate percentage growth rate between two values.

        Args:
            current: Current value
            previous: Previous value

        Returns:
            Growth rate as percentage (e.g., 50.0 for 50% growth)
        """
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    @staticmethod
    def calculate_view_velocity(video: "Video", hours: int = 24) -> float:
        """
        Calculate views per hour since publication.

        Args:
            video: Video object
            hours: Time window in hours (default 24)

        Returns:
            Views per hour, or 0 if insufficient data
        """
        if not video.metrics or not video.metrics.views:
            return 0.0
        if not video.published_at:
            return 0.0

        # Normalize published_at to be timezone-aware
        published_at = video.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)

        time_since_publish = datetime.now(UTC) - published_at
        hours_since_publish = max(time_since_publish.total_seconds() / 3600, 1)

        # Cap at the specified time window
        effective_hours = min(hours_since_publish, hours)
        return round(video.metrics.views / effective_hours, 2)

    @staticmethod
    def calculate_viral_score(video: "Video") -> float:
        """
        Calculate a viral score based on view velocity and engagement rate.

        The score combines:
        - View velocity (views per hour in first 24h)
        - Engagement rate (platform-specific formula)

        Score formula: (velocity_score * 0.6) + (engagement_score * 0.4)
        Where velocity_score = min(velocity / 10000, 1.0) * 100
        And engagement_score = min(engagement_rate, 20) * 5

        Args:
            video: Video object

        Returns:
            Viral score from 0-100
        """
        velocity = MetricsCalculator.calculate_view_velocity(video)
        velocity_score = min(velocity / 10000, 1.0) * 100

        engagement_rate = 0.0
        if video.metrics:
            rate = video.metrics.calculate_engagement_rate(
                platform=video.platform,
                creator_followers=video.creator.followers if video.creator else None,
            )
            engagement_rate = rate if rate is not None else 0.0

        # Cap engagement contribution at 20% rate
        engagement_score = min(engagement_rate, 20) * 5

        viral_score = (velocity_score * 0.6) + (engagement_score * 0.4)
        return round(min(viral_score, 100), 2)

    @staticmethod
    def calculate_engagement_trend(
        videos: list["Video"], time_period_hours: int = 168
    ) -> dict[str, str | float]:
        """
        Calculate engagement trend over a time period.

        Splits videos into older half vs newer half and compares engagement.

        Args:
            videos: List of Video objects with published_at dates
            time_period_hours: Time window (default 168h = 7 days)

        Returns:
            Dict with trend analysis:
            {
                "trend": "increasing" | "decreasing" | "stable",
                "change_percent": float,
                "older_avg_engagement": float,
                "newer_avg_engagement": float,
            }
        """
        # Filter to videos with valid dates within time period
        cutoff = datetime.now(UTC) - timedelta(hours=time_period_hours)

        def normalize_dt(dt: datetime) -> datetime:
            """Normalize datetime to be timezone-aware."""
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

        dated_videos = [
            v for v in videos if v.published_at and normalize_dt(v.published_at) >= cutoff
        ]

        if len(dated_videos) < 2:
            return {
                "trend": "stable",
                "change_percent": 0.0,
                "older_avg_engagement": 0.0,
                "newer_avg_engagement": 0.0,
            }

        # Sort by date and split
        sorted_videos = sorted(
            dated_videos,
            key=lambda v: v.published_at or datetime.min.replace(tzinfo=UTC),
        )
        midpoint = len(sorted_videos) // 2
        older_videos = sorted_videos[:midpoint]
        newer_videos = sorted_videos[midpoint:]

        older_avg = MetricsCalculator.calculate_average_engagement_rate(older_videos)
        newer_avg = MetricsCalculator.calculate_average_engagement_rate(newer_videos)

        change = MetricsCalculator.calculate_growth_rate(
            int(newer_avg * 100), int(older_avg * 100)
        )

        if change > 10:
            trend = "increasing"
        elif change < -10:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change_percent": change,
            "older_avg_engagement": older_avg,
            "newer_avg_engagement": newer_avg,
        }

    @staticmethod
    def rank_by_fastest_growth(videos: list["Video"]) -> list["Video"]:
        """
        Rank videos by view velocity (fastest growing views).

        Args:
            videos: List of Video objects

        Returns:
            Videos sorted by view velocity (highest first)
        """
        return sorted(
            videos,
            key=lambda v: MetricsCalculator.calculate_view_velocity(v),
            reverse=True,
        )

    @staticmethod
    def rank_by_engagement(
        videos: list["Video"], platform: "Platform | None" = None
    ) -> list["Video"]:
        """
        Rank videos by engagement rate.

        Args:
            videos: List of Video objects
            platform: Platform for engagement rate formula

        Returns:
            Videos sorted by engagement rate (highest first)
        """

        def get_engagement(v: "Video") -> float:
            if not v.metrics:
                return 0.0
            rate = v.metrics.calculate_engagement_rate(
                platform=platform or v.platform,
                creator_followers=v.creator.followers if v.creator else None,
            )
            return rate if rate is not None else 0.0

        return sorted(videos, key=get_engagement, reverse=True)

    @staticmethod
    def rank_by_viral_score(videos: list["Video"]) -> list["Video"]:
        """
        Rank videos by viral score.

        Args:
            videos: List of Video objects

        Returns:
            Videos sorted by viral score (highest first)
        """
        return sorted(
            videos,
            key=lambda v: MetricsCalculator.calculate_viral_score(v),
            reverse=True,
        )

    @staticmethod
    def get_summary_stats(videos: list["Video"]) -> dict[str, Any]:
        """
        Get summary statistics for a collection of videos.

        Args:
            videos: List of Video objects

        Returns:
            Dict with summary statistics
        """
        if not videos:
            return {
                "total_videos": 0,
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "avg_views": 0.0,
                "avg_likes": 0.0,
                "avg_comments": 0.0,
                "avg_engagement_rate": 0.0,
                "top_performer_views": None,
                "top_performer_engagement": None,
            }

        total_views = sum(
            v.metrics.views for v in videos if v.metrics and v.metrics.views
        )
        total_likes = sum(
            v.metrics.likes for v in videos if v.metrics and v.metrics.likes
        )
        total_comments = sum(
            v.metrics.comments for v in videos if v.metrics and v.metrics.comments
        )

        top_by_views = max(
            videos,
            key=lambda v: v.metrics.views if v.metrics and v.metrics.views else 0,
            default=None,
        )
        top_by_engagement = (
            MetricsCalculator.rank_by_engagement(videos)[0] if videos else None
        )

        return {
            "total_videos": len(videos),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_views": MetricsCalculator.calculate_average_views(videos),
            "avg_likes": MetricsCalculator.calculate_average_likes(videos),
            "avg_comments": MetricsCalculator.calculate_average_comments(videos),
            "avg_engagement_rate": MetricsCalculator.calculate_average_engagement_rate(
                videos
            ),
            "top_performer_views": top_by_views.platform_id if top_by_views else None,
            "top_performer_engagement": (
                top_by_engagement.platform_id if top_by_engagement else None
            ),
        }
