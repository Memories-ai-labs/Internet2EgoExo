"""Instagram tools using Apify for reliable scraping.

Apify actors provide professional-grade scraping with anti-bot handling and proxies.
This replaces the fragile instagrapi API + browser fallback chain.
"""

import logging
import re
from datetime import UTC, datetime
from typing import Any

from video_searching_agent.api.apify_client import ApifyClient
from video_searching_agent.models.video import Creator, Platform, Video, VideoMetrics
from video_searching_agent.tools.base import BaseTool, ParseStats, ToolResult
from video_searching_agent.tools.sorting import sort_videos_by_popularity

logger = logging.getLogger(__name__)


class InstagramApifySearchTool(BaseTool):
    """Instagram search using Apify actor for reliable results.

    Uses the apify/instagram-scraper actor which provides:
    - Reliable scraping with proxy rotation
    - Anti-bot handling
    - Support for hashtags, profiles, and posts
    """

    def __init__(self) -> None:
        """Initialize Instagram Apify search tool."""
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
        return "instagram_search"

    @property
    def description(self) -> str:
        return """Search Instagram for reels and posts using Apify scraper.

Use this tool for Instagram-specific queries including:
- Hashtag content discovery
- Creator content and reels
- Trending Instagram content

Returns post/reel data including views, likes, comments, creator info.

Example queries:
- Search for "#fitness" to find fitness-related content
- Search for "@therock" to find a creator's content
- Search for "cooking recipes" (keyword search)"""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keyword phrase, hashtag with #, or @username)",
                },
                "search_type": {
                    "type": "string",
                    "enum": ["keyword", "hashtag", "user"],
                    "description": (
                        "Type of search: 'keyword' for general query terms, "
                        "'hashtag' for hashtag content, "
                        "'user' for creator content"
                    ),
                    "default": "keyword",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum posts/reels to return (1-50)",
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
        """Execute Instagram search via Apify.

        Args:
            query: Search query.
            search_type: Type of search (keyword, hashtag, user).
            max_results: Maximum results to return.
            sort_by: How to sort results (views, likes, engagement, recent).

        Returns:
            ToolResult with list of videos/posts.
        """
        query = kwargs.get("query", "")
        search_type = kwargs.get("search_type", "keyword")
        max_results = min(kwargs.get("max_results", 20), 50)
        sort_by = kwargs.get("sort_by", "views")

        if not query:
            return ToolResult.fail("Query is required")
        query = query.strip()
        if not query:
            return ToolResult.fail("Query must not be empty")

        # Over-fetch to improve quality after sorting (2x requested, capped at 100)
        fetch_count = min(max_results * 2, 100)

        try:
            # Determine search parameters based on query format.
            # Keyword is the safe default for plain multi-word inputs.
            if query.startswith("@") or search_type == "user":
                username = self._normalize_username(query)
                if not username:
                    return ToolResult.fail("Instagram username is invalid")
                raw_results = await self.client.scrape_instagram(
                    username=username, max_results=fetch_count
                )
                effective_search_type = "user"
            elif query.startswith("#") or (
                search_type == "hashtag" and " " not in query.strip()
            ):
                hashtag = self._sanitize_hashtag(query)
                if not hashtag:
                    return ToolResult.fail("Instagram hashtag is invalid")
                raw_results = await self.client.scrape_instagram(
                    hashtag=hashtag, max_results=fetch_count
                )
                effective_search_type = "hashtag"
            else:
                raw_results = await self.client.scrape_instagram(
                    query=query, max_results=fetch_count
                )
                effective_search_type = "keyword"

            # Parse results into Video models
            videos, parse_stats = self._parse_apify_results(raw_results, query)

            # Log parse stats if there were failures
            if parse_stats.has_failures():
                logger.warning(
                    f"Instagram parse issues: {parse_stats.summary()}"
                )

            if not videos:
                return ToolResult.no_results(
                    f"No Instagram content found for query: {query}",
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
                    "platform": "instagram",
                    "search_type": effective_search_type,
                    "sort_by": sort_by,
                    "method": "apify",
                },
                parse_stats=parse_stats,
            )

        except ValueError as e:
            return ToolResult.fail(f"Instagram search configuration error: {e}")
        except Exception as e:
            logger.error(f"Instagram Apify search error: {e}")
            return ToolResult.fail(f"Instagram search error: {e}")

    @staticmethod
    def _sanitize_hashtag(value: str) -> str:
        cleaned = value.lstrip("#").strip()
        hashtag = re.sub(r"[^\w]", "", cleaned, flags=re.UNICODE)
        return hashtag

    @staticmethod
    def _normalize_username(value: str) -> str:
        cleaned = value.lstrip("@").strip()
        username = re.sub(r"[^\w.]", "", cleaned, flags=re.UNICODE)
        return username

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
                # Skip non-video content if marked
                post_type = item.get("type") or item.get("productType", "")
                is_video = post_type.lower() in (
                    "video",
                    "reel",
                    "clips",
                    "igtv",
                ) or item.get("isVideo", True)
                if not is_video:
                    continue

                # Extract creator info
                owner_data = item.get("ownerUsername") or item.get("owner") or {}
                if isinstance(owner_data, str):
                    creator_username = owner_data
                    owner_data = {}
                else:
                    creator_username = (
                        owner_data.get("username")
                        or item.get("ownerUsername")
                        or "unknown"
                    )

                creator = Creator(
                    username=creator_username,
                    display_name=owner_data.get("fullName") or owner_data.get("full_name"),
                    platform=Platform.INSTAGRAM,
                    profile_url=f"https://www.instagram.com/{creator_username}/",  # type: ignore[arg-type]
                    followers=(
                        owner_data.get("followersCount")
                        or owner_data.get("edge_followed_by", {}).get("count")
                    ),
                    avatar_url=owner_data.get("profilePicUrl") or owner_data.get("profile_pic_url"),
                    verified=owner_data.get("isVerified") or owner_data.get("is_verified", False),
                )

                # Extract metrics
                metrics = VideoMetrics(
                    views=self._safe_int(
                        item.get("videoViewCount") or item.get("video_view_count")
                    ),
                    likes=self._safe_int(
                        item.get("likesCount")
                        or item.get("edge_liked_by", {}).get("count")
                    ),
                    comments=self._safe_int(
                        item.get("commentsCount")
                        or item.get("edge_media_to_comment", {}).get("count")
                    ),
                    saves=self._safe_int(item.get("savesCount")),
                )
                if metrics.views or metrics.likes:
                    metrics.engagement_rate = metrics.calculate_engagement_rate(
                        platform=Platform.INSTAGRAM,
                        creator_followers=creator.followers,
                    )

                # Extract post info
                shortcode = item.get("shortCode") or item.get("shortcode") or ""
                platform_id = item.get("id") or shortcode
                url = item.get("url")
                if not url and shortcode:
                    url = f"https://www.instagram.com/p/{shortcode}/"

                if not url:
                    continue

                # Determine if it's a reel
                is_reel = "reel" in url.lower() or post_type.lower() == "reel"
                if is_reel and "/p/" in url:
                    url = url.replace("/p/", "/reel/")

                # Extract hashtags from caption
                caption = item.get("caption") or item.get("text") or ""
                hashtags = re.findall(r"#(\w+)", caption)

                # Parse timestamp
                published_at = None
                timestamp = item.get("timestamp") or item.get("taken_at_timestamp")
                if timestamp:
                    if isinstance(timestamp, int):
                        published_at = datetime.fromtimestamp(timestamp, tz=UTC)
                    elif isinstance(timestamp, str):
                        try:
                            published_at = datetime.fromisoformat(
                                timestamp.replace("Z", "+00:00")
                            )
                        except ValueError:
                            pass

                video = Video(
                    platform=Platform.INSTAGRAM,
                    platform_id=str(platform_id),
                    url=url,
                    title=caption[:100] if caption else None,
                    description=caption,
                    thumbnail_url=(
                        item.get("displayUrl")
                        or item.get("thumbnailUrl")
                        or item.get("thumbnail_src")
                    ),
                    duration_seconds=self._safe_int(
                        item.get("videoDuration") or item.get("video_duration")
                    ),
                    published_at=published_at,
                    creator=creator,
                    metrics=metrics,
                    hashtags=hashtags[:10],
                    source_query=query,
                )
                videos.append(video)
                parse_stats.add_success()

            except Exception as e:
                parse_stats.add_failure(str(e))
                logger.warning(f"Failed to parse Instagram post: {e}")
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


