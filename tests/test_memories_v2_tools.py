"""Tests for Memories.ai v2 tools (MemoriesV2-compatible imports)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from video_searching_agent.tools.memories_v2 import (
    SocialMediaMAITranscriptTool,
    SocialMediaMetadataTool,
    SocialMediaTranscriptTool,
    VLMVideoAnalysisTool,
)


class TestSocialMediaMetadataTool:
    """Tests for SocialMediaMetadataTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = SocialMediaMetadataTool()
        assert tool.name == "social_media_metadata"
        assert "metadata" in tool.description.lower()
        assert "youtube" in tool.description.lower()
        assert "tiktok" in tool.description.lower()
        assert "video_url" in tool.input_schema["required"]
        assert "channel" in tool.input_schema["properties"]

    def test_channel_enum(self):
        """Test channel has valid enum values."""
        tool = SocialMediaMetadataTool()
        channel = tool.input_schema["properties"]["channel"]
        assert "memories.ai" in channel["enum"]
        assert "apify" in channel["enum"]
        assert "rapid" in channel["enum"]

    def test_input_validation_missing_url(self):
        """Test validation fails without video_url."""
        tool = SocialMediaMetadataTool()
        is_valid, error = tool.validate_input()
        assert not is_valid
        assert "video_url" in error.lower()

    def test_input_validation_success(self):
        """Test validation succeeds with video_url."""
        tool = SocialMediaMetadataTool()
        is_valid, error = tool.validate_input(video_url="https://youtube.com/watch?v=abc")
        assert is_valid
        assert error is None

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute fails with missing URL."""
        tool = SocialMediaMetadataTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_unsupported_platform(self):
        """Test execute fails with unsupported platform."""
        tool = SocialMediaMetadataTool()
        with patch.object(tool, "_client", None):
            with patch("video_searching_agent.tools.memories_v2.MemoriesV2Client") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.detect_platform.return_value = None
                mock_client_cls.return_value = mock_client
                tool._client = mock_client

                result = await tool.execute(video_url="https://vimeo.com/123")

        assert not result.success
        assert "unsupported platform" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success_youtube(self):
        """Test successful metadata extraction for YouTube."""
        tool = SocialMediaMetadataTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "youtube"
        mock_client.get_metadata = AsyncMock(return_value={
            "title": "Test YouTube Video",
            "views": 1000000,
            "likes": 50000,
            "channel": "Test Channel",
        })
        tool._client = mock_client

        result = await tool.execute(video_url="https://youtube.com/watch?v=abc123")

        assert result.success
        assert result.data["platform"] == "youtube"
        assert result.data["metadata"]["title"] == "Test YouTube Video"
        assert result.data["metadata"]["views"] == 1000000

    @pytest.mark.asyncio
    async def test_execute_success_tiktok(self):
        """Test successful metadata extraction for TikTok."""
        tool = SocialMediaMetadataTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "tiktok"
        mock_client.get_metadata = AsyncMock(return_value={
            "description": "Test TikTok Video #viral",
            "views": 5000000,
            "likes": 250000,
            "creator": "@testuser",
        })
        tool._client = mock_client

        result = await tool.execute(video_url="https://tiktok.com/@user/video/123")

        assert result.success
        assert result.data["platform"] == "tiktok"
        assert result.data["metadata"]["views"] == 5000000

    @pytest.mark.asyncio
    async def test_execute_with_custom_channel(self):
        """Test metadata extraction with custom channel."""
        tool = SocialMediaMetadataTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "youtube"
        mock_client.get_metadata = AsyncMock(return_value={"title": "Test"})
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            channel="apify",
        )

        assert result.success
        mock_client.get_metadata.assert_called_with("https://youtube.com/watch?v=abc", "apify")

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of API errors."""
        tool = SocialMediaMetadataTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "youtube"
        mock_client.get_metadata = AsyncMock(side_effect=Exception("API rate limit exceeded"))
        tool._client = mock_client

        result = await tool.execute(video_url="https://youtube.com/watch?v=abc")

        assert not result.success
        assert "rate limit" in result.error.lower()


