"""The pass that gives the clean clips trees, and the rules it must not break.

Three properties are worth a test each, because each one has already cost
something in this repo when it was only a comment:

1. A *failed* listing prunes nothing. "The lookup broke" and "the collection is
   empty" are the same return value if you let them be, and acting on the second
   when it was the first deletes rows for clips that exist.
2. A tree lands without destroying the clip's provenance. `put` replaces a row,
   so the naive write blanks `source_video_id` and the span inside it — the only
   copy of where a clip came from.
3. A clip already carrying a tree is skipped unless re-annotation is asked for,
   because every pass over it costs money.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from video_searching_agent.pipeline.annotate_clean import (
    annotate_clean_collection,
    live_video_ids,
)
from video_searching_agent.store.annotations import AnnotationStore, Clip, Segment


class FakeLake:
    """Lists what it is told to, or raises. Records every call."""

    def __init__(self, pages: list[dict] | None = None, error: Exception | None = None):
        self.pages = pages or []
        self.error = error
        self.calls: list[dict] = []

    async def list_videos(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.pages[len(self.calls) - 1] if len(self.calls) <= len(self.pages) else {}


@dataclass
class FakeAnnotationRun:
    annotations: list[Any] = field(default_factory=list)


@dataclass
class FakeCuratedClip:
    video_id: str
    accepted: bool = True
    grade: str = "B"
    annotation_level: str = "L2"
    rejection_reason: str = ""
    annotation: Any = None


@dataclass
class FakeCurationReport:
    clips: list[FakeCuratedClip] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class FakeNode:
    def __init__(self, **kw):
        self.hier_level = kw.get("hier_level", "action")
        self.span_start = kw.get("span_start", 0.0)
        self.span_end = kw.get("span_end", 8.0)
        self.label = kw.get("label", "fit the shade")
        self.narration = kw.get("narration")
        self.left_hand = kw.get("left_hand", "holds the shade")
        self.right_hand = kw.get("right_hand", "turns the ring")
        self.objects = kw.get("objects", ["shade", "ring"])
        self.segment_id = kw.get("segment_id")
        self.parent_segment_id = kw.get("parent_segment_id")
        self.evidence: list[str] = []


class FakeAgent:
    """Returns a fixed curation result and counts how often it was paid for."""

    def __init__(self, nodes: list[Any] | None = None, raise_on: str = ""):
        self.nodes = nodes if nodes is not None else [FakeNode()]
        self.raise_on = raise_on
        self.curated: list[str] = []

    async def curate(self, video_ids=None, **kwargs):
        video_id = (video_ids or [""])[0]
        self.curated.append(video_id)
        if self.raise_on and self.raise_on == video_id:
            raise RuntimeError("the model refused")
        return FakeCurationReport(
            clips=[
                FakeCuratedClip(
                    video_id=video_id,
                    annotation=FakeAnnotationRun(annotations=list(self.nodes)),
                )
            ]
        )


def _store_with(*video_ids: str, trees: dict[str, int] | None = None) -> AnnotationStore:
    """A store as `record_refined` leaves it: provenance, pixels, no tree."""
    store = AnnotationStore(":memory:")
    trees = trees or {}
    for index, video_id in enumerate(video_ids):
        segments = [
            Segment(segment_id=f"old-{n}", hier_level="action", span_end=2.0, label="stale")
            for n in range(trees.get(video_id, 0))
        ]
        store.put(
            Clip(
                video_id=video_id,
                collection_id="col_clean",
                source_video_id=f"vid_source_{index}",
                source_start=10.0 + index,
                source_end=30.0 + index,
                duration_seconds=20.0,
                motion_mean=0.091,
                sharpness_mean=2800.0,
                query="someone assembling the lamp",
                segments=segments,
            )
        )
    return store


def _page(*video_ids: str) -> dict:
    return {"videos": [{"video_id": v} for v in video_ids]}


class TestAFailedLookupPrunesNothing:
    @pytest.mark.asyncio
    async def test_a_listing_error_returns_none_not_an_empty_list(self):
        assert await live_video_ids(FakeLake(error=RuntimeError("500")), "col_x") is None

    @pytest.mark.asyncio
    async def test_an_empty_collection_is_an_empty_list(self):
        """The distinction the None exists for: empty is a real answer."""
        assert await live_video_ids(FakeLake(pages=[{"videos": []}]), "col_x") == []

    @pytest.mark.asyncio
    async def test_nothing_is_pruned_or_paid_for_when_the_listing_broke(self):
        store = _store_with("vid_a", "vid_b")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(error=RuntimeError("503")), agent=agent, store=store
        )
        assert report.looked is False
        assert report.pruned == []
        assert agent.curated == [], "paid for an annotation after a failed lookup"
        assert store.totals()["clips"] == 2, "deleted rows it could not verify"
        assert report.errors and "could not list" in report.errors[0]


class TestReconcilingAgainstTheDatalake:
    @pytest.mark.asyncio
    async def test_a_row_whose_video_is_gone_is_dropped(self):
        """Three real rows pointed at videos deleted with a duplicate collection."""
        store = _store_with("vid_live", "vid_deleted")
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_live")]), agent=FakeAgent(), store=store
        )
        assert report.pruned == ["vid_deleted"]
        assert store.get("vid_deleted") is None
        assert store.get("vid_live") is not None


class TestTheTreeLandsWithoutLosingProvenance:
    @pytest.mark.asyncio
    async def test_the_span_it_was_cut_from_survives(self):
        store = _store_with("vid_clean")
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]), agent=FakeAgent(), store=store
        )
        clip = store.get("vid_clean")
        assert clip.source_video_id == "vid_source_0"
        assert (clip.source_start, clip.source_end) == (10.0, 30.0)
        assert clip.motion_mean == 0.091
        assert [r.nodes for r in report.annotated] == [1]
        assert report.with_hands and clip.segments[0].objects == ["shade", "ring"]

    @pytest.mark.asyncio
    async def test_a_run_that_produced_no_nodes_writes_nothing_and_says_why(self):
        store = _store_with("vid_clean")
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=FakeAgent(nodes=[]),
            store=store,
        )
        assert report.annotated == []
        assert store.get("vid_clean").segments == []
        assert report.results[0].skipped, "a clip with no tree must say why"

    @pytest.mark.asyncio
    async def test_an_agent_error_is_recorded_against_the_clip_not_swallowed(self):
        store = _store_with("vid_clean")
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=FakeAgent(raise_on="vid_clean"),
            store=store,
        )
        assert "curate failed" in report.results[0].error


class TestNotPayingTwiceForTheSameClip:
    @pytest.mark.asyncio
    async def test_a_clip_that_already_has_a_tree_is_skipped(self):
        store = _store_with("vid_done", trees={"vid_done": 2})
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_done")]), agent=agent, store=store
        )
        assert agent.curated == []
        assert "already has 2 node(s)" in report.results[0].skipped

    @pytest.mark.asyncio
    async def test_re_annotation_is_available_and_replaces_the_tree(self):
        store = _store_with("vid_done", trees={"vid_done": 2})
        agent = FakeAgent()
        await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_done")]),
            agent=agent,
            store=store,
            only_missing=False,
        )
        assert agent.curated == ["vid_done"]
        labels = [s.label for s in store.get("vid_done").segments]
        assert labels == ["fit the shade"], "the stale tree is still there"

    @pytest.mark.asyncio
    async def test_the_limit_caps_what_one_pass_pays_for(self):
        store = _store_with("v1", "v2", "v3", "v4")
        agent = FakeAgent()
        await annotate_clean_collection(
            lake=FakeLake(pages=[_page("v1", "v2", "v3", "v4")]),
            agent=agent,
            store=store,
            limit=2,
        )
        assert len(agent.curated) == 2

    @pytest.mark.asyncio
    async def test_a_video_with_no_row_is_reported_rather_than_annotated(self):
        """Refine records a row for everything it uploads, so a missing row is
        a lost record, not a new clip — and a tree needs a row to hang on."""
        store = _store_with("v1")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("v1", "v_orphan")]), agent=agent, store=store
        )
        assert agent.curated == ["v1"]
        orphan = [r for r in report.results if r.video_id == "v_orphan"]
        assert orphan and "no clip row" in orphan[0].skipped
