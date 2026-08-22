"""YouTube Data API search tool."""

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Any

from googleapiclient.discovery import build  # type: ignore[import-untyped]
from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

from video_searching_agent.config.settings import get_settings
from video_searching_agent.models.video import Creator, Platform, Video, VideoMetrics
from video_searching_agent.tools.base import BaseTool, ToolResult
from video_searching_agent.utils.youtube_urls import youtube_video_id

logger = logging.getLogger(__name__)


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


# A burst limit is worth retrying and worth routing around; a spent daily quota
# is neither, because it does not come back until midnight Pacific. Google
# reports both with a message that says "Quota exceeded", so the reason code is
# the only thing that distinguishes them.
_BURST_REASONS = frozenset({"rateLimitExceeded", "userRateLimitExceeded", "backendError"})
_DAILY_REASONS = frozenset({"quotaExceeded", "dailyLimitExceeded"})


def _http_error_reason(error: HttpError) -> str:
    """The machine-readable reason code from a Google API error.

    ``HttpError.reason`` is the human sentence, which is why a rate limit read
    as an exhausted quota for so long: the sentence for both begins "Quota
    exceeded for quota metric".
    """
    try:
        payload = json.loads(error.content.decode("utf-8"))
        errors = (payload.get("error") or {}).get("errors") or []
        if errors and errors[0].get("reason"):
            return str(errors[0]["reason"])
    except (ValueError, AttributeError, UnicodeDecodeError):
        pass
    status = getattr(error, "status_code", None) or getattr(error.resp, "status", None)
    return f"http{status}" if status else "unknown"


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
        """Lazy-load YouTube API client.

        Raises:
            ValueError: When no key is configured. Without this,
                `googleapiclient` falls back to Application Default Credentials
                and the caller gets a confusing Google Cloud error instead of
                being told which key is missing.
        """
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is not configured")
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
        return """Search YouTube for candidate training footage, channels or playlists.

YouTube is the largest public source of both egocentric (POV, head-mounted,
GoPro, wearable) and exocentric (fixed camera, tripod, multi-view) recordings.

Capabilities:
- Search by activity, scene or capture style ("first person kitchen", "POV assembly")
- Filter by clip length (`video_duration`) and by reusable licence (`license`)
- Return duration in seconds and the licence for every hit, which is what
  decides whether a clip can go into a dataset
- Find channels that publish a given capture style

Returns structured video data including duration, licence, thumbnails and channel info."""

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
                        "medium (4-20min), long (>20min). Prefer medium/long for "
                        "training footage."
                    ),
                    "default": "any",
                },
                "license": {
                    "type": "string",
                    "enum": ["any", "reusable"],
                    "description": (
                        "Set to 'reusable' to return only Creative-Commons "
                        "licensed videos, which are the ones safe to reuse as "
                        "training data."
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
        license_filter = str(kwargs.get("license", "any")).lower()

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

            if license_filter == "reusable" and search_type == "video":
                search_params["videoLicense"] = "creativeCommon"

            # Execute search
            search_response = await self._execute_request_locked(
                self.youtube.search().list(**search_params)
            )

            items = search_response.get("items", [])
            if not items:
                return ToolResult.ok(
                    {
                        "videos": [],
                        "message": f"No {search_type}s found for query: {query}",
                    }
                )

            if search_type == "video":
                # Get video IDs for detailed stats
                video_ids: list[str] = [
                    item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")
                ]
                videos = await self._get_video_details(video_ids, str(query) if query else "")
                return ToolResult.ok(
                    {
                        "videos": [v.model_dump(mode="json") for v in videos],
                        "total_results": len(videos),
                        "query": query,
                    }
                )

            elif search_type == "channel":
                channels = self._parse_channels(items)
                return ToolResult.ok(
                    {
                        "channels": channels,
                        "total_results": len(channels),
                        "query": query,
                    }
                )

            else:  # playlist
                playlists = self._parse_playlists(items)
                return ToolResult.ok(
                    {
                        "playlists": playlists,
                        "total_results": len(playlists),
                        "query": query,
                    }
                )

        except HttpError as e:
            reason = _http_error_reason(e)
            if search_type == "video" and reason in _BURST_REASONS:
                # search.list is the only expensive call here: 100 quota units
                # against videos.list's 1. So when *searching* is what got
                # limited, find the videos another way and still describe them
                # through the API, which is a hundredth of the cost.
                logger.info("YouTube search rate limited (%s); finding via Exa instead", reason)
                fallback = await self._search_via_exa(
                    str(query) if query else "",
                    max_results=max_results,
                    license_filter=license_filter,
                )
                if fallback is not None:
                    return fallback
            return ToolResult.fail(f"YouTube API error [{reason}]: {e.reason}")
        except Exception as e:
            return ToolResult.fail(f"YouTube search error: {str(e)}")

    async def _search_via_exa(
        self,
        query: str,
        *,
        max_results: int,
        license_filter: str,
    ) -> ToolResult | None:
        """Find YouTube videos through Exa, then describe them through the API.

        Returns None when Exa cannot serve either, so the caller reports the
        original YouTube failure rather than a confusing second one.

        The licence filter cannot be applied by Exa, so it is applied here
        against what ``videos.list`` reports — which is the authoritative
        answer anyway.
        """
        from video_searching_agent.tools.exa import ExaSearchTool

        try:
            exa = ExaSearchTool()
        except Exception as exc:  # noqa: BLE001 - no Exa key is a normal state
            logger.info("no Exa fallback available: %s", exc)
            return None

        result = await exa.execute(
            query=f"{query} site:youtube.com/watch",
            num_results=min(max(max_results * 2, 10), 25),
            include_domains=["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"],
        )
        if not result.success:
            logger.info("Exa fallback also failed: %s", result.error)
            return None

        payload = result.data if isinstance(result.data, dict) else {}
        candidates = payload.get("results") or payload.get("videos") or []
        video_ids: list[str] = []
        for entry in candidates:
            url = entry.get("url") if isinstance(entry, dict) else None
            found = youtube_video_id(str(url)) if url else None
            if found and found not in video_ids:
                video_ids.append(found)
            if len(video_ids) >= max_results:
                break

        if not video_ids:
            logger.info("Exa returned no YouTube video URLs for %r", query)
            return None

        videos = await self._get_video_details(video_ids, query)
        if license_filter == "reusable":
            videos = [v for v in videos if str(v.license or "").lower() == "creativecommon"]

        return ToolResult.ok(
            {
                "videos": [v.model_dump(mode="json") for v in videos],
                "total_results": len(videos),
                "query": query,
                "found_via": "exa",
                "note": (
                    "YouTube's search endpoint was rate limited, so these were found "
                    "through Exa and then described through the YouTube API"
                ),
            }
        )

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
                part="snippet,statistics,contentDetails,status",
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
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
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
            license=item.get("status", {}).get("license"),
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
            channels.append(
                {
                    "channel_id": item["id"]["channelId"],
                    "title": snippet.get("title"),
                    "description": snippet.get("description", "")[:300],
                    "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "url": f"https://www.youtube.com/channel/{item['id']['channelId']}",
                }
            )
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
            playlists.append(
                {
                    "playlist_id": item["id"]["playlistId"],
                    "title": snippet.get("title"),
                    "description": snippet.get("description", "")[:300],
                    "channel_title": snippet.get("channelTitle"),
                    "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "url": f"https://www.youtube.com/playlist?list={item['id']['playlistId']}",
                }
            )
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
        """Lazy-load YouTube API client.

        Raises:
            ValueError: When no key is configured. Without this,
                `googleapiclient` falls back to Application Default Credentials
                and the caller gets a confusing Google Cloud error instead of
                being told which key is missing.
        """
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is not configured")
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
                    channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
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
