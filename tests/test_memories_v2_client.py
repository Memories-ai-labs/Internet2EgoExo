"""Tests for Memories.ai v2 API client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from video_searching_agent.api.memories_v2_client import MemoriesV2Client


class TestMemoriesV2ClientInit:
    """Tests for MemoriesV2Client initialization."""

    def test_default_init(self):
        """Test client initialization with defaults."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_api_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            client = MemoriesV2Client()
            assert client.api_key == "test_api_key"
            assert client.base_url == "https://test.api.com/v2"
            assert client.default_channel == "memories.ai"
            assert client.timeout == 30

    def test_custom_init(self):
        """Test client initialization with custom values."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="default_key",
                memories_base_url="https://default.api.com/v2",
                memories_default_channel="apify",
                api_timeout_seconds=30,
            )
            client = MemoriesV2Client(
                api_key="custom_api_key",
                base_url="https://custom.api.com/v2/",
            )
            assert client.api_key == "custom_api_key"
            assert client.base_url == "https://custom.api.com/v2"  # Trailing slash stripped

    def test_init_strips_whitespace_values(self):
        """Client should normalize whitespace around key/base_url/channel."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="  settings_key  ",
                memories_base_url=" https://default.api.com/v2/ ",
                memories_default_channel=" memories.ai ",
                api_timeout_seconds=30,
            )

            client = MemoriesV2Client(
                api_key="  custom_api_key  ",
                base_url=" https://custom.api.com/v2/ ",
            )

        assert client.api_key == "custom_api_key"
        assert client.base_url == "https://custom.api.com/v2"
        assert client.default_channel == "memories.ai"

    def test_blank_custom_base_url_falls_back_to_settings_base_url(self):
        """Blank override base_url should not produce empty client base URL."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_api_key",
                memories_base_url="https://settings.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )

            client = MemoriesV2Client(base_url="   ")

        assert client.base_url == "https://settings.api.com/v2"

    def test_blank_settings_base_url_falls_back_to_builtin_default(self):
        """If settings base_url is blank, client should use builtin BASE_URL."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_api_key",
                memories_base_url="   ",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )

            client = MemoriesV2Client()

        assert client.base_url == MemoriesV2Client.BASE_URL

    def test_headers_no_bearer_prefix(self):
        """Test that authorization header does not use Bearer prefix."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_api_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            client = MemoriesV2Client()
            headers = client._headers()
            assert headers["Authorization"] == "test_api_key"
            assert "Bearer" not in headers["Authorization"]


class TestMemoriesV2ClientPlatformDetection:
    """Tests for platform detection from URLs."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    def test_youtube_detection(self, client):
        """Test YouTube URL detection."""
        assert client.detect_platform("https://youtube.com/watch?v=abc") == "youtube"
        assert client.detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
        assert client.detect_platform("https://youtu.be/abc") == "youtube"
        assert client.detect_platform("https://YOUTUBE.COM/watch?v=abc") == "youtube"

    def test_tiktok_detection(self, client):
        """Test TikTok URL detection."""
        assert client.detect_platform("https://tiktok.com/@user/video/123") == "tiktok"
        assert client.detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"

    def test_instagram_detection(self, client):
        """Test Instagram URL detection."""
        assert client.detect_platform("https://instagram.com/reel/ABC") == "instagram"
        assert client.detect_platform("https://www.instagram.com/p/XYZ") == "instagram"

    def test_twitter_detection(self, client):
        """Test Twitter/X URL detection."""
        assert client.detect_platform("https://twitter.com/user/status/123") == "twitter"
        assert client.detect_platform("https://x.com/user/status/456") == "twitter"
        assert client.detect_platform("https://X.COM/user/status/789") == "twitter"

    def test_unsupported_platform(self, client):
        """Test unsupported URL returns None."""
        assert client.detect_platform("https://vimeo.com/123") is None
        assert client.detect_platform("https://dailymotion.com/video/abc") is None
        assert client.detect_platform("https://example.com/video") is None


