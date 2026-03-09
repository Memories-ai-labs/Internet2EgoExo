"""SSE event models for streaming responses."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


class SSEEvent(BaseModel):
    """Base SSE event model."""

    event: str = Field(..., description="Event type")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")

    def to_sse(self) -> str:
        """Format as SSE message."""
        return f"event: {self.event}\ndata: {json.dumps(self.data)}\n\n"


class StartedEvent(SSEEvent):
    """Emitted when query processing starts."""

    event: str = "started"

    @classmethod
    def create(cls, session_id: str, query: str) -> StartedEvent:
        return cls(data={"session_id": session_id, "query": query})


class ProgressEvent(SSEEvent):
    """Emitted for progress updates during execution."""

    event: str = "progress"

    @classmethod
    def create(cls, step: int, max_steps: int, message: str) -> ProgressEvent:
        return cls(data={"step": step, "max_steps": max_steps, "message": message})


class ToolCallEvent(SSEEvent):
    """Emitted when a tool is being called."""

    event: str = "tool_call"

    @classmethod
    def create(cls, tool: str, input_data: dict[str, Any]) -> ToolCallEvent:
        return cls(data={"tool": tool, "input": input_data})


class ToolResultEvent(SSEEvent):
    """Emitted when a tool returns a result."""

    event: str = "tool_result"

    @classmethod
    def create(
        cls,
        tool: str,
        success: bool,
        videos_found: int | None = None,
        error: str | None = None,
    ) -> ToolResultEvent:
        data: dict[str, Any] = {"tool": tool, "success": success}
        if videos_found is not None:
            data["videos_found"] = videos_found
        if error:
            data["error"] = error
        return cls(data=data)


class ClarificationEvent(SSEEvent):
    """Emitted when clarification is needed from the user."""

    event: str = "clarification_needed"

    @classmethod
    def create(
        cls,
        question: str,
        options: list[str] | None = None,
    ) -> ClarificationEvent:
        data: dict[str, Any] = {"question": question}
        if options:
            data["options"] = options
        return cls(data=data)


class CompleteEvent(SSEEvent):
    """Emitted when query processing completes successfully."""

    event: str = "complete"

    @classmethod
    def create(cls, response: dict[str, Any]) -> CompleteEvent:
        return cls(data=response)


class ErrorEvent(SSEEvent):
    """Emitted when an error occurs."""

    event: str = "error"

    @classmethod
    def create(cls, code: str, message: str, details: dict[str, Any] | None = None) -> ErrorEvent:
        data: dict[str, Any] = {"code": code, "message": message}
        if details:
            data["details"] = details
        return cls(data=data)


class PingEvent(SSEEvent):
    """Keep-alive ping event."""

    event: str = "ping"

    @classmethod
    def create(cls) -> PingEvent:
        return cls(data={})
