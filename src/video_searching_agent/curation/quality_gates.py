"""The first-person data quality gates, as executable checks.

Implements the internal standard (*First-Person Data Quality Standard &
Acceptance Criteria v1.0*) for footage collected off the web:

* **Gate 0 — rights.** Licensing and provenance. A hard veto: unclear licensing
  makes a clip worth zero no matter how good it looks, and the standard is
  explicit that this must be blocked by a data field, not by memory. Hence
  ``commercial_use_ok`` on every record.
* **Gate 1 — media usability.** Machine-decidable, run over everything:
  orientation, resolution, frame rate, the wearer's own hands in frame, glove
  fit, other people's hands and faces, editing, blur.
* **Gate 2 — annotation depth.** L0–L3, where L2 (a task → action hierarchy
  with its own text per level, anchored in time and *not* cut into clips) is
  the minimum trainable grade and L3 adds event-level detail.
* **Gate 3 — diversity and deduplication.** Dataset level, not per clip.

Two rules are load-bearing and easy to get wrong:

1. **The four hour measures never mix.** ``worn`` / ``delivered`` /
   ``accepted`` / ``accepted_labeled`` mean different things; reporting a
   delivered hour as an accepted hour inflates the books by 30-40%.
2. **Nothing is scored on a number we did not measure.** Checks we cannot
   compute from available inputs report ``measured=False`` and are excluded
   from the score rather than being assumed to pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# --------------------------------------------------------------------- levels


class AnnotationLevel(StrEnum):
    """Annotation depth. L2 is the minimum trainable, L3 is what sells."""

    L0 = "L0"  # metadata only
    L1 = "L1"  # flat caption / coarse labels
    L2 = "L2"  # task -> action hierarchy, own text per level, time anchors
    L3 = "L3"  # + events, objects, hand state, error/rework samples


LEVEL_POINTS = {
    AnnotationLevel.L0: 0,
    AnnotationLevel.L1: 10,
    AnnotationLevel.L2: 22,
    AnnotationLevel.L3: 30,
}


class Grade(StrEnum):
    """Batch disposition from the 100-point scorecard."""

    A = "A"  # >=85 main training set + sellable
    B = "B"  # 70-84 main training set, not external
    C = "C"  # 55-69 pretrain / diversity supplement only
    D = "D"  # <55 not ingested


# ------------------------------------------------------------------ thresholds

MIN_HAND_FRAME_RATIO = 0.60
RESOLUTION_A_HEIGHT = 1080
RESOLUTION_B_HEIGHT = 720
RESOLUTION_UNUSABLE_HEIGHT = 480
MIN_FPS = 30
MAX_IDLE_RATIO = 0.15
MAX_UNUSABLE_FRAME_RATIO = 0.10

LICENSES_PERMITTING_COMMERCIAL_USE = frozenset(
    {"creativecommon", "creative_commons", "cc-by", "cc0", "public", "apache-2.0", "cc-by-sa"}
)

# Cue sets for the caption-readable Gate 1 items.
_OTHER_PERSON_CUES = (
    "another person",
    "another man",
    "another woman",
    "second person",
    "two people",
    "three people",
    "several people",
    "a group of people",
    "someone else",
    "other people",
    "bystander",
    "colleague",
    "coworker",
    "a man facing",
    "a woman facing",
    "faces the camera",
    "looking at the camera",
    "a crowd",
)
_OTHER_HAND_CUES = (
    "another hand",
    "someone else's hand",
    "second pair of hands",
    "two pairs of hands",
    "their hands reach in",
    "an assistant",
)
_LOOSE_GLOVE_CUES = (
    "loose glove",
    "oversized glove",
    "baggy glove",
    "thick glove",
    "bulky glove",
    "heavy work glove",
    "welding glove",
    "oven mitt",
    "mitten",
)
_EDIT_CUES = (
    "compilation",
    "montage",
    "time-lapse",
    "timelapse",
    "sped up",
    "speed ramp",
    "jump cut",
    "quick cuts",
    "transition effect",
    "split screen",
    "picture in picture",
    "text overlay",
    "subscribe",
    "intro animation",
)
_IDLE_CUES = (
    "empty",
    "nobody",
    "no one is",
    "static shot",
    "nothing happens",
    "waiting",
    "idle",
)


# ----------------------------------------------------------------- structures


@dataclass
class GateCheck:
    """One named threshold, and whether this clip met it."""

    check_id: str
    name: str
    passed: bool = False
    measured: bool = True
    blocking: bool = False
    value: Any = None
    threshold: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.check_id,
            "name": self.name,
            "passed": self.passed,
            "measured": self.measured,
            "blocking": self.blocking,
            "value": self.value,
            "threshold": self.threshold,
            "detail": self.detail,
        }


@dataclass
class HoursLedger:
    """The four hour measures, kept apart on purpose."""

    worn_hours: float = 0.0
    delivered_hours: float = 0.0
    accepted_hours: float = 0.0
    accepted_labeled_hours: float = 0.0
    idle_hours: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "worn_hours": round(self.worn_hours, 3),
            "delivered_hours": round(self.delivered_hours, 3),
            "accepted_hours": round(self.accepted_hours, 3),
            "accepted_labeled_hours": round(self.accepted_labeled_hours, 3),
            "idle_hours": round(self.idle_hours, 3),
            "media_yield": (
                round(self.accepted_hours / self.delivered_hours, 3)
                if self.delivered_hours
                else 0.0
            ),
        }


@dataclass
class QualityReport:
    """A clip's standing against the standard."""

    checks: list[GateCheck] = field(default_factory=list)
    annotation_level: AnnotationLevel = AnnotationLevel.L0

    score: int = 0
    grade: Grade = Grade.D
    accepted: bool = False
    commercial_use_ok: bool = False

    usable_seconds: int = 0
    idle_seconds: int = 0

    blocking_failures: list[str] = field(default_factory=list)
    unmeasured: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def check(self, check_id: str) -> GateCheck | None:
        """Look one check up by id."""
        return next((c for c in self.checks if c.check_id == check_id), None)

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "grade": self.grade.value,
            "accepted": self.accepted,
            "commercial_use_ok": self.commercial_use_ok,
            "annotation_level": self.annotation_level.value,
            "usable_seconds": self.usable_seconds,
            "idle_seconds": self.idle_seconds,
            "blocking_failures": self.blocking_failures,
            "unmeasured": self.unmeasured,
            "notes": self.notes,
            "checks": [c.as_dict() for c in self.checks],
        }


