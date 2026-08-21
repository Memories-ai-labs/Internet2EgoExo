"""Camera-viewpoint classification for training-data collection.

Egocentric footage is shot from the actor's own head/body — the camera moves
with them and their hands enter frame. Exocentric footage observes the actor
from outside — fixed cameras, tripods, multi-view rigs, spectator angles.

Classification is deterministic keyword/pattern evidence over whatever text a
candidate carries (title, description, tags, and — when the video has been
indexed — its captions and transcription). No LLM call: this runs over every
candidate in a search, and the evidence has to be inspectable to be trusted.

Confidence is deliberately conservative. "POV" in particular is heavily used by
meme and skit content that is *not* genuine first-person capture ("POV: you're
the last person on earth"), so it only reaches high confidence alongside a
capture cue (head mount, GoPro, visible hands) or a real activity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum


class Viewpoint(StrEnum):
    """Camera viewpoint of a candidate video."""

    EGOCENTRIC = "egocentric"
    EXOCENTRIC = "exocentric"
    UNKNOWN = "unknown"


# Cues that only make sense for head/body-mounted capture.
_EGO_STRONG = (
    "egocentric",
    "ego-centric",
    "first person view",
    "first-person view",
    "first person perspective",
    "first-person perspective",
    "head mounted",
    "head-mounted",
    "headcam",
    "head cam",
    "helmet cam",
    "helmetcam",
    "chest mount",
    "chest-mount",
    "body cam",
    "bodycam",
    "body-worn",
    "smart glasses",
    "project aria",
    "ego4d",
    "ego-exo4d",
    "epic-kitchens",
    "epic kitchens",
    "charades-ego",
    "第一人称",
    "第一视角",
)

# Weaker ego cues: real signals, but also used loosely.
_EGO_WEAK = (
    "first person",
    "first-person",
    "pov",
    "point of view",
    "gopro",
    "go pro",
    "wearable camera",
    "hands only",
    "my perspective",
    "through my eyes",
    "as seen by",
    "walking tour",
    "handheld",
)

# Cues for an outside-observer camera.
_EXO_STRONG = (
    "exocentric",
    "exo-centric",
    "third person view",
    "third-person view",
    "third person perspective",
    "third-person perspective",
    "fixed camera",
    "static camera",
    "stationary camera",
    "multi-view",
    "multiview",
    "multi-camera",
    "camera rig",
    "surveillance",
    "cctv",
    "security camera",
    "overhead camera",
    "第三人称",
    "第三视角",
    "固定机位",
)

_EXO_WEAK = (
    "third person",
    "third-person",
    "tripod",
    "wide shot",
    "wide angle shot",
    "spectator",
    "sideline",
    "from the side",
    "observing",
    "demonstration video",
    "tutorial camera",
)

# Capture cues that corroborate a weak ego signal into a real one.
_EGO_CORROBORATION = (
    "hands",
    "my hands",
    "手部",
    "gopro",
    "head",
    "helmet",
    "chest",
    "glasses",
    "walking",
    "cooking",
    "assembly",
    "assembling",
    "repair",
    "driving",
    "cycling",
    "kitchen",
    "workshop",
    "warehouse",
    "manipulation",
    "grasping",
)

# The meme construction: "POV: <scenario>" — a caption device, not a camera.
_POV_MEME = re.compile(r"\bpov\s*[:：]", re.IGNORECASE)


@dataclass
class ViewpointVerdict:
    """Outcome of classifying one candidate."""

    viewpoint: Viewpoint
    confidence: float
    evidence: list[str] = field(default_factory=list)

    def matches(self, wanted: Viewpoint | None) -> bool:
        """True when this verdict is acceptable for a requested viewpoint.

        `None` (or UNKNOWN) as the request means the caller takes anything.
        An unknown verdict is never excluded — it just ranks below a match.
        """
        if wanted is None or wanted == Viewpoint.UNKNOWN:
            return True
        if self.viewpoint == Viewpoint.UNKNOWN:
            return True
        return self.viewpoint == wanted


def _found(haystack: str, needles: tuple[str, ...]) -> list[str]:
    """Return the cues present in the text, in cue order."""
    return [needle for needle in needles if needle in haystack]


def classify_viewpoint(
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    captions: str | None = None,
) -> ViewpointVerdict:
    """Classify a candidate's camera viewpoint from its text.

    Args:
        title: Video title.
        description: Video description or summary.
        tags: Hashtags or tag list.
        captions: Indexed visual captions / transcription, when available.
            These are the strongest signal available, because they describe
            what the frame actually shows.

    Returns:
        A verdict with confidence in [0, 1] and the cues that produced it.
    """
    parts = [title or "", description or "", " ".join(tags or []), captions or ""]
    haystack = " ".join(parts).lower()

    if not haystack.strip():
        return ViewpointVerdict(Viewpoint.UNKNOWN, 0.0, [])

    ego_strong = _found(haystack, _EGO_STRONG)
    ego_weak = _found(haystack, _EGO_WEAK)
    exo_strong = _found(haystack, _EXO_STRONG)
    exo_weak = _found(haystack, _EXO_WEAK)

    ego_score = 0.0
    exo_score = 0.0
    evidence: list[str] = []

    if ego_strong:
        ego_score += 0.7 + 0.1 * min(len(ego_strong) - 1, 2)
        evidence += [f"ego:{cue}" for cue in ego_strong[:3]]

    if ego_weak:
        corroborated = bool(_found(haystack, _EGO_CORROBORATION))
        # A bare "POV:" caption is a storytelling device, not a camera rig.
        meme_only = bool(_POV_MEME.search(haystack)) and not corroborated
        weight = 0.15 if meme_only else (0.45 if corroborated else 0.3)
        ego_score += weight
        evidence += [f"ego?:{cue}" for cue in ego_weak[:3]]
        if meme_only:
            evidence.append("ego-penalty:pov-caption-pattern")

    if exo_strong:
        exo_score += 0.7 + 0.1 * min(len(exo_strong) - 1, 2)
        evidence += [f"exo:{cue}" for cue in exo_strong[:3]]

    if exo_weak:
        exo_score += 0.3
        evidence += [f"exo?:{cue}" for cue in exo_weak[:3]]

    if ego_score == 0.0 and exo_score == 0.0:
        return ViewpointVerdict(Viewpoint.UNKNOWN, 0.0, [])

    # Contradictory evidence: keep the leader but discount it.
    if ego_score > 0 and exo_score > 0:
        margin = abs(ego_score - exo_score)
        if margin < 0.2:
            return ViewpointVerdict(
                Viewpoint.UNKNOWN,
                round(min(margin, 0.3), 2),
                evidence + ["conflict:both-viewpoints-cited"],
            )
        penalty = 0.25
    else:
        penalty = 0.0

    if ego_score >= exo_score:
        return ViewpointVerdict(
            Viewpoint.EGOCENTRIC,
            round(max(0.0, min(ego_score - penalty, 1.0)), 2),
            evidence,
        )
    return ViewpointVerdict(
        Viewpoint.EXOCENTRIC,
        round(max(0.0, min(exo_score - penalty, 1.0)), 2),
        evidence,
    )
