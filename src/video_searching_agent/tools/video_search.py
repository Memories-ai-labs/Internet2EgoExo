"""Unified video search tool: Exa discovery + Apify scraping.

This tool orchestrates semantic search via Exa to discover video URLs
and then uses Apify to scrape full video data from those URLs.
"""

import asyncio
import logging
from typing import Any

from video_searching_agent.api.apify_client import ApifyClient
from video_searching_agent.curation.viewpoint import Viewpoint
from video_searching_agent.models.video import Platform, Video
from video_searching_agent.tools.base import BaseTool, ToolResult
from video_searching_agent.tools.exa import ExaSearchTool, extract_platform_urls
from video_searching_agent.tools.instagram_apify import InstagramApifySearchTool
from video_searching_agent.tools.sorting import (
    rank_videos_for_training_data,
    sort_videos_by_popularity,
)
from video_searching_agent.tools.tiktok_apify import TikTokApifySearchTool
from video_searching_agent.tools.twitter_apify import TwitterApifySearchTool

logger = logging.getLogger(__name__)


def _parse_viewpoint(value: Any) -> Viewpoint | None:
    """Map a tool argument to a viewpoint, treating 'any'/missing as no filter."""
    if not value:
        return None
    candidate = str(value).strip().lower()
    if candidate in ("egocentric", "ego", "first_person"):
        return Viewpoint.EGOCENTRIC
    if candidate in ("exocentric", "exo", "third_person"):
        return Viewpoint.EXOCENTRIC
    return None


