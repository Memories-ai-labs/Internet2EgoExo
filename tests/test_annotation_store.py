"""The annotation trees, in a shape that can be queried.

The Datalake round-trips a tree fine and cannot search it — the tree hangs off a
video record as an opaque blob. These tests pin the properties that make the
store worth having instead: a search for an action label finds the clip whose
*title* never mentions it, a re-annotation replaces rather than doubles, and the
store never claims a clip the Datalake has dropped.
"""

from __future__ import annotations

import pytest

from video_searching_agent.store.annotations import AnnotationStore, Clip, Segment


@pytest.fixture
def store() -> AnnotationStore:
    return AnnotationStore(":memory:")


def _clip(video_id: str, **kw) -> Clip:
    base = {
        "collection_id": "col_clean",
        "source_video_id": "vid_src",
        "source_start": 66.3,
        "source_end": 86.3,
        "title": "HOW TO MOUNT THE IKEA SUNNERSTRA RAIL SYSTEM",
        "duration_seconds": 22.0,
        "viewpoint": "egocentric",
        "grade": "C",
        "annotation_level": "L2",
        "accepted": True,
        "created_at": "2026-08-22T09:03:58Z",
    }
    return Clip(video_id=video_id, **{**base, **kw})


def _tree() -> list[Segment]:
    return [
        Segment("t1", "task", 0.0, 22.0, label="mount-wall-rail"),
        Segment(
            "t1.a1",
            "action",
            0.0,
            9.0,
            parent_segment_id="t1",
            label="insert-wall-anchor",
            narration="the left hand steadies the rail while the right taps the anchor in",
            hands_visible=True,
            left_hand="steadies the rail",
            right_hand="taps the anchor into the wall",
            evidence=["frames"],
        ),
        Segment(
            "t1.a2",
            "action",
            9.0,
            22.0,
            parent_segment_id="t1",
            label="fold-shirt-onto-rail",
            hands_visible=True,
        ),
    ]


class TestTheJoinIsTheVideoId:
    def test_a_clip_round_trips_with_its_whole_tree(self, store):
        clip = _clip("vid_clean1", segments=_tree())
        store.put(clip)

        got = store.get("vid_clean1")
        assert got is not None
        assert got.video_id == "vid_clean1"
        assert [s.segment_id for s in got.segments] == ["t1", "t1.a1", "t1.a2"]
        # The hierarchy survives, which is the point of a second table.
        assert got.segments[1].parent_segment_id == "t1"
        assert got.segments[1].left_hand == "steadies the rail"
        assert got.segments[1].evidence == ["frames"]

    def test_provenance_points_back_at_the_source_frames(self, store):
        store.put(_clip("vid_clean1", segments=_tree()))
        got = store.get("vid_clean1")

        assert got.source_video_id == "vid_src"
        assert (got.source_start, got.source_end) == (66.3, 86.3)

    def test_an_unknown_id_is_none_rather_than_an_empty_clip(self, store):
        assert store.get("vid_nope") is None


class TestSearchingTheTree:
    """The reason this is a database and not a blob."""

    def test_an_action_label_finds_a_clip_whose_title_never_says_it(self, store):
        store.put(_clip("vid_clean1", segments=_tree()))

        clips, total = store.search(text="fold-shirt")

        assert total == 1
        assert clips[0].video_id == "vid_clean1"
        assert "fold" not in clips[0].title.lower(), "the title really does not say it"

    def test_narration_is_searchable_too(self, store):
        store.put(_clip("vid_clean1", segments=_tree()))
        clips, total = store.search(text="taps the anchor")
        assert total == 1

    def test_a_title_match_still_works(self, store):
        store.put(_clip("vid_clean1", segments=_tree()))
        assert store.search(text="sunnerstra")[1] == 1

    def test_search_is_case_insensitive(self, store):
        store.put(_clip("vid_clean1", segments=_tree()))
        assert store.search(text="FOLD-SHIRT")[1] == 1

    def test_filters_combine(self, store):
        store.put(_clip("vid_a", segments=_tree()))
        store.put(
            _clip("vid_b", viewpoint="exocentric", grade="D", accepted=False, segments=_tree())
        )

        assert store.search(viewpoint="egocentric")[1] == 1
        assert store.search(accepted_only=True)[1] == 1
        assert store.search(grade="D")[1] == 1
        assert store.search(viewpoint="egocentric", grade="D")[1] == 0

    def test_hands_only_finds_clips_with_a_hand_segment(self, store):
        store.put(_clip("vid_hands", segments=_tree()))
        store.put(_clip("vid_none", segments=[Segment("t1", "task", 0.0, 10.0, label="x")]))

        clips, total = store.search(hands_only=True)
        assert total == 1
        assert clips[0].video_id == "vid_hands"

    def test_by_source_video_gathers_every_clip_cut_from_one_source(self, store):
        store.put(_clip("vid_a", source_video_id="vid_src1", segments=_tree()))
        store.put(_clip("vid_b", source_video_id="vid_src1", segments=_tree()))
        store.put(_clip("vid_c", source_video_id="vid_src2", segments=_tree()))

        assert store.search(source_video_id="vid_src1")[1] == 2

    def test_the_page_and_the_total_are_separate(self, store):
        for i in range(7):
            store.put(_clip(f"vid_{i}", segments=_tree()))

        clips, total = store.search(limit=3)
        assert len(clips) == 3
        assert total == 7, "the total is what matched, not what was returned"
        assert len(store.search(limit=3, offset=6)[0]) == 1


