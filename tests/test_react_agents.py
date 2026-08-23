"""The two ReAct agents: clipping decides boundaries, annotating writes labels.

Both were single-shot calls over caption text before this, and both were
therefore making statements about *wording*. The tests below care most about the
rules that are not the model's to break — a boundary outside the video, a hand
assignment with nothing behind it — because those are enforced in code rather
than asked for in a prompt.
"""

from __future__ import annotations

from typing import Any

import pytest

from video_searching_agent.agent.annotating_agent import AnnotatingAgent
from video_searching_agent.agent.clipping_agent import ClippingAgent
from video_searching_agent.agent.eyes import Frames


class _Model:
    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)

    def new_conversation(self, text: str) -> list[dict[str, Any]]:
        return [{"role": "user", "content": text}]

    def append_user_text(self, messages, text):
        messages.append({"role": "user", "content": text})

    def append_user_images(self, messages, text, images, **_):
        messages.append({"role": "user", "content": text})

    def append_model_response(self, messages, response):
        messages.append({"role": "assistant", "content": response["text"]})

    async def create_message_async(self, messages, **_):
        return {"text": self.replies.pop(0) if self.replies else "{}"}

    def get_text_response(self, response):
        return response["text"]


class _Eyes:
    """Frames on demand, recording what was asked for."""

    def __init__(self, images: list[bytes] | None = None, error: str | None = None) -> None:
        self.images = images if images is not None else [b"jpeg"]
        self.error = error
        self.asked: list[tuple[float, float, int]] = []
        self.looks = 0
        self.spent_usd = 0.0

    async def look(self, video_id: str, start: float, end: float, count: int = 4) -> Frames:
        self.asked.append((start, end, count))
        self.looks += 1
        return Frames(
            video_id=video_id,
            start=start,
            end=end,
            images=[] if self.error else self.images,
            width=854,
            height=480,
            error=self.error,
            cost_usd=0.005,
        )


class _Lake:
    def __init__(self, segments: list[dict[str, Any]] | None = None) -> None:
        self.segments = segments or [{"start": 0.0, "end": 10.0, "text": "a hand turns a wrench"}]

    async def get_caption(self, video_id, start=None, end=None):
        return {"segments": self.segments}


def _proposed(*spans):
    return [
        {"span_start": start, "span_end": end, "hier_level": "action", "evidence": ["hand:hands"]}
        for start, end in spans
    ]


class TestClipping:
    @pytest.mark.asyncio
    async def test_it_looks_and_then_moves_a_boundary(self):
        model = _Model(
            [
                '{"thought": "check where it starts", "tool": "look", '
                '"arguments": {"start": 10, "end": 40}}',
                '{"spans": [{"start": 15.0, "end": 48.0, "why": "the work starts at 15", '
                '"changed": "moved"}], "notes": "the first five seconds are a title"}',
            ]
        )
        eyes = _Eyes()
        agent = ClippingAgent(client=_Lake(), llm=model, eyes=eyes)
        result = await agent.refine("vid_1", _proposed((10.0, 50.0)), duration_seconds=600.0)

        assert eyes.asked == [(10.0, 40.0, 4)]
        assert [(s.start, s.end) for s in result.spans] == [(15.0, 48.0)]
        assert result.spans[0].changed == "moved"
        assert result.spans[0].examined is True, "it looked at that span"
        assert result.notes.startswith("the first five seconds")
        assert result.fell_back is False

    @pytest.mark.asyncio
    async def test_a_span_beyond_the_video_is_clamped(self):
        model = _Model(['{"spans": [{"start": 10.0, "end": 9999.0, "why": "w"}]}'])
        agent = ClippingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.refine("vid_1", _proposed((10.0, 50.0)), duration_seconds=100.0)
        assert result.spans[0].end == 100.0

    @pytest.mark.asyncio
    async def test_a_span_below_the_action_floor_is_dropped(self):
        model = _Model(
            [
                '{"spans": [{"start": 10.0, "end": 10.5, "why": "w"}, '
                '{"start": 20.0, "end": 40.0, "why": "w"}]}'
            ]
        )
        agent = ClippingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.refine("vid_1", _proposed((10.0, 50.0)), duration_seconds=600.0)
        assert [(s.start, s.end) for s in result.spans] == [(20.0, 40.0)]

    @pytest.mark.asyncio
    async def test_overlapping_spans_are_separated(self):
        """G2-TREE-2. A model that moved a boundary easily produces a hair of overlap."""

        model = _Model(
            [
                '{"spans": [{"start": 0.0, "end": 30.0, "why": "a"}, '
                '{"start": 25.0, "end": 60.0, "why": "b"}]}'
            ]
        )
        agent = ClippingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.refine("vid_1", _proposed((0.0, 60.0)), duration_seconds=600.0)
        assert [(s.start, s.end) for s in result.spans] == [(0.0, 30.0), (30.0, 60.0)]

    @pytest.mark.asyncio
    async def test_a_loop_that_does_not_converge_leaves_the_proposal_alone(self):
        """The honest outcome is the skeleton, not an empty set."""

        model = _Model(["not json at all"])
        agent = ClippingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        proposed = _proposed((10.0, 50.0), (60.0, 90.0))
        result = await agent.refine("vid_1", proposed, duration_seconds=600.0)

        assert result.fell_back is True
        assert [(s.start, s.end) for s in result.spans] == [(10.0, 50.0), (60.0, 90.0)]
        assert result.error

    @pytest.mark.asyncio
    async def test_no_model_means_the_proposal_stands(self):
        agent = ClippingAgent(client=_Lake(), llm=False, eyes=_Eyes())
        result = await agent.refine("vid_1", _proposed((10.0, 50.0)))
        assert result.fell_back is True
        assert len(result.spans) == 1

    @pytest.mark.asyncio
    async def test_nothing_proposed_is_not_an_error(self):
        agent = ClippingAgent(client=_Lake(), llm=_Model([]), eyes=_Eyes())
        result = await agent.refine("vid_1", [])
        assert result.spans == []
        assert result.error is None


