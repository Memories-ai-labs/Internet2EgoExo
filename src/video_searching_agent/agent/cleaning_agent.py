"""The cleaning agent: agentic filtering and agentic clipping.

Two jobs, both about *what belongs in the dataset* rather than what it says:

**Agentic filtering.** Twice, at the two moments where it is cheapest:

1. Before the download, from platform metadata only — licence, duration,
   viewpoint. Nothing is fetched and nothing is indexed, so a candidate that
   cannot possibly qualify costs nothing.
2. After indexing, from the derived content — hands in frame, other people,
   editing, resolution, frame rate. This is the pass that matters, because it
   judges the footage rather than the description of it.

**Agentic clipping.** Where the boundaries of an action are. Caption segments
carry timestamps, so a run of consecutive segments with hands in them is an
action span and a run of idle segments is not. The output is a tree of *time
anchors* on the whole video — `[start, end]` pairs, never cut files. That is
`G2-TREE-5` in the standard and it is not negotiable: cut clips lose the context
either side of the boundary, and a boundary that turns out to be wrong can no
longer be moved.

The division of labour with the annotation agent is deliberate: this agent
decides *where* the boundaries are and whether the footage is worth keeping;
the annotation agent decides *what to call* what happens between them.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.react import AgentTrace, segments_of, text_of
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.curation.frame_check import (
    CAPTION_EVIDENCE_CAVEAT,
    FrameCheck,
    check_frames,
    mentions_hands,
)
from video_searching_agent.curation.quality_gates import (
    GateCheck,
    QualityReport,
    evaluate_clip,
    mentions_idle,
    permits_commercial_use,
)
from video_searching_agent.curation.viewpoint import Viewpoint, classify_viewpoint

logger = logging.getLogger(__name__)

AGENT_NAME = "cleaning"

# Clipping bounds. An action shorter than this is noise; a gap longer than this
# is a new action rather than a pause inside one.
MIN_ACTION_SECONDS = 2.0
MAX_MERGE_GAP_SECONDS = 2.0

# Tags the cleaning agent writes so the annotation pass has a worklist.
TAG_CLEAN = "clean_pass"
TAG_REJECTED = "clean_rejected"
TAG_HANDS = "hands_visible"
TAG_NO_HANDS = "no_hands"
TAG_EGOCENTRIC = "first_person_view"
TAG_EXOCENTRIC = "third_person_view"


@dataclass
class Segment:
    """One time anchor on a video. Never a file."""

    segment_id: str
    hier_level: str
    span_start: float
    span_end: float
    parent_segment_id: str | None = None
    label: str | None = None
    narration: str | None = None
    hands_visible: bool = False
    evidence: list[str] = field(default_factory=list)
    source_text: str | None = None

    @property
    def duration(self) -> float:
        return round(max(self.span_end - self.span_start, 0.0), 3)

    def as_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "parent_segment_id": self.parent_segment_id,
            "hier_level": self.hier_level,
            "span_start": round(self.span_start, 3),
            "span_end": round(self.span_end, 3),
            "duration": self.duration,
            "label": self.label,
            "narration": self.narration,
            "hands_visible": self.hands_visible,
            "evidence": self.evidence,
        }


@dataclass
class ScreeningVerdict:
    """The pre-download filter's answer on one candidate."""

    url: str | None = None
    accepted: bool = False
    reasons: list[str] = field(default_factory=list)
    checks: list[GateCheck] = field(default_factory=list)
    viewpoint: Viewpoint = Viewpoint.UNKNOWN
    viewpoint_confidence: float = 0.0
    duration_seconds: int | None = None
    commercial_use_ok: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "accepted": self.accepted,
            "reasons": self.reasons,
            "viewpoint": self.viewpoint.value,
            "viewpoint_confidence": self.viewpoint_confidence,
            "duration_seconds": self.duration_seconds,
            "commercial_use_ok": self.commercial_use_ok,
            "checks": [check.as_dict() for check in self.checks],
        }


