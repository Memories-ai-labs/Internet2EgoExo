"""Pricing configuration for API and tool costs.

This module defines the cost rates for:
- Gemini API token pricing
- External tool/API costs (Apify, Exa, YouTube quota)
"""

from pydantic import BaseModel, Field


class GeminiPricing(BaseModel):
    """Pricing for Gemini API per 1M tokens."""

    # Gemini 3 Flash Preview pricing (as of Jan 2026)
    # Source: https://ai.google.dev/gemini-api/docs/pricing
    input_per_million: float = Field(0.50, description="USD per 1M input tokens")
    output_per_million: float = Field(3.00, description="USD per 1M output tokens")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> tuple[float, float, float]:
        """Calculate costs for given token counts.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Tuple of (input_cost, output_cost, total_cost) in USD.
        """
        input_cost = (input_tokens / 1_000_000) * self.input_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_per_million
        return input_cost, output_cost, input_cost + output_cost


class ToolPricing(BaseModel):
    """Estimated pricing for external tool APIs."""

    # Apify actors - pay-per-event model, estimated per run
    # TikTok: $0.03 start + ~$0.004/item, estimated 10-20 items per search
    apify_tiktok_search: float = Field(0.08, description="TikTok search per run")
    apify_tiktok_creator: float = Field(0.05, description="TikTok creator lookup per run")
    # Instagram: ~$0.50 per 1K posts, typical search returns 10-50 posts
    apify_instagram_search: float = Field(0.05, description="Instagram search per run")
    apify_instagram_creator: float = Field(0.03, description="Instagram creator lookup per run")
    # Twitter: Similar PPE model
    apify_twitter_search: float = Field(0.05, description="Twitter search per run")
    apify_twitter_profile: float = Field(0.03, description="Twitter profile lookup per run")

    # Exa.ai - $5 per 1,000 requests for standard search
    # Source: https://exa.ai/pricing
    exa_search: float = Field(0.005, description="Exa search per request")
    exa_similar: float = Field(0.005, description="Exa similar search per request")
    exa_content: float = Field(0.005, description="Exa content fetch per request")
    exa_research: float = Field(0.005, description="Exa research per request")

    # YouTube Data API (quota-based, no direct cost but tracked)
    youtube_search_quota: int = Field(100, description="Quota units per search")
    youtube_video_quota: int = Field(1, description="Quota units per video detail")
    youtube_channel_quota: int = Field(1, description="Quota units per channel detail")

    # Memories.ai v2 API - pricing varies by channel
    # memories.ai channel: $0.01/video, rapid channel: $0.02/video
    memories_youtube_metadata: float = Field(
        0.01,
        description="YouTube metadata per request (memories.ai)",
    )
    memories_youtube_metadata_rapid: float = Field(
        0.02,
        description="YouTube metadata per request (rapid)",
    )
    memories_youtube_transcript: float = Field(
        0.01,
        description="YouTube transcript per request (memories.ai)",
    )
    memories_youtube_transcript_rapid: float = Field(
        0.02,
        description="YouTube transcript per request (rapid)",
    )
    memories_tiktok_metadata: float = Field(0.01, description="TikTok metadata per request")
    memories_tiktok_transcript: float = Field(0.01, description="TikTok transcript per request")
    memories_instagram_metadata: float = Field(0.01, description="Instagram metadata per request")
    memories_instagram_transcript: float = Field(
        0.01,
        description="Instagram transcript per request",
    )
    memories_twitter_metadata: float = Field(0.01, description="Twitter metadata per request")
    memories_twitter_transcript: float = Field(0.01, description="Twitter transcript per request")
    memories_vlm_input_per_million: float = Field(0.45, description="VLM input per 1M tokens")
    memories_vlm_output_per_million: float = Field(3.75, description="VLM output per 1M tokens")
    memories_transcription: float = Field(0.001, description="Asset transcription per second")
    # MAI transcript - AI-powered dual transcription (token-based + per-second)
    memories_mai_transcript_base: float = Field(0.05, description="MAI transcript base cost")
    memories_mai_transcript_per_second: float = Field(0.0001, description="MAI per second")

    # Video search tool (combines Exa + Apify)
    video_search: float = Field(0.005, description="Unified video search per request")

    def get_tool_cost(self, tool_name: str) -> float:
        """Get estimated cost for a tool by name.

        Args:
            tool_name: Name of the tool (e.g., 'tiktok_search', 'exa_search').

        Returns:
            Estimated cost in USD per invocation.
        """
        # Map tool names to pricing fields
        # NOTE: Keys must match the actual tool name returned by each tool's `name` property
        tool_map = {
            # TikTok (Apify-based tools)
            "tiktok_search": self.apify_tiktok_search,
            "tiktok_creator_info": self.apify_tiktok_creator,
            # Instagram (Apify-based tools)
            "instagram_search": self.apify_instagram_search,
            "instagram_creator_info": self.apify_instagram_creator,
            # Twitter (Apify-based tools)
            "twitter_search": self.apify_twitter_search,
            "twitter_profile_info": self.apify_twitter_profile,
            # Exa
            "exa_search": self.exa_search,
            "exa_similar": self.exa_similar,
            "exa_find_similar": self.exa_similar,  # Alternative name
            "exa_content": self.exa_content,
            "exa_get_content": self.exa_content,  # Alternative name
            "exa_research": self.exa_research,
            # YouTube
            "youtube_search": 0.0,  # Quota-based, no direct cost
            "youtube_channel": 0.0,
            "youtube_channel_info": 0.0,
            # Memories.ai v2
            "social_media_metadata": self.memories_youtube_metadata,  # $0.01 per request
            "social_media_transcript": self.memories_youtube_transcript,  # $0.01 per request
            "social_media_mai_transcript": self.memories_mai_transcript_base,  # $0.05 base
            "vlm_video_analysis": 0.05,  # Flat rate fallback when no token usage available
            # Unified
            "video_search": self.video_search,
        }
        return tool_map.get(tool_name, 0.0)

    def get_youtube_quota(self, tool_name: str) -> int:
        """Get YouTube API quota for a tool.

        Args:
            tool_name: Name of the YouTube tool.

        Returns:
            Quota units used per invocation.
        """
        quota_map = {
            "youtube_search": self.youtube_search_quota,
            "youtube_channel": self.youtube_channel_quota,
            "youtube_channel_info": self.youtube_channel_quota,
        }
        return quota_map.get(tool_name, 0)

    def calculate_vlm_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate VLM cost based on actual token usage.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Total VLM cost in USD.
        """
        input_cost = (input_tokens / 1_000_000) * self.memories_vlm_input_per_million
        output_cost = (output_tokens / 1_000_000) * self.memories_vlm_output_per_million
        return input_cost + output_cost


class PricingConfig(BaseModel):
    """Complete pricing configuration."""

    gemini: GeminiPricing = Field(default_factory=lambda: GeminiPricing())
    tools: ToolPricing = Field(default_factory=lambda: ToolPricing())


# Global default pricing config
DEFAULT_PRICING = PricingConfig()


def get_pricing() -> PricingConfig:
    """Get the default pricing configuration.

    Returns:
        PricingConfig with current pricing rates.
    """
    return DEFAULT_PRICING
