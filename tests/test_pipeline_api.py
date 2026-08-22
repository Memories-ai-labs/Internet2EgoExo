"""Tests for the collection and curation streaming endpoints."""

import contextlib
import json
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from video_searching_agent.agent.curation_agent import CuratedClip, CurationReport
from video_searching_agent.curation.quality_gates import build_hours_ledger
from video_searching_agent.pipeline.ingest import IngestResult
from video_searching_agent.web.app import create_app
from video_searching_agent.web.schemas.requests import CollectRequest, CurateRequest


def _events(raw: str) -> list[tuple[str, dict[str, Any]]]:
    """Parse an SSE body into (event, data) pairs.

    sse-starlette frames with CRLF, so both line endings are accepted here —
    a parser that only splits on \\n silently renders nothing.
    """
    parsed: list[tuple[str, dict[str, Any]]] = []
    for block in raw.replace("\r\n", "\n").split("\n\n"):
        name = payload = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                payload = line[5:].strip()
        if name and payload:
            parsed.append((name, json.loads(payload)))
    return parsed


class _FakePipeline:
    """Stands in for IngestPipeline, reporting the stages it walked."""

    def __init__(self, results: dict[str, IngestResult], stages: list[str] | None = None):
        self._results = results
        self._stages = stages or ["probing", "downloading", "accepted"]
        self.calls: list[dict[str, Any]] = []

    async def ingest(self, url: str, on_stage=None, **kwargs: Any) -> IngestResult:
        self.calls.append({"url": url, **kwargs})
        result = self._results[url]
        for stage in self._stages:
            result.stage = stage
            if on_stage is not None:
                await on_stage(result)
        return result


class _FakeCurationAgent:
    def __init__(self, report: CurationReport, error: Exception | None = None):
        self._report = report
        self._error = error
        self.calls: list[dict[str, Any]] = []

    async def curate(self, video_ids=None, on_clip=None, **kwargs: Any) -> CurationReport:
        self.calls.append({"video_ids": video_ids, **kwargs})
        if self._error:
            raise self._error
        for clip in self._report.clips:
            if on_clip is not None:
                await on_clip(clip)
        return self._report


class TestCollectRequestValidation:
    """The request body, which bounds what a single call can spend."""

    def test_urls_are_deduplicated_and_order_kept(self):
        body = CollectRequest(urls=["https://a/1", "https://b/2", "https://a/1"])
        assert body.urls == ["https://a/1", "https://b/2"]

    def test_non_http_urls_are_rejected(self):
        with pytest.raises(ValidationError):
            CollectRequest(urls=["file:///etc/passwd"])

    def test_at_least_one_url_is_required(self):
        with pytest.raises(ValidationError):
            CollectRequest(urls=[])

    def test_a_request_cannot_queue_an_unbounded_number_of_clips(self):
        with pytest.raises(ValidationError):
            CollectRequest(urls=[f"https://x/{index}" for index in range(26)])

    def test_the_deployment_can_cap_what_one_request_queues(self, monkeypatch):
        # A public deployment running on its owner's key needs a ceiling on the
        # bill a single caller can run up; indexing is per video-minute.
        from video_searching_agent.config import settings as settings_module

        monkeypatch.setenv("MAX_COLLECT_URLS", "2")
        settings_module.get_settings.cache_clear()
        try:
            CollectRequest(urls=["https://a/1", "https://b/2"])
            with pytest.raises(ValidationError, match="accepts 2 URLs per request"):
                CollectRequest(urls=["https://a/1", "https://b/2", "https://c/3"])
        finally:
            settings_module.get_settings.cache_clear()

    def test_hands_are_required_by_default(self):
        assert CollectRequest(urls=["https://a/1"]).require_hands is True
        assert CollectRequest(urls=["https://a/1"]).annotate is True


class TestCurateRequestValidation:
    def test_a_worklist_is_required(self):
        with pytest.raises(ValidationError):
            CurateRequest()

    def test_either_ids_or_a_tag_will_do(self):
        assert CurateRequest(video_ids=["vid_1"]).tag is None
        assert CurateRequest(tag="clean_pass").video_ids is None


