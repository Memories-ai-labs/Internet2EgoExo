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
            ['{"spans": [{"start": 10.0, "end": 10.5, "why": "w"}, '
             '{"start": 20.0, "end": 40.0, "why": "w"}]}']
        )
        agent = ClippingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.refine("vid_1", _proposed((10.0, 50.0)), duration_seconds=600.0)
        assert [(s.start, s.end) for s in result.spans] == [(20.0, 40.0)]

    @pytest.mark.asyncio
    async def test_overlapping_spans_are_separated(self):
        """G2-TREE-2. A model that moved a boundary easily produces a hair of overlap."""

        model = _Model(
            ['{"spans": [{"start": 0.0, "end": 30.0, "why": "a"}, '
             '{"start": 25.0, "end": 60.0, "why": "b"}]}']
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

        model = _Model(
            ['{"tool": "look", "arguments": {"frames": 6}}', self.ANSWER % "frames"]
        )
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
            ['{"label": "x", "usable": true, "events": ['
            '{"start": 5.0, "end": 500.0, "label": "outside"}]}']
        )
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=_Eyes())
        result = await agent.label_span("vid_1", 10.0, 40.0)
        assert result.events[0]["span_start"] == 10.0
        assert result.events[0]["span_end"] == 40.0

    @pytest.mark.asyncio
    async def test_a_look_is_clamped_to_the_span_it_is_labelling(self):
        """A label justified by footage outside its own span is a wrong label."""

        model = _Model(
            ['{"tool": "look", "arguments": {"start": 0, "end": 900}}',
             '{"label": "x", "usable": true}']
        )
        eyes = _Eyes()
        agent = AnnotatingAgent(client=_Lake(), llm=model, eyes=eyes)
        await agent.label_span("vid_1", 10.0, 40.0)
        assert eyes.asked == [(10.0, 40.0, 4)]

    @pytest.mark.asyncio
    async def test_a_failed_look_leaves_the_span_unlooked(self):
        model = _Model(
            ['{"tool": "look", "arguments": {}}', self.ANSWER % "frames"]
        )
        agent = AnnotatingAgent(
            client=_Lake(), llm=model, eyes=_Eyes(error="409 not ready")
        )
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
