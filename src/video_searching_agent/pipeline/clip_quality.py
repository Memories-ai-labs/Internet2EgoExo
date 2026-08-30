"""Fine-grained cleaning of a cut clip, from the pixels.

The gates before this one judge a *video*: its licence, its length, its
viewpoint, whether its captions mention hands. This judges a *clip* — the actual
cut span, decoded — and it is the step the pipeline did not have. The Datalake is
optimal on the read side (index, search, read); this is the write side (clean,
dedup, then hand a clean corpus back).

NVIDIA's cosmos-curate is the reference for this stage and it does **not** run
here: it is a Ray pipeline over NIM containers and needs GPUs, and it is not a
package you install. So these are equivalents, written natively, and named as
equivalents rather than as the thing they stand in for:

| cosmos-curate | here |
|---|---|
| motion filtering | mean absolute frame difference |
| aesthetic filtering | measured (see below) and deliberately **not** a gate |
| TransNetV2 shot detection | frame-difference peaks — an approximation, and a crude one |
| semantic dedup | the Datalake's own frame embeddings, not a local model |
| T5-XXL text embedding | not attempted |
| webdataset sharding | not attempted |

**What the calibration found, and why there is no blur filter.**

Nine spans across three real videos, decoded at 2fps and 256x144 grayscale:

| span | motion_mean | sharp_mean | what it actually is |
|---|---|---|---|
| a | 0.047 | **96** | a hand placing a cup into a wall bin — *usable* |
| b | 0.018 | **4144** | a channel's subscribe end card — *worthless* |
| c | 0.157 | 1119 | hands folding laundry — *usable* |

Sharpness (variance of the Laplacian) is the standard blur proxy and on this
footage it measures **texture, not quality**. The softest span in the sample is
good egocentric footage of a flat white surface; the sharpest is an outro card
full of text and thumbnails. A blur filter in either direction would have thrown
away the good clip and kept the graphic. So sharpness is measured, reported, and
never gated on — and a caller that wants to gate on it has the number and the
warning.

What *is* discriminating is the pair. Low motion with high sharpness is a title
card, an end card or a frozen graphic: still, and full of hard edges because the
edges are type. That is the one gate here, and it catches a real contaminant of
web-sourced clips that no metadata check sees.

Everything else — exposure clipping, the shot-cut guesses, the frame geometry —
is measured and carried, with `gated` saying plainly which measurements were
allowed to reject anything. Nothing is scored on a number that was not measured,
and nothing rejects on a number that was not calibrated.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Decode geometry. Small on purpose: these are aggregate statistics over a span,
# and 256x144 grayscale at 2fps is enough for every measurement here while
# keeping a ten-second clip under a megabyte of pixels.
DECODE_WIDTH = 256
DECODE_HEIGHT = 144
DECODE_FPS = 2.0
MAX_FRAMES = 48

# Calibrated from the table in the module docstring. A static graphic is the one
# thing the pair of measurements identifies without ambiguity: the end card sat
# at motion 0.018 / sharpness 4144, while the quietest real footage in the
# sample was 0.047 at sharpness 96.
STATIC_MOTION_MAX = 0.030
GRAPHIC_SHARPNESS_MIN = 2500.0

# Below this, a span is barely moving whatever it contains. The standard wants
# idle time marked rather than silently counted, and this is how a cut span gets
# marked. It is not a rejection on its own: a hand can rest mid-task.
IDLE_MOTION_MAX = 0.015

# A frame-difference spike this many times the span's median reads as a cut.
# Explicitly a guess at what TransNetV2 would say, and reported as a guess.
SHOT_CUT_RATIO = 4.0


@dataclass
class ClipMeasurement:
    """Numbers read off the decoded pixels of one clip.

    Every field is a measurement. None of them is a verdict, and the ones that
    were never computed are ``None`` rather than zero, because a zero here would
    read as "measured, and it was nothing".
    """

    frames: int = 0
    seconds: float = 0.0
    motion_mean: float | None = None
    motion_p90: float | None = None
    motion_max: float | None = None
    sharpness_mean: float | None = None
    sharpness_p10: float | None = None
    clipped_fraction: float | None = None
    width: int | None = None
    height: int | None = None
    # Seconds into the clip where a hard cut looks likely. An approximation of
    # shot detection, not shot detection.
    shot_cut_candidates: list[float] = field(default_factory=list)
    error: str | None = None

    @property
    def measured(self) -> bool:
        return self.error is None and self.frames >= 2

    def as_dict(self) -> dict[str, Any]:
        return {
            "frames": self.frames,
            "seconds": round(self.seconds, 2),
            "motion_mean": self.motion_mean,
            "motion_p90": self.motion_p90,
            "motion_max": self.motion_max,
            "sharpness_mean": self.sharpness_mean,
            "sharpness_p10": self.sharpness_p10,
            "clipped_fraction": self.clipped_fraction,
            "width": self.width,
            "height": self.height,
            "shot_cut_candidates": self.shot_cut_candidates,
            "error": self.error,
            "sharpness_note": (
                "texture, not quality: the softest usable span measured 96 and a "
                "subscribe end card measured 4144. Never gated on."
            ),
        }


@dataclass
class ClipVerdict:
    """What the fine-grained pass concluded, and on which numbers."""

    usable: bool = True
    reasons: list[str] = field(default_factory=list)
    # Which measurements were allowed to reject. Named so a reader never assumes
    # a number that is merely present was also enforced.
    gated: tuple[str, ...] = ("static_graphic",)
    notes: list[str] = field(default_factory=list)
    measurement: ClipMeasurement = field(default_factory=ClipMeasurement)

    def as_dict(self) -> dict[str, Any]:
        return {
            "usable": self.usable,
            "reasons": self.reasons,
            "gated_on": list(self.gated),
            "notes": self.notes,
            "measurement": self.measurement.as_dict(),
        }


def _ffmpeg() -> str | None:
    """The ffmpeg to decode with, system first then the wheel's."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
    except ImportError:
        return None
    try:
        return str(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:  # noqa: BLE001 - no decoder is a reason to abstain
        return None


def measure_clip(path: str, *, max_frames: int = MAX_FRAMES) -> ClipMeasurement:
    """Decode a clip and read the numbers off it.

    Returns a measurement with ``error`` set rather than raising: a clip that
    cannot be decoded has not been judged, and the caller keeps the clip.
    """
    measurement = ClipMeasurement()
    binary = _ffmpeg()
    if not binary:
        measurement.error = "no ffmpeg available to decode with"
        return measurement
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - numpy ships with the project
        measurement.error = "numpy unavailable"
        return measurement

    try:
        completed = subprocess.run(  # noqa: S603 - fixed binary, fixed args
            [
                binary,
                "-v",
                "error",
                "-i",
                path,
                "-vf",
                f"fps={DECODE_FPS},scale={DECODE_WIDTH}:{DECODE_HEIGHT},format=gray",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "gray",
                "-",
            ],
            capture_output=True,
            timeout=300,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        measurement.error = f"decode failed: {str(exc)[:150]}"
        return measurement
    if completed.returncode != 0:
        measurement.error = f"decode failed: {completed.stderr.decode()[:150]}"
        return measurement

    stride = DECODE_WIDTH * DECODE_HEIGHT
    count = len(completed.stdout) // stride
    if count < 2:
        measurement.error = f"only {count} frame(s) decoded"
        measurement.frames = count
        return measurement

    frames = (
        np.frombuffer(completed.stdout[: count * stride], dtype=np.uint8)
        .reshape(count, DECODE_HEIGHT, DECODE_WIDTH)
        .astype(np.float32)
    )
    if count > max_frames:
        frames = frames[:: max(1, count // max_frames)][:max_frames]

    measurement.frames = int(frames.shape[0])
    measurement.seconds = count / DECODE_FPS
    measurement.width = DECODE_WIDTH
    measurement.height = DECODE_HEIGHT

    diffs = np.abs(frames[1:] - frames[:-1]).mean(axis=(1, 2)) / 255.0
    measurement.motion_mean = round(float(diffs.mean()), 5)
    measurement.motion_p90 = round(float(np.percentile(diffs, 90)), 5)
    measurement.motion_max = round(float(diffs.max()), 5)

    sharp = _laplacian_variance(frames, np)
    measurement.sharpness_mean = round(float(sharp.mean()), 1)
    measurement.sharpness_p10 = round(float(np.percentile(sharp, 10)), 1)

    measurement.clipped_fraction = round(float(((frames <= 2) | (frames >= 253)).mean()), 5)

    # Where the difference spikes against the span's own median. Scale-free on
    # purpose: an absolute cut threshold would fire on every fast pan.
    median = float(np.median(diffs))
    if median > 0:
        spikes = np.nonzero(diffs > median * SHOT_CUT_RATIO)[0]
        measurement.shot_cut_candidates = [
            round(float(index + 1) / DECODE_FPS, 2) for index in spikes[:20]
        ]
    return measurement


def _laplacian_variance(frames: Any, np: Any) -> Any:
    """Variance of the Laplacian per frame — the standard sharpness proxy.

    Kept because the number is worth *reporting*. It is not worth gating on:
    see the calibration table in the module docstring.
    """
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    from numpy.lib.stride_tricks import sliding_window_view

    windows = sliding_window_view(frames, (3, 3), axis=(1, 2))
    response = (windows * kernel).sum(axis=(-1, -2))
    return response.var(axis=(1, 2))


def judge_clip(measurement: ClipMeasurement) -> ClipVerdict:
    """Decide whether a measured clip is worth keeping.

    One rejection, and it is the one the calibration supports: a span that
    barely moves and is full of hard edges is a title card or an end card, not
    footage. Everything else is recorded as a note.
    """
    verdict = ClipVerdict(measurement=measurement)
    if not measurement.measured:
        verdict.notes.append(
            f"not measured ({measurement.error or 'too few frames'}); kept unjudged"
        )
        return verdict

    motion = measurement.motion_mean or 0.0
    sharpness = measurement.sharpness_mean or 0.0

    if motion <= STATIC_MOTION_MAX and sharpness >= GRAPHIC_SHARPNESS_MIN:
        verdict.usable = False
        verdict.reasons.append(
            f"a static graphic, not footage: motion {motion:.3f} with sharpness "
            f"{sharpness:.0f} — the shape of a title or end card"
        )
        return verdict

    if motion <= IDLE_MOTION_MAX:
        # Marked, not rejected. Idle time has to be visible in the ledger rather
        # than silently counted as delivered footage, and a hand does rest.
        verdict.notes.append(f"barely any movement (motion {motion:.3f}) — idle span")

    if measurement.shot_cut_candidates:
        verdict.notes.append(
            f"{len(measurement.shot_cut_candidates)} possible shot cut(s) at "
            f"{measurement.shot_cut_candidates[:4]}s — a frame-difference guess, "
            "not shot detection"
        )
    if (measurement.clipped_fraction or 0.0) > 0.10:
        verdict.notes.append(
            f"{measurement.clipped_fraction:.1%} of pixels at the black or white "
            "limit; no exposure threshold is calibrated, so this does not reject"
        )
    return verdict