class TestCollectStream:
    """`POST /api/v1/collect/stream`."""

    @staticmethod
    def _result(url: str, accepted: bool = True, **overrides: Any) -> IngestResult:
        result = IngestResult(url=url, accepted=accepted, video_id="vid_1")
        for key, value in overrides.items():
            setattr(result, key, value)
        return result

    def _post(self, pipeline: _FakePipeline, body: dict[str, Any]):
        with patch(
            "video_searching_agent.web.routers.pipeline.IngestPipeline",
            return_value=pipeline,
        ):
            client = TestClient(create_app())
            return client.post("/api/v1/collect/stream", json=body)

    def test_each_stage_is_streamed_before_the_clip_finishes(self):
        url = "https://youtube.com/watch?v=abc"
        pipeline = _FakePipeline({url: self._result(url)})
        response = self._post(pipeline, {"urls": [url]})

        assert response.status_code == 200
        events = _events(response.text)
        names = [name for name, _ in events]
        assert names[0] == "started"
        assert names.count("clip_stage") == 3
        assert names[-2:] == ["clip_done", "complete"]

    def test_the_complete_event_carries_the_indexed_ids(self):
        url = "https://youtube.com/watch?v=abc"
        response = self._post(
            _FakePipeline({url: self._result(url)}), {"urls": [url]}
        )
        complete = dict(_events(response.text))["complete"]
        assert complete["accepted_count"] == 1
        assert complete["video_ids"] == ["vid_1"]

    def test_a_rejected_clip_is_reported_with_its_reason(self):
        url = "https://youtube.com/watch?v=abc"
        pipeline = _FakePipeline(
            {
                url: self._result(
                    url, accepted=False, rejection_reason="no hands visible in the captions"
                )
            },
            stages=["probing", "cleaning", "rejected"],
        )
        response = self._post(pipeline, {"urls": [url]})
        complete = dict(_events(response.text))["complete"]
        assert complete["rejected_count"] == 1
        assert (
            complete["rejected"][0]["rejection_reason"]
            == "no hands visible in the captions"
        )

    def test_one_failing_clip_does_not_end_the_run(self):
        class _Exploding(_FakePipeline):
            async def ingest(self, url: str, on_stage=None, **kwargs: Any) -> IngestResult:
                if url.endswith("bad"):
                    raise RuntimeError("yt-dlp exploded")
                return await super().ingest(url, on_stage=on_stage, **kwargs)

        good = "https://youtube.com/watch?v=good"
        pipeline = _Exploding({good: self._result(good)})
        response = self._post(pipeline, {"urls": ["https://x/bad", good]})

        complete = dict(_events(response.text))["complete"]
        assert complete["accepted_count"] == 1
        assert complete["rejected"][0]["error"] == "yt-dlp exploded"

    def test_the_gate_settings_reach_the_pipeline(self):
        url = "https://youtube.com/watch?v=abc"
        pipeline = _FakePipeline({url: self._result(url)})
        self._post(
            pipeline,
            {
                "urls": [url],
                "require_hands": False,
                "viewpoint": "egocentric",
                "min_duration_seconds": 60,
                "annotate": False,
            },
        )
        call = pipeline.calls[0]
        assert call["require_hands"] is False
        assert call["wanted_viewpoint"].value == "egocentric"
        assert call["min_duration_seconds"] == 60
        assert call["annotate"] is False

    def test_a_bad_body_is_a_422_not_a_stream(self):
        client = TestClient(create_app())
        assert client.post("/api/v1/collect/stream", json={"urls": []}).status_code == 422


class TestCurateStream:
    """`POST /api/v1/curate/stream`."""

    @staticmethod
    def _report() -> CurationReport:
        report = CurationReport(query="first person cooking")
        report.clips = [
            CuratedClip(
                video_id="vid_1",
                accepted=True,
                grade="B",
                score=75,
                annotation_level="L3",
                duration_seconds=600,
                usable_seconds=540,
                idle_seconds=60,
                labeled=True,
            ),
            CuratedClip(
                video_id="vid_2",
                accepted=False,
                rejection_reason="no hands visible in the captions",
                duration_seconds=300,
            ),
        ]
        report.hours = build_hours_ledger(900, 540, 60, 540)
        return report

    def _post(self, agent: _FakeCurationAgent, body: dict[str, Any]):
        with patch(
            "video_searching_agent.web.routers.pipeline.CurationAgent",
            return_value=agent,
        ):
            client = TestClient(create_app())
            return client.post("/api/v1/curate/stream", json=body)

    def test_each_verdict_streams_as_it_lands(self):
        response = self._post(
            _FakeCurationAgent(self._report()), {"video_ids": ["vid_1", "vid_2"]}
        )
        assert response.status_code == 200
        names = [name for name, _ in _events(response.text)]
        assert names == ["started", "clip_done", "clip_done", "complete"]

    def test_the_complete_event_keeps_the_hour_measures_apart(self):
        response = self._post(
            _FakeCurationAgent(self._report()), {"video_ids": ["vid_1", "vid_2"]}
        )
        complete = dict(_events(response.text))["complete"]
        hours = complete["hours"]
        assert hours["delivered_hours"] == 0.25
        assert hours["accepted_hours"] == 0.15
        assert hours["accepted_labeled_hours"] == 0.15
        assert complete["accepted_clips"] == 1
        assert complete["batch_grade"] == "B"

    def test_a_tag_worklist_is_passed_through(self):
        agent = _FakeCurationAgent(self._report())
        self._post(agent, {"tag": "clean_pass", "query": "cooking"})
        assert agent.calls[0]["tag"] == "clean_pass"
        assert agent.calls[0]["query"] == "cooking"

    def test_a_failure_is_streamed_as_an_error_event(self):
        agent = _FakeCurationAgent(self._report(), error=RuntimeError("datalake down"))
        response = self._post(agent, {"video_ids": ["vid_1"]})
        events = dict(_events(response.text))
        assert "error" in events
        assert events["error"]["message"] == "datalake down"

    def test_a_body_with_no_worklist_is_rejected(self):
        client = TestClient(create_app())
        assert client.post("/api/v1/curate/stream", json={}).status_code == 422


