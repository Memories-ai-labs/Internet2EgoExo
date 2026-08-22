"""The quality-check agent: audit the clips that actually came out.

The other three agents each make a judgement and then act on it. This one makes
no judgements of its own about footage — it audits *their output*, adversarially,
and it is allowed to fail a clip that all three of them accepted.

That independence is the whole point. A pipeline that grades its own homework
will tell you a dataset is fine in exactly the cases where its own reasoning was
wrong: the anchor whose annotation describes something the captions never
mention, the "task" whose children sit outside it, the fifty clips that turn out
to be the same twelve videos. Nothing here re-reads the footage or re-scores a
gate. It asks a narrower and harsher question of the finished artefact:

    *If someone handed me this dataset, would I accept it?*

Three kinds of check, cheapest first:

**Arithmetic and structure** (free). Does an anchor lie inside its video? Do
children lie inside their parents, and siblings not overlap? Is every anchor
above the minimum action length? Do the hours the manifest claims equal the sum
of the anchors it lists? Does a clip's tree have a level whose text was copied
from its parent? Is hand assignment either stated or absent, never invented?

**Evidence** (one model call per annotated span). The annotation says the hands
pick up a soldering iron between 0:42 and 0:58. Do the captions *for that
window* support that? This is the check that catches a plausible label attached
to the wrong seconds, and it is asked as a refutation — the model is told to
look for the reason this label is wrong, because a model asked to confirm will.

**The set** (free). Duplicates and near-duplicates across clips, the viewpoint
mix against what was asked for, and whether the delivered hours are concentrated
in a handful of long videos — a dataset of fifty clips from three recordings is
not a dataset of fifty clips.

Every finding names the clip, the span and what the evidence actually said. A
finding with no evidence behind it is a bug in this agent, not a finding.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.react import AgentTrace, parse_json_object, segments_of
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.curation.frame_check import action_signature
from video_searching_agent.curation.viewpoint import Viewpoint

logger = logging.getLogger(__name__)

AGENT_NAME = "quality_check"

# An anchor shorter than this is not an action; the cleaning agent already drops
# them, so one arriving here means the boundary logic let it through.
MIN_ANCHOR_SECONDS = 2.0

# A span this long is not one action either, whatever it is labelled.
MAX_ANCHOR_SECONDS = 180.0

# Two anchors overlapping by less than this are touching, not overlapping — a
# rounding artefact rather than a real fault.
OVERLAP_TOLERANCE_SECONDS = 0.05

# Below this share of clips coming from distinct source videos, a set is a few
# recordings wearing fifty hats.
MIN_SOURCE_DIVERSITY = 0.4

REFUTE_PROMPT = """You are auditing one annotation against the evidence behind it.

The annotation claims that between {start} and {end} of a video, this happens:

    {label}
    {narration}

These are the caption segments the index produced for that window:

{evidence}

Your job is to find the reason this annotation is WRONG, if there is one. Be
specific and be hard to please, but do not invent a fault: if the captions
support the claim, say so.

Reply with JSON only:
{{"supported": true | false,
  "confidence": 0.0-1.0,
  "problem": "what the captions say that contradicts the claim, or empty"}}

