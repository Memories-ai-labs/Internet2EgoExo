"""Rate limiting middleware using token bucket algorithm."""

import logging
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from video_searching_agent.config.settings import get_settings
from video_searching_agent.web.credentials import RequestCredentials
from video_searching_agent.web.schemas.errors import APIError, ErrorCode

logger = logging.getLogger(__name__)


def _client_address(request: Request) -> str:
    """The caller's address, honouring the proxy header a platform sets."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: float
    tokens: float = field(init=False)
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.tokens = self.capacity

    def consume(self, tokens: float = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_until_available(self, tokens: float = 1) -> float:
        """Calculate seconds until tokens will be available."""
        if self.tokens >= tokens:
            return 0
        needed = tokens - self.tokens
        return needed / self.refill_rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiting middleware."""

    # Paths that don't have rate limiting
    EXEMPT_PATHS = {"/", "/api/v1/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    # Prefixes that don't have rate limiting (static UI assets)
    EXEMPT_PREFIXES = ("/ui/",)

    def __init__(self, app: Any, rpm: int | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self.rpm = rpm or settings.rate_limit_rpm
        self.enabled = settings.rate_limit_enabled
        # bucket per API key
        self._buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=float(self.rpm),
                refill_rate=self.rpm / 60.0,  # refill over a minute
            )
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Apply rate limiting."""
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for exempt paths
        path = request.url.path
        if path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES):
            return await call_next(request)

        # A caller who brought their own keys is spending their own money, so
        # the shared quota does not apply to them. That is the whole point of
        # the bring-your-own-key path.
        if RequestCredentials.from_headers(request.headers).supplied:
            return await call_next(request)

        # One bucket per API key, or per client address when there is none —
        # otherwise a single anonymous caller starves every other visitor.
        api_key = getattr(request.state, "api_key", None)
        bucket = self._buckets[api_key or f"ip:{_client_address(request)}"]

        if not bucket.consume(1):
            retry_after = bucket.time_until_available(1)
            error = APIError(
                code=ErrorCode.RATE_LIMITED,
                message=f"Rate limit exceeded. Try again in {retry_after:.1f}s",
                details={"retry_after_seconds": round(retry_after, 1)},
            )
            response = JSONResponse(status_code=429, content=error.to_dict())
            response.headers["Retry-After"] = str(int(retry_after) + 1)
            return response

        return await call_next(request)