class TestAnnotating:
    ANSWER = (
        '{"label": "insert-cam-lock", "narration": "The cam lock is turned home.", '
        '"usable": true, "hands_visible": true, "left_hand": "steadies the panel", '
        '"right_hand": "turns the cam lock", "hand_evidence": "%s", '
        '"objects": ["cam lock", "panel"], '
        '"events": [{"start": 12.0, "end": 15.0, "label": "dropped-screw"}]}'
    )

    @pytest.mark.asyncio
    async def test_looking_recovers_the_hand_assignment(self):
        """The whole point. Captions that do not name a hand used to mean both
        fields null; the frames often show it."""

        model = _Model(['{"tool": "look", "arguments": {"frames": 6}}', self.ANSWER % "frames"])
        eyes = _Eyes()
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=eyes)
        result = await agent.label_span("vid_1", 10.0, 40.0)

        assert result.looked is True
        assert result.left_hand == "steadies the panel"
        assert result.right_hand == "turns the cam lock"
        assert result.hand_evidence == "frames"
        assert result.objects == ["cam lock", "panel"]

    @pytest.mark.asyncio
    async def test_a_hand_claimed_from_frames_without_looking_is_discarded(self):
        """A hand is never invented, and "I saw it" has to mean a look happened."""

        model = _Model([self.ANSWER % "frames"])
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.label_span("vid_1", 10.0, 40.0)

        assert result.looked is False
        assert result.left_hand is None
        assert result.right_hand is None
        assert result.hand_evidence is None
        assert result.label == "insert-cam-lock", "the rest of the answer survives"

    @pytest.mark.asyncio
    async def test_an_unsupported_evidence_value_drops_the_hands(self):
        model = _Model([self.ANSWER % "obvious"])
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.label_span("vid_1", 10.0, 40.0)
        assert (result.left_hand, result.right_hand, result.hand_evidence) == (None, None, None)

    @pytest.mark.asyncio
    async def test_captions_are_a_valid_way_of_knowing(self):
        model = _Model([self.ANSWER % "captions"])
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.label_span("vid_1", 10.0, 40.0)
        assert result.hand_evidence == "captions"
        assert result.left_hand == "steadies the panel"

    @pytest.mark.asyncio
    async def test_events_are_clamped_inside_their_span(self):
        model = _Model(
            [
                '{"label": "x", "usable": true, "events": ['
                '{"start": 5.0, "end": 500.0, "label": "outside"}]}'
            ]
        )
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.label_span("vid_1", 10.0, 40.0)
        assert result.events[0]["span_start"] == 10.0
        assert result.events[0]["span_end"] == 40.0

    @pytest.mark.asyncio
    async def test_a_look_is_clamped_to_the_span_it_is_labelling(self):
        """A label justified by footage outside its own span is a wrong label."""

        model = _Model(
            [
                '{"tool": "look", "arguments": {"start": 0, "end": 900}}',
                '{"label": "x", "usable": true}',
            ]
        )
        eyes = _Eyes()
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=eyes)
        await agent.label_span("vid_1", 10.0, 40.0)
        assert eyes.asked == [(10.0, 40.0, 4)]

    @pytest.mark.asyncio
    async def test_a_failed_look_leaves_the_span_unlooked(self):
        model = _Model(['{"tool": "look", "arguments": {}}', self.ANSWER % "frames"])
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes(error="409 not ready"))
        result = await agent.label_span("vid_1", 10.0, 40.0)
        assert result.looked is False
        assert result.left_hand is None, "a look that failed is not evidence"

    @pytest.mark.asyncio
    async def test_a_loop_that_does_not_converge_leaves_the_span_unlabelled(self):
        model = _Model(["nonsense"])
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.label_span("vid_1", 10.0, 40.0)
        assert result.label is None
        assert result.error

    @pytest.mark.asyncio
    async def test_the_task_and_the_used_labels_reach_the_prompt(self):
        seen: list[Any] = []

        class Watching(_Model):
            async def create_message_async(self, messages, **_):
                seen.append(messages[0]["content"])
                return {"text": '{"label": "x", "usable": true}'}

        agent = AnnotatingAgent(client=_Lake(), llm=Watching([]), eyes=_Eyes())
        await agent.label_span(
            "vid_1", 10.0, 40.0, task_label="assemble-wardrobe", used_labels=["read-manual"]
        )
        assert "assemble-wardrobe" in seen[0]
        assert "read-manual" in seen[0]


