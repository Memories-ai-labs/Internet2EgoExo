"""Step three: cut the accepted spans and give them their own collection.

What these tests hold onto: a cut that was paid for is reported whether or not
its clip survived, provenance is on every uploaded clip because the clean
collection is worthless without it, one bad anchor does not abandon the cuts
already made, and a host that cannot do this step says so instead of failing.
"""

from __future__ import annotations

import pytest

from video_searching_agent.pipeline.clip_quality import ClipMeasurement, ClipVerdict
from video_searching_agent.pipeline.refine import (
    CUT_COST_USD,
    MAX_CLIP_SECONDS,
    MIN_CLIP_SECONDS,
    RefinedClip,
    RefineResult,
    ensure_clean_collection,
    refine_anchors,
)


class _FakeLake:
    """A Datalake that records what it was asked to do."""

    def __init__(
        self,
        *,
        collections: list[dict] | None = None,
        create_id: str = "col_clean",
        clip_fails: set[str] | None = None,
        upload_fails: set[str] | None = None,
    ):
        self.collections = collections or []
        self.create_id = create_id
        self.clip_fails = clip_fails or set()
        self.upload_fails = upload_fails or set()
        self.created: list[str] = []
        self.cuts: list[tuple[str, float, float]] = []
        self.uploads: list[dict] = []
        self._n = 0

    async def list_collections(self, limit: int = 100) -> dict:
        return {"collections": self.collections}

    async def create_collection(self, name: str) -> dict:
        self.created.append(name)
        return {"collection_id": self.create_id, "name": name}

    async def get_clip(self, video_id: str, start: float, end: float) -> dict:
        self.cuts.append((video_id, start, end))
        if video_id in self.clip_fails:
            raise RuntimeError("clip service said no")
        return {"url": f"https://example.test/{video_id}/{start:.0f}.mp4"}

    async def upload_video_file(self, path, collection_id=None, fps=None, metadata=None) -> dict:
        if str(path) in self.upload_fails:
            raise RuntimeError("upload rejected")
        self._n += 1
        self.uploads.append(
            {"path": str(path), "collection_id": collection_id, "metadata": metadata}
        )
        return {
            "video_id": f"vid_clean{self._n}",
            "operation": {"operation_id": f"op_{self._n}"},
        }


@pytest.fixture
def patched(monkeypatch, tmp_path):
    """A writable dir, a stub HTTP get, and a pixel pass that says yes."""
    from video_searching_agent.pipeline import refine

    monkeypatch.setattr(refine, "_writable_dir", lambda: str(tmp_path))
    monkeypatch.setattr(refine, "measure_clip", lambda path, **_: ClipMeasurement(frames=20))
    monkeypatch.setattr(refine, "judge_clip", lambda m: ClipVerdict(usable=True, measurement=m))

    class _Response:
        status_code = 200
        content = b"\x00" * 4096

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url):
            return _Response()

        async def aclose(self):
            return None

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", _Client)
    return tmp_path


ANCHORS = [
    {"video_id": "vid_a", "start": 10.0, "end": 40.0, "title": "folding laundry"},
    {"video_id": "vid_b", "start": 5.0, "end": 25.0, "url": "https://y.test/b"},
]


@pytest.mark.asyncio
async def test_survivors_land_in_the_clean_collection_with_their_provenance(patched):
    lake = _FakeLake()
    result = await refine_anchors(lake, ANCHORS, collection_name="egoexo-clean-clips")

    assert lake.created == ["egoexo-clean-clips"]
    assert result.collection_id == "col_clean"
    assert len(result.uploaded) == 2
    assert result.uploaded_seconds == pytest.approx(50.0)

    # Provenance under `custom`, which is the only place the endpoint takes
    # arbitrary keys — a clip nobody can trace is a clip that fails G0-PROV.
    first = lake.uploads[0]["metadata"]
    assert first["custom"]["source_video_id"] == "vid_a"
    assert first["custom"]["source_start"] == 10.0
    assert first["custom"]["source_end"] == 40.0
    assert "folding laundry" in first["title"]
    assert lake.uploads[1]["metadata"]["custom"]["source_url"] == "https://y.test/b"
    # Nothing arbitrary at the top level, which is what the endpoint rejects.
    assert set(first) == {"title", "custom"}


@pytest.mark.asyncio
async def test_an_existing_collection_is_reused_rather_than_duplicated(patched):
    lake = _FakeLake(collections=[{"name": "egoexo-clean-clips", "collection_id": "col_existing"}])
    result = await refine_anchors(lake, ANCHORS[:1], collection_name="egoexo-clean-clips")

    assert lake.created == []
    assert result.collection_id == "col_existing"


@pytest.mark.asyncio
async def test_a_clip_the_pixel_pass_rejects_is_not_uploaded_but_is_still_charged(
    patched, monkeypatch
):
    """A cut that was paid for and thrown away is the number a strict pass hides."""

    from video_searching_agent.pipeline import refine

    monkeypatch.setattr(
        refine,
        "judge_clip",
        lambda m: ClipVerdict(usable=False, reasons=["a static graphic"], measurement=m),
    )
    lake = _FakeLake()
    result = await refine_anchors(lake, ANCHORS)

    assert lake.uploads == []
    assert len(result.rejected) == 2
    assert result.cut_cost_usd == pytest.approx(2 * CUT_COST_USD)
    assert result.as_dict()["rejected_by_the_pixel_pass"] == 2
    assert [clip.stage for clip in result.clips] == ["rejected", "rejected"]


