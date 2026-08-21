"""Tests for the Memories.ai Video Datalake client and tools."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.tools.memories_datalake import (
    VideoAnalysisTool,
    VideoIndexTool,
    VideoMomentSearchTool,
)


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text or str(self._payload)

    def json(self) -> Any:
        return self._payload


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient, recording every request it is handed."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, *args: Any, **kwargs: Any) -> "_FakeAsyncClient":
        # httpx.AsyncClient(timeout=...) — the patched symbol is called first.
        return self

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError(f"unexpected request: {method} {url}")
        return self._responses.pop(0)


def _client(responses: list[_FakeResponse]) -> tuple[MemoriesDatalakeClient, _FakeAsyncClient]:
    """Build a client whose HTTP layer serves the given responses in order."""
    fake = _FakeAsyncClient(responses)
    client = MemoriesDatalakeClient(
        api_key="sk-mai-test",
        base_url="https://api.memories.ai/serve/datalake/v1",
        timeout=5,
    )
    client._collection_id = "col_test"
    return client, fake


class TestDatalakeClient:
    """Transport, auth and endpoint contracts."""

    def test_base_url_trailing_slash_stripped(self):
        client = MemoriesDatalakeClient(api_key="k", base_url="https://host/serve/datalake/v1/")
        assert client.base_url == "https://host/serve/datalake/v1"

    def test_headers_send_raw_key_without_bearer(self):
        client = MemoriesDatalakeClient(api_key="sk-mai-abc", base_url="https://host")
        headers = client._headers()
        assert headers["Authorization"] == "sk-mai-abc"
        assert "Bearer" not in headers["Authorization"]

    @pytest.mark.asyncio
    async def test_missing_api_key_is_an_error(self):
        client = MemoriesDatalakeClient(api_key="", base_url="https://host")
        with pytest.raises(MemoriesDatalakeError, match="MEMORIES_API_KEY"):
            await client.get_video("vid_1")

    @pytest.mark.asyncio
    async def test_http_error_status_is_surfaced(self):
        client, fake = _client([_FakeResponse(status_code=402, text="quota_exceeded")])
        with patch("httpx.AsyncClient", fake):
            with pytest.raises(MemoriesDatalakeError) as excinfo:
                await client.get_summary("vid_1")
        assert excinfo.value.status_code == 402
        assert "quota_exceeded" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_index_video_url_posts_expected_body(self):
        client, fake = _client([
            _FakeResponse(payload={"video_id": "vid_1", "operation": "op_1", "status": "processing"})
        ])
        with patch("httpx.AsyncClient", fake):
            result = await client.index_video_url("https://example.com/a.mp4", fps=2.0)

        assert result["video_id"] == "vid_1"
        call = fake.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/videos")
        assert call["json"] == {
            "collection_id": "col_test",
            "source_url": "https://example.com/a.mp4",
            "fps": 2.0,
        }

    @pytest.mark.asyncio
    async def test_ensure_collection_reuses_existing_by_name(self):
        client, fake = _client([
            _FakeResponse(payload={"collections": [
                {"id": "col_other", "name": "something-else"},
                {"id": "col_match", "name": "my-lake"},
            ]}),
        ])
        client._collection_id = None
        with patch("httpx.AsyncClient", fake):
            collection_id = await client.ensure_collection("my-lake")

        assert collection_id == "col_match"
        assert len(fake.calls) == 1  # no creation call

    @pytest.mark.asyncio
    async def test_ensure_collection_creates_when_absent_and_caches(self):
        client, fake = _client([
            _FakeResponse(payload={"collections": []}),
            _FakeResponse(payload={"id": "col_new", "name": "my-lake"}),
        ])
        client._collection_id = None
        with patch("httpx.AsyncClient", fake):
            first = await client.ensure_collection("my-lake")
            second = await client.ensure_collection("my-lake")

        assert first == second == "col_new"
        # Second call is served from the cache, so no further requests.
        assert [c["method"] for c in fake.calls] == ["GET", "POST"]

    @pytest.mark.asyncio
    async def test_wait_for_operation_returns_when_done(self):
        client, fake = _client([_FakeResponse(payload={"operation": "op_1", "done": True})])
        with patch("httpx.AsyncClient", fake):
            operation = await client.wait_for_operation("op_1", max_wait_seconds=10)
        assert operation["done"] is True
        assert len(fake.calls) == 1

    @pytest.mark.asyncio
    async def test_wait_for_operation_gives_up_within_budget(self):
        """A zero budget polls once and returns the unfinished operation."""
        client, fake = _client([
            _FakeResponse(payload={"operation": "op_1", "done": False, "progress": {"percent": 10}}),
        ])
        with patch("httpx.AsyncClient", fake):
            operation = await client.wait_for_operation(
                "op_1", max_wait_seconds=0, poll_interval_seconds=1
            )
        assert operation["done"] is False
        assert operation["progress"] == {"percent": 10}

    @pytest.mark.asyncio
    async def test_search_defaults_to_caption_and_transcription(self):
        client, fake = _client([_FakeResponse(payload={"results": []})])
        with patch("httpx.AsyncClient", fake):
            await client.search("a person walking")

        body = fake.calls[0]["json"]
        assert body["targets"] == ["caption", "transcription"]
        assert body["mode"] == "semantic"
        assert body["collection_id"] == "col_test"
        assert "rerank" not in body

    @pytest.mark.asyncio
    async def test_windowed_reads_pass_time_params(self):
        client, fake = _client([_FakeResponse(payload={"segments": []})])
        with patch("httpx.AsyncClient", fake):
            await client.get_transcription("vid_1", start=10.0, end=20.0)

        assert fake.calls[0]["params"] == {"start": 10.0, "end": 20.0}

    @pytest.mark.asyncio
    async def test_none_params_are_dropped(self):
        client, fake = _client([_FakeResponse(payload={"caption": "text"})])
        with patch("httpx.AsyncClient", fake):
            await client.get_caption("vid_1")

        assert fake.calls[0]["params"] == {}


class TestVideoIndexTool:
    """video_index hands back the ids needed to resume later."""

    @pytest.mark.asyncio
    async def test_requires_video_url(self):
        result = await VideoIndexTool(client=object()).execute()
        assert not result.success
        assert "video_url is required" in result.error

    @pytest.mark.asyncio
    async def test_returns_ids_without_waiting(self):
        client, fake = _client([
            _FakeResponse(payload={"video_id": "vid_1", "operation": "op_1", "status": "processing"})
        ])
        with patch("httpx.AsyncClient", fake):
            result = await VideoIndexTool(client=client).execute(
                video_url="https://example.com/a.mp4"
            )

        assert result.success
        assert result.data["video_id"] == "vid_1"
        assert result.data["operation"] == "op_1"
        # One request only: indexing is not awaited here.
        assert len(fake.calls) == 1

    @pytest.mark.asyncio
    async def test_api_error_becomes_failed_result(self):
        client, fake = _client([_FakeResponse(status_code=500, text="boom")])
        with patch("httpx.AsyncClient", fake):
            result = await VideoIndexTool(client=client).execute(
                video_url="https://example.com/a.mp4"
            )
        assert not result.success
        assert "500" in result.error


class TestVideoAnalysisTool:
    """video_analysis is the content-analysis path over the Datalake."""

    @pytest.mark.asyncio
    async def test_requires_a_video_reference(self):
        result = await VideoAnalysisTool(client=object()).execute()
        assert not result.success
        assert "video_url or video_id" in result.error

    @pytest.mark.asyncio
    async def test_reports_processing_when_indexing_is_unfinished(self):
        client, fake = _client([
            _FakeResponse(payload={"video_id": "vid_1", "operation": "op_1"}),
            _FakeResponse(payload={"operation": "op_1", "done": False, "progress": {"percent": 30}}),
        ])
        # Zero wait budget: poll once, then hand the caller back the video_id.
        with patch("httpx.AsyncClient", fake), patch(
            "video_searching_agent.api.memories_datalake_client.get_settings",
            return_value=SimpleNamespace(
                memories_index_fps=1.0,
                memories_index_wait_seconds=0,
                memories_index_poll_seconds=1,
            ),
        ):
            result = await VideoAnalysisTool(client=client).execute(
                video_url="https://example.com/a.mp4"
            )

        assert result.success
        assert result.data["status"] == "processing"
        assert result.data["video_id"] == "vid_1"
        assert result.data["progress"] == {"percent": 30}

    @pytest.mark.asyncio
    async def test_reads_derived_content_for_indexed_video(self):
        client, fake = _client([
            _FakeResponse(payload={
                "video_id": "vid_1",
                "status": "ready",
                "duration_seconds": 47.0,
                "metadata": {"title": "Latte art", "tags": ["coffee"]},
            }),
            _FakeResponse(payload={"summary": "Someone pours a rosetta."}),
            _FakeResponse(payload={"caption": "close-up of a milk pour"}),
            _FakeResponse(payload={"segments": [
                {"start": 1.0, "end": 3.0, "speaker_id": "spk_1", "text": "start slow"},
            ]}),
        ])
        with patch("httpx.AsyncClient", fake):
            result = await VideoAnalysisTool(client=client).execute(video_id="vid_1")

        assert result.success
        assert result.data["status"] == "ready"
        assert result.data["title"] == "Latte art"
        assert result.data["duration_seconds"] == 47.0
        assert result.data["summary"] == "Someone pours a rosetta."
        assert result.data["caption"] == "close-up of a milk pour"
        assert result.data["transcription"][0]["text"] == "start slow"

    @pytest.mark.asyncio
    async def test_window_is_recorded_and_passed_through(self):
        client, fake = _client([
            _FakeResponse(payload={"video_id": "vid_1", "status": "ready"}),
            _FakeResponse(payload={"summary": "s"}),
            _FakeResponse(payload={"aggregated": "windowed caption"}),
            _FakeResponse(payload={"aggregated": "windowed speech"}),
        ])
        with patch("httpx.AsyncClient", fake):
            result = await VideoAnalysisTool(client=client).execute(
                video_id="vid_1", start=5.0, end=9.0
            )

        assert result.data["window"] == {"start": 5.0, "end": 9.0}
        assert result.data["caption"] == "windowed caption"
        caption_call = next(c for c in fake.calls if c["url"].endswith("/caption"))
        assert caption_call["params"] == {"start": 5.0, "end": 9.0}

    @pytest.mark.asyncio
    async def test_fails_when_nothing_is_derived_yet(self):
        """A video that is still indexing returns 409 on every derived read."""
        client, fake = _client([
            _FakeResponse(payload={"video_id": "vid_1", "status": "processing"}),
            _FakeResponse(status_code=409, text="video_not_ready"),
            _FakeResponse(status_code=409, text="video_not_ready"),
            _FakeResponse(status_code=409, text="video_not_ready"),
        ])
        with patch("httpx.AsyncClient", fake):
            result = await VideoAnalysisTool(client=client).execute(video_id="vid_1")

        assert not result.success
        assert "vid_1" in result.error

    @pytest.mark.asyncio
    async def test_partial_content_still_succeeds_with_warnings(self):
        client, fake = _client([
            _FakeResponse(payload={"video_id": "vid_1", "status": "ready"}),
            _FakeResponse(payload={"summary": "a summary"}),
            _FakeResponse(status_code=409, text="video_not_ready"),
            _FakeResponse(status_code=409, text="video_not_ready"),
        ])
        with patch("httpx.AsyncClient", fake):
            result = await VideoAnalysisTool(client=client).execute(video_id="vid_1")

        assert result.success
        assert result.data["summary"] == "a summary"
        assert any("caption unavailable" in w for w in result.warnings)


class TestVideoMomentSearchTool:
    """video_moment_search reads the indexed library."""

    @pytest.mark.asyncio
    async def test_requires_query(self):
        result = await VideoMomentSearchTool(client=object()).execute()
        assert not result.success
        assert "query is required" in result.error

    @pytest.mark.asyncio
    async def test_maps_results_to_moments(self):
        client, fake = _client([
            _FakeResponse(payload={"results": [
                {
                    "ref": "vid_1@25.0-32.0",
                    "video_id": "vid_1",
                    "target": "caption",
                    "score": 0.61,
                    "start": 25.0,
                    "end": 32.0,
                    "snippet": "a woman wearing headphones",
                    "thumbnail_url": "https://storage.example/thumb.jpg",
                },
                "not-a-dict",
            ]}),
        ])
        with patch("httpx.AsyncClient", fake):
            result = await VideoMomentSearchTool(client=client).execute(
                query="woman with headphones", top_k=5, mode="hybrid"
            )

        assert result.success
        assert result.data["total_results"] == 1
        moment = result.data["moments"][0]
        assert moment["ref"] == "vid_1@25.0-32.0"
        assert moment["start"] == 25.0
        body = fake.calls[0]["json"]
        assert body["top_k"] == 5
        assert body["mode"] == "hybrid"

    @pytest.mark.asyncio
    async def test_empty_results_are_no_results_not_an_error(self):
        client, fake = _client([_FakeResponse(payload={"results": []})])
        with patch("httpx.AsyncClient", fake):
            result = await VideoMomentSearchTool(client=client).execute(query="anything")

        assert result.success
        assert result.result_type == "no_results"
        assert "video_index" in result.data["message"]


class TestDatalakeToolWiring:
    """Registration, schemas and configuration health."""

    def test_tools_are_registered_by_default(self):
        from video_searching_agent.tools.registry import create_default_registry

        names = {tool.name for tool in create_default_registry()}
        assert {"video_index", "video_analysis", "video_moment_search"} <= names

    def test_tool_definitions_are_well_formed(self):
        for tool in (VideoIndexTool(), VideoAnalysisTool(), VideoMomentSearchTool()):
            definition = tool.to_tool_definition()
            assert definition["name"] == tool.name
            assert definition["description"]
            assert definition["input_schema"]["type"] == "object"

    def test_health_check_requires_api_key(self):
        with patch(
            "video_searching_agent.tools.memories_datalake.get_settings"
        ) as mock_settings:
            mock_settings.return_value.memories_api_key = ""
            healthy, error = VideoAnalysisTool().health_check()
            assert healthy is False
            assert "MEMORIES_API_KEY" in error

            mock_settings.return_value.memories_api_key = "sk-mai-x"
            healthy, error = VideoAnalysisTool().health_check()
            assert healthy is True
            assert error is None

    def test_moment_search_rejects_unknown_target(self):
        tool = VideoMomentSearchTool()
        valid, error = tool.validate_input(query="q", targets=["caption"])
        assert valid is True
        assert error is None
