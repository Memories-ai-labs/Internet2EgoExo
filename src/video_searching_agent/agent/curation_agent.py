"""The curation agent: what the set as a whole is worth.

Cleaning and annotation both work one clip at a time. Curation is the pass that
can only be done across the whole set, and it answers the questions a buyer
actually asks:

* **How many hours are there really?** Four different numbers, never mixed:
  what was worn, what was delivered, what was accepted, what was accepted *and*
  labelled. Only the last one should ever be quoted externally.
* **What grade is the batch?** A-D from the mean of what got in, which decides
  whether it goes to the main training set, stays internal, or is not ingested.

Diversity and deduplication used to be graded here (`G3-OP`, `G3-SOP`, `G3-ERR`,
`G3-DUP`) and no longer are: they judge a *set* rather than the footage, and
this project's deliverable is a clip you can train on. What matters about a clip
is whether the hands are in frame, whether you can see what they are doing, and
whether the tree over it says what they did.

It also drives the per-clip agents over a worklist, because "curate this
collection" is one request, not three: for each video it runs the cleaning
agent, and only what survives is worth paying the annotation agent for.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.annotation_agent import AnnotationAgent, AnnotationRun
from video_searching_agent.agent.cleaning_agent import (
    CleaningAgent,
    CleaningVerdict,
)
from video_searching_agent.agent.react import AgentTrace
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.curation.quality_gates import (
    Grade,
    HoursLedger,
    build_hours_ledger,
    evaluate_clip,
)
from video_searching_agent.curation.viewpoint import Viewpoint
from video_searching_agent.models.dataset import DatasetManifest

logger = logging.getLogger(__name__)

AGENT_NAME = "curation"

# Awaited as each clip finishes, so a caller can stream verdicts as they land
# rather than waiting for the whole set.
ClipCallback = Callable[["CuratedClip"], Awaitable[None]]


@dataclass
class CuratedClip:
    """One clip's standing after cleaning and annotation."""

    video_id: str
    accepted: bool = False
    rejection_reason: str | None = None
    grade: str = Grade.D.value
    score: int = 0
    annotation_level: str = "L0"
    duration_seconds: int = 0
    usable_seconds: int = 0
    idle_seconds: int = 0
    labeled: bool = False
    commercial_use_ok: bool = False
    uploader: str | None = None
    task_family: str | None = None
    error_sample: bool = False
    blocking_failures: list[str] = field(default_factory=list)
    cleaning: CleaningVerdict | None = None
    annotation: AnnotationRun | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "grade": self.grade,
            "score": self.score,
            "annotation_level": self.annotation_level,
            "duration_seconds": self.duration_seconds,
            "usable_seconds": self.usable_seconds,
            "idle_seconds": self.idle_seconds,
            "labeled": self.labeled,
            "commercial_use_ok": self.commercial_use_ok,
            "uploader": self.uploader,
            "task_family": self.task_family,
            "error_sample": self.error_sample,
            "blocking_failures": self.blocking_failures,
            "cleaning": self.cleaning.as_dict() if self.cleaning else None,
            "annotation": self.annotation.as_dict() if self.annotation else None,
        }


@dataclass
class CurationReport:
    """What a curation pass concluded about the set."""

    query: str = ""
    clips: list[CuratedClip] = field(default_factory=list)
    hours: HoursLedger = field(default_factory=HoursLedger)
    grades: dict[str, int] = field(default_factory=dict)
    annotation_levels: dict[str, int] = field(default_factory=dict)
    trace: AgentTrace = field(default_factory=lambda: AgentTrace(agent=AGENT_NAME))
    errors: list[str] = field(default_factory=list)

    @property
    def accepted_clips(self) -> int:
        return sum(1 for clip in self.clips if clip.accepted)

    @property
    def batch_grade(self) -> str:
        """The set's grade, from the mean score of the clips that got in.

        A rejected clip is not averaged in — it is not part of the batch. With
        nothing accepted the batch is a D, which is the honest answer.
        """
        accepted = [clip.score for clip in self.clips if clip.accepted]
        if not accepted:
            return Grade.D.value
        mean = sum(accepted) / len(accepted)
        return (
            Grade.A.value
            if mean >= 85
            else Grade.B.value
            if mean >= 70
            else Grade.C.value
            if mean >= 55
            else Grade.D.value
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "clips": [clip.as_dict() for clip in self.clips],
            "hours": self.hours.as_dict(),
            "accepted_clips": self.accepted_clips,
            "total_clips": len(self.clips),
            "batch_grade": self.batch_grade,
            "grades": self.grades,
            "annotation_levels": self.annotation_levels,
            "trace": self.trace.as_list(),
            "errors": self.errors,
        }


