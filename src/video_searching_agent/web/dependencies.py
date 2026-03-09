"""Dependency injection for the API."""

from functools import lru_cache

from video_searching_agent.web.streaming.agent_stream import StreamingAgentWrapper


@lru_cache
def get_agent() -> StreamingAgentWrapper:
    """Get the shared streaming agent instance.

    Uses lru_cache to ensure a single agent instance is created
    and reused across all requests.

    Returns:
        StreamingAgentWrapper instance.
    """
    return StreamingAgentWrapper()