# ------------------------------------------------------------------ gate logic


def _cues(haystack: str, cues: tuple[str, ...]) -> list[str]:
    return [cue for cue in cues if cue in haystack]


def mentions_idle(text: str | None) -> list[str]:
    """Idle cues in a piece of caption text.

    Idle time is paid for and never trained on, so it is found and subtracted
    rather than quietly averaged in. Exposed per segment for the cleaning agent.
    """
    if not text or not text.strip():
        return []
    return _cues(text.lower(), _IDLE_CUES)


def permits_commercial_use(license_value: str | None) -> bool:
    """Gate 0: does the licence text permit commercial training use?"""
    if not license_value:
        return False
    normalised = re.sub(r"[\s_]+", "", license_value.strip().lower())
    return normalised in {re.sub(r"[\s_]+", "", v) for v in LICENSES_PERMITTING_COMMERCIAL_USE}


def hand_frame_ratio(caption_segments: list[dict[str, Any]] | None) -> float | None:
    """Share of caption segments that mention a hand.

    This is the honest proxy for `G1-HAND` ("fraction of frames containing the
    wearer's own hands"): we have caption segments, not per-frame detections, so
    the unit is segments and the number is reported as such. Returns None when
    there are no segments to measure.
    """
    if not caption_segments:
        return None
    hand_pattern = re.compile(r"\b(hand|hands|fingers|thumb|palm|gloved)\b")
    total = 0
    with_hands = 0
    for segment in caption_segments:
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text") or "").lower()
        if not text.strip():
            continue
        total += 1
        if hand_pattern.search(text):
            with_hands += 1
    if not total:
        return None
    return round(with_hands / total, 3)


