"""The dataset as a directory, rather than as three live services.

These tests pin the properties that make the exported folder usable by someone
who has neither an API key nor this repo: the media and the tree pair up by
filename alone, a clip whose footage could not be fetched still appears (saying
so) instead of vanishing from the count, and the paths in the manifest survive
the directory being moved.
"""

from __future__ import annotations

import json

import pytest

from video_searching_agent.pipeline.dataset import export_dataset
from video_searching_agent.store.annotations import AnnotationStore, Clip, Segment


class FakeLake:
    """A Datalake that hands back a URL for some videos and nothing for others."""

    def __init__(self, missing: set[str] | None = None) -> None:
        self.missing = missing or set()
        self.asked: list[str] = []

    async def get_video(self, video_id: str) -> dict:
        self.asked.append(video_id)
        if video_id in self.missing:
            return {"video_id": video_id, "source_url": None}
        return {"video_id": video_id, "source_url": f"https://signed.example/{video_id}.mp4"}


@pytest.fixture
def store() -> AnnotationStore:
    store = AnnotationStore(":memory:")
    store.put(
        Clip(
            video_id="vid_clean1",
            collection_id="col_clean",
            source_video_id="vid_src",
            source_start=15.0,
            source_end=130.0,
            title="someone assembling the cabinet",
            duration_seconds=115.0,
            viewpoint="egocentric",
            grade="B",
            annotation_level="L2",
            accepted=True,
            segments=[
                Segment(
                    segment_id="t1",
                    hier_level="task",
                    span_start=0.0,
                    span_end=115.0,
                    label="prepare-furniture-assembly",
                ),
                Segment(
                    segment_id="t1.a1",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=0.0,
                    span_end=81.0,
                    label="review-assembly-instructions",
                    left_hand="holds the instruction manual steady",
                    objects=["instruction manual"],
                ),
            ],
        )
    )
    # Cut but never annotated: a real state, and the export has to show it.
    store.put(
        Clip(
            video_id="vid_clean2",
            collection_id="col_clean",
            source_video_id="vid_src",
            source_start=200.0,
            source_end=206.0,
            title="someone assembling the lamp",
            duration_seconds=6.0,
            viewpoint="egocentric",
        )
    )
    return store


async def _export(tmp_path, store, **kw):
    written: dict[str, bytes] = {}

    async def fake_download(url: str, dest):
        dest.write_bytes(b"\x00mp4")
        written[dest.name] = b"\x00mp4"
        return 4

    import video_searching_agent.pipeline.dataset as export_module

    original = export_module._download
    export_module._download = fake_download
    try:
        report = await export_dataset(tmp_path, store=store, **kw)
    finally:
        export_module._download = original
    return report, written


async def test_media_and_tree_pair_up_by_filename(tmp_path, store):
    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.clips == 2
    for video_id in ("vid_clean1", "vid_clean2"):
        clip = tmp_path / "clips" / f"{video_id}.mp4"
        tree = tmp_path / "annotations" / f"{video_id}.json"
        assert clip.exists(), f"{video_id} has no media"
        assert tree.exists(), f"{video_id} has no annotation"
        assert json.loads(tree.read_text())["video_id"] == video_id


async def test_the_tree_carries_provenance_and_hands(tmp_path, store):
    await _export(tmp_path, store, lake=FakeLake())

    tree = json.loads((tmp_path / "annotations" / "vid_clean1.json").read_text())
    assert tree["source_video_id"] == "vid_src"
    assert (tree["source_start"], tree["source_end"]) == (15.0, 130.0)

    action = next(s for s in tree["segments"] if s["hier_level"] == "action")
    assert action["left_hand"] == "holds the instruction manual steady"
    assert action["objects"] == ["instruction manual"]


async def test_a_clip_with_no_tree_is_counted_not_hidden(tmp_path, store):
    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert (report.with_tree, report.without_tree) == (1, 1)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["clips"] == 2
    assert {row["video_id"] for row in manifest["items"]} == {"vid_clean1", "vid_clean2"}
    bare = next(r for r in manifest["items"] if r["video_id"] == "vid_clean2")
    assert bare["segment_count"] == 0


async def test_media_that_could_not_be_fetched_says_so(tmp_path, store):
    report, _ = await _export(tmp_path, store, lake=FakeLake(missing={"vid_clean2"}))

    assert report.media_failed == 1
    assert report.clips == 2, "a failed download must not drop the clip"

    tree = json.loads((tmp_path / "annotations" / "vid_clean2.json").read_text())
    assert tree["clip_file"] is None
    assert tree["annotation_file"] == "annotations/vid_clean2.json"
    assert any("vid_clean2" in err for err in report.errors)


async def test_paths_are_relative_so_the_directory_can_move(tmp_path, store):
    await _export(tmp_path, store, lake=FakeLake())

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for row in manifest["items"]:
        assert row["annotation_file"].startswith("annotations/")
        if row["clip_file"]:
            assert row["clip_file"].startswith("clips/")
            assert not row["clip_file"].startswith("/")