class TestSocialMediaTranscriptTool:
    """Tests for SocialMediaTranscriptTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = SocialMediaTranscriptTool()
        assert tool.name == "social_media_transcript"
        assert "transcript" in tool.description.lower()
        assert "video_url" in tool.input_schema["required"]

    def test_input_validation_missing_url(self):
        """Test validation fails without video_url."""
        tool = SocialMediaTranscriptTool()
        is_valid, error = tool.validate_input()
        assert not is_valid
        assert "video_url" in error.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute fails with missing URL."""
        tool = SocialMediaTranscriptTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_unsupported_platform(self):
        """Test execute fails with unsupported platform."""
        tool = SocialMediaTranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = None
        tool._client = mock_client

        result = await tool.execute(video_url="https://vimeo.com/123")

        assert not result.success
        assert "unsupported platform" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful transcript extraction."""
        tool = SocialMediaTranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "youtube"
        mock_client.get_transcript = AsyncMock(return_value={
            "text": "Hello and welcome to this video tutorial...",
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "Hello and welcome"},
                {"start": 2.5, "end": 5.0, "text": "to this video tutorial"},
            ],
        })
        tool._client = mock_client

        result = await tool.execute(video_url="https://youtube.com/watch?v=abc123")

        assert result.success
        assert result.data["platform"] == "youtube"
        assert "Hello and welcome" in result.data["transcript"]["text"]
        assert len(result.data["transcript"]["segments"]) == 2

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of API errors."""
        tool = SocialMediaTranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "instagram"
        mock_client.get_transcript = AsyncMock(side_effect=Exception("Video not found"))
        tool._client = mock_client

        result = await tool.execute(video_url="https://instagram.com/reel/ABC")

        assert not result.success
        assert "video not found" in result.error.lower()


