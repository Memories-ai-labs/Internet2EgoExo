"""Tests for YouTube tools."""

from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from video_searching_agent.tools.youtube import YouTubeChannelTool, YouTubeSearchTool


class TestMissingCredentials:
    """A missing key must say which key, not leak a Google Cloud error.

    Seen live: with no key configured, `googleapiclient` fell back to
    Application Default Credentials and the agent was told "Your default
    credentials were not found ... set up ADC", which names neither the tool nor
    the key it wants.
    """

    @pytest.fixture
    def unconfigured(self, monkeypatch):
        from video_searching_agent.config import settings as settings_module

        monkeypatch.setenv("YOUTUBE_API_KEY", "")
        settings_module.get_settings.cache_clear()
        yield
        settings_module.get_settings.cache_clear()

    def test_no_key_says_which_key_is_missing(self, unconfigured):
        with pytest.raises(ValueError, match="YOUTUBE_API_KEY is not configured"):
            YouTubeSearchTool().youtube

    def test_the_channel_tool_says_the_same(self, unconfigured):
        with pytest.raises(ValueError, match="YOUTUBE_API_KEY is not configured"):
            YouTubeChannelTool().youtube

    def test_health_reports_it_too(self, unconfigured):
        healthy, reason = YouTubeSearchTool().health_check()
        assert healthy is False
        assert reason == "YOUTUBE_API_KEY is not configured"

    def test_a_configured_key_still_builds_a_client(self):
        tool = YouTubeSearchTool(api_key="a-key")
        with patch("video_searching_agent.tools.youtube.build") as build:
            assert tool.youtube is build.return_value
            build.assert_called_once_with("youtube", "v3", developerKey="a-key")