async def test_signed_urls_are_never_written_to_disk(tmp_path, store):
    """They expire in a day; a manifest holding one is broken by tomorrow."""
    await _export(tmp_path, store, lake=FakeLake())

    for path in (tmp_path / "manifest.json", tmp_path / "manifest.jsonl"):
        assert "signed.example" not in path.read_text()
    for path in (tmp_path / "annotations").glob("*.json"):
        assert "signed.example" not in path.read_text()


async def test_existing_media_is_not_downloaded_again(tmp_path, store):
    await _export(tmp_path, store, lake=FakeLake())
    report, written = await _export(tmp_path, store, lake=FakeLake())

    assert report.media_skipped == 2
    assert report.media_written == 0
    assert written == {}, "a re-export must not re-fetch footage that is already there"


async def test_refresh_media_overrides_the_skip(tmp_path, store):
    await _export(tmp_path, store, lake=FakeLake())
    report, _ = await _export(tmp_path, store, lake=FakeLake(), refresh_media=True)

    assert report.media_written == 2
    assert report.media_skipped == 0


async def test_no_media_writes_the_json_and_asks_the_lake_nothing(tmp_path, store):
    lake = FakeLake()
    report, _ = await _export(tmp_path, store, lake=lake, media=False)

    assert report.clips == 2
    assert lake.asked == []
    assert (tmp_path / "annotations" / "vid_clean1.json").exists()
    assert not any((tmp_path / "clips").glob("*.mp4"))


async def test_manifest_is_longest_first(tmp_path, store):
    await _export(tmp_path, store, lake=FakeLake())

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    durations = [row["duration_seconds"] for row in manifest["items"]]
    assert durations == sorted(durations, reverse=True)


async def test_jsonl_is_one_row_per_clip(tmp_path, store):
    await _export(tmp_path, store, lake=FakeLake())

    lines = (tmp_path / "manifest.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    assert {json.loads(line)["video_id"] for line in lines} == {
        "vid_clean1",
        "vid_clean2",
    }


async def test_a_collection_filter_narrows_the_export(tmp_path, store):
    store.put(
        Clip(
            video_id="vid_other",
            collection_id="col_elsewhere",
            duration_seconds=9.0,
            viewpoint="egocentric",
        )
    )

    report, _ = await _export(tmp_path, store, lake=FakeLake(), collection_id="col_clean")

    assert report.clips == 2
    assert not (tmp_path / "annotations" / "vid_other.json").exists()


# ---- the egocentric requirement -------------------------------------------
#
# The deliverable is first-person footage. These pin that a clip which is not
# confirmed egocentric does not reach the directory, and — just as important —
# that what was held back is *counted*, split by what the frames actually said.


async def test_exocentric_clips_do_not_reach_the_directory(tmp_path, store):
    store.put(
        Clip(
            video_id="vid_presenter",
            collection_id="col_clean",
            title="a man demonstrating smoke alarms to camera",
            duration_seconds=103.0,
            viewpoint="exocentric",
        )
    )

    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.clips == 2, "the exocentric clip must not be exported"
    assert not (tmp_path / "clips" / "vid_presenter.mp4").exists()
    assert not (tmp_path / "annotations" / "vid_presenter.json").exists()


async def test_an_unchecked_clip_is_held_back_too(tmp_path, store):
    """Not established and wrong have the same consequence at delivery."""
    store.put(Clip(video_id="vid_unseen", collection_id="col_clean", duration_seconds=30.0))

    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.clips == 2
    assert report.withheld.get("unchecked") == 1


async def test_what_was_held_back_is_counted_by_reason_not_as_a_total(tmp_path, store):
    """'12 excluded' hides whether to run step four or to fix the footage."""
    store.put(Clip(video_id="vid_exo", collection_id="col_clean", viewpoint="exocentric"))
    store.put(Clip(video_id="vid_unknown", collection_id="col_clean", viewpoint="unknown"))
    store.put(Clip(video_id="vid_unseen", collection_id="col_clean"))

    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.withheld == {"exocentric": 1, "unknown": 1, "unchecked": 1}
    assert report.withheld_total == 3

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["wanted_viewpoint"] == "egocentric"
    assert manifest["withheld_wrong_viewpoint"] == 3
    assert manifest["withheld_by_viewpoint"] == {
        "exocentric": 1,
        "unchecked": 1,
        "unknown": 1,
    }


async def test_any_ships_everything(tmp_path, store):
    """Somebody who wants the whole store is not making a mistake."""
    store.put(Clip(video_id="vid_exo", collection_id="col_clean", viewpoint="exocentric"))

    report, _ = await _export(tmp_path, store, lake=FakeLake(), viewpoint="any")

    assert report.clips == 3
    assert report.withheld == {}
    assert (tmp_path / "annotations" / "vid_exo.json").exists()