def evaluate_clip(
    *,
    license_value: str | None = None,
    source_url: str | None = None,
    uploader: str | None = None,
    width: int | None = None,
    height: int | None = None,
    fps: float | None = None,
    duration_seconds: int | None = None,
    container: str | None = None,
    caption: str | None = None,
    caption_segments: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    require_commercial_use: bool = True,
) -> QualityReport:
    """Run Gate 0-2 over one clip and score it.

    Gate 3 is dataset level; see :func:`evaluate_dataset`.

    Every argument is optional because a clip is judged at whatever stage it has
    reached — a candidate has no captions yet, and an unindexed download has no
    annotations. Checks that cannot be computed are recorded as unmeasured and
    left out of the score.
    """
    report = QualityReport()
    visual = (caption or "").lower()

    # ------------------------------------------------------ Gate 0: rights
    commercial_ok = permits_commercial_use(license_value)
    report.commercial_use_ok = commercial_ok
    report.checks.append(
        GateCheck(
            "G0-LIC",
            "Licence permits commercial training use",
            passed=commercial_ok,
            blocking=require_commercial_use,
            value=license_value or "unknown",
            threshold="explicit commercial-use permission",
            detail=(
                None
                if commercial_ok
                else "licence unknown or non-commercial; barred from the training set"
            ),
        )
    )

    provenance_fields = {"source_url": source_url, "uploader": uploader, "license": license_value}
    missing = [name for name, value in provenance_fields.items() if not value]
    present = len(provenance_fields) - len(missing)
    report.checks.append(
        GateCheck(
            "G0-PROV",
            "Provenance complete",
            passed=not missing,
            # No provenance at all means none was handed to us — that is an
            # unmeasured check, not a clip whose paperwork is incomplete.
            measured=present > 0,
            # Scored, not vetoed: the rights veto is G0-LIC, which the caller
            # turns on at delivery. An incomplete record costs points here and
            # bars external delivery there, rather than being two vetoes.
            blocking=False,
            value=f"{present}/{len(provenance_fields)} fields",
            threshold="source_url, uploader and licence all present",
            detail=f"missing: {', '.join(missing)}" if missing else None,
        )
    )

    # ------------------------------------------------ Gate 1: media usability
    if width and height:
        landscape = width >= height
        report.checks.append(
            GateCheck(
                "G1-ORIENT",
                "Landscape orientation",
                passed=landscape,
                value=f"{width}x{height}",
                threshold="width >= height",
                detail=None if landscape else "portrait footage is scrapped by the standard",
            )
        )
    else:
        report.checks.append(
            GateCheck(
                "G1-ORIENT",
                "Landscape orientation",
                measured=False,
                threshold="width >= height",
            )
        )

    if height:
        if height >= RESOLUTION_A_HEIGHT:
            res_detail, res_pass = "A (>=1080p)", True
        elif height >= RESOLUTION_B_HEIGHT:
            res_detail, res_pass = "B (720p, coarse-grained only)", True
        elif height > RESOLUTION_UNUSABLE_HEIGHT:
            res_detail, res_pass = "below 720p", False
        else:
            res_detail, res_pass = "<=480p, unusable for hands or fine manipulation", False
        report.checks.append(
            GateCheck(
                "G1-RES",
                "Resolution",
                passed=res_pass,
                value=f"{height}p",
                threshold=">=1080p for grade A, >=720p to pass",
                detail=res_detail,
            )
        )
    else:
        report.checks.append(
            GateCheck("G1-RES", "Resolution", measured=False, threshold=">=720p")
        )

    if fps:
        report.checks.append(
            GateCheck(
                "G1-FPS",
                "Frame rate",
                passed=fps >= MIN_FPS,
                value=round(float(fps), 2),
                threshold=f">={MIN_FPS} fps",
                detail=None if fps >= MIN_FPS else "below the temporal-annotation floor",
            )
        )
    else:
        report.checks.append(
            GateCheck("G1-FPS", "Frame rate", measured=False, threshold=f">={MIN_FPS} fps")
        )

    ratio = hand_frame_ratio(caption_segments)
    if ratio is None and visual:
        # No segments, but there is caption text: fall back to presence/absence.
        has_hand = bool(re.search(r"\b(hand|hands|fingers|thumb|palm)\b", visual))
        report.checks.append(
            GateCheck(
                "G1-HAND",
                "Wearer's own hands in frame",
                passed=has_hand,
                value="mentioned" if has_hand else "not mentioned",
                threshold=f">={int(MIN_HAND_FRAME_RATIO * 100)}% of segments",
                detail="whole-caption fallback: no segment breakdown available",
            )
        )
    elif ratio is None:
        report.checks.append(
            GateCheck(
                "G1-HAND",
                "Wearer's own hands in frame",
                measured=False,
                threshold=f">={int(MIN_HAND_FRAME_RATIO * 100)}% of segments",
            )
        )
    else:
        report.checks.append(
            GateCheck(
                "G1-HAND",
                "Wearer's own hands in frame",
                passed=ratio >= MIN_HAND_FRAME_RATIO,
                blocking=True,
                value=ratio,
                threshold=f">={MIN_HAND_FRAME_RATIO:.0%} of caption segments",
                detail=(
                    None
                    if ratio >= MIN_HAND_FRAME_RATIO
                    else "first-person footage without hands is just ordinary video"
                ),
            )
        )

    if visual:
        loose = _cues(visual, _LOOSE_GLOVE_CUES)
        report.checks.append(
            GateCheck(
                "G1-GLOVE",
                "Glove fit",
                passed=not loose,
                value=", ".join(loose) if loose else "none seen",
                threshold="no gloves, or close-fitting",
                detail="loose gloves swallow hand shape and keypoints" if loose else None,
            )
        )

        other_hands = _cues(visual, _OTHER_HAND_CUES)
        report.checks.append(
            GateCheck(
                "G1-OTHERHAND",
                "No one else's hands in frame",
                passed=not other_hands,
                blocking=True,
                value=", ".join(other_hands) if other_hands else "none seen",
                threshold="only the wearer's hands",
                detail=(
                    "a second person's hands misattribute the action" if other_hands else None
                ),
            )
        )

        other_people = _cues(visual, _OTHER_PERSON_CUES)
        report.checks.append(
            GateCheck(
                "G1-OTHERFACE",
                "No one else's face in frame",
                passed=not other_people,
                blocking=True,
                value=", ".join(other_people[:2]) if other_people else "none seen",
                threshold="no other person in frame",
                detail=(
                    "consent and de-identification risk, and the mount must be wrong"
                    if other_people
                    else None
                ),
            )
        )

        edits = _cues(visual, _EDIT_CUES)
        report.checks.append(
            GateCheck(
                "G1-WHOLE",
                "One complete take, unedited",
                passed=not edits,
                value=", ".join(edits[:2]) if edits else "no edit cues",
                threshold="no splicing, speed changes or beautifying edits",
                detail="splicing manufactures causality that never happened" if edits else None,
            )
        )
    else:
        for check_id, name in (
            ("G1-GLOVE", "Glove fit"),
            ("G1-OTHERHAND", "No one else's hands in frame"),
            ("G1-OTHERFACE", "No one else's face in frame"),
            ("G1-WHOLE", "One complete take, unedited"),
        ):
            report.checks.append(GateCheck(check_id, name, measured=False))

    if container:
        ok_container = container.lower() in ("mp4", "m4v", "mov")
        report.checks.append(
            GateCheck(
                "G1-CODEC",
                "Container and integrity",
                passed=ok_container,
                value=container,
                threshold="H.264/H.265 MP4",
            )
        )

    # Idle: caption-readable only, and only as a coarse signal.
    if caption_segments:
        idle_segments = sum(
            1
            for segment in caption_segments
            if isinstance(segment, dict)
            and _cues(str(segment.get("text") or "").lower(), _IDLE_CUES)
        )
        total_segments = sum(
            1 for segment in caption_segments if isinstance(segment, dict) and segment.get("text")
        )
        idle_ratio = round(idle_segments / total_segments, 3) if total_segments else 0.0
        report.checks.append(
            GateCheck(
                "G1-IDLE",
                "Idle share",
                passed=idle_ratio <= MAX_IDLE_RATIO,
                value=idle_ratio,
                threshold=f"<={MAX_IDLE_RATIO:.0%}, and marked",
            )
        )
        if duration_seconds:
            report.idle_seconds = int(duration_seconds * idle_ratio)
            report.usable_seconds = duration_seconds - report.idle_seconds
    elif duration_seconds:
        report.usable_seconds = duration_seconds
        report.checks.append(GateCheck("G1-IDLE", "Idle share", measured=False))

    # --------------------------------------------- Gate 2: annotation depth
    report.annotation_level = grade_annotation_level(annotations, caption=caption)
    report.checks.extend(structural_checks(annotations))

    # ------------------------------------------------------------- scoring
    _score(report)
    return report


