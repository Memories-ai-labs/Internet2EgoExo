"""Query and session data models."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from video_searching_agent.curation.viewpoint import Viewpoint


class QueryType(str, Enum):
    """Classification of user query types."""

    DATA_COLLECTION = "data_collection"  # "2h of egocentric cooking footage"
    ACTIVITY_SEARCH = "activity_search"  # "warehouse picking, fixed camera"
    DATASET_DISCOVERY = "dataset_discovery"  # "existing ego-exo datasets"
    SOURCE_SURVEY = "source_survey"  # "channels that publish POV assembly"
    VIDEO_ANALYSIS = "video_analysis"  # inspect one video's own content
    GENERAL = "general"  # Catch-all for other queries

    # Retained so older callers and stored sessions keep deserialising.
    INDUSTRY_TOPIC = "industry_topic"
    PRODUCT_SEARCH = "product_search"
    CREATOR_PROFILE = "creator_profile"
    CREATOR_DISCOVERY = "creator_discovery"
    COMPARISON = "comparison"
    CHANNEL_ANALYSIS = "channel_analysis"
    BRAND_ANALYSIS = "brand_analysis"
    CREATIVE_INSPIRATION = "creative_inspiration"


class MetricType(str, Enum):
    """Ranking criteria for candidate clips.

    `USABILITY` is the default for data collection: viewpoint match, then
    duration, then licence. The popularity metrics remain for callers that
    still want them, but they say nothing about training-data value.
    """

    USABILITY = "usability"  # Default: viewpoint match, duration, licence
    LONGEST = "longest"  # Longest continuous footage first

    MOST_POPULAR = "most_popular"  # Highest current views
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
        description="User asked about a specific video's own content",
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
        MetricType.USABILITY,
        description="Ranking criteria for candidate clips",
    )

    # Training-data collection slots
    viewpoint: Viewpoint | None = Field(
        None,
        description="Required camera viewpoint (egocentric/exocentric); None means any",
    )
    activities: list[str] = Field(
        default_factory=list,
        description="Activities or tasks the footage must show (e.g. 'chopping', 'assembly')",
    )
    min_duration_seconds: int | None = Field(
        None,
        ge=0,
        description="Reject clips shorter than this",
    )
    license_filter: str = Field(
        "any",
        description="'any', or 'reusable' to require a licence that permits reuse",
    )
    target_hours: float | None = Field(
        None,
        gt=0,
        description="How many hours of footage the run should try to collect",
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
