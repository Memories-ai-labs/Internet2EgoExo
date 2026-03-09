"""Request schemas for the API."""

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Request body for streaming query endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language query for video searching",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate that query is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or whitespace only")
        return stripped
    clarification: str | None = Field(
        None,
        max_length=500,
        description="Clarification response if following up on a clarification request",
    )
    max_steps: int | None = Field(
        None,
        ge=1,
        le=20,
        description="Maximum agent steps (overrides default)",
    )
    enable_clarification: bool = Field(
        True,
        description="Whether to enable clarification flow",
    )
