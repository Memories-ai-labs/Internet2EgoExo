"""Tests for Apify-based platform tools (TikTok, Instagram, Twitter)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from video_searching_agent.api.apify_client import ApifyClient
from video_searching_agent.models.video import Platform
from video_searching_agent.tools.exa import extract_platform_urls
from video_searching_agent.tools.instagram_apify import (
    InstagramApifyCreatorTool,
    InstagramApifySearchTool,
)
from video_searching_agent.tools.tiktok_apify import (
    TikTokApifyCreatorTool,
    TikTokApifySearchTool,
)
from video_searching_agent.tools.twitter_apify import (
    TwitterApifyProfileTool,
    TwitterApifySearchTool,
)
from video_searching_agent.tools.video_search import VideoSearchTool


class TestApifyClient:
    """Tests for ApifyClient."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = ApifyClient(api_token="test_token")
        assert client.api_token == "test_token"
        assert client.base_url == "https://api.apify.com/v2"

    def test_actors_dict(self):
        """Test actors dictionary has expected platforms."""
        assert "tiktok" in ApifyClient.ACTORS
        assert "instagram" in ApifyClient.ACTORS
        assert "twitter" in ApifyClient.ACTORS

    @pytest.mark.asyncio
    async def test_scrape_tiktok_requires_input(self):
        """Test scrape_tiktok fails without required input."""
        client = ApifyClient(api_token="test")
        with pytest.raises(ValueError, match="Must provide"):
            await client.scrape_tiktok()

    @pytest.mark.asyncio
    async def test_scrape_instagram_requires_input(self):
        """Test scrape_instagram fails without required input."""
        client = ApifyClient(api_token="test")
        with pytest.raises(ValueError, match="Must provide"):
            await client.scrape_instagram()

    @pytest.mark.asyncio
    async def test_scrape_twitter_requires_input(self):
        """Test scrape_twitter fails without required input."""
        client = ApifyClient(api_token="test")
        with pytest.raises(ValueError, match="Must provide"):
            await client.scrape_twitter()

    @pytest.mark.asyncio
    async def test_scrape_instagram_keyword_query_is_sanitized(self):
        """Keyword Instagram queries should become sanitized hashtag URLs."""
        client = ApifyClient(api_token="test")
        client.run_actor = AsyncMock(return_value=[])  # type: ignore[method-assign]

        await client.scrape_instagram(query="AI breakthroughs 2026")

        input_data = client.run_actor.call_args.args[1]  # type: ignore[index]
        assert input_data["directUrls"] == [
            "https://www.instagram.com/explore/tags/AIbreakthroughs2026/"
        ]
        assert input_data["resultsType"] == "posts"

    @pytest.mark.asyncio
    async def test_scrape_instagram_hashtag_is_sanitized(self):
        """Hashtag Instagram queries should strip invalid characters."""
        client = ApifyClient(api_token="test")
        client.run_actor = AsyncMock(return_value=[])  # type: ignore[method-assign]

        await client.scrape_instagram(hashtag="#AI breakthroughs 2026!!!")

        input_data = client.run_actor.call_args.args[1]  # type: ignore[index]
        assert input_data["directUrls"] == [
            "https://www.instagram.com/explore/tags/AIbreakthroughs2026/"
        ]
        assert input_data["resultsType"] == "posts"

    @pytest.mark.asyncio
    async def test_run_actor_reuses_client_for_same_timeout(self):
        """Repeated actor runs with same timeout should reuse one AsyncClient."""
        client = ApifyClient(api_token="test")

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = [{"id": "1"}]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            await client.run_actor("clockworks/tiktok-scraper", {"q": "a"}, timeout_secs=120)
            await client.run_actor("clockworks/tiktok-scraper", {"q": "b"}, timeout_secs=120)

        assert mock_client.call_count == 1

    @pytest.mark.asyncio
    async def test_get_client_concurrent_first_use_reuses_single_instance(self):
        """Concurrent first-use should initialize one AsyncClient per timeout bucket."""
        client = ApifyClient(api_token="test")

        active_client = MagicMock()
        active_client.post = AsyncMock()

        async def delayed_enter():
            await asyncio.sleep(0.01)
            return active_client

        def build_raw_client(*args, **kwargs):
            del args, kwargs
            raw_client = MagicMock()
            raw_client.__aenter__.side_effect = delayed_enter
            raw_client.aclose = AsyncMock()
            return raw_client

        with patch("httpx.AsyncClient", side_effect=build_raw_client) as mock_client:
            await asyncio.gather(*[
                client._get_client(30.0)
                for _ in range(10)
            ])

        assert mock_client.call_count == 1