def grade_annotation_level(
    annotations: list[dict[str, Any]] | None,
    caption: str | None = None,
) -> AnnotationLevel:
    """Grade annotation depth L0-L3.

    L2 requires a real hierarchy — a task level and action entries with their
    own text and time anchors. A single caption for a whole video is L1 no
    matter how good it is.
    """
    entries = [a for a in (annotations or []) if isinstance(a, dict)]
    if not entries:
        return AnnotationLevel.L1 if caption else AnnotationLevel.L0

    levels = {str(entry.get("hier_level") or "").lower() for entry in entries}
    has_task = "task" in levels
    has_action = "action" in levels
    has_event = "event" in levels

    anchored_actions = [
        entry
        for entry in entries
        if str(entry.get("hier_level") or "").lower() == "action"
        and entry.get("span_start") is not None
        and entry.get("span_end") is not None
    ]

    if not (has_task and has_action and anchored_actions):
        return AnnotationLevel.L1

    l3_signals = any(
        entry.get("objects") or entry.get("left_hand") or entry.get("right_hand")
        for entry in entries
    )
    if has_event and l3_signals:
        return AnnotationLevel.L3
    return AnnotationLevel.L2


def structural_checks(annotations: list[dict[str, Any]] | None) -> list[GateCheck]:
    """The machine-decidable hierarchy rules (`G2-TREE-*`)."""
    entries = [a for a in (annotations or []) if isinstance(a, dict)]
    if not entries:
        return [
            GateCheck("G2-TREE-1", "Child spans inside their parent", measured=False),
            GateCheck("G2-TREE-2", "Sibling spans do not overlap", measured=False),
            GateCheck("G2-TREE-3", "Each level has its own text", measured=False),
            GateCheck("G2-TREE-5", "No clips delivered, anchors only", measured=False),
        ]

    by_id = {str(entry.get("segment_id")): entry for entry in entries if entry.get("segment_id")}

    # G2-TREE-1: a child's range sits inside its parent's.
    contained = overruns = 0
    for entry in entries:
        parent_id = entry.get("parent_segment_id")
        parent = by_id.get(str(parent_id)) if parent_id else None
        if not parent:
            continue
        child_start, child_end = entry.get("span_start"), entry.get("span_end")
        parent_start, parent_end = parent.get("span_start"), parent.get("span_end")
        if None in (child_start, child_end, parent_start, parent_end):
            continue
        if float(child_start) >= float(parent_start) - 0.001 and float(child_end) <= float(
            parent_end
        ) + 0.001:
            contained += 1
        else:
            overruns += 1

    checks = [
        GateCheck(
            "G2-TREE-1",
            "Child spans inside their parent",
            passed=overruns == 0,
            measured=bool(contained or overruns),
            value=f"{overruns} overrun(s)",
            threshold="100% contained",
        )
    ]

    # G2-TREE-2: siblings must not overlap.
    overlaps = 0
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        by_parent.setdefault(str(entry.get("parent_segment_id") or "root"), []).append(entry)
    for siblings in by_parent.values():
        spans = sorted(
            (
                (float(s.get("span_start")), float(s.get("span_end")))
                for s in siblings
                if s.get("span_start") is not None and s.get("span_end") is not None
            ),
        )
        for earlier, later in zip(spans, spans[1:], strict=False):
            if later[0] < earlier[1] - 0.001:
                overlaps += 1
    checks.append(
        GateCheck(
            "G2-TREE-2",
            "Sibling spans do not overlap",
            passed=overlaps == 0,
            value=f"{overlaps} overlap(s)",
            threshold="no overlap between siblings",
        )
    )

    # G2-TREE-3: no copying the parent's text down to a child.
    duplicated = 0
    for entry in entries:
        parent = by_id.get(str(entry.get("parent_segment_id"))) if entry.get(
            "parent_segment_id"
        ) else None
        if not parent:
            continue
        child_text = (entry.get("label") or "") + (entry.get("narration") or "")
        parent_text = (parent.get("label") or "") + (parent.get("narration") or "")
        if child_text and child_text.strip() == parent_text.strip():
            duplicated += 1
    checks.append(
        GateCheck(
            "G2-TREE-3",
            "Each level has its own text",
            passed=duplicated == 0,
            value=f"{duplicated} copied",
            threshold="<=2% cross-level duplication",
        )
    )

    # G2-TREE-5: annotations are time anchors, never delivered clip files.
    cut_files = sum(1 for entry in entries if entry.get("clip_file"))
    checks.append(
        GateCheck(
            "G2-TREE-5",
            "No clips delivered, anchors only",
            passed=cut_files == 0,
            value=f"{cut_files} cut file(s)",
            threshold="every annotation is a [start, end] anchor on the whole video",
        )
    )
    return checks