@dataclass
class CleaningVerdict:
    """The post-index filter's answer, plus the clipping it produced."""

    video_id: str
    accepted: bool = False
    rejection_reason: str | None = None
    frame_check: FrameCheck | None = None
    quality: QualityReport | None = None
    segments: list[Segment] = field(default_factory=list)
    caption: str | None = None
    caption_segments: list[dict[str, Any]] = field(default_factory=list)
    idle_seconds: int = 0
    usable_seconds: int = 0
    tags_written: list[str] = field(default_factory=list)
    trace: AgentTrace = field(default_factory=lambda: AgentTrace(agent=AGENT_NAME))
    errors: list[str] = field(default_factory=list)
    caveat: str = CAPTION_EVIDENCE_CAVEAT

    @property
    def action_segments(self) -> list[Segment]:
        """Just the action-level anchors — what the annotation agent reads."""
        return [segment for segment in self.segments if segment.hier_level == "action"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "frame_check": (
                {
                    "hands_visible": self.frame_check.hands_visible,
                    "hands_confidence": self.frame_check.hands_confidence,
                    "hand_evidence": self.frame_check.hand_evidence,
                    "viewpoint": self.frame_check.viewpoint.value,
                    "is_footage": self.frame_check.is_footage,
                }
                if self.frame_check
                else None
            ),
            "quality": self.quality.as_dict() if self.quality else None,
            "segments": [segment.as_dict() for segment in self.segments],
            "idle_seconds": self.idle_seconds,
            "usable_seconds": self.usable_seconds,
            "tags_written": self.tags_written,
            "trace": self.trace.as_list(),
            "errors": self.errors,
            "caveat": self.caveat,
        }


