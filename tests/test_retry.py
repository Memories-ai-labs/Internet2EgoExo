"""Tests for RetryExecutor."""


import pytest

from video_searching_agent.tools.base import BaseTool, ToolResult
from video_searching_agent.tools.retry import RetryExecutor, get_fallback_tools


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, name: str = "mock_tool", results: list[ToolResult] | None = None):
        self._name = name
        self._results = results or []
        self._call_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Mock tool for testing"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        if self._call_count < len(self._results):
            result = self._results[self._call_count]
            self._call_count += 1
            return result
        # Default to success
        return ToolResult.ok({"data": "success"})


class TestRetryExecutor:
    """Tests for RetryExecutor."""

    def test_initialization(self):
        """Test executor initialization with custom parameters."""
        executor = RetryExecutor(
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            backoff_factor=3.0,
        )
        assert executor.max_retries == 5
        assert executor.base_delay == 2.0
        assert executor.max_delay == 60.0
        assert executor.backoff_factor == 3.0

    def test_default_initialization(self):
        """Test executor initialization with default parameters."""
        executor = RetryExecutor()
        assert executor.max_retries == 3
        assert executor.base_delay == 1.0
        assert executor.max_delay == 30.0
        assert executor.backoff_factor == 2.0

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_try(self):
        """Test successful execution without retry."""
        executor = RetryExecutor(max_retries=3)
        tool = MockTool(results=[ToolResult.ok({"data": "success"})])

        result = await executor.execute_with_retry(tool, query="test")

        assert result.success
        assert result.data["data"] == "success"
        assert tool._call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_retries_on_transient_error(self):
        """Test retry on transient errors."""
        executor = RetryExecutor(max_retries=3, base_delay=0.01)  # Fast for testing
        tool = MockTool(results=[
            ToolResult.fail("timeout error"),  # First attempt fails
            ToolResult.fail("connection timeout"),  # Second attempt fails
            ToolResult.ok({"data": "success"}),  # Third attempt succeeds
        ])

        result = await executor.execute_with_retry(tool, query="test")

        assert result.success
        assert tool._call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self):
        """Test non-retryable errors stop immediately."""
        executor = RetryExecutor(max_retries=3, base_delay=0.01)
        tool = MockTool(results=[
            ToolResult.fail("Invalid API key"),  # Non-retryable
        ])

        result = await executor.execute_with_retry(tool, query="test")

        assert not result.success
        assert tool._call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_instagram_is_fail_fast(self):
        """instagram_search should run a single attempt even for retryable errors."""
        executor = RetryExecutor(max_retries=3, base_delay=0.01)
        tool = MockTool(
            name="instagram_search",
            results=[
                ToolResult.fail("timeout error"),
                ToolResult.ok({"data": "would succeed on retry"}),
            ],
        )

        result = await executor.execute_with_retry(tool, query="test")

        assert not result.success
        assert tool._call_count == 1
        assert "Failed after 1 attempts" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_retry_video_analysis_is_fail_fast(self):
        """video_analysis should run a single attempt on retryable errors."""
        executor = RetryExecutor(max_retries=3, base_delay=0.01)
        tool = MockTool(
            name="video_analysis",
            results=[
                ToolResult.fail("timeout error"),
                ToolResult.ok({"data": "would succeed on retry"}),
            ],
        )

        result = await executor.execute_with_retry(tool, query="test")

        assert not result.success
        assert tool._call_count == 1
        assert "Failed after 1 attempts" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self):
        """Test failure after max retries exceeded."""
        executor = RetryExecutor(max_retries=2, base_delay=0.01)
        tool = MockTool(results=[
            ToolResult.fail("timeout error"),
            ToolResult.fail("timeout error"),
            ToolResult.fail("timeout error"),
        ])

        result = await executor.execute_with_retry(tool, query="test")

        assert not result.success
        assert "Failed after 3 attempts" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_fallback_primary_succeeds(self):
        """Test fallback not used when primary succeeds."""
        executor = RetryExecutor(max_retries=1, base_delay=0.01)
        primary = MockTool(name="primary", results=[ToolResult.ok({"data": "primary"})])
        fallback = MockTool(name="fallback", results=[ToolResult.ok({"data": "fallback"})])

        result = await executor.execute_with_fallback(primary, [fallback], query="test")

        assert result.success
        assert result.data["data"] == "primary"
        assert primary._call_count == 1
        assert fallback._call_count == 0

    @pytest.mark.asyncio
    async def test_execute_with_fallback_uses_fallback_on_primary_failure(self):
        """Test fallback is used when primary fails."""
        executor = RetryExecutor(max_retries=1, base_delay=0.01)
        primary = MockTool(name="primary", results=[
            ToolResult.fail("primary failed"),
            ToolResult.fail("primary failed"),
        ])
        fallback = MockTool(name="fallback", results=[ToolResult.ok({"data": "fallback"})])

        result = await executor.execute_with_fallback(primary, [fallback], query="test")

        assert result.success
        assert result.data["data"] == "fallback"
        # Should have warning about fallback being used
        assert len(result.warnings) > 0
        assert "fallback" in result.warnings[0].lower()

    @pytest.mark.asyncio
    async def test_execute_with_fallback_all_fail(self):
        """Test error message when all tools fail."""
        executor = RetryExecutor(max_retries=1, base_delay=0.01)
        primary = MockTool(name="primary", results=[
            ToolResult.fail("primary error"),
            ToolResult.fail("primary error"),
        ])
        fallback1 = MockTool(name="fallback1", results=[
            ToolResult.fail("fallback1 error"),
            ToolResult.fail("fallback1 error"),
        ])
        fallback2 = MockTool(name="fallback2", results=[
            ToolResult.fail("fallback2 error"),
            ToolResult.fail("fallback2 error"),
        ])

        result = await executor.execute_with_fallback(
            primary, [fallback1, fallback2], query="test"
        )

        assert not result.success
        # Should include all errors in the message
        assert "primary" in result.error.lower()
        assert "fallback1" in result.error.lower()
        assert "fallback2" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_fallback_multiple_fallbacks(self):
        """Test multiple fallbacks are tried in order."""
        executor = RetryExecutor(max_retries=1, base_delay=0.01)
        primary = MockTool(name="primary", results=[
            ToolResult.fail("primary failed"),
            ToolResult.fail("primary failed"),
        ])
        fallback1 = MockTool(name="fallback1", results=[
            ToolResult.fail("fallback1 failed"),
            ToolResult.fail("fallback1 failed"),
        ])
        fallback2 = MockTool(name="fallback2", results=[
            ToolResult.ok({"data": "fallback2 success"}),
        ])

        result = await executor.execute_with_fallback(
            primary, [fallback1, fallback2], query="test"
        )

        assert result.success
        assert result.data["data"] == "fallback2 success"
        assert primary._call_count >= 1
        assert fallback1._call_count >= 1
        assert fallback2._call_count == 1


