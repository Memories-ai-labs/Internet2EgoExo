"""Tests for video sorting utilities."""

from datetime import datetime

from video_searching_agent.models.video import Platform, Video, VideoMetrics
from video_searching_agent.tools.sorting import sort_videos_by_popularity


def create_video(
    video_id: str,
    views: int | None = None,
    likes: int | None = None,
    engagement_rate: float | None = None,
    published_at: datetime | None = None,
) -> Video:
    """Create a test video with specified metrics."""
    metrics = VideoMetrics(
        views=views,
        likes=likes,
        engagement_rate=engagement_rate,
    )
    return Video(
        platform=Platform.YOUTUBE,
        platform_id=video_id,
        url=f"https://youtube.com/watch?v={video_id}",
        title=f"Test Video {video_id}",
        metrics=metrics,
        published_at=published_at,
    )


class TestSortByViews:
    """Tests for sorting by view count."""

    def test_sort_by_views_descending(self):
        """Test videos are sorted by views in descending order."""
        videos = [
            create_video("a", views=100),
            create_video("b", views=1000),
            create_video("c", views=500),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")

        assert sorted_videos[0].platform_id == "b"  # 1000 views
        assert sorted_videos[1].platform_id == "c"  # 500 views
        assert sorted_videos[2].platform_id == "a"  # 100 views

    def test_sort_by_views_with_likes_tiebreaker(self):
        """Test likes are used as tiebreaker for equal views."""
        videos = [
            create_video("a", views=1000, likes=50),
            create_video("b", views=1000, likes=100),
            create_video("c", views=1000, likes=75),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")

        assert sorted_videos[0].platform_id == "b"  # 100 likes
        assert sorted_videos[1].platform_id == "c"  # 75 likes
        assert sorted_videos[2].platform_id == "a"  # 50 likes

    def test_sort_by_views_with_none(self):
        """Test handling of None view counts."""
        videos = [
            create_video("a", views=None),
            create_video("b", views=1000),
            create_video("c", views=500),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")

        # Video with None views should be at the end
        assert sorted_videos[0].platform_id == "b"
        assert sorted_videos[1].platform_id == "c"
        assert sorted_videos[2].platform_id == "a"


class TestSortByLikes:
    """Tests for sorting by like count."""

    def test_sort_by_likes_descending(self):
        """Test videos are sorted by likes in descending order."""
        videos = [
            create_video("a", likes=50),
            create_video("b", likes=200),
            create_video("c", likes=100),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="likes")

        assert sorted_videos[0].platform_id == "b"  # 200 likes
        assert sorted_videos[1].platform_id == "c"  # 100 likes
        assert sorted_videos[2].platform_id == "a"  # 50 likes

    def test_sort_by_likes_with_none(self):
        """Test handling of None like counts."""
        videos = [
            create_video("a", likes=None),
            create_video("b", likes=100),
            create_video("c", likes=50),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="likes")

        # Video with None likes should be at the end
        assert sorted_videos[0].platform_id == "b"
        assert sorted_videos[1].platform_id == "c"
        assert sorted_videos[2].platform_id == "a"


class TestSortByEngagement:
    """Tests for sorting by engagement rate."""

    def test_sort_by_engagement_descending(self):
        """Test videos are sorted by engagement rate in descending order."""
        videos = [
            create_video("a", engagement_rate=0.05),
            create_video("b", engagement_rate=0.15),
            create_video("c", engagement_rate=0.10),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="engagement")

        assert sorted_videos[0].platform_id == "b"  # 15% engagement
        assert sorted_videos[1].platform_id == "c"  # 10% engagement
        assert sorted_videos[2].platform_id == "a"  # 5% engagement

    def test_sort_by_engagement_with_none(self):
        """Test handling of None engagement rates."""
        videos = [
            create_video("a", engagement_rate=None),
            create_video("b", engagement_rate=0.10),
            create_video("c", engagement_rate=0.05),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="engagement")

        # Video with None engagement should be at the end
        assert sorted_videos[0].platform_id == "b"
        assert sorted_videos[1].platform_id == "c"
        assert sorted_videos[2].platform_id == "a"


class TestSortByRecent:
    """Tests for sorting by publish date (most recent first)."""

    def test_sort_by_recent_descending(self):
        """Test videos are sorted by date with newest first."""
        videos = [
            create_video("a", published_at=datetime(2024, 1, 1)),
            create_video("b", published_at=datetime(2024, 3, 1)),
            create_video("c", published_at=datetime(2024, 2, 1)),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="recent")

        assert sorted_videos[0].platform_id == "b"  # March 2024
        assert sorted_videos[1].platform_id == "c"  # February 2024
        assert sorted_videos[2].platform_id == "a"  # January 2024

    def test_sort_by_recent_with_none(self):
        """Test handling of None publish dates."""
        videos = [
            create_video("a", published_at=None),
            create_video("b", published_at=datetime(2024, 3, 1)),
            create_video("c", published_at=datetime(2024, 2, 1)),
        ]

        sorted_videos = sort_videos_by_popularity(videos, sort_by="recent")

        # Video with None date should be at the end
        assert sorted_videos[0].platform_id == "b"
        assert sorted_videos[1].platform_id == "c"
        assert sorted_videos[2].platform_id == "a"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_list(self):
        """Test sorting an empty list returns empty list."""
        videos: list[Video] = []
        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")
        assert sorted_videos == []

    def test_single_video(self):
        """Test sorting a single video returns the same video."""
        videos = [create_video("a", views=100)]
        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")
        assert len(sorted_videos) == 1
        assert sorted_videos[0].platform_id == "a"

    def test_all_none_metrics(self):
        """Test handling when all videos have None metrics."""
        videos = [
            create_video("a", views=None),
            create_video("b", views=None),
            create_video("c", views=None),
        ]

        # Should not raise an exception
        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")
        assert len(sorted_videos) == 3

    def test_default_sort_is_views(self):
        """Test default sort order is by views."""
        videos = [
            create_video("a", views=100),
            create_video("b", views=500),
        ]

        # Default sort_by is "views"
        sorted_videos = sort_videos_by_popularity(videos)
        assert sorted_videos[0].platform_id == "b"

    def test_unknown_sort_defaults_to_views(self):
        """Test unknown sort_by values default to views."""
        videos = [
            create_video("a", views=100),
            create_video("b", views=500),
        ]

        # Unknown sort_by should default to views
        sorted_videos = sort_videos_by_popularity(videos, sort_by="unknown")
        assert sorted_videos[0].platform_id == "b"

    def test_video_without_metrics(self):
        """Test handling videos with no metrics object."""
        video = Video(
            platform=Platform.YOUTUBE,
            platform_id="a",
            url="https://youtube.com/watch?v=a",
            title="Test",
            metrics=None,  # No metrics
        )
        videos = [
            video,
            create_video("b", views=100),
        ]

        # Should not raise an exception
        sorted_videos = sort_videos_by_popularity(videos, sort_by="views")
        assert len(sorted_videos) == 2
        # Video with actual views should be first
        assert sorted_videos[0].platform_id == "b"
