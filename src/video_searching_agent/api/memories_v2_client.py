"""Memories.ai v2 API client.

This client provides access to the new Memories.ai v2 API which offers:
- Direct social media metadata/transcript extraction (no upload required)
- VLM chat completions with Gemini, Nova, Qwen models
- Asset management and transcription endpoints
- MAI transcript (AI-powered dual-layer visual + audio transcription)
"""

import asyncio
import re
from typing import Any, BinaryIO, cast

import httpx

from video_searching_agent.config.settings import get_settings


class MemoriesV2Client:
    """Client for interacting with the Memories.ai v2 API."""

    BASE_URL = "https://mavi-backend.memories.ai/serve/api/v2"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the Memories.ai v2 client.

        Args:
            api_key: Memories.ai v2 API key. Defaults to settings.memories_api_key.
            base_url: API base URL. Defaults to Memories.ai v2 base URL.
        """
        settings = get_settings()
        effective_api_key = api_key if api_key is not None else settings.memories_api_key
        effective_base_url = base_url if base_url is not None else settings.memories_base_url

        self.api_key = effective_api_key.strip()
        normalized_base_url = effective_base_url.strip()
        settings_base_url = settings.memories_base_url.strip()
        self.base_url = (normalized_base_url or settings_base_url or self.BASE_URL).rstrip("/")
        self.timeout = settings.api_timeout_seconds
        self.default_channel = settings.memories_default_channel.strip() or "memories.ai"
        self._clients: dict[float, tuple[httpx.AsyncClient, Any]] = {}
        self._client_lock = asyncio.Lock()

    def _headers(self) -> dict[str, str]:
        """Get request headers.

        Note: Memories.ai v2 API uses 'Authorization: {api_key}' without 'Bearer' prefix.
        """
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    def _is_success_code(self, code: Any) -> bool:
        """Evaluate whether an API envelope code represents success."""
        if code is None:
            return True
        return str(code).strip() in {"0000", "0", ""}

    def _format_api_error(self, payload: dict[str, Any], endpoint: str) -> str:
        """Create a concise error message from a Memories API envelope."""
        code = payload.get("code")
        msg = payload.get("msg") or payload.get("message") or payload.get("error")
        code_str = str(code) if code is not None else "unknown"
        msg_str = str(msg).strip() if msg is not None else "Unknown error"
        return f"Memories API error at {endpoint}: code={code_str}, message={msg_str}"

    def _ensure_api_success(self, payload: dict[str, Any], endpoint: str) -> None:
        """Raise when an API-level failure envelope is returned with HTTP 200."""
        failed = payload.get("failed")
        success = payload.get("success")
        code = payload.get("code")

        if failed is True:
            raise RuntimeError(self._format_api_error(payload, endpoint))
        if success is False:
            raise RuntimeError(self._format_api_error(payload, endpoint))
        if not self._is_success_code(code):
            raise RuntimeError(self._format_api_error(payload, endpoint))

    def _decode_json_response(self, response: Any, endpoint: str) -> dict[str, Any]:
        """Decode and validate JSON responses with envelope-aware error handling."""
        response.raise_for_status()
        payload_raw = response.json()
        if not isinstance(payload_raw, dict):
            raise RuntimeError(
                f"Unexpected non-object response from Memories API at {endpoint}"
            )
        payload = cast(dict[str, Any], payload_raw)
        self._ensure_api_success(payload, endpoint)
        return payload

    async def _get_client(self, timeout: float) -> Any:
        """Get or create a shared AsyncClient for the given timeout."""
        key = float(timeout)
        existing = self._clients.get(key)
        if existing is not None:
            return existing[1]

        async with self._client_lock:
            existing = self._clients.get(key)
            if existing is not None:
                return existing[1]

            raw_client = httpx.AsyncClient(timeout=timeout)
            enter = getattr(raw_client, "__aenter__", None)
            if callable(enter):
                entered = enter()
                active_client = await entered if asyncio.iscoroutine(entered) else entered
            else:
                active_client = raw_client
            self._clients[key] = (raw_client, active_client)
            return active_client

    async def aclose(self) -> None:
        """Close all shared clients."""
        async with self._client_lock:
            clients = list(self._clients.values())
            self._clients.clear()

        for raw_client, _ in clients:
            if hasattr(raw_client, "aclose"):
                await raw_client.aclose()

    # -------------------------------------------------------------------------
    # YouTube endpoints
    # -------------------------------------------------------------------------

    async def get_youtube_metadata(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a YouTube video.

        Args:
            video_url: YouTube video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video metadata including title, description, views, etc.
        """
        client = await self._get_client(float(self.timeout))
        response = await client.post(
            f"{self.base_url}/youtube/video/metadata",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/youtube/video/metadata")

    async def get_youtube_transcript(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get transcript for a YouTube video.

        Args:
            video_url: YouTube video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video transcript with timestamps.
        """
        client = await self._get_client(60.0)
        response = await client.post(
            f"{self.base_url}/youtube/video/transcript",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/youtube/video/transcript")

    # -------------------------------------------------------------------------
    # TikTok endpoints
    # -------------------------------------------------------------------------

    async def get_tiktok_metadata(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a TikTok video.

        Args:
            video_url: TikTok video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video metadata including creator info, engagement, etc.
        """
        client = await self._get_client(float(self.timeout))
        response = await client.post(
            f"{self.base_url}/tiktok/video/metadata",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/tiktok/video/metadata")

    async def get_tiktok_transcript(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get transcript for a TikTok video.

        Args:
            video_url: TikTok video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video transcript with timestamps.
        """
        client = await self._get_client(60.0)
        response = await client.post(
            f"{self.base_url}/tiktok/video/transcript",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/tiktok/video/transcript")

    # -------------------------------------------------------------------------
    # Instagram endpoints
    # -------------------------------------------------------------------------

    async def get_instagram_metadata(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get metadata for an Instagram video/reel.

        Args:
            video_url: Instagram video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video metadata including creator info, engagement, etc.
        """
        client = await self._get_client(float(self.timeout))
        response = await client.post(
            f"{self.base_url}/instagram/video/metadata",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/instagram/video/metadata")

    async def get_instagram_transcript(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get transcript for an Instagram video/reel.

        Args:
            video_url: Instagram video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video transcript with timestamps.
        """
        client = await self._get_client(60.0)
        response = await client.post(
            f"{self.base_url}/instagram/video/transcript",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/instagram/video/transcript")

    # -------------------------------------------------------------------------
    # Twitter endpoints
    # -------------------------------------------------------------------------

    async def get_twitter_metadata(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a Twitter video.

        Args:
            video_url: Twitter video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video metadata including creator info, engagement, etc.
        """
        client = await self._get_client(float(self.timeout))
        response = await client.post(
            f"{self.base_url}/twitter/video/metadata",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/twitter/video/metadata")

    async def get_twitter_transcript(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get transcript for a Twitter video.

        Args:
            video_url: Twitter video URL.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video transcript with timestamps.
        """
        client = await self._get_client(60.0)
        response = await client.post(
            f"{self.base_url}/twitter/video/transcript",
            headers=self._headers(),
            json={
                "video_url": video_url,
                "channel": channel or self.default_channel,
            },
        )
        return self._decode_json_response(response, "/twitter/video/transcript")

    # -------------------------------------------------------------------------
    # VLM Chat endpoint
    # -------------------------------------------------------------------------

    def _get_mime_type(self, url: str) -> str:
        """Detect mime type from URL.

        Args:
            url: Video URL to detect mime type from.

        Returns:
            Mime type string (defaults to video/mp4 for social media URLs).
        """
        url_lower = url.lower()
        if any(ext in url_lower for ext in [".mp4", ".m4v"]):
            return "video/mp4"
        elif ".webm" in url_lower:
            return "video/webm"
        elif ".mov" in url_lower:
            return "video/quicktime"
        elif ".avi" in url_lower:
            return "video/x-msvideo"
        elif ".mkv" in url_lower:
            return "video/x-matroska"
        # Default to mp4 for social media URLs (YouTube, TikTok, Instagram, Twitter)
        return "video/mp4"

    async def vlm_chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Send a chat completion request to the VLM API.

        Args:
            messages: List of message objects with role and content.
                Content can include text and video references.
            model: VLM model to use (e.g., 'gemini:gemini-3-flash-preview',
                'gemini:gemini-2.5-flash', 'nova:nova-lite-v1',
                'qwen:qwen2.5-vl-72b-instruct'). Defaults to settings.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            Chat completion response.
        """
        settings = get_settings()
        client = await self._get_client(120.0)
        response = await client.post(
            f"{self.base_url}/vu/chat/completions",
            headers=self._headers(),
            json={
                "model": model or settings.memories_vlm_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        return self._decode_json_response(response, "/vu/chat/completions")

    async def analyze_video_with_vlm(
        self,
        video_url: str,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        """Analyze a video using VLM with a custom prompt.

        Convenience method that wraps vlm_chat for video analysis.

        Args:
            video_url: URL of the video to analyze.
            prompt: Analysis prompt/question about the video.
            model: VLM model to use. Defaults to settings.
            max_tokens: Maximum tokens in response.

        Returns:
            VLM analysis response.
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_uri": video_url,
                        "mime_type": self._get_mime_type(video_url),
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        return await self.vlm_chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
        )

    async def get_tiktok_video_download_url(self, video_url: str) -> str | None:
        """Get direct download URL for a TikTok video.

        TikTok page URLs are blocked by robots.txt for Vertex AI (VLM).
        The download URL is a CDN link that Vertex AI can potentially access.

        Args:
            video_url: TikTok page URL (e.g., https://www.tiktok.com/@user/video/123)

        Returns:
            CDN download URL if available, None otherwise.
        """
        metadata = await self.get_tiktok_metadata(video_url)
        data = metadata.get("data")

        # Metadata payloads can be dict- or list-shaped depending on channel/provider.
        candidates: list[dict[str, Any]] = []
        if isinstance(data, dict):
            candidates.append(data)
        elif isinstance(data, list):
            candidates.extend([item for item in data if isinstance(item, dict)])

        for candidate in candidates:
            item_info = candidate.get("itemInfo")
            item_struct = item_info.get("itemStruct") if isinstance(item_info, dict) else None

            possible_sources = [candidate]
            if isinstance(item_info, dict):
                possible_sources.append(item_info)
            if isinstance(item_struct, dict):
                possible_sources.append(item_struct)

            for source in possible_sources:
                video = source.get("video")
                if not isinstance(video, dict):
                    continue

                # Try downloadAddr first (no watermark), then playAddr.
                download_url = video.get("downloadAddr") or video.get("playAddr")
                if isinstance(download_url, str) and download_url:
                    return download_url

        return None

    async def analyze_tiktok_video_with_vlm(
        self,
        video_url: str,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        """Analyze a TikTok video using VLM with download URL.

        This method attempts to bypass robots.txt restrictions by:
        1. Getting the CDN download URL from TikTok metadata
        2. Passing the CDN URL (not the page URL) to VLM for analysis

        WARNING: This approach has limitations:
        - TikTok CDN URLs often require authentication headers
        - Vertex AI may still be blocked from accessing these URLs
        - CDN URLs are time-limited and may expire quickly

        For reliable TikTok video analysis, use transcript-based analysis:
        get_tiktok_transcript() + text-based LLM analysis.

        Args:
            video_url: TikTok page URL (e.g., https://www.tiktok.com/@user/video/123)
            prompt: Analysis prompt/question about the video.
            model: VLM model to use. Defaults to settings.
            max_tokens: Maximum tokens in response.

        Returns:
            VLM analysis response. Check response['status'] for 'errored' status
            and response['error'] for error details.

        Raises:
            ValueError: If download URL cannot be obtained from metadata.
        """
        download_url = await self.get_tiktok_video_download_url(video_url)
        if not download_url:
            raise ValueError(
                f"Could not get download URL for TikTok video: {video_url}. "
                "Consider using transcript-based analysis instead."
            )

        return await self.analyze_video_with_vlm(
            video_url=download_url,
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
        )

    # -------------------------------------------------------------------------
    # Asset management endpoints
    # -------------------------------------------------------------------------

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
    ) -> dict[str, Any]:
        """Upload a file to get an asset_id.

        Args:
            file: File-like object to upload.
            filename: Name of the file.

        Returns:
            Upload response with asset_id.
        """
        client = await self._get_client(120.0)
        # Use multipart form data for file upload
        files = {"file": (filename, file)}
        headers = {"Authorization": self.api_key}  # No Content-Type for multipart
        response = await client.post(
            f"{self.base_url}/upload",
            headers=headers,
            files=files,
        )
        return self._decode_json_response(response, "/upload")

    async def get_asset_metadata(self, asset_id: str) -> dict[str, Any]:
        """Get metadata for an uploaded asset.

        Args:
            asset_id: Asset ID from upload.

        Returns:
            Asset metadata.
        """
        client = await self._get_client(float(self.timeout))
        response = await client.get(
            f"{self.base_url}/{asset_id}/metadata",
            headers=self._headers(),
        )
        return self._decode_json_response(response, f"/{asset_id}/metadata")

    async def delete_asset(self, asset_id: str) -> bool:
        """Delete an uploaded asset.

        Args:
            asset_id: Asset ID to delete.

        Returns:
            True if deleted successfully.
        """
        client = await self._get_client(float(self.timeout))
        response = await client.delete(
            f"{self.base_url}/asset/{asset_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return True

    # -------------------------------------------------------------------------
    # Transcription endpoint (for uploaded assets)
    # -------------------------------------------------------------------------

    async def generate_transcription(
        self,
        asset_id: str,
        model: str = "whisper",
        speaker_diarization: bool = False,
    ) -> dict[str, Any]:
        """Generate transcription for an uploaded asset.

        Args:
            asset_id: Asset ID from upload.
            model: Transcription model to use.
            speaker_diarization: Whether to detect speakers.

        Returns:
            Transcription response with text and timestamps.
        """
        client = await self._get_client(120.0)
        response = await client.post(
            f"{self.base_url}/asset/{asset_id}/transcription",
            headers=self._headers(),
            json={
                "model": model,
                "speaker_diarization": speaker_diarization,
            },
        )
        return self._decode_json_response(response, f"/asset/{asset_id}/transcription")

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------

    def detect_platform(self, url: str) -> str | None:
        """Detect the social media platform from a URL.

        Args:
            url: Video URL.

        Returns:
            Platform name ('youtube', 'tiktok', 'instagram', 'twitter') or None.
        """
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "tiktok.com" in url_lower:
            return "tiktok"
        elif "instagram.com" in url_lower:
            return "instagram"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        return None

    async def get_metadata(
        self,
        video_url: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """Get metadata for any supported social media video URL.

        Auto-detects the platform and calls the appropriate endpoint.

        Args:
            video_url: Video URL from any supported platform.
            channel: Channel for scraping. Defaults to settings.

        Returns:
            Video metadata.

        Raises:
            ValueError: If platform is not supported.
        """
        platform = self.detect_platform(video_url)
        if platform == "youtube":
            return await self.get_youtube_metadata(video_url, channel)
        elif platform == "tiktok":
            return await self.get_tiktok_metadata(video_url, channel)
        elif platform == "instagram":
            return await self.get_instagram_metadata(video_url, channel)
        elif platform == "twitter":
            return await self.get_twitter_metadata(video_url, channel)
        else:
            raise ValueError(f"Unsupported platform URL: {video_url}")

    async def get_transcript(
        self,
        video_url: str,
        channel: str | None = None,
        normalize: bool = True,
    ) -> dict[str, Any]:
        """Get transcript for any supported social media video URL.

        Auto-detects the platform and calls the appropriate endpoint.

        Args:
            video_url: Video URL from any supported platform.
            channel: Channel for scraping. Defaults to settings.
            normalize: Whether to normalize the response format. Defaults to True.

        Returns:
            Video transcript in normalized format if normalize=True:
            {
                "text": "full transcript text",
                "segments": [{"start": float, "end": float, "text": str}]
            }

        Raises:
            ValueError: If platform is not supported.
        """
        platform = self.detect_platform(video_url)
        if platform == "youtube":
            result = await self.get_youtube_transcript(video_url, channel)
        elif platform == "tiktok":
            result = await self.get_tiktok_transcript(video_url, channel)
        elif platform == "instagram":
            result = await self.get_instagram_transcript(video_url, channel)
        elif platform == "twitter":
            result = await self.get_twitter_transcript(video_url, channel)
        else:
            raise ValueError(f"Unsupported platform URL: {video_url}")

        if normalize:
            return self._normalize_transcript(result, platform)
        return result

    def _normalize_transcript(
        self,
        response: dict[str, Any],
        platform: str,
    ) -> dict[str, Any]:
        """Normalize transcript response to a standard format.

        Different platforms return different transcript formats:
        - YouTube: {data: [{data: [{start: "1.48", dur: "4.84", text: "..."}]}]}
        - TikTok: {data: [{transcript: "WEBVTT format..."}]}
        - Instagram/Twitter: Similar variations

        This normalizes all to:
        {
            "text": "full transcript",
            "segments": [{"start": float, "end": float, "text": str}]
        }

        Args:
            response: Raw API response.
            platform: Platform name for format detection.

        Returns:
            Normalized transcript dict.
        """
        segments: list[dict[str, Any]] = []
        full_text_parts: list[str] = []

        # Handle nested data structure common in responses
        data = response.get("data", response)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # YouTube format: nested data with start/dur/text as strings
        if platform == "youtube":
            inner_data = data.get("data", []) if isinstance(data, dict) else []
            if isinstance(inner_data, list):
                for seg in inner_data:
                    if not isinstance(seg, dict):
                        continue
                    try:
                        start = float(seg.get("start", 0))
                        dur = float(seg.get("dur", 0))
                        text = seg.get("text", "")
                        segments.append({
                            "start": start,
                            "end": start + dur,
                            "text": text,
                        })
                        full_text_parts.append(text)
                    except (ValueError, TypeError):
                        continue

        # TikTok format: WebVTT string
        elif platform == "tiktok":
            transcript_str = data.get("transcript", "") if isinstance(data, dict) else ""
            if isinstance(transcript_str, str) and transcript_str.strip():
                segments = self._parse_webvtt(transcript_str)
                full_text_parts = [seg["text"] for seg in segments]

        # Instagram/Twitter: May follow similar patterns or have pre-normalized format
        else:
            # Try to extract from common structures
            if isinstance(data, dict):
                # Check for pre-normalized format
                if "segments" in data and isinstance(data["segments"], list):
                    for seg in data["segments"]:
                        if isinstance(seg, dict):
                            try:
                                segments.append({
                                    "start": float(seg.get("start", 0)),
                                    "end": float(seg.get("end", 0)),
                                    "text": seg.get("text", ""),
                                })
                                full_text_parts.append(seg.get("text", ""))
                            except (ValueError, TypeError):
                                continue
                # Check for transcript string (WebVTT)
                elif "transcript" in data and isinstance(data["transcript"], str):
                    segments = self._parse_webvtt(data["transcript"])
                    full_text_parts = [seg["text"] for seg in segments]
                # Check for text field directly
                elif "text" in data and isinstance(data["text"], str):
                    return {
                        "text": data["text"],
                        "segments": data.get("segments", []),
                    }

        # Build full text
        full_text = " ".join(full_text_parts).strip()

        # If we couldn't extract segments but have raw text, return it
        if not segments and isinstance(data, dict):
            raw_text = data.get("text", "")
            if raw_text:
                return {"text": raw_text, "segments": []}

        return {
            "text": full_text,
            "segments": segments,
        }

    def _parse_webvtt(self, webvtt_str: str) -> list[dict[str, Any]]:
        """Parse WebVTT format transcript into segments.

        WebVTT format:
        WEBVTT

        00:00:00.000 --> 00:00:02.500
        First line of text

        00:00:02.500 --> 00:00:05.000
        Second line of text

        Args:
            webvtt_str: WebVTT formatted string.

        Returns:
            List of segment dicts with start, end, text.
        """
        segments: list[dict[str, Any]] = []

        # Match timestamp lines: 00:00:00.000 --> 00:00:02.500
        timestamp_pattern = re.compile(
            r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})"
        )

        lines = webvtt_str.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = timestamp_pattern.match(line)
            if match:
                start_str, end_str = match.groups()
                start = self._webvtt_timestamp_to_seconds(start_str)
                end = self._webvtt_timestamp_to_seconds(end_str)

                # Collect text lines until next timestamp or empty line
                text_lines = []
                i += 1
                while i < len(lines):
                    text_line = lines[i].strip()
                    if not text_line or timestamp_pattern.match(text_line):
                        break
                    # Skip cue identifiers (numeric lines before timestamps)
                    if not text_line.isdigit():
                        text_lines.append(text_line)
                    i += 1

                text = " ".join(text_lines)
                if text:
                    segments.append({
                        "start": start,
                        "end": end,
                        "text": text,
                    })
            else:
                i += 1

        return segments

    def _webvtt_timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert WebVTT timestamp to seconds.

        Args:
            timestamp: Timestamp in format HH:MM:SS.mmm or HH:MM:SS,mmm

        Returns:
            Time in seconds as float.
        """
        # Normalize comma to dot for milliseconds
        timestamp = timestamp.replace(",", ".")
        parts = timestamp.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0.0

    # -------------------------------------------------------------------------
    # MAI Transcript endpoints (async AI-powered transcription)
    # -------------------------------------------------------------------------

    async def request_mai_transcript(
        self,
        video_url: str,
        platform: str | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """Request MAI (AI-powered) transcript generation for a video.

        MAI transcript provides dual-layer transcription:
        - videoTranscript: Visual scene descriptions using Gemini VLM
        - audioTranscript: Speech-to-text using Whisper

        This is an async operation. Results are typically delivered via webhook.
        Depending on project configuration, callbacks may come from a default
        dashboard-level callback URL even when webhook_url is omitted.

        Args:
            video_url: Video URL to transcribe.
            platform: Platform name. Auto-detected if not provided.
            webhook_url: Optional webhook URL to receive callback results.

        Returns:
            Task info with task_id.

        Raises:
            ValueError: If platform is not supported.
        """
        if platform is None:
            platform = self.detect_platform(video_url)
        if platform is None:
            raise ValueError(f"Unsupported platform URL: {video_url}")

        endpoint = f"{self.base_url}/{platform}/video/mai/transcript"
        payload: dict[str, Any] = {"video_url": video_url}
        if webhook_url:
            payload["webhook_url"] = webhook_url

        client = await self._get_client(float(self.timeout))
        response = await client.post(
            endpoint,
            headers=self._headers(),
            json=payload,
        )
        return self._decode_json_response(
            response,
            f"/{platform}/video/mai/transcript",
        )

    async def get_mai_transcript_status(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """Get status and results of an MAI transcript task.

        Args:
            task_id: Task ID from request_mai_transcript.

        Returns:
            Task status and results if completed:
            {
                "status": "pending" | "processing" | "completed" | "failed",
                "videoTranscript": "...",  # Visual descriptions (if completed)
                "audioTranscript": "...",  # Speech-to-text (if completed)
                "error": "..."  # Error message (if failed)
            }
        """
        client = await self._get_client(float(self.timeout))
        response = await client.get(
            f"{self.base_url}/task/{task_id}",
            headers=self._headers(),
        )
        return self._decode_json_response(response, f"/task/{task_id}")

    async def wait_for_mai_transcript(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> dict[str, Any]:
        """Wait for MAI transcript task to complete with polling.

        Args:
            task_id: Task ID from request_mai_transcript.
            poll_interval: Seconds between status checks. Defaults to 2.0.
            max_wait: Maximum seconds to wait. Defaults to 300.0 (5 minutes).

        Returns:
            Completed task result with videoTranscript and audioTranscript.

        Raises:
            TimeoutError: If task doesn't complete within max_wait.
            RuntimeError: If task fails.
        """
        elapsed = 0.0
        while elapsed < max_wait:
            status = await self.get_mai_transcript_status(task_id)
            task_status = status.get("status", "unknown")

            if task_status == "completed":
                return status
            elif task_status == "failed":
                error = status.get("error", "Unknown error")
                raise RuntimeError(f"MAI transcript task failed: {error}")
            elif task_status in ("pending", "processing"):
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            else:
                # Unknown status, continue polling
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        raise TimeoutError(
            f"MAI transcript task {task_id} did not complete within {max_wait}s"
        )

    async def get_mai_transcript(
        self,
        video_url: str,
        platform: str | None = None,
        wait: bool = True,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """Get MAI transcript for a video (compatibility convenience method).

        Args:
            video_url: Video URL to transcribe.
            platform: Platform name. Auto-detected if not provided.
            wait: Whether to wait for completion. Defaults to True.
            poll_interval: Seconds between status checks if waiting.
            max_wait: Maximum seconds to wait if waiting.
            webhook_url: Optional webhook URL to receive callback results.

        Returns:
            If wait=True: Completed result when task_id is available.
            If wait=False: Task submission payload.
        """
        task_info = await self.request_mai_transcript(
            video_url=video_url,
            platform=platform,
            webhook_url=webhook_url,
        )

        if not wait:
            return task_info

        task_id: Any = None
        nested_data = task_info.get("data")
        if isinstance(nested_data, dict):
            task_id = nested_data.get("task_id") or nested_data.get("id")

        if task_id is None:
            task_id = task_info.get("task_id") or task_info.get("id")

        if task_id is None:
            # Defensive fallback for unexpected sync-like response shapes.
            return task_info

        return await self.wait_for_mai_transcript(
            str(task_id),
            poll_interval=poll_interval,
            max_wait=max_wait,
        )