class CleaningAgent:
    """Filters candidates and clips what survives into time anchors."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        min_action_seconds: float = MIN_ACTION_SECONDS,
        max_merge_gap_seconds: float = MAX_MERGE_GAP_SECONDS,
    ) -> None:
        """Initialize the agent.

        Args:
            client: Datalake client. Created on first use when omitted.
            min_action_seconds: Shortest span worth anchoring.
            max_merge_gap_seconds: Longest pause that still counts as one action.
        """
        self._client = client
        self.min_action_seconds = min_action_seconds
        self.max_merge_gap_seconds = max_merge_gap_seconds

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    # ------------------------------------------------ agentic filtering (pre)

    def screen(
        self,
        info: dict[str, Any],
        *,
        wanted_viewpoint: Viewpoint | None = None,
        min_duration_seconds: int | None = None,
        require_commercial_use: bool = False,
    ) -> ScreeningVerdict:
        """Filter one candidate on metadata alone, before spending anything.

        Args:
            info: Platform metadata — a yt-dlp probe result or an equivalent
                dict with title/description/duration/license/tags.
            wanted_viewpoint: Reject candidates the metadata places elsewhere.
            min_duration_seconds: Reject anything shorter.
            require_commercial_use: Make Gate 0 blocking here rather than at
                delivery. Off by default: an unclear licence is recorded and
                carried, and only bars the clip from the *training* set.

        Returns:
            A ScreeningVerdict. `accepted` False means do not download.
        """
        verdict = ScreeningVerdict(url=info.get("webpage_url") or info.get("url"))

        duration = info.get("duration")
        verdict.duration_seconds = (
            int(duration) if isinstance(duration, int | float) else None
        )

        tags = [str(tag) for tag in (info.get("tags") or info.get("categories") or [])]
        reading = classify_viewpoint(
            title=info.get("title"),
            description=info.get("description"),
            tags=tags,
        )
        verdict.viewpoint = reading.viewpoint
        verdict.viewpoint_confidence = reading.confidence

        licence = info.get("license") or info.get("licence")
        verdict.commercial_use_ok = permits_commercial_use(
            str(licence) if licence else None
        )
        verdict.checks.append(
            GateCheck(
                "G0-LIC",
                "Licence permits commercial training use",
                passed=verdict.commercial_use_ok,
                blocking=require_commercial_use,
                value=str(licence) if licence else "unknown",
                threshold="explicit commercial-use permission",
            )
        )

        if min_duration_seconds:
            long_enough = (verdict.duration_seconds or 0) >= min_duration_seconds
            verdict.checks.append(
                GateCheck(
                    "PRE-DUR",
                    "Long enough to be worth indexing",
                    passed=long_enough,
                    blocking=True,
                    value=verdict.duration_seconds,
                    threshold=f">={min_duration_seconds}s",
                )
            )
            if not long_enough:
                verdict.reasons.append(
                    f"duration {verdict.duration_seconds or 'unknown'}s is below the "
                    f"{min_duration_seconds}s minimum"
                )

        if wanted_viewpoint:
            # Silence never rejects: the metadata is a weak signal and the frame
            # check gets the deciding vote after indexing.
            contradicted = (
                verdict.viewpoint != Viewpoint.UNKNOWN
                and verdict.viewpoint != wanted_viewpoint
            )
            verdict.checks.append(
                GateCheck(
                    "PRE-VIEW",
                    "Viewpoint not contradicted by the metadata",
                    passed=not contradicted,
                    blocking=True,
                    value=verdict.viewpoint.value,
                    threshold=f"{wanted_viewpoint.value} or unstated",
                )
            )
            if contradicted:
                verdict.reasons.append(
                    f"metadata places this in {verdict.viewpoint.value}, "
                    f"wanted {wanted_viewpoint.value}"
                )

        if require_commercial_use and not verdict.commercial_use_ok:
            verdict.reasons.append(
                "licence does not clearly permit commercial training use"
            )

        verdict.accepted = not verdict.reasons
        return verdict

    # ----------------------------------------------- agentic filtering (post)

    async def clean(
        self,
        video_id: str,
        *,
        title: str | None = None,
        require_hands: bool = True,
        wanted_viewpoint: Viewpoint | None = None,
        media: dict[str, Any] | None = None,
        write_back: bool = True,
    ) -> CleaningVerdict:
        """Judge an indexed video and clip it into time anchors.

        Args:
            video_id: The indexed video.
            title: Title, used for the viewpoint reading.
            require_hands: Reject footage with no hands in it.
            wanted_viewpoint: Reject footage the captions place elsewhere.
            media: What the download knew — width, height, fps, container,
                licence, source_url, uploader, duration_seconds. Passed to the
                media gates, which cannot otherwise be measured.
            write_back: Write the verdict onto the video as tags.

        Returns:
            A CleaningVerdict. Rejected videos still carry their segments, so a
            near-miss can be inspected rather than silently dropped.
        """
        verdict = CleaningVerdict(video_id=video_id)
        media = media or {}

        caption, caption_segments, transcription, summary = await self._read_derived(
            video_id, verdict
        )

        # --- the frame check: does the footage show what we need? ----------
        check = check_frames(
            caption=caption,
            transcription=transcription,
            summary=summary,
            title=title,
        )
        verdict.frame_check = check
        rejection = check.rejection(
            require_hands=require_hands, wanted_viewpoint=wanted_viewpoint
        )
        verdict.trace.add(
            thought="Judge the footage on what the index says is in the frames.",
            action="frame_check",
            action_input={"video_id": video_id, "require_hands": require_hands},
            observation=(
                f"hands={check.hands_visible} ({check.hands_confidence:.2f}), "
                f"viewpoint={check.viewpoint.value}, "
                f"verdict={'keep' if rejection is None else rejection}"
            ),
        )

        # --- the standard's media and rights gates ------------------------
        quality = evaluate_clip(
            license_value=media.get("license") or media.get("license_note"),
            source_url=media.get("source_url"),
            uploader=media.get("uploader"),
            width=media.get("width"),
            height=media.get("height"),
            fps=media.get("fps"),
            duration_seconds=media.get("duration_seconds"),
            container=media.get("container"),
            caption=caption,
            caption_segments=caption_segments,
            require_commercial_use=False,
        )
        verdict.quality = quality
        verdict.idle_seconds = quality.idle_seconds
        verdict.usable_seconds = quality.usable_seconds
        verdict.trace.add(
            thought="Run the media and rights gates from the quality standard.",
            action="quality_gates",
            action_input={"video_id": video_id},
            observation=(
                f"score={quality.score} grade={quality.grade.value} "
                f"blocking={quality.blocking_failures or 'none'} "
                f"unmeasured={len(quality.unmeasured)}"
            ),
        )

        if rejection is None and quality.blocking_failures:
            rejection = "blocking gate failure: " + ", ".join(quality.blocking_failures)

        # --- agentic clipping ---------------------------------------------
        verdict.segments = self.propose_segments(
            caption_segments,
            require_hands=require_hands,
            total_duration=media.get("duration_seconds"),
        )
        verdict.trace.add(
            thought="Find where each action starts and stops, as time anchors.",
            action="propose_segments",
            action_input={"segments_read": len(caption_segments)},
            observation=(
                f"{len(verdict.action_segments)} action anchors over "
                f"{sum(s.duration for s in verdict.action_segments):.1f}s"
                if verdict.segments
                else "no timed caption segments to anchor against"
            ),
        )

        verdict.caption = caption
        verdict.caption_segments = caption_segments
        verdict.rejection_reason = rejection
        verdict.accepted = rejection is None

        if write_back:
            await self._write_back(verdict, check)

        return verdict

    # -------------------------------------------------------- agentic clipping

    def propose_segments(
        self,
        caption_segments: list[dict[str, Any]],
        *,
        require_hands: bool = True,
        total_duration: int | None = None,
        task_label: str | None = None,
    ) -> list[Segment]:
        """Turn timed caption segments into a task → action anchor tree.

        Consecutive segments that show work being done merge into one action;
        idle segments break the run and are excluded. The task span covers the
        actions that survived — which is usually *less* than the whole video,
        and deliberately so: the intro and the outro are not the task.

        Args:
            caption_segments: `[{start, end, text}, …]` from the index.
            require_hands: Only anchor spans with hands in them.
            total_duration: Whole-video duration, used only as a fallback bound.
            task_label: Name for the task level. The annotation agent normally
                supplies this later; it is accepted here for callers that
                already know it.

        Returns:
            `[task, action, action, …]`, or `[]` when there is nothing timed to
            anchor against. Never cut files.
        """
        timed = [
            segment
            for segment in caption_segments
            if segment.get("start") is not None and segment.get("end") is not None
        ]
        if not timed:
            return []
        timed.sort(key=lambda segment: float(segment["start"]))

        runs: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        for segment in timed:
            text = str(segment.get("text") or "")
            hands, evidence = mentions_hands(text)
            idle = bool(mentions_idle(text))
            keep = (hands or not require_hands) and not idle

            if not keep:
                if current:
                    runs.append(current)
                    current = []
                continue

            segment = {**segment, "evidence": evidence, "hands_visible": hands}
            if current:
                gap = float(segment["start"]) - float(current[-1]["end"])
                if gap > self.max_merge_gap_seconds:
                    runs.append(current)
                    current = []
            current.append(segment)
        if current:
            runs.append(current)

        actions: list[Segment] = []
        for index, run in enumerate(runs, start=1):
            start = float(run[0]["start"])
            end = float(run[-1]["end"])
            if end - start < self.min_action_seconds:
                continue
            evidence: list[str] = []
            for segment in run:
                for item in segment.get("evidence", []):
                    if item not in evidence:
                        evidence.append(item)
            actions.append(
                Segment(
                    segment_id=f"t1.a{index}",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=start,
                    span_end=end,
                    hands_visible=any(s.get("hands_visible") for s in run),
                    evidence=evidence[:4],
                    source_text=" ".join(
                        str(s.get("text") or "") for s in run
                    ).strip()[:600],
                )
            )

        if not actions:
            return []

        # Renumber so ids stay contiguous after the short runs were dropped.
        for index, action in enumerate(actions, start=1):
            action.segment_id = f"t1.a{index}"

        task = Segment(
            segment_id="t1",
            parent_segment_id=None,
            hier_level="task",
            span_start=actions[0].span_start,
            span_end=max(action.span_end for action in actions),
            label=task_label,
            hands_visible=any(action.hands_visible for action in actions),
            evidence=[f"{len(actions)} action anchors"],
        )
        if total_duration and task.span_end > total_duration:
            task.span_end = float(total_duration)
        return [task, *actions]

    # --------------------------------------------------------------- plumbing

    async def _read_derived(
        self,
        video_id: str,
        verdict: CleaningVerdict,
    ) -> tuple[str | None, list[dict[str, Any]], str | None, str | None]:
        """Read caption, caption segments, transcription and summary.

        Missing pieces are tolerated. A clip whose captions are not ready yet
        produces an abstention downstream, not a rejection.
        """
        caption: str | None = None
        caption_segments: list[dict[str, Any]] = []
        transcription: str | None = None
        summary: str | None = None

        try:
            payload = await self.client.get_caption(video_id)
            caption = text_of(payload, "caption")
            caption_segments = segments_of(payload, "caption")
        except MemoriesDatalakeError as exc:
            verdict.errors.append(f"caption unavailable: {exc}")

        try:
            payload = await self.client.get_transcription(video_id)
            transcription = text_of(payload, "transcription")
        except MemoriesDatalakeError:
            pass

        try:
            payload = await self.client.get_summary(video_id)
            summary = payload.get("summary") if isinstance(payload, dict) else None
        except MemoriesDatalakeError:
            pass

        verdict.trace.add(
            thought="Read what the index derived from this video.",
            action="get_video_content",
            action_input={"video_id": video_id},
            observation=(
                f"caption {len(caption or '')} chars, "
                f"{len(caption_segments)} timed segments, "
                f"transcription {'yes' if transcription else 'no'}"
            ),
        )
        return caption, caption_segments, transcription, summary

    async def _write_back(self, verdict: CleaningVerdict, check: FrameCheck) -> None:
        """Land the verdict on the video so the next pass can filter on it."""
        tags = [TAG_CLEAN if verdict.accepted else TAG_REJECTED]
        tags.append(TAG_HANDS if check.hands_visible else TAG_NO_HANDS)
        if check.viewpoint == Viewpoint.EGOCENTRIC:
            tags.append(TAG_EGOCENTRIC)
        elif check.viewpoint == Viewpoint.EXOCENTRIC:
            tags.append(TAG_EXOCENTRIC)

        custom: dict[str, Any] = {
            "cleaning": {
                "accepted": verdict.accepted,
                "rejection_reason": verdict.rejection_reason,
                "hands_visible": check.hands_visible,
                "hands_confidence": check.hands_confidence,
                "hand_evidence": check.hand_evidence,
                "viewpoint": check.viewpoint.value,
                "caveat": CAPTION_EVIDENCE_CAVEAT,
            },
            "segments": [segment.as_dict() for segment in verdict.segments],
        }
        if verdict.quality:
            custom["quality"] = verdict.quality.as_dict()

        try:
            await self.client.update_video(verdict.video_id, tags=tags, custom=custom)
            verdict.tags_written = tags
            observation = f"wrote {len(tags)} tags"
        except MemoriesDatalakeError as exc:
            # The judgement stands even if the bookkeeping write failed.
            verdict.errors.append(f"could not write tags: {exc}")
            observation = f"failed: {exc}"

        verdict.trace.add(
            thought="Write the verdict back so the next pass can filter on it.",
            action="update_video",
            action_input={"video_id": verdict.video_id, "tags": tags},
            observation=observation,
        )