def _llm_or_none() -> Any | None:
    """A model client, or None when this deployment has no key for one."""

    try:
        from video_searching_agent.api.llm import get_llm_client

        return get_llm_client()
    except Exception as exc:  # noqa: BLE001 - the caption-only path still works
        logger.info("no model available for the looking passes: %s", exc)
        return None


class CurationAgent:
    """Drives cleaning and annotation over a set, then grades the set."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        cleaning_agent: CleaningAgent | None = None,
        annotation_agent: AnnotationAgent | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            client: Datalake client. Created on first use when omitted.
            cleaning_agent: Filtering and clipping. Created when omitted.
            annotation_agent: Narration. Created when omitted.
        """
        self._client = client
        self._cleaning = cleaning_agent
        self._annotation = annotation_agent

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def cleaning(self) -> CleaningAgent:
        if self._cleaning is None:
            # The model is handed in on purpose: the cleaning agent only looks
            # at frames when it was given one, so a bare agent stays offline and
            # this is the wiring that opts the pipeline in.
            self._cleaning = CleaningAgent(client=self.client, llm=_llm_or_none())
        return self._cleaning

    @property
    def annotation(self) -> AnnotationAgent:
        if self._annotation is None:
            self._annotation = AnnotationAgent(client=self.client)
        return self._annotation

    async def curate(
        self,
        video_ids: list[str] | None = None,
        *,
        tag: str | None = None,
        query: str = "",
        media: dict[str, dict[str, Any]] | None = None,
        require_hands: bool = True,
        wanted_viewpoint: Viewpoint | None = None,
        annotate: bool = True,
        write_back: bool = True,
        limit: int = 50,
        on_clip: ClipCallback | None = None,
    ) -> CurationReport:
        """Clean, annotate and grade a set of indexed videos.

        Args:
            video_ids: Videos to curate. When omitted, `tag` is listed instead.
            tag: Worklist tag to pull the set from.
            query: What the collection was looking for, carried for the record.
            media: Per-video download facts (`{video_id: {width, height, …}}`),
                which the media gates cannot otherwise measure.
            require_hands: Drop footage with no hands in it.
            wanted_viewpoint: Drop footage the captions place elsewhere.
            annotate: Run the annotation agent on what survives cleaning.
                False gives a cleaning-only pass, which is much cheaper.
            write_back: Write verdicts onto the videos.
            limit: Ceiling on videos pulled from a tag listing.
            on_clip: Awaited as each clip finishes, for progress streaming.

        Returns:
            A CurationReport with per-clip verdicts, the hours ledger, the
            Gate 3 checks and the batch grade.
        """
        report = CurationReport(query=query)
        media = media or {}

        ids = list(video_ids or [])
        if not ids and tag:
            ids = await self._worklist(tag, report, limit)
        if not ids:
            report.trace.add(
                thought="Establish the worklist for this pass.",
                action="curate",
                action_input={"tag": tag},
                observation="nothing to curate",
            )
            return report

        for video_id in ids[:limit]:
            # What the caller knows, over what the Datalake already stored. A
            # collection run hands in the download's facts; a curation run over
            # already-indexed videos hands in nothing — and then reported
            # licence, provenance, resolution and frame rate as "not measured"
            # for facts sitting in the video's own metadata, put there by the
            # upload that indexed it.
            facts = {**await self._stored_facts(video_id, report), **media.get(video_id, {})}
            clip = CuratedClip(
                video_id=video_id,
                duration_seconds=int(facts.get("duration_seconds") or 0),
                uploader=facts.get("uploader"),
            )

            verdict = await self.cleaning.clean(
                video_id,
                title=facts.get("title"),
                require_hands=require_hands,
                wanted_viewpoint=wanted_viewpoint,
                media=facts,
                write_back=write_back,
            )
            clip.cleaning = verdict
            clip.accepted = verdict.accepted
            clip.rejection_reason = verdict.rejection_reason
            clip.idle_seconds = verdict.idle_seconds
            clip.usable_seconds = verdict.usable_seconds or max(
                clip.duration_seconds - verdict.idle_seconds, 0
            )
            if verdict.quality:
                clip.grade = verdict.quality.grade.value
                clip.score = verdict.quality.score
                clip.commercial_use_ok = verdict.quality.commercial_use_ok
                clip.blocking_failures = list(verdict.quality.blocking_failures)
            report.errors.extend(verdict.errors)
            report.trace.extend(verdict.trace)

            if clip.accepted and annotate:
                run = await self.annotation.annotate_video(
                    video_id,
                    verdict.segments,
                    query=query,
                    require_hands=require_hands,
                    write_back=write_back,
                )
                clip.annotation = run
                clip.annotation_level = run.annotation_level.value
                clip.labeled = clip.annotation_level in ("L2", "L3")
                clip.task_family = run.task_family
                clip.error_sample = run.error_sample
                report.errors.extend(run.errors)
                report.trace.extend(run.trace)
                self._regrade(clip, verdict, facts, report)

            report.clips.append(clip)
            if on_clip is not None:
                await on_clip(clip)

        self._tally(report)
        report.trace.add(
            thought="Grade the set from the clips that got in.",
            action="tally",
            action_input={"accepted": report.accepted_clips},
            observation=(
                f"batch {report.batch_grade}, "
                f"{report.hours.accepted_labeled_hours:.2f} accepted_labeled hours"
            ),
        )
        return report

    def apply_to_manifest(
        self,
        manifest: DatasetManifest,
        report: CurationReport,
    ) -> DatasetManifest:
        """Fold a curation pass back into a collection manifest.

        Matches on `datalake_video_id`, so a manifest built by the search pass
        gains the gate verdicts, the annotations and the hours ledger without
        being rebuilt.
        """
        by_id = {clip.video_id: clip for clip in report.clips}
        for entry in manifest.clips:
            curated = by_id.get(entry.datalake_video_id or "")
            if curated is None:
                continue
            entry.quality_score = curated.score
            entry.quality_grade = curated.grade
            entry.annotation_level = curated.annotation_level
            entry.commercial_use_ok = curated.commercial_use_ok
            entry.usable_seconds = curated.usable_seconds
            entry.idle_seconds = curated.idle_seconds
            entry.task_family = curated.task_family
            entry.error_sample = curated.error_sample
            entry.blocking_failures = curated.blocking_failures
            if curated.annotation:
                entry.annotations = list(curated.annotation.annotations)
            if not curated.accepted and curated.rejection_reason:
                entry.notes = curated.rejection_reason

        manifest.recompute_totals()
        return manifest

    # --------------------------------------------------------------- plumbing

    @staticmethod
    def _regrade(
        clip: CuratedClip,
        verdict: CleaningVerdict,
        facts: dict[str, Any],
        report: CurationReport,
    ) -> None:
        """Re-score a clip once its annotations exist.

        Annotation depth is 45 of the 100 points, so the score the cleaning
        agent produced is a floor, not a grade: it was computed before there
        was anything to grade. Re-running the gates with the tree in hand is
        what turns a floor into the number the batch is sold on.
        """
        if clip.annotation is None:
            return

        annotations = [
            annotation.model_dump(mode="json")
            for annotation in clip.annotation.annotations
        ]
        regraded = evaluate_clip(
            license_value=facts.get("license") or facts.get("license_note"),
            source_url=facts.get("source_url"),
            uploader=facts.get("uploader"),
            width=facts.get("width"),
            height=facts.get("height"),
            fps=facts.get("fps"),
            duration_seconds=facts.get("duration_seconds"),
            container=facts.get("container"),
            caption=verdict.caption,
            caption_segments=verdict.caption_segments,
            annotations=annotations,
            require_commercial_use=False,
        )
        clip.grade = regraded.grade.value
        clip.score = regraded.score
        clip.blocking_failures = list(regraded.blocking_failures)
        # Acceptance is the re-graded verdict's own, never a second opinion
        # assembled here: `evaluate_clip` refuses both a blocking failure and a
        # grade of D, and re-deriving only the first half is how a clip scoring
        # 25 with no annotations was reported as accepted. Conjoined with the
        # cleaning stage's decision because that one knows things the quality
        # report does not (viewpoint, hands), and a re-grade may only take
        # acceptance away.
        clip.accepted = clip.accepted and regraded.accepted
        if not clip.accepted and not clip.rejection_reason:
            clip.rejection_reason = (
                "blocking gate failure: " + ", ".join(regraded.blocking_failures)
                if regraded.blocking_failures
                else f"re-graded {regraded.grade.value} at {regraded.score}/100 "
                "once annotation depth was known"
            )
        report.trace.add(
            thought="Re-grade the clip now that its annotation depth is known.",
            action="quality_gates",
            action_input={"video_id": clip.video_id},
            observation=(
                f"score {verdict.quality.score if verdict.quality else 0} -> "
                f"{regraded.score}, grade {clip.grade}, "
                f"level {clip.annotation_level}"
            ),
        )

    async def _stored_facts(
        self, video_id: str, report: CurationReport
    ) -> dict[str, Any]:
        """The media facts the Datalake is already holding for a video.

        The upload writes provenance and media properties into the video's
        metadata, so reading them back costs one free call and turns four gates
        from "not measured" into measured. Anything missing stays missing — this
        fills in what was recorded, it does not invent what was not.
        """
        try:
            record = await self.client.get_video(video_id)
        except MemoriesDatalakeError as exc:
            report.errors.append(f"stored facts unavailable for {video_id}: {exc}")
            return {}
        if not isinstance(record, dict):
            return {}

        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        custom = metadata.get("custom") if isinstance(metadata.get("custom"), dict) else {}

        facts: dict[str, Any] = {}
        duration = record.get("duration_seconds") or record.get("duration")
        if isinstance(duration, int | float) and duration > 0:
            facts["duration_seconds"] = float(duration)
        if metadata.get("title"):
            facts["title"] = metadata["title"]
        # Deliberately *not* mapped: record["fps"] is the rate the Datalake
        # sampled the video at while indexing — 1, normally — and not the
        # video's own frame rate. Feeding it to G1-FPS (>=30) would report 1 fps
        # and fail footage that is fine. A wrong measurement is worse than an
        # honest "not measured", so the frame rate stays unmeasured unless a
        # download reports it.

        # The upload's own record of where this came from.
        for key in ("source_url", "uploader", "width", "height", "extractor"):
            value = custom.get(key)
            if value not in (None, ""):
                facts[key] = value
        licence = custom.get("license_note") or custom.get("license")
        if licence:
            facts["license"] = licence
        return facts

    async def _worklist(
        self, tag: str, report: CurationReport, limit: int
    ) -> list[str]:
        """Video ids carrying a tag."""
        try:
            listing = await self.client.list_videos(tag=tag, limit=limit)
        except MemoriesDatalakeError as exc:
            report.errors.append(f"worklist unavailable: {exc}")
            report.trace.add(
                thought=f"Pull the set tagged {tag}.",
                action="list_videos",
                action_input={"tag": tag},
                observation=f"failed: {exc}",
            )
            return []

        ids = [
            str(video.get("video_id"))
            for video in (listing.get("videos") or [])
            if isinstance(video, dict) and video.get("video_id")
        ]
        report.trace.add(
            thought=f"Pull the set tagged {tag}.",
            action="list_videos",
            action_input={"tag": tag},
            observation=f"{len(ids)} videos to curate",
        )
        return ids

    @staticmethod
    def _tally(report: CurationReport) -> None:
        """Fill in the hours ledger and the grade/level histograms."""
        delivered = sum(clip.duration_seconds for clip in report.clips)
        accepted = sum(clip.usable_seconds for clip in report.clips if clip.accepted)
        labeled = sum(
            clip.usable_seconds
            for clip in report.clips
            if clip.accepted and clip.labeled
        )
        idle = sum(clip.idle_seconds for clip in report.clips)
        report.hours = build_hours_ledger(
            delivered_seconds=delivered,
            accepted_seconds=accepted,
            idle_seconds=idle,
            labeled_seconds=labeled,
        )

        grades: dict[str, int] = {}
        levels: dict[str, int] = {}
        for clip in report.clips:
            grades[clip.grade] = grades.get(clip.grade, 0) + 1
            levels[clip.annotation_level] = levels.get(clip.annotation_level, 0) + 1
        report.grades = grades
        report.annotation_levels = levels
