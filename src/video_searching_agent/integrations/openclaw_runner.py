"""CLI runner for OpenClaw skill integration.

This module streams agent events as NDJSON for command-line consumers.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import sys
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TextIO

from video_searching_agent.config.settings import Settings, get_settings
from video_searching_agent.web.streaming.agent_stream import StreamingAgentWrapper


class EventDetail(StrEnum):
    """Detail level for emitted NDJSON events."""

    COMPACT = "compact"
    VERBOSE = "verbose"


class UxMode(StrEnum):
    """Output UX mode for stream shaping."""

    RAW = "raw"
    THREE_MESSAGE = "three_message"


IDLE_POLL_SECONDS = 1.0
STARTING_STAGE_MESSAGE = "Starting video searching..."
PROGRESS_STAGE_PLACEHOLDER = "In progress..."
DEFAULT_PROGRESS_GATE_SECONDS = int(
    Settings.model_fields["openclaw_progress_gate_seconds"].default or 5
)


def monotonic_now() -> float:
    """Runner-local monotonic clock helper (test-friendly)."""
    return time.monotonic()


def _non_empty_query(value: str) -> str:
    """Argparse validator for user query."""
    cleaned = value.strip()
    if not cleaned:
        raise argparse.ArgumentTypeError("query must not be empty or whitespace-only")
    return cleaned


def _bounded_max_steps(value: str) -> int:
    """Argparse validator for max steps."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("max_steps must be an integer") from exc
    if parsed < 1 or parsed > 20:
        raise argparse.ArgumentTypeError("max_steps must be in range [1, 20]")
    return parsed


def _bounded_progress_gate(value: str) -> int:
    """Argparse validator for throttled progress gate seconds."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("progress_gate_seconds must be an integer") from exc
    if parsed < 1 or parsed > 60:
        raise argparse.ArgumentTypeError("progress_gate_seconds must be in range [1, 60]")
    return parsed


def _default_progress_gate_seconds() -> int:
    """Resolve default progress gate from app settings with safe fallback."""
    try:
        clear_cache = getattr(get_settings, "cache_clear", None)
        if callable(clear_cache):
            clear_cache()
        configured = get_settings().openclaw_progress_gate_seconds
        return _bounded_progress_gate(str(configured))
    except Exception:
        return DEFAULT_PROGRESS_GATE_SECONDS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run Video Searching Agent for OpenClaw and emit NDJSON events.",
    )
    parser.add_argument(
        "--query",
        required=True,
        type=_non_empty_query,
        help="Natural language query to run against the video searching agent.",
    )
    parser.add_argument(
        "--clarification",
        default=None,
        help="Optional clarification text appended to the user query context.",
    )
    parser.add_argument(
        "--max-steps",
        type=_bounded_max_steps,
        default=None,
        help="Override maximum agent steps for this run.",
    )
    parser.add_argument(
        "--event-detail",
        choices=[e.value for e in EventDetail],
        default=EventDetail.COMPACT.value,
        help="Event detail level for NDJSON payloads.",
    )
    parser.add_argument(
        "--ux-mode",
        choices=[m.value for m in UxMode],
        default=UxMode.RAW.value,
        help="UX shaping mode for emitted events.",
    )
    parser.add_argument(
        "--progress-gate-seconds",
        type=_bounded_progress_gate,
        default=_default_progress_gate_seconds(),
        help=(
            "Emit throttled progress once elapsed time reaches this threshold, "
            "then at the same interval while running."
        ),
    )
    return parser.parse_args(argv)


def _compact_complete_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Keep complete events concise and stable for chat UX."""
    return {
        "answer": data.get("answer", ""),
        "video_references": data.get("video_references", []),
        "tools_used": data.get("tools_used", []),
        "steps_taken": data.get("steps_taken", 0),
    }


def _compact_tool_call_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Hide raw tool input by default."""
    return {
        "tool": data.get("tool"),
        "status": "running",
    }


def _compact_tool_result_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize tool result status for concise progress display."""
    status = "success" if data.get("success") else "failed"
    compact: dict[str, Any] = {
        "tool": data.get("tool"),
        "status": status,
    }
    if "videos_found" in data:
        compact["videos_found"] = data.get("videos_found")
    if status == "failed" and data.get("error"):
        compact["error"] = data.get("error")
    return compact


