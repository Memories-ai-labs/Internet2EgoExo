"""Health check router."""

from typing import Any

from fastapi import APIRouter

from video_searching_agent.web.dependencies import get_agent

# Import version directly to avoid circular import
__version__ = "0.1.0"

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint with tool status.

    Returns:
        Health status including version and tool availability.
    """
    agent = get_agent()
    tool_health = agent.get_tool_health()

    # Count healthy vs unhealthy tools
    healthy_count = sum(1 for t in tool_health.values() if t.get("healthy", False))
    total_count = len(tool_health)

    return {
        "status": "healthy",
        "version": __version__,
        "tools": {
            "total": total_count,
            "healthy": healthy_count,
            "details": tool_health,
        },
    }
