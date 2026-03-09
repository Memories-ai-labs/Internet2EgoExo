"""Memories.ai v2 API tools for direct social media metadata/transcript extraction and VLM analysis.

These tools use the Memories.ai v2 API which provides:
- Direct metadata extraction from YouTube, TikTok, Instagram, Twitter (no upload required)
- Direct transcript extraction from social media videos
- VLM-powered video analysis with Gemini, Nova, Qwen models
"""

from typing import Any

from video_searching_agent.api.memories_v2_client import MemoriesV2Client
from video_searching_agent.tools.base import BaseTool, ToolResult


class SocialMediaMetadataTool(BaseTool):
    """Tool for extracting metadata directly from social media video URLs.

    No upload required - extracts metadata immediately from the platform.
    """

    def __init__(self) -> None:
        """Initialize social media metadata tool."""
        self._client: MemoriesV2Client | None = None

    @property
    def client(self) -> MemoriesV2Client:
        """Lazy-load Memories.ai v2 client."""
        if self._client is None:
            self._client = MemoriesV2Client()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Memories.ai v2 API key is configured."""
        from video_searching_agent.config.settings import get_settings
        settings = get_settings()
        if not settings.memories_api_key:
            return False, "MEMORIES_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "social_media_metadata"

    @property
    def description(self) -> str:
        return """Extract metadata from a SINGLE video URL you already have.

USE THIS TOOL WHEN:
- You have a specific video URL and need its stats (views, likes, comments)
- User shares a link and asks "how is this video performing?"
- You need metadata for ONE specific video

DO NOT USE THIS TOOL WHEN:
- You need to SEARCH/DISCOVER videos
  (use tiktok_search, instagram_search, twitter_search, youtube_search)
- You need multiple videos matching a topic or hashtag

Supports: YouTube, TikTok, Instagram, Twitter/X
Cost: $0.01/video (cheaper than search tools)"""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_url": {
                    "type": "string",
                    "description": "URL of the video (YouTube, TikTok, Instagram, or Twitter)",
                },
                "channel": {
                    "type": "string",
                    "enum": ["memories.ai", "apify", "rapid"],
                    "description": "Scraping channel (memories.ai=$0.01/video)",
                    "default": "memories.ai",
                },
            },
            "required": ["video_url"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Extract metadata from social media video URL.

        Args:
            video_url: URL of the video.
            channel: Scraping channel to use.

        Returns:
            ToolResult with video metadata.
        """
        video_url = kwargs.get("video_url")
        channel = kwargs.get("channel")

        if not video_url:
            return ToolResult.fail("video_url is required")

        try:
            # Auto-detect platform and get metadata
            platform = self.client.detect_platform(video_url)
            if not platform:
                return ToolResult.fail(
                    f"Unsupported platform URL: {video_url}. "
                    "Supported: YouTube, TikTok, Instagram, Twitter/X"
                )

            metadata = await self.client.get_metadata(video_url, channel)

            return ToolResult.ok({
                "platform": platform,
                "video_url": video_url,
                "metadata": metadata,
            })

        except Exception as e:
            return ToolResult.fail(f"Memories.ai v2 metadata extraction error: {str(e)}")


class SocialMediaTranscriptTool(BaseTool):
    """Tool for extracting transcripts directly from social media video URLs.

    No upload required - extracts transcript immediately from the platform.
    """

    def __init__(self) -> None:
        """Initialize social media transcript tool."""
        self._client: MemoriesV2Client | None = None

    @property
    def client(self) -> MemoriesV2Client:
        """Lazy-load Memories.ai v2 client."""
        if self._client is None:
            self._client = MemoriesV2Client()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Memories.ai v2 API key is configured."""
        from video_searching_agent.config.settings import get_settings
        settings = get_settings()
        if not settings.memories_api_key:
            return False, "MEMORIES_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "social_media_transcript"

    @property
    def description(self) -> str:
        return """Extract transcript/captions from a video URL directly.

USE THIS TOOL WHEN:
- User asks "what does the creator say in this video?"
- You need the spoken words or captions from a video
- Analyzing what is SAID (not what is shown visually)

