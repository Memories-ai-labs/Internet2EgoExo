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


class TestWaitingForTheCleanClipsToIndex:
    """Annotation cannot start on a clip that is still indexing, and the point of
    the clean collection is that it is what gets annotated next.

    This existed untested and had the wrong keyword: `timeout=` where the client
    takes `max_wait_seconds=`. The TypeError was caught by the same function's
    except clause and reported as "still indexing", so a wait that never ran
    looked exactly like a slow index — and the embedding check that followed it
    ran against a half-indexed clip and produced a wrong answer.
    """

    @staticmethod
    def _result(*operation_ids: str) -> RefineResult:
        result = RefineResult(collection_id="col_clean")
        for index, operation in enumerate(operation_ids, start=1):
            clip = RefinedClip("vid_src", 0.0, 20.0)
            clip.uploaded_video_id = f"vid_clean{index}"
            clip.operation_id = operation
            result.clips.append(clip)
        return result

    @pytest.mark.asyncio
    async def test_it_calls_the_client_the_way_the_client_is_written(self):
        from video_searching_agent.pipeline.refine import wait_for_clean_clips

        seen: list[dict] = []

        class Lake:
            async def wait_for_operation(
                self, operation_id, max_wait_seconds=None, poll_interval_seconds=None
            ):
                seen.append({"operation_id": operation_id, "max_wait_seconds": max_wait_seconds})
                return {"done": True}

        statuses = await wait_for_clean_clips(Lake(), self._result("op_1", "op_2"), timeout=90)

        assert [row["operation_id"] for row in seen] == ["op_1", "op_2"]
        assert {row["max_wait_seconds"] for row in seen} == {90}
        assert statuses == {"vid_clean1": "ready", "vid_clean2": "ready"}

    @pytest.mark.asyncio
    async def test_a_wrong_keyword_would_be_caught_here(self):
        """A client that only accepts the real keyword. If the call regresses to
        `timeout=`, this fails instead of silently reporting 'still indexing'."""

        from video_searching_agent.pipeline.refine import wait_for_clean_clips

        class StrictLake:
            async def wait_for_operation(self, operation_id, max_wait_seconds=None):
                return {"done": True}

        statuses = await wait_for_clean_clips(StrictLake(), self._result("op_1"))
        assert statuses == {"vid_clean1": "ready"}

    @pytest.mark.asyncio
    async def test_a_slow_index_is_reported_rather_than_raised(self):
        from video_searching_agent.pipeline.refine import wait_for_clean_clips

        class SlowLake:
            async def wait_for_operation(self, operation_id, max_wait_seconds=None):
                raise TimeoutError("still running after the budget")

        statuses = await wait_for_clean_clips(SlowLake(), self._result("op_1"))
        assert "still indexing" in statuses["vid_clean1"]

    @pytest.mark.asyncio
    async def test_nothing_uploaded_means_nothing_to_wait_for(self):
        from video_searching_agent.pipeline.refine import wait_for_clean_clips

        class Lake:
            async def wait_for_operation(self, *a, **k):
                raise AssertionError("should not be called")

        assert await wait_for_clean_clips(Lake(), RefineResult()) == {}


class TestTheCleanCollectionIsFoundNotMultiplied:
    """One clean collection, reused. Five duplicates say otherwise.

    `ensure_clean_collection` asked for `limit=200`; the endpoint caps it at 100
    and returns 400. A broad `except` turned that into an empty listing, an
    empty listing read as "no collection of that name", and every call created a
    fresh one — six collections named `egoexo-clean-clips` in ten minutes, each
    holding a slice of the output.
    """

    @staticmethod
    def _lake(rows, *, raise_on_list=False, limit_cap=100):
        class Lake:
            created: list[str] = []
            asked_limit: int | None = None

            async def list_collections(self, limit=100):
                Lake.asked_limit = limit
                if raise_on_list:
                    raise RuntimeError("boom")
                if limit > limit_cap:
                    raise RuntimeError(f"limit must be between 1 and {limit_cap}")
                return {"collections": rows}

            async def create_collection(self, name):
                Lake.created.append(name)
                return {"collection_id": f"col_new{len(Lake.created)}"}

        Lake.created = []
        return Lake()

    @pytest.mark.asyncio
    async def test_an_existing_collection_is_reused(self):
        from video_searching_agent.pipeline.refine import ensure_clean_collection

        lake = self._lake([{"id": "col_old", "name": "egoexo-clean-clips"}])
        got = await ensure_clean_collection(lake, "egoexo-clean-clips")
        assert got == "col_old"
        assert type(lake).created == [], "must not create when one already exists"

    @pytest.mark.asyncio
    async def test_the_limit_it_asks_for_is_inside_the_endpoints_range(self):
        """The regression itself: 200 was rejected and the failure was hidden."""
        from video_searching_agent.pipeline.refine import ensure_clean_collection

        lake = self._lake([{"id": "col_old", "name": "egoexo-clean-clips"}])
        await ensure_clean_collection(lake, "egoexo-clean-clips")
        assert type(lake).asked_limit is not None
        assert type(lake).asked_limit <= 100

    @pytest.mark.asyncio
    async def test_a_failed_lookup_creates_nothing(self):
        """The consequence that actually cost something.

        Not knowing whether a collection exists is not the same as knowing it
        does not, and only one of those justifies a create.
        """
        from video_searching_agent.pipeline.refine import ensure_clean_collection

        lake = self._lake([], raise_on_list=True)
        got = await ensure_clean_collection(lake, "egoexo-clean-clips")
        assert got is None
        assert type(lake).created == []

    @pytest.mark.asyncio
    async def test_duplicates_resolve_to_the_oldest_every_time(self):
        """So a name that already has duplicates stops scattering output."""
        from video_searching_agent.pipeline.refine import ensure_clean_collection

        lake = self._lake(
            [
                {"id": "col_newer", "name": "egoexo-clean-clips",
                 "created_at": "2026-08-22T19:12:00Z"},
                {"id": "col_oldest", "name": "egoexo-clean-clips",
                 "created_at": "2026-08-22T09:03:00Z"},
            ]
        )
        assert await ensure_clean_collection(lake, "egoexo-clean-clips") == "col_oldest"

    @pytest.mark.asyncio
    async def test_a_genuinely_absent_collection_is_created_once(self):
        from video_searching_agent.pipeline.refine import ensure_clean_collection

        lake = self._lake([{"id": "col_other", "name": "something-else"}])
        got = await ensure_clean_collection(lake, "egoexo-clean-clips")
        assert got == "col_new1"
        assert type(lake).created == ["egoexo-clean-clips"]