class InstagramApifyCreatorTool(BaseTool):
    """Instagram creator info using Apify actor."""

    def __init__(self) -> None:
        """Initialize Instagram Apify creator tool."""
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
        return "instagram_creator_info"

    @property
    def description(self) -> str:
        return """Get Instagram creator profile information using Apify.

Use this tool when you need:
- Creator statistics (followers, following, posts count)
- Profile information and bio
- Recent posts/reels from a specific creator
- Verification status

Returns profile data and recent content."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Instagram username (without @)",
                },
                "include_recent_posts": {
                    "type": "boolean",
                    "description": "Whether to include recent posts/reels",
                    "default": True,
                },
                "recent_posts_count": {
                    "type": "integer",
                    "description": "Number of recent posts to include (1-30)",
                    "default": 10,
                },
            },
            "required": ["username"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Get Instagram creator profile via Apify.

        Args:
            username: Creator's username.
            include_recent_posts: Whether to get recent posts.
            recent_posts_count: Number of recent posts.

        Returns:
            ToolResult with creator profile and posts.
        """
        username = kwargs.get("username", "").lstrip("@")
        include_recent_posts = kwargs.get("include_recent_posts", True)
        recent_posts_count = min(kwargs.get("recent_posts_count", 10), 30)

        if not username:
            return ToolResult.fail("Username is required")

        try:
            # Fetch creator profile and posts
            raw_results = await self.client.scrape_instagram(
                username=username,
                max_results=recent_posts_count if include_recent_posts else 1,
            )

            if not raw_results:
                return ToolResult.fail(f"Creator @{username} not found")

            # Extract creator info from results
            first_item = raw_results[0] if raw_results else {}
            owner_data = first_item.get("owner") or {}

            creator_info = {
                "username": username,
                "display_name": owner_data.get("fullName") or owner_data.get("full_name"),
                "platform": "instagram",
                "profile_url": f"https://www.instagram.com/{username}/",
                "avatar_url": owner_data.get("profilePicUrl") or owner_data.get("profile_pic_url"),
                "bio": owner_data.get("biography") or owner_data.get("bio"),
                "followers": (
                    owner_data.get("followersCount")
                    or owner_data.get("edge_followed_by", {}).get("count")
                ),
                "following": (
                    owner_data.get("followingCount")
                    or owner_data.get("edge_follow", {}).get("count")
                ),
                "total_posts": (
                    owner_data.get("postsCount")
                    or owner_data.get("edge_owner_to_timeline_media", {}).get("count")
                ),
                "verified": owner_data.get("isVerified") or owner_data.get("is_verified", False),
            }

            # Parse posts if requested
            recent_posts = []
            parse_stats = None
            if include_recent_posts:
                search_tool = InstagramApifySearchTool()
                search_tool._client = self._client
                videos, parse_stats = search_tool._parse_apify_results(raw_results, f"@{username}")
                recent_posts = [v.model_dump(mode="json") for v in videos]

            return ToolResult.ok(
                {
                    "creator": creator_info,
                    "recent_videos": recent_posts,
                    "platform": "instagram",
                    "method": "apify",
                },
                parse_stats=parse_stats,
            )

        except ValueError as e:
            return ToolResult.fail(f"Instagram creator lookup configuration error: {e}")
        except Exception as e:
            logger.error(f"Instagram Apify creator lookup error: {e}")
            return ToolResult.fail(f"Instagram creator lookup error: {e}")
