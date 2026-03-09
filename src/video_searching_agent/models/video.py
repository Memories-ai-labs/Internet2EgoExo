"""Video and creator data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class Platform(str, Enum):
    """Supported video platforms."""

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    OTHER = "other"


class VideoMetrics(BaseModel):
    """Engagement metrics for a video."""

    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = Field(None, description="Bookmarks/favorites/saves count")
    impressions: int | None = Field(None, description="Total impressions (Twitter)")
    reposts: int | None = Field(None, description="Reposts count (TikTok/Instagram)")
    quote_tweets: int | None = Field(None, description="Quote tweets count (Twitter)")
    engagement_rate: float | None = Field(
        None,
        description="Engagement rate as percentage, calculated per platform formula",
    )

    def calculate_engagement_rate(
        self,
        platform: Optional["Platform"] = None,
        creator_followers: int | None = None,
    ) -> float | None:
        """
        Calculate engagement rate using platform-specific formulas per PRD.

        Formulas:
        - YouTube: (likes + comments) / views * 100
        - TikTok: (likes + comments + shares + saves) / views * 100
        - Instagram Reels/Video: (likes + comments + saves) / views * 100
        - Instagram Image: (likes + comments + saves) / followers * 100
        - Twitter: (likes + replies + retweets + quote_tweets) / impressions * 100

        Args:
            platform: The platform to use for formula selection
            creator_followers: Creator's follower count (for Instagram image formula)

        Returns:
            Engagement rate as percentage, or None if insufficient data
        """
        if platform == Platform.YOUTUBE:
            # YouTube: (likes + comments) / views
            if self.views and self.views > 0 and self.likes is not None:
                interactions = (self.likes or 0) + (self.comments or 0)
                return round((interactions / self.views) * 100, 2)

        elif platform == Platform.TIKTOK:
            # TikTok: (likes + comments + shares + saves) / views
            if self.views and self.views > 0:
                interactions = (
                    (self.likes or 0)
                    + (self.comments or 0)
                    + (self.shares or 0)
                    + (self.saves or 0)
                )
                return round((interactions / self.views) * 100, 2)

        elif platform == Platform.INSTAGRAM:
            # Instagram Reels/Video: (likes + comments + saves) / views
            # Instagram Image: (likes + comments + saves) / followers
            interactions = (self.likes or 0) + (self.comments or 0) + (self.saves or 0)
            if self.views and self.views > 0:
                return round((interactions / self.views) * 100, 2)
            elif creator_followers and creator_followers > 0:
                return round((interactions / creator_followers) * 100, 2)

        elif platform == Platform.TWITTER:
            # Twitter: (likes + replies + retweets + quote_tweets) / impressions
            base = self.impressions if self.impressions and self.impressions > 0 else self.views
            if base and base > 0:
                interactions = (
                    (self.likes or 0)
                    + (self.comments or 0)  # replies
                    + (self.shares or 0)  # retweets
                    + (self.quote_tweets or 0)
                )
                return round((interactions / base) * 100, 2)

        else:
            # Default/fallback: simple (likes + comments) / views formula
            if self.views and self.views > 0 and self.likes is not None:
                interactions = (self.likes or 0) + (self.comments or 0)
                return round((interactions / self.views) * 100, 2)

        return None


class Creator(BaseModel):
    """Content creator information."""

    username: str
    display_name: str | None = None
    platform: Platform
    profile_url: HttpUrl | None = None
    followers: int | None = None
    following: int | None = None
    avatar_url: HttpUrl | None = None
    region: str | None = None
    description: str | None = None
    verified: bool = False

    # Aggregate metrics
    total_videos: int | None = None
    avg_views: int | None = None
    avg_likes: int | None = None
    avg_comments: int | None = None


class Video(BaseModel):
    """Unified video model across all platforms."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Internal unique ID")
    platform: Platform
    platform_id: str = Field(..., description="Video ID on the source platform")
    url: HttpUrl
    title: str | None = None
    description: str | None = None
    thumbnail_url: HttpUrl | None = None
    duration_seconds: int | None = None
    published_at: datetime | None = None

    # Creator info
    creator: Creator | None = None

    # Engagement metrics
    metrics: VideoMetrics | None = None

    # Content metadata
    hashtags: list[str] = Field(default_factory=list)
    category: str | None = None
    language: str | None = None

    # Memories.ai integration
    memories_video_no: str | None = Field(
        None,
        description="Video number in Memories.ai if uploaded",
    )
    memories_status: str | None = Field(
        None,
        description="Processing status in Memories.ai",
    )

    # Search relevance
    relevance_score: float | None = Field(None, ge=0, le=1)
    source_query: str | None = Field(None, description="Query that found this video")

    @property
    def platform_url(self) -> str:
        """Get the platform-specific URL for the video."""
        return str(self.url)

    @property
    def formatted_duration(self) -> str | None:
        """Format duration as MM:SS or HH:MM:SS."""
        if self.duration_seconds is None:
            return None
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class VideoCollection(BaseModel):
    """Collection of videos with metadata."""

    videos: list[Video] = Field(default_factory=list)
    total_count: int = 0
    query: str | None = None
    platform_filter: Platform | None = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    def add_video(self, video: Video) -> None:
        """Add a video to the collection."""
        self.videos.append(video)
        self.total_count = len(self.videos)

    def deduplicate(self) -> "VideoCollection":
        """Remove duplicate videos based on platform_id and platform."""
        seen: set[tuple[str, Platform]] = set()
        unique_videos: list[Video] = []
        for video in self.videos:
            key = (video.platform_id, video.platform)
            if key not in seen:
                seen.add(key)
                unique_videos.append(video)
        return VideoCollection(
            videos=unique_videos,
            total_count=len(unique_videos),
            query=self.query,
            platform_filter=self.platform_filter,
            fetched_at=self.fetched_at,
        )

    def sort_by_relevance(self) -> "VideoCollection":
        """Sort videos by relevance score (highest first)."""
        sorted_videos = sorted(
            self.videos,
            key=lambda v: v.relevance_score or 0,
            reverse=True,
        )
        return VideoCollection(
            videos=sorted_videos,
            total_count=self.total_count,
            query=self.query,
            platform_filter=self.platform_filter,
            fetched_at=self.fetched_at,
        )

    def sort_by_views(self) -> "VideoCollection":
        """Sort videos by view count (highest first)."""
        sorted_videos = sorted(
            self.videos,
            key=lambda v: (v.metrics.views if v.metrics and v.metrics.views else 0),
            reverse=True,
        )
        return VideoCollection(
            videos=sorted_videos,
            total_count=self.total_count,
            query=self.query,
            platform_filter=self.platform_filter,
            fetched_at=self.fetched_at,
        )