class TestMemoriesV2ClientYouTube:
    """Tests for YouTube-specific methods."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    @pytest.mark.asyncio
    async def test_get_youtube_metadata_success(self, client):
        """Test successful YouTube metadata extraction."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "title": "Test Video",
            "description": "Test description",
            "views": 1000000,
            "likes": 50000,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.get_youtube_metadata(
                "https://youtube.com/watch?v=abc123"
            )

        assert result["title"] == "Test Video"
        assert result["views"] == 1000000

    @pytest.mark.asyncio
    async def test_get_youtube_metadata_envelope_failure_raises(self, client):
        """API envelope failures (HTTP 200) should raise RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": "0409",
            "msg": "Service is busy, try later",
            "success": False,
            "failed": True,
            "data": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(RuntimeError) as exc_info:
                await client.get_youtube_metadata("https://youtube.com/watch?v=abc123")

        assert "code=0409" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_youtube_metadata_code_only_failure_raises(self, client):
        """Non-success code should fail even without explicit success/failed flags."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": "0429",
            "msg": "Rate limit exceeded",
            "data": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(RuntimeError) as exc_info:
                await client.get_youtube_metadata("https://youtube.com/watch?v=abc123")

        assert "code=0429" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_youtube_metadata_non_object_payload_raises(self, client):
        """Non-dict JSON payloads should raise a clear runtime error."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"unexpected": "shape"}]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(RuntimeError) as exc_info:
                await client.get_youtube_metadata("https://youtube.com/watch?v=abc123")

        assert "non-object response" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_youtube_transcript_success(self, client):
        """Test successful YouTube transcript extraction."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "Hello and welcome to this video...",
            "segments": [
                {"start": 0.0, "end": 3.5, "text": "Hello and welcome"},
                {"start": 3.5, "end": 7.0, "text": "to this video"},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.get_youtube_transcript(
                "https://youtube.com/watch?v=abc123"
            )

        assert "text" in result
        assert len(result["segments"]) == 2

    @pytest.mark.asyncio
    async def test_reuses_httpx_client_for_same_timeout(self, client):
        """Two metadata calls should reuse the same underlying AsyncClient."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Reuse test"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            await client.get_youtube_metadata("https://youtube.com/watch?v=one")
            await client.get_youtube_metadata("https://youtube.com/watch?v=two")

        assert mock_client.call_count == 1

    @pytest.mark.asyncio
    async def test_reuses_single_client_during_concurrent_first_use(self, client):
        """Concurrent first-use should still initialize only one AsyncClient."""
        active_client = MagicMock()
        active_client.post = AsyncMock(return_value=MagicMock())

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


class TestMemoriesV2ClientVLM:
    """Tests for VLM chat methods."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                memories_vlm_model="gemini:gemini-3-flash-preview",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    @pytest.mark.asyncio
    async def test_vlm_chat_success(self, client):
        """Test successful VLM chat completion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "text": "This video shows a cooking tutorial...",
                }
            ],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.vlm_chat(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "file_uri": "https://youtube.com/watch?v=abc",
                                "mime_type": "video/mp4",
                            },
                            {"type": "text", "text": "Describe this video"},
                        ],
                    }
                ],
                model="gemini:gemini-2.5-flash",
            )

        assert len(result["choices"]) == 1
        assert "cooking tutorial" in result["choices"][0]["text"]

    @pytest.mark.asyncio
    async def test_analyze_video_with_vlm_convenience(self, client):
        """Test convenience method for VLM video analysis."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "text": "Video analysis result...",
                }
            ],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.analyze_video_with_vlm(
                video_url="https://youtube.com/watch?v=abc",
                prompt="What is happening in this video?",
            )

        assert "choices" in result
        assert result["choices"][0]["text"] == "Video analysis result..."

    @pytest.mark.asyncio
    async def test_get_tiktok_video_download_url_from_dict_data(self, client):
        """Test extracting TikTok download URL when metadata data is dict-shaped."""
        with patch.object(client, "get_tiktok_metadata") as mock_metadata:
            mock_metadata.return_value = {
                "code": "0000",
                "data": {
                    "itemInfo": {
                        "itemStruct": {
                            "video": {
                                "downloadAddr": "https://cdn.example.com/video-no-watermark.mp4",
                                "playAddr": "https://cdn.example.com/video-play.mp4",
                            }
                        }
                    }
                },
            }

            result = await client.get_tiktok_video_download_url(
                "https://www.tiktok.com/@user/video/123"
            )

        assert result == "https://cdn.example.com/video-no-watermark.mp4"

    @pytest.mark.asyncio
    async def test_get_tiktok_video_download_url_from_list_data(self, client):
        """Test extracting TikTok download URL when metadata data is list-shaped."""
        with patch.object(client, "get_tiktok_metadata") as mock_metadata:
            mock_metadata.return_value = {
                "code": "0000",
                "data": [
                    {
                        "itemInfo": {
                            "itemStruct": {
                                "video": {
                                    "playAddr": "https://cdn.example.com/video-play.mp4",
                                }
                            }
                        }
                    }
                ],
            }

            result = await client.get_tiktok_video_download_url(
                "https://www.tiktok.com/@user/video/123"
            )

        assert result == "https://cdn.example.com/video-play.mp4"