class TestRetryableErrorDetection:
    """Tests for retryable error detection."""

    def test_is_retryable_error_timeout(self):
        """Test timeout errors are retryable."""
        executor = RetryExecutor()
        result = ToolResult.fail("Connection timeout")
        assert executor._is_retryable_error(result) is True

    def test_is_retryable_error_rate_limit(self):
        """Test rate limit errors are retryable."""
        executor = RetryExecutor()
        result = ToolResult.fail("Rate limit exceeded, too many requests")
        assert executor._is_retryable_error(result) is True

    def test_is_retryable_error_503(self):
        """Test 503 errors are retryable."""
        executor = RetryExecutor()
        result = ToolResult.fail("HTTP 503 Service Unavailable")
        assert executor._is_retryable_error(result) is True

    def test_is_retryable_error_connection(self):
        """Test connection errors are retryable."""
        executor = RetryExecutor()
        result = ToolResult.fail("Connection refused")
        assert executor._is_retryable_error(result) is True

    def test_is_retryable_error_auth_failure(self):
        """Test auth errors are not retryable."""
        executor = RetryExecutor()
        result = ToolResult.fail("Invalid API key")
        assert executor._is_retryable_error(result) is False

    def test_is_retryable_error_run_failed_bad_request(self):
        """Apify 400 run-failed errors should not be retried."""
        executor = RetryExecutor()
        result = ToolResult.fail(
            "Apify API error 400: {'error': {'type': 'run-failed', 'message': 'timed-out'}}"
        )
        assert executor._is_retryable_error(result) is False

    def test_is_retryable_error_success(self):
        """Test success is not retryable."""
        executor = RetryExecutor()
        result = ToolResult.ok({"data": "success"})
        assert executor._is_retryable_error(result) is False


class TestKwargsAdaptation:
    """Tests for kwargs adaptation between tools."""

    def test_adapt_kwargs_direct_match(self):
        """Test direct parameter matching."""
        executor = RetryExecutor()
        tool = MockTool()

        adapted = executor._adapt_kwargs_for_tool(tool, {"query": "test"})

        assert adapted["query"] == "test"

    def test_adapt_kwargs_mapping(self):
        """Test parameter mapping between tools."""
        executor = RetryExecutor()

        # Tool that expects 'query' parameter
        tool = MockTool()

        # Input with 'search_query' should map to 'query'
        adapted = executor._adapt_kwargs_for_tool(tool, {"search_query": "test"})

        # Should map search_query to query
        assert adapted.get("query") == "test" or "search_query" in adapted


class TestGetFallbackTools:
    """Tests for fallback tool configuration."""

    def test_get_fallback_tools_twitter(self):
        """Test Twitter has Exa fallback configured."""
        fallbacks = get_fallback_tools("twitter_search")
        assert "exa_search" in fallbacks

    def test_get_fallback_tools_unknown(self):
        """Test unknown tools return empty list."""
        fallbacks = get_fallback_tools("unknown_tool")
        assert fallbacks == []

    def test_get_fallback_tools_no_fallback(self):
        """Test tools with no fallback return empty list."""
        fallbacks = get_fallback_tools("twitter_profile_info")
        assert fallbacks == []
