"""TikTok tools using Apify for reliable scraping.

Apify actors provide professional-grade scraping with anti-bot handling and proxies.
This replaces the fragile API + browser fallback chain with a single reliable source.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from video_searching_agent.api.apify_client import ApifyClient
from video_searching_agent.models.video import Creator, Platform, Video, VideoMetrics
from video_searching_agent.tools.base import BaseTool, ParseStats, ToolResult
from video_searching_agent.tools.sorting import sort_videos_by_popularity

logger = logging.getLogger(__name__)


class TikTokApifySearchTool(BaseTool):
    """TikTok search using Apify actor for reliable results.

    Uses the clockworks/tiktok-scraper actor which provides:
    - 600 posts/sec throughput
    - 98% success rate
    - Anti-bot handling and proxy rotation
    """

    def __init__(self) -> None:
        """Initialize TikTok Apify search tool."""
        self._client: ApifyClient | None = None

    @property
    def client(self) -> ApifyClient:
        """Lazy-load Apify client."""
        if self._client is None:
            self._client = ApifyClient()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Apify API key is configured."""
        from video_searching_agent.config.settings import get_settings
        settings = get_settings()
        if not settings.apify_api_token:
            return False, "APIFY_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "tiktok_search"

    @property
    def description(self) -> str:
        return """Search TikTok for videos using Apify scraper.

Use this tool for TikTok-specific queries including:
- Trending videos by topic or hashtag
- Creator content discovery
- Challenge and trend discovery

Returns video data including views, likes, comments, shares, creator info, and hashtags.

Example queries:
- Search for "#cooking" to find cooking-related videos
- Search for "@charlidamelio" to find a creator's content
- Search for "dance trends" to find trending dance content"""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keyword, hashtag with #, or @username)",
                },
                "search_type": {
                    "type": "string",
                    "enum": ["keyword", "hashtag", "user"],
                    "description": (
                        "Type of search: 'keyword' for general search, "
                        "'hashtag' for hashtag-specific, 'user' for creator videos"
                    ),
                    "default": "keyword",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum videos to return (1-50)",
                    "default": 20,
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["views", "likes", "engagement", "recent"],
                    "description": "Sort by: views (default), likes, engagement, or recent",
                    "default": "views",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute TikTok search via Apify.

        Args:
            query: Search query.
            search_type: Type of search (keyword, hashtag, user).
            max_results: Maximum results to return.
            sort_by: How to sort results (views, likes, engagement, recent).

        Returns:
            ToolResult with list of videos.
        """
        query = kwargs.get("query", "")
        search_type = kwargs.get("search_type", "keyword")
        max_results = min(kwargs.get("max_results", 20), 50)
        sort_by = kwargs.get("sort_by", "views")

        if not query:
            return ToolResult.fail("Query is required")

        # Over-fetch to improve quality after sorting (2x requested, capped at 100)
        fetch_count = min(max_results * 2, 100)

        try:
            # Determine search parameters based on query format
            if query.startswith("#") or search_type == "hashtag":
                hashtag = query.lstrip("#")
                raw_results = await self.client.scrape_tiktok(
                    hashtag=hashtag, max_results=fetch_count
                )
                effective_search_type = "hashtag"
            elif query.startswith("@") or search_type == "user":
                username = query.lstrip("@")
                raw_results = await self.client.scrape_tiktok(
                    username=username, max_results=fetch_count
                )
                effective_search_type = "user"
            else:
                raw_results = await self.client.scrape_tiktok(
                    query=query, max_results=fetch_count
                )
                effective_search_type = "keyword"

            # Parse results into Video models
            videos, parse_stats = self._parse_apify_results(raw_results, query)

            # Log parse stats if there were failures
            if parse_stats.has_failures():
                logger.warning(
                    f"TikTok parse issues: {parse_stats.summary()}"
                )

            if not videos:
                return ToolResult.no_results(
                    f"No TikTok videos found for query: {query}",
                    parse_stats=parse_stats,
                )

            # Sort by popularity and trim to requested count
            videos = sort_videos_by_popularity(videos, sort_by=sort_by)
            videos = videos[:max_results]

            return ToolResult.ok(
                {
                    "videos": [v.model_dump(mode="json") for v in videos],
                    "total_results": len(videos),
                    "query": query,
                    "platform": "tiktok",
                    "search_type": effective_search_type,
                    "sort_by": sort_by,
                    "method": "apify",
                },
                parse_stats=parse_stats,
            )

        except ValueError as e:
            return ToolResult.fail(f"TikTok search configuration error: {e}")
        except Exception as e:
            logger.error(f"TikTok Apify search error: {e}")
            return ToolResult.fail(f"TikTok search error: {e}")

    def _parse_apify_results(
        self, raw_results: list[dict[str, Any]], query: str
    ) -> tuple[list[Video], ParseStats]:
        """Parse Apify actor results into Video models.

        Args:
            raw_results: Raw data from Apify actor.
            query: Original search query.

        Returns:
            Tuple of (list of Video models, ParseStats with parse statistics).
        """
        videos: list[Video] = []
        parse_stats = ParseStats()

        for item in raw_results:
            try:
                # Extract creator info
                author_data = item.get("authorMeta") or item.get("author") or {}
                creator_username = (
                    author_data.get("name")
                    or author_data.get("uniqueId")
                    or item.get("authorMeta", {}).get("name")
                    or "unknown"
                )

                creator = Creator(
                    username=creator_username,
                    display_name=author_data.get("nickName") or author_data.get("nickname"),
                    platform=Platform.TIKTOK,
                    profile_url=f"https://www.tiktok.com/@{creator_username}",  # type: ignore[arg-type]
                    followers=author_data.get("fans") or author_data.get("followerCount"),
                    avatar_url=author_data.get("avatar"),
                    verified=author_data.get("verified", False),
                )

                # Extract metrics
                stats = item.get("stats") or item.get("statsV2") or {}
                metrics = VideoMetrics(
                    views=self._safe_int(stats.get("playCount") or item.get("playCount")),
                    likes=self._safe_int(stats.get("diggCount") or item.get("diggCount")),
                    comments=self._safe_int(stats.get("commentCount") or item.get("commentCount")),
                    shares=self._safe_int(stats.get("shareCount") or item.get("shareCount")),
                    saves=self._safe_int(stats.get("collectCount") or item.get("collectCount")),
                )
                if metrics.views:
                    metrics.engagement_rate = metrics.calculate_engagement_rate(
                        platform=Platform.TIKTOK
                    )

                # Extract video info
                platform_id = str(item.get("id") or item.get("videoId") or "")
                web_url = item.get("webVideoUrl") or item.get("url")
                if not web_url and creator_username and platform_id:
                    web_url = f"https://www.tiktok.com/@{creator_username}/video/{platform_id}"

                # Extract hashtags
                hashtags = []
                challenges = item.get("challenges") or item.get("hashtags") or []
                for challenge in challenges:
                    if isinstance(challenge, dict):
                        hashtags.append(challenge.get("title") or challenge.get("name", ""))
                    elif isinstance(challenge, str):
                        hashtags.append(challenge)
                hashtags = [h for h in hashtags if h]

                # Parse creation time
                published_at = None
                create_time = item.get("createTime") or item.get("createTimeISO")
                if create_time:
                    if isinstance(create_time, int):
                        published_at = datetime.fromtimestamp(create_time, tz=UTC)
                    elif isinstance(create_time, str):
                        try:
                            published_at = datetime.fromisoformat(
                                create_time.replace("Z", "+00:00")
                            )
                        except ValueError:
                            pass

                video = Video(
                    platform=Platform.TIKTOK,
                    platform_id=platform_id,
                    url=web_url or f"https://www.tiktok.com/video/{platform_id}",  # type: ignore[arg-type]
                    title=item.get("desc") or item.get("text") or item.get("title"),
                    description=item.get("desc") or item.get("text"),
                    thumbnail_url=item.get("cover") or item.get("coverUrl"),
                    duration_seconds=self._safe_int(
                        item.get("duration") or item.get("videoMeta", {}).get("duration")
                    ),
                    published_at=published_at,
                    creator=creator,
                    metrics=metrics,
                    hashtags=hashtags,
                    source_query=query,
                )
                videos.append(video)
                parse_stats.add_success()

            except Exception as e:
                parse_stats.add_failure(str(e))
                logger.warning(f"Failed to parse TikTok video: {e}")
                continue

        return videos, parse_stats

    def _safe_int(self, value: Any) -> int | None:
        """Safely convert a value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


class TikTokApifyCreatorTool(BaseTool):
    """TikTok creator info using Apify actor."""

    def __init__(self) -> None:
        """Initialize TikTok Apify creator tool."""
        self._client: ApifyClient | None = None

    @property
    def client(self) -> ApifyClient:
        """Lazy-load Apify client."""
        if self._client is None:
            self._client = ApifyClient()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Apify API key is configured."""
        from video_searching_agent.config.settings import get_settings
        settings = get_settings()
        if not settings.apify_api_token:
            return False, "APIFY_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "tiktok_creator_info"

    @property
    def description(self) -> str:
        return """Get TikTok creator profile information using Apify.

Use this tool when you need:
- Creator statistics (followers, following, total likes)
- Profile information and bio
- Recent video content from a specific creator
- Verification status

Returns profile data and recent videos."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "TikTok username (without @)",
                },
                "include_recent_videos": {
                    "type": "boolean",
                    "description": "Whether to include recent video data",
                    "default": True,
                },
                "recent_videos_count": {
                    "type": "integer",
                    "description": "Number of recent videos to include (1-30)",
                    "default": 10,
                },
            },
            "required": ["username"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Get TikTok creator profile via Apify.

        Args:
            username: Creator's username.
            include_recent_videos: Whether to get recent videos.
            recent_videos_count: Number of recent videos.

        Returns:
            ToolResult with creator profile and videos.
        """
        username = kwargs.get("username", "").lstrip("@")
        include_recent_videos = kwargs.get("include_recent_videos", True)
        recent_videos_count = min(kwargs.get("recent_videos_count", 10), 30)

        if not username:
            return ToolResult.fail("Username is required")

        try:
            # Fetch creator profile and videos
            raw_results = await self.client.scrape_tiktok(
                username=username,
                max_results=recent_videos_count if include_recent_videos else 1,
            )

            if not raw_results:
                return ToolResult.fail(f"Creator @{username} not found")

            # Extract creator info from first result
            first_item = raw_results[0]
            author_data = first_item.get("authorMeta") or first_item.get("author") or {}

            creator_info = {
                "username": author_data.get("name") or author_data.get("uniqueId") or username,
                "display_name": author_data.get("nickName") or author_data.get("nickname"),
                "platform": "tiktok",
                "profile_url": f"https://www.tiktok.com/@{username}",
                "avatar_url": author_data.get("avatar"),
                "bio": author_data.get("signature") or author_data.get("bio"),
                "followers": author_data.get("fans") or author_data.get("followerCount"),
                "following": author_data.get("following") or author_data.get("followingCount"),
                "total_likes": author_data.get("heart") or author_data.get("heartCount"),
                "total_videos": author_data.get("video") or author_data.get("videoCount"),
                "verified": author_data.get("verified", False),
            }

            # Parse videos if requested
            recent_videos = []
            parse_stats = None
            if include_recent_videos:
                search_tool = TikTokApifySearchTool()
                search_tool._client = self._client
                videos, parse_stats = search_tool._parse_apify_results(raw_results, f"@{username}")
                recent_videos = [v.model_dump(mode="json") for v in videos]

            return ToolResult.ok(
                {
                    "creator": creator_info,
                    "recent_videos": recent_videos,
                    "platform": "tiktok",
                    "method": "apify",
                },
                parse_stats=parse_stats,
            )

        except ValueError as e:
            return ToolResult.fail(f"TikTok creator lookup configuration error: {e}")
        except Exception as e:
            logger.error(f"TikTok Apify creator lookup error: {e}")
            return ToolResult.fail(f"TikTok creator lookup error: {e}")