class VideoSearchTool(BaseTool):
    """Unified video search: Exa discovery + Apify scraping.

    This tool orchestrates a two-step process:
    1. Use Exa semantic search to discover video URLs across platforms
    2. Use Apify to scrape full video data from discovered URLs

    This provides the best of both worlds:
    - Exa's powerful semantic search for discovery
    - Apify's reliable scraping for full data extraction
    """

    def __init__(self) -> None:
        """Initialize unified video search tool."""
        self._exa_tool: ExaSearchTool | None = None
        self._apify_client: ApifyClient | None = None
        self._tiktok_tool: TikTokApifySearchTool | None = None
        self._instagram_tool: InstagramApifySearchTool | None = None
        self._twitter_tool: TwitterApifySearchTool | None = None

    @property
    def exa_tool(self) -> ExaSearchTool:
        """Lazy-load Exa search tool."""
        if self._exa_tool is None:
            self._exa_tool = ExaSearchTool()
        return self._exa_tool

    @property
    def apify_client(self) -> ApifyClient:
        """Lazy-load Apify client."""
        if self._apify_client is None:
            self._apify_client = ApifyClient()
        return self._apify_client

    @property
    def tiktok_tool(self) -> TikTokApifySearchTool:
        """Lazy-load TikTok tool."""
        if self._tiktok_tool is None:
            self._tiktok_tool = TikTokApifySearchTool()
        return self._tiktok_tool

    @property
    def instagram_tool(self) -> InstagramApifySearchTool:
        """Lazy-load Instagram tool."""
        if self._instagram_tool is None:
            self._instagram_tool = InstagramApifySearchTool()
        return self._instagram_tool

    @property
    def twitter_tool(self) -> TwitterApifySearchTool:
        """Lazy-load Twitter tool."""
        if self._twitter_tool is None:
            self._twitter_tool = TwitterApifySearchTool()
        return self._twitter_tool

    @property
    def name(self) -> str:
        return "video_search"

    @property
    def description(self) -> str:
        return """Find candidate training footage across platforms and the open web.

Combines Exa semantic search for discovery with Apify scraping for full data,
then ranks what it finds by training-data usability rather than popularity.

Use this tool as the first step of any collection run:
- Gathering footage of an activity without a specific platform in mind
- Sweeping for a capture style ("first person", "fixed camera", "GoPro")
- Building the initial candidate pool that later steps filter and verify

Curation arguments do real work here: `viewpoint` drops footage shot from the
wrong perspective, `min_duration_seconds` drops clips too short to train on,
and `license` restricts to material that is safe to reuse. The response reports
what was excluded and why.

Sources searched: YouTube, TikTok, Instagram, Twitter/X and the open web."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query for video content",
                },
                "platforms": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["tiktok", "instagram", "twitter", "youtube", "all"],
                    },
                    "description": "Platforms to search (default: all)",
                    "default": ["all"],
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum total videos to return (1-50)",
                    "default": 20,
                },
                "scrape_urls": {
                    "type": "boolean",
                    "description": "Scrape URLs for full data (slower but more complete)",
                    "default": False,
                },
                "viewpoint": {
                    "type": "string",
                    "enum": ["egocentric", "exocentric", "any"],
                    "description": (
                        "Required camera viewpoint. 'egocentric' keeps "
                        "first-person/head-mounted footage, 'exocentric' keeps "
                        "third-person/fixed-camera footage. Default 'any'."
                    ),
                    "default": "any",
                },
                "min_duration_seconds": {
                    "type": "integer",
                    "description": "Drop clips shorter than this many seconds.",
                },
                "license": {
                    "type": "string",
                    "enum": ["any", "reusable"],
                    "description": (
                        "'reusable' keeps only clips whose licence is known to "
                        "permit reuse."
                    ),
                    "default": "any",
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["usability", "longest", "views", "likes", "engagement", "recent"],
                    "description": (
                        "Ranking. 'usability' (default) ranks by viewpoint match, "
                        "then duration, then licence. The popularity options exist "
                        "for reporting, not for building datasets."
                    ),
                    "default": "usability",
                },
                "time_frame": {
                    "type": "string",
                    "enum": [
                        "past_24_hours",
                        "past_48_hours",
                        "past_week",
                        "past_month",
                        "past_year",
                    ],
                    "description": "Time window for results (filters to videos "
                    "published within this period)",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute unified video search.

        Steps:
        1. Exa semantic search for video URLs
        2. Group URLs by platform
        3. Optionally scrape each platform with Apify
        4. Merge and return results

        Args:
            query: Search query.
            platforms: List of platforms to search.
            max_results: Maximum results to return.
            scrape_urls: Whether to scrape URLs for full data.

        Returns:
            ToolResult with videos from all platforms.
        """
        query = kwargs.get("query", "")
        platforms = kwargs.get("platforms", ["all"])
        max_results = min(kwargs.get("max_results", 20), 50)
        scrape_urls = kwargs.get("scrape_urls", False)
        sort_by = kwargs.get("sort_by", "usability")
        time_frame = kwargs.get("time_frame")
        wanted_viewpoint = _parse_viewpoint(kwargs.get("viewpoint"))
        min_duration_seconds = kwargs.get("min_duration_seconds")
        license_filter = str(kwargs.get("license", "any")).lower()

        if not query:
            return ToolResult.fail("Query is required")

        # Convert time_frame to start_date for Exa filtering
        start_date = None
        if time_frame:
            from video_searching_agent.utils import get_published_after_date
            start_date = get_published_after_date(time_frame)

        # Normalize platforms
        if "all" in platforms:
            platforms = ["tiktok", "instagram", "twitter", "youtube"]

        try:
            # Step 1: Exa semantic search for video URLs
            exa_result = await self._search_with_exa(query, platforms, max_results, start_date)

            if not exa_result.success:
                return exa_result

            exa_data = exa_result.data
            exa_results = exa_data.get("results", [])

            # Step 2: Extract and group URLs by platform
            platform_urls = extract_platform_urls(exa_results)

            # Collect videos from Exa results
            all_videos = exa_data.get("videos", [])

            # Step 3: Optionally scrape URLs for full data
            if scrape_urls and any(platform_urls.values()):
                scraped_videos = await self._scrape_platform_urls(
                    platform_urls, platforms, max_results
                )
                all_videos.extend(scraped_videos)

            exclusions: dict[str, int] = {}

            # Deduplicate by URL
            seen_urls = set()
            unique_videos = []
            for video in all_videos:
                url = video.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_videos.append(video)

            # Sort videos by specified metric before limiting
            if unique_videos:
                video_objects = []
                for v in unique_videos:
                    try:
                        video_objects.append(Video(**v) if isinstance(v, dict) else v)
                    except Exception:
                        pass  # Skip malformed entries

                if video_objects:
                    if sort_by in ("usability", "longest"):
                        kept, dropped = rank_videos_for_training_data(
                            video_objects,
                            wanted_viewpoint=wanted_viewpoint,
                            min_duration_seconds=min_duration_seconds,
                            license_filter=license_filter,
                        )
                        if sort_by == "longest":
                            kept.sort(key=lambda v: v.duration_seconds or 0, reverse=True)
                        for video, reason in dropped:
                            exclusions[reason] = exclusions.get(reason, 0) + 1
                            del video
                        unique_videos = [v.model_dump(mode="json") for v in kept]
                    else:
                        sorted_videos = sort_videos_by_popularity(video_objects, sort_by=sort_by)
                        unique_videos = [v.model_dump(mode="json") for v in sorted_videos]

            # Limit to max_results after sorting
            unique_videos = unique_videos[:max_results]

            return ToolResult.ok({
                "videos": unique_videos,
                "total_results": len(unique_videos),
                "query": query,
                "platforms_searched": platforms,
                "urls_discovered": {
                    str(p.value): len(urls) for p, urls in platform_urls.items() if urls
                },
                "method": "exa+apify" if scrape_urls else "exa",
                "sorted_by": sort_by,
                "requested_viewpoint": wanted_viewpoint.value if wanted_viewpoint else None,
                "excluded": sum(exclusions.values()),
                "exclusion_reasons": exclusions,
            })

        except Exception as e:
            logger.error(f"Video search error: {e}")
            return ToolResult.fail(f"Video search error: {e}")

    async def _search_with_exa(
        self, query: str, platforms: list[str], max_results: int, start_date: str | None = None
    ) -> ToolResult:
        """Search with Exa for video URLs.

        Args:
            query: Search query.
            platforms: Target platforms.
            max_results: Maximum results.
            start_date: Filter to results published after this date (ISO 8601 format).

        Returns:
            ToolResult with Exa search results.
        """
        # Build platform-specific domain filters
        include_domains = []
        if "tiktok" in platforms:
            include_domains.append("tiktok.com")
        if "instagram" in platforms:
            include_domains.append("instagram.com")
        if "twitter" in platforms:
            include_domains.extend(["twitter.com", "x.com"])
        if "youtube" in platforms:
            include_domains.extend(["youtube.com", "youtu.be"])

        # Enhance query for video content
        video_query = f"{query} video"

        # Build kwargs for Exa search
        exa_kwargs: dict[str, Any] = {
            "query": video_query,
            "num_results": max_results * 2,  # Get more to filter
        }
        if include_domains:
            exa_kwargs["include_domains"] = include_domains
        if start_date:
            exa_kwargs["start_published_date"] = start_date

        return await self.exa_tool.execute(**exa_kwargs)

    async def _scrape_platform_urls(
        self,
        platform_urls: dict[Platform, list[str]],
        requested_platforms: list[str],
        max_results: int,
    ) -> list[dict[str, Any]]:
        """Scrape URLs with Apify for full video data.

        Args:
            platform_urls: URLs grouped by platform.
            requested_platforms: Platforms to scrape.
            max_results: Maximum results to return.

        Returns:
            List of video data dicts.
        """
        all_videos: list[dict[str, Any]] = []
        tasks = []

        # Create scraping tasks for each platform
        if "tiktok" in requested_platforms and platform_urls.get(Platform.TIKTOK):
            urls = platform_urls[Platform.TIKTOK][:max_results]
            tasks.append(self._scrape_tiktok_urls(urls))

        if "instagram" in requested_platforms and platform_urls.get(Platform.INSTAGRAM):
            urls = platform_urls[Platform.INSTAGRAM][:max_results]
            tasks.append(self._scrape_instagram_urls(urls))

        if "twitter" in requested_platforms and platform_urls.get(Platform.TWITTER):
            urls = platform_urls[Platform.TWITTER][:max_results]
            tasks.append(self._scrape_twitter_urls(urls))

        # Execute all scraping tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_videos.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Scraping task failed: {result}")

        return all_videos

    async def _scrape_tiktok_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        """Scrape TikTok URLs for video data."""
        try:
            raw_results = await self.apify_client.scrape_tiktok(urls=urls)
            videos, _ = self.tiktok_tool._parse_apify_results(raw_results, "url_scrape")
            return [v.model_dump(mode="json") for v in videos]
        except Exception as e:
            logger.warning(f"TikTok URL scraping failed: {e}")
            return []

    async def _scrape_instagram_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        """Scrape Instagram URLs for video data."""
        try:
            raw_results = await self.apify_client.scrape_instagram(urls=urls)
            videos, _ = self.instagram_tool._parse_apify_results(raw_results, "url_scrape")
            return [v.model_dump(mode="json") for v in videos]
        except Exception as e:
            logger.warning(f"Instagram URL scraping failed: {e}")
            return []

    async def _scrape_twitter_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        """Scrape Twitter URLs for video data."""
        try:
            raw_results = await self.apify_client.scrape_twitter(urls=urls)
            videos, _ = self.twitter_tool._parse_apify_results(raw_results, "url_scrape")
            return [v.model_dump(mode="json") for v in videos]
        except Exception as e:
            logger.warning(f"Twitter URL scraping failed: {e}")
            return []
