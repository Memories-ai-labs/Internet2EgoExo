"""The clipping agent, as a ReAct loop that looks at the footage.

Anchors were found by a deterministic walk over caption segments: merge the runs
where hands appear, split on a gap over two seconds, split again when the verbs
change. That walk is a good skeleton and it is blind. It cannot tell a pause in
the narration from a pause in the work, it takes the caption's word for where an
action begins, and when the captions are vague it produces vague boundaries with
no way to know it has.

So the walk stays — it proposes — and this agent decides. It is given the
proposal and the caption evidence behind it, and it can:

* **look at frames** around a boundary, to see whether the action really starts
  there or a few seconds either side;
* **read the captions** for any window, to check what the walk summarised;
* **merge, split, move or drop** what was proposed, saying why each time.

The loop is what makes that possible: a single call would have to be handed all
the evidence in advance, and the whole point is that which evidence matters is
not knowable in advance.

What it may not do is invent anchors out of nothing. Every anchor it returns has
to trace to a proposal or to a span it looked at, and the boundaries it returns
are clamped to the video. An agent that widens a span to cover footage it never
examined is guessing, and a guessed boundary is worse than a rough one, because
it looks the same as a checked one.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.eyes import Eyes
from video_searching_agent.agent.react import AgentTrace, segments_of
from video_searching_agent.agent.react_loop import LoopResult, Tool, ToolResult, run_loop
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.curation.embedding_search import search_frames

logger = logging.getLogger(__name__)

AGENT_NAME = "clipping"

# What one clip's worth of looking may cost before the agent has to conclude
# from what it has. Two or three looks, which is enough to check the boundaries
# that matter without auditing every anchor.
DEFAULT_LOOK_BUDGET_USD = 0.02

SYSTEM_PROMPT = """You decide where the actions in a video begin and end.

A first pass has proposed spans by reading caption segments: it merged the runs
where hands appear and split on pauses and on changes of verb. It is a skeleton,
not an answer, and it has never seen the footage.

Your job is to correct it where the footage disagrees, and to leave it alone
where it does not. Specifically:

- A span should start when the work starts, not when the narration mentions it.
- A span should cover ONE action. If frames show two different operations in it,
  split it.
- Two spans that are the same continuous action interrupted by nothing should be
  one span.
- A span showing no hands doing anything is not an action; drop it.
- A span you cannot see (a tool told you it could not look) stays exactly as
  proposed. Do not adjust a boundary on evidence you do not have.

Rules that are not yours to break:

- Every span you return must lie inside the video's duration.
- Never return a span shorter than 2 seconds; that is not an action.
- Never invent a span covering footage you have not examined and that no
  proposal covered.
- Times are seconds, as numbers.

Answer with ONLY this JSON:

