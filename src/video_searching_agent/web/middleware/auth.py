"""API key authentication middleware."""

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from video_searching_agent.config.settings import get_settings
from video_searching_agent.web.schemas.errors import APIError, ErrorCode

logger = logging.getLogger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {"/api/v1/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Check API key for protected endpoints."""
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        settings = get_settings()
        api_keys_str = settings.api_keys.strip()

        # If no API keys configured, skip authentication (dev mode)
        if not api_keys_str:
            logger.warning("No API keys configured - running without authentication")
            return await call_next(request)

        # Parse valid API keys
        valid_keys = {k.strip() for k in api_keys_str.split(",") if k.strip()}

        # Get API key from header
        api_key = request.headers.get(settings.api_key_header)

        if not api_key:
            error = APIError(
                code=ErrorCode.AUTHENTICATION_FAILED,
                message=f"Missing {settings.api_key_header} header",
            )
            return JSONResponse(status_code=401, content=error.to_dict())

        if api_key not in valid_keys:
            error = APIError(
                code=ErrorCode.AUTHENTICATION_FAILED,
                message="Invalid API key",
            )
            return JSONResponse(status_code=401, content=error.to_dict())

        # Store API key in request state for rate limiting
        request.state.api_key = api_key
        return await call_next(request)
