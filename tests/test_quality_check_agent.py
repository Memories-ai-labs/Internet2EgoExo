"""The audit that is allowed to fail what the pipeline accepted.

The point of a fourth agent is that it does not share the reasoning of the other
three. So these tests are mostly about it *catching* things — a plausible label
on the wrong seconds, a child span outside its parent, fifty clips that are
really twelve videos — and about it not inventing faults where the evidence is
merely thin.
"""

from __future__ import annotations

import pytest

from video_searching_agent.agent.quality_check_agent import (
    QualityCheckAgent,
    _sample_across,
)
from video_searching_agent.curation.viewpoint import Viewpoint


def anchor(sid, start, end, level="action", parent=None, label=None):
    return {
        "segment_id": sid,
        "parent_segment_id": parent,
        "hier_level": level,
        "span_start": start,
        "span_end": end,
        "label": label,
    }


def clip(video_id="vid_1", **kwargs):
    base = {
        "video_id": video_id,
        "title": "a clip",
        "duration_seconds": 600,
        "viewpoint": "egocentric",
        "segments": [],
        "annotations": [],
    }
    base.update(kwargs)
    return base


class TestStructure:
    """The free checks, which need no model and catch the arithmetic faults."""

    @pytest.mark.asyncio
    async def test_a_clean_clip_passes(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 0.0, 30.0), anchor("a2", 40.0, 70.0)])],
            verify_evidence=False,
        )
        assert audit.passed is True
        assert audit.verdict == "accept"
        assert audit.clips_passed == 1

    @pytest.mark.asyncio
    async def test_an_anchor_past_the_end_of_the_video_fails(self):
        """The defect that shipped once already, caught from the artefact."""

        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(duration_seconds=100, segments=[anchor("a1", 60.0, 140.0)])],
            verify_evidence=False,
        )
        assert audit.passed is False
        assert [f.check for f in audit.clips[0].findings] == ["ANCHOR-OVERRUN"]

    @pytest.mark.asyncio
    async def test_overlapping_siblings_fail(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 0.0, 30.0), anchor("a2", 20.0, 50.0)])],
            verify_evidence=False,
        )
        assert "G2-TREE-2" in {f.check for f in audit.clips[0].findings}

    @pytest.mark.asyncio
    async def test_touching_siblings_are_not_overlapping(self):
        """A boundary shared to the millisecond is not a fault."""

        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 0.0, 30.0), anchor("a2", 30.0, 60.0)])],
            verify_evidence=False,
        )
        assert audit.passed is True

    @pytest.mark.asyncio
    async def test_a_child_outside_its_parent_fails(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [
                clip(
                    segments=[
                        anchor("t1", 10.0, 100.0, level="task"),
                        anchor("a1", 5.0, 40.0, parent="t1"),
                    ]
                )
            ],
            verify_evidence=False,
        )
        assert "G2-TREE-1" in {f.check for f in audit.clips[0].findings}

    @pytest.mark.asyncio
    async def test_an_anchor_starting_at_zero_is_not_treated_as_missing(self):
        """A falsy zero dropped every video's first segment once. Not again."""

        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 0.0, 20.0)])], verify_evidence=False
        )
        assert audit.clips[0].anchors_checked == 1
        assert audit.passed is True

    @pytest.mark.asyncio
    async def test_a_sub_second_anchor_fails(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 10.0, 10.5)])], verify_evidence=False
        )
        assert "ANCHOR-SHORT" in {f.check for f in audit.clips[0].findings}

    @pytest.mark.asyncio
    async def test_a_backwards_anchor_fails(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 50.0, 20.0)])], verify_evidence=False
        )
        assert "ANCHOR-ORDER" in {f.check for f in audit.clips[0].findings}

    @pytest.mark.asyncio
    async def test_a_level_repeating_its_parents_words_fails(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [
                clip(
                    annotations=[
                        {"segment_id": "t1", "label": "Assemble the shelf", "hier_level": "task"},
                        {
                            "segment_id": "a1",
                            "parent_segment_id": "t1",
                            "label": "assemble the shelf",
                            "hier_level": "action",
                        },
                    ]
                )
            ],
            verify_evidence=False,
        )
        assert "G2-TREE-3" in {f.check for f in audit.clips[0].findings}

    @pytest.mark.asyncio
    async def test_viewpoint_drift_is_caught_per_clip(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(viewpoint="exocentric")],
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
            verify_evidence=False,
        )
        assert "VIEWPOINT-DRIFT" in {f.check for f in audit.clips[0].findings}

    @pytest.mark.asyncio
    async def test_an_unknown_viewpoint_is_not_drift(self):
        """Abstention is honest; it is not a wrong answer."""

        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(viewpoint="unknown")],
            wanted_viewpoint=Viewpoint.EGOCENTRIC,
            verify_evidence=False,
        )
        assert audit.passed is True


