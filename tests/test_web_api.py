"""Tests for the web API."""

import re
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from video_searching_agent.web.app import create_app
from video_searching_agent.web.middleware.rate_limit import TokenBucket
from video_searching_agent.web.schemas.events import (
    ClarificationEvent,
    CompleteEvent,
    ErrorEvent,
    ProgressEvent,
    StartedEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from video_searching_agent.web.schemas.requests import QueryRequest


class TestSSEEvents:
    """Test SSE event formatting."""

    def test_started_event(self):
        event = StartedEvent.create(session_id="test-123", query="test query")
        sse = event.to_sse()
        assert "event: started" in sse
        assert "test-123" in sse
        assert "test query" in sse

    def test_progress_event(self):
        event = ProgressEvent.create(step=1, max_steps=10, message="Processing...")
        sse = event.to_sse()
        assert "event: progress" in sse
        assert '"step": 1' in sse
        assert '"max_steps": 10' in sse

    def test_tool_call_event(self):
        event = ToolCallEvent.create(tool="youtube_search", input_data={"query": "AI"})
        sse = event.to_sse()
        assert "event: tool_call" in sse
        assert "youtube_search" in sse

    def test_tool_result_event_success(self):
        event = ToolResultEvent.create(tool="youtube_search", success=True, videos_found=5)
        sse = event.to_sse()
        assert "event: tool_result" in sse
        assert '"success": true' in sse
        assert '"videos_found": 5' in sse

    def test_tool_result_event_failure(self):
        event = ToolResultEvent.create(tool="youtube_search", success=False, error="API error")
        sse = event.to_sse()
        assert "event: tool_result" in sse
        assert '"success": false' in sse
        assert "API error" in sse

    def test_complete_event(self):
        response = {"answer": "Here are the videos", "video_references": []}
        event = CompleteEvent.create(response)
        sse = event.to_sse()
        assert "event: complete" in sse
        assert "Here are the videos" in sse

    def test_error_event(self):
        event = ErrorEvent.create(code="tool_error", message="Something went wrong")
        sse = event.to_sse()
        assert "event: error" in sse
        assert "tool_error" in sse
        assert "Something went wrong" in sse

    def test_tool_result_event_reports_indexing_status(self):
        """Datalake tools report status while indexing is unfinished."""
        event = ToolResultEvent.create(
            tool="video_analysis", success=True, videos_found=0, status="processing"
        )
        assert event.data["status"] == "processing"
        assert "event: tool_result" in event.to_sse()

    def test_tool_result_event_reports_moment_count(self):
        event = ToolResultEvent.create(
            tool="video_moment_search", success=True, moments_found=3
        )
        assert event.data["moments_found"] == 3

    def test_tool_result_event_omits_absent_detail(self):
        """Unset fields stay out of the payload."""
        event = ToolResultEvent.create(tool="youtube_search", success=True, videos_found=5)
        assert "status" not in event.data
        assert "moments_found" not in event.data

    def test_clarification_event(self):
        event = ClarificationEvent.create(
            question="Which platform?",
            options=["YouTube", "TikTok"],
        )
        sse = event.to_sse()
        assert "event: clarification_needed" in sse
        assert "Which platform?" in sse
        assert "YouTube" in sse


class TestQueryRequest:
    """Test query request validation."""

    def test_valid_request(self):
        request = QueryRequest(query="find trending AI videos")
        assert request.query == "find trending AI videos"
        assert request.clarification is None
        assert request.max_steps is None
        assert request.enable_clarification is True

    def test_request_with_all_fields(self):
        request = QueryRequest(
            query="find videos",
            clarification="on YouTube",
            max_steps=5,
            enable_clarification=False,
        )
        assert request.query == "find videos"
        assert request.clarification == "on YouTube"
        assert request.max_steps == 5
        assert request.enable_clarification is False

    def test_empty_query_rejected(self):
        with pytest.raises(ValueError):
            QueryRequest(query="")

    def test_max_steps_bounds(self):
        # Valid bounds
        QueryRequest(query="test", max_steps=1)
        QueryRequest(query="test", max_steps=20)

        # Invalid bounds
        with pytest.raises(ValueError):
            QueryRequest(query="test", max_steps=0)
        with pytest.raises(ValueError):
            QueryRequest(query="test", max_steps=21)


class TestTokenBucket:
    """Test rate limiting token bucket."""

    def test_initial_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1)
        assert bucket.tokens == 10

    def test_consume_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1)
        assert bucket.consume(5) is True
        assert bucket.tokens == 5

    def test_consume_all_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1)
        assert bucket.consume(10) is True
        assert bucket.consume(1) is False

    def test_time_until_available(self):
        bucket = TokenBucket(capacity=10, refill_rate=1)
        bucket.consume(10)  # Empty bucket
        wait_time = bucket.time_until_available(1)
        assert wait_time > 0
        assert wait_time <= 1  # Should be about 1 second for 1 token at rate 1/sec