def compact_event_payload(event: str, data: dict[str, Any]) -> dict[str, Any]:
    """Create compact payloads aligned to chat-first UX."""
    if event == "tool_call":
        return _compact_tool_call_payload(data)
    if event == "tool_result":
        return _compact_tool_result_payload(data)
    if event == "complete":
        return _compact_complete_payload(data)
    return data


def format_event(event: str, data: dict[str, Any], detail: EventDetail) -> dict[str, Any]:
    """Format event output based on detail level."""
    payload = data if detail == EventDetail.VERBOSE else compact_event_payload(event, data)
    return {"event": event, "data": payload}


def emit_event(out: TextIO, payload: dict[str, Any]) -> None:
    """Emit one NDJSON line and flush immediately."""
    out.write(json.dumps(payload, ensure_ascii=False) + "\n")
    out.flush()


async def poll_stream_event(
    event_iter: AsyncIterator[Any],
    *,
    timeout_seconds: float,
    state: _StreamPollState,
) -> Any | None:
    """Read one stream event with timeout and return None when idle.

    Keeps a persistent pending `anext` task so timeout polling doesn't cancel
    the stream's next event retrieval.
    """
    if state.pending_event_task is None:
        state.pending_event_task = asyncio.create_task(anext(event_iter))

    done, _pending = await asyncio.wait({state.pending_event_task}, timeout=timeout_seconds)
    if not done:
        return None

    task = state.pending_event_task
    state.pending_event_task = None
    return task.result()


@dataclass
class _StreamPollState:
    """State container for non-cancelling async stream polling."""

    pending_event_task: asyncio.Task[Any] | None = None


@dataclass
class _UxState:
    """State container for throttled UX progress mode."""

    started_at: float
    latest_stage: str = STARTING_STAGE_MESSAGE
    has_progress_stage: bool = False
    success_count: int = 0
    failure_count: int = 0
    tools_seen: list[str] = field(default_factory=list)
    last_progress_emit_at: float | None = None

    def add_tool(self, tool: str | None) -> None:
        if tool and tool not in self.tools_seen:
            self.tools_seen.append(tool)

    def absorb_event(self, event: str, data: dict[str, Any]) -> None:
        if event == "progress":
            message = data.get("message")
            if isinstance(message, str) and message.strip():
                self.latest_stage = message.strip()
                self.has_progress_stage = True
        elif event == "tool_call":
            self.add_tool(data.get("tool") if isinstance(data.get("tool"), str) else None)
        elif event == "tool_result":
            self.add_tool(data.get("tool") if isinstance(data.get("tool"), str) else None)
            if data.get("success") is True:
                self.success_count += 1
            elif data.get("success") is False:
                self.failure_count += 1

    def elapsed_seconds(self, now: float | None = None) -> int:
        current = monotonic_now() if now is None else now
        return max(0, int(current - self.started_at))

    def summary(self) -> str:
        parts = [self._formatted_stage()]
        if self.tools_seen:
            parts.append(f"tools: {', '.join(self.tools_seen[:4])}")
        if self.success_count > 0:
            parts.append(f"success: {self.success_count}")
        if self.failure_count > 0:
            parts.append(f"failed: {self.failure_count}")
        return " | ".join(parts)

    def build_progress_payload(self, now: float | None = None) -> dict[str, Any]:
        elapsed_seconds = self.elapsed_seconds(now)
        return {
            "event": "ux_progress",
            "data": {
                "elapsed_seconds": elapsed_seconds,
                "stage": self._formatted_stage(),
                "tools_seen": self.tools_seen,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "summary": self.summary(),
            },
        }

    def should_emit_progress(self, *, now: float, gate_seconds: int) -> bool:
        if now - self.started_at < gate_seconds:
            return False
        if self.last_progress_emit_at is None:
            return True
        return now - self.last_progress_emit_at >= gate_seconds

    def mark_progress_emitted(self, *, now: float) -> None:
        self.last_progress_emit_at = now

    def _formatted_stage(self) -> str:
        if not self.has_progress_stage:
            return PROGRESS_STAGE_PLACEHOLDER
        if self.latest_stage == STARTING_STAGE_MESSAGE:
            return PROGRESS_STAGE_PLACEHOLDER
        return self.latest_stage or PROGRESS_STAGE_PLACEHOLDER


