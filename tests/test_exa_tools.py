"""Tests for Exa.ai integration tools."""

from unittest.mock import MagicMock, patch

import pytest

from video_searching_agent.models.video import Platform
from video_searching_agent.tools.exa import (
    ExaContentTool,
    ExaResearchTool,
    ExaSearchTool,
    ExaSimilarTool,
)


class TestExaSearchTool:
    """Tests for ExaSearchTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = ExaSearchTool()
        assert tool.name == "exa_search"
        assert "neural" in tool.description.lower() or "semantic" in tool.description.lower()
        assert "query" in tool.input_schema["required"]
        assert "num_results" in tool.input_schema["properties"]
        assert "search_type" in tool.input_schema["properties"]
        assert "include_domains" in tool.input_schema["properties"]
        assert "exclude_domains" in tool.input_schema["properties"]

    def test_search_type_enum(self):
        """Test search_type has valid enum values."""
        tool = ExaSearchTool()
        search_type = tool.input_schema["properties"]["search_type"]
        assert "neural" in search_type["enum"]
        assert "keyword" in search_type["enum"]
        assert "auto" in search_type["enum"]

    def test_input_validation_missing_query(self):
        """Test validation fails without query."""
        tool = ExaSearchTool()
        is_valid, error = tool.validate_input()
        assert not is_valid
        assert "query" in error.lower()

    def test_input_validation_success(self):
        """Test validation succeeds with query."""
        tool = ExaSearchTool()
        is_valid, error = tool.validate_input(query="test query")
        assert is_valid
        assert error is None

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test execute fails with missing query."""
        tool = ExaSearchTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_api_key(self):
        """Test execute fails without API key."""
        tool = ExaSearchTool(api_key=None)
        # Override the lazy-loaded client to force the check
        tool._client = None

        with patch.object(tool, 'api_key', None):
            result = await tool.execute(query="test")
            assert not result.success
            assert "api key" in result.error.lower() or "exa" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful search with mocked client."""
        tool = ExaSearchTool(api_key="test_key")

        # Create mock Exa response
        mock_result = MagicMock()
        mock_result.url = "https://example.com/video"
        mock_result.title = "Test Video"
        mock_result.text = "This is a test video description"
        mock_result.published_date = "2024-01-15"
        mock_result.score = 0.95

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        # Mock the client
        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(query="test video content")

        assert result.success
        assert "results" in result.data
        assert len(result.data["results"]) == 1
        assert result.data["results"][0]["url"] == "https://example.com/video"
        assert result.data["total_results"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_content_extraction(self):
        """Test search with content extraction enabled."""
        tool = ExaSearchTool(api_key="test_key")

        mock_result = MagicMock()
        mock_result.url = "https://example.com/article"
        mock_result.title = "Test Article"
        mock_result.text = "Full article content here..."
        mock_result.published_date = None
        mock_result.score = 0.8

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.search_and_contents = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(query="test", include_content=True)

        assert result.success
        mock_client.search_and_contents.assert_called_once()
        assert result.data["results"][0]["content"] == "Full article content here..."

    @pytest.mark.asyncio
    async def test_execute_with_domain_filters(self):
        """Test search with domain filtering."""
        tool = ExaSearchTool(api_key="test_key")

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(
            query="test",
            include_domains=["vimeo.com", "dailymotion.com"],
            exclude_domains=["youtube.com"],
        )

        assert result.success
        # Check domains were passed (exact arg checking depends on SDK)

    @pytest.mark.asyncio
    async def test_execute_rate_limit_error(self):
        """Test handling of rate limit errors."""
        tool = ExaSearchTool(api_key="test_key")

        mock_client = MagicMock()
        mock_client.search = MagicMock(side_effect=Exception("Rate limit exceeded"))
        tool._client = mock_client

        result = await tool.execute(query="test")

        assert not result.success
        assert "rate limit" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_auth_error(self):
        """Test handling of authentication errors."""
        tool = ExaSearchTool(api_key="test_key")

        mock_client = MagicMock()
        mock_client.search = MagicMock(side_effect=Exception("Invalid API key"))
        tool._client = mock_client

        result = await tool.execute(query="test")

        assert not result.success
        assert "authentication" in result.error.lower() or "api key" in result.error.lower()


class TestExaSearchToolPlatformDetection:
    """Tests for platform detection from URLs."""

    def test_youtube_detection(self):
        """Test YouTube URL detection."""
        tool = ExaSearchTool()
        assert tool._detect_platform("https://youtube.com/watch?v=abc") == Platform.YOUTUBE
        assert tool._detect_platform("https://www.youtube.com/watch?v=abc") == Platform.YOUTUBE
        assert tool._detect_platform("https://youtu.be/abc") == Platform.YOUTUBE

    def test_tiktok_detection(self):
        """Test TikTok URL detection."""
        tool = ExaSearchTool()
        assert tool._detect_platform("https://tiktok.com/@user/video/123") == Platform.TIKTOK
        assert tool._detect_platform("https://www.tiktok.com/@user/video/123") == Platform.TIKTOK

    def test_instagram_detection(self):
        """Test Instagram URL detection."""
        tool = ExaSearchTool()
        assert tool._detect_platform("https://instagram.com/reel/ABC") == Platform.INSTAGRAM
        assert tool._detect_platform("https://www.instagram.com/p/XYZ") == Platform.INSTAGRAM

    def test_twitter_detection(self):
        """Test Twitter/X URL detection."""
        tool = ExaSearchTool()
        assert tool._detect_platform("https://twitter.com/user/status/123") == Platform.TWITTER
        assert tool._detect_platform("https://x.com/user/status/456") == Platform.TWITTER

    def test_facebook_detection(self):
        """Test Facebook URL detection."""
        tool = ExaSearchTool()
        assert tool._detect_platform("https://facebook.com/video/123") == Platform.FACEBOOK
        assert tool._detect_platform("https://fb.watch/abc") == Platform.FACEBOOK

    def test_other_detection(self):
        """Test other platform detection."""
        tool = ExaSearchTool()
        assert tool._detect_platform("https://vimeo.com/123") == Platform.OTHER
        assert tool._detect_platform("https://dailymotion.com/video/abc") == Platform.OTHER
        assert tool._detect_platform("https://example.com/article") == Platform.OTHER


class TestExaSearchToolIdExtraction:
    """Tests for platform-specific ID extraction."""

    def test_youtube_id_extraction(self):
        """Test YouTube video ID extraction."""
        tool = ExaSearchTool()
        assert tool._extract_platform_id(
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            Platform.YOUTUBE
        ) == "dQw4w9WgXcQ"
        assert tool._extract_platform_id(
            "https://youtu.be/dQw4w9WgXcQ",
            Platform.YOUTUBE
        ) == "dQw4w9WgXcQ"

    def test_tiktok_id_extraction(self):
        """Test TikTok video ID extraction."""
        tool = ExaSearchTool()
        assert tool._extract_platform_id(
            "https://tiktok.com/@user/video/7123456789012345678",
            Platform.TIKTOK
        ) == "7123456789012345678"

    def test_instagram_id_extraction(self):
        """Test Instagram post ID extraction."""
        tool = ExaSearchTool()
        assert tool._extract_platform_id(
            "https://instagram.com/reel/ABC123xyz/",
            Platform.INSTAGRAM
        ) == "ABC123xyz"
        assert tool._extract_platform_id(
            "https://instagram.com/p/XYZ789/",
            Platform.INSTAGRAM
        ) == "XYZ789"

    def test_twitter_id_extraction(self):
        """Test Twitter status ID extraction."""
        tool = ExaSearchTool()
        assert tool._extract_platform_id(
            "https://twitter.com/user/status/1234567890123456789",
            Platform.TWITTER
        ) == "1234567890123456789"


class TestExaSearchToolVideoConversion:
    """Tests for converting Exa results to Video models."""

    @pytest.mark.asyncio
    async def test_video_url_converted(self):
        """Test that video URLs are converted to Video models."""
        tool = ExaSearchTool(api_key="test_key")

        # YouTube IDs are always 11 characters
        mock_result = MagicMock()
        mock_result.url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        mock_result.title = "Test YouTube Video"
        mock_result.text = "Video description"
        mock_result.published_date = "2024-01-15"
        mock_result.score = 0.9

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(query="test")

        assert result.success
        assert len(result.data["videos"]) == 1
        assert result.data["videos"][0]["platform"] == "youtube"
        assert result.data["videos"][0]["platform_id"] == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_non_video_url_not_converted(self):
        """Test that non-video URLs are not converted to Video models."""
        tool = ExaSearchTool(api_key="test_key")

        mock_result = MagicMock()
        mock_result.url = "https://example.com/article"
        mock_result.title = "Test Article"
        mock_result.text = "Article content"
        mock_result.published_date = None
        mock_result.score = 0.8

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(query="test")

        assert result.success
        assert len(result.data["videos"]) == 0
        assert len(result.data["results"]) == 1


class TestExaSimilarTool:
    """Tests for ExaSimilarTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = ExaSimilarTool()
        assert tool.name == "exa_find_similar"
        assert "similar" in tool.description.lower()
        assert "url" in tool.input_schema["required"]
        assert "num_results" in tool.input_schema["properties"]
        assert "exclude_source_domain" in tool.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute fails with missing URL."""
        tool = ExaSimilarTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower() or "url" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful similarity search."""
        tool = ExaSimilarTool(api_key="test_key")

        mock_result = MagicMock()
        mock_result.url = "https://similar.com/page"
        mock_result.title = "Similar Page"
        mock_result.text = "Similar content"
        mock_result.published_date = None
        mock_result.score = 0.85

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.find_similar = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(url="https://example.com/original")

        assert result.success
        assert "results" in result.data
        assert len(result.data["results"]) == 1
        assert result.data["source_url"] == "https://example.com/original"

    @pytest.mark.asyncio
    async def test_execute_with_content(self):
        """Test similarity search with content extraction."""
        tool = ExaSimilarTool(api_key="test_key")

        mock_result = MagicMock()
        mock_result.url = "https://similar.com/page"
        mock_result.title = "Similar Page"
        mock_result.text = "Full similar content..."
        mock_result.published_date = None
        mock_result.score = 0.85

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.find_similar_and_contents = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(url="https://example.com", include_content=True)

        assert result.success
        mock_client.find_similar_and_contents.assert_called_once()


