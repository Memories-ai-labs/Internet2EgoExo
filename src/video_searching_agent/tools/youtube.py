"""YouTube Data API search tool."""

import asyncio
import threading
from datetime import datetime
from typing import Any

from googleapiclient.discovery import build  # type: ignore[import-untyped]
from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

from video_searching_agent.config.settings import get_settings
from video_searching_agent.models.video import Creator, Platform, Video, VideoMetrics
from video_searching_agent.tools.base import BaseTool, ToolResult


def _execute_request_with_lock(
    request: Any,
    request_lock: threading.Lock,
) -> dict[str, Any]:
    """Execute a blocking request while guarding shared SDK client state."""
    with request_lock:
        return request.execute()


async def _execute_request(request: Any, request_lock: threading.Lock) -> dict[str, Any]:
    """Execute a blocking googleapiclient request without blocking event loop."""
    return await asyncio.to_thread(_execute_request_with_lock, request, request_lock)


class YouTubeSearchTool(BaseTool):
    """Tool for searching YouTube videos, channels, and playlists."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize YouTube search tool.

        Args:
            api_key: YouTube Data API key. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.youtube_api_key
        self._youtube: Any = None
        self._request_lock = threading.Lock()

    @property
    def youtube(self) -> Any:
        """Lazy-load YouTube API client."""
        if self._youtube is None:
            self._youtube = build("youtube", "v3", developerKey=self.api_key)
        return self._youtube

    def health_check(self) -> tuple[bool, str | None]:
        """Check if YouTube API key is configured."""
        if not self.api_key:
            return False, "YOUTUBE_API_KEY is not configured"
        return True, None

    async def _execute_request_locked(self, request: Any) -> dict[str, Any]:
        """Execute one YouTube request with per-tool lock protection."""
        return await _execute_request(request, self._request_lock)

    @property
    def name(self) -> str:
        return "youtube_search"

    @property
    def description(self) -> str:
        return """Search YouTube for videos, channels, or playlists.
Use this tool when the user specifically asks about YouTube content or when
YouTube is the most relevant platform for their query.

Capabilities:
- Search for videos by keyword, topic, or trend
- Find specific channels or creators
- Get video details including views, likes, comments, duration
- Filter by upload date, view count, or relevance