This is the FASTEST way to get transcripts - no upload or processing wait.
For visual content analysis (what's SHOWN), use vlm_video_analysis instead.

Supports: YouTube, TikTok, Instagram, Twitter/X"""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_url": {
                    "type": "string",
                    "description": "URL of the video (YouTube, TikTok, Instagram, or Twitter)",
                },
                "channel": {
                    "type": "string",
                    "enum": ["memories.ai", "apify", "rapid"],
                    "description": "Scraping channel (memories.ai=$0.01/video)",
                    "default": "memories.ai",
                },
            },
            "required": ["video_url"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Extract transcript from social media video URL.

        Args:
            video_url: URL of the video.
            channel: Scraping channel to use.

        Returns:
            ToolResult with video transcript.
        """
        video_url = kwargs.get("video_url")
        channel = kwargs.get("channel")

        if not video_url:
            return ToolResult.fail("video_url is required")

        try:
            # Auto-detect platform and get transcript
            platform = self.client.detect_platform(video_url)
            if not platform:
                return ToolResult.fail(
                    f"Unsupported platform URL: {video_url}. "
                    "Supported: YouTube, TikTok, Instagram, Twitter/X"
                )

            transcript = await self.client.get_transcript(video_url, channel)

            return ToolResult.ok({
                "platform": platform,
                "video_url": video_url,
                "transcript": transcript,
            })

        except Exception as e:
            return ToolResult.fail(f"Memories.ai v2 transcript extraction error: {str(e)}")


class SocialMediaMAITranscriptTool(BaseTool):
    """Tool for AI-powered dual-layer transcription of social media videos.

    MAI (Memories AI) transcript provides:
    - videoTranscript: Visual scene descriptions using Gemini VLM
    - audioTranscript: Speech-to-text using Whisper

    Use this when:
    - Regular transcript fails (no captions available)
    - You need visual descriptions of what's shown in the video
    - You need both spoken words AND visual scene analysis
    """

    def __init__(self) -> None:
        """Initialize MAI transcript tool."""
        self._client: MemoriesV2Client | None = None
        self.default_max_wait_seconds = 90
        self.max_wait_cap_seconds = 90

    @property
    def client(self) -> MemoriesV2Client:
        """Lazy-load Memories.ai v2 client."""
        if self._client is None:
            self._client = MemoriesV2Client()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Memories.ai v2 API key is configured."""
        from video_searching_agent.config.settings import get_settings
        settings = get_settings()
        if not settings.memories_api_key:
            return False, "MEMORIES_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "social_media_mai_transcript"

    @property
    def description(self) -> str:
        return """AI-powered dual-layer transcription: visual descriptions + speech-to-text.

USE THIS TOOL WHEN:
- Regular transcript unavailable (no captions on video)
- You need to know what's SHOWN visually (scenes, objects, actions)
- You need BOTH what's said AND what's shown
- User asks "describe everything in this video"

OUTPUT PROVIDES:
- videoTranscript: AI-generated visual scene descriptions (what you SEE)
- audioTranscript: Speech-to-text of spoken words (what you HEAR)

This is AI-powered (Gemini VLM + Whisper) - more expensive but works without captions.
For videos WITH existing captions, use social_media_transcript instead (faster, cheaper).

Supports: YouTube, TikTok, Instagram, Twitter/X"""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_url": {
                    "type": "string",
                    "description": "URL of the video (YouTube, TikTok, Instagram, or Twitter)",
                },
                "wait_for_completion": {
                    "type": "boolean",
                    "description": "Wait for completion (default: true). "
                    "Set false to get task_id for polling.",
                    "default": True,
                },
                "max_wait_seconds": {
                    "type": "number",
                    "description": "Max wait seconds if wait_for_completion=true. "
                    "Default: 90 (bounded for chat UX).",
                    "default": 90,
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Optional webhook URL for async MAI callback delivery.",
                },
            },
            "required": ["video_url"],
        }

    def _is_short_form_url(self, platform: str, video_url: str) -> bool:
        """Allow MAI on short-form surfaces by default."""
        if platform in {"tiktok", "instagram"}:
            return True
        if platform == "youtube":
            return "youtube.com/shorts/" in video_url.lower()
        # Default deny for long-form/unknown surfaces (e.g., Twitter/X)
        return False

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Generate MAI transcript for a social media video.

        Args:
            video_url: URL of the video.
            wait_for_completion: Whether to wait for completion.
            max_wait_seconds: Max wait time in seconds.
            webhook_url: Optional webhook URL for async callback.

        Returns:
            ToolResult with MAI transcript (videoTranscript + audioTranscript).
        """
        video_url = kwargs.get("video_url")
        wait = kwargs.get("wait_for_completion", True)
        max_wait = kwargs.get("max_wait_seconds", self.default_max_wait_seconds)
        webhook_url = kwargs.get("webhook_url")

        if not video_url:
            return ToolResult.fail("video_url is required")

        try:
            # Auto-detect platform
            platform = self.client.detect_platform(video_url)
            if not platform:
                return ToolResult.fail(
                    f"Unsupported platform URL: {video_url}. "
                    "Supported: YouTube, TikTok, Instagram, Twitter/X"
                )
            if not self._is_short_form_url(platform, video_url):
                return ToolResult.fail(
                    "MAI transcript is restricted to short-form videos by default "
                    "(TikTok/Instagram/YouTube Shorts). For long-form content, use "
                    "social_media_transcript or social_media_metadata."
                )

            try:
                requested_wait = float(max_wait)
            except (TypeError, ValueError):
                requested_wait = float(self.default_max_wait_seconds)
            effective_max_wait = max(1.0, min(requested_wait, float(self.max_wait_cap_seconds)))

            result = await self.client.get_mai_transcript(
                video_url=video_url,
                platform=platform,
                wait=wait,
                poll_interval=2.0,
                max_wait=effective_max_wait,
                webhook_url=str(webhook_url) if webhook_url else None,
            )

            # Check if we got a task_id (async mode) or completed result
            if not wait:
                task_id = result.get("task_id") or result.get("id")
                if task_id is None:
                    nested = result.get("data")
                    if isinstance(nested, dict):
                        task_id = nested.get("task_id") or nested.get("id")
                return ToolResult.ok({
                    "platform": platform,
                    "video_url": video_url,
                    "status": "pending",
                    "task_id": task_id,
                    "message": "MAI transcript started. Use task_id to poll for results.",
                })

            # Completed result may be top-level or nested under result.data.
            data = result.get("data", {})
            if not isinstance(data, dict):
                data = {}
            return ToolResult.ok({
                "platform": platform,
                "video_url": video_url,
                "status": result.get("status", "completed"),
                "video_transcript": (
                    data.get("videoTranscript") or result.get("videoTranscript", "")
                ),
                "audio_transcript": (
                    data.get("audioTranscript") or result.get("audioTranscript", "")
                ),
            })

        except TimeoutError as e:
            return ToolResult.fail(f"MAI transcript timed out: {str(e)}")
        except RuntimeError as e:
            return ToolResult.fail(f"MAI transcript failed: {str(e)}")
        except Exception as e:
            return ToolResult.fail(f"MAI transcript error: {str(e)}")


class VLMVideoAnalysisTool(BaseTool):
    """Tool for analyzing videos using Vision Language Models (VLM).

    Uses modern multimodal models (Gemini, Nova, Qwen) for deep video understanding.
    """

    def __init__(self) -> None:
        """Initialize VLM video analysis tool."""
        self._client: MemoriesV2Client | None = None

    @property
    def client(self) -> MemoriesV2Client:
        """Lazy-load Memories.ai v2 client."""
        if self._client is None:
            self._client = MemoriesV2Client()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """Check if Memories.ai v2 API key is configured."""
        from video_searching_agent.config.settings import get_settings
        settings = get_settings()
        if not settings.memories_api_key:
            return False, "MEMORIES_API_KEY is not configured"
        return True, None

    @property
    def name(self) -> str:
        return "vlm_video_analysis"

    @property
    def description(self) -> str:
        return """AI-powered VISUAL analysis of video content using Vision Language Models.

USE THIS TOOL WHEN:
- User asks "what happens in this video?" or "what is shown?"
- Analyzing visual elements: scenes, objects, people, actions, editing style
- Evaluating production quality, engagement hooks, or visual storytelling
- Content moderation or brand safety checks

This tool actually "watches" the video with Gemini VLM.
For what is SAID (spoken words), use social_media_transcript instead.
For basic stats (views, likes), use social_media_metadata instead.

Works on video URLs directly - no upload needed.

Models:
- gemini:gemini-3-flash-preview (default, fast)
- gemini:gemini-3-pro-preview (highest quality)"""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_url": {
                    "type": "string",
                    "description": "URL of the video to analyze",
                },
                "prompt": {
                    "type": "string",
                    "description": "Analysis prompt or question about the video",
                },
                "model": {
                    "type": "string",
                    "description": (
                        "VLM model: gemini-3-flash-preview (default, fast) or "
                        "gemini-3-pro-preview (best quality)"
                    ),
                    "default": "gemini:gemini-3-flash-preview",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens in response",
                    "default": 1000,
                },
                "analysis_type": {
                    "type": "string",
                    "enum": [
                        "custom", "summary", "content_analysis",
                        "engagement_factors", "safety_check"
                    ],
                    "description": "Analysis type: custom, summary, content/engagement/safety",
                    "default": "custom",
                },
            },
            "required": ["video_url"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Analyze video using VLM.

        Args:
            video_url: URL of the video.
            prompt: Analysis prompt.
            model: VLM model to use.
            max_tokens: Max response tokens.
            analysis_type: Type of analysis.

        Returns:
            ToolResult with VLM analysis.
        """
        video_url = kwargs.get("video_url")
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model")
        max_tokens = kwargs.get("max_tokens", 1000)
        analysis_type = kwargs.get("analysis_type", "custom")

        if not video_url:
            return ToolResult.fail("video_url is required")

        # Build prompt based on analysis type
        if analysis_type == "summary":
            prompt = prompt or (
                "Provide a comprehensive summary of this video, "
                "including the main topic, key points, and overall message."
            )
        elif analysis_type == "content_analysis":
            prompt = prompt or """Analyze this video's content in detail:
1. What is the main subject/topic?
2. What visual elements are prominent (people, objects, locations)?
3. What is the style/format (tutorial, vlog, entertainment, etc.)?
4. What is the tone/mood of the video?
5. Who appears to be the target audience?"""
        elif analysis_type == "engagement_factors":
            prompt = prompt or """Analyze what makes this video engaging or not:
1. Hook: How does the video capture attention in the first few seconds?
2. Pacing: Is the video well-paced or does it drag?
3. Visual quality: Production quality, editing, effects
4. Audio: Voice, music, sound effects quality
5. Call to action: Does it encourage engagement?
6. What could be improved for better engagement?"""
        elif analysis_type == "safety_check":
            prompt = prompt or """Review this video for content safety:
1. Is there any inappropriate content (violence, adult content, hate speech)?
2. Is there any misleading or false information?
3. Is there any copyright-infringing content visible?
4. Is it brand-safe for advertising?
Provide a brief safety assessment."""
        elif not prompt:
            return ToolResult.fail("prompt is required for custom analysis_type")

        try:
            result = await self.client.analyze_video_with_vlm(
                video_url=video_url,
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
            )

            # Extract response content from the API result
            choices = result.get("choices", [])
            if not choices:
                # Log full response for debugging
                error_detail = result.get("error", {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get("message", "")
                else:
                    error_msg = str(error_detail)
                return ToolResult.fail(
                    f"VLM returned no choices - video may not be accessible. "
                    f"Error: {error_msg or 'No error details'}. "
                    f"Response keys: {list(result.keys())}"
                )

            response_content = choices[0].get("text", "")
            if not response_content:
                # Provide more context about the empty response
                finish_reason = choices[0].get("finish_reason", "unknown")
                return ToolResult.fail(
                    f"VLM returned empty content (finish_reason: {finish_reason}). "
                    f"Video may be inaccessible, too long, or blocked by the model. "
                    f"Try a different video URL or model."
                )

            usage = result.get("usage", {})
            return ToolResult.ok({
                "video_url": video_url,
                "analysis_type": analysis_type,
                "model": model or "gemini:gemini-3-flash-preview",
                "response": response_content,
                "usage": {
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                },
            })

        except Exception as e:
            return ToolResult.fail(f"VLM video analysis error: {str(e)}")
