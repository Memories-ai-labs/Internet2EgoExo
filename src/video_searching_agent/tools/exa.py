"""Exa.ai web search tools for semantic/neural search."""

import asyncio
import re
from datetime import datetime
from typing import Any

from video_searching_agent.config.settings import get_settings
from video_searching_agent.models.video import Platform, Video
from video_searching_agent.tools.base import BaseTool, ToolResult


def extract_platform_urls(results: list[dict[str, Any]]) -> dict[Platform, list[str]]:
    """Extract and group video platform URLs from Exa search results.

    Args:
        results: List of Exa search results with 'url' field.

    Returns:
        Dictionary mapping Platform to list of URLs from that platform.
    """
    platform_urls: dict[Platform, list[str]] = {
        Platform.TIKTOK: [],
        Platform.INSTAGRAM: [],
        Platform.TWITTER: [],
        Platform.YOUTUBE: [],
        Platform.FACEBOOK: [],
    }

    for result in results:
        url = result.get("url", "")
        if not url:
            continue

        url_lower = url.lower()

        # Match URLs to platforms
        if "tiktok.com" in url_lower:
            # Only include actual video URLs
            if "/video/" in url_lower or "/@" in url_lower:
                platform_urls[Platform.TIKTOK].append(url)
        elif "instagram.com" in url_lower:
            # Include reels and posts
            if "/reel/" in url_lower or "/p/" in url_lower:
                platform_urls[Platform.INSTAGRAM].append(url)
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            # Include status URLs (tweets)
            if "/status/" in url_lower:
                platform_urls[Platform.TWITTER].append(url)
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            # Include watch URLs and shorts
            if "watch?v=" in url_lower or "/shorts/" in url_lower or "youtu.be/" in url_lower:
                platform_urls[Platform.YOUTUBE].append(url)
        elif "facebook.com" in url_lower or "fb.watch" in url_lower:
            if "/video" in url_lower or "fb.watch" in url_lower:
                platform_urls[Platform.FACEBOOK].append(url)

    return platform_urls