@pytest.mark.asyncio
async def test_one_failed_anchor_does_not_abandon_the_rest(patched):
    lake = _FakeLake(clip_fails={"vid_a"})
    result = await refine_anchors(lake, ANCHORS)

    assert len(result.clips) == 2
    assert result.clips[0].error and "clip service said no" in result.clips[0].error
    assert result.clips[1].uploaded is True
    # Only one cut is charged for. A `get_clip` that raised produced no clip, so
    # billing for it would overstate the run — which is the opposite of the
    # rejected-clip case above, where the cut succeeded and the file was then
    # thrown away. That one is charged, and should be.
    assert result.cut_cost_usd == pytest.approx(CUT_COST_USD)


@pytest.mark.asyncio
async def test_an_upload_failure_is_recorded_against_that_clip_alone(patched):
    lake = _FakeLake()
    lake.upload_fails = {str(patched / "clip_vid_a_10_40.mp4")}
    result = await refine_anchors(lake, ANCHORS)

    assert result.clips[0].uploaded is False
    assert "upload rejected" in (result.clips[0].error or "")
    assert result.clips[1].uploaded is True


class TestAnchorsNotWorthCutting:
    @pytest.mark.asyncio
    async def test_too_short_is_skipped_before_it_costs_anything(self, patched):
        lake = _FakeLake()
        result = await refine_anchors(
            lake, [{"video_id": "vid_a", "start": 0.0, "end": MIN_CLIP_SECONDS - 0.5}]
        )

        assert lake.cuts == [], "no cut was made"
        assert result.cut_cost_usd == 0.0
        assert result.clips[0].stage == "skipped"

    @pytest.mark.asyncio
    async def test_too_long_is_the_video_again(self, patched):
        lake = _FakeLake()
        result = await refine_anchors(
            lake, [{"video_id": "vid_a", "start": 0.0, "end": MAX_CLIP_SECONDS + 1}]
        )
        assert lake.cuts == []
        assert result.clips[0].stage == "skipped"

    @pytest.mark.asyncio
    async def test_a_malformed_anchor_is_reported_not_raised(self, patched):
        lake = _FakeLake()
        result = await refine_anchors(
            lake,
            [
                {"video_id": "vid_a", "start": "x", "end": 40.0},
                {"start": 1.0, "end": 40.0},
            ],
        )
        assert lake.cuts == []
        assert "numeric start and end" in (result.clips[0].error or "")
        assert "no video_id" in (result.clips[1].error or "")


class TestHostsThatCannotDoThisStep:
    @pytest.mark.asyncio
    async def test_a_read_only_filesystem_says_so_instead_of_failing(self, monkeypatch):
        from video_searching_agent.pipeline import refine

        monkeypatch.setattr(refine, "_writable_dir", lambda: None)
        lake = _FakeLake()
        result = await refine_anchors(lake, ANCHORS)

        assert result.clips == []
        assert lake.cuts == []
        assert "serverless" in (result.skipped_reason or "")

    @pytest.mark.asyncio
    async def test_a_collection_that_cannot_be_opened_stops_before_spending(
        self, patched, monkeypatch
    ):
        from video_searching_agent.pipeline import refine

        async def no_collection(lake, name):
            return None

        monkeypatch.setattr(refine, "ensure_clean_collection", no_collection)
        lake = _FakeLake()
        result = await refine_anchors(lake, ANCHORS)

        assert lake.cuts == []
        assert result.cut_cost_usd == 0.0
        assert "could not open" in (result.skipped_reason or "")


@pytest.mark.asyncio
async def test_the_deadline_stops_before_a_cut_it_cannot_upload(patched, monkeypatch):
    """A cut made and then abandoned is money spent for nothing."""

    import time as time_module

    from video_searching_agent.pipeline import refine

    monkeypatch.setattr(refine, "UPLOAD_FLOOR_SECONDS", 30.0)
    deadline = time_module.monotonic() + 5.0  # less than the floor
    lake = _FakeLake()
    result = await refine_anchors(lake, ANCHORS, deadline=deadline)

    assert lake.cuts == []
    assert result.cut_cost_usd == 0.0
    assert "out of time" in (result.skipped_reason or "")
    assert "not made rather than paid for" in (result.skipped_reason or "")


@pytest.mark.asyncio
async def test_max_clips_bounds_the_spend(patched):
    lake = _FakeLake()
    result = await refine_anchors(lake, ANCHORS, max_clips=1)

    assert len(result.clips) == 1
    assert result.cut_cost_usd == pytest.approx(CUT_COST_USD)


@pytest.mark.asyncio
async def test_the_downloaded_bytes_do_not_outlive_the_upload(patched):
    """The clip lives in the Datalake now; copies on a container that gets
    reclaimed are how a disk allowance disappears mid-run."""

    lake = _FakeLake()
    await refine_anchors(lake, ANCHORS)

    assert list(patched.glob("clip_*.mp4")) == []


@pytest.mark.asyncio
async def test_a_collection_response_shaped_either_way_is_read(patched):
    class Nested(_FakeLake):
        async def create_collection(self, name: str) -> dict:
            self.created.append(name)
            return {"collection": {"collection_id": "col_nested"}}

    assert await ensure_clean_collection(Nested(), "x") == "col_nested"


def test_the_result_reports_the_cuts_it_paid_for_even_with_nothing_uploaded():
    result = RefineResult(collection_name="x", cut_cost_usd=0.015)
    result.clips = [
        RefinedClip("vid_a", 0, 30, verdict=ClipVerdict(usable=False), cut_cost_usd=0.005)
    ]
    payload = result.as_dict()

    assert payload["uploaded"] == 0
    assert payload["rejected_by_the_pixel_pass"] == 1
    assert payload["cut_cost_usd"] == 0.015