Answer "supported": false only when the captions actively contradict the claim
or describe something else entirely. Captions that are merely vaguer than the
annotation still support it — an index that says "hands work on the board" does
not contradict "solders a joint". Silence is not contradiction: if the window
has no captions at all, say supported true with confidence 0.0, because there is
nothing to judge against."""


@dataclass
class Finding:
    """One thing wrong with the delivered dataset."""

    clip: str
    check: str
    detail: str
    severity: str = "fail"  # fail | warn
    span: tuple[float, float] | None = None
    evidence: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "clip": self.clip,
            "check": self.check,
            "detail": self.detail,
            "severity": self.severity,
            "span": list(self.span) if self.span else None,
            "evidence": self.evidence,
        }


@dataclass
class ClipAudit:
    """The verdict on one delivered clip."""

    video_id: str
    title: str | None = None
    anchors_checked: int = 0
    spans_verified: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(f.severity == "fail" for f in self.findings)

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "passed": self.passed,
            "anchors_checked": self.anchors_checked,
            "spans_verified": self.spans_verified,
            "findings": [f.as_dict() for f in self.findings],
        }


@dataclass
class QualityAudit:
    """The verdict on the whole delivered set."""

    clips: list[ClipAudit] = field(default_factory=list)
    set_findings: list[Finding] = field(default_factory=list)
    trace: AgentTrace = field(default_factory=lambda: AgentTrace(agent=AGENT_NAME))
    cost_usd: float = 0.0

    @property
    def clips_passed(self) -> int:
        return sum(1 for clip in self.clips if clip.passed)

    @property
    def passed(self) -> bool:
        """Whether the set is deliverable.

        A set fails when anything at set level fails, or when any clip in it
        does. There is no partial credit: a dataset with a wrong label in it is
        a dataset somebody will train on.
        """
        return not any(f.severity == "fail" for f in self.set_findings) and all(
            clip.passed for clip in self.clips
        )

    @property
    def verdict(self) -> str:
        if self.passed:
            return "accept"
        failures = sum(1 for f in self.all_findings() if f.severity == "fail")
        return f"reject ({failures} failing checks)"

    def all_findings(self) -> list[Finding]:
        return [*self.set_findings, *(f for clip in self.clips for f in clip.findings)]

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "passed": self.passed,
            "clips_total": len(self.clips),
            "clips_passed": self.clips_passed,
            "cost_usd": round(self.cost_usd, 5),
            "set_findings": [f.as_dict() for f in self.set_findings],
            "clips": [clip.as_dict() for clip in self.clips],
            "trace": self.trace.as_list(),
        }


class QualityCheckAgent:
    """Audits delivered clips against the standard, independently."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        llm: Any | None = None,
        min_anchor_seconds: float = MIN_ANCHOR_SECONDS,
        max_anchor_seconds: float = MAX_ANCHOR_SECONDS,
    ) -> None:
        """Initialize the agent.

        Args:
            client: Datalake client, for reading the captions an annotation is
                checked against. Created on first use when omitted.
            llm: The model that tries to refute a label. ``False`` audits
                structure only, which is free.
            min_anchor_seconds: Shortest anchor that is still an action.
            max_anchor_seconds: Longest span still called one action.
        """
        self._client = client
        self._llm = llm
        self._llm_resolved = llm is not None
        self.min_anchor_seconds = min_anchor_seconds
        self.max_anchor_seconds = max_anchor_seconds

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def llm(self) -> Any | None:
        if not self._llm_resolved:
            self._llm_resolved = True
            try:
                from video_searching_agent.api.llm import get_llm_client

                self._llm = get_llm_client()
            except Exception as exc:  # noqa: BLE001 - the evidence pass is optional
                logger.info("no model for the evidence audit: %s", exc)
                self._llm = None
        return self._llm or None

    async def audit(
        self,
        clips: list[dict[str, Any]],
        *,
        wanted_viewpoint: Viewpoint | None = None,
        claimed_hours: float | None = None,
        verify_evidence: bool = True,
        max_spans_per_clip: int = 4,
    ) -> QualityAudit:
        """Audit the delivered clips.

        Args:
            clips: What the pipeline delivered. Each needs `video_id`, and may
                carry `title`, `duration_seconds`, `viewpoint`, `segments`
                (the anchors) and `annotations`.
            wanted_viewpoint: What the collection asked for, so a set that
                drifted can be caught.
            claimed_hours: The hours the manifest reports, checked against the
                anchors actually listed.
            verify_evidence: Ask the model to refute labels. False is free.
            max_spans_per_clip: How many spans per clip to verify. The spans are
                sampled across the clip rather than taken from the front, so a
                clip whose later anchors drift is not missed.

        Returns:
            A QualityAudit. `passed` False means do not ship this set.
        """
        audit = QualityAudit()

        for clip in clips:
            result = await self._audit_clip(
                clip,
                wanted_viewpoint=wanted_viewpoint,
                verify_evidence=verify_evidence,
                max_spans=max_spans_per_clip,
                audit=audit,
            )
            audit.clips.append(result)

        self._audit_set(
            clips, audit, wanted_viewpoint=wanted_viewpoint, claimed_hours=claimed_hours
        )
        audit.trace.add(
            thought="A pipeline that grades its own homework passes itself.",
            action="audit",
            action_input={"clips": len(clips), "evidence": verify_evidence},
            observation=(
                f"{audit.verdict}; {audit.clips_passed}/{len(audit.clips)} clips passed, "
                f"{len(audit.all_findings())} findings"
            ),
        )
        return audit

    # ------------------------------------------------------------ per clip

    async def _audit_clip(
        self,
        clip: dict[str, Any],
        *,
        wanted_viewpoint: Viewpoint | None,
        verify_evidence: bool,
        max_spans: int,
        audit: QualityAudit,
    ) -> ClipAudit:
        video_id = str(clip.get("video_id") or clip.get("datalake_video_id") or "unknown")
        result = ClipAudit(video_id=video_id, title=clip.get("title"))
        duration = _as_float(clip.get("duration_seconds"))
        anchors = [a for a in (clip.get("segments") or []) if isinstance(a, dict)]
        annotations = [a for a in (clip.get("annotations") or []) if isinstance(a, dict)]
        result.anchors_checked = len(anchors)

        self._check_bounds(result, anchors, duration)
        self._check_tree(result, anchors)
        self._check_annotation_text(result, annotations)
        self._check_viewpoint(result, clip, wanted_viewpoint)

        if verify_evidence and annotations and self.llm is not None:
            await self._check_evidence(result, video_id, annotations, max_spans, audit)
        return result

    def _check_bounds(
        self, result: ClipAudit, anchors: list[dict[str, Any]], duration: float | None
    ) -> None:
        """An anchor has to lie inside the video and be an action-sized span."""

        for anchor in anchors:
            start, end = _span(anchor)
            if start is None or end is None:
                result.findings.append(
                    Finding(result.video_id, "ANCHOR-SPAN", "anchor has no usable span")
                )
                continue
            if end <= start:
                result.findings.append(
                    Finding(
                        result.video_id,
                        "ANCHOR-ORDER",
                        f"anchor ends at or before it starts ({start:.2f} → {end:.2f})",
                        span=(start, end),
                    )
                )
                continue
            length = end - start
            if length < self.min_anchor_seconds:
                result.findings.append(
                    Finding(
                        result.video_id,
                        "ANCHOR-SHORT",
                        f"{length:.2f}s is below the {self.min_anchor_seconds}s floor",
                        span=(start, end),
                    )
                )
            if length > self.max_anchor_seconds and anchor.get("hier_level") == "action":
                result.findings.append(
                    Finding(
                        result.video_id,
                        "ANCHOR-LONG",
                        f"{length:.0f}s is one 'action', over the "
                        f"{self.max_anchor_seconds:.0f}s ceiling",
                        severity="warn",
                        span=(start, end),
                    )
                )
            if duration and end > duration + 0.5:
                result.findings.append(
                    Finding(
                        result.video_id,
                        "ANCHOR-OVERRUN",
                        f"anchor ends at {end:.2f}s, past the video's {duration:.2f}s",
                        span=(start, end),
                    )
                )

    def _check_tree(self, result: ClipAudit, anchors: list[dict[str, Any]]) -> None:
        """G2-TREE-1 and G2-TREE-2, checked on what was delivered."""

        by_id = {str(a.get("segment_id")): a for a in anchors if a.get("segment_id")}

        for anchor in anchors:
            parent_id = anchor.get("parent_segment_id")
            if not parent_id:
                continue
            parent = by_id.get(str(parent_id))
            if parent is None:
                result.findings.append(
                    Finding(
                        result.video_id,
                        "TREE-ORPHAN",
                        f"parent {parent_id} is not in the delivered tree",
                    )
                )
                continue
            start, end = _span(anchor)
            p_start, p_end = _span(parent)
            if None in (start, end, p_start, p_end):
                continue
            if start < p_start - 0.5 or end > p_end + 0.5:
                result.findings.append(
                    Finding(
                        result.video_id,
                        "G2-TREE-1",
                        f"child {start:.2f}–{end:.2f} is outside its parent "
                        f"{p_start:.2f}–{p_end:.2f}",
                        span=(start, end),
                    )
                )

        # Siblings, level by level, must not overlap.
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for anchor in anchors:
            key = (str(anchor.get("parent_segment_id") or ""), str(anchor.get("hier_level") or ""))
            groups.setdefault(key, []).append(anchor)
        for (_, level), group in groups.items():
            spans = sorted(
                (s for s in (_span(a) for a in group) if s[0] is not None and s[1] is not None),
                key=lambda s: s[0],  # type: ignore[arg-type,index]
            )
            for earlier, later in zip(spans, spans[1:], strict=False):
                if later[0] < earlier[1] - OVERLAP_TOLERANCE_SECONDS:  # type: ignore[operator]
                    result.findings.append(
                        Finding(
                            result.video_id,
                            "G2-TREE-2",
                            f"two {level or 'sibling'} spans overlap: "
                            f"{earlier[0]:.2f}–{earlier[1]:.2f} and "
                            f"{later[0]:.2f}–{later[1]:.2f}",
                            span=(later[0], later[1]),  # type: ignore[arg-type]
                        )
                    )

    def _check_annotation_text(self, result: ClipAudit, annotations: list[dict[str, Any]]) -> None:
        """G2-TREE-3, and the rule that hand assignment is never invented."""

        by_id = {str(a.get("segment_id")): a for a in annotations if a.get("segment_id")}
        for annotation in annotations:
            text = _text_of(annotation)
            parent_id = annotation.get("parent_segment_id")
            if parent_id and text:
                parent_text = _text_of(by_id.get(str(parent_id)) or {})
                if parent_text and text.strip().lower() == parent_text.strip().lower():
                    result.findings.append(
                        Finding(
                            result.video_id,
                            "G2-TREE-3",
                            f"a level repeats its parent's words verbatim: {text[:70]!r}",
                        )
                    )

            # A hand named without evidence is the one invention that matters,
            # because it is the label a manipulation model learns from.
            for side in ("left_hand", "right_hand"):
                claim = annotation.get(side)
                if not claim:
                    continue
                if not str(claim).strip():
                    result.findings.append(
                        Finding(
                            result.video_id,
                            "HAND-EMPTY",
                            f"{side} is present but blank, which reads as a claim",
                            severity="warn",
                        )
                    )

    def _check_viewpoint(
        self, result: ClipAudit, clip: dict[str, Any], wanted: Viewpoint | None
    ) -> None:
        if wanted is None:
            return
        raw = str(clip.get("viewpoint") or "").lower()
        if raw and raw not in (wanted.value, "unknown"):
            result.findings.append(
                Finding(
                    result.video_id,
                    "VIEWPOINT-DRIFT",
                    f"delivered as {raw} for a {wanted.value} collection",
                )
            )

    async def _check_evidence(
        self,
        result: ClipAudit,
        video_id: str,
        annotations: list[dict[str, Any]],
        max_spans: int,
        audit: QualityAudit,
    ) -> None:
        """Try to refute each sampled label from the captions for its window."""

        labelled = [
            a
            for a in annotations
            if _text_of(a) and _span(a)[0] is not None and _span(a)[1] is not None
        ]
        if not labelled:
            return
        for annotation in _sample_across(labelled, max_spans):
            start, end = _span(annotation)
            assert start is not None and end is not None
            evidence = await self._captions_for(video_id, start, end)
            if not evidence:
                # Nothing to judge against is not a fault, but it is worth
                # saying: an annotation with no caption behind it is a claim
                # resting on the model's memory of the video.
                result.findings.append(
                    Finding(
                        video_id,
                        "EVIDENCE-NONE",
                        "no captions cover this span, so the label rests on nothing checkable",
                        severity="warn",
                        span=(start, end),
                    )
                )
                continue

            verdict, cost = await self._refute(annotation, start, end, evidence)
            audit.cost_usd += cost
            result.spans_verified += 1
            if verdict is None:
                continue
            if not verdict.get("supported", True):
                result.findings.append(
                    Finding(
                        video_id,
                        "EVIDENCE-CONTRADICTED",
                        str(verdict.get("problem") or "the captions describe something else"),
                        span=(start, end),
                        evidence=evidence[:300],
                    )
                )

    async def _captions_for(self, video_id: str, start: float, end: float) -> str:
        """Caption text for one window, which is the only honest evidence here.

        A whole-video read comes back with no timings, so the window has to be
        asked for explicitly — the same contract the cleaning agent works to.
        """
        try:
            payload = await self.client.get_caption(video_id, start=start, end=end)
        except MemoriesDatalakeError as exc:
            logger.info("captions unavailable for %s: %s", video_id, exc)
            return ""
        segments = segments_of(payload, "caption")
        lines = []
        for segment in segments:
            text = str(segment.get("text") or "").strip()
            if text:
                lines.append(f"[{segment.get('start')}–{segment.get('end')}] {text}")
        return "\n".join(lines)

    async def _refute(
        self, annotation: dict[str, Any], start: float, end: float, evidence: str
    ) -> tuple[dict[str, Any] | None, float]:
        prompt = REFUTE_PROMPT.format(
            start=f"{start:.1f}s",
            end=f"{end:.1f}s",
            label=annotation.get("label") or "(no label)",
            narration=annotation.get("narration") or "",
            evidence=evidence[:4000],
        )
        client = self.llm
        if client is None:
            return None, 0.0
        try:
            messages = client.new_conversation(prompt)
            response = await client.create_message_async(messages, max_tokens=500)
        except Exception as exc:  # noqa: BLE001 - a failed audit call is not a finding
            logger.info("refutation call failed: %s", exc)
            return None, 0.0

        cost = 0.0
        if hasattr(client, "get_cost_usd"):
            try:
                cost = float(client.get_cost_usd(response) or 0.0)
            except Exception:  # noqa: BLE001
                cost = 0.0
        text = ""
        if hasattr(client, "get_text_response"):
            text = client.get_text_response(response) or ""
        try:
            return parse_json_object(text), cost
        except Exception:  # noqa: BLE001 - an unreadable answer is not a finding
            return None, cost

    # ------------------------------------------------------------- per set

    def _audit_set(
        self,
        clips: list[dict[str, Any]],
        audit: QualityAudit,
        *,
        wanted_viewpoint: Viewpoint | None,
        claimed_hours: float | None,
    ) -> None:
        if not clips:
            audit.set_findings.append(Finding("(set)", "SET-EMPTY", "nothing was delivered"))
            return

        # A set of clips with no anchors in any of them is not a dataset, and
        # this audit passed exactly that — five task queries, six accepted
        # clips, zero anchors, verdict "accept" on all five, because there were
        # no labels to find fault with. Nothing to audit is not the same as
        # nothing wrong.
        anchored = sum(
            1 for clip in clips if any(isinstance(a, dict) for a in (clip.get("segments") or []))
        )
        if anchored == 0:
            audit.set_findings.append(
                Finding(
                    "(set)",
                    "SET-NO-ANCHORS",
                    f"{len(clips)} clips delivered and not one action anchor between "
                    "them — there is nothing here to train on",
                )
            )
        elif anchored < len(clips) / 2:
            audit.set_findings.append(
                Finding(
                    "(set)",
                    "SET-THIN-ANCHORS",
                    f"only {anchored} of {len(clips)} clips carry any anchor",
                    severity="warn",
                )
            )

        # Fifty clips from three recordings is not fifty clips.
        sources = {
            str(clip.get("source_url") or clip.get("url") or clip.get("video_id")) for clip in clips
        }
        ratio = len(sources) / len(clips)
        if len(clips) > 4 and ratio < MIN_SOURCE_DIVERSITY:
            audit.set_findings.append(
                Finding(
                    "(set)",
                    "SET-CONCENTRATED",
                    f"{len(clips)} clips come from only {len(sources)} sources "
                    f"({ratio:.0%} distinct)",
                    severity="warn",
                )
            )

        # The same action described twice at the same seconds of the same video
        # is one anchor delivered twice. The *level* is part of that identity: a
        # video with one action has a task anchor and an action anchor over the
        # same seconds, by design, and calling that a duplicate cried wolf on
        # every short clip.
        seen: set[tuple[str, str, int, int, frozenset[str]]] = set()
        for clip in clips:
            video_id = str(clip.get("video_id") or "")
            for anchor in clip.get("segments") or []:
                if not isinstance(anchor, dict):
                    continue
                start, end = _span(anchor)
                if start is None or end is None:
                    continue
                key = (
                    video_id,
                    str(anchor.get("hier_level") or ""),
                    int(start),
                    int(end),
                    frozenset(action_signature(str(anchor.get("label") or ""))),
                )
                if key in seen:
                    audit.set_findings.append(
                        Finding(
                            video_id,
                            "SET-DUPLICATE",
                            f"the same span {start:.1f}–{end:.1f} is delivered twice",
                            span=(start, end),
                        )
                    )
                seen.add(key)

        if claimed_hours is not None:
            # Summing every anchor double-counts, because a task anchor contains
            # its actions and an action contains its events — 16 seconds of
            # footage with one action in it totalled 32. The honest figure is the
            # union of the action-level spans: the seconds actually covered,
            # counted once.
            anchored = sum(_covered_seconds(clip) for clip in clips)
            anchored_hours = anchored / 3600
            # Anchors are a subset of the footage, so they should never exceed
            # the hours claimed. Exceeding it means something is double counted.
            if anchored_hours > claimed_hours + 0.01:
                audit.set_findings.append(
                    Finding(
                        "(set)",
                        "SET-HOURS",
                        f"anchors total {anchored_hours:.3f}h but the manifest "
                        f"claims {claimed_hours:.3f}h delivered",
                    )
                )

        if wanted_viewpoint:
            drifted = sum(
                1
                for clip in clips
                if str(clip.get("viewpoint") or "").lower()
                not in (wanted_viewpoint.value, "unknown", "")
            )
            if drifted and drifted / len(clips) > 0.2:
                audit.set_findings.append(
                    Finding(
                        "(set)",
                        "SET-VIEWPOINT",
                        f"{drifted} of {len(clips)} clips are not {wanted_viewpoint.value}",
                    )
                )