class TestHowManyVideosCanBeCuratedAtOnce:
    """Curation had the collect cap bolted onto it, which is the wrong cost.

    Collecting a URL is a download, an upload and an index — minutes each, so 25
    is a real guard. Curating an already-indexed video is a caption read, about
    0.6s, so the same number rejected a perfectly ordinary run of 35 clips with
    `body.video_ids: List should have at most 25 items`.
    """

    def test_a_set_larger_than_the_collect_cap_is_accepted(self):
        from video_searching_agent.web.schemas.requests import (
            MAX_URLS_PER_REQUEST,
            CurateRequest,
        )

        ids = [f"vid_{n}" for n in range(MAX_URLS_PER_REQUEST + 10)]
        request = CurateRequest(video_ids=ids)
        assert len(request.video_ids or []) == MAX_URLS_PER_REQUEST + 10

    def test_there_is_still_a_ceiling(self):
        import pytest
        from pydantic import ValidationError

        from video_searching_agent.web.schemas.requests import (
            MAX_VIDEOS_PER_CURATION,
            CurateRequest,
        )

        with pytest.raises(ValidationError):
            CurateRequest(video_ids=[f"vid_{n}" for n in range(MAX_VIDEOS_PER_CURATION + 1)])

    def test_the_two_ceilings_are_not_the_same_number(self):
        """If they get unified again, this is the failure that says why not."""

        from video_searching_agent.web.schemas.requests import (
            MAX_URLS_PER_REQUEST,
            MAX_VIDEOS_PER_CURATION,
        )

        assert MAX_VIDEOS_PER_CURATION > MAX_URLS_PER_REQUEST


class TestNotLookingTwiceAtTheSameFrames:
    """A verdict the search already bought is carried, not re-bought.

    The frame check now runs at search time, so a candidate queued from the
    results has already been looked at. Paying $0.002 to reach the same verdict,
    and showing a "looking" stage for work that was already settled, is waste
    on both counts.
    """

    def test_the_request_can_name_what_was_already_checked(self):
        from video_searching_agent.web.schemas.requests import CollectRequest

        body = CollectRequest(
            urls=["https://www.youtube.com/watch?v=a", "https://www.youtube.com/watch?v=b"],
            viewpoint_verified_urls=["https://www.youtube.com/watch?v=a"],
        )
        assert body.viewpoint_verified_urls == ["https://www.youtube.com/watch?v=a"]

    def test_it_defaults_to_nothing_checked(self):
        """A URL pasted by hand never came through a search."""

        from video_searching_agent.web.schemas.requests import CollectRequest

        body = CollectRequest(urls=["https://www.youtube.com/watch?v=a"])
        assert body.viewpoint_verified_urls == []

    @pytest.mark.asyncio
    async def test_a_verified_url_skips_the_look(self, monkeypatch):
        from video_searching_agent.curation.viewpoint import Viewpoint
        from video_searching_agent.pipeline.ingest import IngestPipeline

        looked: list[str] = []

        pipeline = IngestPipeline.__new__(IngestPipeline)

        class Cleaning:
            def screen(self, info, **kwargs):
                from video_searching_agent.agent.cleaning_agent import ScreeningVerdict

                return ScreeningVerdict(url=info.get("url"), accepted=True)

            async def look(self, verdict, info, **kwargs):
                looked.append(str(info.get("url")))
                return verdict

        class Downloader:
            async def probe_async(self, url):
                return {"id": "x", "title": "a clip", "duration": 120}

            async def download_async(self, url):
                raise RuntimeError("stop here; the look is what is under test")

        pipeline._cleaning = Cleaning()
        pipeline._downloader = Downloader()

        stages: list[str] = []

        async def on_stage(result):
            stages.append(result.stage)

        url = "https://www.youtube.com/watch?v=a"
        with contextlib.suppress(Exception):
            await pipeline.ingest(
                url,
                wanted_viewpoint=Viewpoint.EGOCENTRIC,
                on_stage=on_stage,
                viewpoint_verified=True,
            )
        assert looked == []
        assert "looking" not in stages

        with contextlib.suppress(Exception):
            await pipeline.ingest(
                url,
                wanted_viewpoint=Viewpoint.EGOCENTRIC,
                on_stage=on_stage,
                viewpoint_verified=False,
            )
        assert looked == [url]
