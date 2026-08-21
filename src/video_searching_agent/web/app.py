"""FastAPI application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from video_searching_agent.config.settings import get_settings
from video_searching_agent.web.middleware.auth import APIKeyAuthMiddleware
from video_searching_agent.web.middleware.rate_limit import RateLimitMiddleware
from video_searching_agent.web.routers import health_router, queries_router

# Import version directly to avoid circular import
__version__ = "0.1.0"

logger = logging.getLogger(__name__)

# Static single-page UI shipped with the package.
STATIC_DIR = Path(__file__).parent / "static"
UI_PATH = "/ui"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown events."""
    settings = get_settings()
    logger.info(f"Video Searching Agent API v{__version__} starting up")
    logger.info(f"Debug mode: {settings.api_debug}")
    if not settings.api_keys:
        logger.warning("No API keys configured - running without authentication")
    yield
    # Shutdown logic would go here if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    settings = get_settings()

    app = FastAPI(
        title="Video Searching Agent API",
        description="AI-powered video searching and analysis API",
        version=__version__,
        docs_url="/docs" if settings.api_debug else None,
        redoc_url="/redoc" if settings.api_debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware (order matters: auth first, then rate limit)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIKeyAuthMiddleware)

    # Include routers
    app.include_router(health_router)
    app.include_router(queries_router)

    # Serve the bundled web UI (no build step) and send "/" to it.
    if STATIC_DIR.is_dir():
        app.mount(UI_PATH, StaticFiles(directory=STATIC_DIR, html=True), name="ui")

        @app.get("/", include_in_schema=False)
        async def ui_root() -> RedirectResponse:
            return RedirectResponse(url=f"{UI_PATH}/")
    else:  # pragma: no cover - only when static assets are stripped from a build
        logger.warning("Static UI directory not found at %s - UI disabled", STATIC_DIR)

    return app