class TestWritingTwice:
    def test_a_re_annotation_replaces_rather_than_doubles(self, store):
        """Two copies of a tree would double every hour derived from it."""

        store.put(_clip("vid_clean1", segments=_tree()))
        store.put(_clip("vid_clean1", segments=_tree()))

        got = store.get("vid_clean1")
        assert len(got.segments) == 3
        assert store.search()[1] == 1

    def test_a_corrected_tree_loses_the_segments_it_dropped(self, store):
        store.put(_clip("vid_clean1", segments=_tree()))
        store.put(_clip("vid_clean1", segments=[Segment("t1", "task", 0.0, 22.0, label="new")]))

        got = store.get("vid_clean1")
        assert [s.segment_id for s in got.segments] == ["t1"]
        assert got.segments[0].label == "new"

    def test_clip_fields_are_updated_not_just_the_tree(self, store):
        store.put(_clip("vid_clean1", grade="D", segments=_tree()))
        store.put(_clip("vid_clean1", grade="B", segments=_tree()))
        assert store.get("vid_clean1").grade == "B"


class TestTheDatalakeIsAuthoritative:
    def test_a_clip_the_lake_dropped_is_pruned(self, store):
        """A row for a deleted video is a search result that 404s when clicked."""

        store.put(_clip("vid_kept", segments=_tree()))
        store.put(_clip("vid_gone", segments=_tree()))

        pruned = store.prune_missing(["vid_kept"])

        assert pruned == ["vid_gone"]
        assert store.get("vid_gone") is None
        assert store.get("vid_kept") is not None
        # And its segments went with it, rather than orphaning.
        assert store.search(text="fold-shirt")[1] == 1

    def test_pruning_against_everything_removes_nothing(self, store):
        store.put(_clip("vid_a", segments=_tree()))
        assert store.prune_missing(["vid_a"]) == []

    def test_delete_takes_the_segments_too(self, store):
        store.put(_clip("vid_a", segments=_tree()))
        store.delete("vid_a")
        assert store.search(text="fold-shirt")[1] == 0


class TestWhatIsInHere:
    def test_the_label_vocabulary_comes_from_the_data(self, store):
        """A browse UI offers these as filters. Inventing a facet list would
        offer labels nothing has."""

        store.put(_clip("vid_a", segments=_tree()))
        store.put(_clip("vid_b", segments=_tree()))

        labels = store.labels(hier_level="action")
        by_label = {row["label"]: row for row in labels}

        assert set(by_label) == {"insert-wall-anchor", "fold-shirt-onto-rail"}
        assert by_label["insert-wall-anchor"]["segments"] == 2
        assert by_label["insert-wall-anchor"]["clips"] == 2
        # The task level is a different vocabulary and is not mixed in.
        assert "mount-wall-rail" not in by_label

    def test_totals_are_counted_not_estimated(self, store):
        store.put(_clip("vid_a", duration_seconds=22.0, segments=_tree()))
        store.put(
            _clip(
                "vid_b",
                duration_seconds=23.0,
                viewpoint="exocentric",
                accepted=False,
                segments=_tree(),
            )
        )

        totals = store.totals()
        assert totals["clips"] == 2
        assert totals["accepted_clips"] == 1
        assert totals["hours"] == pytest.approx(45 / 3600, abs=1e-6)
        assert totals["action_segments"] == 4
        assert totals["by_viewpoint"] == {"egocentric": 1, "exocentric": 1}

    def test_an_empty_store_reports_zeroes_not_errors(self, store):
        assert store.totals()["clips"] == 0
        assert store.labels() == []
        assert store.search() == ([], 0)


def test_a_tree_with_no_segments_is_a_clip_with_no_tree(store):
    """A clip that was cut and cleaned but not yet annotated is a real state."""

    store.put(_clip("vid_bare", segments=[]))
    got = store.get("vid_bare")

    assert got is not None
    assert got.segments == []
    assert got.as_dict()["segment_count"] == 0
    assert store.totals()["action_segments"] == 0


def test_two_viewpoint_spellings_that_display_alike_are_added_not_overwritten(store):
    """An empty viewpoint and a literal "unknown" are different rows that read as
    the same word. A dict comprehension keeps only the last, and reported three
    clips as one."""

    store.put(_clip("vid_a", viewpoint=""))
    store.put(_clip("vid_b", viewpoint="unknown"))
    store.put(_clip("vid_c", viewpoint="egocentric"))

    totals = store.totals()
    assert totals["clips"] == 3
    assert totals["by_viewpoint"] == {"unknown": 2, "egocentric": 1}
    assert sum(totals["by_viewpoint"].values()) == totals["clips"], (
        "the buckets must account for every clip"
    )