def _score(report: QualityReport) -> None:
    """Fill in score, grade and acceptance from the checks.

    Weights follow the standard's scorecard: annotation 45, diversity 25 (only
    the part measurable per clip is credited here), media 20, licensing 10.
    Unmeasured checks are excluded rather than assumed.
    """
    def passed(check_id: str) -> bool | None:
        check = report.check(check_id)
        if check is None or not check.measured:
            return None
        return check.passed

    report.unmeasured = [c.check_id for c in report.checks if not c.measured]
    report.blocking_failures = [
        c.check_id for c in report.checks if c.blocking and c.measured and not c.passed
    ]

    # --- annotation depth and quality: 45 -------------------------------
    score = LEVEL_POINTS[report.annotation_level]
    structural = [
        passed("G2-TREE-1"),
        passed("G2-TREE-2"),
        passed("G2-TREE-3"),
        passed("G2-TREE-5"),
    ]
    measured_structural = [value for value in structural if value is not None]
    if measured_structural:
        score += round(15 * sum(measured_structural) / len(measured_structural))

    # --- media quality: 20 ----------------------------------------------
    if passed("G1-RES"):
        score += 5
    hands = passed("G1-HAND")
    glove = passed("G1-GLOVE")
    hand_block = [value for value in (hands, glove) if value is not None]
    if hand_block:
        score += round(7 * sum(hand_block) / len(hand_block))
    others = [
        value
        for value in (passed("G1-OTHERHAND"), passed("G1-OTHERFACE"))
        if value is not None
    ]
    if others:
        score += round(4 * sum(others) / len(others))
    integrity = [
        value
        for value in (passed("G1-FPS"), passed("G1-ORIENT"), passed("G1-WHOLE"), passed("G1-CODEC"))
        if value is not None
    ]
    if integrity:
        score += round(4 * sum(integrity) / len(integrity))

    # --- licensability and provenance: 10 -------------------------------
    if passed("G0-LIC"):
        score += 7
    if passed("G0-PROV"):
        score += 3

    # Diversity is a dataset property; per clip it stays uncredited and is
    # noted so a single clip can never read as an A on its own.
    report.notes.append("Gate 3 (diversity/dedup) is scored per dataset, not per clip")

    report.score = min(score, 100)
    report.grade = (
        Grade.A
        if report.score >= 85
        else Grade.B
        if report.score >= 70
        else Grade.C
        if report.score >= 55
        else Grade.D
    )
    report.accepted = not report.blocking_failures and report.grade != Grade.D