class TestMemoriesV2ClientUnifiedMethods:
    """Tests for unified get_metadata and get_transcript methods."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    @pytest.mark.asyncio
    async def test_get_metadata_routes_to_youtube(self, client):
        """Test get_metadata routes YouTube URLs correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "YouTube Video"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await client.get_metadata("https://youtube.com/watch?v=abc")

            # Verify the correct endpoint was called
            call_args = mock_post.call_args
            assert "/youtube/video/metadata" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_metadata_routes_to_tiktok(self, client):
        """Test get_metadata routes TikTok URLs correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "TikTok Video"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await client.get_metadata("https://tiktok.com/@user/video/123")

            call_args = mock_post.call_args
            assert "/tiktok/video/metadata" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_metadata_unsupported_platform_raises(self, client):
        """Test get_metadata raises error for unsupported platforms."""
        with pytest.raises(ValueError) as exc_info:
            await client.get_metadata("https://vimeo.com/123")
        assert "Unsupported platform" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_transcript_routes_correctly(self, client):
        """Test get_transcript routes to correct platform endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Transcript text"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await client.get_transcript("https://instagram.com/reel/ABC")

            call_args = mock_post.call_args
            assert "/instagram/video/transcript" in call_args[0][0]


class TestMemoriesV2ClientAssetManagement:
    """Tests for asset management methods."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    @pytest.mark.asyncio
    async def test_get_asset_metadata(self, client):
        """Test getting asset metadata."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "asset_id": "abc123",
            "filename": "video.mp4",
            "size": 1024000,
            "duration": 120.5,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await client.get_asset_metadata("abc123")

        assert result["asset_id"] == "abc123"
        assert result["duration"] == 120.5

    @pytest.mark.asyncio
    async def test_delete_asset(self, client):
        """Test deleting an asset."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )
            result = await client.delete_asset("abc123")

        assert result is True


class TestMemoriesV2ClientTranscription:
    """Tests for transcription methods."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    @pytest.mark.asyncio
    async def test_generate_transcription(self, client):
        """Test generating transcription for uploaded asset."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "Full transcription text...",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "First segment"},
                {"start": 5.0, "end": 10.0, "text": "Second segment"},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.generate_transcription(
                asset_id="abc123",
                model="whisper",
                speaker_diarization=True,
            )

        assert "text" in result
        assert len(result["segments"]) == 2


class TestMemoriesV2ClientTranscriptNormalization:
    """Tests for transcript response normalization."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    def test_normalize_youtube_format(self, client):
        """Test normalizing YouTube nested array format with string timestamps."""
        response = {
            "data": [{
                "data": [
                    {"start": "1.48", "dur": "4.84", "text": "Hello world"},
                    {"start": "6.32", "dur": "3.5", "text": "Welcome to the video"},
                ]
            }]
        }
        result = client._normalize_transcript(response, "youtube")

        assert "text" in result
        assert "segments" in result
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 1.48
        assert result["segments"][0]["end"] == 1.48 + 4.84
        assert result["segments"][0]["text"] == "Hello world"
        assert "Hello world Welcome to the video" in result["text"]

    def test_normalize_tiktok_webvtt_format(self, client):
        """Test normalizing TikTok WebVTT format."""
        webvtt = """WEBVTT

00:00:00.000 --> 00:00:02.500
First line of speech

00:00:02.500 --> 00:00:05.000
Second line of speech"""

        response = {"data": [{"transcript": webvtt}]}
        result = client._normalize_transcript(response, "tiktok")

        assert "text" in result
        assert "segments" in result
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 2.5
        assert result["segments"][0]["text"] == "First line of speech"
        assert result["segments"][1]["start"] == 2.5
        assert result["segments"][1]["end"] == 5.0

    def test_normalize_already_normalized(self, client):
        """Test handling of already normalized format."""
        response = {
            "text": "Already normalized text",
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Already normalized"},
                {"start": 2.0, "end": 4.0, "text": "text"},
            ]
        }
        result = client._normalize_transcript(response, "instagram")

        assert result["text"] == "Already normalized text"
        assert len(result["segments"]) == 2

    def test_normalize_empty_response(self, client):
        """Test handling of empty transcript response."""
        response = {"data": []}
        result = client._normalize_transcript(response, "youtube")

        assert result["text"] == ""
        assert result["segments"] == []

    def test_webvtt_timestamp_parsing(self, client):
        """Test WebVTT timestamp to seconds conversion."""
        assert client._webvtt_timestamp_to_seconds("00:00:00.000") == 0.0
        assert client._webvtt_timestamp_to_seconds("00:01:30.500") == 90.5
        assert client._webvtt_timestamp_to_seconds("01:00:00.000") == 3600.0
        # Handle comma as decimal separator
        assert client._webvtt_timestamp_to_seconds("00:00:05,250") == 5.25

    def test_parse_webvtt_with_cue_numbers(self, client):
        """Test WebVTT parsing with cue identifier numbers."""
        webvtt = """WEBVTT

1
00:00:00.000 --> 00:00:02.000
First cue

2
00:00:02.000 --> 00:00:04.000
Second cue"""

        segments = client._parse_webvtt(webvtt)
        assert len(segments) == 2
        assert segments[0]["text"] == "First cue"
        assert segments[1]["text"] == "Second cue"


