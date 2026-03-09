"""Tests for OpenClaw NDJSON runner integration."""

from __future__ import annotations

import asyncio
import inspect
import json
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from video_searching_agent.integrations import openclaw_runner


def _parse_ndjson(text: str) -> list[dict[str, object]]:
    lines = [line for line in text.splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def _monotonic_sequence(values: list[float]):
    iterator = iter(values)
    last = values[-1]

    def _next() -> float:
        nonlocal last
        try:
            last = next(iterator)
        except StopIteration:
            return last
        return last

    return _next


class OrderedWrapper:
    """Fake wrapper that emits a deterministic successful stream."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        assert user_query == "find trending videos"
        assert clarification is None
        assert max_steps == 6
        assert enable_clarification is True
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        yield SimpleNamespace(event="progress", data={
            "step": 1,
            "max_steps": 6,
            "message": "Parsing",
        })
        yield SimpleNamespace(event="tool_call", data={
            "tool": "youtube_search",
            "input": {"query": "trending"},
        })
        yield SimpleNamespace(event="tool_result", data={
            "tool": "youtube_search",
            "success": True,
            "videos_found": 12,
        })
        yield SimpleNamespace(event="complete", data={
            "answer": "Top videos found.",
            "video_references": [{"title": "Video A", "url": "https://example.com/a"}],
            "tools_used": ["youtube_search"],
            "steps_taken": 2,
            "execution_time_seconds": 1.25,
            "session_id": "s1",
        })


class ExplodingWrapper:
    """Fake wrapper that raises an exception mid-stream."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        raise RuntimeError("boom")
        if False:  # pragma: no cover - keeps this function an async generator
            yield None


class ToolPayloadWrapper:
    """Fake wrapper for detail-level assertions."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="tool_call", data={
            "tool": "exa_search",
            "input": {"query": "should-hide-in-compact"},
        })
        yield SimpleNamespace(event="complete", data={
            "answer": "Done.",
            "video_references": [],
            "tools_used": ["exa_search"],
            "steps_taken": 1,
            "execution_time_seconds": 0.5,
            "session_id": "verbose-only-field",
        })


class ErrorEventWrapper:
    """Fake wrapper that emits an error event instead of raising."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        yield SimpleNamespace(event="error", data={
            "code": "agent_error",
            "message": "upstream failed",
        })


class ClarificationWrapper:
    """Fake wrapper that asks for clarification."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        yield SimpleNamespace(event="progress", data={
            "step": 1,
            "max_steps": 6,
            "message": "Parsing query...",
        })
        yield SimpleNamespace(event="clarification_needed", data={
            "question": "Which platform do you want?",
            "options": ["YouTube", "TikTok"],
        })


class SlowCompleteWrapper:
    """Fake wrapper to test throttled progress behavior over time."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        yield SimpleNamespace(event="progress", data={
            "step": 1,
            "max_steps": 10,
            "message": "Searching platforms",
        })
        yield SimpleNamespace(
            event="tool_call",
            data={"tool": "youtube_search", "input": {"query": "x"}},
        )
        yield SimpleNamespace(
            event="tool_result",
            data={"tool": "youtube_search", "success": True, "videos_found": 5},
        )
        yield SimpleNamespace(
            event="tool_call",
            data={"tool": "exa_search", "input": {"query": "x"}},
        )
        yield SimpleNamespace(
            event="tool_result",
            data={"tool": "exa_search", "success": False, "error": "timeout"},
        )
        yield SimpleNamespace(event="complete", data={
            "answer": "Done.",
            "video_references": [],
            "tools_used": ["youtube_search", "exa_search"],
            "steps_taken": 3,
            "execution_time_seconds": 8.0,
        })


class CompleteOnlyWrapper:
    """Fake wrapper that completes without intermediate progress/tool events."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        yield SimpleNamespace(event="complete", data={
            "answer": "Done.",
            "video_references": [],
            "tools_used": [],
            "steps_taken": 1,
            "execution_time_seconds": 7.0,
        })


class DelayedCompleteWrapper:
    """Fake wrapper that pauses before terminal event."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        await asyncio.sleep(0.05)
        yield SimpleNamespace(event="complete", data={
            "answer": "Done.",
            "video_references": [],
            "tools_used": [],
            "steps_taken": 1,
            "execution_time_seconds": 0.05,
        })


class NoTerminalWrapper:
    """Fake wrapper that exits without a terminal event."""

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
    ):
        yield SimpleNamespace(event="started", data={"session_id": "s1", "query": user_query})
        yield SimpleNamespace(event="progress", data={
            "step": 1,
            "max_steps": 10,
            "message": "Working",
        })


