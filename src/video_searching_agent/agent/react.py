"""Shared ReAct plumbing for the specialized agents.

Every agent in this package works the same way: it thinks, it calls one
Datalake tool, it records what came back, and it repeats. Keeping that
machinery here means the cleaning agent and the annotation agent produce the
*same* auditable trace shape, so a label can always be walked back to the span
and the reasoning that produced it.

Nothing here talks to the network. These are the bookkeeping pieces: a step, a
trace, and the tolerant readers that turn whatever shape a Datalake payload
arrived in into text.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReActStep:
    """One Thought → Action → Observation cycle."""

    step: int
    thought: str
    action: str
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    agent: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "agent": self.agent,
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation[:500],
        }


@dataclass
class AgentTrace:
    """An append-only trace that numbers its own steps.

    The agent name is stamped on every step, so a trace assembled from several
    agents still says which one did what.
    """

    agent: str
    steps: list[ReActStep] = field(default_factory=list)

    def add(
        self,
        thought: str,
        action: str,
        action_input: dict[str, Any] | None = None,
        observation: str = "",
    ) -> ReActStep:
        """Record a step and return it."""
        step = ReActStep(
            step=len(self.steps) + 1,
            thought=thought,
            action=action,
            action_input=action_input or {},
            observation=observation,
            agent=self.agent,
        )
        self.steps.append(step)
        return step

    def extend(self, other: AgentTrace) -> None:
        """Fold another agent's trace in, renumbering as it goes."""
        for step in other.steps:
            self.steps.append(
                ReActStep(
                    step=len(self.steps) + 1,
                    thought=step.thought,
                    action=step.action,
                    action_input=step.action_input,
                    observation=step.observation,
                    agent=step.agent,
                )
            )

    def as_list(self) -> list[dict[str, Any]]:
        return [step.as_dict() for step in self.steps]

    def __len__(self) -> int:
        return len(self.steps)


def parse_json_object(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of a model response.

    Raises:
        json.JSONDecodeError: When there is no parseable object.
        ValueError: When what parsed was not an object.
    """
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```[a-zA-Z]*\n?", "", candidate)
        candidate = re.sub(r"\n?```$", "", candidate)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("model response was not a JSON object")
    return parsed


def text_of(payload: dict[str, Any], field_name: str) -> str | None:
    """Pull text out of a derived-content payload, whichever shape it came in.

    The Datalake returns caption and transcription content as a string, as an
    object with an aggregated field, or as a list of segments, depending on the
    endpoint. All three are read here so callers never have to branch.
    """
    value = payload.get(field_name)
    if isinstance(value, str) and value.strip():
        return value
    if value is None and isinstance(payload.get("segments"), list):
        # A windowed read returns segments and no aggregated field.
        return _join_segments(payload["segments"])
    if isinstance(value, dict):
        for key in (field_name, "aggregated", "text"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner
        return _join_segments(value.get("segments"))
    if isinstance(value, list):
        return _join_segments(value)
    return None


def segments_of(payload: dict[str, Any], field_name: str = "caption") -> list[dict[str, Any]]:
    """Pull timed segments out of a derived-content payload.

    Segments are what makes time-anchored annotation possible at all, so they
    are read separately from the aggregated text. Returns an empty list when the
    payload carries no per-segment breakdown.
    """
    candidates: Any = payload.get("segments")
    if candidates is None:
        value = payload.get(field_name)
        if isinstance(value, dict):
            candidates = value.get("segments")
        elif isinstance(value, list):
            candidates = value
    if not isinstance(candidates, list):
        return []

    segments: list[dict[str, Any]] = []
    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        text = entry.get("text") or entry.get("caption") or entry.get("content")
        segments.append(
            {
                # `or` would swallow a 0.0 start, which is every video's first
                # segment, so each key is checked for presence instead.
                "start": as_float(_first_present(entry, "start", "start_time")),
                "end": as_float(_first_present(entry, "end", "end_time")),
                "text": str(text) if text else "",
            }
        )
    return segments


def _first_present(entry: dict[str, Any], *keys: str) -> Any:
    """The first key that is actually present and not None."""
    for key in keys:
        value = entry.get(key)
        if value is not None:
            return value
    return None


def _join_segments(segments: Any) -> str | None:
    if not isinstance(segments, list):
        return None
    joined = " ".join(
        str(segment.get("text", ""))
        for segment in segments
        if isinstance(segment, dict)
    ).strip()
    return joined or None


def as_float(value: Any) -> float | None:
    """Coerce to float, or None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
