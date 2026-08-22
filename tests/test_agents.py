"""Tests for the specialized agents: cleaning, annotation, curation.

The agents only ever talk to the Datalake and the model through their clients,
so both are stubbed here and every assertion is about the judgement the agent
made, not about transport.
"""

from typing import Any

import pytest

from video_searching_agent.agent.annotation_agent import AnnotationAgent
from video_searching_agent.agent.cleaning_agent import (
    TAG_CLEAN,
    TAG_NO_HANDS,
    TAG_REJECTED,
    CleaningAgent,
)
from video_searching_agent.agent.curation_agent import CurationAgent
from video_searching_agent.api.memories_datalake_client import MemoriesDatalakeError
from video_searching_agent.curation.viewpoint import Viewpoint
from video_searching_agent.models.dataset import DatasetClip, DatasetManifest


class _FakeDatalake:
    """A Datalake that returns what the test wants and records the writes."""

    def __init__(
        self,
        caption: str | None = None,
        segments: list[dict[str, Any]] | None = None,
        transcription: str | None = None,
        summary: str | None = None,
        videos: list[dict[str, Any]] | None = None,
        search_results: list[dict[str, Any]] | None = None,
        moments: dict[str, dict[str, Any]] | None = None,
        fail_update: bool = False,
        duration_seconds: float | None = 600.0,
    ) -> None:
        # A duration by default, because the real client has one and the
        # windowed caption read depends on it. A fake that reported none made
        # the untimed fallback look like the normal path.
        self._duration = duration_seconds
        self._caption = caption
        self._segments = segments or []
        self._transcription = transcription
        self._summary = summary
        self._videos = videos or []
        self._search = search_results or []
        self._moments = moments or {}
        self._fail_update = fail_update
        self.updates: list[dict[str, Any]] = []

    async def get_video(self, video_id: str) -> dict[str, Any]:
        """Mirror the real endpoint, which reports the duration."""

        return {"video_id": video_id, "duration_seconds": self._duration}

    async def get_caption(
        self,
        video_id: str,
        start: float | None = None,
        end: float | None = None,
    ) -> dict[str, Any]:
        """Mirror the real endpoint: timings only when a window is asked for.

        A whole-video read comes back as one aggregated string with no
        timestamps; a `[start, end]` read comes back as timed segments. Getting
        this wrong in the fake is what hid the bug that anchors need a window.
        """
        if self._caption is None and not self._segments:
            raise MemoriesDatalakeError("caption not ready")
        if start is None and end is None:
            return {"caption": self._caption}
        return {"segments": self._segments}

    async def get_transcription(self, video_id: str) -> dict[str, Any]:
        return {"transcription": self._transcription}

    async def get_summary(self, video_id: str) -> dict[str, Any]:
        return {"summary": self._summary}

    async def list_videos(self, **kwargs: Any) -> dict[str, Any]:
        return {"videos": self._videos}

    async def search(self, query: str, top_k: int | None = None) -> dict[str, Any]:
        return {"results": self._search}

    async def get_moment(self, ref: str, expand: list[str] | None = None) -> dict[str, Any]:
        return self._moments[ref]

    async def update_video(
        self,
        video_id: str,
        tags: list[str] | None = None,
        custom: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        if self._fail_update:
            raise MemoriesDatalakeError("write refused")
        self.updates.append({"video_id": video_id, "tags": tags, "custom": custom})
        return {"video_id": video_id}


class _FakeGemini:
    """Returns canned JSON, in order, and counts the calls."""

    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.prompts: list[str] = []

    async def create_message_async(
        self, messages: list[dict[str, str]], system: str | None = None
    ) -> str:
        self.prompts.append(messages[0]["content"])
        if not self._replies:
            raise AssertionError("no reply left for this call")
        return self._replies.pop(0)

    @staticmethod
    def get_text_response(response: Any) -> str:
        return str(response)


def _segments(*spans: tuple[float, float, str]) -> list[dict[str, Any]]:
    return [{"start": start, "end": end, "text": text} for start, end, text in spans]


class TestTheLookBeforeTheDownload:
    """The layer that looks at frames, not at words about the footage."""

    @staticmethod
    def _sighted(text: str) -> Any:
        """A cleaning agent whose model answers with `text`."""

        class Client:
            def new_visual_conversation(self, prompt: str, images: list[bytes]) -> list[dict]:
                return [{"role": "user", "content": prompt}]

            async def create_message_async(self, messages: list[dict], **_: object) -> dict:
                return {"text": text}

            def get_text_response(self, response: dict) -> str:
                return response["text"]

            def get_cost_usd(self, response: dict) -> float | None:
                return 0.002

        return CleaningAgent(llm=Client())

    @pytest.mark.asyncio
    async def test_frames_that_show_the_wrong_viewpoint_stop_the_download(self, monkeypatch):
        """This is the case metadata cannot catch: the title says POV, the
        frames say tripod."""

        import video_searching_agent.curation.frame_viewpoint as sight

        async def frames(urls, limit=4):
            return [b"x" * 3000]

        monkeypatch.setattr(sight, "fetch_frames", frames)
        agent = self._sighted(
            '{"viewpoint": "exocentric", "hands_visible": true, "confidence": 0.96,'
            ' "why": "a presenter faces the camera"}'
        )
        info = {"title": "POV cooking", "url": "https://www.youtube.com/watch?v=abc"}
        verdict = agent.screen(info, wanted_viewpoint=Viewpoint.EGOCENTRIC)
        assert verdict.accepted is True  # the words gave nothing away

        verdict = await agent.look(
            verdict, info, wanted_viewpoint=Viewpoint.EGOCENTRIC, mode="frames"
        )
        assert verdict.accepted is False
        assert "frames show exocentric" in verdict.reasons[0]
        assert any(check.check_id == "PRE-SIGHT" for check in verdict.checks)

    @pytest.mark.asyncio
    async def test_frames_that_agree_raise_confidence_without_inventing_it(self, monkeypatch):
        import video_searching_agent.curation.frame_viewpoint as sight

        async def frames(urls, limit=4):
            return [b"x" * 3000]

        monkeypatch.setattr(sight, "fetch_frames", frames)
        agent = self._sighted(
            '{"viewpoint": "egocentric", "hands_visible": true, "confidence": 0.9,'
            ' "why": "own hands from below"}'
        )
        info = {"title": "cooking", "url": "https://www.youtube.com/watch?v=abc"}
        verdict = await agent.look(
            agent.screen(info, wanted_viewpoint=Viewpoint.EGOCENTRIC),
            info,
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
            mode="frames",
        )
        assert verdict.accepted is True
        assert verdict.viewpoint == Viewpoint.EGOCENTRIC
        assert verdict.viewpoint_confidence == pytest.approx(0.9)
        assert verdict.sight is not None and verdict.sight.method == "frames"

    @pytest.mark.asyncio
    async def test_a_look_that_fails_leaves_the_verdict_alone(self, monkeypatch):
        """A rate limit must not become a rejection."""

        import video_searching_agent.curation.frame_viewpoint as sight

        async def no_frames(urls, limit=4):
            return []

        monkeypatch.setattr(sight, "fetch_frames", no_frames)
        agent = self._sighted("{}")
        info = {"title": "cooking", "url": "https://www.youtube.com/watch?v=abc"}
        before = agent.screen(info, wanted_viewpoint=Viewpoint.EGOCENTRIC)
        after = await agent.look(
            before, info, wanted_viewpoint=Viewpoint.EGOCENTRIC, mode="frames"
        )
        assert after.accepted is True
        assert any("frame check did not run" in note for note in after.notes)

    @pytest.mark.asyncio
    async def test_looking_can_be_turned_off(self):
        agent = CleaningAgent(llm=False)
        info = {"title": "cooking", "url": "https://www.youtube.com/watch?v=abc"}
        verdict = await agent.look(
            agent.screen(info), info, wanted_viewpoint=Viewpoint.EGOCENTRIC, mode="off"
        )
        assert verdict.sight is None


class TestCleaningAgentScreening:
    """The pre-download filter, which spends nothing."""

    def test_short_candidate_is_rejected_before_download(self):
        verdict = CleaningAgent().screen(
            {"title": "POV cooking", "duration": 20}, min_duration_seconds=60
        )
        assert verdict.accepted is False
        assert "below the 60s minimum" in verdict.reasons[0]

    def test_contradicted_viewpoint_is_rejected(self):
        verdict = CleaningAgent().screen(
            {"title": "Knife skills demo, third-person view from a fixed camera"},
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
        )
        assert verdict.viewpoint == Viewpoint.EXOCENTRIC
        assert verdict.accepted is False

    def test_silent_metadata_is_not_a_rejection(self):
        # The frame check gets the deciding vote; metadata silence must not veto.
        verdict = CleaningAgent().screen(
            {"title": "Making pasta", "duration": 600},
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
            min_duration_seconds=60,
        )
        assert verdict.viewpoint == Viewpoint.UNKNOWN
        assert verdict.accepted is True

    def test_licence_is_recorded_but_only_blocks_when_asked(self):
        candidate = {"title": "first person welding", "duration": 300, "license": None}
        carried = CleaningAgent().screen(candidate)
        assert carried.accepted is True
        assert carried.commercial_use_ok is False

        strict = CleaningAgent().screen(candidate, require_commercial_use=True)
        assert strict.accepted is False

    def test_creative_commons_passes_gate_zero(self):
        verdict = CleaningAgent().screen(
            {"title": "ego cooking", "license": "Creative Commons"},
            require_commercial_use=True,
        )
        assert verdict.commercial_use_ok is True
        assert verdict.accepted is True


class TestAgenticClipping:
    """Where the boundaries are — anchors only, never files."""

    def test_the_same_action_continuing_merges_into_one_anchor(self):
        segments = _segments(
            (0.0, 4.0, "The right hand slices an onion"),
            (4.0, 9.0, "The right hand slices the last of it"),
        )
        tree = CleaningAgent().propose_segments(segments)
        actions = [s for s in tree if s.hier_level == "action"]
        assert len(actions) == 1
        assert (actions[0].span_start, actions[0].span_end) == (0.0, 9.0)

    def test_a_change_of_action_splits_even_with_no_pause(self):
        # Chopping then stirring is two actions. Merging them on the strength of
        # "no gap" produces one shapeless anchor that teaches nothing.
        segments = _segments(
            (0.0, 40.0, "The right hand chops an onion on the board"),
            (40.0, 90.0, "The right hand stirs the pan with a wooden spoon"),
        )
        tree = CleaningAgent().propose_segments(segments)
        actions = [s for s in tree if s.hier_level == "action"]
        assert [(a.span_start, a.span_end) for a in actions] == [(0.0, 40.0), (40.0, 90.0)]

    def test_a_segment_with_no_verb_does_not_split_the_run(self):
        # Only a real change of action splits; silence about the verb is not one.
        segments = _segments(
            (0.0, 5.0, "The right hand slices an onion"),
            (5.0, 10.0, "Both hands are in frame over the board"),
            (10.0, 16.0, "The right hand slices the carrot"),
        )
        tree = CleaningAgent().propose_segments(segments)
        actions = [s for s in tree if s.hier_level == "action"]
        assert len(actions) == 1

    def test_idle_segment_breaks_the_run(self):
        segments = _segments(
            (0.0, 5.0, "hands assemble the bracket"),
            (5.0, 12.0, "the workbench is empty, nothing happens"),
            (12.0, 20.0, "the hands tighten the last screw"),
        )
        tree = CleaningAgent().propose_segments(segments)
        actions = [s for s in tree if s.hier_level == "action"]
        assert [(a.span_start, a.span_end) for a in actions] == [(0.0, 5.0), (12.0, 20.0)]

    def test_a_long_gap_splits_rather_than_merges(self):
        segments = _segments(
            (0.0, 4.0, "the hand solders a joint"),
            (30.0, 36.0, "the hand solders the next joint"),
        )
        tree = CleaningAgent().propose_segments(segments)
        assert len([s for s in tree if s.hier_level == "action"]) == 2

    def test_spans_below_the_floor_are_dropped_and_ids_stay_contiguous(self):
        segments = _segments(
            (0.0, 0.5, "a hand appears"),
            (10.0, 20.0, "both hands knead the dough"),
        )
        tree = CleaningAgent().propose_segments(segments)
        actions = [s for s in tree if s.hier_level == "action"]
        assert len(actions) == 1
        assert actions[0].segment_id == "t1.a1"

    def test_task_span_covers_the_actions_not_the_whole_video(self):
        segments = _segments(
            (0.0, 8.0, "a title card with text on a black background"),
            (10.0, 30.0, "the hands wire the connector"),
        )
        tree = CleaningAgent().propose_segments(segments, require_hands=True)
        task = tree[0]
        assert task.hier_level == "task"
        assert task.parent_segment_id is None
        assert task.span_start == 10.0
        assert task.span_end == 30.0

    def test_a_very_long_run_is_cut_at_segment_boundaries(self):
        # 10 minutes of uninterrupted work is not one action.
        segments = _segments(
            *[
                (float(i * 60), float((i + 1) * 60), "the right hand seats a connector")
                for i in range(10)
            ]
        )
        tree = CleaningAgent().propose_segments(segments)
        actions = [s for s in tree if s.hier_level == "action"]
        assert len(actions) > 1
        assert all(a.duration <= 120.0 for a in actions)
        # Cuts land on boundaries the index gave us, not invented ones.
        boundaries = {0.0} | {float((i + 1) * 60) for i in range(10)}
        assert all(a.span_start in boundaries and a.span_end in boundaries for a in actions)

    def test_no_timed_segments_yields_no_anchors(self):
        assert CleaningAgent().propose_segments([{"text": "hands"}]) == []

    def test_anchors_never_carry_a_clip_file(self):
        tree = CleaningAgent().propose_segments(_segments((0.0, 12.0, "the hands wipe the bench")))
        assert all("clip_file" not in segment.as_dict() for segment in tree)

    def test_hands_not_required_still_anchors_activity(self):
        tree = CleaningAgent().propose_segments(
            _segments((0.0, 30.0, "a cyclist rides along a canal")),
            require_hands=False,
        )
        assert len([s for s in tree if s.hier_level == "action"]) == 1


class TestCleaningAgentVerdicts:
    """The post-index filter, which judges the footage."""

    @pytest.mark.asyncio
    async def test_hands_and_viewpoint_accepted_and_tagged(self):
        datalake = _FakeDatalake(
            caption="A first-person view as the left hand holds an onion and the "
            "right hand slices it on a cutting board.",
            segments=_segments(
                (0.0, 6.0, "the left hand holds the onion"),
                (6.0, 14.0, "the right hand slices it"),
            ),
        )
        agent = CleaningAgent(client=datalake)
        verdict = await agent.clean(
            "vid_1",
            title="POV cooking, GoPro chest mount",
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
            media={
                "source_url": "https://example.com/v",
                "uploader": "chef",
                "license": "Creative Commons",
                "width": 1920,
                "height": 1080,
                "fps": 60,
                "duration_seconds": 20,
                "container": "mp4",
            },
        )
        assert verdict.accepted is True
        assert TAG_CLEAN in verdict.tags_written
        assert verdict.quality is not None
        assert verdict.quality.commercial_use_ok is True
        # Holding and slicing are different actions, so they anchor separately.
        assert len(verdict.action_segments) == 2
        assert datalake.updates[0]["custom"]["segments"]

    @pytest.mark.asyncio
    async def test_no_hands_is_rejected_and_says_why(self):
        datalake = _FakeDatalake(
            caption="A wide shot of a kitchen. Steam rises from a pot on the stove.",
            segments=_segments((0.0, 10.0, "steam rises from a pot")),
        )
        verdict = await CleaningAgent(client=datalake).clean("vid_2")
        assert verdict.accepted is False
        assert verdict.rejection_reason == "no hands visible in the captions"
        assert TAG_REJECTED in verdict.tags_written
        assert TAG_NO_HANDS in verdict.tags_written

    @pytest.mark.asyncio
    async def test_screen_recording_is_rejected_however_well_it_matches(self):
        datalake = _FakeDatalake(
            caption="A screen recording of a spreadsheet; the cursor moves between cells."
        )
        verdict = await CleaningAgent(client=datalake).clean("vid_3")
        assert verdict.accepted is False
        assert "not real-world footage" in (verdict.rejection_reason or "")

    @pytest.mark.asyncio
    async def test_missing_captions_abstain_rather_than_pass(self):
        verdict = await CleaningAgent(client=_FakeDatalake()).clean("vid_4")
        assert verdict.accepted is False
        assert "no captions" in (verdict.rejection_reason or "")
        assert any("caption unavailable" in error for error in verdict.errors)

    @pytest.mark.asyncio
    async def test_blocking_gate_failure_rejects_even_with_hands(self):
        # Hands are there, but so is a second person, in most of the footage.
        datalake = _FakeDatalake(
            caption="The wearer's hands pass a tool while another person faces "
            "the camera across the bench.",
            segments=_segments(
                (0.0, 12.0, "the hands pass a tool while another person faces the camera"),
                (12.0, 24.0, "two people work across the bench"),
            ),
        )
        verdict = await CleaningAgent(client=datalake).clean(
            "vid_5", media={"duration_seconds": 24}
        )
        assert verdict.accepted is False
        assert "G1-OTHERFACE" in (verdict.rejection_reason or "")

    @pytest.mark.asyncio
    async def test_spans_with_someone_else_in_them_are_not_anchored(self):
        datalake = _FakeDatalake(
            caption="hands work, then a colleague reaches in",
            segments=_segments(
                (0.0, 30.0, "the left hand seats the connector"),
                (30.0, 60.0, "a colleague reaches in to hold the jig"),
                (60.0, 90.0, "the left hand seats the next connector"),
            ),
        )
        verdict = await CleaningAgent(client=datalake).clean(
            "vid_6", media={"duration_seconds": 90}
        )
        spans = [(s.span_start, s.span_end) for s in verdict.action_segments]
        assert spans == [(0.0, 30.0), (60.0, 90.0)]

    @pytest.mark.asyncio
    async def test_a_failed_tag_write_does_not_lose_the_verdict(self):
        datalake = _FakeDatalake(
            caption="The left hand steadies the pipe while the right hand turns the wrench.",
            segments=_segments((0.0, 20.0, "the right hand turns the wrench")),
            fail_update=True,
        )
        verdict = await CleaningAgent(client=datalake).clean("vid_6")
        assert verdict.accepted is True
        assert verdict.tags_written == []
        assert any("could not write tags" in error for error in verdict.errors)

    @pytest.mark.asyncio
    async def test_anchors_need_a_windowed_caption_read(self):
        """The whole-video caption read has no timings, so the window is asked for."""

        datalake = _FakeDatalake(
            caption="The right hand turns the wrench.",
            segments=_segments((0.0, 30.0, "the right hand turns the wrench")),
        )
        agent = CleaningAgent(client=datalake)
        anchored = await agent.clean("vid_1", media={"duration_seconds": 30})
        assert anchored.action_segments

    @pytest.mark.asyncio
    async def test_an_unsupplied_duration_is_looked_up_rather_than_given_up_on(self):
        """A curation run has no download behind it, so nothing hands in a
        duration — and without one there are no timed segments and no anchors.
        Five task queries produced six accepted clips and zero anchors between
        them before this was asked for instead of assumed absent.
        """
        datalake = _FakeDatalake(
            caption="The right hand turns the wrench.",
            segments=_segments((0.0, 30.0, "the right hand turns the wrench")),
            duration_seconds=30.0,
        )
        verdict = await CleaningAgent(client=datalake).clean("vid_1")
        assert verdict.action_segments, "the duration was there for the asking"

    @pytest.mark.asyncio
    async def test_a_duration_nobody_knows_still_judges_the_footage(self):
        """The honest limit: no duration anywhere means no anchors, but the
        frame check still runs off the untimed caption."""

        datalake = _FakeDatalake(
            caption="The right hand turns the wrench.",
            segments=_segments((0.0, 30.0, "the right hand turns the wrench")),
            duration_seconds=None,
        )
        verdict = await CleaningAgent(client=datalake).clean("vid_1")
        assert verdict.accepted is True
        assert verdict.action_segments == []

    @pytest.mark.asyncio
    async def test_the_trace_records_every_step(self):
        datalake = _FakeDatalake(
            caption="Both hands fold the dough.",
            segments=_segments((0.0, 15.0, "both hands fold the dough")),
        )
        verdict = await CleaningAgent(client=datalake).clean("vid_7")
        actions = [step.action for step in verdict.trace.steps]
        assert actions == [
            "get_video_content",
            "frame_check",
            "quality_gates",
            "propose_segments",
            "update_video",
        ]
        assert all(step.agent == "cleaning" for step in verdict.trace.steps)


_ACTION_REPLY = """{
  "label": "chop-vegetables",
  "narration": "The knife works through an onion held against the board.",
  "hands_visible": true,
  "left_hand": "holds the onion steady",
  "right_hand": "moves the knife",
  "objects": ["onion", "knife"],
  "events": [{"start": 3.0, "end": 4.5, "label": "reposition-grip",
              "narration": "The left hand shifts back."}],
  "tags": ["hoi/chop-vegetables/right/move-knife", "hands_visible"],
  "confidence": 0.7,
  "usable": true,
  "reason": "both hands in frame, one continuous take"
}"""

_TASK_REPLY = """```json
{"label": "prep-mirepoix", "narration": "Onion, carrot and celery are cut for a base.",
 "task_family": "cooking", "error_sample": false, "confidence": 0.8}
```"""


class TestAnnotationAgent:
    """What happens between the boundaries."""

    @pytest.mark.asyncio
    async def test_anchors_become_a_task_action_event_tree(self):
        datalake = _FakeDatalake()
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        segments = CleaningAgent().propose_segments(
            _segments((0.0, 10.0, "the right hand moves the knife through an onion"))
        )
        run = await AnnotationAgent(client=datalake, gemini=gemini).annotate_video(
            "vid_1", segments
        )

        levels = [annotation.hier_level for annotation in run.annotations]
        assert levels == ["task", "action", "event"]
        assert run.annotation_level.value == "L3"
        assert run.task_family == "cooking"

        task, action, event = run.annotations
        assert task.segment_id == "t1" and task.parent_segment_id is None
        assert action.parent_segment_id == "t1"
        assert event.parent_segment_id == action.segment_id

    @pytest.mark.asyncio
    async def test_each_level_says_something_of_its_own(self):
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        segments = CleaningAgent().propose_segments(
            _segments((0.0, 10.0, "the right hand moves the knife"))
        )
        run = await AnnotationAgent(client=_FakeDatalake(), gemini=gemini).annotate_video(
            "vid_1", segments
        )
        task, action, _ = run.annotations
        assert task.narration and action.narration
        assert task.narration != action.narration

    @pytest.mark.asyncio
    async def test_events_are_clamped_inside_their_parent(self):
        overrunning = _ACTION_REPLY.replace('"start": 3.0, "end": 4.5', '"start": -5, "end": 99')
        gemini = _FakeGemini([overrunning, _TASK_REPLY])
        segments = CleaningAgent().propose_segments(
            _segments((0.0, 10.0, "the right hand moves the knife"))
        )
        run = await AnnotationAgent(client=_FakeDatalake(), gemini=gemini).annotate_video(
            "vid_1", segments
        )
        event = run.annotations[-1]
        assert (event.span_start, event.span_end) == (0.0, 10.0)

    @pytest.mark.asyncio
    async def test_hand_assignment_is_never_invented(self):
        silent = _ACTION_REPLY.replace('"left_hand": "holds the onion steady",', "").replace(
            '"right_hand": "moves the knife",', ""
        )
        gemini = _FakeGemini([silent, _TASK_REPLY])
        segments = CleaningAgent().propose_segments(
            _segments((0.0, 10.0, "a hand reaches into frame and picks up a knife"))
        )
        run = await AnnotationAgent(client=_FakeDatalake(), gemini=gemini).annotate_video(
            "vid_1", segments
        )
        action = next(a for a in run.annotations if a.hier_level == "action")
        assert action.left_hand is None and action.right_hand is None
        assert action.caveat

    @pytest.mark.asyncio
    async def test_a_hands_free_span_is_dropped_when_hands_are_required(self):
        no_hands = _ACTION_REPLY.replace('"hands_visible": true', '"hands_visible": false')
        gemini = _FakeGemini([no_hands])
        segments = CleaningAgent().propose_segments(
            _segments((0.0, 10.0, "the hand moves out of frame")), require_hands=False
        )
        run = await AnnotationAgent(client=_FakeDatalake(), gemini=gemini).annotate_video(
            "vid_1", segments, require_hands=True
        )
        assert run.annotations == []
        assert run.spans_rejected == 1
        assert run.survival_rate == 0.0

    @pytest.mark.asyncio
    async def test_a_model_failure_does_not_kill_the_pass(self):
        gemini = _FakeGemini(["not json at all", _ACTION_REPLY, _TASK_REPLY])
        segments = CleaningAgent().propose_segments(
            _segments(
                (0.0, 10.0, "the right hand moves the knife"),
                (40.0, 55.0, "the left hand sweeps the board clean"),
            )
        )
        run = await AnnotationAgent(client=_FakeDatalake(), gemini=gemini).annotate_video(
            "vid_1", segments
        )
        assert run.spans_considered == 2
        assert run.spans_rejected == 1
        assert run.survival_rate == 0.5
        assert any(a.hier_level == "action" for a in run.annotations)

    @pytest.mark.asyncio
    async def test_the_tree_and_its_level_are_written_back(self):
        datalake = _FakeDatalake()
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        segments = CleaningAgent().propose_segments(
            _segments((0.0, 10.0, "the right hand moves the knife"))
        )
        await AnnotationAgent(client=datalake, gemini=gemini).annotate_video("vid_1", segments)
        write = datalake.updates[-1]
        assert write["custom"]["annotation"]["level"] == "L3"
        assert len(write["custom"]["hoi"]) == 3
        assert "hoi/chop-vegetables/right/move-knife" in write["tags"]

    @pytest.mark.asyncio
    async def test_discovery_mode_scopes_to_the_worklist(self):
        datalake = _FakeDatalake(
            videos=[{"video_id": "vid_1"}],
            search_results=[
                {"ref": "vid_1@0-10", "video_id": "vid_1", "start": 0, "end": 10},
                {"ref": "vid_9@0-10", "video_id": "vid_9", "start": 0, "end": 10},
            ],
            moments={
                "vid_1@0-10": {"caption": "the right hand moves the knife"},
            },
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        run = await AnnotationAgent(client=datalake, gemini=gemini).run(
            "chopping vegetables", tag="clean_pass"
        )
        assert run.spans_considered == 1
        assert run.videos_touched == ["vid_1"]
        assert run.annotation_level.value in ("L2", "L3")

    @pytest.mark.asyncio
    async def test_a_failed_search_is_reported_not_raised(self):
        class _Broken(_FakeDatalake):
            async def search(self, query: str, top_k: int | None = None) -> dict[str, Any]:
                raise MemoriesDatalakeError("search is down")

        run = await AnnotationAgent(client=_Broken(), gemini=_FakeGemini([])).run("x")
        assert run.annotations == []
        assert "search failed: search is down" in run.errors


class TestCurationAgent:
    """What the set as a whole is worth."""

    @staticmethod
    def _agent(datalake: _FakeDatalake, gemini: _FakeGemini) -> CurationAgent:
        return CurationAgent(
            client=datalake,
            cleaning_agent=CleaningAgent(client=datalake),
            annotation_agent=AnnotationAgent(client=datalake, gemini=gemini),
        )

    @pytest.mark.asyncio
    async def test_the_four_hour_measures_stay_apart(self):
        datalake = _FakeDatalake(
            caption="The left hand holds the pipe while the right hand turns the wrench.",
            segments=_segments(
                (0.0, 600.0, "the right hand turns the wrench"),
                (600.0, 900.0, "the bench is empty, nothing happens"),
            ),
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        report = await self._agent(datalake, gemini).curate(
            ["vid_1"],
            media={"vid_1": {"duration_seconds": 900, "uploader": "fixit"}},
        )
        hours = report.hours
        assert hours.delivered_hours == pytest.approx(0.25)
        # Half the segments read as idle, so accepted is strictly less than
        # delivered — the two must never be reported as one number.
        assert hours.accepted_hours < hours.delivered_hours
        assert hours.accepted_labeled_hours == hours.accepted_hours
        assert report.hours.as_dict()["media_yield"] < 1.0

    @pytest.mark.asyncio
    async def test_a_rejected_clip_contributes_delivered_hours_only(self):
        datalake = _FakeDatalake(
            caption="A wide shot of an empty workshop.",
            segments=_segments((0.0, 300.0, "an empty workshop")),
        )
        report = await self._agent(datalake, _FakeGemini([])).curate(
            ["vid_2"], media={"vid_2": {"duration_seconds": 300}}
        )
        assert report.accepted_clips == 0
        assert report.hours.delivered_hours == pytest.approx(300 / 3600)
        assert report.hours.accepted_hours == 0.0
        assert report.batch_grade == "D"

    @pytest.mark.asyncio
    async def test_annotation_is_skipped_for_rejected_footage(self):
        datalake = _FakeDatalake(
            caption="An empty room.", segments=_segments((0.0, 60.0, "an empty room"))
        )
        gemini = _FakeGemini([])  # any call would raise
        report = await self._agent(datalake, gemini).curate(["vid_3"])
        assert report.clips[0].annotation is None
        assert gemini.prompts == []

    @pytest.mark.asyncio
    async def test_the_worklist_can_come_from_a_tag(self):
        datalake = _FakeDatalake(
            caption="Both hands knead dough.",
            segments=_segments((0.0, 100.0, "both hands knead dough")),
            videos=[{"video_id": "vid_7"}],
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        report = await self._agent(datalake, gemini).curate(tag="clean_pass")
        assert [clip.video_id for clip in report.clips] == ["vid_7"]

    @pytest.mark.asyncio
    async def test_verdicts_fold_back_into_a_manifest(self):
        datalake = _FakeDatalake(
            caption="The left hand steadies the board, the right hand saws.",
            segments=_segments((0.0, 400.0, "the right hand saws")),
        )
        gemini = _FakeGemini([_ACTION_REPLY, _TASK_REPLY])
        agent = self._agent(datalake, gemini)
        report = await agent.curate(
            ["vid_1"],
            media={
                "vid_1": {
                    "duration_seconds": 400,
                    "uploader": "woodwork",
                    "license": "Creative Commons",
                    "source_url": "https://example.com/v",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30,
                }
            },
        )
        manifest = DatasetManifest(
            query="first person woodworking",
            clips=[
                DatasetClip(
                    url="https://example.com/v",
                    platform="youtube",
                    duration_seconds=400,
                    datalake_video_id="vid_1",
                )
            ],
        )
        agent.apply_to_manifest(manifest, report)

        entry = manifest.clips[0]
        assert entry.quality_grade in ("A", "B", "C")
        assert entry.annotation_level in ("L2", "L3")
        assert entry.annotations
        assert manifest.hours.accepted_labeled_hours > 0
        assert manifest.hours.delivered_hours == pytest.approx(400 / 3600, abs=1e-3)

    @pytest.mark.asyncio
    async def test_an_empty_worklist_is_not_an_error(self):
        report = await self._agent(_FakeDatalake(), _FakeGemini([])).curate([])
        assert report.clips == []
        assert report.batch_grade == "D"
        assert report.errors == []


class TestCurationReadsWhatTheLakeAlreadyKnows:
    """A curation run has no download behind it, and used to admit nothing.

    The upload writes provenance and media properties into the video's own
    metadata. Curation ignored them, so licence, provenance and resolution came
    back "not measured" for facts that were sitting in the Datalake — put there
    by the upload that indexed the video.
    """

    class _Lake:
        """Enough of the client to answer get_video, with a real record shape."""

        def __init__(self, record: dict[str, Any]) -> None:
            self.record = record
            self.asked: list[str] = []

        async def get_video(self, video_id: str) -> dict[str, Any]:
            self.asked.append(video_id)
            return self.record

    @pytest.mark.asyncio
    async def test_stored_provenance_and_media_are_read_back(self):
        from video_searching_agent.agent.curation_agent import CurationAgent, CurationReport

        lake = self._Lake(
            {
                "video_id": "vid_1",
                "duration_seconds": 740.0,
                "fps": 1,
                "metadata": {
                    "title": "POV Wash and Fold",
                    "custom": {
                        "source_url": "https://www.youtube.com/watch?v=UvEpBlU-KBw",
                        "uploader": "Mama Coco At Home",
                        "license_note": "youtube",
                        "height": 720,
                        "width": None,
                    },
                },
            }
        )
        agent = CurationAgent(client=lake)
        facts = await agent._stored_facts("vid_1", CurationReport())

        assert facts["duration_seconds"] == 740.0
        assert facts["title"] == "POV Wash and Fold"
        assert facts["source_url"].endswith("UvEpBlU-KBw")
        assert facts["uploader"] == "Mama Coco At Home"
        assert facts["license"] == "youtube"
        assert facts["height"] == 720
        assert "width" not in facts, "a null field is not a fact"

    @pytest.mark.asyncio
    async def test_the_index_sampling_rate_is_never_read_as_the_frame_rate(self):
        """record["fps"] is how often the Datalake sampled the video — 1 —
        not the video's frame rate. Feeding it to G1-FPS (>=30) would fail
        good footage on a number nobody measured."""

        from video_searching_agent.agent.curation_agent import CurationAgent, CurationReport

        lake = self._Lake({"video_id": "vid_1", "duration_seconds": 100.0, "fps": 1})
        facts = await CurationAgent(client=lake)._stored_facts("vid_1", CurationReport())
        assert "fps" not in facts

    @pytest.mark.asyncio
    async def test_what_the_caller_knows_wins_over_what_was_stored(self):
        """A download saw the file itself; the stored record is second best."""

        from video_searching_agent.agent.curation_agent import CurationAgent, CurationReport

        lake = self._Lake(
            {"video_id": "vid_1", "duration_seconds": 100.0,
             "metadata": {"custom": {"uploader": "stored"}}}
        )
        agent = CurationAgent(client=lake)
        stored = await agent._stored_facts("vid_1", CurationReport())
        merged = {**stored, **{"uploader": "from the download"}}
        assert merged["uploader"] == "from the download"
        assert merged["duration_seconds"] == 100.0

    @pytest.mark.asyncio
    async def test_an_unreachable_record_is_reported_not_fatal(self):
        from video_searching_agent.agent.curation_agent import CurationAgent, CurationReport
        from video_searching_agent.api.memories_datalake_client import MemoriesDatalakeError

        class Broken:
            async def get_video(self, video_id: str) -> dict[str, Any]:
                raise MemoriesDatalakeError("503 upstream")

        report = CurationReport()
        facts = await CurationAgent(client=Broken())._stored_facts("vid_1", report)
        assert facts == {}
        assert any("stored facts unavailable" in e for e in report.errors)