def test_ux_state_summary_is_minimal_and_conditional():
    """Summary should only include sections with meaningful data."""
    state = openclaw_runner._UxState(started_at=0.0)

    assert state.summary() == openclaw_runner.PROGRESS_STAGE_PLACEHOLDER

    state.absorb_event("progress", {"message": "Searching platforms"})
    assert state.summary() == "Searching platforms"

    state.absorb_event("tool_call", {"tool": "youtube_search"})
    assert state.summary() == "Searching platforms | tools: youtube_search"

    state.absorb_event("tool_result", {"tool": "youtube_search", "success": True})
    assert state.summary() == "Searching platforms | tools: youtube_search | success: 1"

    state.absorb_event("tool_result", {"tool": "exa_search", "success": False})
    assert state.summary() == (
        "Searching platforms | tools: youtube_search, exa_search | success: 1 | failed: 1"
    )


def test_ux_state_never_reuses_starting_message_in_summary():
    """Starting label should remain reserved for the first deterministic message."""
    state = openclaw_runner._UxState(started_at=0.0)
    state.absorb_event("progress", {"message": openclaw_runner.STARTING_STAGE_MESSAGE})

    assert state.summary() == openclaw_runner.PROGRESS_STAGE_PLACEHOLDER
    assert openclaw_runner.STARTING_STAGE_MESSAGE not in state.summary()


@pytest.mark.asyncio
async def test_event_ordering_and_json_validity(monkeypatch: pytest.MonkeyPatch):
    """Runner should emit valid NDJSON in expected event order."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", OrderedWrapper)

    out = StringIO()
    err = StringIO()
    code = await openclaw_runner.run_query_stream(
        query="find trending videos",
        clarification=None,
        max_steps=6,
        detail=openclaw_runner.EventDetail.COMPACT,
        ux_mode=openclaw_runner.UxMode.RAW,
        out=out,
        err=err,
    )

    assert code == 0
    assert err.getvalue() == ""

    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == [
        "started",
        "progress",
        "tool_call",
        "tool_result",
        "complete",
    ]

    for payload in payloads:
        assert "event" in payload
        assert "data" in payload

    complete = payloads[-1]["data"]
    assert isinstance(complete, dict)
    assert "answer" in complete
    assert "video_references" in complete
    assert "tools_used" in complete
    assert "steps_taken" in complete
    assert "execution_time_seconds" not in complete


@pytest.mark.asyncio
async def test_error_exit_path_and_stderr(monkeypatch: pytest.MonkeyPatch):
    """Runner should emit an error event and non-zero exit code on exception."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", ExplodingWrapper)

    out = StringIO()
    err = StringIO()
    code = await openclaw_runner.run_query_stream(
        query="find trending videos",
        clarification=None,
        max_steps=None,
        detail=openclaw_runner.EventDetail.COMPACT,
        ux_mode=openclaw_runner.UxMode.RAW,
        out=out,
        err=err,
    )

    assert code == 1
    assert "openclaw_runner failed: boom" in err.getvalue()

    payloads = _parse_ndjson(out.getvalue())
    assert len(payloads) == 1
    assert payloads[0]["event"] == "error"
    assert payloads[0]["data"] == {"code": "runner_error", "message": "boom"}


@pytest.mark.asyncio
async def test_compact_vs_verbose_event_detail(monkeypatch: pytest.MonkeyPatch):
    """Compact mode should hide raw tool input while verbose keeps full payloads."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", ToolPayloadWrapper)

    compact_out = StringIO()
    compact_err = StringIO()
    compact_code = await openclaw_runner.run_query_stream(
        query="q",
        clarification=None,
        max_steps=None,
        detail=openclaw_runner.EventDetail.COMPACT,
        ux_mode=openclaw_runner.UxMode.RAW,
        out=compact_out,
        err=compact_err,
    )
    assert compact_code == 0
    compact_payloads = _parse_ndjson(compact_out.getvalue())
    assert compact_payloads[0]["event"] == "tool_call"
    assert compact_payloads[0]["data"] == {"tool": "exa_search", "status": "running"}
    assert set(compact_payloads[1]["data"].keys()) == {
        "answer",
        "video_references",
        "tools_used",
        "steps_taken",
    }

    verbose_out = StringIO()
    verbose_err = StringIO()
    verbose_code = await openclaw_runner.run_query_stream(
        query="q",
        clarification=None,
        max_steps=None,
        detail=openclaw_runner.EventDetail.VERBOSE,
        ux_mode=openclaw_runner.UxMode.RAW,
        out=verbose_out,
        err=verbose_err,
    )
    assert verbose_code == 0
    verbose_payloads = _parse_ndjson(verbose_out.getvalue())
    assert verbose_payloads[0]["data"]["input"] == {"query": "should-hide-in-compact"}
    assert verbose_payloads[1]["data"]["session_id"] == "verbose-only-field"


@pytest.mark.asyncio
async def test_error_event_stream_sets_nonzero_exit(monkeypatch: pytest.MonkeyPatch):
    """A streamed error event should produce non-zero exit code."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", ErrorEventWrapper)

    out = StringIO()
    err = StringIO()
    code = await openclaw_runner.run_query_stream(
        query="q",
        clarification=None,
        max_steps=None,
        detail=openclaw_runner.EventDetail.COMPACT,
        ux_mode=openclaw_runner.UxMode.RAW,
        out=out,
        err=err,
    )
    assert code == 1
    assert err.getvalue() == ""
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "error"]