async def run_query_stream(
    *,
    query: str,
    clarification: str | None,
    max_steps: int | None,
    detail: EventDetail,
    ux_mode: UxMode = UxMode.RAW,
    progress_gate_seconds: int = DEFAULT_PROGRESS_GATE_SECONDS,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    """Execute the agent stream and emit NDJSON events.

    Returns:
        Process exit code.
    """
    poll_state: _StreamPollState | None = None
    try:
        if progress_gate_seconds < 1 or progress_gate_seconds > 60:
            raise ValueError("progress_gate_seconds must be in range [1, 60]")

        wrapper = StreamingAgentWrapper()
        saw_error = False
        ux_state: _UxState | None = None
        saw_terminal = False
        if ux_mode == UxMode.THREE_MESSAGE:
            # Emit deterministic "started" immediately for command UX.
            emit_event(
                out,
                format_event(
                    "started",
                    {"query": query, "max_steps": max_steps},
                    detail,
                ),
            )
            ux_state = _UxState(started_at=monotonic_now())

        stream_iter = wrapper.stream_query(
            user_query=query,
            clarification=clarification,
            max_steps=max_steps,
            enable_clarification=True,
        ).__aiter__()
        poll_state = _StreamPollState()

        if ux_mode == UxMode.RAW:
            async for event in stream_iter:
                payload = format_event(event.event, event.data, detail)
                emit_event(out, payload)
                if event.event == "error":
                    saw_error = True
        else:
            while True:
                try:
                    event = await poll_stream_event(
                        stream_iter,
                        timeout_seconds=IDLE_POLL_SECONDS,
                        state=poll_state,
                    )
                except StopAsyncIteration:
                    break

                if ux_state is None:
                    ux_state = _UxState(started_at=monotonic_now())

                if event is None:
                    now = monotonic_now()
                    if ux_state.should_emit_progress(now=now, gate_seconds=progress_gate_seconds):
                        emit_event(out, ux_state.build_progress_payload(now))
                        ux_state.mark_progress_emitted(now=now)
                    continue

                # Throttled UX mode
                if event.event == "started":
                    # Ignore wrapper-emitted started; runner already emitted deterministic started.
                    continue

                ux_state.absorb_event(event.event, event.data)
                now = monotonic_now()

                is_terminal = event.event in {"complete", "clarification_needed", "error"}
                if ux_state.should_emit_progress(now=now, gate_seconds=progress_gate_seconds):
                    emit_event(out, ux_state.build_progress_payload(now))
                    ux_state.mark_progress_emitted(now=now)

                if is_terminal:
                    payload = format_event(event.event, event.data, detail)
                    emit_event(out, payload)
                    if event.event == "error":
                        saw_error = True
                    saw_terminal = True
                    break

        if ux_mode == UxMode.THREE_MESSAGE and not saw_terminal:
            emit_event(
                out,
                {
                    "event": "error",
                    "data": {
                        "code": "runner_error",
                        "message": "stream ended without terminal event",
                    },
                },
            )
            return 1
        return 1 if saw_error else 0
    except Exception as exc:
        err.write(f"openclaw_runner failed: {exc}\n")
        err.flush()
        emit_event(
            out,
            {
                "event": "error",
                "data": {
                    "code": "runner_error",
                    "message": str(exc),
                },
            },
        )
        return 1
    finally:
        if poll_state is not None and poll_state.pending_event_task is not None:
            pending_task = poll_state.pending_event_task
            if not pending_task.done():
                pending_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, StopAsyncIteration):
                await pending_task


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    return asyncio.run(
        run_query_stream(
            query=args.query,
            clarification=args.clarification,
            max_steps=args.max_steps,
            detail=EventDetail(args.event_detail),
            ux_mode=UxMode(args.ux_mode),
            progress_gate_seconds=args.progress_gate_seconds,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
