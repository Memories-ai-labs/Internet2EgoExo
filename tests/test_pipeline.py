"""Tests for the collection pipeline: download bounds and ingest orchestration."""

from pathlib import Path
from typing import Any

import pytest

from tests.test_agents import _ACTION_REPLY, _TASK_REPLY, _FakeDatalake, _FakeGemini
from video_searching_agent.agent.annotation_agent import AnnotationAgent
from video_searching_agent.agent.cleaning_agent import CleaningAgent
from video_searching_agent.pipeline.download import (
    ClipDownloader,
    DownloadedClip,
    DownloadError,
    _select_info,
)
from video_searching_agent.pipeline.ingest import IngestPipeline


class _StubDownloader:
    """Stands in for yt-dlp: serves canned metadata and a fake file."""

    def __init__(
        self,
        info: dict[str, Any],
        clip: DownloadedClip | None = None,
        probe_error: str | None = None,
        download_error: str | None = None,
    ) -> None:
        self._info = info
        self._clip = clip
        self._probe_error = probe_error
        self._download_error = download_error
        self.downloads = 0
        self.discarded: list[DownloadedClip] = []

    async def probe_async(self, url: str) -> dict[str, Any]:
        if self._probe_error:
            raise DownloadError(self._probe_error)
        return self._info

    async def download_async(self, url: str) -> DownloadedClip:
        if self._download_error:
            raise DownloadError(self._download_error)
        self.downloads += 1
        assert self._clip is not None
        return self._clip

    def discard(self, clip: DownloadedClip) -> None:
        self.discarded.append(clip)