class TestExaContentTool:
    """Tests for ExaContentTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = ExaContentTool()
        assert tool.name == "exa_get_content"
        assert "content" in tool.description.lower() or "extract" in tool.description.lower()
        assert "urls" in tool.input_schema["required"]

    @pytest.mark.asyncio
    async def test_execute_missing_urls(self):
        """Test execute fails with missing URLs."""
        tool = ExaContentTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower() or "url" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful content extraction."""
        tool = ExaContentTool(api_key="test_key")

        mock_result = MagicMock()
        mock_result.url = "https://example.com/page"
        mock_result.title = "Page Title"
        mock_result.text = "Extracted page content..."
        mock_result.published_date = "2024-01-15"

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = MagicMock()
        mock_client.get_contents = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(urls=["https://example.com/page"])

        assert result.success
        assert "results" in result.data
        assert len(result.data["results"]) == 1
        assert result.data["results"][0]["content"] == "Extracted page content..."

    @pytest.mark.asyncio
    async def test_execute_limits_urls(self):
        """Test that URLs are limited to 10."""
        tool = ExaContentTool(api_key="test_key")

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = MagicMock()
        mock_client.get_contents = MagicMock(return_value=mock_response)
        tool._client = mock_client

        # Pass 15 URLs
        urls = [f"https://example.com/page{i}" for i in range(15)]
        result = await tool.execute(urls=urls)

        assert result.success
        # Verify only first 10 were passed
        call_args = mock_client.get_contents.call_args
        assert len(call_args[0][0]) == 10


