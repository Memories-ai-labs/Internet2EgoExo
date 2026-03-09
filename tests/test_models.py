"""Tests for data models."""


from video_searching_agent.models.query import AgentSession, ParsedQuery, QueryType
from video_searching_agent.models.result import AgentResponse, VideoReference
from video_searching_agent.models.video import (
    Platform,
    Video,
    VideoCollection,
    VideoMetrics,
)


class TestVideoMetrics:
    """Tests for VideoMetrics model."""

    def test_calculate_engagement_rate(self):
        """Test engagement rate calculation."""
        metrics = VideoMetrics(views=1000, likes=50, comments=10)
        rate = metrics.calculate_engagement_rate()
        assert rate == 6.0  # (50 + 10) / 1000 * 100

    def test_calculate_engagement_rate_no_views(self):
        """Test engagement rate with no views."""
        metrics = VideoMetrics(views=0, likes=50)
        rate = metrics.calculate_engagement_rate()
        assert rate is None


class TestVideo:
    """Tests for Video model."""

    def test_video_creation(self):
        """Test creating a video."""
        video = Video(
            platform=Platform.YOUTUBE,
            platform_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="Test Video",
        )
        assert video.platform == Platform.YOUTUBE
        assert video.platform_id == "abc123"
        assert video.id is not None  # Auto-generated

    def test_formatted_duration(self):
        """Test duration formatting."""
        video = Video(
            platform=Platform.YOUTUBE,
            platform_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            duration_seconds=125,
        )
        assert video.formatted_duration == "2:05"

    def test_formatted_duration_with_hours(self):
        """Test duration formatting with hours."""
        video = Video(
            platform=Platform.YOUTUBE,
            platform_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            duration_seconds=3725,  # 1:02:05
        )
        assert video.formatted_duration == "1:02:05"


class TestVideoCollection:
    """Tests for VideoCollection model."""

    def test_add_video(self):
        """Test adding videos to collection."""
        collection = VideoCollection()
        video = Video(
            platform=Platform.YOUTUBE,
            platform_id="abc123",
            url="https://youtube.com/watch?v=abc123",
        )
        collection.add_video(video)
        assert collection.total_count == 1
        assert len(collection.videos) == 1

    def test_deduplicate(self):
        """Test deduplication."""
        collection = VideoCollection()
        video1 = Video(
            platform=Platform.YOUTUBE,
            platform_id="abc123",
            url="https://youtube.com/watch?v=abc123",
        )
        video2 = Video(
            platform=Platform.YOUTUBE,
            platform_id="abc123",  # Same as video1
            url="https://youtube.com/watch?v=abc123",
        )
        video3 = Video(
            platform=Platform.YOUTUBE,
            platform_id="def456",
            url="https://youtube.com/watch?v=def456",
        )
        collection.videos = [video1, video2, video3]
        collection.total_count = 3

        deduped = collection.deduplicate()
        assert deduped.total_count == 2


class TestParsedQuery:
    """Tests for ParsedQuery model."""

    def test_query_type_default(self):
        """Test default query type."""
        query = ParsedQuery(original_query="test query")
        assert query.query_type == QueryType.GENERAL

    def test_query_with_entities(self):
        """Test query with extracted entities."""
        query = ParsedQuery(
            original_query="Analyze @mkbhd on YouTube",
            query_type=QueryType.CREATOR_PROFILE,
            creators=["mkbhd"],
            platforms=["youtube"],
        )
        assert query.creators == ["mkbhd"]
        assert "youtube" in query.platforms


class TestAgentSession:
    """Tests for AgentSession model."""

    def test_session_lifecycle(self):
        """Test session state transitions."""
        session = AgentSession(user_query="test query")
        assert session.status == "initialized"

        session.start()
        assert session.status == "running"

        session.complete("Final answer")
        assert session.status == "completed"
        assert session.final_answer == "Final answer"

    def test_increment_step(self):
        """Test step incrementing."""
        session = AgentSession(user_query="test", max_steps=3)
        assert session.increment_step() is True  # step 1
        assert session.increment_step() is True  # step 2
        assert session.increment_step() is False  # step 3 = max


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_to_markdown(self):
        """Test markdown formatting."""
        response = AgentResponse(
            session_id="test-123",
            query="test query",
            answer="This is the answer.",
            video_references=[
                VideoReference(
                    video_id="abc",
                    url="https://youtube.com/watch?v=abc",
                    title="Test Video",
                    platform="youtube",
                    views=1000,
                )
            ],
        )
        md = response.to_markdown()
        assert "This is the answer" in md
        assert "Test Video" in md
        assert "1,000" in md  # Formatted views
