"""Performance-focused tests for streaming agent execution behavior."""

from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace
from typing import Any

import pytest

from video_searching_agent.agent.core import VideoSearchingAgent
from video_searching_agent.models.query import ParsedQuery, TimeFrame
from video_searching_agent.tools.base import ToolResult
from video_searching_agent.web.streaming.agent_stream import StreamingAgentWrapper


class _SingleToolGemini:
    """Gemini stub that produces one tool call then a final answer."""

    def __init__(self, gemini_delay_seconds: float = 0.05):
        self._calls = 0
        self._delay = gemini_delay_seconds

    def create_message(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Blocking create_message() path should not be used")

    async def create_message_async(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(self._delay)
        self._calls += 1
        if self._calls == 1:
            return {
                "done": False,
                "tool_calls": [{"name": "slow_tool", "input": {"query": "q"}}],
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


class _TwoToolGemini(_SingleToolGemini):
    """Gemini stub that emits two tool calls in one turn."""

    async def create_message_async(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(self._delay)
        self._calls += 1
        if self._calls == 1:
            return {
                "done": False,
                "tool_calls": [
                    {"name": "tool_a", "input": {"query": "a"}},
                    {"name": "tool_b", "input": {"query": "b"}},
                ],
            }
        return {"done": True, "text": "done"}


async def _collect_events(wrapper: StreamingAgentWrapper, query: str) -> list[Any]:
    """Collect all emitted SSE events from a stream query."""
    events = []
    async for event in wrapper.stream_query(query):
        events.append(event)
    return events


def _build_wrapper(
    monkeypatch: pytest.MonkeyPatch,
    gemini_stub: _SingleToolGemini,
) -> StreamingAgentWrapper:
    """Build a wrapper with lightweight dependencies for execution tests."""
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

    wrapper = StreamingAgentWrapper()
    wrapper.gemini = gemini_stub
    wrapper.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(original_query=query, time_frame=TimeFrame.ALL_TIME),
        )
    )
    wrapper.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    wrapper.tools = SimpleNamespace(get_tool_definitions=lambda: [])
    return wrapper


@pytest.mark.asyncio
async def test_concurrent_queries_do_not_block_each_other(monkeypatch: pytest.MonkeyPatch):
    """Concurrent stream queries should overlap instead of serializing."""
    wrapper_a = _build_wrapper(monkeypatch, _SingleToolGemini())
    wrapper_b = _build_wrapper(monkeypatch, _SingleToolGemini())

    async def slow_execute(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_name
        del tool_input
        await asyncio.sleep(0.2)
        return ToolResult.ok({"videos": [], "total_results": 0})

    wrapper_a._execute_tool = slow_execute  # type: ignore[assignment]
    wrapper_b._execute_tool = slow_execute  # type: ignore[assignment]

    started_at = time.perf_counter()
    events_a, events_b = await asyncio.gather(
        _collect_events(wrapper_a, "q1"),
        _collect_events(wrapper_b, "q2"),
    )
    elapsed = time.perf_counter() - started_at

    assert any(event.event == "complete" for event in events_a)
    assert any(event.event == "complete" for event in events_b)
    # Each run is ~0.3s; concurrent should stay far below ~0.6s serialized runtime.
    assert elapsed < 0.5


@pytest.mark.asyncio
async def test_parallel_tool_calls_preserve_order(monkeypatch: pytest.MonkeyPatch):
    """Multiple tool calls from one Gemini turn should run in parallel and keep order."""
    wrapper = _build_wrapper(monkeypatch, _TwoToolGemini())

    async def slow_execute(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        await asyncio.sleep(0.2)
        return ToolResult.ok({"videos": [{"url": f"https://example.com/{tool_name}"}]})

    wrapper._execute_tool = slow_execute  # type: ignore[assignment]

    started_at = time.perf_counter()
    events = await _collect_events(wrapper, "parallel tools")
    elapsed = time.perf_counter() - started_at

    tool_result_tools = [
        event.data["tool"]
        for event in events
        if event.event == "tool_result"
    ]
    assert tool_result_tools == ["tool_a", "tool_b"]
    # Two 0.2s tools should overlap when executed in parallel.
    assert elapsed < 0.4


@pytest.mark.asyncio
async def test_parallel_tool_calls_emit_ordered_prefix_before_completion(
    monkeypatch: pytest.MonkeyPatch,
):
    """Streaming should emit ordered tool results before final completion when possible."""
    wrapper = _build_wrapper(monkeypatch, _TwoToolGemini())

    async def variable_execute(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        await asyncio.sleep(0.05 if tool_name == "tool_a" else 0.25)
        return ToolResult.ok({"videos": [{"url": f"https://example.com/{tool_name}"}]})

    wrapper._execute_tool = variable_execute  # type: ignore[assignment]

    started_at = time.perf_counter()
    first_tool_result_at: float | None = None
    completed_at: float | None = None

    async for event in wrapper.stream_query("parallel tools"):
        elapsed = time.perf_counter() - started_at
        if event.event == "tool_result" and event.data["tool"] == "tool_a":
            first_tool_result_at = elapsed
        elif event.event == "complete":
            completed_at = elapsed

    assert first_tool_result_at is not None
    assert completed_at is not None
    # First tool result should be visible well before final completion.
    assert completed_at - first_tool_result_at > 0.12


@pytest.mark.asyncio
async def test_core_agent_parallel_tool_calls_preserve_order(monkeypatch: pytest.MonkeyPatch):
    """Core agent should parallelize same-turn tool calls while preserving ordering."""
    settings = SimpleNamespace(max_agent_steps=3, tool_execution_concurrency=4)
    monkeypatch.setattr("video_searching_agent.agent.core.get_settings", lambda: settings)
    monkeypatch.setattr(VideoSearchingAgent, "_register_tools", lambda self, _: None)

    agent = VideoSearchingAgent(enable_clarification=False)
    agent.gemini = _TwoToolGemini()
    agent.query_parser = SimpleNamespace(
        parse=lambda query: asyncio.sleep(
            0,
            result=ParsedQuery(original_query=query, time_frame=TimeFrame.ALL_TIME),
        )
    )
    agent.clarification_manager = SimpleNamespace(needs_clarification=lambda parsed: False)
    agent.tools = SimpleNamespace(get_tool_definitions=lambda: [])

    async def slow_execute(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_input
        await asyncio.sleep(0.2)
        return ToolResult.ok({"videos": [{"url": f"https://example.com/{tool_name}"}]})

    agent._execute_tool = slow_execute  # type: ignore[assignment]

    started_at = time.perf_counter()
    response = await agent.query("parallel tools")
    elapsed = time.perf_counter() - started_at

    ordered_tools = [detail["tool"] for detail in response.tool_execution_details]
    assert ordered_tools == ["tool_a", "tool_b"]
    assert elapsed < 0.4


@pytest.mark.asyncio
async def test_core_agent_cancels_pending_parallel_tasks_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
):
    """Core agent should cancel in-flight same-turn tool tasks when cancelled."""
    settings = SimpleNamespace(max_agent_steps=3, tool_execution_concurrency=4)
    monkeypatch.setattr("video_searching_agent.agent.core.get_settings", lambda: settings)
    monkeypatch.setattr(VideoSearchingAgent, "_register_tools", lambda self, _: None)

    agent = VideoSearchingAgent(enable_clarification=False)
    started = 0
    all_started = asyncio.Event()
    blocker = asyncio.Event()

    async def blocked_execute(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_name
        del tool_input
        nonlocal started
        started += 1
        if started == 2:
            all_started.set()
        await blocker.wait()
        return ToolResult.ok({"videos": []})

    agent._execute_tool = blocked_execute  # type: ignore[assignment]

    created_tasks: list[asyncio.Task[Any]] = []
    real_create_task = asyncio.create_task

    def tracking_create_task(coro: Any, *args: Any, **kwargs: Any) -> asyncio.Task[Any]:
        task = real_create_task(coro, *args, **kwargs)
        created_tasks.append(task)
        return task

    monkeypatch.setattr(
        "video_searching_agent.agent.core.asyncio.create_task",
        tracking_create_task,
    )

    parent_task = asyncio.create_task(
        agent._execute_tool_calls_in_order(
            [(0, "tool_a", {"query": "a"}), (1, "tool_b", {"query": "b"})]
        )
    )

    try:
        await asyncio.wait_for(all_started.wait(), timeout=1.0)
        parent_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await parent_task
        await asyncio.sleep(0)
        bounded_tasks = [
            task
            for task in created_tasks
            if "_execute_bounded" in getattr(task.get_coro(), "__qualname__", "")
        ]
        assert len(bounded_tasks) == 2
        assert all(task.cancelled() for task in bounded_tasks)
    finally:
        if not parent_task.done():
            parent_task.cancel()
            try:
                await parent_task
            except asyncio.CancelledError:
                pass
        for task in created_tasks:
            if not task.done():
                task.cancel()
        if created_tasks:
            await asyncio.gather(*created_tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_streaming_wrapper_cancels_pending_parallel_tasks_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
):
    """Streaming helper should cancel in-flight tool tasks on cancellation."""
    wrapper = _build_wrapper(monkeypatch, _TwoToolGemini())
    started = 0
    all_started = asyncio.Event()
    blocker = asyncio.Event()

    async def blocked_execute(tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        del tool_name
        del tool_input
        nonlocal started
        started += 1
        if started == 2:
            all_started.set()
        await blocker.wait()
        return ToolResult.ok({"videos": []})

    wrapper._execute_tool = blocked_execute  # type: ignore[assignment]

    created_tasks: list[asyncio.Task[Any]] = []
    real_create_task = asyncio.create_task

    def tracking_create_task(coro: Any, *args: Any, **kwargs: Any) -> asyncio.Task[Any]:
        task = real_create_task(coro, *args, **kwargs)
        created_tasks.append(task)
        return task

    monkeypatch.setattr(
        "video_searching_agent.web.streaming.agent_stream.asyncio.create_task",
        tracking_create_task,
    )

    result_iter = wrapper._iter_tool_call_results_in_order(
        [(0, "tool_a", {"query": "a"}), (1, "tool_b", {"query": "b"})]
    )
    next_result_task = asyncio.create_task(anext(result_iter))

    try:
        await asyncio.wait_for(all_started.wait(), timeout=1.0)
        next_result_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await next_result_task
        await asyncio.sleep(0)
        bounded_tasks = [
            task
            for task in created_tasks
            if "_execute_bounded" in getattr(task.get_coro(), "__qualname__", "")
        ]
        assert len(bounded_tasks) == 2
        assert all(task.cancelled() for task in bounded_tasks)
    finally:
        if not next_result_task.done():
            next_result_task.cancel()
            try:
                await next_result_task
            except asyncio.CancelledError:
                pass
        await result_iter.aclose()
        for task in created_tasks:
            if not task.done():
                task.cancel()
        if created_tasks:
            await asyncio.gather(*created_tasks, return_exceptions=True)
