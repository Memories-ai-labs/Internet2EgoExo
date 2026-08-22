"""The annotation agent: hierarchical narration over time anchors.

The cleaning agent decides which footage is worth keeping and where each action
starts and stops. This agent says what happens between those boundaries, at
three depths:

    task    "replace a bicycle inner tube"          the whole job
      action  "lever the tyre off the rim"          one step of it
        event   "the second lever slips out"        one moment inside a step

That shape is `Gate 2` of the quality standard, and the depth it reaches is the
grade: a single caption for a whole video is `L1` and untrainable; a task with
anchored actions that each say something of their own is `L2`, the minimum;
`L3` adds events, objects and hand state.

Two rules the prompt enforces because the data is worthless without them:

* **Each level says something of its own.** Copying the task sentence down onto
  its actions produces a tree that looks deep and teaches nothing (`G2-TREE-3`).
* **Never invent hand assignment.** If the captions do not say which hand did
  what, the field stays null. A guessed left/right is worse than a blank one,
  because it cannot be told apart from a real one downstream.

There are two ways in. `annotate_video` annotates anchors the cleaning agent
already found. `run` is the discovery loop the Datalake is built for —
`search_moments` shortlists spans, `get_moment` says what is really in them,
the model judges, and `update_video` writes the verdict back so it becomes the
filter for the next pass.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.cleaning_agent import Segment
from video_searching_agent.agent.react import (
    AgentTrace,
    as_float,
    parse_json_object,
    text_of,
)
from video_searching_agent.api.llm import get_llm_client
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.curation.frame_check import CAPTION_EVIDENCE_CAVEAT
from video_searching_agent.curation.quality_gates import (
    AnnotationLevel,
    grade_annotation_level,
)
from video_searching_agent.models.dataset import ClipAnnotation

logger = logging.getLogger(__name__)

AGENT_NAME = "annotation"

ACTION_SYSTEM_PROMPT = """You annotate one span of a video for a training dataset.

You are given a span's time range, its visual captions and its speech. Say what
happens in it, in a schema a training pipeline can filter on.

Report only what the captions and speech support. You are reading a description
of the frames, not the frames themselves, so:

- If the captions do not say which hand does what, leave that field null. Never
  assign a hand to make the record look complete.
- If the span shows no hands at all, say so with `hands_visible: false`. That is
  a useful answer, not a failure.
- Objects are the things acted on, named as the captions name them.
- `label` is a short kebab-case name for what happens in THIS span
  ("solder-joint", "tube-insertion", "chop-vegetables"). Two rules make it
  worth having:
  * It must not restate the overall task. A span of a derailleur overhaul
    labelled "service-derailleur" adds nothing the task name did not already
    say — label the step, not the job.
  * It must not repeat a label already used for another span of this video. If
    three spans really are the same operation, distinguish them by what is being
    acted on or which pass it is ("degrease-jockey-wheels",
    "rinse-jockey-wheels"), because three identically named spans cannot be told
    apart by anything downstream.
  Any labels already used are listed below; do not reuse them.
- `narration` is one sentence in your own words about THIS span. It must not
  repeat the name of the overall task back at me.
- `events` are moments inside this span worth their own anchor — a slip, a
  retry, a tool change. Times must lie inside the span. Omit if there are none.
- `tags` follow `hoi/<label>/<hand>/<verb-object>` when a hand is known, plus
  any of `hands_visible`, `no_hands`, `continuous_take` that apply.

Return ONLY a JSON object, no markdown:

{
  "label": "chop-vegetables",
  "narration": "The knife works through an onion held steady against the board.",
  "hands_visible": true,
  "left_hand": "holds the onion steady",
  "right_hand": "moves the knife through it",
  "objects": ["onion", "knife", "cutting board"],
  "events": [{"start": 12.5, "end": 14.0, "label": "reposition-grip",
              "narration": "The left hand shifts back from the blade."}],
  "tags": ["hoi/chop-vegetables/right/move-knife", "hands_visible"],
  "confidence": 0.7,
  "usable": true,
  "reason": "one continuous take, both hands in frame, no cuts"
}