Returns structured video data including thumbnails, statistics, and channel info."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for YouTube",
                },
                "search_type": {
                    "type": "string",
                    "enum": ["video", "channel", "playlist"],
                    "description": "Type of content to search for",
                    "default": "video",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (1-50)",
                    "default": 10,
                },
                "order_by": {
                    "type": "string",
                    "enum": ["relevance", "date", "viewCount", "rating"],
                    "description": "How to order results",
                    "default": "relevance",
                },
                "published_after": {
                    "type": "string",
                    "description": (
                        "ISO 8601 date to filter videos published after "
                        "(e.g., 2024-01-01T00:00:00Z)"
                    ),
                },
                "channel_id": {
                    "type": "string",
                    "description": "Optional channel ID to search within a specific channel",
                },
                "video_duration": {
                    "type": "string",
                    "enum": ["any", "short", "medium", "long"],
                    "description": (
                        "Filter by video duration: short (<4min), "
                        "medium (4-20min), long (>20min)"
                    ),
                    "default": "any",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute YouTube search.

        Args:
            query: Search query.
            search_type: Type of search (video, channel, playlist).
            max_results: Maximum results to return.
            order_by: Sort order.
            published_after: Date filter.
            channel_id: Filter by channel.
            video_duration: Duration filter.

        Returns:
            ToolResult with list of videos/channels.
        """
        query = kwargs.get("query")
        search_type = kwargs.get("search_type", "video")
        max_results = min(kwargs.get("max_results", 10), 50)
        order_by = kwargs.get("order_by", "relevance")
        published_after = kwargs.get("published_after")
        channel_id = kwargs.get("channel_id")
        video_duration = kwargs.get("video_duration", "any")

        try:
            # Build search request
            search_params: dict[str, Any] = {
                "q": query,
                "type": search_type,
                "part": "snippet",
                "maxResults": max_results,
                "order": order_by,
            }

            if published_after:
                search_params["publishedAfter"] = published_after

            if channel_id:
                search_params["channelId"] = channel_id

            if video_duration != "any" and search_type == "video":
                search_params["videoDuration"] = video_duration

            # Execute search
            search_response = await self._execute_request_locked(
                self.youtube.search().list(**search_params)
            )

            items = search_response.get("items", [])
            if not items:
                return ToolResult.ok({
                    "videos": [],
                    "message": f"No {search_type}s found for query: {query}",
                })

            if search_type == "video":
                # Get video IDs for detailed stats
                video_ids: list[str] = [
                    item["id"]["videoId"] for item in items
                    if item.get("id", {}).get("videoId")
                ]
                videos = await self._get_video_details(video_ids, str(query) if query else "")
                return ToolResult.ok({
                    "videos": [v.model_dump(mode='json') for v in videos],
                    "total_results": len(videos),
                    "query": query,
                })

            elif search_type == "channel":
                channels = self._parse_channels(items)
                return ToolResult.ok({
                    "channels": channels,
                    "total_results": len(channels),
                    "query": query,
                })

            else:  # playlist
                playlists = self._parse_playlists(items)
                return ToolResult.ok({
                    "playlists": playlists,
                    "total_results": len(playlists),
                    "query": query,
                })

        except HttpError as e:
            return ToolResult.fail(f"YouTube API error: {e.reason}")
        except Exception as e:
            return ToolResult.fail(f"YouTube search error: {str(e)}")

    async def _get_video_details(self, video_ids: list[str], query: str) -> list[Video]:
        """Get detailed video information including stats.

        Args:
            video_ids: List of video IDs.
            query: Original search query.

        Returns:
            List of Video objects with full details.
        """
        videos_response = await self._execute_request_locked(
            self.youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics,contentDetails",
            )
        )

        videos: list[Video] = []
        for item in videos_response.get("items", []):
            video = self._parse_video(item, query)
            videos.append(video)

        return videos

    def _parse_video(self, item: dict[str, Any], query: str) -> Video:
        """Parse YouTube API video item to Video model.

        Args:
            item: YouTube API video item.
            query: Original search query.

        Returns:
            Video model instance.
        """
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        # Parse duration (ISO 8601 format: PT#M#S)
        duration_str = content.get("duration", "")
        duration_seconds = self._parse_duration(duration_str)

        # Parse published date
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        # Create creator
        creator = Creator(
            username=snippet.get("channelTitle", "Unknown"),
            display_name=snippet.get("channelTitle"),
            platform=Platform.YOUTUBE,
            profile_url=f"https://www.youtube.com/channel/{snippet.get('channelId')}",  # type: ignore[arg-type]
        )

        # Create metrics
        metrics = VideoMetrics(
            views=int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
            likes=int(stats.get("likeCount", 0)) if stats.get("likeCount") else None,
            comments=int(stats.get("commentCount", 0)) if stats.get("commentCount") else None,
        )
        if metrics.views and metrics.likes:
            metrics.engagement_rate = metrics.calculate_engagement_rate()

        # Get best thumbnail
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("maxres", {}).get("url")
            or thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
        )

        return Video(
            platform=Platform.YOUTUBE,
            platform_id=item["id"],
            url=f"https://www.youtube.com/watch?v={item['id']}",  # type: ignore[arg-type]
            title=snippet.get("title"),
            description=snippet.get("description", "")[:500],  # Truncate
            thumbnail_url=thumbnail_url,
            duration_seconds=duration_seconds,
            published_at=published_at,
            creator=creator,
            metrics=metrics,
            hashtags=self._extract_hashtags(snippet.get("description", "")),
            category=snippet.get("categoryId"),
            source_query=query,
        )

    def _parse_duration(self, duration_str: str) -> int | None:
        """Parse ISO 8601 duration to seconds.

        Args:
            duration_str: ISO 8601 duration (e.g., PT4M13S).

        Returns:
            Duration in seconds or None.
        """
        if not duration_str:
            return None

        import re

        match = re.match(
            r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
            duration_str,
        )
        if not match:
            return None

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def _extract_hashtags(self, text: str) -> list[str]:
        """Extract hashtags from text.

        Args:
            text: Text to extract hashtags from.

        Returns:
            List of hashtags (without #).
        """
        import re

        hashtags = re.findall(r"#(\w+)", text)
        return list(set(hashtags))[:10]  # Limit to 10 unique hashtags

    def _parse_channels(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse channel search results.

        Args:
            items: YouTube API search items.

        Returns:
            List of channel data dicts.
        """
        channels = []
        for item in items:
            snippet = item.get("snippet", {})
            channels.append({
                "channel_id": item["id"]["channelId"],
                "title": snippet.get("title"),
                "description": snippet.get("description", "")[:300],
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "url": f"https://www.youtube.com/channel/{item['id']['channelId']}",
            })
        return channels

    def _parse_playlists(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse playlist search results.

        Args:
            items: YouTube API search items.

        Returns:
            List of playlist data dicts.
        """
        playlists = []
        for item in items:
            snippet = item.get("snippet", {})
            playlists.append({
                "playlist_id": item["id"]["playlistId"],
                "title": snippet.get("title"),
                "description": snippet.get("description", "")[:300],
                "channel_title": snippet.get("channelTitle"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "url": f"https://www.youtube.com/playlist?list={item['id']['playlistId']}",
            })
        return playlists


class YouTubeChannelTool(BaseTool):
    """Tool for getting detailed YouTube channel information."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize YouTube channel tool.

        Args:
            api_key: YouTube Data API key. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.youtube_api_key
        self._youtube: Any = None
        self._request_lock = threading.Lock()

    @property
    def youtube(self) -> Any:
        """Lazy-load YouTube API client."""
        if self._youtube is None:
            self._youtube = build("youtube", "v3", developerKey=self.api_key)
        return self._youtube

    def health_check(self) -> tuple[bool, str | None]:
        """Check if YouTube API key is configured."""
        if not self.api_key:
            return False, "YOUTUBE_API_KEY is not configured"
        return True, None

    async def _execute_request_locked(self, request: Any) -> dict[str, Any]:
        """Execute one YouTube request with per-tool lock protection."""
        return await _execute_request(request, self._request_lock)

    @property
    def name(self) -> str:
        return "youtube_channel_info"

    @property
    def description(self) -> str:
        return """Get detailed information about a YouTube channel.
Use this tool when you need specific channel statistics, recent videos,
or detailed creator information.

Returns: subscriber count, video count, view count, recent uploads, and channel description."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "string",
                    "description": "YouTube channel ID (e.g., UC...)",
                },
                "username": {
                    "type": "string",
                    "description": "YouTube username/handle (alternative to channel_id)",
                },
                "include_recent_videos": {
                    "type": "boolean",
                    "description": "Whether to include recent video uploads",
                    "default": True,
                },
                "recent_videos_count": {
                    "type": "integer",
                    "description": "Number of recent videos to include (1-20)",
                    "default": 5,
                },
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Get YouTube channel information.

        Args:
            channel_id: Channel ID to look up.
            username: Username to look up (alternative).
            include_recent_videos: Whether to get recent videos.
            recent_videos_count: Number of recent videos.

        Returns:
            ToolResult with channel details.
        """
        channel_id = kwargs.get("channel_id")
        username = kwargs.get("username")
        include_recent_videos = kwargs.get("include_recent_videos", True)
        recent_videos_count = min(kwargs.get("recent_videos_count", 5), 20)

        if not channel_id and not username:
            return ToolResult.fail("Either channel_id or username is required")

        try:
            # Get channel info
            if channel_id:
                channel_response = await self._execute_request_locked(
                    self.youtube.channels().list(
                        id=channel_id,
                        part="snippet,statistics,contentDetails",
                    )
                )
            else:
                channel_response = await self._execute_request_locked(
                    self.youtube.channels().list(
                        forHandle=username,
                        part="snippet,statistics,contentDetails",
                    )
                )

            items = channel_response.get("items", [])
            if not items:
                return ToolResult.fail(f"Channel not found: {channel_id or username}")

            channel = items[0]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})

            result = {
                "channel_id": channel["id"],
                "title": snippet.get("title"),
                "description": snippet.get("description", "")[:500],
                "custom_url": snippet.get("customUrl"),
                "country": snippet.get("country"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "view_count": int(stats.get("viewCount", 0)),
                "url": f"https://www.youtube.com/channel/{channel['id']}",
            }

            # Get recent videos if requested
            if include_recent_videos:
                uploads_playlist_id = (
                    channel.get("contentDetails", {})
                    .get("relatedPlaylists", {})
                    .get("uploads")
                )
                if uploads_playlist_id:
                    playlist_response = await self._execute_request_locked(
                        self.youtube.playlistItems().list(
                            playlistId=uploads_playlist_id,
                            part="snippet",
                            maxResults=recent_videos_count,
                        )
                    )
                    result["recent_videos"] = [
                        {
                            "video_id": item["snippet"]["resourceId"]["videoId"],
                            "title": item["snippet"]["title"],
                            "published_at": item["snippet"]["publishedAt"],
                            "url": f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
                        }
                        for item in playlist_response.get("items", [])
                    ]

            return ToolResult.ok(result)

        except HttpError as e:
            return ToolResult.fail(f"YouTube API error: {e.reason}")
        except Exception as e:
            return ToolResult.fail(f"YouTube channel error: {str(e)}")