class TestSocialMediaMAITranscriptTool:
    """Tests for SocialMediaMAITranscriptTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = SocialMediaMAITranscriptTool()
        assert tool.name == "social_media_mai_transcript"
        assert "mai" in tool.description.lower() or "ai-powered" in tool.description.lower()
        assert "video_url" in tool.input_schema["required"]
        assert "wait_for_completion" in tool.input_schema["properties"]
        assert "max_wait_seconds" in tool.input_schema["properties"]
        assert "webhook_url" in tool.input_schema["properties"]

    def test_input_validation_missing_url(self):
        """Test validation fails without video_url."""
        tool = SocialMediaMAITranscriptTool()
        is_valid, error = tool.validate_input()
        assert not is_valid
        assert "video_url" in error.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute fails with missing URL."""
        tool = SocialMediaMAITranscriptTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_unsupported_platform(self):
        """Test execute fails with unsupported platform."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = None
        tool._client = mock_client

        result = await tool.execute(video_url="https://vimeo.com/123")

        assert not result.success
        assert "unsupported platform" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success_wait(self):
        """Test successful MAI transcript extraction with waiting."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "instagram"
        # API returns nested data: response.data.videoTranscript
        mock_client.get_mai_transcript = AsyncMock(return_value={
            "status": "completed",
            "data": {
                "videoTranscript": "Person walking through a park...",
                "audioTranscript": "Hello everyone, today we're exploring...",
            },
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://instagram.com/reel/ABC123",
            wait_for_completion=True,
        )

        assert result.success
        assert result.data["platform"] == "instagram"
        assert result.data["status"] == "completed"
        assert "walking through a park" in result.data["video_transcript"]
        assert "Hello everyone" in result.data["audio_transcript"]

    @pytest.mark.asyncio
    async def test_execute_success_no_wait(self):
        """Test MAI transcript returns task_id when not waiting."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "tiktok"
        mock_client.get_mai_transcript = AsyncMock(return_value={
            "task_id": "task_abc123",
            "status": "pending",
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://tiktok.com/@user/video/123",
            wait_for_completion=False,
        )

        assert result.success
        assert result.data["platform"] == "tiktok"
        assert result.data["status"] == "pending"
        assert result.data["task_id"] == "task_abc123"
        assert "task_id" in result.data["message"].lower()

    @pytest.mark.asyncio
    async def test_execute_success_no_wait_nested_task_id(self):
        """Test MAI transcript extracts nested task_id when not waiting."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "instagram"
        mock_client.get_mai_transcript = AsyncMock(return_value={
            "status": "pending",
            "data": {"task_id": "nested_task_123"},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://instagram.com/reel/ABC123",
            wait_for_completion=False,
        )

        assert result.success
        assert result.data["task_id"] == "nested_task_123"

    @pytest.mark.asyncio
    async def test_execute_webhook_passthrough(self):
        """Test MAI transcript forwards webhook_url to client."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "tiktok"
        mock_client.get_mai_transcript = AsyncMock(return_value={
            "task_id": "task_abc123",
            "status": "pending",
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://tiktok.com/@user/video/123",
            wait_for_completion=False,
            webhook_url="https://example.com/callback",
        )

        assert result.success
        call_kwargs = mock_client.get_mai_transcript.call_args.kwargs
        assert call_kwargs["webhook_url"] == "https://example.com/callback"

    @pytest.mark.asyncio
    async def test_execute_timeout_error(self):
        """Test handling of timeout error."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "instagram"
        mock_client.get_mai_transcript = AsyncMock(
            side_effect=TimeoutError("Task did not complete in 300s")
        )
        tool._client = mock_client

        result = await tool.execute(video_url="https://instagram.com/reel/ABC")

        assert not result.success
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self):
        """Test handling of task failure."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "instagram"
        mock_client.get_mai_transcript = AsyncMock(
            side_effect=RuntimeError("MAI transcript task failed: Video not accessible")
        )
        tool._client = mock_client

        result = await tool.execute(video_url="https://instagram.com/reel/ABC")

        assert not result.success
        assert "failed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of general API errors."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "instagram"
        mock_client.get_mai_transcript = AsyncMock(
            side_effect=Exception("Network connection failed")
        )
        tool._client = mock_client

        result = await tool.execute(video_url="https://instagram.com/reel/ABC")

        assert not result.success
        assert "network" in result.error.lower() or "error" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_blocks_long_form_youtube(self):
        """MAI should be blocked for long-form YouTube by default."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "youtube"
        mock_client.get_mai_transcript = AsyncMock(return_value={})
        tool._client = mock_client

        result = await tool.execute(video_url="https://youtube.com/watch?v=abc123")

        assert not result.success
        assert "short-form" in result.error.lower()
        mock_client.get_mai_transcript.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_blocks_twitter_by_default(self):
        """MAI should be blocked for Twitter/X URLs by default."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "twitter"
        mock_client.get_mai_transcript = AsyncMock(return_value={})
        tool._client = mock_client

        result = await tool.execute(video_url="https://twitter.com/user/status/123")

        assert not result.success
        assert "short-form" in result.error.lower()
        mock_client.get_mai_transcript.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_allows_youtube_shorts(self):
        """YouTube Shorts URLs are allowed for MAI."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "youtube"
        mock_client.get_mai_transcript = AsyncMock(return_value={
            "status": "completed",
            "data": {"videoTranscript": "Visual", "audioTranscript": "Audio"},
        })
        tool._client = mock_client

        result = await tool.execute(video_url="https://youtube.com/shorts/abc123")

        assert result.success
        assert result.data["platform"] == "youtube"

    @pytest.mark.asyncio
    async def test_execute_caps_max_wait_seconds(self):
        """Max wait should be capped to bounded in-run timeout."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "tiktok"
        mock_client.get_mai_transcript = AsyncMock(return_value={"task_id": "task_abc123"})
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://tiktok.com/@user/video/123",
            wait_for_completion=False,
            max_wait_seconds=999,
        )

        assert result.success
        call_kwargs = mock_client.get_mai_transcript.call_args.kwargs
        assert call_kwargs["max_wait"] == 90.0

    @pytest.mark.asyncio
    async def test_execute_invalid_max_wait_defaults_to_bounded_value(self):
        """Invalid max_wait_seconds input should fall back to default bounded wait."""
        tool = SocialMediaMAITranscriptTool()

        mock_client = MagicMock()
        mock_client.detect_platform.return_value = "tiktok"
        mock_client.get_mai_transcript = AsyncMock(return_value={"task_id": "task_abc123"})
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://tiktok.com/@user/video/123",
            wait_for_completion=False,
            max_wait_seconds="invalid",
        )

        assert result.success
        call_kwargs = mock_client.get_mai_transcript.call_args.kwargs
        assert call_kwargs["max_wait"] == 90.0


class TestVLMVideoAnalysisTool:
    """Tests for VLMVideoAnalysisTool."""

    def test_tool_properties(self):
        """Test tool name, description, and schema."""
        tool = VLMVideoAnalysisTool()
        assert tool.name == "vlm_video_analysis"
        assert "vlm" in tool.description.lower() or "vision" in tool.description.lower()
        assert "video_url" in tool.input_schema["required"]
        assert "prompt" in tool.input_schema["properties"]
        assert "model" in tool.input_schema["properties"]
        assert "analysis_type" in tool.input_schema["properties"]

    def test_analysis_type_enum(self):
        """Test analysis_type has valid enum values."""
        tool = VLMVideoAnalysisTool()
        analysis_type = tool.input_schema["properties"]["analysis_type"]
        assert "custom" in analysis_type["enum"]
        assert "summary" in analysis_type["enum"]
        assert "content_analysis" in analysis_type["enum"]
        assert "engagement_factors" in analysis_type["enum"]
        assert "safety_check" in analysis_type["enum"]

    def test_input_validation_missing_url(self):
        """Test validation fails without video_url."""
        tool = VLMVideoAnalysisTool()
        is_valid, error = tool.validate_input()
        assert not is_valid
        assert "video_url" in error.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute fails with missing URL."""
        tool = VLMVideoAnalysisTool()
        result = await tool.execute()
        assert not result.success
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_custom_analysis_missing_prompt(self):
        """Test execute fails with custom analysis without prompt."""
        tool = VLMVideoAnalysisTool()
        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            analysis_type="custom",
        )
        assert not result.success
        assert "prompt is required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_custom_analysis_success(self):
        """Test successful custom VLM analysis."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [
                {
                    "text": "This video shows a person cooking pasta...",
                }
            ],
            "usage": {"input_tokens": 1000, "output_tokens": 200, "total_tokens": 1200},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            prompt="What is happening in this video?",
        )

        assert result.success
        assert "cooking pasta" in result.data["response"]
        assert result.data["analysis_type"] == "custom"

    @pytest.mark.asyncio
    async def test_execute_summary_analysis(self):
        """Test summary analysis type generates correct prompt."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [{"text": "Video summary..."}],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            analysis_type="summary",
        )

        assert result.success
        assert result.data["analysis_type"] == "summary"
        # Check that a summary-specific prompt was used
        call_args = mock_client.analyze_video_with_vlm.call_args
        assert "summary" in call_args[1]["prompt"].lower()

    @pytest.mark.asyncio
    async def test_execute_content_analysis(self):
        """Test content_analysis type generates correct prompt."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [{"text": "Content analysis..."}],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            analysis_type="content_analysis",
        )

        assert result.success
        assert result.data["analysis_type"] == "content_analysis"

    @pytest.mark.asyncio
    async def test_execute_engagement_factors(self):
        """Test engagement_factors type generates correct prompt."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [{"text": "Engagement analysis..."}],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            analysis_type="engagement_factors",
        )

        assert result.success
        call_args = mock_client.analyze_video_with_vlm.call_args
        assert (
            "hook" in call_args[1]["prompt"].lower()
            or "pacing" in call_args[1]["prompt"].lower()
        )

    @pytest.mark.asyncio
    async def test_execute_safety_check(self):
        """Test safety_check type generates correct prompt."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [{"text": "This video appears safe..."}],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            analysis_type="safety_check",
        )

        assert result.success
        call_args = mock_client.analyze_video_with_vlm.call_args
        assert (
            "safety" in call_args[1]["prompt"].lower()
            or "inappropriate" in call_args[1]["prompt"].lower()
        )

    @pytest.mark.asyncio
    async def test_execute_with_custom_model(self):
        """Test VLM analysis with custom model."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [{"text": "Analysis..."}],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            prompt="Analyze this video",
            model="nova:nova-pro-v1",
        )

        assert result.success
        call_args = mock_client.analyze_video_with_vlm.call_args
        assert call_args[1]["model"] == "nova:nova-pro-v1"

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of API errors."""
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(
            side_effect=Exception("Model quota exceeded")
        )
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://youtube.com/watch?v=abc",
            prompt="Analyze this",
        )

        assert not result.success
        assert "quota" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_empty_response_fails(self):
        """Test that empty VLM response is treated as failure.

        When VLM returns empty response (video inaccessible or model failure),
        the tool should fail rather than return empty success to avoid wasted costs.
        """
        tool = VLMVideoAnalysisTool()

        mock_client = MagicMock()
        mock_client.analyze_video_with_vlm = AsyncMock(return_value={
            "choices": [{"text": ""}],
            "usage": None,  # No token usage when response is empty
        })
        tool._client = mock_client

        result = await tool.execute(
            video_url="https://tiktok.com/@user/video/123",
            prompt="Analyze this video",
        )

        assert not result.success
        assert "empty content" in result.error.lower()


class TestMemoriesV2ToolRegistration:
    """Tests for Memories.ai v2 tool registration in agent."""

    def test_v2_tools_registered(self):
        """Test that all Memories.ai v2 tools are registered in the agent."""
        from video_searching_agent.agent.core import VideoSearchingAgent

        with patch("video_searching_agent.agent.core.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                google_api_key="test",
                youtube_api_key="test",
                memories_api_key="test",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                memories_vlm_model="gemini:gemini-3-flash-preview",
                exa_api_key="test",
                max_agent_steps=10,
            )

            agent = VideoSearchingAgent()
            tool_names = agent.tools.list_tools()

            assert "social_media_metadata" in tool_names
            assert "social_media_transcript" in tool_names
            assert "social_media_mai_transcript" in tool_names
            assert "vlm_video_analysis" in tool_names

    def test_v1_tools_not_registered(self):
        """Test that removed Memories.ai v1 tools are not registered."""
        from video_searching_agent.agent.core import VideoSearchingAgent

        with patch("video_searching_agent.agent.core.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                google_api_key="test",
                youtube_api_key="test",
                memories_api_key="test",
                memories_base_url="https://test.api.com/v2",
                memories_default_channel="memories.ai",
                memories_vlm_model="gemini:gemini-3-flash-preview",
                exa_api_key="test",
                max_agent_steps=10,
                api_timeout_seconds=30,
            )

            agent = VideoSearchingAgent()
            tool_names = agent.tools.list_tools()

            assert "memories_upload_video" not in tool_names
            assert "memories_search" not in tool_names
            assert "memories_chat" not in tool_names
            assert "memories_transcription" not in tool_names
            assert "social_media_metadata" in tool_names
            assert "social_media_transcript" in tool_names
            assert "social_media_mai_transcript" in tool_names
            assert "vlm_video_analysis" in tool_names

    def test_streaming_wrapper_registers_same_v2_tools(self):
        """Streaming wrapper should expose the same v2 analysis tools."""
        from video_searching_agent.tools.registry import ToolRegistry
        from video_searching_agent.web.streaming.agent_stream import StreamingAgentWrapper

        wrapper = StreamingAgentWrapper.__new__(StreamingAgentWrapper)
        wrapper.tools = ToolRegistry()
        wrapper._register_tools()

        tool_names = wrapper.tools.list_tools()
        assert "social_media_metadata" in tool_names
        assert "social_media_transcript" in tool_names
        assert "social_media_mai_transcript" in tool_names
        assert "vlm_video_analysis" in tool_names
        assert "memories_upload_video" not in tool_names
        assert "memories_search" not in tool_names
        assert "memories_chat" not in tool_names
        assert "memories_transcription" not in tool_names


class TestMemoriesV2ToolCostTracking:
    """Tests for MemoriesV2 tool cost tracking."""

    def test_metadata_tool_cost(self):
        """Test that metadata tool cost is tracked correctly."""
        from video_searching_agent.config.pricing import get_pricing

        pricing = get_pricing()
        cost = pricing.tools.get_tool_cost("social_media_metadata")
        assert cost == 0.01  # $0.01 per request

    def test_transcript_tool_cost(self):
        """Test that transcript tool cost is tracked correctly."""
        from video_searching_agent.config.pricing import get_pricing

        pricing = get_pricing()
        cost = pricing.tools.get_tool_cost("social_media_transcript")
        assert cost == 0.01  # $0.01 per request

    def test_vlm_tool_cost(self):
        """Test that VLM tool cost is tracked."""
        from video_searching_agent.config.pricing import get_pricing

        pricing = get_pricing()
        cost = pricing.tools.get_tool_cost("vlm_video_analysis")
        assert cost > 0  # Token-based pricing

    def test_mai_transcript_tool_cost(self):
        """Test that MAI transcript tool cost is tracked."""
        from video_searching_agent.config.pricing import get_pricing

        pricing = get_pricing()
        cost = pricing.tools.get_tool_cost("social_media_mai_transcript")
        assert cost == 0.05  # $0.05 base cost per video

    def test_removed_v1_tool_names_default_to_zero(self):
        """Removed v1 tool names should resolve to unknown-tool default cost."""
        from video_searching_agent.config.pricing import get_pricing

        pricing = get_pricing()
        assert pricing.tools.get_tool_cost("memories_upload_video") == 0.0
        assert pricing.tools.get_tool_cost("memories_search") == 0.0
        assert pricing.tools.get_tool_cost("memories_chat") == 0.0
        assert pricing.tools.get_tool_cost("memories_transcription") == 0.0

    def test_youtube_channel_info_quota_mapping(self):
        """youtube_channel_info should map to channel quota."""
        from video_searching_agent.config.pricing import get_pricing

        pricing = get_pricing()
        assert pricing.tools.get_youtube_quota("youtube_channel_info") == 1