`usable` is false when the span should not go into the dataset — no hands, a
screen recording, a title card, or too heavily edited to learn from. Say why in
`reason` either way, in one sentence."""

TASK_SYSTEM_PROMPT = """You name the overall task a sequence of annotated spans belongs to.

You are given the actions found in one video, in order. Name the job they add up
to and describe it in one sentence. The sentence must describe the whole job, not
repeat any single action.

`task_family` is a coarse bucket for coverage accounting: "cooking",
"bike-repair", "electronics-assembly", "warehouse-picking", "cleaning". Use
kebab-case.

`error_sample` is true when the sequence contains a mistake, a retry or a
rework — those are wanted, at 10-20% of a set, so say when you see one.

Return ONLY a JSON object, no markdown:

{
  "label": "replace-inner-tube",
  "narration": "A punctured inner tube is swapped for a new one and the tyre refitted.",
  "task_family": "bike-repair",
  "error_sample": false,
  "confidence": 0.8
}"""


@dataclass
class AnnotationRun:
    """Everything one annotation pass produced."""

    query: str
    annotations: list[ClipAnnotation] = field(default_factory=list)
    trace: AgentTrace = field(default_factory=lambda: AgentTrace(agent=AGENT_NAME))
    videos_touched: list[str] = field(default_factory=list)
    spans_considered: int = 0
    spans_rejected: int = 0
    tags_written: list[str] = field(default_factory=list)
    task_family: str | None = None
    error_sample: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def survival_rate(self) -> float:
        """Share of shortlisted spans that survived the read.

        The number that matters when quoting a shortlist: retrieval proposes,
        the span decides.
        """
        if not self.spans_considered:
            return 0.0
        kept = self.spans_considered - self.spans_rejected
        return round(kept / self.spans_considered, 3)

    @property
    def annotation_level(self) -> AnnotationLevel:
        """The depth this pass actually reached, graded by the standard."""
        return grade_annotation_level(
            [annotation.model_dump(mode="json") for annotation in self.annotations]
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "annotations": [a.model_dump(mode="json") for a in self.annotations],
            "trace": self.trace.as_list(),
            "videos_touched": self.videos_touched,
            "spans_considered": self.spans_considered,
            "spans_rejected": self.spans_rejected,
            "survival_rate": self.survival_rate,
            "annotation_level": self.annotation_level.value,
            "task_family": self.task_family,
            "error_sample": self.error_sample,
            "tags_written": sorted(set(self.tags_written)),
            "errors": self.errors,
            "caveat": CAPTION_EVIDENCE_CAVEAT,
        }


class AnnotationAgent:
    """Narrates anchored spans into a task → action → event tree."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        gemini: Any | None = None,
        max_spans: int = 12,
    ) -> None:
        """Initialize the agent.

        Args:
            client: Datalake client. Created on first use when omitted.
            gemini: Model client for the verdicts.
            max_spans: Ceiling on spans read per pass — each read costs money.
        """
        self._client = client
        self._gemini = gemini
        self.max_spans = max_spans

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def gemini(self) -> Any:
        if self._gemini is None:
            self._gemini = get_llm_client()
        return self._gemini

    # ------------------------------------------------- annotate known anchors

    async def annotate_video(
        self,
        video_id: str,
        segments: list[Segment],
        *,
        query: str = "",
        require_hands: bool = True,
        write_back: bool = True,
    ) -> AnnotationRun:
        """Narrate the anchors the cleaning agent found for one video.

        Args:
            video_id: The indexed video the anchors belong to.
            segments: The anchor tree from `CleaningAgent.propose_segments`.
            query: What the collection was looking for, for the record.
            require_hands: Drop spans the model reports as hands-free.
            write_back: Write the tree onto the video.

        Returns:
            An AnnotationRun whose `annotation_level` is the depth reached.
        """
        run = AnnotationRun(query=query)
        actions = [segment for segment in segments if segment.hier_level == "action"]
        if not actions:
            run.trace.add(
                thought="Nothing was anchored, so there is nothing to narrate.",
                action="annotate_video",
                action_input={"video_id": video_id},
                observation="no action anchors supplied",
            )
            return run

        run.videos_touched.append(video_id)
        run.spans_considered = len(actions)
        action_annotations: list[ClipAnnotation] = []

        for segment in actions[: self.max_spans]:
            verdict = await self._judge_span(
                text=segment.source_text,
                transcription=None,
                start=segment.span_start,
                end=segment.span_end,
                ref=None,
                used_labels=[a.label for a in action_annotations if a.label],
            )
            if verdict is None:
                run.spans_rejected += 1
                run.trace.add(
                    thought=f"Narrate {segment.segment_id}.",
                    action="annotate_span",
                    action_input={"segment_id": segment.segment_id},
                    observation="no usable verdict returned",
                )
                continue

            usable = bool(verdict.get("usable", True))
            hands_visible = bool(verdict.get("hands_visible", False))
            if require_hands and not hands_visible:
                usable = False
            reason = str(verdict.get("reason") or "")

            run.trace.add(
                thought=f"Narrate {segment.segment_id}.",
                action="annotate_span",
                action_input={
                    "segment_id": segment.segment_id,
                    "span": [segment.span_start, segment.span_end],
                },
                observation=f"{'keep' if usable else 'drop'}: {reason}"[:300],
            )
            if not usable:
                run.spans_rejected += 1
                continue

            annotation = self._annotation_from(
                verdict,
                segment_id=segment.segment_id,
                parent_segment_id=segment.parent_segment_id,
                hier_level="action",
                span_start=segment.span_start,
                span_end=segment.span_end,
            )
            action_annotations.append(annotation)
            run.annotations.append(annotation)
            run.annotations.extend(
                self._events_from(verdict, parent=annotation)
            )

        if not action_annotations:
            return run

        task_segment = next(
            (segment for segment in segments if segment.hier_level == "task"), None
        )
        task = await self._name_task(
            action_annotations,
            span_start=task_segment.span_start if task_segment else None,
            span_end=task_segment.span_end if task_segment else None,
        )
        if task is not None:
            # The task goes first so the tree reads top-down.
            run.annotations.insert(0, task)
            run.task_family = task.tags[0].split("task_family/")[-1] if task.tags else None
        run.trace.add(
            thought="Name the job these actions add up to.",
            action="name_task",
            action_input={"actions": [a.label for a in action_annotations]},
            observation=(task.narration or task.label or "unnamed") if task else "unnamed",
        )

        if write_back:
            observation = await self._write_back(video_id, run)
            run.trace.add(
                thought="Write the tree back so it filters the next pass.",
                action="update_video",
                action_input={"video_id": video_id, "spans": len(run.annotations)},
                observation=observation,
            )
        return run

    # ------------------------------------------------------- discovery loop

    async def run(
        self,
        query: str,
        tag: str | None = None,
        top_k: int | None = None,
        require_hands: bool = True,
        write_back: bool = True,
    ) -> AnnotationRun:
        """Find spans matching a query and annotate them.

        Args:
            query: What to look for, in natural language.
            tag: Restrict the pass to videos already carrying this tag — the
                worklist pattern (`clean_pass`, `first_person_view`).
            top_k: Spans to shortlist. Defaults to `max_spans`.
            require_hands: Reject spans whose captions show no hands.
            write_back: Write verdicts onto the videos. False for a dry run.

        Returns:
            An AnnotationRun with the annotations, the trace and the survival
            rate.
        """
        run = AnnotationRun(query=query)
        limit = min(top_k or self.max_spans, self.max_spans)

        worklist_ids = await self._worklist(tag, run) if tag else None

        try:
            found = await self.client.search(query=query, top_k=limit)
        except MemoriesDatalakeError as exc:
            run.errors.append(f"search failed: {exc}")
            run.trace.add(
                thought=f"Shortlist spans matching '{query}'.",
                action="search_moments",
                action_input={"query": query, "top_k": limit},
                observation=f"failed: {exc}",
            )
            return run

        results = [item for item in (found.get("results") or []) if isinstance(item, dict)]
        if worklist_ids is not None:
            results = [
                item for item in results if str(item.get("video_id")) in worklist_ids
            ]
        run.spans_considered = len(results)
        run.trace.add(
            thought=f"Shortlist spans matching '{query}'.",
            action="search_moments",
            action_input={"query": query, "top_k": limit},
            observation=f"{len(results)} spans shortlisted",
        )

        # Spans are annotated per video so each video gets its own task level.
        by_video: dict[str, list[ClipAnnotation]] = {}
        for item in results:
            ref = item.get("ref")
            video_id = item.get("video_id")
            if not ref or not video_id:
                continue

            moment = await self._read_moment(str(ref), run)
            if moment is None:
                run.spans_rejected += 1
                continue
            caption, transcription = moment

            verdict = await self._judge_span(
                text=caption,
                transcription=transcription,
                start=item.get("start"),
                end=item.get("end"),
                ref=str(ref),
                used_labels=[a.label for a in run.annotations if a.label],
            )
            if verdict is None:
                run.spans_rejected += 1
                run.trace.add(
                    thought="Judge the span against the schema.",
                    action="annotate_span",
                    action_input={"ref": ref},
                    observation="no usable verdict returned",
                )
                continue

            usable = bool(verdict.get("usable", True))
            if require_hands and not bool(verdict.get("hands_visible", False)):
                usable = False
            reason = str(verdict.get("reason") or "")
            run.trace.add(
                thought="Judge the span against the schema.",
                action="annotate_span",
                action_input={"ref": ref},
                observation=f"{'keep' if usable else 'drop'}: {reason}"[:300],
            )
            if not usable:
                run.spans_rejected += 1
                continue

            siblings = by_video.setdefault(str(video_id), [])
            annotation = self._annotation_from(
                verdict,
                segment_id=f"t1.a{len(siblings) + 1}",
                parent_segment_id="t1",
                hier_level="action",
                span_start=as_float(item.get("start")),
                span_end=as_float(item.get("end")),
                ref=str(ref),
            )
            siblings.append(annotation)
            if str(video_id) not in run.videos_touched:
                run.videos_touched.append(str(video_id))
            run.annotations.append(annotation)
            run.annotations.extend(self._events_from(verdict, parent=annotation))

        # A task level per video is what lifts the pass from L1 to L2.
        for video_id, actions in by_video.items():
            task = await self._name_task(actions)
            if task is not None:
                run.annotations.insert(0, task)
                run.task_family = run.task_family or (
                    task.tags[0].split("task_family/")[-1] if task.tags else None
                )
            if write_back:
                observation = await self._write_back(video_id, run, only_video=video_id)
                run.trace.add(
                    thought="Write the tree back so it filters the next pass.",
                    action="update_video",
                    action_input={"video_id": video_id, "spans": len(actions)},
                    observation=observation,
                )
        return run

    # --------------------------------------------------------------- plumbing

    async def _worklist(self, tag: str, run: AnnotationRun) -> list[str] | None:
        """Video ids carrying a tag, or None when the listing failed."""
        try:
            listing = await self.client.list_videos(tag=tag, limit=100)
        except MemoriesDatalakeError as exc:
            run.errors.append(f"worklist unavailable: {exc}")
            run.trace.add(
                thought="Scope the pass to a tagged worklist.",
                action="list_videos",
                action_input={"tag": tag},
                observation=f"failed: {exc}",
            )
            return None

        ids = [
            str(video.get("video_id"))
            for video in (listing.get("videos") or [])
            if isinstance(video, dict) and video.get("video_id")
        ]
        run.trace.add(
            thought=f"The pass is scoped to videos tagged {tag}.",
            action="list_videos",
            action_input={"tag": tag},
            observation=f"{len(ids)} videos carry that tag",
        )
        return ids

    async def _read_moment(
        self, ref: str, run: AnnotationRun
    ) -> tuple[str | None, str | None] | None:
        """Read one span's derived content, or None when it could not be read."""
        try:
            moment = await self.client.get_moment(
                ref, expand=["caption", "transcription"]
            )
        except MemoriesDatalakeError as exc:
            run.errors.append(f"could not read {ref}: {exc}")
            run.trace.add(
                thought=f"Read {ref} to see what is actually in it.",
                action="get_moment",
                action_input={"ref": ref},
                observation=f"failed: {exc}",
            )
            return None

        caption = text_of(moment, "caption")
        transcription = text_of(moment, "transcription")
        run.trace.add(
            thought=f"Read {ref} to see what is actually in it.",
            action="get_moment",
            action_input={"ref": ref},
            observation=(caption or transcription or "no derived text")[:300],
        )
        return caption, transcription

    async def _judge_span(
        self,
        text: str | None,
        transcription: str | None,
        start: Any,
        end: Any,
        ref: str | None,
        used_labels: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Ask the model for a schema-shaped verdict on one span.

        `used_labels` are the labels already given to other spans of this video.
        Without them the model annotates each span in isolation and cannot know
        it is repeating itself — which is how one derailleur overhaul produced
        three consecutive actions all called `clean-mechanical-parts`, and an
        action that restated its own task.
        """
        if not text and not transcription:
            return None

        already = ", ".join(dict.fromkeys(label for label in (used_labels or []) if label))
        prompt = (
            f"Span: {ref or 'anchored span'} ({start}s to {end}s)\n\n"
            f"Visual captions:\n{text or '(none)'}\n\n"
            f"Speech:\n{transcription or '(none)'}\n\n"
            + (f"Labels already used for other spans of this video: {already}\n\n"
               if already else "")
            + "Annotate this span."
        )
        return await self._ask(prompt, ACTION_SYSTEM_PROMPT, ref or "span")

    async def _name_task(
        self,
        actions: list[ClipAnnotation],
        span_start: float | None = None,
        span_end: float | None = None,
    ) -> ClipAnnotation | None:
        """Ask the model to name the job a run of actions adds up to."""
        if not actions:
            return None

        listing = "\n".join(
            f"- {annotation.span_start}s-{annotation.span_end}s "
            f"{annotation.label or 'unnamed'}: {annotation.narration or ''}"
            for annotation in actions
        )
        verdict = await self._ask(
            f"Actions found in this video, in order:\n{listing}\n\nName the task.",
            TASK_SYSTEM_PROMPT,
            "task",
        )
        if verdict is None:
            return None

        family = str(verdict.get("task_family") or "").strip()
        tags = [f"task_family/{family}"] if family else []
        if verdict.get("error_sample"):
            tags.append("error_sample")

        return ClipAnnotation(
            segment_id="t1",
            parent_segment_id=None,
            hier_level="task",
            span_start=span_start if span_start is not None else actions[0].span_start,
            span_end=(
                span_end
                if span_end is not None
                else max(
                    (a.span_end for a in actions if a.span_end is not None),
                    default=None,
                )
            ),
            label=str(verdict.get("label") or "") or None,
            narration=str(verdict.get("narration") or "") or None,
            tags=tags,
            source="agent",
            confidence=as_float(verdict.get("confidence")),
            caveat=CAPTION_EVIDENCE_CAVEAT,
        )

    async def _ask(
        self, prompt: str, system: str, what: str
    ) -> dict[str, Any] | None:
        """One model call, returning a parsed object or None.

        Transport and parse failures are logged and swallowed: one unreadable
        span must not take the whole pass down with it.
        """
        try:
            response = await self.gemini.create_message_async(
                messages=[{"role": "user", "content": prompt}],
                system=system,
            )
            text = self.gemini.get_text_response(response)
        except Exception as exc:  # model/transport errors must not kill the pass
            logger.warning("annotation model call failed for %s: %s", what, exc)
            return None

        if not text:
            return None
        try:
            return parse_json_object(text)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.info("unparseable annotation for %s: %s", what, exc)
            return None

    @staticmethod
    def _annotation_from(
        verdict: dict[str, Any],
        *,
        segment_id: str,
        parent_segment_id: str | None,
        hier_level: str,
        span_start: float | None,
        span_end: float | None,
        ref: str | None = None,
    ) -> ClipAnnotation:
        """Build one annotation from a model verdict."""
        return ClipAnnotation(
            span_start=span_start,
            span_end=span_end,
            ref=ref,
            segment_id=segment_id,
            parent_segment_id=parent_segment_id,
            hier_level=hier_level,
            label=verdict.get("label"),
            narration=str(verdict.get("narration") or "") or None,
            left_hand=verdict.get("left_hand"),
            right_hand=verdict.get("right_hand"),
            objects=[str(obj) for obj in (verdict.get("objects") or [])],
            tags=[str(tag) for tag in (verdict.get("tags") or [])],
            source="agent",
            confidence=as_float(verdict.get("confidence")),
            caveat=CAPTION_EVIDENCE_CAVEAT,
        )

    @staticmethod
    def _events_from(
        verdict: dict[str, Any], parent: ClipAnnotation
    ) -> list[ClipAnnotation]:
        """Event-level children of one action, clamped inside their parent.

        An event whose times fall outside the action it belongs to would fail
        `G2-TREE-1`, so it is clamped here rather than written out broken.
        """
        events: list[ClipAnnotation] = []
        raw = verdict.get("events")
        if not isinstance(raw, list):
            return events

        for index, entry in enumerate(raw, start=1):
            if not isinstance(entry, dict):
                continue
            start = as_float(entry.get("start"))
            end = as_float(entry.get("end"))
            if start is None or end is None or end <= start:
                continue
            if parent.span_start is not None:
                start = max(start, parent.span_start)
            if parent.span_end is not None:
                end = min(end, parent.span_end)
            if end <= start:
                continue
            events.append(
                ClipAnnotation(
                    span_start=start,
                    span_end=end,
                    ref=parent.ref,
                    segment_id=f"{parent.segment_id}.e{index}",
                    parent_segment_id=parent.segment_id,
                    hier_level="event",
                    label=str(entry.get("label") or "") or None,
                    narration=str(entry.get("narration") or "") or None,
                    source="agent",
                    caveat=CAPTION_EVIDENCE_CAVEAT,
                )
            )
        return events

    async def _write_back(
        self,
        video_id: str,
        run: AnnotationRun,
        only_video: str | None = None,
    ) -> str:
        """Land the annotation tree and its tags on the video."""
        annotations = run.annotations
        if only_video:
            # In discovery mode one run spans several videos; write each video
            # only the spans that belong to it.
            annotations = [
                annotation
                for annotation in run.annotations
                if annotation.ref is None or str(annotation.ref).startswith(video_id)
            ]

        tags: list[str] = []
        for annotation in annotations:
            for tag in annotation.tags:
                if tag not in tags:
                    tags.append(tag)

        try:
            await self.client.update_video(
                video_id,
                tags=tags,
                custom={
                    "annotation": {
                        "level": run.annotation_level.value,
                        "query": run.query,
                        "caveat": CAPTION_EVIDENCE_CAVEAT,
                    },
                    "hoi": [a.model_dump(mode="json") for a in annotations],
                },
            )
        except MemoriesDatalakeError as exc:
            run.errors.append(f"could not write annotations: {exc}")
            return f"failed: {exc}"

        run.tags_written.extend(tags)
        return f"wrote {len(annotations)} spans and {len(tags)} tags"