class TestTheLookingPathIsActuallyReached:
    """Wiring bugs that only appear when looking is switched on.

    Looking is off in tests by default (conftest pins it), which is right — it
    spends money and touches the network. The cost of that is a whole code path
    nothing exercises, and it bit immediately: the annotation agent's wiring
    referenced `self._llm` on a class whose field is `_gemini`, and a field it
    never declared. Both crashed on the first real run and no test noticed.
    """

    @pytest.mark.asyncio
    async def test_annotation_routes_spans_through_the_looking_loop(self, looking):
        from video_searching_agent.agent.annotation_agent import AnnotationAgent
        from video_searching_agent.agent.cleaning_agent import Segment

        answer = (
            '{"label": "screw-bracket-to-panel", "narration": "n", "usable": true, '
            '"hands_visible": true, "left_hand": "holds the bracket", '
            '"right_hand": "turns the screwdriver", "hand_evidence": "frames", '
            '"objects": ["bracket"]}'
        )
        model = _Model(['{"tool": "look", "arguments": {}}', answer])
        agent = AnnotationAgent(client=_Lake(), llm=model)
        agent._annotating = __import__(
            "video_searching_agent.agent.annotating_agent", fromlist=["AnnotatingAgent"]
        ).AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())

        segments = [
            Segment(
                segment_id="t1.a1",
                parent_segment_id="t1",
                hier_level="action",
                span_start=10.0,
                span_end=40.0,
                hands_visible=True,
                source_text="a hand does something",
            )
        ]
        run = await agent.annotate_video("vid_1", segments, write_back=False)

        labelled = [a for a in run.annotations if a.hier_level == "action"]
        assert labelled, "the looking path produced nothing"
        assert labelled[0].label == "screw-bracket-to-panel"
        assert labelled[0].left_hand == "holds the bracket"
        assert labelled[0].right_hand == "turns the screwdriver"
        # Where the assignment came from is part of the record.
        assert "hand_evidence/frames" in labelled[0].tags
        assert run.look_cost_usd > 0

    @pytest.mark.asyncio
    async def test_a_loop_that_fails_falls_back_to_the_caption_path(self, looking):
        """An unlabelled span is worse than one labelled from words alone."""

        from video_searching_agent.agent.annotating_agent import AnnotatingAgent
        from video_searching_agent.agent.annotation_agent import AnnotationAgent
        from video_searching_agent.agent.cleaning_agent import Segment

        caption_answer = (
            '{"label": "from-captions", "narration": "n", "usable": true, "hands_visible": true}'
        )
        # The looking loop fails; the caption-only call after it succeeds.
        agent = AnnotationAgent(client=_Lake(), llm=_Model([caption_answer, caption_answer]))
        agent._annotating = AnnotatingAgent(client=_Lake(), llm=_Model(["not json"]), eyes=_Eyes())

        run = await agent.annotate_video(
            "vid_1",
            [
                Segment(
                    segment_id="t1.a1",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=10.0,
                    span_end=40.0,
                    hands_visible=True,
                    source_text="a hand does something",
                )
            ],
            write_back=False,
        )
        labelled = [a for a in run.annotations if a.hier_level == "action"]
        assert labelled and labelled[0].label == "from-captions"

    @pytest.mark.asyncio
    async def test_an_agent_built_without_a_model_still_looks(self, looking, monkeypatch):
        """The gate must not depend on whether anybody touched the property yet.

        `CurationAgent` builds `AnnotationAgent(client=...)` and injects no
        model, so `_gemini` is None until the lazy `gemini` property is first
        read. The gate tested `self._gemini not in (None, False)`, so on that
        path looking was silently off — with LOOK_AT_FRAMES=1 set — and the
        caption fallback returned zero annotations for anchors carrying no
        caption text, which is every anchor the pixel path produces.

        Every existing test here injects `llm=` and `_annotating`, which is
        exactly why none of them caught it.
        """
        from video_searching_agent.agent import annotation_agent as module
        from video_searching_agent.agent.annotation_agent import AnnotationAgent
        from video_searching_agent.agent.cleaning_agent import Segment

        answer = (
            '{"label": "seen-it", "narration": "n", "usable": true, '
            '"hands_visible": true, "left_hand": "holds", "hand_evidence": "frames"}'
        )
        model = _Model(['{"tool": "look", "arguments": {}}', answer, answer])
        monkeypatch.setattr(module, "get_llm_client", lambda *a, **k: model)

        agent = AnnotationAgent(client=_Lake())  # no llm, as CurationAgent does
        looker = __import__(
            "video_searching_agent.agent.annotating_agent", fromlist=["AnnotatingAgent"]
        ).AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        monkeypatch.setattr(agent, "_looker", lambda: looker)

        run = await agent.annotate_video(
            "vid_1",
            [
                Segment(
                    segment_id="t1.a1",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=0.0,
                    span_end=6.8,
                    # No source_text: a pixel-derived anchor carries none, so
                    # the caption fallback has nothing and looking is the only
                    # path that can produce anything at all.
                    source_text="",
                )
            ],
            write_back=False,
        )
        labelled = [a for a in run.annotations if a.hier_level == "action"]
        assert labelled, f"looking never ran; errors: {run.errors}"
        assert labelled[0].label == "seen-it"

    @pytest.mark.asyncio
    async def test_a_span_that_produced_nothing_says_why(self, monkeypatch):
        """Zero annotations and zero errors reads as "the footage was empty".

        It usually means the looking path was off and the anchor had no caption
        text. The pass costs money either way, so it has to explain itself.
        """
        from video_searching_agent.agent.annotation_agent import AnnotationAgent
        from video_searching_agent.agent.cleaning_agent import Segment

        agent = AnnotationAgent(client=_Lake(), llm=_Model([]))
        run = await agent.annotate_video(
            "vid_1",
            [
                Segment(
                    segment_id="t1.a1",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=0.0,
                    span_end=6.8,
                    source_text="",
                )
            ],
            write_back=False,
        )
        assert run.annotations == []
        assert run.errors, "a paid pass that produced nothing said nothing about it"
        assert "no annotation" in run.errors[0]

    @pytest.mark.asyncio
    async def test_looking_off_never_builds_the_loop(self):
        """The default path must not touch the network or the field.

        No `looking` fixture here, so the conftest's off setting applies.
        """
        from video_searching_agent.agent.annotation_agent import AnnotationAgent
        from video_searching_agent.agent.cleaning_agent import Segment

        agent = AnnotationAgent(
            client=_Lake(),
            llm=_Model(['{"label": "x", "narration": "n", "usable": true, "hands_visible": true}']),
        )
        run = await agent.annotate_video(
            "vid_1",
            [
                Segment(
                    segment_id="t1.a1",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=10.0,
                    span_end=40.0,
                    hands_visible=True,
                    source_text="a hand does something",
                )
            ],
            write_back=False,
        )
        assert agent._annotating is None, "no loop should have been built"
        assert run.look_cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_cleaning_refines_anchors_only_with_a_model_it_was_given(self, looking):
        """Refinement must never resolve a model of its own — doing so made an
        expensive network round trip a hidden side effect of clean()."""

        from video_searching_agent.agent.cleaning_agent import CleaningAgent

        agent = CleaningAgent(client=_Lake(), llm=None)
        assert agent._llm is None
        # With no model handed in, the refinement path is not entered at all,
        # which is what keeps a bare agent offline.
        verdict = type("V", (), {"segments": [], "errors": [], "trace": None})()
        refined = await agent._refine_anchors("vid_1", verdict, duration=100.0)
        assert refined == []