class TestExaResearchTool:
    """Tests for ExaResearchTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = ExaResearchTool()
        assert tool.name == "exa_research"
        assert "research" in tool.description.lower()
        assert "query" in tool.input_schema["required"]

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test execute fails with missing query."""
        tool = ExaResearchTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful research query."""
        tool = ExaResearchTool(api_key="test_key")

        mock_source = MagicMock()
        mock_source.url = "https://source.com/article"
        mock_source.title = "Source Article"
        mock_source.text = "Source content snippet"

        mock_response = MagicMock()
        mock_response.answer = "Research findings based on multiple sources..."
        mock_response.results = [mock_source]

        mock_client = MagicMock()
        mock_client.answer = MagicMock(return_value=mock_response)
        tool._client = mock_client

        result = await tool.execute(query="What are the latest trends in video marketing?")

        assert result.success
        assert "answer" in result.data
        assert "sources" in result.data
        assert len(result.data["sources"]) == 1


class TestExaToolFallbacks:
    """Tests for Exa tool fallback configuration."""

    def test_apify_tools_fallback_config(self):
        """Test that Apify-based tools have proper fallback chains configured.

        With the new Apify architecture:
        - TikTok, Instagram use Apify directly (no fallbacks needed)
        - Twitter has exa fallback
        - Exa tools have internal fallbacks
        """
        from video_searching_agent.tools.retry import TOOL_FALLBACKS

        # Twitter still has exa fallback
        assert "exa_search" in TOOL_FALLBACKS.get("twitter_search", [])

        # TikTok and Instagram tools don't need fallbacks - they use Apify
        # (they're not in TOOL_FALLBACKS, which is correct)
        assert "tiktok_search" not in TOOL_FALLBACKS
        assert "instagram_search" not in TOOL_FALLBACKS

    def test_exa_similar_falls_back_to_search(self):
        """Test that exa_find_similar falls back to exa_search."""
        from video_searching_agent.tools.retry import TOOL_FALLBACKS

        assert "exa_search" in TOOL_FALLBACKS.get("exa_find_similar", [])

    def test_exa_research_falls_back_to_search(self):
        """Test that exa_research falls back to exa_search."""
        from video_searching_agent.tools.retry import TOOL_FALLBACKS

        assert "exa_search" in TOOL_FALLBACKS.get("exa_research", [])


class TestExaToolRegistration:
    """Tests for Exa tool registration in agent."""

    def test_exa_tools_registered(self):
        """Test that all Exa tools are registered in the agent."""
        # Import here to avoid circular imports during test collection
        from video_searching_agent.agent.core import VideoSearchingAgent

        # Note: This test requires mocking settings to avoid requiring API keys
        with patch("video_searching_agent.agent.core.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                google_api_key="test",
                youtube_api_key="test",
                memories_api_key="test",
                exa_api_key="test",
                max_agent_steps=10,
            )

            agent = VideoSearchingAgent()
            tool_names = agent.tools.list_tools()

            assert "exa_search" in tool_names
            assert "exa_find_similar" in tool_names
            assert "exa_get_content" in tool_names
            assert "exa_research" in tool_names

    def test_web_search_not_registered(self):
        """Test that old web_search tool is not registered."""
        from video_searching_agent.agent.core import VideoSearchingAgent

        with patch("video_searching_agent.agent.core.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                google_api_key="test",
                youtube_api_key="test",
                memories_api_key="test",
                exa_api_key="test",
                max_agent_steps=10,
            )

            agent = VideoSearchingAgent()
            tool_names = agent.tools.list_tools()

            assert "web_search" not in tool_names

    def test_create_default_registry_uses_exa_tools(self):
        """Test create_default_registry registers Exa tools and no legacy web_search."""
        from video_searching_agent.tools.registry import create_default_registry

        registry = create_default_registry()
        tool_names = registry.list_tools()

        assert "web_search" not in tool_names
        assert "exa_search" in tool_names
        assert "exa_find_similar" in tool_names