async def test_a_held_back_clip_is_never_downloaded(tmp_path, store):
    """The filter runs before the fetch, so it costs nothing to enforce."""
    store.put(Clip(video_id="vid_exo", collection_id="col_clean", viewpoint="exocentric"))
    lake = FakeLake()

    await _export(tmp_path, store, lake=lake)

    assert "vid_exo" not in lake.asked


async def test_a_clip_withheld_after_an_earlier_export_has_its_files_removed(tmp_path, store):
    """Step four can re-check a clip and change its mind. A manifest saying 2
    beside a directory holding 3 files hands the footage over anyway."""
    store.put(
        Clip(
            video_id="vid_presenter",
            collection_id="col_clean",
            duration_seconds=103.0,
            viewpoint="egocentric",
        )
    )
    await _export(tmp_path, store, lake=FakeLake())
    assert (tmp_path / "clips" / "vid_presenter.mp4").exists()

    store.set_viewpoint("vid_presenter", "exocentric")
    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.clips == 2
    assert report.removed_stale == 2, "both the mp4 and the json must go"
    assert not (tmp_path / "clips" / "vid_presenter.mp4").exists()
    assert not (tmp_path / "annotations" / "vid_presenter.json").exists()
    assert len(list((tmp_path / "clips").glob("*.mp4"))) == report.clips


async def test_nothing_the_exporter_did_not_write_is_deleted(tmp_path, store):
    """Only ids this pass considered and refused are the exporter's to remove."""
    (tmp_path / "clips").mkdir(parents=True, exist_ok=True)
    stranger = tmp_path / "clips" / "somebody-elses-file.mp4"
    stranger.write_bytes(b"not ours")
    notes = tmp_path / "README.txt"
    notes.write_text("hand-written")

    store.put(Clip(video_id="vid_exo", collection_id="col_clean", viewpoint="exocentric"))
    await _export(tmp_path, store, lake=FakeLake())

    assert stranger.exists()
    assert notes.exists()


async def test_a_still_is_written_beside_each_clip(tmp_path, store, monkeypatch):
    """The directory has to be browsable in a file manager, not only by script."""
    import video_searching_agent.pipeline.dataset as dataset_module

    made: list[str] = []

    def fake_still(video, dest, duration):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8jpeg")
        made.append(dest.stem)
        return True

    monkeypatch.setattr(dataset_module, "_still_from", fake_still)
    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.thumbnails == 2
    assert sorted(made) == ["vid_clean1", "vid_clean2"]
    for video_id in ("vid_clean1", "vid_clean2"):
        assert (tmp_path / "thumbnails" / f"{video_id}.jpg").exists()
        tree = json.loads((tmp_path / "annotations" / f"{video_id}.json").read_text())
        assert tree["thumbnail_file"] == f"thumbnails/{video_id}.jpg"


async def test_a_withheld_clip_loses_its_still_too(tmp_path, store, monkeypatch):
    import video_searching_agent.pipeline.dataset as dataset_module

    def fake_still(video, dest, duration):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8jpeg")
        return True

    monkeypatch.setattr(dataset_module, "_still_from", fake_still)
    store.put(
        Clip(
            video_id="vid_presenter",
            collection_id="col_clean",
            duration_seconds=103.0,
            viewpoint="egocentric",
        )
    )
    await _export(tmp_path, store, lake=FakeLake())
    assert (tmp_path / "thumbnails" / "vid_presenter.jpg").exists()

    store.set_viewpoint("vid_presenter", "exocentric")
    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert not (tmp_path / "thumbnails" / "vid_presenter.jpg").exists()
    assert report.removed_stale == 3, "the mp4, the json and the still"


async def test_a_host_with_no_ffmpeg_still_exports(tmp_path, store, monkeypatch):
    """A directory without stills is still a dataset."""
    import video_searching_agent.pipeline.dataset as dataset_module

    monkeypatch.setattr(dataset_module, "_still_from", lambda *a, **k: False)
    report, _ = await _export(tmp_path, store, lake=FakeLake())

    assert report.clips == 2
    assert report.thumbnails == 0
    tree = json.loads((tmp_path / "annotations" / "vid_clean1.json").read_text())
    assert tree["thumbnail_file"] is None


async def test_asking_for_exocentric_ships_the_fixed_camera(tmp_path, store):
    """The filter follows the request. Asking for exo, a tripod is the hit."""
    store.put(
        Clip(
            video_id="vid_tripod",
            collection_id="col_clean",
            duration_seconds=40.0,
            viewpoint="exocentric",
        )
    )

    report, _ = await _export(tmp_path, store, lake=FakeLake(), viewpoint="exocentric")

    assert report.clips == 1
    assert (tmp_path / "annotations" / "vid_tripod.json").exists()
    # The two egocentric fixtures are what is held back now.
    assert report.withheld == {"egocentric": 2}
    assert report.wanted_viewpoint == "exocentric"


async def test_an_unshippable_viewpoint_is_refused_outright(tmp_path, store):
    import pytest as _pytest

    with _pytest.raises(ValueError):
        await export_dataset(tmp_path, store=store, media=False, viewpoint="unknown")