def test_query_validation_rejects_whitespace_only():
    """CLI parser should reject empty/whitespace-only query values."""
    with pytest.raises(SystemExit):
        openclaw_runner.parse_args(["--query", "   "])


@pytest.mark.parametrize("value", ["0", "61", "abc"])
def test_progress_gate_validation_rejects_invalid_values(value: str):
    """CLI parser should reject invalid progress gate values."""
    with pytest.raises(SystemExit):
        openclaw_runner.parse_args(["--query", "ok", "--progress-gate-seconds", value])


def test_progress_gate_default_is_five_seconds():
    """CLI parser default aligns with deterministic 5-second heartbeat cadence."""
    args = openclaw_runner.parse_args(["--query", "ok"])
    assert args.progress_gate_seconds == 5


def test_run_query_stream_default_progress_gate_matches_setting_default():
    """Programmatic runner default should match configured OpenClaw progress gate."""
    signature = inspect.signature(openclaw_runner.run_query_stream)
    default_value = signature.parameters["progress_gate_seconds"].default
    assert default_value == openclaw_runner.DEFAULT_PROGRESS_GATE_SECONDS == 5


def test_progress_gate_default_can_be_overridden_by_env(monkeypatch: pytest.MonkeyPatch):
    """CLI parser should read OPENCLAW_PROGRESS_GATE_SECONDS when set."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")
    monkeypatch.setenv("OPENCLAW_PROGRESS_GATE_SECONDS", "9")
    args = openclaw_runner.parse_args(["--query", "ok"])
    assert args.progress_gate_seconds == 9


def test_progress_gate_default_reads_from_settings(monkeypatch: pytest.MonkeyPatch):
    """CLI parser should use app settings source (including .env loading semantics)."""
    monkeypatch.setattr(
        openclaw_runner,
        "get_settings",
        lambda: SimpleNamespace(openclaw_progress_gate_seconds=11),
    )
    args = openclaw_runner.parse_args(["--query", "ok"])
    assert args.progress_gate_seconds == 11


@pytest.mark.asyncio
async def test_three_message_fast_run_emits_two_messages(monkeypatch: pytest.MonkeyPatch):
    """Fast runs in three_message mode should emit started + terminal only."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", OrderedWrapper)
    out = StringIO()
    err = StringIO()

    # Fake monotonic times keep elapsed below the 10s gate.
    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            100.0,
            100.5,
            101.0,
            101.5,
            102.0,
            102.2,
            102.3,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="find trending videos",
            clarification=None,
            max_steps=6,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "complete"]


@pytest.mark.asyncio
async def test_three_message_slow_run_emits_multiple_progress_updates(
    monkeypatch: pytest.MonkeyPatch,
):
    """Slow runs should emit recurring throttled ux_progress events."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", SlowCompleteWrapper)
    out = StringIO()
    err = StringIO()

    # Gate crossings should produce multiple throttled progress events.
    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            10.0,
            12.0,
            20.2,
            21.0,
            30.5,
            31.0,
            31.5,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "ux_progress", "ux_progress", "complete"]

    first_middle = payloads[1]["data"]
    assert isinstance(first_middle, dict)
    assert first_middle["elapsed_seconds"] >= 10
    assert first_middle["tools_seen"] == ["youtube_search"]
    assert first_middle["success_count"] == 0
    assert first_middle["failure_count"] == 0
    assert first_middle["summary"] == "Searching platforms | tools: youtube_search"

    second_middle = payloads[2]["data"]
    assert isinstance(second_middle, dict)
    assert second_middle["elapsed_seconds"] >= 20
    assert second_middle["tools_seen"] == ["youtube_search", "exa_search"]
    assert second_middle["success_count"] == 1
    assert second_middle["failure_count"] == 0
    assert second_middle["summary"] == (
        "Searching platforms | tools: youtube_search, exa_search | success: 1"
    )


@pytest.mark.asyncio
async def test_three_message_progress_updates_are_throttled(monkeypatch: pytest.MonkeyPatch):
    """Progress updates should not emit more often than the gate interval."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", SlowCompleteWrapper)
    out = StringIO()
    err = StringIO()

    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            10.0,
            20.2,
            21.0,
            21.5,
            22.0,
            22.4,
            22.8,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "ux_progress", "complete"]