class TestHealthEndpoint:
    """Test health check endpoint."""

    @patch("video_searching_agent.web.routers.health.get_agent")
    def test_health_check(self, mock_get_agent):
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent.get_tool_health.return_value = {
            "youtube_search": {"healthy": True, "error": None},
            "tiktok_search": {"healthy": False, "error": "API key missing"},
        }
        mock_get_agent.return_value = mock_agent

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["tools"]["total"] == 2
        assert data["tools"]["healthy"] == 1


class TestAuthMiddleware:
    """Test API key authentication middleware."""

    def test_health_no_auth_required(self):
        """Health endpoint should work without auth."""
        with patch("video_searching_agent.web.routers.health.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.get_tool_health.return_value = {}
            mock_get_agent.return_value = mock_agent

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/health")
            assert response.status_code == 200

    def test_query_requires_auth_when_configured(self):
        """Query endpoint should require auth when API keys are configured."""
        # Patch where it's used, not where it's defined
        with patch("video_searching_agent.web.middleware.auth.get_settings") as mock_settings:
            mock_settings_instance = MagicMock()
            mock_settings_instance.api_keys = "valid-key-1,valid-key-2"
            mock_settings_instance.api_key_header = "X-API-Key"
            mock_settings.return_value = mock_settings_instance

            # Also need to patch app creation settings
            with patch("video_searching_agent.web.app.get_settings") as mock_app_settings:
                mock_app_settings_instance = MagicMock()
                mock_app_settings_instance.cors_origins = "*"
                mock_app_settings_instance.api_debug = True
                mock_app_settings.return_value = mock_app_settings_instance

                # And rate limit settings
                rl_patch = "video_searching_agent.web.middleware.rate_limit.get_settings"
                with patch(rl_patch) as mock_rl:
                    mock_rl_instance = MagicMock()
                    mock_rl_instance.rate_limit_enabled = False
                    mock_rl_instance.rate_limit_rpm = 60
                    mock_rl.return_value = mock_rl_instance

                    app = create_app()
                    client = TestClient(app)

                    # Without API key
                    response = client.post(
                        "/api/v1/queries/stream",
                        json={"query": "test"},
                    )
                    assert response.status_code == 401
                    assert "Missing" in response.json()["message"]

                    # With invalid API key
                    response = client.post(
                        "/api/v1/queries/stream",
                        json={"query": "test"},
                        headers={"X-API-Key": "invalid-key"},
                    )
                    assert response.status_code == 401
                    assert "Invalid" in response.json()["message"]


class TestQueryRequestEdgeCases:
    """Test edge cases for query request validation."""

    def test_whitespace_only_query_rejected(self):
        """Query with only whitespace should be rejected."""
        with pytest.raises(ValueError):
            QueryRequest(query="   ")

    def test_whitespace_query_stripped(self):
        """Whitespace around query should be handled."""
        request = QueryRequest(query="  find videos  ")
        # Query should either be stripped or validation should accept it
        assert request.query.strip() == "find videos"

    def test_very_long_query_rejected(self):
        """Very long query strings over max_length should be rejected."""
        long_query = "find videos " * 500  # ~6000 chars, exceeds 2000 char limit
        with pytest.raises(ValueError):
            QueryRequest(query=long_query)

    def test_query_at_max_length(self):
        """Query at exactly max_length should work."""
        # max_length is 2000
        query = "a" * 2000
        request = QueryRequest(query=query)
        assert len(request.query) == 2000

    def test_unicode_query(self):
        """Unicode characters in query should work."""
        request = QueryRequest(query="Find 日本語 videos about 中文 content")
        assert "日本語" in request.query
        assert "中文" in request.query

    def test_special_characters_in_query(self):
        """Special characters should be handled."""
        request = QueryRequest(query="Find videos about C++ and @username #hashtag")
        assert "C++" in request.query
        assert "@username" in request.query
        assert "#hashtag" in request.query


class TestTokenBucketEdgeCases:
    """Test edge cases for rate limiting token bucket."""

    def test_consume_more_than_capacity(self):
        """Trying to consume more than capacity should fail."""
        bucket = TokenBucket(capacity=5, refill_rate=1)
        assert bucket.consume(10) is False
        assert bucket.tokens == 5  # Tokens unchanged

    def test_refill_over_time(self):
        """Bucket should refill tokens over time."""
        import time
        bucket = TokenBucket(capacity=10, refill_rate=10)  # 10 tokens/sec
        bucket.consume(10)  # Empty bucket
        time.sleep(0.2)  # Wait 200ms
        # Should have refilled ~2 tokens
        assert bucket.consume(1) is True

    def test_capacity_ceiling(self):
        """Tokens should not exceed capacity."""
        import time
        bucket = TokenBucket(capacity=5, refill_rate=100)  # Fast refill
        bucket.consume(2)
        time.sleep(0.1)  # Wait for refill
        # After refill, should not exceed capacity
        bucket.consume(0)  # Trigger refill calculation
        assert bucket.tokens <= bucket.capacity


class TestMalformedRequests:
    """Test handling of malformed requests."""

    def test_missing_query_field(self):
        """Request missing query field should fail."""
        with patch("video_searching_agent.web.routers.health.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.get_tool_health.return_value = {}
            mock_get_agent.return_value = mock_agent

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/queries/stream",
                json={},  # Missing query
            )
            assert response.status_code == 422  # Validation error

    def test_invalid_json(self):
        """Invalid JSON should fail gracefully."""
        with patch("video_searching_agent.web.routers.health.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.get_tool_health.return_value = {}
            mock_get_agent.return_value = mock_agent

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/queries/stream",
                content="not valid json",
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 422

    def test_wrong_content_type(self):
        """Request with wrong content type should fail."""
        with patch("video_searching_agent.web.routers.health.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.get_tool_health.return_value = {}
            mock_get_agent.return_value = mock_agent

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/queries/stream",
                content="query=test",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 422


class TestRateLimitingBehavior:
    """Test rate limiting behavior."""

    def test_rate_limit_exhaustion_and_recovery(self):
        """Rate limiting should exhaust and eventually recover."""
        bucket = TokenBucket(capacity=2, refill_rate=10)

        # Exhaust tokens
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        assert bucket.consume(1) is False  # Exhausted

        # Check time until available
        wait_time = bucket.time_until_available(1)
        assert wait_time > 0
        assert wait_time <= 0.2  # Should be ~0.1 sec at 10 tokens/sec

    def test_exempt_paths_not_limited(self):
        """Exempt paths should bypass rate limiting."""
        with patch("video_searching_agent.web.routers.health.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.get_tool_health.return_value = {}
            mock_get_agent.return_value = mock_agent

            app = create_app()
            client = TestClient(app)

            # Health endpoint is exempt - should work many times
            for _ in range(10):
                response = client.get("/api/v1/health")
                assert response.status_code == 200


class TestSSEEventEdgeCases:
    """Test edge cases for SSE events."""

    def test_event_with_special_characters(self):
        """Events should handle special characters in data."""
        event = StartedEvent.create(
            session_id="test-123",
            query='find "videos" with <special> chars & symbols'
        )
        sse = event.to_sse()
        # Should be properly escaped in JSON
        assert "started" in sse
        assert "test-123" in sse

    def test_event_with_newlines(self):
        """Events should handle newlines in data."""
        event = ErrorEvent.create(
            code="error",
            message="Line 1\nLine 2\nLine 3"
        )
        sse = event.to_sse()
        # Newlines should be escaped in JSON
        assert "\\n" in sse or "Line 1" in sse

    def test_tool_result_with_large_data(self):
        """Tool result events should handle large data."""
        event = ToolResultEvent.create(
            tool="test_tool",
            success=True,
            videos_found=1000,
        )
        sse = event.to_sse()
        assert "1000" in sse


class TestSourceSelection:
    """Test source (platform) pinning on the query request."""

    def test_sources_default_to_auto(self):
        """No sources means auto-select."""
        assert QueryRequest(query="find coffee videos").sources is None

    def test_sources_normalized_and_deduplicated(self):
        """Aliases map to canonical names, order is preserved, dupes dropped."""
        request = QueryRequest(
            query="find coffee videos",
            sources=["YouTube", "yt", " X ", "web", "tiktok"],
        )
        assert request.sources == ["youtube", "twitter", "web", "tiktok"]

    def test_empty_and_auto_mean_auto(self):
        """Empty list and the explicit 'auto' sentinel both mean auto-select."""
        assert QueryRequest(query="q", sources=[]).sources is None
        assert QueryRequest(query="q", sources=["auto"]).sources is None

    def test_unsupported_source_rejected(self):
        """Unknown sources are a validation error, not silently ignored."""
        with pytest.raises(ValueError, match="Unsupported source"):
            QueryRequest(query="q", sources=["vimeo"])


class TestSourcesForwarding:
    """Test that pinned sources reach the streaming agent."""

    def test_sources_forwarded_to_stream_query(self):
        captured: dict = {}

        async def fake_stream(**kwargs):
            captured.update(kwargs)
            yield StartedEvent.create(session_id="test-123", query=kwargs["user_query"])

        with patch("video_searching_agent.web.routers.queries.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.stream_query.side_effect = lambda **kwargs: fake_stream(**kwargs)
            mock_get_agent.return_value = mock_agent

            client = TestClient(create_app())
            response = client.post(
                "/api/v1/queries/stream",
                json={"query": "viral coffee videos", "sources": ["youtube", "x"]},
            )

            assert response.status_code == 200
            assert captured["user_query"] == "viral coffee videos"
            assert captured["sources"] == ["youtube", "twitter"]

    def test_auto_forwards_no_sources(self):
        captured: dict = {}

        async def fake_stream(**kwargs):
            captured.update(kwargs)
            yield StartedEvent.create(session_id="test-123", query=kwargs["user_query"])

        with patch("video_searching_agent.web.routers.queries.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.stream_query.side_effect = lambda **kwargs: fake_stream(**kwargs)
            mock_get_agent.return_value = mock_agent

            client = TestClient(create_app())
            response = client.post(
                "/api/v1/queries/stream",
                json={"query": "viral coffee videos"},
            )

            assert response.status_code == 200
            assert captured["sources"] is None


def _asset_paths() -> list[str]:
    """The hashed asset URLs the built index.html actually references.

    The bundle is hashed on every build, so the test reads the paths out of the
    served HTML rather than hard-coding names that go stale.
    """
    client = TestClient(create_app())
    html = client.get("/ui/").text
    return [f"/ui/{match}" for match in re.findall(r'(?:src|href)="/ui/(assets/[^"]+)"', html)]


class TestWebUI:
    """Test the bundled static UI (built from ui/ by Vite, output committed)."""

    def test_root_redirects_to_ui(self):
        client = TestClient(create_app())
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (307, 308)
        assert response.headers["location"] == "/ui/"

    def test_index_served(self):
        client = TestClient(create_app())
        response = client.get("/ui/")
        assert response.status_code == 200
        assert "Internet EgoExo Video Search" in response.text
        assert '<div id="root">' in response.text

    def test_assets_served(self):
        paths = _asset_paths()
        # A script and a stylesheet, both hashed by the build.
        assert any(path.endswith(".js") for path in paths)
        assert any(path.endswith(".css") for path in paths)

        client = TestClient(create_app())
        for path in paths:
            assert client.get(path).status_code == 200

    def test_ui_public_while_api_protected(self):
        """The UI loads without a key; the API still requires one."""
        with patch("video_searching_agent.web.middleware.auth.get_settings") as mock_settings:
            mock_settings_instance = MagicMock()
            mock_settings_instance.api_keys = "valid-key"
            mock_settings_instance.api_key_header = "X-API-Key"
            mock_settings.return_value = mock_settings_instance

            client = TestClient(create_app())

            assert client.get("/ui/").status_code == 200
            for path in _asset_paths():
                assert client.get(path).status_code == 200
            assert client.get("/", follow_redirects=False).status_code in (307, 308)

            response = client.post("/api/v1/queries/stream", json={"query": "test"})
            assert response.status_code == 401
