"""The annotation agent, as a ReAct loop that looks at the span it is labelling.

The old one was handed a span's caption text and asked for a label, a narration
and a hand assignment in a single call. Everything it said was therefore a
statement about *wording*, and the caveat attached to every verdict —
"read from caption wording, not a hand-tracking or pose model" — was doing a lot
of work.

The specific thing that cost: hand assignment. The rule has always been that a
hand is never invented, so when the captions did not say which hand did what,
the fields came back null and the tree showed "hand assignment not stated in the
captions". That is honest and it is also a hole in the dataset, because the
frames very often *do* show it. A caption saying "a hand turns the wrench" left
both fields null; a look at the span shows a right hand on the wrench and a left
hand steadying the frame.

So this loop can look. It gets the span, the captions behind it, and tools to
examine frames and to re-read any window, and it answers from what it saw. Two
rules survive unchanged and are enforced here rather than trusted:

* **A hand is still never invented.** The difference is that "I saw it" is now a
  way of knowing, and each hand field records which. A field with no evidence
  behind it stays null.
* **Events stay inside their action.** A model that returns an event outside its
  parent has misread the times; the times are clamped, not argued with.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.eyes import Eyes
from video_searching_agent.agent.react import AgentTrace, segments_of
from video_searching_agent.agent.react_loop import Tool, ToolResult, run_loop
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.curation.embedding_search import hits_within, search_frames

logger = logging.getLogger(__name__)

AGENT_NAME = "annotating"

# One span's worth of looking. A label does not need four looks.
DEFAULT_LOOK_BUDGET_USD = 0.012

SYSTEM_PROMPT = """You label one span of a video for a manipulation training set.

You have the index's caption text for the span, and you can look at the frames.
Look when the captions leave something you are being asked for unclear — which
hand did what, what the object actually is, whether the span is one action.

What matters about your answer:

- `label` names what happens in THIS span, kebab-case, and does not restate the
  overall task. Label the step, not the job.
- `narration` is one sentence in your own words about this span.
- `left_hand` and `right_hand` say what each hand does. **Never invent one.**
  Fill a field only if the captions say so or you saw it, and set
  `hand_evidence` to "captions" or "frames" accordingly. If you cannot tell
  which hand is which, leave both null and say so in `narration` — a null field
  is a correct answer and a guessed one is a wrong label in a dataset somebody
  trains on.
- `objects` are the things acted on, named as specifically as you can support.
- `hands_visible` is whether the wearer's hands are in frame at all.
- `usable` is false when the span shows no work happening, and `reason` says why.
- `events` are moments inside this span worth their own anchor — a slip, a retry,
  a tool change. Their times must lie inside the span. Omit if there are none.

Answer with ONLY this JSON:

