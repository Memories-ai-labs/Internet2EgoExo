"""API routers."""

from video_searching_agent.web.routers.health import router as health_router
from video_searching_agent.web.routers.pipeline import router as pipeline_router
from video_searching_agent.web.routers.queries import router as queries_router

__all__ = ["health_router", "pipeline_router", "queries_router"]