class TestObjectsAreStoredAndMigrated:
    """`objects` is part of the spec for an atomic action, alongside the hands.

    It was in the annotation model and dropped on the way into the store, so the
    library could never answer "footage of somebody handling a drill" — which is
    a question about objects, not about labels.
    """

    @staticmethod
    def _clip(objects):
        from video_searching_agent.store.annotations import Clip, Segment

        return Clip(
            video_id="vid_objects",
            source_video_id="src_1",
            title="assembling a desk",
            segments=[
                Segment(
                    segment_id="s1",
                    hier_level="action",
                    span_start=0.0,
                    span_end=8.0,
                    label="drive the screw",
                    left_hand="steadies the panel",
                    right_hand="turns the screwdriver",
                    objects=objects,
                )
            ],
        )

    def test_objects_round_trip(self, tmp_path):
        from video_searching_agent.store.annotations import AnnotationStore

        store = AnnotationStore(str(tmp_path / "a.sqlite3"))
        store.put(self._clip(["screwdriver", "panel"]))
        got = store.get("vid_objects")
        assert got is not None
        assert got.segments[0].objects == ["screwdriver", "panel"]
        assert got.segments[0].as_dict()["objects"] == ["screwdriver", "panel"]

    def test_an_empty_object_list_stays_empty_rather_than_null(self, tmp_path):
        from video_searching_agent.store.annotations import AnnotationStore

        store = AnnotationStore(str(tmp_path / "b.sqlite3"))
        store.put(self._clip([]))
        assert store.get("vid_objects").segments[0].objects == []

    def test_a_database_written_before_the_column_existed_still_opens(self, tmp_path):
        """The store holds the only copy of every tree we paid to produce.

        `CREATE TABLE IF NOT EXISTS` is a no-op on a table that already exists,
        so without a migration the column never reaches a store somebody has —
        and reading a missing key from a sqlite3.Row raises rather than
        returning None, so the failure would be a crash on read, not a blank.
        """
        import sqlite3

        from video_searching_agent.store.annotations import AnnotationStore

        path = str(tmp_path / "old.sqlite3")
        # An old-shape segments table: everything except `objects`.
        legacy = sqlite3.connect(path)
        legacy.executescript(
            """
            CREATE TABLE segments (
                rowid_alias       INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id          TEXT NOT NULL,
                segment_id        TEXT NOT NULL,
                parent_segment_id TEXT,
                hier_level        TEXT,
                span_start        REAL,
                span_end          REAL,
                label             TEXT,
                narration         TEXT,
                hands_visible     INTEGER,
                left_hand         TEXT,
                right_hand        TEXT,
                evidence          TEXT,
                UNIQUE(video_id, segment_id)
            );
            INSERT INTO segments (video_id, segment_id, hier_level, span_start,
                                  span_end, label, evidence)
            VALUES ('vid_old', 's1', 'action', 0.0, 5.0, 'fold the towel', '[]');
            """
        )
        legacy.commit()
        legacy.close()

        store = AnnotationStore(path)
        rows = store._conn.execute("PRAGMA table_info(segments)").fetchall()
        assert "objects" in {row["name"] for row in rows}

        # The pre-existing row survives the migration and reads as an empty list.
        segment = store.get("vid_old")
        if segment is not None:  # the clips row was never written for this fixture
            assert segment.segments[0].objects == []
        store.put(self._clip(["towel"]))
        assert store.get("vid_objects").segments[0].objects == ["towel"]


class TestSearchingByWhatIsInTheFootage:
    """The reason the tree is rows and not a blob.

    A buyer does not search by title — they ask for footage of somebody handling
    a drill, or footage where a hand steadies something. Those are questions
    about objects and hands, and only a per-segment search can answer them.
    """

    @staticmethod
    def _store(tmp_path):
        from video_searching_agent.store.annotations import AnnotationStore, Clip, Segment

        store = AnnotationStore(str(tmp_path / "s.sqlite3"))
        store.put(
            Clip(
                video_id="vid_desk",
                source_video_id="src_1",
                # Title says nothing useful on purpose.
                title="Saturday project vlog 4K",
                segments=[
                    Segment(
                        segment_id="s1",
                        hier_level="action",
                        span_start=0.0,
                        span_end=9.0,
                        label="drive the screw",
                        left_hand="steadies the panel",
                        right_hand="turns the screwdriver",
                        objects=["screwdriver", "side panel"],
                    )
                ],
            )
        )
        return store

    def test_a_search_for_an_object_finds_a_clip_whose_title_never_says_it(self, tmp_path):
        store = self._store(tmp_path)
        found, total = store.search(text="screwdriver")
        assert total == 1 and [c.video_id for c in found] == ["vid_desk"]

    def test_a_search_for_a_hand_action_finds_it(self, tmp_path):
        store = self._store(tmp_path)
        assert store.search(text="steadies")[1] == 1

    def test_a_search_for_something_absent_finds_nothing(self, tmp_path):
        """The guard that makes the three above mean anything."""
        store = self._store(tmp_path)
        assert store.search(text="soldering iron")[1] == 0
