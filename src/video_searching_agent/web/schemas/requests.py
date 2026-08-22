"""Request schemas for the API."""

from pydantic import BaseModel, Field, field_validator, model_validator

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


# Every clip in a collection request costs money to index, so a single request
# cannot queue an unbounded number of them.
MAX_URLS_PER_REQUEST = 25

# Curation gets its own, much higher ceiling. It is a different operation with a
# different cost: collecting a URL means a download, an upload and an index —
# minutes each — while curating an already-indexed video means reading its
# captions, measured at about 0.6s a clip. Sharing the collect cap here is what
# made "Grade the set" reject a run of 35 clips outright, and verdicts stream as
# they complete, so a set large enough to run long still delivers what it graded.
MAX_VIDEOS_PER_CURATION = 200


class CollectRequest(BaseModel):
    """Request body for the collection stream.

    The candidates a search found, handed to the pipeline: download, index,
    clean, annotate.
    """

    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_URLS_PER_REQUEST,
        description="Candidate page URLs to collect (YouTube, TikTok, Instagram, X)",
    )
    require_hands: bool = Field(
        True,
        description="Reject footage with no hands in frame — the manipulation-data gate",
    )
    viewpoint: Viewpoint | None = Field(
        None, description="Require a camera viewpoint; omit for any"
    )
    min_duration_seconds: int | None = Field(
        None, ge=0, le=86_400, description="Skip candidates shorter than this"
    )
    annotate: bool = Field(
        True,
        description="Run the annotation agent on what survives cleaning. "
        "False is a cleaning-only pass, which is much cheaper.",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        """Keep http(s) URLs only, de-duplicated, order preserved.

        The count is also checked against `MAX_COLLECT_URLS`, which is how a
        public deployment running on its owner's key bounds what one caller can
        spend: indexing is billed per video-minute.
        """
        cleaned: list[str] = []
        for raw in v:
            candidate = raw.strip()
            if not candidate:
                continue
            if not candidate.startswith(("http://", "https://")):
                raise ValueError(f"'{raw}' is not an http(s) URL")
            if candidate not in cleaned:
                cleaned.append(candidate)
        if not cleaned:
            raise ValueError("At least one URL is required")

        from video_searching_agent.config.settings import get_settings

        allowed = get_settings().max_collect_urls
        if len(cleaned) > allowed:
            raise ValueError(
                f"This deployment accepts {allowed} URL"
                f"{'' if allowed == 1 else 's'} per request. "
                "Send fewer, or bring your own key with the X-Memories-Key header."
            )
        return cleaned


class CurateRequest(BaseModel):
    """Request body for the curation stream.

    Either a list of indexed video ids, or a tag to pull the worklist from.
    """

    video_ids: list[str] | None = Field(
        None,
        max_length=MAX_VIDEOS_PER_CURATION,
        description="Indexed videos to curate",
    )
    tag: str | None = Field(
        None,
        max_length=100,
        description="Pull the worklist from this tag instead (e.g. 'clean_pass')",
    )
    query: str | None = Field(
        None, max_length=2000, description="What the collection was looking for"
    )
    require_hands: bool = Field(True, description="Reject footage with no hands")
    viewpoint: Viewpoint | None = Field(None, description="Require a camera viewpoint")
    annotate: bool = Field(True, description="Annotate what survives cleaning")

    @model_validator(mode="after")
    def require_a_worklist(self) -> "CurateRequest":
        """One of `video_ids` or `tag` has to say what to curate."""
        if not self.video_ids and not self.tag:
            raise ValueError("Provide either video_ids or tag")
        return self
