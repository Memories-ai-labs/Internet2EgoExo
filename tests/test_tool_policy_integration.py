"""Integration tests for tool-call policy enforcement in runtime loops."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from video_searching_agent.agent.core import VideoSearchingAgent
from video_searching_agent.models.query import ParsedQuery, QueryType, TimeFrame
from video_searching_agent.tools.base import ToolResult
from video_searching_agent.web.streaming.agent_stream import StreamingAgentWrapper


class _DeepToolGemini:
    """Gemini stub that asks for MAI first, then returns final text."""

    def __init__(self) -> None:
        self._calls = 0

    async def create_message_async(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        self._calls += 1
        if self._calls == 1:
            return {
                "done": False,
                "tool_calls": [{
                    "name": "social_media_mai_transcript",
                    "input": {"video_url": "https://twitter.com/user/status/123"},
                }],
            }
        return {"done": True, "text": "done"}

    def convert_tool_definitions(self, tools: list[dict[str, Any]]) -> list[Any]:
        del tools
        return []

    def get_usage_metadata(self, response: dict[str, Any]) -> dict[str, int]:
        del response
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def is_done(self, response: dict[str, Any]) -> bool:
        return bool(response.get("done"))

    def get_text_response(self, response: dict[str, Any]) -> str | None:
        return response.get("text")

    def get_tool_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        return response.get("tool_calls", [])

    def get_response_content(self, response: dict[str, Any]) -> Any:
        del response
        return None


class _MetadataToolGemini:
    """Gemini stub that asks for metadata first, then returns final text."""

    def __init__(self) -> None:
        self._calls = 0

    async def create_message_async(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        self._calls += 1
        if self._calls == 1:
            return {
                "done": False,
                "tool_calls": [{
                    "name": "social_media_metadata",
                    "input": {"video_url": "https://www.youtube.com/watch?v=abc123"},
                }],
            }
        return {"done": True, "text": "done"}

    def convert_tool_definitions(self, tools: list[dict[str, Any]]) -> list[Any]:
        del tools
        return []

    def get_usage_metadata(self, response: dict[str, Any]) -> dict[str, int]:
        del response
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def is_done(self, response: dict[str, Any]) -> bool:
        return bool(response.get("done"))

    def get_text_response(self, response: dict[str, Any]) -> str | None:
        return response.get("text")

    def get_tool_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        return response.get("tool_calls", [])

    def get_response_content(self, response: dict[str, Any]) -> Any:
        del response
        return None


class _TranscriptToolGemini:
    """Gemini stub that asks for transcript first, then returns final text."""

    def __init__(self) -> None:
        self._calls = 0

    async def create_message_async(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        self._calls += 1
        if self._calls == 1:
            return {
                "done": False,
                "tool_calls": [{
                    "name": "social_media_transcript",
                    "input": {"video_url": "https://www.youtube.com/watch?v=abc123"},
                }],
            }
        return {"done": True, "text": "done"}

    def convert_tool_definitions(self, tools: list[dict[str, Any]]) -> list[Any]:
        del tools
        return []

    def get_usage_metadata(self, response: dict[str, Any]) -> dict[str, int]:
        del response
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def is_done(self, response: dict[str, Any]) -> bool:
        return bool(response.get("done"))

    def get_text_response(self, response: dict[str, Any]) -> str | None:
        return response.get("text")

    def get_tool_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        return response.get("tool_calls", [])

    def get_response_content(self, response: dict[str, Any]) -> Any:
        del response
        return None


@pytest.mark.asyncio
async def test_stream_wrapper_rewrites_discovery_deep_tool_to_video_search(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = SimpleNamespace(
        max_agent_steps=3,
        sse_ping_interval=15,
        tool_execution_concurrency=4,
    )
    monkeypatch.setattr(
        "video_searching_agent.web.streaming.agent_stream.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(StreamingAgentWrapper, "_register_tools", lambda self, _: None)

    wrapper = StreamingAgentWrapper(enable_clarification=False)
    wrapper.gemini = _DeepToolGemini()
    wrapper.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(
                original_query=query,
                query_type=QueryType.GENERAL,
                needs_video_analysis=False,
                time_frame=TimeFrame.ALL_TIME,
            ),
        )
    )
    wrapper.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    wrapper.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    called_tools: list[str] = []

    async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        called_tools.append(tool_name)
        return ToolResult.ok({"videos": []})

    wrapper._execute_tool = execute_tool  # type: ignore[assignment]

    events = []
    async for event in wrapper.stream_query("find me top ai ugc videos"):
        events.append(event)

    tool_calls = [e.data["tool"] for e in events if e.event == "tool_call"]
    assert tool_calls == ["video_search"]
    assert called_tools == ["video_search"]


@pytest.mark.asyncio
async def test_stream_wrapper_allows_deep_tool_for_explicit_url_analysis_phrase(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = SimpleNamespace(
        max_agent_steps=3,
        sse_ping_interval=15,
        tool_execution_concurrency=4,
    )
    monkeypatch.setattr(
        "video_searching_agent.web.streaming.agent_stream.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(StreamingAgentWrapper, "_register_tools", lambda self, _: None)

    wrapper = StreamingAgentWrapper(enable_clarification=False)
    wrapper.gemini = _TranscriptToolGemini()
    wrapper.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(
                original_query=query,
                query_type=QueryType.VIDEO_ANALYSIS,
                needs_video_analysis=True,
                video_urls=["https://www.youtube.com/watch?v=abc123"],
                time_frame=TimeFrame.ALL_TIME,
            ),
        )
    )
    wrapper.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    wrapper.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    called_tools: list[str] = []

    async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        called_tools.append(tool_name)
        return ToolResult.ok({"videos": []})

    wrapper._execute_tool = execute_tool  # type: ignore[assignment]

    events = []
    async for event in wrapper.stream_query(
        "what does this video say? https://www.youtube.com/watch?v=abc123"
    ):
        events.append(event)

    tool_calls = [e.data["tool"] for e in events if e.event == "tool_call"]
    assert tool_calls == ["social_media_transcript"]
    assert called_tools == ["social_media_transcript"]


@pytest.mark.asyncio
async def test_stream_wrapper_blocks_deep_tool_for_non_video_url_analysis_phrase(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = SimpleNamespace(
        max_agent_steps=3,
        sse_ping_interval=15,
        tool_execution_concurrency=4,
    )
    monkeypatch.setattr(
        "video_searching_agent.web.streaming.agent_stream.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(StreamingAgentWrapper, "_register_tools", lambda self, _: None)

    wrapper = StreamingAgentWrapper(enable_clarification=False)
    wrapper.gemini = _DeepToolGemini()
    wrapper.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(
                original_query=query,
                query_type=QueryType.GENERAL,
                needs_video_analysis=False,
                video_urls=[],
                time_frame=TimeFrame.ALL_TIME,
            ),
        )
    )
    wrapper.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    wrapper.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    called_tools: list[str] = []

    async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        called_tools.append(tool_name)
        return ToolResult.ok({"videos": []})

    wrapper._execute_tool = execute_tool  # type: ignore[assignment]

    events = []
    async for event in wrapper.stream_query(
        "summarize this article https://medium.com/some-post"
    ):
        events.append(event)

    tool_calls = [e.data["tool"] for e in events if e.event == "tool_call"]
    assert tool_calls == ["video_search"]
    assert called_tools == ["video_search"]


@pytest.mark.asyncio
async def test_stream_wrapper_preserves_metadata_tool_for_url_specific_query(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = SimpleNamespace(
        max_agent_steps=3,
        sse_ping_interval=15,
        tool_execution_concurrency=4,
    )
    monkeypatch.setattr(
        "video_searching_agent.web.streaming.agent_stream.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(StreamingAgentWrapper, "_register_tools", lambda self, _: None)

    wrapper = StreamingAgentWrapper(enable_clarification=False)
    wrapper.gemini = _MetadataToolGemini()
    wrapper.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(
                original_query=query,
                query_type=QueryType.GENERAL,
                needs_video_analysis=False,
                time_frame=TimeFrame.ALL_TIME,
            ),
        )
    )
    wrapper.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    wrapper.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    called_tools: list[str] = []

    async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        called_tools.append(tool_name)
        return ToolResult.ok({"videos": []})

    wrapper._execute_tool = execute_tool  # type: ignore[assignment]

    events = []
    async for event in wrapper.stream_query(
        "how many views does this video have? https://www.youtube.com/watch?v=abc123"
    ):
        events.append(event)

    tool_calls = [e.data["tool"] for e in events if e.event == "tool_call"]
    assert tool_calls == ["social_media_metadata"]
    assert called_tools == ["social_media_metadata"]


@pytest.mark.asyncio
async def test_core_agent_allows_deep_tool_for_explicit_video_analysis(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = SimpleNamespace(max_agent_steps=3, tool_execution_concurrency=4)
    monkeypatch.setattr("video_searching_agent.agent.core.get_settings", lambda: settings)
    monkeypatch.setattr(VideoSearchingAgent, "_register_tools", lambda self, _: None)

    agent = VideoSearchingAgent(enable_clarification=False)
    agent.gemini = _DeepToolGemini()
    agent.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(
                original_query=query,
                query_type=QueryType.VIDEO_ANALYSIS,
                needs_video_analysis=True,
                time_frame=TimeFrame.ALL_TIME,
            ),
        )
    )
    agent.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    agent.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    called_tools: list[str] = []

    async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        called_tools.append(tool_name)
        return ToolResult.ok({"videos": []})

    agent._execute_tool = execute_tool  # type: ignore[assignment]

    response = await agent.query("analyze this video https://twitter.com/user/status/123")
    assert called_tools == ["social_media_mai_transcript"]
    assert [detail["tool"] for detail in response.tool_execution_details] == [
        "social_media_mai_transcript"
    ]


@pytest.mark.asyncio
async def test_core_agent_preserves_metadata_tool_for_url_specific_query(
    monkeypatch: pytest.MonkeyPatch,
):
    settings = SimpleNamespace(max_agent_steps=3, tool_execution_concurrency=4)
    monkeypatch.setattr("video_searching_agent.agent.core.get_settings", lambda: settings)
    monkeypatch.setattr(VideoSearchingAgent, "_register_tools", lambda self, _: None)

    agent = VideoSearchingAgent(enable_clarification=False)
    agent.gemini = _MetadataToolGemini()
    agent.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(
                original_query=query,
                query_type=QueryType.GENERAL,
                needs_video_analysis=False,
                time_frame=TimeFrame.ALL_TIME,
            ),
        )
    )
    agent.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    agent.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    called_tools: list[str] = []

    async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        called_tools.append(tool_name)
        return ToolResult.ok({"videos": []})

    agent._execute_tool = execute_tool  # type: ignore[assignment]

    response = await agent.query(
        "how many views does this video have? https://www.youtube.com/watch?v=abc123"
    )
    assert called_tools == ["social_media_metadata"]
    assert [detail["tool"] for detail in response.tool_execution_details] == [
        "social_media_metadata"
    ]
