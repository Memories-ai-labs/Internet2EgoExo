"""Result and response data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from video_searching_agent.models.cost import UsageMetrics


class VideoReference(BaseModel):
    """A video reference to include in the response."""

    video_id: str
    url: str
    title: str | None = None
    platform: str
    creator: str | None = None
    creator_url: str | None = None
    thumbnail_url: str | None = None
    relevance_note: str | None = Field(
        None,
        description="Why this video is relevant to the query",
    )

    # Key metrics for display
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    engagement_rate: float | None = None
    duration: str | None = None
    published_at: str | None = None


class ComparisonResult(BaseModel):
    """Result of comparing multiple entities."""

    entities: list[str]
    comparison_type: str = Field(
        default="general",
        description="Type of comparison: brand, creator, product",
    )
    metrics: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="entity -> metric -> value mapping",
    )
    winner_by_metric: dict[str, str] = Field(
        default_factory=dict,
        description="metric -> winning entity mapping",
    )
    insights: list[str] = Field(default_factory=list)
    time_period: str | None = None


class CreatorAnalysis(BaseModel):
    """Detailed analysis of a content creator."""

    username: str
    platform: str
    profile_url: str | None = None
    avatar_url: str | None = None

    # Classification
    creator_type: str = Field(
        default="unknown",
        description="e.g., 'beauty blogger', 'tech reviewer', 'food creator'",
    )
    content_themes: list[str] = Field(default_factory=list)
    niche: str | None = None

    # Metrics
    followers: int | None = None
    following: int | None = None
    total_videos: int | None = None
    posting_frequency: str | None = None  # e.g., "3 videos per week"
    average_views: int | None = None
    average_likes: int | None = None
    average_comments: int | None = None
    average_engagement_rate: float | None = None

    # Content insights
    top_performing_content: list[VideoReference] = Field(default_factory=list)
    content_style: str | None = None
    common_hashtags: list[str] = Field(default_factory=list)

    # Demographics (if available)
    region: str | None = None
    language: str | None = None
    audience_demographics: dict[str, Any] | None = None

    # Trends
    growth_trend: str | None = None  # "growing", "stable", "declining"
    recent_focus: str | None = None  # What they've been posting about recently


class AgentResponse(BaseModel):
    """Final response from the agent."""

    session_id: str
    query: str

    # Main answer
    answer: str = Field(..., description="Natural language answer to the query")

    # Supporting data
    video_references: list[VideoReference] = Field(default_factory=list)
    creator_analyses: list[CreatorAnalysis] = Field(default_factory=list)
    comparisons: list[ComparisonResult] = Field(default_factory=list)

    # Metadata about the search
    platforms_searched: list[str] = Field(default_factory=list)
    total_videos_analyzed: int = 0
    total_creators_analyzed: int = 0

    # Quality indicators
    confidence_score: float | None = Field(
        None,
        ge=0,
        le=1,
        description="Confidence in the answer (0-1)",
    )
    data_freshness: str | None = Field(
        None,
        description="How recent the data is (e.g., 'last 24 hours')",
    )

    # Execution info
    steps_taken: int = 0
    tools_used: list[str] = Field(default_factory=list)
    tool_execution_details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed execution results for each tool call including success/failure",
    )
    execution_time_seconds: float = 0

    # Usage and cost tracking
    usage_metrics: UsageMetrics | None = Field(
        None,
        description="Detailed usage and cost metrics for this query",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Clarification flow (per PRD)
    needs_clarification: bool = Field(
        False,
        description="Whether the query needs user clarification before proceeding",
    )
    clarification_question: str | None = Field(
        None,
        description="Question to ask the user for clarification",
    )

    # Parsed query with extracted slots (per PRD)
    parsed_query: Any | None = Field(
        None,
        description="Parsed query with extracted PRD slots",
    )

    def add_video_reference(self, ref: VideoReference) -> None:
        """Add a video reference to the response."""
        self.video_references.append(ref)
        self.total_videos_analyzed += 1

    def add_creator_analysis(self, analysis: CreatorAnalysis) -> None:
        """Add a creator analysis to the response."""
        self.creator_analyses.append(analysis)
        self.total_creators_analyzed += 1

    def to_markdown(self) -> str:
        """Format response as markdown for display."""
        lines = [
            f"## Answer\n\n{self.answer}\n",
        ]

        if self.video_references:
            lines.append("\n## Video References\n")
            for i, ref in enumerate(self.video_references, 1):
                lines.append(f"{i}. **[{ref.title or 'Video'}]({ref.url})**")
                if ref.creator:
                    lines.append(f"   - Creator: {ref.creator}")
                if ref.views:
                    lines.append(f"   - Views: {ref.views:,}")
                if ref.relevance_note:
                    lines.append(f"   - *{ref.relevance_note}*")
                lines.append("")

        if self.creator_analyses:
            lines.append("\n## Creator Profiles\n")
            for analysis in self.creator_analyses:
                lines.append(f"### @{analysis.username} ({analysis.platform})")
                lines.append(f"- Type: {analysis.creator_type}")
                if analysis.followers:
                    lines.append(f"- Followers: {analysis.followers:,}")
                if analysis.content_themes:
                    lines.append(f"- Themes: {', '.join(analysis.content_themes)}")
                lines.append("")

        if self.comparisons:
            lines.append("\n## Comparisons\n")
            for comp in self.comparisons:
                lines.append(f"Comparing: {', '.join(comp.entities)}\n")
                for insight in comp.insights:
                    lines.append(f"- {insight}")
                lines.append("")

        return "\n".join(lines)