class TestTheVisualSearchTool:
    """Both looking agents can now ask the video's own per-second index.

    They used to reach only for caption text and extracted frames. The index is
    a third instrument and a cheaper one than looking: it finds the seconds
    worth looking at, so a $0.005 cut can be spent where it will change the
    answer instead of on a guess.
    """

    @staticmethod
    def _lake(rows):
        class Lake:
            def __init__(self):
                self.bodies = []

            async def ensure_collection(self):
                return "col_test"

            async def _request(self, method, path, json):
                self.bodies.append(json)
                return {"results": rows}

        return Lake()

    @staticmethod
    def _row(start, snippet, score=0.4, video_id="vid_a"):
        return {
            "video_id": video_id,
            "start": float(start),
            "end": float(start) + 1.0,
            "score": score,
            "snippet": snippet,
            "thumbnail_url": "",
        }

    @pytest.mark.asyncio
    async def test_the_clipping_agent_can_locate_the_action(self):
        from video_searching_agent.agent.clipping_agent import ClippingAgent

        lake = self._lake(
            [
                self._row(40, "two hands turn a bolt with an allen key"),
                self._row(41, "two hands turn a bolt with an allen key"),
                self._row(300, "an empty workbench"),
            ]
        )
        agent = ClippingAgent(client=lake, llm=object())
        tools = {tool.name: tool for tool in agent._tools("vid_a", _clipping_result())}

        assert "find_frames" in tools
        result = await tools["find_frames"].run({"query": "hands turning a bolt"})

        # Scoped the only way the endpoint honours.
        assert lake.bodies[0]["filter"] == {"video_ids": ["vid_a"]}
        assert lake.bodies[0]["targets"] == ["frame_embedding"]
        # Runs, so the agent sees a stretch rather than three dots.
        assert "run 40s-42s" in result.observation
        assert "allen key" in result.observation
        assert result.cost_usd == pytest.approx(0.008)

    @pytest.mark.asyncio
    async def test_the_tool_tells_the_agent_the_ranking_is_not_a_detection(self):
        """The scores overlap with gibberish, so the observation has to say so —
        otherwise the agent reads a rank as a finding."""

        from video_searching_agent.agent.clipping_agent import ClippingAgent

        lake = self._lake([self._row(5, "a hand grips a wrench", score=0.99)])
        agent = ClippingAgent(client=lake, llm=object())
        tools = {tool.name: tool for tool in agent._tools("vid_a", _clipping_result())}
        result = await tools["find_frames"].run({"query": "hands"})

        assert "never that it is" in result.observation or "not a detection" in result.observation

    @pytest.mark.asyncio
    async def test_the_annotating_agent_only_sees_its_own_span(self):
        """A label justified by footage outside its span is a wrong label, and
        the search has no span scope — so the clamping has to happen here."""

        from video_searching_agent.agent.annotating_agent import AnnotatingAgent

        lake = self._lake(
            [
                self._row(45, "the left hand steadies the panel"),
                self._row(600, "somebody carries a box across the room"),
            ]
        )
        agent = AnnotatingAgent(client=lake, llm=object())
        tools = {tool.name: tool for tool in agent._tools("vid_a", 40.0, 60.0, _span_label())}
        result = await tools["find_frames"].run({"query": "which hand acts"})

        assert "steadies the panel" in result.observation
        assert "carries a box" not in result.observation

    @pytest.mark.asyncio
    async def test_a_span_with_no_match_is_not_reported_as_a_video_with_no_match(self):
        from video_searching_agent.agent.annotating_agent import AnnotatingAgent

        lake = self._lake([self._row(600, "somebody carries a box")])
        agent = AnnotatingAgent(client=lake, llm=object())
        tools = {tool.name: tool for tool in agent._tools("vid_a", 40.0, 60.0, _span_label())}
        result = await tools["find_frames"].run({"query": "hands"})

        assert "found nothing" in result.observation
        assert "elsewhere in the video" in result.observation
        assert "says nothing about this span" in result.observation

    @pytest.mark.asyncio
    async def test_an_empty_query_is_refused_before_it_is_charged_for(self):
        from video_searching_agent.agent.clipping_agent import ClippingAgent

        lake = self._lake([])
        agent = ClippingAgent(client=lake, llm=object())
        tools = {tool.name: tool for tool in agent._tools("vid_a", _clipping_result())}
        result = await tools["find_frames"].run({})

        assert lake.bodies == []
        assert result.cost_usd in (0.0, None)
        assert "needs a query" in result.observation


def _clipping_result():
    from video_searching_agent.agent.clipping_agent import ClippingResult

    return ClippingResult(video_id="vid_a")


def _span_label():
    from video_searching_agent.agent.annotating_agent import SpanLabel

    return SpanLabel(start=40.0, end=60.0)