class ExaSearchTool(BaseTool):
    """Tool for neural/semantic web search using Exa.ai.

    This tool replaces the placeholder WebSearchTool with powerful
    semantic search capabilities that understand intent, not just keywords.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Exa search tool.

        Args:
            api_key: Exa API key. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.exa_api_key
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy-load Exa client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("EXA_API_KEY is required for Exa search")
            from exa_py import Exa

            self._client = Exa(api_key=self.api_key)
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Exa API key is configured."""
        if not self.api_key:
            return False, "EXA_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "exa_search"

    @property
    def description(self) -> str:
        return """Search the web for video-related content using neural/semantic search.
Use this tool for:
- Finding video content across blogs, news sites, Vimeo, Dailymotion, etc.
- Discovering trending video topics and news
- Researching brands, products, or topics with video coverage
- Finding video content NOT on major platforms (YouTube, TikTok, Instagram)
- General web research about video trends, creators, or content strategies

More powerful than traditional keyword search - understands semantic meaning.
Returns search results with titles, URLs, snippets, and optionally full page content."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language search query. Can be a question or topic."
                    ),
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-25)",
                    "default": 10,
                },
                "search_type": {
                    "type": "string",
                    "enum": ["neural", "keyword", "auto"],
                    "description": "Search type: neural (semantic), keyword, auto (default)",
                    "default": "auto",
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Whether to extract page content along with results",
                    "default": False,
                },
                "start_published_date": {
                    "type": "string",
                    "description": "Filter results published after this date (YYYY-MM-DD format)",
                },
                "end_published_date": {
                    "type": "string",
                    "description": "Filter results published before this date (YYYY-MM-DD format)",
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only include results from these domains",
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exclude results from these domains",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute Exa web search.

        Args:
            query: Search query.
            num_results: Maximum results to return.
            search_type: Type of search (neural, keyword, auto).
            include_content: Whether to extract page content.
            start_published_date: Filter by publish date.
            end_published_date: Filter by publish date.
            include_domains: Only include these domains.
            exclude_domains: Exclude these domains.

        Returns:
            ToolResult with search results and any detected video content.
        """
        query = kwargs.get("query")
        if not query:
            return ToolResult.fail("Query is required")

        num_results = min(kwargs.get("num_results", 10), 25)
        search_type = kwargs.get("search_type", "auto")
        include_content = kwargs.get("include_content", False)
        start_published_date = kwargs.get("start_published_date")
        end_published_date = kwargs.get("end_published_date")
        include_domains = kwargs.get("include_domains")
        exclude_domains = kwargs.get("exclude_domains")

        try:
            # Build search parameters
            search_kwargs: dict[str, Any] = {
                "num_results": num_results,
            }

            # Set search type
            if search_type == "neural":
                search_kwargs["type"] = "neural"
            elif search_type == "keyword":
                search_kwargs["type"] = "keyword"
            # "auto" - don't specify, let Exa decide

            # Date filters
            if start_published_date:
                search_kwargs["start_published_date"] = start_published_date
            if end_published_date:
                search_kwargs["end_published_date"] = end_published_date

            # Domain filters
            if include_domains:
                search_kwargs["include_domains"] = include_domains
            if exclude_domains:
                search_kwargs["exclude_domains"] = exclude_domains

            # Execute search (exa-py is synchronous, wrap in thread)
            if include_content:
                search_kwargs["text"] = True
                response = await asyncio.to_thread(
                    self.client.search_and_contents, query, **search_kwargs
                )
            else:
                response = await asyncio.to_thread(
                    self.client.search, query, **search_kwargs
                )

            # Parse results
            results = []
            videos = []
            for result in response.results:
                url = result.url
                text = getattr(result, "text", "") if hasattr(result, "text") else ""
                result_data = {
                    "url": url,
                    "title": result.title,
                    "snippet": text[:300] if text else None,
                    "published_date": getattr(result, "published_date", None),
                    "score": getattr(result, "score", None),
                }

                if include_content and hasattr(result, "text"):
                    result_data["content"] = result.text

                results.append(result_data)

                # Try to parse as video if it looks like a video URL
                video = self._try_parse_video(result, query)
                if video:
                    videos.append(video)

            return ToolResult.ok({
                "results": results,
                "videos": [v.model_dump(mode="json") for v in videos] if videos else [],
                "total_results": len(results),
                "videos_found": len(videos),
                "query": query,
            })

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                return ToolResult.fail(f"Exa rate limit exceeded: {e}")
            elif "api key" in error_msg or "authentication" in error_msg:
                return ToolResult.fail(f"Exa authentication error: {e}")
            else:
                return ToolResult.fail(f"Exa search error: {e}")

    def _try_parse_video(self, result: Any, query: str) -> Video | None:
        """Try to parse Exa result as a Video if it's a video URL.

        Args:
            result: Exa search result.
            query: Original search query.

        Returns:
            Video model or None if not a video.
        """
        url = result.url
        platform = self._detect_platform(url)

        # Only create Video for recognized platforms or if URL strongly suggests video
        if platform == Platform.OTHER:
            # Check if URL path suggests video content
            video_indicators = ["/video", "/watch", "/embed", "/clip", "/reel"]
            if not any(indicator in url.lower() for indicator in video_indicators):
                return None

        platform_id = self._extract_platform_id(url, platform) or url

        # Parse publish date if available
        published_at = None
        if hasattr(result, "published_date") and result.published_date:
            try:
                published_at = datetime.fromisoformat(
                    result.published_date.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        return Video(
            platform=platform,
            platform_id=platform_id,
            url=url,
            title=result.title,
            description=getattr(result, "text", "")[:500] if hasattr(result, "text") else None,
            published_at=published_at,
            relevance_score=getattr(result, "score", None),
            source_query=query,
        )

    def _detect_platform(self, url: str) -> Platform:
        """Detect video platform from URL.

        Args:
            url: URL to check.

        Returns:
            Platform enum value.
        """
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return Platform.YOUTUBE
        elif "tiktok.com" in url_lower:
            return Platform.TIKTOK
        elif "instagram.com" in url_lower:
            return Platform.INSTAGRAM
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return Platform.TWITTER
        elif "facebook.com" in url_lower or "fb.com" in url_lower or "fb.watch" in url_lower:
            return Platform.FACEBOOK
        else:
            return Platform.OTHER

    def _extract_platform_id(self, url: str, platform: Platform) -> str | None:
        """Extract platform-specific video ID from URL.

        Args:
            url: Video URL.
            platform: Detected platform.

        Returns:
            Video ID or None.
        """
        if platform == Platform.YOUTUBE:
            # youtube.com/watch?v=ID or youtu.be/ID
            match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
            return match.group(1) if match else None
        elif platform == Platform.TIKTOK:
            # tiktok.com/@user/video/ID
            match = re.search(r"/video/(\d+)", url)
            return match.group(1) if match else None
        elif platform == Platform.INSTAGRAM:
            # instagram.com/reel/ID or /p/ID
            match = re.search(r"/(reel|p)/([A-Za-z0-9_-]+)", url)
            return match.group(2) if match else None
        elif platform == Platform.TWITTER:
            # twitter.com/user/status/ID
            match = re.search(r"/status/(\d+)", url)
            return match.group(1) if match else None
        return None


class ExaSimilarTool(BaseTool):
    """Tool for finding content similar to a given URL using Exa.ai."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Exa similarity tool.

        Args:
            api_key: Exa API key. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.exa_api_key
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy-load Exa client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("EXA_API_KEY is required for Exa similar search")
            from exa_py import Exa

            self._client = Exa(api_key=self.api_key)
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Exa API key is configured."""
        if not self.api_key:
            return False, "EXA_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "exa_find_similar"

    @property
    def description(self) -> str:
        return """Find web pages similar to a given URL.
Use this tool when:
- You have a good example video/article and want to find similar content
- User provides a reference URL and wants "more like this"
- Expanding search results to find related content
- Competitive analysis - finding similar content to a known piece

Works with any URL - video pages, articles, creator profiles, etc."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to find similar content for",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of similar results to return (1-25)",
                    "default": 10,
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Whether to extract page content for each result",
                    "default": False,
                },
                "exclude_source_domain": {
                    "type": "boolean",
                    "description": "Whether to exclude results from the source URL's domain",
                    "default": True,
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only include results from these domains",
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exclude results from these domains",
                },
                "start_published_date": {
                    "type": "string",
                    "description": "Filter results published after this date (YYYY-MM-DD format)",
                },
            },
            "required": ["url"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Find content similar to the given URL.

        Args:
            url: URL to find similar content for.
            num_results: Maximum results to return.
            include_content: Whether to extract page content.
            exclude_source_domain: Exclude the source URL's domain.
            include_domains: Only include these domains.
            exclude_domains: Exclude these domains.
            start_published_date: Filter by publish date.

        Returns:
            ToolResult with similar content results.
        """
        url = kwargs.get("url")
        if not url:
            return ToolResult.fail("URL is required")

        num_results = min(kwargs.get("num_results", 10), 25)
        include_content = kwargs.get("include_content", False)
        exclude_source_domain = kwargs.get("exclude_source_domain", True)
        include_domains = kwargs.get("include_domains")
        exclude_domains = kwargs.get("exclude_domains")
        start_published_date = kwargs.get("start_published_date")

        try:
            # Build search parameters
            search_kwargs: dict[str, Any] = {
                "num_results": num_results,
                "exclude_source_domain": exclude_source_domain,
            }

            if include_domains:
                search_kwargs["include_domains"] = include_domains
            if exclude_domains:
                search_kwargs["exclude_domains"] = exclude_domains
            if start_published_date:
                search_kwargs["start_published_date"] = start_published_date

            # Execute similarity search
            if include_content:
                search_kwargs["text"] = True
                response = await asyncio.to_thread(
                    self.client.find_similar_and_contents, url, **search_kwargs
                )
            else:
                response = await asyncio.to_thread(
                    self.client.find_similar, url, **search_kwargs
                )

            # Parse results
            results = []
            for result in response.results:
                text = getattr(result, "text", "") if hasattr(result, "text") else ""
                result_data = {
                    "url": result.url,
                    "title": result.title,
                    "snippet": text[:300] if text else None,
                    "published_date": getattr(result, "published_date", None),
                    "score": getattr(result, "score", None),
                }

                if include_content and text:
                    result_data["content"] = text

                results.append(result_data)

            return ToolResult.ok({
                "results": results,
                "total_results": len(results),
                "source_url": url,
            })

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                return ToolResult.fail(f"Exa rate limit exceeded: {e}")
            elif "api key" in error_msg or "authentication" in error_msg:
                return ToolResult.fail(f"Exa authentication error: {e}")
            else:
                return ToolResult.fail(f"Exa find similar error: {e}")


class ExaContentTool(BaseTool):
    """Tool for extracting content from specific URLs using Exa.ai."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Exa content extraction tool.

        Args:
            api_key: Exa API key. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.exa_api_key
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy-load Exa client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("EXA_API_KEY is required for Exa content extraction")
            from exa_py import Exa

            self._client = Exa(api_key=self.api_key)
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Exa API key is configured."""
        if not self.api_key:
            return False, "EXA_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "exa_get_content"

    @property
    def description(self) -> str:
        return """Extract content (text/markdown) from specific URLs.
Use this tool when:
- Need to analyze the full content of a page found in search results
- User provides a URL and wants detailed information extracted
- Need to read article/blog content about videos or creators
- Want to get the full text of a web page for analysis

Returns clean, parsed content from web pages."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs to extract content from (1-10 URLs)",
                },
            },
            "required": ["urls"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Extract content from specified URLs.

        Args:
            urls: List of URLs to extract content from.

        Returns:
            ToolResult with extracted content for each URL.
        """
        urls = kwargs.get("urls")
        if not urls:
            return ToolResult.fail("URLs list is required")

        if not isinstance(urls, list):
            urls = [urls]

        # Limit to 10 URLs
        urls = urls[:10]

        try:
            # Execute content extraction
            response = await asyncio.to_thread(
                self.client.get_contents, urls
            )

            # Parse results
            results = []
            for result in response.results:
                result_data = {
                    "url": result.url,
                    "title": result.title,
                    "content": getattr(result, "text", None),
                    "published_date": getattr(result, "published_date", None),
                }
                results.append(result_data)

            return ToolResult.ok({
                "results": results,
                "total_extracted": len(results),
            })

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                return ToolResult.fail(f"Exa rate limit exceeded: {e}")
            elif "api key" in error_msg or "authentication" in error_msg:
                return ToolResult.fail(f"Exa authentication error: {e}")
            else:
                return ToolResult.fail(f"Exa content extraction error: {e}")


class ExaResearchTool(BaseTool):
    """Tool for deep research tasks using Exa.ai's research API."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Exa research tool.

        Args:
            api_key: Exa API key. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.exa_api_key
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy-load Exa client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("EXA_API_KEY is required for Exa research")
            from exa_py import Exa

            self._client = Exa(api_key=self.api_key)
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Exa API key is configured."""
        if not self.api_key:
            return False, "EXA_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "exa_research"

    @property
    def description(self) -> str:
        return """Conduct deep research on a topic with AI-powered synthesis.
Use this tool for:
- Comprehensive brand or creator research
- Trend analysis requiring multiple source synthesis
- Complex questions needing thorough investigation
- When user explicitly asks for "research" or "in-depth analysis"

Returns structured research output with citations and sources.
More thorough but slower than exa_search - use for complex queries only."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Research question or topic to investigate",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute deep research on a topic.

        Args:
            query: Research question or topic.

        Returns:
            ToolResult with research findings and citations.
        """
        query = kwargs.get("query")
        if not query:
            return ToolResult.fail("Research query is required")

        try:
            # Use the answer endpoint for research-style queries
            # This provides a synthesized answer with sources
            response = await asyncio.to_thread(
                self.client.answer, query, text=True
            )

            # Format the response
            result = {
                "query": query,
                "answer": response.answer if hasattr(response, "answer") else str(response),
                "sources": [],
            }

            # Extract source citations if available
            if hasattr(response, "results"):
                for source in response.results:
                    text = getattr(source, "text", "") if hasattr(source, "text") else ""
                    result["sources"].append({
                        "url": source.url,
                        "title": source.title,
                        "snippet": text[:300] if text else None,
                    })

            return ToolResult.ok(result)

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                return ToolResult.fail(f"Exa rate limit exceeded: {e}")
            elif "api key" in error_msg or "authentication" in error_msg:
                return ToolResult.fail(f"Exa authentication error: {e}")
            else:
                return ToolResult.fail(f"Exa research error: {e}")