@pytest.mark.asyncio
async def test_three_message_long_complete_without_intermediate_events(
    monkeypatch: pytest.MonkeyPatch,
):
    """Long run with terminal-only events still emits progress before completion."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", CompleteOnlyWrapper)
    out = StringIO()
    err = StringIO()

    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            10.0,
            20.5,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "ux_progress", "complete"]
    middle = payloads[1]["data"]
    assert isinstance(middle, dict)
    assert middle["tools_seen"] == []
    assert middle["success_count"] == 0
    assert middle["failure_count"] == 0
    assert middle["stage"] == openclaw_runner.PROGRESS_STAGE_PLACEHOLDER
    assert middle["summary"] == openclaw_runner.PROGRESS_STAGE_PLACEHOLDER
    assert openclaw_runner.STARTING_STAGE_MESSAGE not in middle["summary"]


@pytest.mark.asyncio
async def test_three_message_emits_heartbeat_while_stream_is_idle(
    monkeypatch: pytest.MonkeyPatch,
):
    """Idle polling should still emit heartbeat ux_progress events."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", CompleteOnlyWrapper)
    out = StringIO()
    err = StringIO()

    call_state = {"calls": 0}

    async def fake_poll_stream_event(event_iter, *, timeout_seconds: float, state):
        del timeout_seconds
        del state
        call_state["calls"] += 1
        if call_state["calls"] in {2, 3}:
            return None
        return await anext(event_iter)

    monkeypatch.setattr(openclaw_runner, "poll_stream_event", fake_poll_stream_event)
    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            100.0,
            111.0,
            122.0,
            123.0,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "ux_progress", "ux_progress", "complete"]


@pytest.mark.asyncio
async def test_three_message_idle_poll_does_not_cancel_stream(monkeypatch: pytest.MonkeyPatch):
    """Timeout-based idle polling must not cancel the underlying stream."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", DelayedCompleteWrapper)
    monkeypatch.setattr(openclaw_runner, "IDLE_POLL_SECONDS", 0.01)
    out = StringIO()
    err = StringIO()

    code = await openclaw_runner.run_query_stream(
        query="q",
        clarification=None,
        max_steps=None,
        detail=openclaw_runner.EventDetail.COMPACT,
        ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
        progress_gate_seconds=10,
        out=out,
        err=err,
    )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert payloads[0]["event"] == "started"
    assert payloads[-1]["event"] == "complete"
    assert all(p["event"] != "error" for p in payloads)


@pytest.mark.asyncio
async def test_three_message_clarification_is_terminal(monkeypatch: pytest.MonkeyPatch):
    """Clarification-needed should be terminal in three_message mode."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", ClarificationWrapper)
    out = StringIO()
    err = StringIO()

    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            50.0,
            53.0,
            60.5,
            60.7,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )

    assert code == 0
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "ux_progress", "clarification_needed"]
    middle = payloads[1]["data"]
    assert isinstance(middle, dict)
    assert middle["elapsed_seconds"] >= 10


@pytest.mark.asyncio
async def test_three_message_error_is_nonzero(monkeypatch: pytest.MonkeyPatch):
    """Error terminal remains non-zero in three_message mode."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", ErrorEventWrapper)
    out = StringIO()
    err = StringIO()
    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            1.0,
            2.0,
            2.1,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )
    assert code == 1
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "error"]


@pytest.mark.asyncio
async def test_three_message_missing_terminal_emits_runner_error(monkeypatch: pytest.MonkeyPatch):
    """A non-terminal stream should emit runner error and return non-zero."""
    monkeypatch.setattr(openclaw_runner, "StreamingAgentWrapper", NoTerminalWrapper)
    out = StringIO()
    err = StringIO()
    with patch(
        "video_searching_agent.integrations.openclaw_runner.monotonic_now",
        side_effect=_monotonic_sequence([
            20.0,
            21.0,
        ]),
    ):
        code = await openclaw_runner.run_query_stream(
            query="q",
            clarification=None,
            max_steps=None,
            detail=openclaw_runner.EventDetail.COMPACT,
            ux_mode=openclaw_runner.UxMode.THREE_MESSAGE,
            progress_gate_seconds=10,
            out=out,
            err=err,
        )
    assert code == 1
    payloads = _parse_ndjson(out.getvalue())
    assert [p["event"] for p in payloads] == ["started", "error"]
    assert payloads[1]["data"]["code"] == "runner_error"