class _StubUploader(_FakeDatalake):
    """A Datalake that also accepts uploads and finishes indexing."""

    def __init__(self, *args: Any, done: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._done = done
        self.uploads: list[Path] = []

    async def upload_video_file(
        self, path: Path, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.uploads.append(path)
        return {"video_id": "vid_1", "operation": "op_1"}

    async def wait_for_operation(
        self, operation: str, max_wait_seconds: float | None = None
    ) -> dict[str, Any]:
        return {"done": self._done}


def _clip(tmp_path: Path, **overrides: Any) -> DownloadedClip:
    path = tmp_path / "youtube-abc.mp4"
    path.write_bytes(b"0" * 1024)
    defaults = {
        "url": "https://youtube.com/watch?v=abc",
        "path": path,
        "duration_seconds": 300,
        "filesize_bytes": 1024,
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "title": "POV cooking",
        "uploader": "chef",
        "extractor": "youtube",
        "license_note": "Creative Commons",
    }
    defaults.update(overrides)
    return DownloadedClip(**defaults)


def _pipeline(downloader: _StubDownloader, datalake: _StubUploader, gemini: _FakeGemini):
    return IngestPipeline(
        client=datalake,
        downloader=downloader,
        cleaning_agent=CleaningAgent(client=datalake),
        annotation_agent=AnnotationAgent(client=datalake, gemini=gemini),
    )


class TestDownloadBounds:
    """A collection run must not be able to fill the disk."""

    def test_playlists_unwrap_to_the_entry_that_was_fetched(self):
        info = {"_type": "playlist", "entries": [{"id": "abc", "duration": 12}]}
        assert _select_info(info)["id"] == "abc"

    def test_an_empty_playlist_is_an_error(self):
        with pytest.raises(DownloadError):
            _select_info({"_type": "playlist", "entries": []})

    def test_size_is_reported_in_megabytes(self, tmp_path):
        assert _clip(tmp_path, filesize_bytes=5 * 1024 * 1024).size_mb == 5.0

    def test_discarding_a_file_frees_the_disk(self, tmp_path):
        clip = _clip(tmp_path)
        ClipDownloader(output_dir=tmp_path).discard(clip)
        assert not clip.path.exists()

    def test_discarding_twice_is_not_an_error(self, tmp_path):
        clip = _clip(tmp_path)
        downloader = ClipDownloader(output_dir=tmp_path)
        downloader.discard(clip)
        downloader.discard(clip)

    def test_free_space_is_reported_for_pre_flight_checks(self, tmp_path):
        assert ClipDownloader(output_dir=tmp_path).free_space_mb() >= 0


class TestIngestPipeline:
    """Screen → download → upload → index → clean → annotate."""

    @pytest.mark.asyncio
    async def test_a_clip_that_clears_every_gate_is_accepted_and_annotated(self, tmp_path):
        downloader = _StubDownloader(
            {"title": "POV cooking", "duration": 300}, clip=_clip(tmp_path)
        )
        datalake = _StubUploader(
            caption="A first-person view; the left hand holds the onion, the right slices.",
            segments=[
                {"start": 0.0, "end": 120.0, "text": "the left hand holds the onion"},
            ],
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        result = await _pipeline(downloader, datalake, gemini).ingest(
            "https://youtube.com/watch?v=abc"
        )

        assert result.stage == "accepted"
        assert result.accepted is True
        assert result.video_id == "vid_1"
        assert result.annotation_level in ("L2", "L3")
        assert result.frame_check is not None and result.frame_check.hands_visible
        assert "hoi/chop-vegetables/right/move-knife" in result.tags_written

    @pytest.mark.asyncio
    async def test_screening_stops_a_short_clip_before_any_download(self, tmp_path):
        downloader = _StubDownloader({"title": "quick clip", "duration": 8})
        result = await _pipeline(
            downloader, _StubUploader(), _FakeGemini([])
        ).ingest("https://x/1", min_duration_seconds=60)

        assert result.stage == "skipped"
        assert downloader.downloads == 0
        assert "below the 60s minimum" in (result.rejection_reason or "")

    @pytest.mark.asyncio
    async def test_a_clip_with_no_hands_is_rejected_after_indexing(self, tmp_path):
        downloader = _StubDownloader(
            {"title": "kitchen tour", "duration": 300}, clip=_clip(tmp_path)
        )
        datalake = _StubUploader(
            caption="A wide shot of a kitchen; steam rises from a pot.",
            segments=[{"start": 0.0, "end": 60.0, "text": "steam rises from a pot"}],
        )
        result = await _pipeline(downloader, datalake, _FakeGemini([])).ingest(
            "https://youtube.com/watch?v=abc"
        )

        assert result.stage == "rejected"
        assert result.accepted is False
        assert result.rejection_reason == "no hands visible in the captions"
        assert result.annotation is None

    @pytest.mark.asyncio
    async def test_the_local_file_is_deleted_once_it_is_uploaded(self, tmp_path):
        clip = _clip(tmp_path)
        downloader = _StubDownloader({"title": "POV", "duration": 300}, clip=clip)
        datalake = _StubUploader(caption="Both hands knead dough.")
        await _pipeline(downloader, datalake, _FakeGemini([])).ingest("https://x/1")
        assert downloader.discarded == [clip]

    @pytest.mark.asyncio
    async def test_indexing_still_running_is_reported_not_failed(self, tmp_path):
        downloader = _StubDownloader(
            {"title": "POV", "duration": 300}, clip=_clip(tmp_path)
        )
        datalake = _StubUploader(caption="hands", done=False)
        result = await _pipeline(downloader, datalake, _FakeGemini([])).ingest("https://x/1")

        assert result.stage == "indexing"
        assert result.video_id == "vid_1"
        assert any("still running" in note for note in result.notes)

    @pytest.mark.asyncio
    async def test_a_failed_probe_never_spends_anything(self):
        downloader = _StubDownloader({}, probe_error="video unavailable")
        result = await _pipeline(
            downloader, _StubUploader(), _FakeGemini([])
        ).ingest("https://x/1")

        assert result.stage == "failed"
        assert result.error == "video unavailable"
        assert downloader.downloads == 0

    @pytest.mark.asyncio
    async def test_download_facts_reach_the_media_gates(self, tmp_path):
        downloader = _StubDownloader(
            {"title": "POV", "duration": 300},
            clip=_clip(tmp_path, height=360, width=640),
        )
        datalake = _StubUploader(
            caption="The left hand turns the valve.",
            segments=[{"start": 0.0, "end": 90.0, "text": "the left hand turns the valve"}],
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        result = await _pipeline(downloader, datalake, gemini).ingest("https://x/1")

        quality = result.as_dict()["quality"]
        resolution = next(c for c in quality["checks"] if c["id"] == "G1-RES")
        assert resolution["passed"] is False
        assert quality["commercial_use_ok"] is True

    @pytest.mark.asyncio
    async def test_annotation_can_be_turned_off_for_a_cheap_pass(self, tmp_path):
        downloader = _StubDownloader(
            {"title": "POV", "duration": 300}, clip=_clip(tmp_path)
        )
        datalake = _StubUploader(
            caption="Both hands fold the dough.",
            segments=[{"start": 0.0, "end": 60.0, "text": "both hands fold the dough"}],
        )
        gemini = _FakeGemini([])  # any model call would raise
        result = await _pipeline(downloader, datalake, gemini).ingest(
            "https://x/1", annotate=False
        )

        assert result.accepted is True
        assert result.annotation is None
        assert gemini.prompts == []

    @pytest.mark.asyncio
    async def test_the_payload_is_json_safe_end_to_end(self, tmp_path):
        import json

        downloader = _StubDownloader(
            {"title": "POV", "duration": 300}, clip=_clip(tmp_path)
        )
        datalake = _StubUploader(
            caption="The right hand moves the knife.",
            segments=[{"start": 0.0, "end": 60.0, "text": "the right hand moves the knife"}],
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        result = await _pipeline(downloader, datalake, gemini).ingest("https://x/1")
        payload = json.loads(json.dumps(result.as_dict()))
        assert payload["segments"] and payload["annotation"]["annotations"]
