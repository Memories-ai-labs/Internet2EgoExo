"""Video Datalake tools — index a video, read its content, search indexed moments.

These replace the retired v2 metadata/transcript/VLM tools. The Datalake is the
agent's long-term video memory: anything indexed once stays searchable, so later
queries hit `video_moment_search` instead of re-processing the video.
"""

from __future__ import annotations

import logging
from typing import Any

from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.config.settings import get_settings
from video_searching_agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class _DatalakeTool(BaseTool):
    """Shared client wiring and configuration health check."""

    def __init__(self, client: MemoriesDatalakeClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    def health_check(self) -> tuple[bool, str | None]:
        """The tools need a Datalake API key to do anything."""
        if not get_settings().memories_api_key:
            return False, "MEMORIES_API_KEY is not configured"
        return True, None


class VideoIndexTool(_DatalakeTool):
    """Index a video URL into the Datalake without waiting for it to finish."""

    @property
    def name(self) -> str:
        return "video_index"

    @property
    def description(self) -> str:
        return (
            "Add a video to the Memories.ai Video Datalake so its visuals and speech "
            "become searchable. Returns immediately with a video_id and an operation id; "
            "indexing continues in the background and is billed per minute of video. "
            "Use this when the user wants a video added to the library for later search. "
            "To analyse a video now, use video_analysis instead."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_url": {
                    "type": "string",
                    "description": "Direct, publicly reachable URL of the video to index.",
                },
                "fps": {
                    "type": "number",
                    "description": "Frames per second to index at. Default 1.0.",
                },
            },
            "required": ["video_url"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        video_url = kwargs.get("video_url")
        if not video_url:
            return ToolResult.fail("video_url is required")

        try:
            indexed = await self.client.index_video_url(
                source_url=str(video_url),
                fps=kwargs.get("fps"),
            )
        except MemoriesDatalakeError as exc:
            return ToolResult.fail(str(exc))

        return ToolResult.ok({
            "video_id": indexed.get("video_id"),
            "operation": indexed.get("operation"),
            "status": indexed.get("status", "processing"),
            "note": "Indexing runs in the background. Poll with video_analysis once ready.",
        })


class VideoAnalysisTool(_DatalakeTool):
    """Analyse a video's own content via the Datalake's derived content."""

    @property
    def name(self) -> str:
        return "video_analysis"

    @property
    def description(self) -> str:
        return (
            "Analyse what actually happens inside a video: AI title, summary, visual "
            "captions and speech transcription, for the whole video or one time window. "
            "Accepts a video_url (indexed on first use, billed per minute of video) or a "
            "video_id already in the Datalake. Indexing takes time: if it is still running "
            "when the wait budget expires, the tool returns status='processing' with the "
            "video_id so a later call can read the results. Use this for 'what does this "
            "video say/show', transcripts, or summarising a specific video."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_url": {
                    "type": "string",
                    "description": (
                        "Direct, publicly reachable video URL. Indexed if not already."
                    ),
                },
                "video_id": {
                    "type": "string",
                    "description": "Datalake video id, if the video is already indexed.",
                },
                "start": {
                    "type": "number",
                    "description": "Start of the time window in seconds (optional).",
                },
                "end": {
                    "type": "number",
                    "description": "End of the time window in seconds (optional).",
                },
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        video_id = kwargs.get("video_id")
        video_url = kwargs.get("video_url")
        start = kwargs.get("start")
        end = kwargs.get("end")

        if not video_id and not video_url:
            return ToolResult.fail("Either video_url or video_id is required")

        try:
            if not video_id:
                indexed = await self.client.index_video_url(source_url=str(video_url))
                video_id = indexed.get("video_id")
                operation = indexed.get("operation")
                if not video_id:
                    return ToolResult.fail("Indexing returned no video_id")

                if operation:
                    completed = await self.client.wait_for_operation(str(operation))
                    if not completed.get("done"):
                        return ToolResult.ok({
                            "status": "processing",
                            "video_id": video_id,
                            "operation": operation,
                            "progress": completed.get("progress"),
                            "note": (
                                "Still indexing. Call video_analysis again with this "
                                "video_id to read the results."
                            ),
                        })
                    if completed.get("error"):
                        return ToolResult.fail(f"Indexing failed: {completed['error']}")

            return await self._read_content(str(video_id), start, end)
        except MemoriesDatalakeError as exc:
            return ToolResult.fail(str(exc))

    async def _read_content(
        self,
        video_id: str,
        start: float | None,
        end: float | None,
    ) -> ToolResult:
        """Read derived content for a video, tolerating partially ready fields."""
        analysis: dict[str, Any] = {"status": "ready", "video_id": video_id}
        warnings: list[str] = []

        try:
            details = await self.client.get_video(video_id)
            analysis["duration_seconds"] = details.get("duration_seconds")
            analysis["video_status"] = details.get("status")
            metadata = details.get("metadata")
            if isinstance(metadata, dict):
                analysis["title"] = metadata.get("title")
                analysis["tags"] = metadata.get("tags")
        except MemoriesDatalakeError as exc:
            warnings.append(f"video details unavailable: {exc}")

        if start is not None or end is not None:
            analysis["window"] = {"start": start, "end": end}

        for field, reader in (
            ("summary", lambda: self.client.get_summary(video_id)),
            ("caption", lambda: self.client.get_caption(video_id, start=start, end=end)),
            ("transcription", lambda: self.client.get_transcription(
                video_id, start=start, end=end
            )),
        ):
            try:
                payload = await reader()
            except MemoriesDatalakeError as exc:
                # A 409 here means indexing has not produced this field yet.
                warnings.append(f"{field} unavailable: {exc}")
                continue
            analysis[field] = self._flatten(field, payload)

        if not any(analysis.get(f) for f in ("summary", "caption", "transcription")):
            return ToolResult.fail(
                "No derived content available yet for this video "
                f"(video_id={video_id}). It may still be indexing."
            )

        return ToolResult.ok(analysis, warnings=warnings)

    @staticmethod
    def _flatten(field: str, payload: dict[str, Any]) -> Any:
        """Reduce a derived-content payload to the most useful text form."""
        for key in (field, "aggregated"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        segments = payload.get("segments")
        if isinstance(segments, list) and segments:
            return segments
        return None


class VideoMomentSearchTool(_DatalakeTool):
    """Search the indexed Datalake collection for matching moments."""

    @property
    def name(self) -> str:
        return "video_moment_search"

    @property
    def description(self) -> str:
        return (
            "Search videos already indexed in the Memories.ai Video Datalake and get back "
            "the exact moments that match, with timestamps, a snippet and a thumbnail. "
            "This is the agent's video memory: it only covers videos indexed earlier via "
            "video_index or video_analysis, not the open web. Use it to find a moment "
            "inside known videos ('where does she mention the price'), not to discover "
            "new videos — use video_search or the platform search tools for that."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to look for, in natural language.",
                },
                "targets": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["caption", "transcription", "summary", "title", "event"],
                    },
                    "description": "Content to match against. Default caption + transcription.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum moments to return. Default 10.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["semantic", "keyword", "hybrid"],
                    "description": "Match mode. Default semantic.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query")
        if not query:
            return ToolResult.fail("query is required")

        try:
            payload = await self.client.search(
                query=str(query),
                targets=kwargs.get("targets"),
                top_k=int(kwargs.get("top_k") or 10),
                mode=str(kwargs.get("mode") or "semantic"),
            )
        except MemoriesDatalakeError as exc:
            return ToolResult.fail(str(exc))

        results = payload.get("results")
        moments = [
            {
                "ref": item.get("ref"),
                "video_id": item.get("video_id"),
                "target": item.get("target"),
                "score": item.get("score"),
                "start": item.get("start"),
                "end": item.get("end"),
                "snippet": item.get("snippet"),
                "thumbnail_url": item.get("thumbnail_url"),
            }
            for item in (results or [])
            if isinstance(item, dict)
        ]

        if not moments:
            return ToolResult.no_results(
                f"No indexed moments matched '{query}'. "
                "Index the video first with video_index or video_analysis."
            )

        return ToolResult.ok({"moments": moments, "total_results": len(moments)})