{
  "label": "insert-cam-lock",
  "narration": "The cam lock is pressed into the panel edge and turned home.",
  "usable": true,
  "reason": "",
  "hands_visible": true,
  "left_hand": "steadies the panel",
  "right_hand": "turns the cam lock",
  "hand_evidence": "frames",
  "objects": ["cam lock", "side panel"],
  "events": [{"start": 12.0, "end": 15.0, "label": "dropped-screw"}]
}"""


@dataclass
class SpanLabel:
    """What the agent decided about one span."""

    start: float
    end: float
    label: str | None = None
    narration: str | None = None
    usable: bool = True
    reason: str = ""
    hands_visible: bool | None = None
    left_hand: str | None = None
    right_hand: str | None = None
    hand_evidence: str | None = None
    objects: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    looked: bool = False
    cost_usd: float = 0.0
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "span_start": self.start,
            "span_end": self.end,
            "hier_level": "action",
            "label": self.label,
            "narration": self.narration,
            "usable": self.usable,
            "reason": self.reason,
            "hands_visible": self.hands_visible,
            "left_hand": self.left_hand,
            "right_hand": self.right_hand,
            "hand_evidence": self.hand_evidence,
            "objects": self.objects,
            "events": self.events,
            "looked": self.looked,
            "cost_usd": round(self.cost_usd, 4),
            "error": self.error,
        }


class AnnotatingAgent:
    """Labels a span by reading it and, when it needs to, looking at it."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        llm: Any | None = None,
        eyes: Eyes | None = None,
        look_budget_usd: float = DEFAULT_LOOK_BUDGET_USD,
    ) -> None:
        self._client = client
        self._llm = llm
        self._llm_resolved = llm is not None
        self._eyes = eyes
        self.look_budget_usd = look_budget_usd

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def eyes(self) -> Eyes:
        if self._eyes is None:
            self._eyes = Eyes(client=self.client)
        return self._eyes

    @property
    def llm(self) -> Any | None:
        if not self._llm_resolved:
            self._llm_resolved = True
            try:
                from video_searching_agent.api.llm import get_llm_client

                self._llm = get_llm_client()
            except Exception as exc:  # noqa: BLE001
                logger.info("no model for the annotating loop: %s", exc)
                self._llm = None
        return self._llm or None

    async def label_span(
        self,
        video_id: str,
        start: float,
        end: float,
        *,
        task_label: str | None = None,
        used_labels: list[str] | None = None,
        trace: AgentTrace | None = None,
        max_steps: int = 5,
    ) -> SpanLabel:
        """Label one span, looking at it if the captions are not enough.

        Args:
            video_id: The indexed video.
            start: Span start, seconds.
            end: Span end, seconds.
            task_label: The overall task, so the label does not restate it.
            used_labels: Labels already given to other spans of this video, so
                three spans do not come back with the same name.
            trace: Where to record the loop's steps.
            max_steps: Loop turns.

        Returns:
            A SpanLabel. `error` set with no label means the loop did not
            converge and the span is unlabelled — which is the honest outcome.
        """
        result = SpanLabel(start=float(start), end=float(end))
        if self.llm is None:
            result.error = "no model available"
            return result

        outcome = await run_loop(
            self.llm,
            SYSTEM_PROMPT,
            await self._opening(video_id, start, end, task_label, used_labels),
            self._tools(video_id, start, end, result),
            trace=trace,
            agent=AGENT_NAME,
            max_steps=max_steps,
            budget_usd=self.look_budget_usd,
            answer_keys=("label", "usable"),
        )
        result.cost_usd = outcome.cost_usd
        if not outcome.answered:
            result.error = outcome.stopped_because
            return result

        self._read_answer(result, outcome.answer or {})
        return result

    # ------------------------------------------------------------- internals

    async def _opening(
        self,
        video_id: str,
        start: float,
        end: float,
        task_label: str | None,
        used_labels: list[str] | None,
    ) -> str:
        lines = [
            f"Video {video_id}",
            f"Span: {start:.1f}s to {end:.1f}s ({end - start:.1f}s)",
        ]
        if task_label:
            lines.append(f"The overall task is `{task_label}`. Do not restate it.")
        already = ", ".join(dict.fromkeys(label for label in (used_labels or []) if label))
        if already:
            lines.append(f"Labels already used for other spans: {already}. Do not reuse them.")
        lines += ["", "Caption segments for this span:"]
        lines.append(await self._captions(video_id, start, end) or "  (none)")
        lines += ["", "Label this span."]
        return "\n".join(lines)

    async def _captions(self, video_id: str, start: float, end: float) -> str:
        try:
            payload = await self.client.get_caption(video_id, start=start, end=end)
        except MemoriesDatalakeError as exc:
            return f"  (captions unavailable: {str(exc)[:120]})"
        segments = segments_of(payload, "caption")
        if not segments:
            return ""
        return "\n".join(
            f"  [{segment.get('start')}–{segment.get('end')}] "
            f"{str(segment.get('text') or '')[:200]}"
            for segment in segments[:10]
        )

    def _tools(self, video_id: str, start: float, end: float, result: SpanLabel) -> list[Tool]:
        async def look(arguments: dict[str, Any]) -> ToolResult:
            # Clamped to the span: an agent labelling 40s–70s has no business
            # looking at 300s, and a label justified by footage outside its own
            # span is a wrong label.
            look_start = max(start, _as_float(arguments.get("start")) or start)
            look_end = min(end, _as_float(arguments.get("end")) or end)
            if look_end <= look_start:
                look_start, look_end = start, end
            frames = await self.eyes.look(
                video_id, look_start, look_end, count=int(arguments.get("frames") or 4)
            )
            if frames.looked:
                result.looked = True
            return ToolResult(
                observation=frames.describe(),
                images=frames.images,
                cost_usd=frames.cost_usd,
            )

        async def read_captions(arguments: dict[str, Any]) -> ToolResult:
            window_start = max(start, _as_float(arguments.get("start")) or start)
            window_end = min(end, _as_float(arguments.get("end")) or end)
            text = await self._captions(video_id, window_start, window_end)
            return ToolResult(observation=text or "no caption segments in that window")

        async def find_frames(arguments: dict[str, Any]) -> ToolResult:
            query = str(arguments.get("query") or "").strip()
            if not query:
                return ToolResult(
                    observation="find_frames needs a query, "
                    'e.g. {"query": "which hand holds the bracket"}'
                )
            evidence = await search_frames(self.client, query, video_ids=[video_id], top_k=24)
            if not evidence.looked:
                return ToolResult(observation=f"visual search unavailable: {evidence.error}")
            # Clamped to this span, for the same reason `look` is: a label
            # justified by footage outside its own span is a wrong label. The
            # search runs over the whole video because that is the only scope
            # the endpoint takes, so the clamping happens here.
            inside = hits_within(evidence, start, end)
            if not inside:
                return ToolResult(
                    observation=(
                        f"the visual index found nothing like {query!r} inside "
                        f"{start:.0f}s-{end:.0f}s"
                        + (
                            " (it did match elsewhere in the video, which says nothing "
                            "about this span)"
                            if evidence.hits
                            else ""
                        )
                    ),
                    cost_usd=evidence.cost_usd,
                )
            lines = [
                f"{len(inside)} seconds inside this span rank as most like {query!r}. "
                "A ranking, not a detection — read what each second shows."
            ]
            lines += [
                f"  [{hit.start:.0f}s] {hit.snippet[:170]}"
                for hit in sorted(inside, key=lambda h: h.start)[:8]
            ]
            return ToolResult(observation="\n".join(lines), cost_usd=evidence.cost_usd)

        return [
            Tool(
                name="find_frames",
                description=(
                    "search the video's per-second visual index and get back the seconds "
                    "inside this span that most look like your description, each with "
                    "what it shows. The frames, not the captions. $0.008. Use it when "
                    "the captions do not name the object or say which hand acts"
                ),
                arguments='{"query": "<what to look for>"}',
                run=find_frames,
            ),
            Tool(
                name="look",
                description=(
                    "see frames from this span. Use it when the captions do not settle "
                    "which hand does what, or what the object is. Costs money"
                ),
                arguments='{"start": <seconds>, "end": <seconds>, "frames": 2-8}',
                run=look,
            ),
            Tool(
                name="read_captions",
                description="re-read the index's captions for a window inside this span. Free",
                arguments='{"start": <seconds>, "end": <seconds>}',
                run=read_captions,
            ),
        ]

    def _read_answer(self, result: SpanLabel, answer: dict[str, Any]) -> None:
        """Copy the answer onto the result, enforcing the two standing rules."""

        result.label = _clean(answer.get("label"))
        result.narration = _clean(answer.get("narration"))
        result.usable = bool(answer.get("usable", True))
        result.reason = str(answer.get("reason") or "")[:300]
        hands = answer.get("hands_visible")
        result.hands_visible = hands if isinstance(hands, bool) else None

        evidence = str(answer.get("hand_evidence") or "").strip().lower()
        # A hand is never invented. "captions" and "frames" are the two ways of
        # knowing; anything else — including a look that never happened — is not
        # evidence, so the fields go back to null.
        if evidence == "frames" and not result.looked:
            evidence = ""
        if evidence not in ("captions", "frames"):
            result.left_hand = None
            result.right_hand = None
            result.hand_evidence = None
        else:
            result.left_hand = _clean(answer.get("left_hand"))
            result.right_hand = _clean(answer.get("right_hand"))
            result.hand_evidence = evidence if (result.left_hand or result.right_hand) else None

        objects = answer.get("objects")
        if isinstance(objects, list):
            result.objects = [str(item)[:80] for item in objects if str(item).strip()][:8]

        # Events are clamped inside the span rather than argued with.
        events = answer.get("events")
        if isinstance(events, list):
            for entry in events:
                if not isinstance(entry, dict):
                    continue
                event_start = _as_float(entry.get("start"))
                event_end = _as_float(entry.get("end"))
                if event_start is None or event_end is None:
                    continue
                event_start = max(result.start, min(event_start, result.end))
                event_end = max(event_start, min(event_end, result.end))
                if event_end - event_start < 0.5:
                    continue
                result.events.append(
                    {
                        "span_start": round(event_start, 3),
                        "span_end": round(event_end, 3),
                        "hier_level": "event",
                        "label": _clean(entry.get("label")),
                    }
                )


def _clean(value: Any) -> str | None:
    text = str(value or "").strip()
    return text[:300] or None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
