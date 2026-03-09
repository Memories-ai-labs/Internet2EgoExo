"""Query and session data models."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Classification of user query types."""

    INDUSTRY_TOPIC = "industry_topic"  # "trending UGC for SaaS"
    BRAND_ANALYSIS = "brand_analysis"  # "analyze Sephora's Reels"
    PRODUCT_SEARCH = "product_search"  # "viral videos featuring mugs"
    CREATOR_PROFILE = "creator_profile"  # "what type of blogger is @user"
    CREATOR_DISCOVERY = "creator_discovery"  # "10 popular pet bloggers"
    COMPARISON = "comparison"  # "Coca-Cola vs Pepsi"
    CHANNEL_ANALYSIS = "channel_analysis"  # "@mkbhd's views on tech"
    CREATIVE_INSPIRATION = "creative_inspiration"  # title/script generation
    VIDEO_ANALYSIS = "video_analysis"  # analyze specific video content
    GENERAL = "general"  # Catch-all for other queries


class MetricType(str, Enum):
    """Metric types for sorting/filtering videos per PRD."""

    MOST_POPULAR = "most_popular"  # Default: highest current views
    FASTEST_GROWTH_VIEWS = "fastest_growth_views"  # View velocity
    HIGHEST_ENGAGEMENT = "highest_engagement"  # Engagement rate
    MOST_LIKED = "most_liked"  # Highest likes
    MOST_COMMENTED = "most_commented"  # Highest comments
    MOST_SHARED = "most_shared"  # Highest shares
    MOST_RECENT = "most_recent"  # Most recently published


class TimeFrame(str, Enum):
    """Time frame options for video search per PRD."""

    PAST_24_HOURS = "past_24_hours"
    PAST_48_HOURS = "past_48_hours"
    PAST_WEEK = "past_week"
    PAST_MONTH = "past_month"
    PAST_YEAR = "past_year"  # Default
    ALL_TIME = "all_time"


class SortOrder(str, Enum):
    """Sort order for results."""

    DESC = "desc"  # Default: highest first
    ASC = "asc"  # Lowest first


class SubTask(BaseModel):
    """A sub-task decomposed from the main query."""

    task_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    description: str
    tool_name: str
    tool_input: dict[str, Any]
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of tasks this depends on",
    )
    status: str = "pending"  # pending, running, completed, failed
    result: Any | None = None
    error: str | None = None

    def mark_running(self) -> None:
        """Mark task as running."""
        self.status = "running"

    def mark_completed(self, result: Any) -> None:
        """Mark task as completed with result."""
        self.status = "completed"
        self.result = result

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error message."""
        self.status = "failed"
        self.error = error


class ParsedQuery(BaseModel):
    """Structured representation of a user query with PRD-defined slots."""

    original_query: str
    query_type: QueryType = QueryType.GENERAL

    # Extracted entities
    brands: list[str] = Field(default_factory=list)
    creators: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)

    # Platform preferences
    platforms: list[str] = Field(
        default_factory=list,
        description="Preferred platforms for search",
    )

    # Time constraints
    time_range: str | None = None  # "past week", "2025", "last 30 days"

    # Special requirements
    needs_video_analysis: bool = Field(
        False,
        description="Requires Memories.ai deep video analysis",
    )
    is_comparison: bool = False
    comparison_entities: list[str] = Field(default_factory=list)
    result_count: int | None = Field(
        None,
        description="Requested number of results (e.g., 'give me 10 bloggers')",
    )

    # PRD-defined slots (see prd.md Slot Extraction section)
    video_category: str | None = Field(
        None,
        description="Video category (industry, brand, product). E.g., 'Technology', 'Beauty'",
    )
    metric: MetricType = Field(
        MetricType.MOST_POPULAR,
        description="Metric for sorting/filtering videos",
    )
    time_frame: TimeFrame = Field(
        TimeFrame.PAST_YEAR,
        description="Time range for video search",
    )
    quantity: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of videos requested",
    )
    language: str | None = Field(
        None,
        description="Video language (ISO code, e.g., 'en', 'zh-CN')",
    )
    sort_order: SortOrder = Field(
        SortOrder.DESC,
        description="Sorting direction (desc/asc)",
    )

    # Extraction metadata
    extraction_confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores per extracted slot (0-1)",
    )
    needs_clarification: bool = Field(
        False,
        description="Whether the query needs user clarification",
    )
    clarification_reason: str | None = Field(
        None,
        description="Reason why clarification is needed",
    )

    # Decomposed sub-tasks
    sub_tasks: list[SubTask] = Field(default_factory=list)


class AgentSession(BaseModel):
    """Tracks the state of an agent session."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_query: str
    parsed_query: ParsedQuery | None = None

    # Execution tracking
    current_step: int = 0
    max_steps: int = Field(default=10, description="Maximum iteration steps")

    # Results accumulation
    search_results: list[dict[str, Any]] = Field(default_factory=list)
    videos_found: list[str] = Field(
        default_factory=list,
        description="Video IDs collected during search",
    )

    # State
    status: str = "initialized"  # initialized, running, needs_more_info, completed, failed
    final_answer: str | None = None
    error_message: str | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    # Conversation history for Claude
    messages: list[dict[str, Any]] = Field(default_factory=list)

    def start(self) -> None:
        """Mark session as started."""
        self.status = "running"

    def complete(self, answer: str) -> None:
        """Mark session as completed with final answer."""
        self.status = "completed"
        self.final_answer = answer
        self.completed_at = datetime.now(UTC)

    def fail(self, error: str) -> None:
        """Mark session as failed with error message."""
        self.status = "failed"
        self.error_message = error
        self.completed_at = datetime.now(UTC)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.messages.append({"role": role, "content": content})

    def increment_step(self) -> bool:
        """Increment step counter and return True if under limit."""
        self.current_step += 1
        return self.current_step < self.max_steps
