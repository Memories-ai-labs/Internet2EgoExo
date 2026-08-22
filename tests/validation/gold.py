"""The validation set: inputs with the verdict a careful human would give.

Unit tests check that a function does what it was written to do. This set checks
something else — that the *judgements* are right on data the code did not come
from. Half of it is real Datalake output for real industrial footage
(`real_captions.json`, four recordings, 79 timed caption segments), and the rest
are cases distilled from defects that actually shipped.

Every expectation here is a claim about the footage, not about the
implementation. If a change makes one fail, either the change is wrong or the
claim was — and both are worth stopping for.

Cases marked `regression` encode a bug that reached production:

* `wrist_camera` — "slides the sleeve over the wires" was read as slideware and
  the clip was rejected as "not real-world footage".
* `ego_harness` — one mention of another person in a 40-minute recording vetoed
  the whole clip; and its 14 caption segments collapsed into a single
  499-second "action".
* `medical_tubing` — the opposite case: someone else really is in half of it, so
  it *must* be rejected. A fix for the case above must not swallow this one.
* `rotating_pot` — search metadata said cooking; the frames were a pot rotating
  on a turntable. No hands, so it must be dropped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REAL = json.loads((Path(__file__).parent / "real_captions.json").read_text())


@dataclass
class GoldCase:
    """One judgement with its expected answer."""

    name: str
    why: str
    caption_segments: list[dict[str, Any]]
    duration_seconds: int | None = None
    title: str | None = None
    media: dict[str, Any] = field(default_factory=dict)
    regression: bool = False

    # --- what the answer has to be -------------------------------------
    hands_visible: bool | None = None
    viewpoint: str | None = None
    is_footage: bool | None = None
    accepted: bool | None = None
    blocking_gates: list[str] | None = None
    min_anchors: int | None = None
    max_anchors: int | None = None
    max_anchor_seconds: float | None = None
    hand_ratio_at_least: float | None = None
    idle_detected: bool | None = None

    @property
    def caption(self) -> str:
        return " ".join(str(s.get("text") or "") for s in self.caption_segments).strip()


def _real(name: str) -> dict[str, Any]:
    return _REAL[name]


def _segments(*spans: tuple[float, float, str]) -> list[dict[str, Any]]:
    return [{"start": a, "end": b, "text": t} for a, b, t in spans]


REAL_CASES: list[GoldCase] = [
    GoldCase(
        name="soldering",
        why="Head-mounted soldering: hands stated explicitly, one worker, clean take.",
        caption_segments=_real("soldering")["segments"],
        duration_seconds=_real("soldering")["duration_seconds"],
        title=_real("soldering")["title"],
        media={
            "source_url": "datalake://soldering",
            "uploader": "memories.ai internal set",
            "duration_seconds": 75,
            "container": "mp4",
        },
        hands_visible=True,
        viewpoint="egocentric",
        is_footage=True,
        accepted=True,
        blocking_gates=[],
        min_anchors=1,
        hand_ratio_at_least=0.9,
    ),
    GoldCase(
        name="wrist_camera",
        why="Wrist-camera wire harnessing. 'Slides the sleeve over the wires' must "
        "not be read as slideware, and 499s must not become one action.",
        regression=True,
        caption_segments=_real("wrist_camera")["segments"],
        duration_seconds=_real("wrist_camera")["duration_seconds"],
        title=_real("wrist_camera")["title"],
        media={
            "source_url": "datalake://wrist",
            "uploader": "memories.ai internal set",
            "duration_seconds": 499,
            "container": "mp4",
        },
        hands_visible=True,
        viewpoint="egocentric",
        is_footage=True,
        accepted=True,
        blocking_gates=[],
        min_anchors=3,
        max_anchor_seconds=125.0,
        hand_ratio_at_least=0.8,
    ),
    GoldCase(
        name="ego_harness",
        why="40 minutes of egocentric assembly. A passing colleague must not veto "
        "the clip, and the anchors must be action-sized.",
        regression=True,
        caption_segments=_real("ego_harness")["segments"],
        duration_seconds=_real("ego_harness")["duration_seconds"],
        title=_real("ego_harness")["title"],
        media={
            "source_url": "datalake://ego002",
            "uploader": "memories.ai internal set",
            "duration_seconds": 2388,
            "container": "mp4",
        },
        hands_visible=True,
        viewpoint="egocentric",
        is_footage=True,
        accepted=True,
        blocking_gates=[],
        min_anchors=10,
        max_anchor_seconds=125.0,
        hand_ratio_at_least=0.9,
        idle_detected=True,
    ),
    GoldCase(
        name="medical_tubing",
        why="Someone else is in half of this one, so it has to be rejected — the "
        "counterweight to the two cases above.",
        regression=True,
        caption_segments=_real("medical_tubing")["segments"],
        duration_seconds=_real("medical_tubing")["duration_seconds"],
        title=_real("medical_tubing")["title"],
        media={
            "source_url": "datalake://medical",
            "uploader": "memories.ai internal set",
            "duration_seconds": 65,
            "container": "mp4",
        },
        hands_visible=True,
        viewpoint="egocentric",
        accepted=False,
        blocking_gates=["G1-OTHERFACE"],
    ),
]

SYNTHETIC_CASES: list[GoldCase] = [
    GoldCase(
        name="rotating_pot",
        why="Search said cooking; the frames are a pot on a turntable. No hands.",
        regression=True,
        caption_segments=_segments(
            (
                0.0,
                34.0,
                "A blue ceramic pot with white floral patterns and a silver metal lid "
                "slowly rotates on a white surface. The lid features intricate "
                "embossed designs and a small lever-like handle.",
            )
        ),
        duration_seconds=34,
        title="Senftegerl (Commons)",
        hands_visible=False,
        accepted=False,
        min_anchors=0,
        max_anchors=0,
    ),
    GoldCase(
        name="screen_recording",
        why="A screen recording is not footage of the world, however well it matches.",
        caption_segments=_segments(
            (0.0, 60.0, "A screen recording of a spreadsheet; the cursor moves between cells.")
        ),
        duration_seconds=60,
        is_footage=False,
        accepted=False,
    ),
    GoldCase(
        name="chop_then_stir",
        why="Chopping and then stirring is two actions, with no pause between them.",
        regression=True,
        caption_segments=_segments(
            (0.0, 40.0, "The right hand chops an onion on the board"),
            (40.0, 90.0, "The right hand stirs the pan with a wooden spoon"),
        ),
        duration_seconds=90,
        hands_visible=True,
        accepted=True,
        min_anchors=2,
        max_anchors=2,
    ),
    GoldCase(
        name="first_segment_at_zero",
        why="A segment starting at 0.0 must not be dropped by a falsy-zero check.",
        regression=True,
        caption_segments=_segments((0.0, 40.0, "the left hand seats the connector")),
        duration_seconds=40,
        hands_visible=True,
        accepted=True,
        min_anchors=1,
    ),
    GoldCase(
        name="colleague_in_one_span",
        why="One colleague span in twelve is 8% of the footage: drop the span, "
        "keep the clip. The anchors split around it.",
        regression=True,
        caption_segments=_segments(
            *[
                (
                    float(i * 10),
                    float((i + 1) * 10),
                    "a colleague reaches in to hold the jig"
                    if i == 6
                    else "the left hand seats the connector",
                )
                for i in range(12)
            ]
        ),
        duration_seconds=120,
        hands_visible=True,
        accepted=True,
        min_anchors=2,
        max_anchors=2,
        blocking_gates=[],
    ),
    GoldCase(
        name="colleague_in_a_third_of_it",
        why="A third of the footage with someone else in it is the clip's "
        "character, not an incident: it is scrapped.",
        caption_segments=_segments(
            (0.0, 30.0, "the left hand seats the connector"),
            (30.0, 60.0, "a colleague reaches in to hold the jig"),
            (60.0, 90.0, "the left hand seats the next connector"),
        ),
        duration_seconds=90,
        hands_visible=True,
        accepted=False,
        blocking_gates=["G1-OTHERFACE"],
    ),
    GoldCase(
        name="wide_shot_no_hands",
        why="A kitchen with nobody's hands in it is not manipulation data.",
        caption_segments=_segments(
            (0.0, 120.0, "A wide shot of a kitchen. Steam rises from a pot on the stove.")
        ),
        duration_seconds=120,
        hands_visible=False,
        accepted=False,
        min_anchors=0,
        max_anchors=0,
    ),
    GoldCase(
        name="exocentric_demo",
        why="A fixed-camera demonstration is exocentric and must not pass as ego.",
        caption_segments=_segments(
            (
                0.0,
                200.0,
                "A third-person view from a fixed camera on a tripod. The hands of a "
                "chef work at a counter across the room.",
            )
        ),
        duration_seconds=200,
        title="Knife skills demonstration, static camera",
        viewpoint="exocentric",
        hands_visible=True,
    ),
]

ALL_CASES: list[GoldCase] = REAL_CASES + SYNTHETIC_CASES
