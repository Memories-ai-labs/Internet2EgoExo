"""Application settings and configuration."""

from functools import lru_cache
from typing import Any

from pydantic import Field, model_validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Demo mode: serve canned payloads instead of calling anything.
    demo_mode: bool = Field(
        default=False,
        description=(
            "Serve canned payloads from the streaming endpoints instead of "
            "calling Gemini, the platforms or the Datalake. Nothing is "
            "downloaded, indexed or spent. Credentials become optional."
        ),
        validation_alias="DEMO_MODE",
    )

    # Google Gemini API
    google_api_key: str = Field(
        ...,
        description="Google API key for Gemini",
        validation_alias="GOOGLE_API_KEY",
    )
    gemini_model: str = Field(
        default="gemini-3.1-pro-preview",
        description="Gemini model to use",
        validation_alias="GEMINI_MODEL",
    )

    # OpenRouter (an alternative to Gemini: one key, hundreds of models)
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter key (sk-or-...). When set, it drives the agents "
        "instead of Gemini unless LLM_PROVIDER says otherwise.",
        validation_alias="OPENROUTER_API_KEY",
    )
    openrouter_model: str = Field(
        default="google/gemini-3.7-flash",
        description="OpenRouter model slug; multimodal by default so the same "
        "key can read frames, not only caption text",
        validation_alias="OPENROUTER_MODEL",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API root",
        validation_alias="OPENROUTER_BASE_URL",
    )
    llm_provider: str = Field(
        default="auto",
        description="'auto' (OpenRouter when its key is set, else Gemini), "
        "'openrouter', or 'gemini'",
        validation_alias="LLM_PROVIDER",
    )

    # YouTube API
    youtube_api_key: str = Field(
        ...,
        description="YouTube Data API key",
        validation_alias="YOUTUBE_API_KEY",
    )

    # Memories.ai Video Datalake API
    memories_api_key: str = Field(
        default="",
        description="Memories.ai Video Datalake API key (sk-mai-...)",
        validation_alias="MEMORIES_API_KEY",
    )
    memories_base_url: str = Field(
        default="https://api.memories.ai/serve/datalake/v1",
        description="Video Datalake API base URL",
        validation_alias="MEMORIES_BASE_URL",
    )
    memories_collection_id: str = Field(
        default="",
        description="Existing Datalake collection to index into (optional)",
        validation_alias="MEMORIES_COLLECTION_ID",
    )
    memories_collection_name: str = Field(
        default="video-searching-agent",
        description="Collection created/reused when no collection id is configured",
        validation_alias="MEMORIES_COLLECTION_NAME",
    )
    memories_index_fps: float = Field(
        default=1.0,
        gt=0,
        le=30,
        description="Frames per second to index at (cost scales with fps)",
        validation_alias="MEMORIES_INDEX_FPS",
    )
    memories_index_wait_seconds: int = Field(
        default=120,
        ge=0,
        le=900,
        description="How long a single tool call waits for indexing to finish",
        validation_alias="MEMORIES_INDEX_WAIT_SECONDS",
    )
    memories_index_poll_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Delay between ingest-operation polls",
        validation_alias="MEMORIES_INDEX_POLL_SECONDS",
    )

    # Exa.ai API (for web search)
    exa_api_key: str | None = Field(
        default=None,
        description="Exa.ai API key for neural web search",
        validation_alias="EXA_API_KEY",
    )
    exa_timeout_seconds: int = Field(
        default=30,
        description="Timeout for Exa API requests",
        validation_alias="EXA_TIMEOUT_SECONDS",
    )

    # Apify API (for social media scraping)
    apify_api_token: str | None = Field(
        default=None,
        description="Apify API token for social media scraping actors",
        validation_alias="APIFY_API_TOKEN",
    )

    # Downloading
    download_user_agent: str = Field(
        default="",
        description="User-Agent for yt-dlp. Empty uses the project default; "
        "some hosts refuse requests that do not identify themselves.",
        validation_alias="DOWNLOAD_USER_AGENT",
    )

    # Agent configuration
    max_agent_steps: int = Field(
        default=10,
        description="Maximum steps the agent can take per query",
        validation_alias="MAX_AGENT_STEPS",
    )
    max_videos_per_search: int = Field(
        default=20,
        description="Maximum videos to return per search",
        validation_alias="MAX_VIDEOS_PER_SEARCH",
    )
    tool_execution_concurrency: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Maximum concurrent tool calls within one agent step",
        validation_alias="TOOL_EXECUTION_CONCURRENCY",
    )

    # Timeouts
    api_timeout_seconds: int = Field(
        default=30,
        description="API request timeout",
        validation_alias="API_TIMEOUT_SECONDS",
    )

    # API Server
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host",
        validation_alias="API_HOST",
    )
    api_port: int = Field(
        default=8000,
        description="API server port",
        validation_alias="API_PORT",
    )
    api_debug: bool = Field(
        default=False,
        description="Enable debug mode",
        validation_alias="API_DEBUG",
    )

    # Authentication
    api_key_header: str = Field(
        default="X-API-Key",
        description="Header for API key",
        validation_alias="API_KEY_HEADER",
    )
    api_keys: str = Field(
        default="",
        description="Comma-separated valid API keys",
        validation_alias="API_KEYS",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
        validation_alias="RATE_LIMIT_ENABLED",
    )
    rate_limit_rpm: int = Field(
        default=60,
        description="Requests per minute per API key",
        validation_alias="RATE_LIMIT_RPM",
    )

    # CORS
    cors_origins: str = Field(
        default="*",
        description="Comma-separated allowed CORS origins (* for all)",
        validation_alias="CORS_ORIGINS",
    )

    # SSE Streaming
    sse_ping_interval: int = Field(
        default=15,
        description="Keep-alive ping interval in seconds",
        validation_alias="SSE_PING_INTERVAL",
    )

    # OpenClaw UX tuning
    openclaw_progress_gate_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Seconds before first throttled OpenClaw progress update",
        validation_alias="OPENCLAW_PROGRESS_GATE_SECONDS",
    )

    @model_validator(mode="before")
    @classmethod
    def allow_missing_keys_in_demo_mode(cls, values: Any) -> Any:
        """Make Google credentials optional when they are not what drives the run.

        Keys stay *required* in every other mode on purpose: a deployment with
        a missing key should fail at startup with a clear message, not halfway
        through someone's first query.
        """
        if not isinstance(values, dict):
            return values

        demo = str(values.get("DEMO_MODE") or values.get("demo_mode") or "").strip().lower()
        openrouter = str(
            values.get("OPENROUTER_API_KEY") or values.get("openrouter_api_key") or ""
        ).strip()

        if demo not in ("1", "true", "yes", "on") and not openrouter:
            return values

        # Either the app is serving canned data, or OpenRouter is driving the
        # models — in both cases a Google project is not required to boot.
        #
        # The filler is an *empty string*, not a sentinel: a tool that checks
        # whether its key is configured would report itself healthy on a
        # sentinel and then fail at call time, which is worse than saying up
        # front that it has no key.
        for alias in ("GOOGLE_API_KEY", "YOUTUBE_API_KEY"):
            if not values.get(alias):
                values[alias] = ""
        return values

    @model_validator(mode="after")
    def normalize_memories_settings(self) -> "Settings":
        """Normalize user-provided Datalake settings values."""
        self.memories_api_key = self.memories_api_key.strip()
        self.memories_collection_id = self.memories_collection_id.strip()

        # Preserve sane defaults when users provide empty/whitespace env values.
        base_url = self.memories_base_url.strip()
        collection_name = self.memories_collection_name.strip()

        self.memories_base_url = base_url or "https://api.memories.ai/serve/datalake/v1"
        self.memories_collection_name = collection_name or "video-searching-agent"
        return self

    @property
    def resolved_llm_provider(self) -> str:
        """Which provider actually drives the models: 'openrouter' or 'gemini'."""
        choice = (self.llm_provider or "auto").strip().lower()
        if choice in ("openrouter", "gemini"):
            return choice
        return "openrouter" if self.openrouter_api_key.strip() else "gemini"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
