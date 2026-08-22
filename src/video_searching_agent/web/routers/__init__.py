"""API routers."""

from video_searching_agent.web.routers.clips import router as clips_router
from video_searching_agent.web.routers.health import router as health_router
from video_searching_agent.web.routers.pipeline import router as pipeline_router
from video_searching_agent.web.routers.queries import router as queries_router

__all__ = ["clips_router", "health_router", "pipeline_router", "queries_router"]
