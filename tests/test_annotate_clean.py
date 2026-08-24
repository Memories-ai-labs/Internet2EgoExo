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

import json
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


class FakeEyes:
    """Hands back frames without an ffmpeg or a Datalake."""

    def __init__(self, available: bool = True, error: str = "") -> None:
        self.available = available
        self.error = error
        self.looked_at: list[str] = []

    async def look(self, video_id: str, start: float, end: float, count: int = 4):
        self.looked_at.append(video_id)
        from video_searching_agent.agent.eyes import Frames

        if self.error:
            return Frames(video_id=video_id, start=start, end=end, error=self.error)
        return Frames(
            video_id=video_id,
            start=start,
            end=end,
            images=[b"jpeg"] * count,
            width=1920,
            height=1080,
        )


class FakeSightLLM:
    """Speaks the ReAct protocol: look once, then answer.

    Scripted rather than canned so the tests exercise the loop the real gate
    runs — a fake that returned a verdict without ever calling `look` would
    pass a gate that had lost its eyes.
    """

    def __init__(
        self,
        viewpoint: str = "egocentric",
        matches: bool | None = None,
        why: str = "the camera is worn",
        looks: int = 1,
        answer_first: bool = False,
        replies: list[str] | None = None,
    ) -> None:
        self.viewpoint = viewpoint
        self.matches = viewpoint == "egocentric" if matches is None else matches
        self.why = why
        self.looks = looks
        self.answer_first = answer_first
        self.replies = replies
        self.turns = 0

    def new_conversation(self, opening):
        # One conversation per clip, and the real client carries no state
        # between them. Without this reset the script ran on past its end and
        # the second clip was judged without a look.
        self.turns = 0
        self.conversations = getattr(self, "conversations", 0) + 1
        return [{"role": "user", "content": opening}]

    def new_visual_conversation(self, prompt, frames):
        return [{"role": "user", "content": prompt, "frames": len(frames)}]

    async def create_message_async(self, messages, system=None, max_tokens=1200):
        if self.replies is not None:
            reply = self.replies[min(self.turns, len(self.replies) - 1)]
            self.turns += 1
            return reply
        self.turns += 1
        if not self.answer_first and self.turns <= self.looks:
            return json.dumps(
                {"thought": "see the footage", "tool": "look",
                 "arguments": {"start": 0, "end": 10, "frames": 4}}
            )
        return json.dumps(
            {"matches": self.matches, "viewpoint": self.viewpoint, "why": self.why}
        )

    def get_text_response(self, response):
        return response

    def append_model_response(self, messages, response):
        messages.append({"role": "assistant", "content": response})

    def append_user_text(self, messages, text):
        messages.append({"role": "user", "content": text})

    def append_user_images(self, messages, text, images):
        messages.append({"role": "user", "content": text, "images": len(images)})


def _sighted(**kw):
    """The gate's dependencies, defaulting to a clip that is first-person."""
    kw.setdefault("eyes", FakeEyes())
    kw.setdefault("llm", FakeSightLLM())
    return kw


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
            **_sighted(), lake=FakeLake(pages=[_page("vid_live")]), agent=FakeAgent(), store=store
        )
        assert report.pruned == ["vid_deleted"]
        assert store.get("vid_deleted") is None
        assert store.get("vid_live") is not None


class TestTheTreeLandsWithoutLosingProvenance:
    @pytest.mark.asyncio
    async def test_the_span_it_was_cut_from_survives(self):
        store = _store_with("vid_clean")
        report = await annotate_clean_collection(
            **_sighted(), lake=FakeLake(pages=[_page("vid_clean")]), agent=FakeAgent(), store=store
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
            **_sighted(),
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
            **_sighted(),
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
            **_sighted(), lake=FakeLake(pages=[_page("vid_done")]), agent=agent, store=store
        )
        assert agent.curated == []
        assert "already has 2 node(s)" in report.results[0].skipped

    @pytest.mark.asyncio
    async def test_re_annotation_is_available_and_replaces_the_tree(self):
        store = _store_with("vid_done", trees={"vid_done": 2})
        agent = FakeAgent()
        await annotate_clean_collection(
            **_sighted(),
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
            **_sighted(),
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
            **_sighted(), lake=FakeLake(pages=[_page("v1", "v_orphan")]), agent=agent, store=store
        )
        assert agent.curated == ["v1"]
        orphan = [r for r in report.results if r.video_id == "v_orphan"]
        assert orphan and "no clip row" in orphan[0].skipped


