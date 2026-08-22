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
    action_signature,
    check_frames,
    mentions_hands,
)
from video_searching_agent.curation.frame_viewpoint import (
    SightVerdict,
    check_viewpoint,
)
from video_searching_agent.curation.quality_gates import (
    GateCheck,
    QualityReport,
    evaluate_clip,
    mentions_idle,
    mentions_other_people,
    permits_commercial_use,
)
from video_searching_agent.curation.viewpoint import Viewpoint, classify_viewpoint
from video_searching_agent.utils.youtube_urls import youtube_video_id

logger = logging.getLogger(__name__)

AGENT_NAME = "cleaning"

# Clipping bounds. An action shorter than this is noise; a gap longer than this
# is a new action rather than a pause inside one; and an "action" longer than
# this is not an action any more — a single eight-minute span says nothing a
# trainer can use, so a long continuous run is cut at segment boundaries.
MIN_ACTION_SECONDS = 2.0
MAX_MERGE_GAP_SECONDS = 2.0
MAX_ACTION_SECONDS = 120.0

# Tags the cleaning agent writes so the annotation pass has a worklist.
TAG_CLEAN = "clean_pass"
TAG_REJECTED = "clean_rejected"
TAG_HANDS = "hands_visible"
TAG_NO_HANDS = "no_hands"
TAG_EGOCENTRIC = "first_person_view"
TAG_EXOCENTRIC = "third_person_view"


def _looking_enabled() -> bool:
    """Whether this deployment lets the clipping pass examine frames."""

    try:
        from video_searching_agent.config.settings import get_settings

        return bool(get_settings().look_at_frames)
    except Exception:  # noqa: BLE001 - settings are optional here
        return False


def _configured_sight_mode() -> str:
    """How hard to look before downloading: ``off``, ``frames`` or ``watch``.

    Defaults to ``frames``, which is the tier that costs about a fifth of a
    cent. ``watch`` has Gemini watch the whole video and cost $0.26 for ten
    minutes of footage in testing, so it is never the default.
    """
    try:
        from video_searching_agent.config.settings import get_settings

        return get_settings().viewpoint_check
    except Exception:  # noqa: BLE001 - settings are optional here
        return "frames"


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
    notes: list[str] = field(default_factory=list)
    # What the frames showed, when they were looked at at all.
    sight: SightVerdict | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "accepted": self.accepted,
            "reasons": self.reasons,
            "viewpoint": self.viewpoint.value,
            "viewpoint_confidence": self.viewpoint_confidence,
            "duration_seconds": self.duration_seconds,
            "commercial_use_ok": self.commercial_use_ok,
            "notes": self.notes,
            "sight": self.sight.as_dict() if self.sight else None,
            "checks": [check.as_dict() for check in self.checks],
        }


