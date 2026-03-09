"""Middleware for the API."""

from video_searching_agent.web.middleware.auth import APIKeyAuthMiddleware
from video_searching_agent.web.middleware.rate_limit import RateLimitMiddleware

__all__ = ["APIKeyAuthMiddleware", "RateLimitMiddleware"]