class TestYouTubeSearchTool:
    """Tests for YouTube search tool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = YouTubeSearchTool(api_key="test_key")
        assert tool.name == "youtube_search"
        assert "YouTube" in tool.description
        assert "query" in tool.input_schema["required"]
        assert "search_type" in tool.input_schema["properties"]
        assert "max_results" in tool.input_schema["properties"]

    def test_input_schema_has_search_type_enum(self):
        """Test that search_type has valid enum values."""
        tool = YouTubeSearchTool(api_key="test_key")
        search_type = tool.input_schema["properties"]["search_type"]
        assert "video" in search_type["enum"]
        assert "channel" in search_type["enum"]
        assert "playlist" in search_type["enum"]

    def test_health_check_with_api_key(self):
        """Test health check passes with API key configured."""
        tool = YouTubeSearchTool(api_key="test_key")
        is_healthy, error = tool.health_check()
        assert is_healthy is True
        assert error is None

    def test_health_check_without_api_key(self):
        """Test health check fails without API key."""
        with patch("video_searching_agent.tools.youtube.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = None
            tool = YouTubeSearchTool(api_key=None)
            is_healthy, error = tool.health_check()
            assert is_healthy is False
            assert "YOUTUBE_API_KEY" in error

    def test_parse_duration_hours_minutes_seconds(self):
        """Test ISO 8601 duration parsing with hours, minutes, seconds."""
        tool = YouTubeSearchTool(api_key="test_key")
        # PT1H2M3S = 1 hour, 2 minutes, 3 seconds = 3600 + 120 + 3 = 3723
        assert tool._parse_duration("PT1H2M3S") == 3723

    def test_parse_duration_minutes_seconds(self):
        """Test ISO 8601 duration parsing with minutes and seconds."""
        tool = YouTubeSearchTool(api_key="test_key")
        # PT4M13S = 4 minutes, 13 seconds = 240 + 13 = 253
        assert tool._parse_duration("PT4M13S") == 253

    def test_parse_duration_seconds_only(self):
        """Test ISO 8601 duration parsing with seconds only."""
        tool = YouTubeSearchTool(api_key="test_key")
        # PT45S = 45 seconds
        assert tool._parse_duration("PT45S") == 45

    def test_parse_duration_minutes_only(self):
        """Test ISO 8601 duration parsing with minutes only."""
        tool = YouTubeSearchTool(api_key="test_key")
        # PT10M = 10 minutes = 600 seconds
        assert tool._parse_duration("PT10M") == 600

    def test_parse_duration_invalid(self):
        """Test duration parsing with invalid input."""
        tool = YouTubeSearchTool(api_key="test_key")
        assert tool._parse_duration("") is None
        assert tool._parse_duration("invalid") is None

    def test_extract_hashtags(self):
        """Test hashtag extraction from text."""
        tool = YouTubeSearchTool(api_key="test_key")
        text = "Check out this video! #cooking #food #recipe #viral"
        hashtags = tool._extract_hashtags(text)
        assert "cooking" in hashtags
        assert "food" in hashtags
        assert "recipe" in hashtags
        assert "viral" in hashtags

    def test_extract_hashtags_limit(self):
        """Test hashtag extraction limits to 10."""
        tool = YouTubeSearchTool(api_key="test_key")
        text = " ".join([f"#{i}" for i in range(20)])  # 20 hashtags
        hashtags = tool._extract_hashtags(text)
        assert len(hashtags) <= 10

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful search with mocked client."""
        tool = YouTubeSearchTool(api_key="test_key")

        # Mock the YouTube API client
        mock_search_response = {
            "items": [{"id": {"videoId": "abc123"}, "snippet": {"title": "Test Video"}}]
        }
        mock_video_response = {
            "items": [
                {
                    "id": "abc123",
                    "snippet": {
                        "title": "Test Video",
                        "description": "A test video",
                        "channelTitle": "Test Channel",
                        "channelId": "UC123",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
                    },
                    "statistics": {
                        "viewCount": "10000",
                        "likeCount": "500",
                        "commentCount": "50",
                    },
                    "contentDetails": {
                        "duration": "PT5M30S",
                    },
                }
            ]
        }

        mock_youtube = MagicMock()
        mock_youtube.search().list().execute.return_value = mock_search_response
        mock_youtube.videos().list().execute.return_value = mock_video_response
        tool._youtube = mock_youtube

        result = await tool.execute(query="test query")

        assert result.success
        assert "videos" in result.data
        assert len(result.data["videos"]) == 1
        assert result.data["videos"][0]["title"] == "Test Video"

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of YouTube API HTTP errors."""
        tool = YouTubeSearchTool(api_key="test_key")

        mock_youtube = MagicMock()
        mock_youtube.search().list().execute.side_effect = HttpError(
            resp=MagicMock(status=403),
            content=b'{"error": {"message": "Quota exceeded"}}',
        )
        tool._youtube = mock_youtube

        result = await tool.execute(query="test query")

        assert not result.success
        assert "YouTube API error" in result.error

    @pytest.mark.asyncio
    async def test_execute_no_results(self):
        """Test handling of empty search results."""
        tool = YouTubeSearchTool(api_key="test_key")

        mock_youtube = MagicMock()
        mock_youtube.search().list().execute.return_value = {"items": []}
        tool._youtube = mock_youtube

        result = await tool.execute(query="very obscure query")

        assert result.success
        assert result.data["videos"] == []
        assert "No video" in result.data.get("message", "")


class TestYouTubeChannelTool:
    """Tests for YouTube channel tool."""

    def test_tool_properties(self):
        """Test tool name and schema."""
        tool = YouTubeChannelTool(api_key="test_key")
        assert tool.name == "youtube_channel_info"
        assert "channel" in tool.description.lower()

    def test_health_check_with_api_key(self):
        """Test health check passes with API key configured."""
        tool = YouTubeChannelTool(api_key="test_key")
        is_healthy, error = tool.health_check()
        assert is_healthy is True
        assert error is None

    def test_health_check_without_api_key(self):
        """Test health check fails without API key."""
        with patch("video_searching_agent.tools.youtube.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = None
            tool = YouTubeChannelTool(api_key=None)
            is_healthy, error = tool.health_check()
            assert is_healthy is False
            assert "YOUTUBE_API_KEY" in error

    @pytest.mark.asyncio
    async def test_execute_missing_params(self):
        """Test execute fails when neither channel_id nor username provided."""
        tool = YouTubeChannelTool(api_key="test_key")
        result = await tool.execute()
        assert not result.success
        assert "channel_id or username is required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success_by_channel_id(self):
        """Test successful channel lookup by ID."""
        tool = YouTubeChannelTool(api_key="test_key")

        mock_channel_response = {
            "items": [
                {
                    "id": "UC123",
                    "snippet": {
                        "title": "Test Channel",
                        "description": "A test channel",
                        "customUrl": "@testchannel",
                        "thumbnails": {"high": {"url": "https://example.com/avatar.jpg"}},
                    },
                    "statistics": {
                        "subscriberCount": "100000",
                        "videoCount": "50",
                        "viewCount": "5000000",
                    },
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UU123"},
                    },
                }
            ]
        }

        mock_playlist_response = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "video1"},
                        "title": "Recent Video 1",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    }
                }
            ]
        }

        mock_youtube = MagicMock()
        mock_youtube.channels().list().execute.return_value = mock_channel_response
        mock_youtube.playlistItems().list().execute.return_value = mock_playlist_response
        tool._youtube = mock_youtube

        result = await tool.execute(channel_id="UC123")

        assert result.success
        assert result.data["title"] == "Test Channel"
        assert result.data["subscriber_count"] == 100000

    @pytest.mark.asyncio
    async def test_execute_channel_not_found(self):
        """Test handling of channel not found."""
        tool = YouTubeChannelTool(api_key="test_key")

        mock_youtube = MagicMock()
        mock_youtube.channels().list().execute.return_value = {"items": []}
        tool._youtube = mock_youtube

        result = await tool.execute(channel_id="UC_nonexistent")

        assert not result.success
        assert "not found" in result.error.lower()


class TestWhenYouTubeSearchIsRateLimited:
    """The failure that produced "every result is TikTok".

    `search.list` costs 100 quota units against `videos.list`'s 1, so bursts of
    searches hit a rate limit long before the day's quota is spent. Google
    reports that burst with a message reading *"Quota exceeded for quota metric
    'Search Queries' and limit 'Search Queries per day'"* — which read as a
    spent day to both the retry classifier and to me, so nothing retried and
    nothing routed around it. The reason code is the only thing that tells them
    apart.
    """

    RESP = type("Resp", (), {"status": 403, "reason": "Forbidden"})

    BURST = (
        b'{"error": {"code": 403, "message": "Quota exceeded for quota metric '
        b"'Search Queries' and limit 'Search Queries per day'\", "
        b'"errors": [{"reason": "rateLimitExceeded", "domain": "usageLimits"}]}}'
    )
    DAILY = (
        b'{"error": {"code": 403, "message": "Quota exceeded for quota metric '
        b'\'Queries\'", "errors": [{"reason": "quotaExceeded"}]}}'
    )

    def _error(self, body: bytes):
        from googleapiclient.errors import HttpError

        return HttpError(self.RESP(), body)

    def test_the_reason_code_is_read_not_the_sentence(self):
        from video_searching_agent.tools.youtube import (
            _BURST_REASONS,
            _DAILY_REASONS,
            _http_error_reason,
        )

        burst = _http_error_reason(self._error(self.BURST))
        daily = _http_error_reason(self._error(self.DAILY))
        assert burst == "rateLimitExceeded"
        assert burst in _BURST_REASONS and burst not in _DAILY_REASONS
        assert daily == "quotaExceeded"
        assert daily in _DAILY_REASONS and daily not in _BURST_REASONS

    def test_a_malformed_error_body_does_not_raise(self):
        from video_searching_agent.tools.youtube import _http_error_reason

        assert _http_error_reason(self._error(b"not json at all")) == "http403"

    @pytest.mark.asyncio
    async def test_a_burst_limit_falls_back_to_exa(self, monkeypatch):
        """Exa finds them; the YouTube API still describes them, at 1/100th."""

        from video_searching_agent.models.video import Platform, Video
        from video_searching_agent.tools.youtube import YouTubeSearchTool

        tool = YouTubeSearchTool(api_key="a-key")

        async def rate_limited(request):
            raise self._error(self.BURST)

        described: list[list[str]] = []

        async def describe(video_ids, query):
            described.append(list(video_ids))
            return [
                Video(
                    platform=Platform.YOUTUBE,
                    platform_id=vid,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    title=f"clip {vid}",
                    license="creativeCommon" if vid == "aaa" else "youtube",
                    source_query=query,
                )
                for vid in video_ids
            ]

        class FakeExa:
            async def execute(self, **kwargs):
                from video_searching_agent.tools.base import ToolResult

                assert "youtube.com" in kwargs["include_domains"]
                return ToolResult.ok(
                    {
                        "results": [
                            {"url": "https://www.youtube.com/watch?v=aaa"},
                            {"url": "https://youtu.be/bbb"},
                            {"url": "https://example.com/not-a-video"},
                            {"url": "https://www.youtube.com/watch?v=aaa"},
                        ]
                    }
                )

        monkeypatch.setattr(
            "video_searching_agent.tools.exa.ExaSearchTool", lambda *a, **k: FakeExa()
        )
        tool._execute_request_locked = rate_limited
        tool._get_video_details = describe
        tool._youtube = _StubYouTubeApi()

        result = await tool.execute(query="pov cooking", max_results=5)
        assert result.success is True
        assert result.data["found_via"] == "exa"
        # Deduplicated, non-YouTube URLs dropped, both id shapes understood.
        assert described == [["aaa", "bbb"]]
        assert result.data["total_results"] == 2

    @pytest.mark.asyncio
    async def test_the_licence_filter_survives_the_fallback(self, monkeypatch):
        """Exa cannot filter by licence, so it is applied to what the API says."""

        from video_searching_agent.models.video import Platform, Video
        from video_searching_agent.tools.youtube import YouTubeSearchTool

        tool = YouTubeSearchTool(api_key="a-key")

        async def rate_limited(request):
            raise self._error(self.BURST)

        async def describe(video_ids, query):
            return [
                Video(
                    platform=Platform.YOUTUBE,
                    platform_id=vid,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    license="creativeCommon" if vid == "aaa" else "youtube",
                    source_query=query,
                )
                for vid in video_ids
            ]

        class FakeExa:
            async def execute(self, **kwargs):
                from video_searching_agent.tools.base import ToolResult

                return ToolResult.ok(
                    {
                        "results": [
                            {"url": "https://www.youtube.com/watch?v=aaa"},
                            {"url": "https://www.youtube.com/watch?v=bbb"},
                        ]
                    }
                )

        monkeypatch.setattr(
            "video_searching_agent.tools.exa.ExaSearchTool", lambda *a, **k: FakeExa()
        )
        tool._execute_request_locked = rate_limited
        tool._get_video_details = describe
        tool._youtube = _StubYouTubeApi()

        result = await tool.execute(query="pov cooking", max_results=5, license="reusable")
        assert [v["platform_id"] for v in result.data["videos"]] == ["aaa"]

    @pytest.mark.asyncio
    async def test_a_spent_daily_quota_does_not_pretend_otherwise(self, monkeypatch):
        """Routing around a spent day is pointless; say so instead."""

        from video_searching_agent.tools.youtube import YouTubeSearchTool

        tool = YouTubeSearchTool(api_key="a-key")

        async def exhausted(request):
            raise self._error(self.DAILY)

        called = []

        class FakeExa:
            async def execute(self, **kwargs):
                called.append(kwargs)
                raise AssertionError("should not reach Exa for a spent day")

        monkeypatch.setattr(
            "video_searching_agent.tools.exa.ExaSearchTool", lambda *a, **k: FakeExa()
        )
        tool._execute_request_locked = exhausted
        tool._youtube = _StubYouTubeApi()

        result = await tool.execute(query="pov cooking", max_results=5)
        assert result.success is False
        assert "quotaExceeded" in str(result.error)
        assert called == []

    @pytest.mark.asyncio
    async def test_no_exa_key_reports_the_original_youtube_failure(self, monkeypatch):
        """A confusing second error is worse than the first one."""

        from video_searching_agent.tools.youtube import YouTubeSearchTool

        tool = YouTubeSearchTool(api_key="a-key")

        async def rate_limited(request):
            raise self._error(self.BURST)

        def no_exa(*a, **k):
            raise RuntimeError("EXA_API_KEY is not configured")

        monkeypatch.setattr("video_searching_agent.tools.exa.ExaSearchTool", no_exa)
        tool._execute_request_locked = rate_limited
        tool._youtube = _StubYouTubeApi()

        result = await tool.execute(query="pov cooking", max_results=5)
        assert result.success is False
        assert "rateLimitExceeded" in str(result.error)


class _StubYouTubeApi:
    """Enough of the discovery client to build a request object."""

    def search(self):
        return self

    def list(self, **kwargs):
        return type("Request", (), {"uri": "https://youtube/search?x=1"})()
