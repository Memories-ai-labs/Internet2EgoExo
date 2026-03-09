"""Cost and usage tracking models."""

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage for a Gemini API call or aggregated session."""

    input_tokens: int = Field(0, description="Number of input/prompt tokens")
    output_tokens: int = Field(0, description="Number of output/completion tokens")
    total_tokens: int = Field(0, description="Total tokens (input + output)")

    def add(self, other: "TokenUsage") -> "TokenUsage":
        """Add another TokenUsage to this one."""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class GeminiCost(BaseModel):
    """Cost breakdown for Gemini API usage."""

    token_usage: TokenUsage = Field(default_factory=lambda: TokenUsage())
    input_cost_usd: float = Field(0.0, description="Cost for input tokens in USD")
    output_cost_usd: float = Field(0.0, description="Cost for output tokens in USD")
    total_cost_usd: float = Field(0.0, description="Total Gemini cost in USD")


class ToolUsageCost(BaseModel):
    """Cost breakdown for a single tool's usage."""

    tool_name: str = Field(..., description="Name of the tool")
    invocation_count: int = Field(1, description="Number of times the tool was invoked")
    estimated_cost_usd: float = Field(0.0, description="Estimated cost in USD")
    quota_used: int | None = Field(None, description="Quota units used (e.g., YouTube API)")
    token_usage: "TokenUsage | None" = Field(None, description="Token usage for token-based tools")
    details: str | None = Field(None, description="Additional cost details")


class UsageMetrics(BaseModel):
    """Comprehensive usage metrics for an agent session."""

    gemini: GeminiCost = Field(default_factory=lambda: GeminiCost())
    tool_costs: list[ToolUsageCost] = Field(default_factory=list)
    total_cost_usd: float = Field(0.0, description="Total cost across Gemini and all tools")
    gemini_calls: int = Field(0, description="Number of Gemini API calls made")
    tool_calls: int = Field(0, description="Total number of tool invocations")

    def calculate_total(self) -> float:
        """Calculate and update total cost."""
        tool_total = sum(t.estimated_cost_usd for t in self.tool_costs)
        self.total_cost_usd = self.gemini.total_cost_usd + tool_total
        return self.total_cost_usd

    def get_tool_cost(self, tool_name: str) -> ToolUsageCost | None:
        """Get cost breakdown for a specific tool."""
        for cost in self.tool_costs:
            if cost.tool_name == tool_name:
                return cost
        return None

    def get_youtube_quota_used(self) -> int:
        """Get total YouTube API quota used."""
        total = 0
        for cost in self.tool_costs:
            if "youtube" in cost.tool_name.lower() and cost.quota_used:
                total += cost.quota_used
        return total
