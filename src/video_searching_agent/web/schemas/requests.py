"""Request schemas for the API."""

from pydantic import BaseModel, Field, field_validator

from video_searching_agent.curation.viewpoint import Viewpoint

# Canonical sources the agent can be pinned to. An empty selection means
# "auto": the agent picks sources from the query itself.
SUPPORTED_SOURCES = ("youtube", "tiktok", "instagram", "twitter", "web")

# Accepted spellings for each canonical source.
SOURCE_ALIASES = {
    "youtube": "youtube",
    "yt": "youtube",
    "tiktok": "tiktok",
    "tik tok": "tiktok",
    "instagram": "instagram",
    "ig": "instagram",
    "reels": "instagram",
    "twitter": "twitter",
    "x": "twitter",
    "x.com": "twitter",
    "web": "web",
    "exa": "web",
}


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
    sources: list[str] | None = Field(
        None,
        description=(
            "Sources to pin the search to "
            f"({', '.join(SUPPORTED_SOURCES)}). Omit or leave empty for auto-select."
        ),
    )

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[str] | None) -> list[str] | None:
        """Normalize sources to canonical names, dropping duplicates.

        `None`, an empty list, and `["auto"]` all mean auto-select.
        """
        if not v:
            return None

        normalized: list[str] = []
        for raw in v:
            candidate = raw.strip().lower()
            if not candidate or candidate == "auto":
                continue
            canonical = SOURCE_ALIASES.get(candidate)
            if canonical is None:
                supported = ", ".join(SUPPORTED_SOURCES)
                raise ValueError(f"Unsupported source '{raw}'. Supported sources: {supported}")
            if canonical not in normalized:
                normalized.append(canonical)

        return normalized or None
    viewpoint: Viewpoint | None = Field(
        None,
        description=(
            "Require a camera viewpoint: egocentric (first-person, head/body "
            "mounted) or exocentric (third-person, fixed camera). Omit for any."
        ),
    )
    min_duration_seconds: int | None = Field(
        None,
        ge=0,
        le=86_400,
        description="Drop candidate clips shorter than this",
    )
    license_filter: str | None = Field(
        None,
        description="'reusable' to keep only licence-clear footage; omit or 'any' for no filter",
    )
    target_hours: float | None = Field(
        None,
        gt=0,
        le=1000,
        description="How many hours of footage this run should try to collect",
    )

    @field_validator("license_filter")
    @classmethod
    def validate_license_filter(cls, v: str | None) -> str | None:
        """Only the two documented values are accepted."""
        if v is None:
            return None
        candidate = v.strip().lower()
        if candidate in ("", "any"):
            return None
        if candidate != "reusable":
            raise ValueError("license_filter must be 'any' or 'reusable'")
        return candidate

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