class TestTheDeliverableIsTheViewpointAskedFor:
    """The gate that reads the *clip's* frames, not the candidate's.

    PRE-SIGHT screens candidates before download and is deliberately lenient —
    unknown never rules a candidate out, because the caption pass gets the last
    word. Here there is no later pass, so the rule inverts: confirmed to be the
    viewpoint that was asked for, or it does not ship.

    Asked-for, not preferred. A set built out of exocentric footage wants the
    fixed camera, and refusing a tripod shot there would refuse the request.
    """

    @pytest.mark.asyncio
    async def test_an_exocentric_clip_is_refused_before_it_is_paid_for(self):
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="exocentric", why="a presenter faces a static camera"),
        )
        assert agent.curated == [], "the annotation spend must not happen"
        assert report.annotated == []
        assert len(report.refused) == 1
        assert "asked for egocentric" in report.results[0].skipped
        assert "a presenter faces a static camera" in report.results[0].skipped
        assert store.get("vid_clean").segments == []

    @pytest.mark.asyncio
    async def test_the_verdict_is_recorded_so_a_second_pass_need_not_look_again(self):
        store = _store_with("vid_clean")
        await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=FakeAgent(),
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="exocentric"),
        )
        assert store.get("vid_clean").viewpoint == "exocentric"

    @pytest.mark.asyncio
    async def test_a_refusal_does_not_erase_the_provenance(self):
        """set_viewpoint merges; a naive put would blank the span it was cut from."""
        store = _store_with("vid_clean")
        await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=FakeAgent(),
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="exocentric"),
        )
        clip = store.get("vid_clean")
        assert clip.source_video_id == "vid_source_0"
        assert (clip.source_start, clip.source_end) == (10.0, 30.0)

    @pytest.mark.asyncio
    async def test_a_clip_that_could_not_be_looked_at_is_refused_not_waved_through(self):
        """Not established and wrong have the same consequence at delivery."""
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            eyes=FakeEyes(error="the cut came back empty"),
            llm=FakeSightLLM(),
        )
        assert agent.curated == []
        assert len(report.refused) == 1
        assert "nothing was seen" in report.results[0].skipped
        assert store.get("vid_clean").viewpoint == "", "a failed look records no verdict"

    @pytest.mark.asyncio
    async def test_a_verdict_reached_without_looking_is_not_a_verdict(self):
        """The gate exists because captions and titles were not enough."""
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(answer_first=True),
        )
        assert agent.curated == []
        assert "without looking at any frames" in report.results[0].skipped

    @pytest.mark.asyncio
    async def test_the_agent_may_look_more_than_once_before_it_answers(self):
        """One span can mislead; deciding how many to sample is the agent's job."""
        store = _store_with("vid_clean")
        eyes = FakeEyes()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=FakeAgent(),
            store=store,
            eyes=eyes,
            llm=FakeSightLLM(looks=3),
        )
        assert len(eyes.looked_at) == 3
        assert [r.nodes for r in report.annotated] == [1]

    @pytest.mark.asyncio
    async def test_a_loop_that_never_answers_refuses_rather_than_guessing(self):
        store = _store_with("vid_clean")
        agent = FakeAgent()
        # Always a tool call, never an answer: the loop runs out of steps.
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(looks=99),
        )
        assert agent.curated == []
        assert len(report.refused) == 1

    @pytest.mark.asyncio
    async def test_no_ffmpeg_refuses_rather_than_silently_passing_everything(self):
        store = _store_with("vid_clean")
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=FakeAgent(),
            store=store,
            eyes=FakeEyes(available=False),
            llm=FakeSightLLM(),
        )
        assert len(report.refused) == 1
        assert "ffmpeg" in report.results[0].skipped

    @pytest.mark.asyncio
    async def test_an_egocentric_clip_passes_and_keeps_its_verdict(self):
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="egocentric"),
        )
        assert agent.curated == ["vid_clean"]
        assert [r.nodes for r in report.annotated] == [1]
        assert report.refused == []
        assert store.get("vid_clean").viewpoint == "egocentric"

    @pytest.mark.asyncio
    async def test_asking_for_exocentric_accepts_a_fixed_camera(self):
        """The gate enforces the request. A tripod is a hit here, not a miss."""
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            wanted_viewpoint="exocentric",
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="exocentric", matches=True, why="a fixed camera"),
        )
        assert agent.curated == ["vid_clean"]
        assert report.refused == []
        assert store.get("vid_clean").viewpoint == "exocentric"

    @pytest.mark.asyncio
    async def test_asking_for_exocentric_refuses_first_person(self):
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            wanted_viewpoint="exocentric",
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="egocentric", matches=False, why="the camera is worn"),
        )
        assert agent.curated == []
        assert len(report.refused) == 1
        assert "asked for exocentric" in report.results[0].skipped

    @pytest.mark.asyncio
    async def test_any_turns_the_gate_off(self):
        store = _store_with("vid_clean")
        agent = FakeAgent()
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_clean")]),
            agent=agent,
            store=store,
            wanted_viewpoint="any",
        )
        assert agent.curated == ["vid_clean"]
        assert report.refused == []

    @pytest.mark.asyncio
    async def test_an_unknown_viewpoint_is_not_a_viewpoint_to_ask_for(self):
        with pytest.raises(ValueError):
            await annotate_clean_collection(
                lake=FakeLake(pages=[_page("vid_clean")]),
                agent=FakeAgent(),
                store=_store_with("vid_clean"),
                wanted_viewpoint="unknown",
            )

    @pytest.mark.asyncio
    async def test_the_report_counts_refusals_separately_from_failures(self):
        store = _store_with("vid_a", "vid_b")
        report = await annotate_clean_collection(
            lake=FakeLake(pages=[_page("vid_a", "vid_b")]),
            agent=FakeAgent(),
            store=store,
            eyes=FakeEyes(),
            llm=FakeSightLLM(viewpoint="exocentric"),
        )
        assert report.as_dict()["refused_wrong_viewpoint"] == 2
        assert report.as_dict()["annotated"] == 0
