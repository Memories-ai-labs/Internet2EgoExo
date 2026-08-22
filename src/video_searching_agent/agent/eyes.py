"""Frames from an indexed video, so an agent can look instead of inferring.

Every judgement in this pipeline used to be read off caption *wording*: whether
hands are in frame, whether the camera is worn, whether a span is one action.
Caption text is a real signal and it is also a lossy one, and the failures were
the kind you only find by looking. A vertical phone clip of somebody using a
washing machine was rejected on a hand density of 43% computed from words like
"pours" and "places", when what actually disqualified it — 9:16 with a burned-in
watermark — was sitting in the pixels.

So this is the eyes. Given a video and a span, it cuts the span through the
Datalake, pulls frames out of the file, and hands them back as images an agent
can be shown. Three things it is careful about:

**Cost.** A cut is $0.005 and a look is around $0.002, so a loop that samples
freely gets expensive fast. Frames are cached per (video, span, count) for the
life of the agent, so re-examining a span it has already seen is free.

**Truth.** Frames come from the file, not from a thumbnail service. A YouTube
thumbnail is chosen to attract a click; frame 400 of the actual clip is
evidence.

**Honesty about failure.** A span that cannot be cut returns no frames and says
why. An agent that cannot see must abstain rather than guess, and it can only do
that if the difference is visible to it.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)

logger = logging.getLogger(__name__)

# What one look costs, so a caller can be told before it spends.
CUT_COST_USD = 0.005

# Frames wider than this waste tokens without adding detail for these questions
# — is a hand in frame, is this portrait, is there an overlay.
FRAME_WIDTH = 640

# More than this per span stops paying for itself: the questions being asked are
# about the span as a whole, not about individual moments.
MAX_FRAMES_PER_LOOK = 8

# Longer than this and a cut is slow and large for no benefit; the frames are
# sampled across the span either way.
MAX_CUT_SECONDS = 120.0


@dataclass
class Frames:
    """What a look returned."""

    video_id: str
    start: float
    end: float
    images: list[bytes] = field(default_factory=list)
    width: int | None = None
    height: int | None = None
    error: str | None = None
    cost_usd: float = 0.0

    @property
    def looked(self) -> bool:
        return bool(self.images)

    @property
    def orientation(self) -> str | None:
        """`portrait`, `landscape` or None when it could not be measured."""

        if not self.width or not self.height:
            return None
        return "portrait" if self.height > self.width else "landscape"

    def describe(self) -> str:
        """One line an agent can read as an observation."""

        if not self.looked:
            return f"could not look at {self.start:.0f}s–{self.end:.0f}s: {self.error}"
        shape = (
            f"{self.width}x{self.height} ({self.orientation})"
            if self.width and self.height
            else "dimensions unmeasured"
        )
        return (
            f"{len(self.images)} frames sampled across {self.start:.0f}s–{self.end:.0f}s, "
            f"source is {shape}"
        )


class Eyes:
    """Cuts spans and extracts frames, with a cache and a spending record."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        ffmpeg: str | None = None,
    ) -> None:
        """Initialize.

        Args:
            client: Datalake client. Created on first use when omitted.
            ffmpeg: Path to an ffmpeg binary. Found automatically when omitted;
                looking is unavailable without one, which is reported rather
                than crashed on.
        """
        self._client = client
        self._ffmpeg = ffmpeg
        self._cache: dict[tuple[str, int, int, int], Frames] = {}
        self.spent_usd = 0.0
        self.looks = 0

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def ffmpeg(self) -> str | None:
        """An ffmpeg to extract with, or None if there is none available."""

        if self._ffmpeg is None:
            self._ffmpeg = shutil.which("ffmpeg") or _bundled_ffmpeg() or ""
        return self._ffmpeg or None

    @property
    def available(self) -> bool:
        """Whether looking is possible at all in this environment."""

        return self.ffmpeg is not None

    async def look(
        self,
        video_id: str,
        start: float,
        end: float,
        count: int = 4,
    ) -> Frames:
        """Sample frames across a span.

        Repeated calls for the same span and count are served from the cache, so
        an agent that reconsiders a span it has already seen pays once.
        """
        count = max(1, min(count, MAX_FRAMES_PER_LOOK))
        start = max(0.0, float(start))
        end = max(start + 0.5, float(end))
        if end - start > MAX_CUT_SECONDS:
            # Sample across the middle rather than cutting something huge.
            middle = (start + end) / 2
            start, end = middle - MAX_CUT_SECONDS / 2, middle + MAX_CUT_SECONDS / 2
            start = max(0.0, start)

        key = (video_id, int(start), int(end), count)
        if key in self._cache:
            return self._cache[key]

        result = await self._look(video_id, start, end, count)
        self._cache[key] = result
        return result

    async def _look(self, video_id: str, start: float, end: float, count: int) -> Frames:
        frames = Frames(video_id=video_id, start=start, end=end)
        if not self.available:
            frames.error = "no ffmpeg available, so frames cannot be extracted"
            return frames

        try:
            payload = await self.client.get_clip(video_id, start, end)
        except MemoriesDatalakeError as exc:
            frames.error = str(exc)[:200]
            return frames
        url = payload.get("url") if isinstance(payload, dict) else None
        if not url:
            frames.error = "the cut returned no URL"
            return frames

        frames.cost_usd = CUT_COST_USD
        self.spent_usd += CUT_COST_USD
        self.looks += 1

        try:
            frames.images, frames.width, frames.height = await asyncio.to_thread(
                self._extract, str(url), end - start, count
            )
        except Exception as exc:  # noqa: BLE001 - a failed look is an observation
            frames.error = str(exc)[:200]
            logger.info("frame extraction failed for %s: %s", video_id, exc)
        if not frames.images and not frames.error:
            frames.error = "the clip yielded no frames"
        return frames

    def _extract(
        self, url: str, span_seconds: float, count: int
    ) -> tuple[list[bytes], int | None, int | None]:
        """Download the cut and pull `count` frames out of it."""
        import urllib.request

        from video_searching_agent.pipeline.media_probe import read_mp4_dimensions

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            video = root / "span.mp4"
            with urllib.request.urlopen(url, timeout=180) as response:
                video.write_bytes(response.read())

            dimensions = read_mp4_dimensions(video)
            # One frame every `step` seconds, spread across the span rather than
            # bunched at the front, because the front of a clip is often a title.
            step = max(1.0, span_seconds / (count + 1))
            subprocess.run(
                [
                    str(self.ffmpeg),
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(video),
                    "-vf",
                    f"fps=1/{step:.3f},scale={FRAME_WIDTH}:-2",
                    "-frames:v",
                    str(count),
                    str(root / "frame_%02d.jpg"),
                ],
                check=True,
                capture_output=True,
                timeout=180,
            )
            images = [path.read_bytes() for path in sorted(root.glob("frame_*.jpg"))]

        width, height = dimensions if dimensions else (None, None)
        return images, width, height


def _bundled_ffmpeg() -> str | None:
    """An ffmpeg shipped with a Python package, if one is installed.

    Not a hard dependency: the pipeline works without looking, less well, and a
    deployment that cannot extract frames should say so rather than fail to
    start.
    """
    try:
        import imageio_ffmpeg

        return str(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:  # noqa: BLE001
        return None
