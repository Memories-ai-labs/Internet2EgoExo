"""Twitter/X tools using Apify for reliable scraping.

Apify actors provide professional-grade scraping with anti-bot handling and proxies.
This replaces the fragile twscrape + browser fallback chain.
"""

import logging
from datetime import datetime
from typing import Any

from video_searching_agent.api.apify_client import ApifyClient
from video_searching_agent.models.video import Creator, Platform, Video, VideoMetrics
from video_searching_agent.tools.base import BaseTool, ParseStats, ToolResult
from video_searching_agent.tools.sorting import sort_videos_by_popularity

logger = logging.getLogger(__name__)


class TwitterApifySearchTool(BaseTool):
    """Twitter/X search using Apify actor for reliable results.

    Uses the apidojo/tweet-scraper actor which provides:
    - Reliable scraping with proxy rotation
    - Anti-bot handling
    - Support for search, hashtags, and user profiles
    """

    def __init__(self) -> None:
        """Initialize Twitter Apify search tool."""
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
        return "twitter_search"

    @property
    def description(self) -> str:
        return """Search Twitter/X for video tweets using Apify scraper.

Use this tool for Twitter-specific queries including:
- Trending video tweets
- Hashtag discovery
- Creator video content

Returns tweet data including views, likes, retweets, replies, and video info.

Example queries:
- Search for "#cooking" to find cooking video tweets
- Search for "@mkbhd" to find a creator's video tweets
- Search for "tech reviews" to find video tweets about tech"""

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
                        "'hashtag' for hashtag content, 'user' for creator tweets"
                    ),
                    "default": "keyword",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum tweets to return (1-50)",
                    "default": 20,
                },
                "videos_only": {
                    "type": "boolean",
                    "description": "Filter to only return tweets with videos",
                    "default": True,
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
        """Execute Twitter search via Apify.

        Args:
            query: Search query.
            search_type: Type of search (keyword, hashtag, user).
            max_results: Maximum results to return.
            videos_only: Filter to video tweets only.
            sort_by: How to sort results (views, likes, engagement, recent).

        Returns:
            ToolResult with list of video tweets.
        """
        query = kwargs.get("query", "")
        search_type = kwargs.get("search_type", "keyword")
        max_results = min(kwargs.get("max_results", 20), 50)
        videos_only = kwargs.get("videos_only", True)
        sort_by = kwargs.get("sort_by", "views")

        if not query:
            return ToolResult.fail("Query is required")

        # Over-fetch to improve quality after sorting (2x requested, capped at 100)
        fetch_count = min(max_results * 2, 100)

        # Determine Twitter native sort parameter
        # Use "Top" for popularity-based sorts, "Latest" for recent
        twitter_sort = "Latest" if sort_by == "recent" else "Top"

        try:
            # Determine search parameters based on query format
            if query.startswith("@") or search_type == "user":
                username = query.lstrip("@")
                raw_results = await self.client.scrape_twitter(
                    username=username, max_results=fetch_count
                )
                effective_search_type = "user"
            elif query.startswith("#") or search_type == "hashtag":
                hashtag = query.lstrip("#")
                raw_results = await self.client.scrape_twitter(
                    hashtag=hashtag, max_results=fetch_count, sort=twitter_sort
                )
                effective_search_type = "hashtag"
            else:
                raw_results = await self.client.scrape_twitter(
                    query=query, max_results=fetch_count, sort=twitter_sort
                )
                effective_search_type = "keyword"

            # Parse results into Video models
            videos, parse_stats = self._parse_apify_results(raw_results, query, videos_only)

            # Log parse stats if there were failures
            if parse_stats.has_failures():
                logger.warning(
                    f"Twitter parse issues: {parse_stats.summary()}"
                )

            if not videos:
                return ToolResult.no_results(
                    f"No Twitter video content found for query: {query}",
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
                    "platform": "twitter",
                    "search_type": effective_search_type,
                    "sort_by": sort_by,
                    "method": "apify",
                },
                parse_stats=parse_stats,
            )

        except ValueError as e:
            return ToolResult.fail(f"Twitter search configuration error: {e}")
        except Exception as e:
            logger.error(f"Twitter Apify search error: {e}")
            return ToolResult.fail(f"Twitter search error: {e}")

    def _parse_apify_results(
        self, raw_results: list[dict[str, Any]], query: str, videos_only: bool = True
    ) -> tuple[list[Video], ParseStats]:
        """Parse Apify actor results into Video models.

        Args:
            raw_results: Raw data from Apify actor.
            query: Original search query.
            videos_only: Filter to only include video tweets.

        Returns:
            Tuple of (list of Video models, ParseStats with parse statistics).
        """
        videos: list[Video] = []
        parse_stats = ParseStats()

        for item in raw_results:
            try:
                # Check if tweet has video
                has_video = (
                    item.get("isVideo")
                    or item.get("extendedEntities", {}).get("media", [{}])[0].get("type") == "video"
                    or any(
                        m.get("type") == "video"
                        for m in item.get("entities", {}).get("media", [])
                    )
                    or item.get("video")
                )

                if videos_only and not has_video:
                    continue

                # Extract creator info
                author_data = item.get("author") or item.get("user") or {}
                creator_username = (
                    author_data.get("userName")
                    or author_data.get("screen_name")
                    or item.get("authorUserName")
                    or "unknown"
                )

                creator = Creator(
                    username=creator_username,
                    display_name=(
                        author_data.get("name")
                        or author_data.get("displayName")
                        or item.get("authorName")
                    ),
                    platform=Platform.TWITTER,
                    profile_url=f"https://twitter.com/{creator_username}",  # type: ignore[arg-type]
                    followers=author_data.get("followers") or author_data.get("followers_count"),
                    following=author_data.get("following") or author_data.get("friends_count"),
                    avatar_url=(
                        author_data.get("profileImageUrl")
                        or author_data.get("profile_image_url_https")
                    ),
                    verified=author_data.get("isVerified") or author_data.get("verified", False),
                )

                # Extract metrics
                metrics = VideoMetrics(
                    views=self._safe_int(
                        item.get("viewCount")
                        or item.get("views")
                        or item.get("public_metrics", {}).get("impression_count")
                    ),
                    likes=self._safe_int(
                        item.get("likeCount")
                        or item.get("favorite_count")
                        or item.get("public_metrics", {}).get("like_count")
                    ),
                    comments=self._safe_int(
                        item.get("replyCount")
                        or item.get("reply_count")
                        or item.get("public_metrics", {}).get("reply_count")
                    ),
                    shares=self._safe_int(
                        item.get("retweetCount")
                        or item.get("retweet_count")
                        or item.get("public_metrics", {}).get("retweet_count")
                    ),
                    quote_tweets=self._safe_int(
                        item.get("quoteCount")
                        or item.get("quote_count")
                        or item.get("public_metrics", {}).get("quote_count")
                    ),
                    impressions=self._safe_int(
                        item.get("impressionCount")
                        or item.get("public_metrics", {}).get("impression_count")
                    ),
                )
                if metrics.views or metrics.impressions or metrics.likes:
                    metrics.engagement_rate = metrics.calculate_engagement_rate(
                        platform=Platform.TWITTER
                    )

                # Extract tweet info
                tweet_id = str(item.get("id") or item.get("id_str") or "")
                url = item.get("url") or f"https://twitter.com/{creator_username}/status/{tweet_id}"

                # Extract hashtags
                hashtags = []
                entities_hashtags = item.get("entities", {}).get("hashtags", [])
                for ht in entities_hashtags:
                    if isinstance(ht, dict):
                        hashtags.append(ht.get("tag") or ht.get("text", ""))
                    elif isinstance(ht, str):
                        hashtags.append(ht)
                hashtags = [h for h in hashtags if h]

                # Parse timestamp
                published_at = None
                created_at = item.get("createdAt") or item.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        try:
                            # Twitter date format: "Wed Oct 10 20:19:24 +0000 2018"
                            published_at = datetime.strptime(
                                created_at, "%a %b %d %H:%M:%S %z %Y"
                            )
                        except ValueError:
                            try:
                                published_at = datetime.fromisoformat(
                                    created_at.replace("Z", "+00:00")
                                )
                            except ValueError:
                                pass

                # Get video duration if available
                video_info = (
                    item.get("extendedEntities", {}).get("media", [{}])[0].get("video_info", {})
                    or item.get("video", {})
                )
                duration_ms = video_info.get("duration_millis") or video_info.get("duration")
                duration_seconds = duration_ms // 1000 if duration_ms else None

                # Get thumbnail
                thumbnail_url = (
                    item.get("extendedEntities", {}).get("media", [{}])[0].get("media_url_https")
                    or item.get("entities", {}).get("media", [{}])[0].get("media_url_https")
                    or item.get("thumbnail")
                )

                text = item.get("text") or item.get("full_text") or ""

                video = Video(
                    platform=Platform.TWITTER,
                    platform_id=tweet_id,
                    url=url,  # type: ignore[arg-type]
                    title=text[:100] if text else None,
                    description=text,
                    thumbnail_url=thumbnail_url,
                    duration_seconds=duration_seconds,
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
                logger.warning(f"Failed to parse Twitter tweet: {e}")
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


class TwitterApifyProfileTool(BaseTool):
    """Twitter/X profile info using Apify actor."""

    def __init__(self) -> None:
        """Initialize Twitter Apify profile tool."""
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
        return "twitter_profile_info"

    @property
    def description(self) -> str:
        return """Get Twitter/X user profile information using Apify.

Use this tool when you need:
- Creator statistics (followers, following, tweet count)
- Profile information and bio
- Recent video tweets from a specific user
- Verification status

Returns profile data and recent video tweets."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Twitter username (without @)",
                },
                "include_recent_tweets": {
                    "type": "boolean",
                    "description": "Whether to include recent video tweets",
                    "default": True,
                },
                "recent_tweets_count": {
                    "type": "integer",
                    "description": "Number of recent tweets to include (1-30)",
                    "default": 10,
                },
            },
            "required": ["username"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Get Twitter profile via Apify.

        Args:
            username: User's username.
            include_recent_tweets: Whether to get recent tweets.
            recent_tweets_count: Number of recent tweets.

        Returns:
            ToolResult with profile and tweets.
        """
        username = kwargs.get("username", "").lstrip("@")
        include_recent_tweets = kwargs.get("include_recent_tweets", True)
        recent_tweets_count = min(kwargs.get("recent_tweets_count", 10), 30)

        if not username:
            return ToolResult.fail("Username is required")

        try:
            # Fetch user tweets
            raw_results = await self.client.scrape_twitter(
                username=username,
                max_results=recent_tweets_count if include_recent_tweets else 1,
            )

            if not raw_results:
                return ToolResult.fail(f"User @{username} not found")

            # Extract user info from first result
            first_item = raw_results[0] if raw_results else {}
            author_data = first_item.get("author") or first_item.get("user") or {}

            profile_info = {
                "username": (
                    author_data.get("userName")
                    or author_data.get("screen_name")
                    or username
                ),
                "display_name": author_data.get("name") or author_data.get("displayName"),
                "platform": "twitter",
                "profile_url": f"https://twitter.com/{username}",
                "avatar_url": (
                    author_data.get("profileImageUrl")
                    or author_data.get("profile_image_url_https")
                ),
                "bio": author_data.get("description") or author_data.get("bio"),
                "followers": author_data.get("followers") or author_data.get("followers_count"),
                "following": author_data.get("following") or author_data.get("friends_count"),
                "total_tweets": (
                    author_data.get("statusesCount")
                    or author_data.get("statuses_count")
                ),
                "verified": author_data.get("isVerified") or author_data.get("verified", False),
                "location": author_data.get("location"),
                "website": author_data.get("url"),
            }

            # Parse video tweets if requested
            recent_videos = []
            parse_stats = None
            if include_recent_tweets:
                search_tool = TwitterApifySearchTool()
                search_tool._client = self._client
                videos, parse_stats = search_tool._parse_apify_results(
                    raw_results, f"@{username}", videos_only=True
                )
                recent_videos = [v.model_dump(mode="json") for v in videos]

            return ToolResult.ok(
                {
                    "profile": profile_info,
                    "recent_videos": recent_videos,
                    "platform": "twitter",
                    "method": "apify",
                },
                parse_stats=parse_stats,
            )

        except ValueError as e:
            return ToolResult.fail(f"Twitter profile lookup configuration error: {e}")
        except Exception as e:
            logger.error(f"Twitter Apify profile lookup error: {e}")
            return ToolResult.fail(f"Twitter profile lookup error: {e}")
