"""Verify a clip against what its indexed frames actually show.

Retrieval proposes, the index decides. A search hit is a claim; the Datalake's
captions are a description of the frames themselves, so they are what a clip is
accepted or rejected on:

* **Hands** — for manipulation data a clip is worthless without hands in frame.
  Caption wording ("a gloved hand", "the left hand holds") is the evidence.
* **Viewpoint** — the caption corroborates or contradicts the viewpoint guessed
  from the title.
* **Screen content** — a screen recording or a slideshow is not footage of the
  world, however well it matches the query.

The honest caveat, carried on every verdict: this reads caption wording, not a
hand-tracking model. It is a text judgement about a visual description, and it
is recorded as such so nobody downstream mistakes it for detector output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from video_searching_agent.curation.viewpoint import (
    Viewpoint,
    ViewpointVerdict,
    classify_viewpoint,
)

CAPTION_EVIDENCE_CAVEAT = (
    "read from caption wording, not a hand-tracking or pose model"
)

# Hands in frame. Ordered longest-first so the specific phrase is the one cited.
_HAND_CUES = (
    "left hand",
    "right hand",
    "both hands",
    "gloved hand",
    "gloved hands",
    "bare hand",
    "his hand",
    "her hand",
    "their hand",
    "the hand",
    "hands",
    "hand",
    "fingers",
    "thumb",
    "palm",
    "grips",
    "grasps",
    "holding",
    "holds",
    "手",
    "双手",
)

# Actions that imply a hand even when no hand noun appears. Doubling as the
# action signature the cleaning agent splits anchors on: a run of segments that
# stops chopping and starts stirring is two actions, not one long one.
_MANIPULATION_CUES = (
    "picks up",
    "places",
    "inserts",
    "screws",
    "unscrews",
    "tightens",
    "peels",
    "chops",
    "slices",
    "stirs",
    "pours",
    "wipes",
    "assembles",
    "solders",
    "connects",
    "presses",
    "turns the",
    "opens the",
    "closes the",
    "chops",
    "cuts",
    "moves",
    "steadies",
    "holds",
    "lifts",
    "scrapes",
    "sprinkles",
    "kneads",
    "folds",
    "washes",
    "rinses",
    "flips",
    "tightens",
    "loosens",
    "removes",
    "attaches",
    "wraps",
    "seals",
    "measures",
    "sands",
    "drills",
    "saws",
    "paints",
    "welds",
)

# Content that is not footage of the physical world.
_NON_FOOTAGE_CUES = (
    "screen recording",
    "screenshot",
    # Not the bare word "slide": manipulation captions are full of "slides the
    # sleeve over the wires", and that cue rejected real assembly footage.
    "presentation slide",
    "slide deck",
    "title slide",
    "slideshow",
    "powerpoint",
    "text on a black background",
    "title card",
    "animated graphic",
    "cartoon",
    "video game",
    "gameplay",
    "user interface",
    "web page",
    "spreadsheet",
)


@dataclass
class FrameCheck:
    """What the indexed frames say about a clip."""

    hands_visible: bool = False
    hands_confidence: float = 0.0
    hand_evidence: list[str] = field(default_factory=list)

    viewpoint: Viewpoint = Viewpoint.UNKNOWN
    viewpoint_confidence: float = 0.0

    is_footage: bool = True
    non_footage_evidence: list[str] = field(default_factory=list)

    checked_characters: int = 0
    caveat: str = CAPTION_EVIDENCE_CAVEAT

    @property
    def has_caption_text(self) -> bool:
        """False when there was nothing to judge — an abstention, not a pass."""
        return self.checked_characters > 0

    def rejection(
        self,
        require_hands: bool = True,
        wanted_viewpoint: Viewpoint | None = None,
    ) -> str | None:
        """Why this clip should be dropped, or None to keep it.

        Args:
            require_hands: Drop clips with no hand evidence.
            wanted_viewpoint: Drop clips the captions place in the other
                viewpoint. A caption that is merely silent never rejects.

        Returns:
            A human-readable reason, or None.
        """
        if not self.has_caption_text:
            return "no captions available yet to verify against"

        if not self.is_footage:
            cited = ", ".join(self.non_footage_evidence[:2])
            return f"not real-world footage ({cited})"

        if require_hands and not self.hands_visible:
            return "no hands visible in the captions"

        if (
            wanted_viewpoint
            and self.viewpoint != Viewpoint.UNKNOWN
            and self.viewpoint != wanted_viewpoint
        ):
            return (
                f"captions place this in {self.viewpoint.value}, "
                f"wanted {wanted_viewpoint.value}"
            )

        return None


def _cues_present(haystack: str, cues: tuple[str, ...]) -> list[str]:
    """Cues found in the text, in cue order, de-duplicated by word boundary."""
    found: list[str] = []
    for cue in cues:
        pattern = re.escape(cue)
        # Latin cues need boundaries so "hand" does not match "handle".
        if cue.isascii():
            pattern = rf"\b{pattern}\b"
        if re.search(pattern, haystack):
            found.append(cue)
    return found


def mentions_hands(text: str | None) -> tuple[bool, list[str]]:
    """Whether a piece of caption text puts a hand in frame, and on what evidence.

    The same cue sets the whole-clip check uses, exposed for per-segment work:
    the cleaning agent needs this per caption segment to decide where an action
    span starts and stops.

    Returns:
        (hands_present, evidence) — evidence entries are prefixed `hand:` or
        `manipulation:` so a reader can tell a stated hand from an inferred one.
    """
    if not text or not text.strip():
        return False, []
    lowered = text.lower()
    hand_cues = _cues_present(lowered, _HAND_CUES)
    manipulation_cues = _cues_present(lowered, _MANIPULATION_CUES)
    evidence = [f"hand:{cue}" for cue in hand_cues[:2]]
    evidence += [f"manipulation:{cue}" for cue in manipulation_cues[:2]]
    return bool(hand_cues or manipulation_cues), evidence


def action_signature(text: str | None) -> set[str]:
    """The manipulation cues in a piece of caption text.

    Used as a cheap proxy for "which action is this": two consecutive caption
    segments whose signatures are disjoint are doing different things, and the
    cleaning agent splits the anchor between them rather than merging a whole
    continuous take into one shapeless action.
    """
    if not text or not text.strip():
        return set()
    return set(_cues_present(text.lower(), _MANIPULATION_CUES))


def is_footage_text(text: str | None) -> tuple[bool, list[str]]:
    """Whether a piece of caption text describes the physical world."""
    if not text or not text.strip():
        return True, []
    found = _cues_present(text.lower(), _NON_FOOTAGE_CUES)
    return not found, found[:3]


def check_frames(
    caption: str | None = None,
    transcription: str | None = None,
    summary: str | None = None,
    title: str | None = None,
) -> FrameCheck:
    """Judge a clip from its indexed derived content.

    Captions carry the most weight because they describe the frames; the
    transcription and summary are corroboration only.

    Args:
        caption: Visual captions from the Datalake.
        transcription: Speech transcription.
        summary: AI summary.
        title: Video title, used for the viewpoint reading.

    Returns:
        A FrameCheck with evidence for each judgement.
    """
    visual = " ".join(part for part in (caption, summary) if part).lower()
    spoken = (transcription or "").lower()
    everything = " ".join(part for part in (visual, spoken) if part)

    check = FrameCheck(checked_characters=len(visual.strip()))

    if not visual.strip():
        # Nothing visual to judge. Abstain rather than pass or fail.
        return check

    # --- hands -------------------------------------------------------------
    hand_cues = _cues_present(visual, _HAND_CUES)
    manipulation_cues = _cues_present(visual, _MANIPULATION_CUES)

    if hand_cues:
        # An explicit left/right/gloved hand is the strongest form.
        specific = [cue for cue in hand_cues if " " in cue or cue in ("手", "双手")]
        check.hands_visible = True
        check.hands_confidence = 0.85 if specific else 0.6
        if manipulation_cues:
            check.hands_confidence = min(check.hands_confidence + 0.1, 0.95)
        check.hand_evidence = [f"hand:{cue}" for cue in hand_cues[:3]]
    elif manipulation_cues:
        # A manipulation verb without a hand noun: likely but not stated.
        check.hands_visible = True
        check.hands_confidence = 0.45
        check.hand_evidence = [f"manipulation:{cue}" for cue in manipulation_cues[:3]]

    if manipulation_cues and check.hand_evidence:
        check.hand_evidence += [
            f"manipulation:{cue}"
            for cue in manipulation_cues[:2]
            if f"manipulation:{cue}" not in check.hand_evidence
        ]

    # --- is this footage at all? -------------------------------------------
    non_footage = _cues_present(visual, _NON_FOOTAGE_CUES)
    if non_footage:
        check.is_footage = False
        check.non_footage_evidence = non_footage[:3]

    # --- viewpoint, corroborated by the captions ---------------------------
    verdict: ViewpointVerdict = classify_viewpoint(title=title, captions=everything)
    check.viewpoint = verdict.viewpoint
    check.viewpoint_confidence = verdict.confidence

    return check
