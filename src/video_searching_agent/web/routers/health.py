"""Health check router."""

from typing import Any

from fastapi import APIRouter

from video_searching_agent.api.llm import llm_label
from video_searching_agent.config.settings import get_settings
from video_searching_agent.web.dependencies import get_agent

# Import version directly to avoid circular import
__version__ = "0.1.0"

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint with tool status.

    Returns:
        Health status including version, whether this deployment is serving
        demo payloads, which model drives it, and tool availability.
    """
    settings = get_settings()

    # Whether callers need a key of this server's own. The UI asks so it can
    # hide the field when nobody needs it — an unused key box in an app whose
    # sources include X reads as "the X API key", which it is not.
    auth_required = bool(settings.api_keys.strip())

    if settings.demo_mode:
        # Nothing is configured in demo mode, so there is nothing to probe.
        return {
            "status": "healthy",
            "version": __version__,
            "demo_mode": True,
            "auth_required": auth_required,
            "model": "none — demo payloads",
            "tools": {"total": 0, "healthy": 0, "details": {}},
        }

    agent = get_agent()
    tool_health = agent.get_tool_health()

    # Count healthy vs unhealthy tools
    healthy_count = sum(1 for t in tool_health.values() if t.get("healthy", False))
    total_count = len(tool_health)

    return {
        "status": "healthy",
        "version": __version__,
        "demo_mode": False,
        "auth_required": auth_required,
        "model": llm_label(),
        "tools": {
            "total": total_count,
            "healthy": healthy_count,
            "details": tool_health,
        },
    }