# ----------------------------------------------------------------- helpers


def _covered_seconds(clip: dict[str, Any]) -> float:
    """Seconds of footage a clip's anchors cover, counted once.

    Anchors nest — a task contains its actions, an action contains its events —
    so adding their lengths counts the same footage two or three times. This
    merges the action-level spans and measures the union, falling back to
    whatever level is present when there are no actions.
    """
    anchors = [a for a in (clip.get("segments") or []) if isinstance(a, dict)]
    actions = [a for a in anchors if str(a.get("hier_level") or "") == "action"]
    chosen = actions or anchors
    spans = sorted(
        (
            (start, end)
            for start, end in (_span(a) for a in chosen)
            if start is not None and end is not None and end > start
        ),
        key=lambda pair: pair[0],
    )
    if not spans:
        return 0.0

    total = 0.0
    current_start, current_end = spans[0]
    for start, end in spans[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    return total + (current_end - current_start)


def _span(entry: dict[str, Any]) -> tuple[float | None, float | None]:
    """The [start, end] of an anchor or annotation, whichever names it."""

    start = _as_float(_first_present(entry, "span_start", "start", "start_time", "start_seconds"))
    end = _as_float(_first_present(entry, "span_end", "end", "end_time", "end_seconds"))
    return start, end


def _first_present(entry: dict[str, Any], *keys: str) -> Any:
    """The first key that is present, including when its value is zero."""

    for key in keys:
        if key in entry and entry[key] is not None:
            return entry[key]
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text_of(annotation: dict[str, Any]) -> str:
    return str(annotation.get("label") or annotation.get("narration") or "")


def _sample_across(items: list[Any], count: int) -> list[Any]:
    """Up to `count` items spread across the list, not taken from the front.

    A clip's later anchors are the ones most likely to have drifted, so an audit
    that always reads the first few would systematically miss them.
    """
    if count <= 0 or not items:
        return []
    if len(items) <= count:
        return list(items)
    step = len(items) / count
    return [items[min(len(items) - 1, int(index * step))] for index in range(count)]