@dataclass
class CleaningVerdict:
    """The post-index filter's answer, plus the clipping it produced."""

    video_id: str
    # What examining frames cost on this clip, so a run's looking is accountable
    # rather than absorbed silently.
    look_cost_usd: float = 0.0
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
        max_action_seconds: float = MAX_ACTION_SECONDS,
        llm: Any | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            client: Datalake client. Created on first use when omitted.
            min_action_seconds: Shortest span worth anchoring.
            max_merge_gap_seconds: Longest pause that still counts as one action.
            max_action_seconds: Longest span still called one action.
            llm: The model that looks at frames before a download. Built from
                settings on first use; pass ``False`` to look at nothing.
        """
        self._client = client
        self.min_action_seconds = min_action_seconds
        self.max_merge_gap_seconds = max_merge_gap_seconds
        self.max_action_seconds = max_action_seconds
        self._llm = llm
        self._llm_resolved = llm is not None
        self._clipping: Any | None = None

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def llm(self) -> Any | None:
        """The model used for the pre-download look, if one can be built.

        Resolved once and cached, including the failure: a run with no model
        configured should skip the look quietly rather than try on every
        candidate.
        """
        if not self._llm_resolved:
            self._llm_resolved = True
            try:
                from video_searching_agent.api.llm import get_llm_client

                self._llm = get_llm_client()
            except Exception as exc:  # noqa: BLE001 - looking is optional
                logger.info("no model for the frame check: %s", exc)
                self._llm = None
        return self._llm or None

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
        verdict.duration_seconds = int(duration) if isinstance(duration, int | float) else None

        tags = [str(tag) for tag in (info.get("tags") or info.get("categories") or [])]
        reading = classify_viewpoint(
            title=info.get("title"),
            description=info.get("description"),
            tags=tags,
        )
        verdict.viewpoint = reading.viewpoint
        verdict.viewpoint_confidence = reading.confidence

        licence = info.get("license") or info.get("licence")
        verdict.commercial_use_ok = permits_commercial_use(str(licence) if licence else None)
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
                verdict.viewpoint != Viewpoint.UNKNOWN and verdict.viewpoint != wanted_viewpoint
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
            verdict.reasons.append("licence does not clearly permit commercial training use")

        verdict.accepted = not verdict.reasons
        return verdict

    async def look(
        self,
        verdict: ScreeningVerdict,
        info: dict[str, Any],
        *,
        wanted_viewpoint: Viewpoint | None = None,
        mode: str | None = None,
    ) -> ScreeningVerdict:
        """Look at the candidate's own frames, and fold what was seen into
        the verdict.

        This is the layer the metadata screen cannot be: a title says
        "POV cooking", the frames say a tripod pointed at a worktop. Cheap
        enough to run on every candidate — about $0.002 and a second or two —
        and it runs *before* the download, so being wrong about a video costs
        that instead of a download, an upload, an index and a caption pass.

        It only ever rejects on a confident, opposite reading. Silence,
        abstention and a weak guess all pass through, because the caption
        evidence after indexing sees the whole video rather than three moments
        of it and has the better claim to the last word.
        """
        resolved = mode or _configured_sight_mode()
        if resolved == "off" or self.llm is None:
            return verdict

        video_id = youtube_video_id(info.get("webpage_url") or info.get("url") or "")
        seen = await check_viewpoint(
            self.llm,
            video_id=video_id,
            video_url=info.get("webpage_url") or info.get("url"),
            mode=resolved,
        )
        verdict.sight = seen
        if not seen.looked:
            # Nothing was seen, so nothing changes — but say why, so a run that
            # silently stopped looking is visible in the record.
            if seen.error:
                verdict.notes.append(f"frame check did not run: {seen.error}")
            return verdict

        contradicted = seen.contradicts(wanted_viewpoint)
        verdict.checks.append(
            GateCheck(
                "PRE-SIGHT",
                "The footage itself shows the viewpoint asked for",
                passed=not contradicted,
                blocking=True,
                value=f"{seen.viewpoint.value} ({seen.confidence:.2f}, {seen.method})",
                threshold=(
                    f"{wanted_viewpoint.value} or unclear"
                    if wanted_viewpoint
                    else "no viewpoint requested"
                ),
            )
        )
        if contradicted:
            verdict.reasons.append(
                f"the frames show {seen.viewpoint.value} footage"
                + (f": {seen.why}" if seen.why else "")
            )
            verdict.accepted = False
        elif seen.viewpoint != Viewpoint.UNKNOWN:
            # A confident agreement is worth recording: it is the difference
            # between a licence-clear guess and a checked match.
            verdict.viewpoint = seen.viewpoint
            verdict.viewpoint_confidence = max(verdict.viewpoint_confidence, seen.confidence)
        if seen.hands_visible is False and seen.confidence >= 0.6:
            verdict.notes.append("no hands in the sampled frames; the caption pass decides")
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

        # Resolved once, here, and used everywhere below. It decides three
        # separate things — whether the caption read returns timings at all,
        # what the media gates measure, and where anchors get clamped — so
        # reading it from `media` in three places meant a curation run with no
        # download behind it silently lost all three. The clamp was the last to
        # notice: an anchor came back ending at 1229.0s on a 1228.0s video.
        duration = media.get("duration_seconds")
        if not duration:
            duration = await self._duration_of(video_id, verdict)
        if duration:
            media = {**media, "duration_seconds": duration}

        caption, caption_segments, transcription, summary = await self._read_derived(
            video_id, verdict, duration_seconds=duration
        )

        # --- the frame check: does the footage show what we need? ----------
        check = check_frames(
            caption=caption,
            transcription=transcription,
            summary=summary,
            title=title,
        )
        verdict.frame_check = check
        rejection = check.rejection(require_hands=require_hands, wanted_viewpoint=wanted_viewpoint)
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
        # The walk has never seen the footage. Where looking is available and
        # affordable, the clipping agent checks its boundaries against frames
        # and corrects them; where it is not, the walk stands and the record
        # says so.
        verdict.segments = await self._refine_anchors(
            video_id, verdict, duration=duration
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

    async def _refine_anchors(
        self,
        video_id: str,
        verdict: CleaningVerdict,
        duration: float | None,
    ) -> list[Segment]:
        """Let the clipping agent look at the proposed boundaries.

        Returns the anchors to keep — the refined ones when the agent ran and
        converged, the walk's own when it did not. A refinement that fails is
        not a reason to lose the anchors: the walk's boundaries are rough, not
        wrong.

        Task and event anchors are left alone. The agent works at action level,
        which is the level whose boundaries the walk actually guesses at, and
        the task span is recomputed from what comes back so it still covers its
        children.
        """
        # Deliberately `self._llm` and not the `llm` property: refinement uses a
        # model it was *given*, and never goes and resolves one. Resolving here
        # turned four offline unit tests into real API calls, and more to the
        # point it made an expensive network round trip a hidden side effect of
        # calling clean(). The pipeline hands one in; a bare agent stays offline.
        if not _looking_enabled() or self._llm is None or self._llm is False:
            return verdict.segments

        actions = [s for s in verdict.segments if s.hier_level == "action"]
        if not actions:
            return verdict.segments

        try:
            from video_searching_agent.agent.clipping_agent import ClippingAgent

            agent = self._clipping or ClippingAgent(client=self.client, llm=self._llm)
            self._clipping = agent
            result = await agent.refine(
                video_id,
                [s.as_dict() for s in actions],
                duration_seconds=duration,
                min_span_seconds=self.min_action_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - the walk still stands
            verdict.errors.append(f"clipping agent unavailable: {str(exc)[:150]}")
            return verdict.segments

        verdict.trace.add(
            thought="The walk has never seen the footage; check its boundaries.",
            action="refine_anchors",
            action_input={"proposed": result.proposed},
            observation=(
                f"{len(result.spans)} spans, {result.examined} examined, "
                f"{result.looks} looks, ${result.cost_usd:.4f}"
                + (f", fell back: {result.notes}" if result.fell_back else "")
            ),
        )
        verdict.look_cost_usd += result.cost_usd
        if result.fell_back or not result.spans:
            return verdict.segments

        refined: list[Segment] = []
        for index, span in enumerate(result.spans, start=1):
            refined.append(
                Segment(
                    segment_id=f"t1.a{index}",
                    parent_segment_id="t1",
                    hier_level="action",
                    span_start=span.start,
                    span_end=span.end,
                    hands_visible=True,
                    evidence=[span.why] if span.why else ["checked against frames"],
                )
            )
        task = Segment(
            segment_id="t1",
            parent_segment_id=None,
            hier_level="task",
            span_start=min(span.span_start for span in refined),
            span_end=max(span.span_end for span in refined),
            hands_visible=True,
            evidence=[f"{len(refined)} action anchors"],
        )
        return [task, *refined]

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
                A run also ends when the action itself changes.
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
            # A span with someone else in it is dropped rather than anchored:
            # their hands and face are not the wearer's, whatever else is right
            # about the footage.
            others = bool(mentions_other_people(text))
            keep = (hands or not require_hands) and not idle and not others

            if not keep:
                if current:
                    runs.append(current)
                    current = []
                continue

            signature = action_signature(text)
            segment = {
                **segment,
                "evidence": evidence,
                "hands_visible": hands,
                "signature": signature,
            }
            if current:
                gap = float(segment["start"]) - float(current[-1]["end"])
                previous = current[-1].get("signature") or set()
                # Two reasons to start a new action: a real pause, or a change
                # of action. Without the second, one continuous take of
                # chopping-then-stirring collapses into a single anchor that
                # says nothing.
                changed_action = bool(previous and signature and not (previous & signature))
                if gap > self.max_merge_gap_seconds or changed_action:
                    runs.append(current)
                    current = []
            current.append(segment)
        if current:
            runs.append(current)

        # A run of segments that never changes action can still be far too long
        # to call one action, so it is cut at segment boundaries first.
        runs = [chunk for run in runs for chunk in self._cap_run_length(run)]

        actions: list[Segment] = []
        previous_end = 0.0
        for index, run in enumerate(runs, start=1):
            start = float(run[0]["start"])
            end = float(run[-1]["end"])
            # Caption segments can overlap by a hair. Left alone that becomes a
            # sibling overlap in the tree, which fails G2-TREE-2.
            start = max(start, previous_end)
            if total_duration:
                end = min(end, float(total_duration))
            if end - start < self.min_action_seconds:
                continue
            previous_end = end
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
                    source_text=" ".join(str(s.get("text") or "") for s in run).strip()[:600],
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

    def _cap_run_length(self, run: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Cut a run into chunks no longer than `max_action_seconds`.

        The cut always lands on a caption-segment boundary — an anchor should
        never claim a boundary the index did not give us.
        """
        if not run:
            return []
        chunks: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        for segment in run:
            if current:
                span = float(segment["end"]) - float(current[0]["start"])
                if span > self.max_action_seconds:
                    chunks.append(current)
                    current = []
            current.append(segment)
        if current:
            chunks.append(current)
        return chunks

    # --------------------------------------------------------------- plumbing

    async def _duration_of(
        self, video_id: str, verdict: CleaningVerdict
    ) -> float | None:
        """Ask the Datalake how long a video is.

        Cheap, and it is the difference between timed caption segments and none.
        A failure here is not a rejection: the read falls back to the untimed
        whole-video caption, which still supports the frame check even though it
        cannot support anchors.
        """
        try:
            record = await self.client.get_video(video_id)
        except MemoriesDatalakeError as exc:
            verdict.errors.append(f"duration unavailable: {exc}")
            return None
        if not isinstance(record, dict):
            return None
        for key in ("duration_seconds", "duration", "durationSeconds"):
            value = record.get(key)
            if isinstance(value, int | float) and value > 0:
                return float(value)
            if isinstance(value, str):
                try:
                    parsed = float(value)
                except ValueError:
                    continue
                if parsed > 0:
                    return parsed
        return None

    async def _read_derived(
        self,
        video_id: str,
        verdict: CleaningVerdict,
        duration_seconds: int | float | None = None,
    ) -> tuple[str | None, list[dict[str, Any]], str | None, str | None]:
        """Read caption, caption segments, transcription and summary.

        The window matters: asked for a whole video, the caption endpoint
        returns one aggregated string with no timings, and there is nothing to
        anchor against. Asked for a `[start, end]` window it returns timed
        segments — so when the duration is known, the whole video is requested
        *as* a window.

        The duration therefore decides whether this pass can produce anchors at
        all, and it is not always handed in. A collection run knows it from the
        download; a curation run over already-indexed videos does not, and
        without it every clip came back with a caption and *no timed segments* —
        which is exactly how five task queries produced six accepted clips and
        zero anchors between them. So when it is not supplied, it is asked for.

        Missing pieces are tolerated. A clip whose captions are not ready yet
        produces an abstention downstream, not a rejection.
        """
        caption: str | None = None
        caption_segments: list[dict[str, Any]] = []
        transcription: str | None = None
        summary: str | None = None

        if not duration_seconds:
            duration_seconds = await self._duration_of(video_id, verdict)

        try:
            if duration_seconds:
                payload = await self.client.get_caption(
                    video_id, start=0, end=float(duration_seconds)
                )
                caption_segments = segments_of(payload, "caption")
                caption = text_of(payload, "caption")
            if not caption_segments:
                payload = await self.client.get_caption(video_id)
                caption = text_of(payload, "caption") or caption
                caption_segments = caption_segments or segments_of(payload, "caption")
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