class TestTikTokApifySearchTool:
    """Tests for TikTok Apify search tool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = TikTokApifySearchTool()
        assert tool.name == "tiktok_search"
        assert "TikTok" in tool.description
        assert "query" in tool.input_schema["required"]
        assert "search_type" in tool.input_schema["properties"]

    def test_input_schema_has_search_type_enum(self):
        """Test that search_type has valid enum values."""
        tool = TikTokApifySearchTool()
        search_type = tool.input_schema["properties"]["search_type"]
        assert "keyword" in search_type["enum"]
        assert "hashtag" in search_type["enum"]
        assert "user" in search_type["enum"]

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test execute fails with missing query."""
        tool = TikTokApifySearchTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful search with mocked client."""
        tool = TikTokApifySearchTool()

        # Mock the Apify client
        mock_result = [
            {
                "id": "123",
                "webVideoUrl": "https://tiktok.com/@user/video/123",
                "desc": "Test video",
                "authorMeta": {
                    "name": "testuser",
                    "nickName": "Test User",
                    "fans": 10000,
                },
                "stats": {
                    "playCount": 50000,
                    "diggCount": 5000,
                    "commentCount": 100,
                    "shareCount": 50,
                },
                "challenges": [{"title": "fyp"}, {"title": "viral"}],
            }
        ]

        mock_client = MagicMock()
        mock_client.scrape_tiktok = AsyncMock(return_value=mock_result)
        tool._client = mock_client

        result = await tool.execute(query="test query")

        assert result.success
        assert result.data["platform"] == "tiktok"
        assert len(result.data["videos"]) == 1
        assert result.data["videos"][0]["platform"] == "tiktok"
        assert result.data["method"] == "apify"

    @pytest.mark.asyncio
    async def test_execute_hashtag_search(self):
        """Test hashtag search."""
        tool = TikTokApifySearchTool()

        mock_client = MagicMock()
        mock_client.scrape_tiktok = AsyncMock(return_value=[])
        tool._client = mock_client

        result = await tool.execute(query="#cooking")

        assert result.success or "No TikTok" in result.error
        mock_client.scrape_tiktok.assert_called_once()
        call_kwargs = mock_client.scrape_tiktok.call_args.kwargs
        assert call_kwargs.get("hashtag") == "cooking"

    @pytest.mark.asyncio
    async def test_execute_user_search(self):
        """Test user/creator search."""
        tool = TikTokApifySearchTool()

        mock_client = MagicMock()
        mock_client.scrape_tiktok = AsyncMock(return_value=[])
        tool._client = mock_client

        result = await tool.execute(query="@charlidamelio")

        assert result.success or "No TikTok" in result.error
        mock_client.scrape_tiktok.assert_called_once()
        call_kwargs = mock_client.scrape_tiktok.call_args.kwargs
        assert call_kwargs.get("username") == "charlidamelio"

    def test_parse_apify_results(self):
        """Test parsing Apify results into Video models."""
        tool = TikTokApifySearchTool()
        raw_results = [
            {
                "id": "123",
                "webVideoUrl": "https://tiktok.com/@user/video/123",
                "desc": "Test video",
                "authorMeta": {"name": "testuser"},
                "stats": {"playCount": 1000, "diggCount": 100},
            }
        ]
        videos, parse_stats = tool._parse_apify_results(raw_results, "test")
        assert len(videos) == 1
        assert videos[0].platform == Platform.TIKTOK
        assert videos[0].metrics.views == 1000
        assert parse_stats.successfully_parsed == 1
        assert parse_stats.failed_to_parse == 0


class TestTikTokApifyCreatorTool:
    """Tests for TikTok Apify creator tool."""

    def test_tool_properties(self):
        """Test tool name and schema."""
        tool = TikTokApifyCreatorTool()
        assert tool.name == "tiktok_creator_info"
        assert "username" in tool.input_schema["required"]

    @pytest.mark.asyncio
    async def test_execute_missing_username(self):
        """Test execute fails with missing username."""
        tool = TikTokApifyCreatorTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_strips_at_symbol(self):
        """Test that @ is stripped from username."""
        tool = TikTokApifyCreatorTool()

        mock_result = [
            {
                "id": "123",
                "authorMeta": {
                    "name": "testuser",
                    "fans": 10000,
                    "following": 100,
                    "heart": 500000,
                    "video": 50,
                },
            }
        ]

        mock_client = MagicMock()
        mock_client.scrape_tiktok = AsyncMock(return_value=mock_result)
        tool._client = mock_client

        result = await tool.execute(username="@testuser")

        assert result.success
        mock_client.scrape_tiktok.assert_called_once()
        call_kwargs = mock_client.scrape_tiktok.call_args.kwargs
        assert call_kwargs.get("username") == "testuser"


class TestInstagramApifySearchTool:
    """Tests for Instagram Apify search tool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = InstagramApifySearchTool()
        assert tool.name == "instagram_search"
        assert "Instagram" in tool.description
        assert "query" in tool.input_schema["required"]
        assert "search_type" in tool.input_schema["properties"]

    def test_search_type_enum(self):
        """Test search_type has valid enum values."""
        tool = InstagramApifySearchTool()
        search_type = tool.input_schema["properties"]["search_type"]
        assert "keyword" in search_type["enum"]
        assert "hashtag" in search_type["enum"]
        assert "user" in search_type["enum"]
        assert search_type["default"] == "keyword"

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful search."""
        tool = InstagramApifySearchTool()

        mock_result = [
            {
                "shortCode": "ABC123",
                "url": "https://instagram.com/reel/ABC123/",
                "caption": "Test reel",
                "ownerUsername": "instauser",
                "likesCount": 500,
                "commentsCount": 50,
            }
        ]

        mock_client = MagicMock()
        mock_client.scrape_instagram = AsyncMock(return_value=mock_result)
        tool._client = mock_client

        result = await tool.execute(query="#fitness")

        assert result.success
        assert result.data["platform"] == "instagram"
        assert result.data["method"] == "apify"

    @pytest.mark.asyncio
    async def test_execute_plain_query_uses_keyword_path(self):
        """Plain multi-word queries should use keyword path, not hashtag path."""
        tool = InstagramApifySearchTool()

        mock_result = [
            {
                "shortCode": "ABC123",
                "url": "https://instagram.com/reel/ABC123/",
                "caption": "Test reel",
                "ownerUsername": "instauser",
                "likesCount": 500,
                "commentsCount": 50,
            }
        ]

        mock_client = MagicMock()
        mock_client.scrape_instagram = AsyncMock(return_value=mock_result)
        tool._client = mock_client

        result = await tool.execute(query="AI breakthroughs 2026")

        assert result.success
        call_kwargs = mock_client.scrape_instagram.call_args.kwargs
        assert call_kwargs.get("query") == "AI breakthroughs 2026"
        assert "hashtag" not in call_kwargs

    @pytest.mark.asyncio
    async def test_execute_hashtag_query_is_sanitized(self):
        """Hashtag query should pass sanitized hashtag to client."""
        tool = InstagramApifySearchTool()

        mock_result = [
            {
                "shortCode": "ABC123",
                "url": "https://instagram.com/reel/ABC123/",
                "caption": "Test reel",
                "ownerUsername": "instauser",
                "likesCount": 500,
                "commentsCount": 50,
            }
        ]

        mock_client = MagicMock()
        mock_client.scrape_instagram = AsyncMock(return_value=mock_result)
        tool._client = mock_client

        result = await tool.execute(query="#AI breakthroughs 2026")

        assert result.success
        call_kwargs = mock_client.scrape_instagram.call_args.kwargs
        assert call_kwargs.get("hashtag") == "AIbreakthroughs2026"


class TestInstagramApifyCreatorTool:
    """Tests for Instagram Apify creator tool."""

    def test_tool_properties(self):
        """Test tool name and schema."""
        tool = InstagramApifyCreatorTool()
        assert tool.name == "instagram_creator_info"
        assert "username" in tool.input_schema["required"]


class TestTwitterApifySearchTool:
    """Tests for Twitter Apify search tool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = TwitterApifySearchTool()
        assert tool.name == "twitter_search"
        assert "Twitter" in tool.description or "X" in tool.description
        assert "query" in tool.input_schema["required"]

    def test_search_type_enum(self):
        """Test search_type has valid enum values."""
        tool = TwitterApifySearchTool()
        search_type = tool.input_schema["properties"]["search_type"]
        assert "keyword" in search_type["enum"]
        assert "hashtag" in search_type["enum"]
        assert "user" in search_type["enum"]

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful search."""
        tool = TwitterApifySearchTool()

        mock_result = [
            {
                "id": "123456",
                "url": "https://twitter.com/user/status/123456",
                "text": "Test tweet with video",
                "author": {
                    "userName": "twitteruser",
                    "followers": 5000,
                },
                "likeCount": 200,
                "retweetCount": 50,
                "isVideo": True,
            }
        ]

        mock_client = MagicMock()
        mock_client.scrape_twitter = AsyncMock(return_value=mock_result)
        tool._client = mock_client

        result = await tool.execute(query="tech news")

        assert result.success
        assert result.data["platform"] == "twitter"
        assert result.data["method"] == "apify"


class TestTwitterApifyProfileTool:
    """Tests for Twitter Apify profile tool."""

    def test_tool_properties(self):
        """Test tool name and schema."""
        tool = TwitterApifyProfileTool()
        assert tool.name == "twitter_profile_info"
        assert "username" in tool.input_schema["required"]


class TestExtractPlatformUrls:
    """Tests for URL extraction from Exa results."""

    def test_extract_tiktok_urls(self):
        """Test TikTok URL extraction."""
        results = [
            {"url": "https://www.tiktok.com/@user/video/123456"},
            {"url": "https://www.tiktok.com/tag/cooking"},  # Not a video URL
        ]
        platform_urls = extract_platform_urls(results)
        assert len(platform_urls[Platform.TIKTOK]) == 1
        assert "video/123456" in platform_urls[Platform.TIKTOK][0]

    def test_extract_instagram_urls(self):
        """Test Instagram URL extraction."""
        results = [
            {"url": "https://www.instagram.com/reel/ABC123/"},
            {"url": "https://www.instagram.com/p/XYZ789/"},
            {"url": "https://www.instagram.com/explore/"},  # Not a post URL
        ]
        platform_urls = extract_platform_urls(results)
        assert len(platform_urls[Platform.INSTAGRAM]) == 2

    def test_extract_twitter_urls(self):
        """Test Twitter URL extraction."""
        results = [
            {"url": "https://twitter.com/user/status/123456"},
            {"url": "https://x.com/user/status/789012"},
            {"url": "https://twitter.com/user"},  # Not a status URL
        ]
        platform_urls = extract_platform_urls(results)
        assert len(platform_urls[Platform.TWITTER]) == 2

    def test_extract_youtube_urls(self):
        """Test YouTube URL extraction."""
        results = [
            {"url": "https://www.youtube.com/watch?v=abc123"},
            {"url": "https://youtu.be/xyz789"},
            {"url": "https://www.youtube.com/shorts/short123"},
            {"url": "https://www.youtube.com/channel/UC123"},  # Not a video URL
        ]
        platform_urls = extract_platform_urls(results)
        assert len(platform_urls[Platform.YOUTUBE]) == 3

    def test_extract_mixed_urls(self):
        """Test extraction of mixed platform URLs."""
        results = [
            {"url": "https://www.tiktok.com/@user/video/123"},
            {"url": "https://www.instagram.com/reel/ABC/"},
            {"url": "https://twitter.com/user/status/456"},
            {"url": "https://www.youtube.com/watch?v=xyz"},
            {"url": "https://example.com/random-page"},  # No platform
        ]
        platform_urls = extract_platform_urls(results)
        assert len(platform_urls[Platform.TIKTOK]) == 1
        assert len(platform_urls[Platform.INSTAGRAM]) == 1
        assert len(platform_urls[Platform.TWITTER]) == 1
        assert len(platform_urls[Platform.YOUTUBE]) == 1


class TestVideoSearchTool:
    """Tests for unified video search tool."""

    def test_tool_properties(self):
        """Test tool name and schema."""
        tool = VideoSearchTool()
        assert tool.name == "video_search"
        assert "query" in tool.input_schema["required"]
        assert "platforms" in tool.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test execute fails with missing query."""
        tool = VideoSearchTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_exa_only(self):
        """Test search with Exa only (no URL scraping)."""
        tool = VideoSearchTool()

        # Mock Exa tool
        mock_exa_result = MagicMock()
        mock_exa_result.success = True
        mock_exa_result.data = {
            "results": [
                {"url": "https://tiktok.com/@user/video/123", "title": "Test"},
            ],
            "videos": [
                {"url": "https://tiktok.com/@user/video/123", "platform": "tiktok"},
            ],
        }

        mock_exa_tool = MagicMock()
        mock_exa_tool.execute = AsyncMock(return_value=mock_exa_result)
        tool._exa_tool = mock_exa_tool

        result = await tool.execute(query="cooking videos", scrape_urls=False)

        assert result.success
        assert result.data["method"] == "exa"
        assert "urls_discovered" in result.data
