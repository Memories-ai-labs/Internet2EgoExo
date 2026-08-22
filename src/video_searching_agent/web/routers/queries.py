"""Query streaming router."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from video_searching_agent.config.settings import get_settings
from video_searching_agent.web import demo
from video_searching_agent.web.credentials import RequestCredentials
from video_searching_agent.web.dependencies import get_agent
from video_searching_agent.web.schemas.events import ErrorEvent
from video_searching_agent.web.schemas.requests import QueryRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["queries"])


def _agent_for(credentials: RequestCredentials) -> Any:
    """The shared agent, or a private one when the caller brought a key.

    Built per request in that case: putting a caller's key into the shared
    agent would serve it to everyone else too.
    """
    client = credentials.llm_client()
    if client is None:
        return get_agent()

    from video_searching_agent.web.streaming.agent_stream import StreamingAgentWrapper

    return StreamingAgentWrapper(llm_client=client)


async def generate_events(
    request: Request,
    query_request: QueryRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Generate SSE events for a query.

    Args:
        request: FastAPI request (for disconnect detection).
        query_request: The query request body.

    Yields:
        Dictionaries with 'event' and 'data' keys for sse-starlette.
    """
    if get_settings().demo_mode:
        # Canned payloads: the deployed link works with no keys and no budget.
        async for frame in demo.frames(demo.query_events(query_request)):
            yield frame
        return

    credentials = RequestCredentials.from_headers(request.headers)
    agent = _agent_for(credentials)
    if credentials.supplied:
        logger.info("serving with caller-supplied credentials: %s", credentials.describe())

    try:
        # Create generator for streaming events
        event_gen = agent.stream_query(
            user_query=query_request.query,
            clarification=query_request.clarification,
            max_steps=query_request.max_steps,
            enable_clarification=query_request.enable_clarification,
            sources=query_request.sources,
            viewpoint=query_request.viewpoint,
            min_duration_seconds=query_request.min_duration_seconds,
            license_filter=query_request.license_filter,
            target_hours=query_request.target_hours,
        )

        async for event in event_gen:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("Client disconnected, stopping stream")
                break

            yield {"event": event.event, "data": json.dumps(event.data)}

    except asyncio.CancelledError:
        logger.info("Stream cancelled")
        raise
    except Exception as e:
        logger.exception(f"Error generating events: {e}")
        error_event = ErrorEvent.create(
            code="internal_error",
            message=str(e),
        )
        yield {"event": error_event.event, "data": json.dumps(error_event.data)}


@router.post("/queries/stream")
async def stream_query(
    request: Request,
    query_request: QueryRequest,
) -> EventSourceResponse:
    """Stream query execution via Server-Sent Events.

    This endpoint streams real-time progress as the agent executes:
    - `started`: Query processing begins
    - `progress`: Step updates during execution
    - `tool_call`: When a tool is being called
    - `tool_result`: When a tool returns results
    - `clarification_needed`: When user clarification is required
    - `complete`: Final response with all data
    - `error`: If an error occurs

    Args:
        request: FastAPI request object.
        query_request: Query request body.

    Returns:
        EventSourceResponse streaming SSE events.
    """
    settings = get_settings()

    return EventSourceResponse(
        generate_events(request, query_request),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )
