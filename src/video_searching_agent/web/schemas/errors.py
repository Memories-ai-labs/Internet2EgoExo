"""Error schemas for the API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """API error codes."""

    INVALID_REQUEST = "invalid_request"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMITED = "rate_limited"
    TOOL_ERROR = "tool_error"
    AGENT_ERROR = "agent_error"
    TIMEOUT = "timeout"
    INTERNAL_ERROR = "internal_error"


class APIError(BaseModel):
    """API error response."""

    code: ErrorCode
    message: str
    details: dict[str, Any] | None = Field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result: dict[str, Any] = {"code": self.code.value, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result
