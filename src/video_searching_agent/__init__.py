"""Video Searching Agent - AI-powered video search and analysis across multiple platforms."""

from typing import Any

from video_searching_agent.agent.core import VideoSearchingAgent
from video_searching_agent.models.result import AgentResponse, VideoReference
from video_searching_agent.models.video import Platform, Video, VideoMetrics

__version__ = "0.1.0"
__all__ = [
    "VideoSearchingAgent",
    "Video",
    "VideoMetrics",
    "Platform",
    "AgentResponse",
    "VideoReference",
]


def create_app() -> Any:
    """Lazy import to avoid circular imports."""
    from video_searching_agent.web.app import create_app as _create_app

    return _create_app()