class TestMemoriesV2ClientMAITranscript:
    """Tests for MAI transcript methods."""

    @pytest.fixture
    def client(self):
        """Create a Memories.ai v2 client for testing."""
        with patch("video_searching_agent.api.memories_v2_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                memories_api_key="test_key",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                api_timeout_seconds=30,
            )
            return MemoriesV2Client()

    @pytest.mark.asyncio
    async def test_request_mai_transcript(self, client):
        """Test requesting MAI transcript generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            result = await client.request_mai_transcript(
                "https://youtube.com/watch?v=abc123"
            )

            # Verify correct endpoint
            call_args = mock_post.call_args
            assert "/youtube/video/mai/transcript" in call_args[0][0]

        assert result["task_id"] == "task_123"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_request_mai_transcript_with_webhook(self, client):
        """Test MAI transcript request forwards optional webhook_url."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "task_123"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await client.request_mai_transcript(
                "https://youtube.com/watch?v=abc123",
                webhook_url="https://example.com/callback",
            )

            payload = mock_post.call_args.kwargs["json"]
            assert payload["video_url"] == "https://youtube.com/watch?v=abc123"
            assert payload["webhook_url"] == "https://example.com/callback"

    @pytest.mark.asyncio
    async def test_request_mai_transcript_auto_platform_detection(self, client):
        """Test MAI transcript auto-detects platform from URL."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "task_123"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Test TikTok URL
            await client.request_mai_transcript("https://tiktok.com/@user/video/123")
            call_args = mock_post.call_args
            assert "/tiktok/video/mai/transcript" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_request_mai_transcript_unsupported_platform(self, client):
        """Test MAI transcript raises error for unsupported platform."""
        with pytest.raises(ValueError) as exc_info:
            await client.request_mai_transcript("https://vimeo.com/123")
        assert "Unsupported platform" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_mai_transcript_status(self, client):
        """Test getting MAI transcript task status."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "completed",
            "videoTranscript": "Visual description of the video...",
            "audioTranscript": "Spoken words in the video...",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get
            result = await client.get_mai_transcript_status("task_123")

            # Verify correct endpoint
            call_args = mock_get.call_args
            assert "/task/task_123" in call_args[0][0]

        assert result["status"] == "completed"
        assert "videoTranscript" in result
        assert "audioTranscript" in result

    @pytest.mark.asyncio
    async def test_get_mai_transcript_status_envelope_failure_raises(self, client):
        """MAI status envelope failures should raise RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": "0409",
            "msg": "Service is busy, try later",
            "success": False,
            "failed": True,
            "data": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get
            with pytest.raises(RuntimeError) as exc_info:
                await client.get_mai_transcript_status("task_123")

        assert "code=0409" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_mai_transcript_success(self, client):
        """Test waiting for MAI transcript completion."""
        # Simulate polling: first call returns pending, second returns completed
        call_count = 0

        async def mock_get_status(task_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"status": "processing"}
            return {
                "status": "completed",
                "videoTranscript": "Visual content...",
                "audioTranscript": "Audio content...",
            }

        with patch.object(client, "get_mai_transcript_status", side_effect=mock_get_status):
            result = await client.wait_for_mai_transcript(
                "task_123",
                poll_interval=0.01,  # Fast polling for tests
                max_wait=1.0,
            )

        assert result["status"] == "completed"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_wait_for_mai_transcript_timeout(self, client):
        """Test MAI transcript timeout raises error."""
        async def mock_get_status(task_id):
            return {"status": "processing"}

        with patch.object(client, "get_mai_transcript_status", side_effect=mock_get_status):
            with pytest.raises(TimeoutError) as exc_info:
                await client.wait_for_mai_transcript(
                    "task_123",
                    poll_interval=0.01,
                    max_wait=0.05,
                )
            assert "did not complete" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_mai_transcript_failure(self, client):
        """Test MAI transcript task failure raises error."""
        async def mock_get_status(task_id):
            return {"status": "failed", "error": "Video not accessible"}

        with patch.object(client, "get_mai_transcript_status", side_effect=mock_get_status):
            with pytest.raises(RuntimeError) as exc_info:
                await client.wait_for_mai_transcript("task_123", poll_interval=0.01)
            assert "Video not accessible" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_mai_transcript_convenience_wait(self, client):
        """Test convenience method with wait=True."""
        with patch.object(client, "request_mai_transcript") as mock_request:
            mock_request.return_value = {"task_id": "task_123"}
            with patch.object(client, "wait_for_mai_transcript") as mock_wait:
                mock_wait.return_value = {
                    "status": "completed",
                    "videoTranscript": "Visual...",
                    "audioTranscript": "Audio...",
                }
                result = await client.get_mai_transcript(
                    "https://youtube.com/watch?v=abc",
                    wait=True,
                )

        assert result["status"] == "completed"
        mock_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mai_transcript_convenience_no_wait(self, client):
        """Test convenience method with wait=False."""
        with patch.object(client, "request_mai_transcript") as mock_request:
            mock_request.return_value = {"task_id": "task_123", "status": "pending"}
            result = await client.get_mai_transcript(
                "https://youtube.com/watch?v=abc",
                wait=False,
            )

        assert result["task_id"] == "task_123"
        # Should not have called wait_for_mai_transcript