{
  "spans": [
    {"start": 12.0, "end": 48.0, "why": "one clause on what happens here",
     "changed": "kept" | "moved" | "split" | "merged" | "dropped"}
  ],
  "unexamined": ["the spans you did not look at, by index"],
  "notes": "anything the next pass should know, or empty"
}"""


@dataclass
class ClippedSpan:
    """One anchor the agent settled on."""

    start: float
    end: float
    why: str = ""
    changed: str = "kept"
    examined: bool = False

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    def as_dict(self) -> dict[str, Any]:
        return {
            "span_start": self.start,
            "span_end": self.end,
            "duration": self.duration,
            "why": self.why,
            "changed": self.changed,
            "examined": self.examined,
            "hier_level": "action",
        }


@dataclass
class ClippingResult:
    """What the agent decided, and what it cost."""

    video_id: str
    spans: list[ClippedSpan] = field(default_factory=list)
    proposed: int = 0
    # The spans the agent actually put eyes on, so a boundary it never checked
    # is distinguishable from one it confirmed.
    windows_looked_at: list[tuple[float, float]] = field(default_factory=list)
    trace: AgentTrace = field(default_factory=lambda: AgentTrace(agent=AGENT_NAME))
    cost_usd: float = 0.0
    looks: int = 0
    notes: str = ""
    fell_back: bool = False
    error: str | None = None

    @property
    def examined(self) -> int:
        return sum(1 for span in self.spans if span.examined)

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "proposed": self.proposed,
            "kept": len(self.spans),
            "examined": self.examined,
            "looks": self.looks,
            "cost_usd": round(self.cost_usd, 4),
            "fell_back": self.fell_back,
            "notes": self.notes,
            "error": self.error,
            "spans": [span.as_dict() for span in self.spans],
            "trace": self.trace.as_list(),
        }


class ClippingAgent:
    """Refines proposed anchors by looking at the footage behind them."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        llm: Any | None = None,
        eyes: Eyes | None = None,
        look_budget_usd: float = DEFAULT_LOOK_BUDGET_USD,
    ) -> None:
        """Initialize the agent.

        Args:
            client: Datalake client, for reading caption windows.
            llm: The model that runs the loop. ``False`` disables the agent,
                which makes it return the proposal untouched.
            eyes: Frame sampler. Created on first use when omitted.
            look_budget_usd: What one video's worth of looking may cost.
        """
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
            except Exception as exc:  # noqa: BLE001 - the walk still works alone
                logger.info("no model for the clipping loop: %s", exc)
                self._llm = None
        return self._llm or None

    async def refine(
        self,
        video_id: str,
        proposed: list[dict[str, Any]],
        *,
        duration_seconds: float | None = None,
        min_span_seconds: float = 2.0,
        max_steps: int = 6,
    ) -> ClippingResult:
        """Look at the proposed anchors and correct them.

        Args:
            video_id: The indexed video.
            proposed: Spans from the caption walk, each with `span_start`,
                `span_end` and optionally `evidence`.
            duration_seconds: The video's length, to clamp against.
            min_span_seconds: Shortest span that is still an action.
            max_steps: Loop turns.

        Returns:
            A ClippingResult. When the loop cannot run or does not converge,
            `fell_back` is True and `spans` is the proposal unchanged — which is
            the honest outcome, not an empty one.
        """
        result = ClippingResult(video_id=video_id, proposed=len(proposed))
        skeleton = [
            ClippedSpan(
                start=float(span["span_start"]),
                end=float(span["span_end"]),
                why="proposed by the caption walk",
            )
            for span in proposed
            if _has_span(span)
        ]

        if not skeleton:
            result.notes = "nothing was proposed, so there is nothing to refine"
            return result
        if self.llm is None:
            result.spans = skeleton
            result.fell_back = True
            result.notes = "no model available; the proposal stands"
            return result

        tools = self._tools(video_id, result)
        outcome = await run_loop(
            self.llm,
            SYSTEM_PROMPT,
            self._opening(video_id, skeleton, proposed, duration_seconds),
            tools,
            trace=result.trace,
            agent=AGENT_NAME,
            max_steps=max_steps,
            budget_usd=self.look_budget_usd,
            answer_keys=("spans",),
        )
        result.cost_usd = outcome.cost_usd
        result.looks = self.eyes.looks

        spans = self._read_answer(outcome, duration_seconds, min_span_seconds)
        if spans is None:
            result.spans = _mark_examined(skeleton, result.windows_looked_at)
            result.fell_back = True
            result.error = outcome.stopped_because
            result.notes = "the loop did not converge; the proposal stands"
            return result

        result.spans = _mark_examined(spans, result.windows_looked_at)
        result.notes = str((outcome.answer or {}).get("notes") or "")
        return result

    # ------------------------------------------------------------- internals

    def _opening(
        self,
        video_id: str,
        skeleton: list[ClippedSpan],
        proposed: list[dict[str, Any]],
        duration_seconds: float | None,
    ) -> str:
        lines = [f"Video {video_id}"]
        if duration_seconds:
            lines.append(f"Duration: {duration_seconds:.0f}s")
        lines.append("")
        lines.append("Proposed spans, from the caption walk:")
        for index, (span, raw) in enumerate(zip(skeleton, proposed, strict=False)):
            evidence = ", ".join(str(cue) for cue in (raw.get("evidence") or [])[:3])
            lines.append(
                f"  [{index}] {span.start:.1f}s–{span.end:.1f}s ({span.duration:.1f}s)"
                + (f" — cues: {evidence}" if evidence else "")
            )
        lines += ["", "Correct these where the footage disagrees."]
        return "\n".join(lines)

    def _tools(self, video_id: str, result: ClippingResult) -> list[Tool]:
        async def look(arguments: dict[str, Any]) -> ToolResult:
            start = _as_float(arguments.get("start"))
            end = _as_float(arguments.get("end"))
            if start is None or end is None:
                return ToolResult(observation="look needs numeric start and end")
            frames = await self.eyes.look(
                video_id, start, end, count=int(arguments.get("frames") or 4)
            )
            if frames.looked:
                # Recorded here and applied to the spans afterwards: during the
                # loop the answer does not exist yet, so marking spans now marks
                # nothing — which is how `examined` stayed at zero through four
                # looks.
                result.windows_looked_at.append((frames.start, frames.end))
            return ToolResult(
                observation=frames.describe(),
                images=frames.images,
                cost_usd=frames.cost_usd,
            )

        async def read_captions(arguments: dict[str, Any]) -> ToolResult:
            start = _as_float(arguments.get("start"))
            end = _as_float(arguments.get("end"))
            if start is None or end is None:
                return ToolResult(observation="read_captions needs numeric start and end")
            try:
                payload = await self.client.get_caption(video_id, start=start, end=end)
            except MemoriesDatalakeError as exc:
                return ToolResult(observation=f"captions unavailable: {str(exc)[:150]}")
            segments = segments_of(payload, "caption")
            if not segments:
                return ToolResult(observation=f"no caption segments cover {start:.0f}s–{end:.0f}s")
            lines = [
                f"[{segment.get('start')}–{segment.get('end')}] "
                f"{str(segment.get('text') or '')[:160]}"
                for segment in segments[:12]
            ]
            return ToolResult(observation="\n".join(lines))

        async def find_frames(arguments: dict[str, Any]) -> ToolResult:
            query = str(arguments.get("query") or "").strip()
            if not query:
                return ToolResult(
                    observation='find_frames needs a query, e.g. {"query": "hands turning a bolt"}'
                )
            evidence = await search_frames(
                self.client,
                query,
                video_ids=[video_id],
                top_k=int(arguments.get("count") or 12),
            )
            if not evidence.looked:
                return ToolResult(observation=f"visual search unavailable: {evidence.error}")
            if not evidence.hits:
                return ToolResult(
                    observation=f"the visual index returned no seconds for {query!r}",
                    cost_usd=evidence.cost_usd,
                )
            lines = [
                f"{len(evidence.hits)} seconds ranked by visual similarity to {query!r}. "
                "The ranking says which seconds are most like it, never that it is "
                "present — gibberish scores nearly as high as a true query. Read what "
                "each second shows."
            ]
            for start, end in evidence.spans():
                lines.append(f"  run {start:.0f}s-{end:.0f}s")
            for hit in evidence.hits[:8]:
                lines.append(f"  [{hit.start:.0f}s] {hit.snippet[:150]}")
            return ToolResult(observation="\n".join(lines), cost_usd=evidence.cost_usd)

        return [
            Tool(
                name="find_frames",
                description=(
                    "search this video's own per-second visual index for a description "
                    "and get back the seconds that most look like it, each with what it "
                    "shows. This is the frames, not the captions: it finds a moment the "
                    "caption never mentioned. One search, $0.008. Use it to locate the "
                    "action before reading or looking at anything"
                ),
                arguments='{"query": "<what to look for>", "count": 4-20}',
                run=find_frames,
            ),
            Tool(
                name="look",
                description=(
                    "sample frames from a span of this video and see them. Use it on a "
                    "boundary you are unsure of, or on a span whose captions are vague. "
                    "Costs money, so look where it will change your answer"
                ),
                arguments='{"start": <seconds>, "end": <seconds>, "frames": 2-8}',
                run=look,
            ),
            Tool(
                name="read_captions",
                description=(
                    "read the index's caption segments for a window, with their times. "
                    "Free. Use it to check what the walk summarised"
                ),
                arguments='{"start": <seconds>, "end": <seconds>}',
                run=read_captions,
            ),
        ]

    def _read_answer(
        self,
        outcome: LoopResult,
        duration_seconds: float | None,
        min_span_seconds: float,
    ) -> list[ClippedSpan] | None:
        """Turn the model's answer into spans, enforcing what is not negotiable."""

        if not outcome.answered:
            return None
        raw_spans = (outcome.answer or {}).get("spans")
        if not isinstance(raw_spans, list):
            return None

        spans: list[ClippedSpan] = []
        for entry in raw_spans:
            if not isinstance(entry, dict):
                continue
            start = _as_float(entry.get("start"))
            end = _as_float(entry.get("end"))
            if start is None or end is None:
                continue
            start = max(0.0, start)
            if duration_seconds:
                end = min(end, float(duration_seconds))
            if end - start < min_span_seconds:
                continue
            spans.append(
                ClippedSpan(
                    start=round(start, 3),
                    end=round(end, 3),
                    why=str(entry.get("why") or "")[:200],
                    changed=str(entry.get("changed") or "kept"),
                )
            )

        spans.sort(key=lambda span: span.start)
        # Siblings must not overlap — G2-TREE-2 — and a model that moved a
        # boundary can easily produce a hair of overlap.
        for earlier, later in zip(spans, spans[1:], strict=False):
            if later.start < earlier.end:
                later.start = earlier.end
        return [span for span in spans if span.duration >= min_span_seconds]


def _mark_examined(
    spans: list[ClippedSpan], windows: list[tuple[float, float]]
) -> list[ClippedSpan]:
    """Flag the spans the agent actually looked at.

    Overlap rather than containment: a look aimed at a boundary deliberately
    straddles two spans, and both of them were seen.
    """
    for span in spans:
        span.examined = any(
            min(span.end, end) - max(span.start, start) > 0 for start, end in windows
        )
    return spans


def _has_span(span: dict[str, Any]) -> bool:
    return (
        _as_float(span.get("span_start")) is not None
        and _as_float(span.get("span_end")) is not None
    )


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