class TestTheSet:
    """What is only visible across clips."""

    @pytest.mark.asyncio
    async def test_fifty_clips_from_three_videos_is_flagged(self):
        agent = QualityCheckAgent(llm=False)
        clips = [clip(video_id=f"vid_{n % 3}", url=f"https://x/{n % 3}") for n in range(30)]
        audit = await agent.audit(clips, verify_evidence=False)
        assert "SET-CONCENTRATED" in {f.check for f in audit.set_findings}

    @pytest.mark.asyncio
    async def test_the_same_span_delivered_twice_fails(self):
        agent = QualityCheckAgent(llm=False)
        same = [anchor("a1", 10.0, 40.0, label="chops onions")]
        audit = await agent.audit(
            [clip(video_id="vid_1", segments=same), clip(video_id="vid_1", segments=same)],
            verify_evidence=False,
        )
        assert "SET-DUPLICATE" in {f.check for f in audit.set_findings}

    @pytest.mark.asyncio
    async def test_anchors_exceeding_the_claimed_hours_fails(self):
        """Anchors are a subset of the footage; more means double counting."""

        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 0.0, 3600.0)], duration_seconds=7200)],
            claimed_hours=0.5,
            verify_evidence=False,
        )
        assert "SET-HOURS" in {f.check for f in audit.set_findings}

    @pytest.mark.asyncio
    async def test_anchors_under_the_claimed_hours_is_normal(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit(
            [clip(segments=[anchor("a1", 0.0, 600.0)], duration_seconds=3600)],
            claimed_hours=1.0,
            verify_evidence=False,
        )
        assert "SET-HOURS" not in {f.check for f in audit.set_findings}

    @pytest.mark.asyncio
    async def test_an_empty_set_fails(self):
        agent = QualityCheckAgent(llm=False)
        audit = await agent.audit([], verify_evidence=False)
        assert audit.passed is False
        assert "SET-EMPTY" in {f.check for f in audit.set_findings}


class TestTheEvidencePass:
    """The model is asked to refute a label, not to confirm it."""

    class _Datalake:
        def __init__(self, text="hands chop onions on the board"):
            self.text = text
            self.windows = []

        async def get_caption(self, video_id, start=None, end=None):
            self.windows.append((start, end))
            if not self.text:
                return {"segments": []}
            return {"segments": [{"start": start, "end": end, "text": self.text}]}

    class _Model:
        def __init__(self, answer):
            self.answer = answer
            self.prompts = []

        def new_conversation(self, text):
            self.prompts.append(text)
            return [{"role": "user", "content": text}]

        async def create_message_async(self, messages, **_):
            return {"text": self.answer}

        def get_text_response(self, response):
            return response["text"]

        def get_cost_usd(self, response):
            return 0.0004

    @pytest.mark.asyncio
    async def test_a_contradicted_label_fails_with_the_evidence_attached(self):
        datalake = self._Datalake("the person talks to the camera about knives")
        model = self._Model(
            '{"supported": false, "confidence": 0.9, '
            '"problem": "the captions describe talking, not chopping"}'
        )
        agent = QualityCheckAgent(client=datalake, llm=model)
        audit = await agent.audit(
            [
                clip(
                    annotations=[
                        {
                            "segment_id": "a1",
                            "label": "chops an onion",
                            "span_start": 42.0,
                            "span_end": 58.0,
                        }
                    ]
                )
            ]
        )
        findings = audit.clips[0].findings
        assert [f.check for f in findings] == ["EVIDENCE-CONTRADICTED"]
        assert "talking" in findings[0].detail
        assert findings[0].evidence  # the captions that decided it
        assert audit.cost_usd == pytest.approx(0.0004)

    @pytest.mark.asyncio
    async def test_the_window_is_read_not_the_whole_video(self):
        """A whole-video caption read comes back with no timings at all."""

        datalake = self._Datalake()
        model = self._Model('{"supported": true, "confidence": 0.8, "problem": ""}')
        agent = QualityCheckAgent(client=datalake, llm=model)
        await agent.audit(
            [
                clip(
                    annotations=[
                        {"segment_id": "a1", "label": "chops", "span_start": 42.0, "span_end": 58.0}
                    ]
                )
            ]
        )
        assert datalake.windows == [(42.0, 58.0)]

    @pytest.mark.asyncio
    async def test_a_supported_label_produces_no_finding(self):
        datalake = self._Datalake()
        model = self._Model('{"supported": true, "confidence": 0.9, "problem": ""}')
        agent = QualityCheckAgent(client=datalake, llm=model)
        audit = await agent.audit(
            [
                clip(
                    annotations=[
                        {"segment_id": "a1", "label": "chops", "span_start": 10.0, "span_end": 30.0}
                    ]
                )
            ]
        )
        assert audit.passed is True
        assert audit.clips[0].spans_verified == 1

    @pytest.mark.asyncio
    async def test_a_span_with_no_captions_is_a_warning_not_a_failure(self):
        """Silence is not contradiction — but it is worth saying out loud."""

        datalake = self._Datalake(text="")
        model = self._Model('{"supported": true}')
        agent = QualityCheckAgent(client=datalake, llm=model)
        audit = await agent.audit(
            [
                clip(
                    annotations=[
                        {"segment_id": "a1", "label": "chops", "span_start": 10.0, "span_end": 30.0}
                    ]
                )
            ]
        )
        assert audit.passed is True
        assert [f.check for f in audit.clips[0].findings] == ["EVIDENCE-NONE"]
        assert audit.clips[0].findings[0].severity == "warn"

    @pytest.mark.asyncio
    async def test_an_unreadable_model_answer_is_not_a_finding(self):
        datalake = self._Datalake()
        model = self._Model("I am not sure, sorry.")
        agent = QualityCheckAgent(client=datalake, llm=model)
        audit = await agent.audit(
            [
                clip(
                    annotations=[
                        {"segment_id": "a1", "label": "chops", "span_start": 10.0, "span_end": 30.0}
                    ]
                )
            ]
        )
        assert audit.passed is True

    @pytest.mark.asyncio
    async def test_the_prompt_asks_for_the_reason_it_is_wrong(self):
        datalake = self._Datalake()
        model = self._Model('{"supported": true}')
        agent = QualityCheckAgent(client=datalake, llm=model)
        await agent.audit(
            [
                clip(
                    annotations=[
                        {"segment_id": "a1", "label": "chops", "span_start": 10.0, "span_end": 30.0}
                    ]
                )
            ]
        )
        assert "WRONG" in model.prompts[0]
        assert "do not invent a fault" in model.prompts[0]

    @pytest.mark.asyncio
    async def test_spans_are_sampled_across_the_clip(self):
        """Later anchors drift most, so reading the first few would miss them."""

        assert _sample_across(list(range(20)), 4) == [0, 5, 10, 15]
        assert _sample_across([1, 2], 4) == [1, 2]
        assert _sample_across([], 3) == []