def build_hours_ledger(
    delivered_seconds: float,
    accepted_seconds: float,
    idle_seconds: float = 0.0,
    labeled_seconds: float = 0.0,
) -> HoursLedger:
    """Assemble the four hour measures from second counts.

    Keeping them apart is the whole point: `delivered` is what landed on disk,
    `accepted` is what cleared Gate 0 and 1 with idle removed, and
    `accepted_labeled` is the only figure that may be quoted externally.
    """
    return HoursLedger(
        delivered_hours=delivered_seconds / 3600,
        accepted_hours=accepted_seconds / 3600,
        accepted_labeled_hours=labeled_seconds / 3600,
        idle_hours=idle_seconds / 3600,
    )


def evaluate_dataset(clips: list[dict[str, Any]]) -> list[GateCheck]:
    """Gate 3 checks, which only mean anything across a whole set.

    Deduplication against public corpora needs embeddings we do not compute
    here, so `G3-DUP` reports unmeasured rather than guessing.
    """
    if not clips:
        return []

    uploaders = [str(clip.get("creator") or clip.get("uploader") or "") for clip in clips]
    known = [name for name in uploaders if name]
    distinct = len(set(known))
    top_share = (
        max((known.count(name) for name in set(known)), default=0) / len(known) if known else 0.0
    )

    checks = [
        GateCheck(
            "G3-OP",
            "Operator diversity",
            passed=distinct >= 3 and top_share <= 0.5,
            measured=bool(known),
            value=f"{distinct} sources, top share {top_share:.0%}",
            threshold=">=3 sources, none above 50%",
        )
    ]

    families = {str(clip.get("task_family") or "").strip() for clip in clips}
    families.discard("")
    checks.append(
        GateCheck(
            "G3-SOP",
            "Task-family coverage",
            passed=len(families) >= 10,
            measured=bool(families),
            value=f"{len(families)} families",
            threshold=">=10 task families",
        )
    )

    error_samples = sum(1 for clip in clips if clip.get("error_sample"))
    error_share = error_samples / len(clips)
    checks.append(
        GateCheck(
            "G3-ERR",
            "Error / rework samples",
            passed=0.10 <= error_share <= 0.20,
            measured=error_samples > 0,
            value=f"{error_share:.0%}",
            threshold="10-20% of each task",
        )
    )

    checks.append(
        GateCheck(
            "G3-DUP",
            "Overlap with public corpora",
            measured=False,
            threshold="<=10%, cosine >=0.95 counts as duplicate",
            detail="needs OmniRetriever embeddings against the Egocentric-10K base",
        )
    )
    return checks
