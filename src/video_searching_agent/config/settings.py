"""Application settings and configuration."""

from functools import lru_cache

from pydantic import Field, model_validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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

    # YouTube API
    youtube_api_key: str = Field(
        ...,
        description="YouTube Data API key",
        validation_alias="YOUTUBE_API_KEY",
    )

    # Memories.ai v2 API (canonical names)
    memories_api_key: str = Field(
        default="",
        description="Memories.ai v2 API key",
        validation_alias="MEMORIES_API_KEY",
    )
    memories_base_url: str = Field(
        default="https://mavi-backend.memories.ai/serve/api/v2",
        description="Memories.ai v2 API base URL",
        validation_alias="MEMORIES_BASE_URL",
    )
    memories_default_channel: str = Field(
        default="memories.ai",
        description="Default scraping channel (memories.ai, apify, rapid)",
        validation_alias="MEMORIES_DEFAULT_CHANNEL",
    )
    memories_vlm_model: str = Field(
        default="gemini:gemini-3-flash-preview",
        description="Default VLM model for video analysis",
        validation_alias="MEMORIES_VLM_MODEL",
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

    @model_validator(mode="after")
    def normalize_memories_settings(self) -> "Settings":
        """Normalize user-provided Memories settings values."""
        self.memories_api_key = self.memories_api_key.strip()

        # Preserve sane defaults when users provide empty/whitespace env values.
        base_url = self.memories_base_url.strip()
        channel = self.memories_default_channel.strip()
        vlm_model = self.memories_vlm_model.strip()

        self.memories_base_url = base_url or "https://mavi-backend.memories.ai/serve/api/v2"
        self.memories_default_channel = channel or "memories.ai"
        self.memories_vlm_model = vlm_model or "gemini:gemini-3-flash-preview"
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
