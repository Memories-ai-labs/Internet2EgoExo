"""Look at the footage before downloading it.

Everything else in the screening step reads *words about* a video — a title, a
description, tags. That is why a run can come back with clips that are licence
clear and completely off topic: a video called "POV cooking" is often a fixed
camera pointed at a worktop, and nothing in the metadata says so.

This module looks at pixels instead, and it does so *before* the download, so a
candidate that is plainly the wrong viewpoint costs a fraction of a cent rather
than a download, an upload, an index and a caption pass.

Two tiers, because the price difference between them is three orders of
magnitude:

**Frames** (the default). YouTube publishes three storyboard stills per video —
``i.ytimg.com/vi/<id>/1.jpg``, ``2.jpg``, ``3.jpg`` — sampled from roughly a
quarter, a half and three quarters of the way in. They are free, they are
actual frames rather than designed cover art, and they are enough to see
whether a camera is worn: measured at about $0.002 and 3.5s per candidate.

**The video** (opt in, and capped). Gemini takes a YouTube URL directly and
watches the whole thing. It is the better judgement, and it cost $0.26 for a
single ten-minute video in testing — 140 times the frame check. Worth it for a
handful of finalists, ruinous for twenty candidates a query on a hosted demo.

Either way the verdict is advisory in one direction only: it can say *this is
not what you asked for* and stop a download, and it can raise confidence in a
match. It never overrides the post-index caption evidence, which sees all of
the footage rather than three moments of it.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.react import parse_json_object
from video_searching_agent.curation.viewpoint import Viewpoint

logger = logging.getLogger(__name__)

# The frames YouTube serves for every video, in the order they are tried. The
# numbered stills come first because they are sampled from inside the video;
# the named ones are cover art, which is chosen to attract a click and can show
# something the footage never does.
_FRAME_NAMES = ("1.jpg", "2.jpg", "3.jpg", "hq720.jpg", "mqdefault.jpg")
MAX_FRAMES = 4

# Below this many bytes the response is YouTube's grey placeholder, not a frame.
_MIN_FRAME_BYTES = 2000

# One frame a minute: enough to see a camera mount change, cheap enough to ask
# for on a long video — but only where the provider honours it. Measured on an
# 89-minute video through OpenRouter, fps, a window and a resolution hint were
# all dropped and the whole video was billed regardless: 488,504 video tokens,
# $0.367. So when sampling cannot be asked for, length is the only lever, and a
# watch is refused above the bound rather than quietly costing that much.
WATCH_FPS = 1 / 60
MAX_UNSAMPLED_WATCH_SECONDS = 15 * 60

SIGHT_PROMPT = """You are looking at frames sampled from one video, to decide \
whether it is usable as first-person (egocentric) training footage.

Egocentric means the camera is worn or held by the person doing the task: their \
own hands come into frame from the bottom or the sides, you never see their face \
or whole body, and the view moves with their head or chest.

Exocentric means a separate camera is looking at a person or a workspace: a \
face, a torso or a whole body is visible, or the frame is static and composed \
like a shot of someone else.

Answer with JSON only:
{"viewpoint": "egocentric" | "exocentric" | "unknown",
 "hands_visible": true | false,
 "confidence": 0.0-1.0,
 "why": "one clause naming what in the frames decided it"}

Say "unknown" when the frames genuinely do not show — a title card, a product \
shot, an empty workbench. Guessing is worse than abstaining here, because a \
wrong "exocentric" throws away good footage before anybody looks at it."""

WATCH_PROMPT = SIGHT_PROMPT.replace("frames sampled from one video", "an entire video").replace(
    'Say "unknown" when the frames genuinely do not show',
    'Say "unknown" when the video genuinely does not show',
)


@dataclass
class SightVerdict:
    """What the model saw, and what it cost to look."""

    viewpoint: Viewpoint = Viewpoint.UNKNOWN
    hands_visible: bool | None = None
    confidence: float = 0.0
    why: str = ""
    method: str = "none"
    frames_seen: int = 0
    cost_usd: float | None = None
    error: str | None = None
    evidence: list[str] = field(default_factory=list)

    @property
    def looked(self) -> bool:
        """Whether anything was actually seen. A failed look decides nothing."""

        return self.method != "none" and self.error is None

    def contradicts(self, wanted: Viewpoint | None) -> bool:
        """Whether what was seen rules this candidate out.

        Only a confident, opposite reading rules anything out. UNKNOWN never
        does, and nor does a low-confidence guess: the caption pass after
        indexing sees far more than three stills, and it gets the last word.
        """
        if not wanted or not self.looked:
            return False
        if self.viewpoint in (Viewpoint.UNKNOWN, wanted):
            return False
        return self.confidence >= 0.6

    def as_dict(self) -> dict[str, Any]:
        return {
            "viewpoint": self.viewpoint.value,
            "hands_visible": self.hands_visible,
            "confidence": round(self.confidence, 2),
            "why": self.why,
            "method": self.method,
            "frames_seen": self.frames_seen,
            "cost_usd": self.cost_usd,
            "error": self.error,
        }


def frame_urls(video_id: str) -> list[str]:
    """The still URLs for a YouTube video, best evidence first."""

    return [f"https://i.ytimg.com/vi/{video_id}/{name}" for name in _FRAME_NAMES]


async def fetch_frames(urls: list[str], limit: int = MAX_FRAMES) -> list[bytes]:
    """Fetch up to ``limit`` stills, skipping the ones that are placeholders."""
    import httpx

    frames: list[bytes] = []
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for url in urls:
            if len(frames) >= limit:
                break
            try:
                response = await client.get(url)
            except httpx.HTTPError as exc:
                logger.debug("frame %s unavailable: %s", url, exc)
                continue
            if response.status_code >= 400 or len(response.content) < _MIN_FRAME_BYTES:
                continue
            frames.append(response.content)
    return frames


async def look_at_frames(
    client: Any,
    frames: list[bytes],
    *,
    max_tokens: int = 900,
) -> SightVerdict:
    """Ask the model what viewpoint some frames show."""

    if not frames:
        return SightVerdict(error="no frames could be fetched")
    try:
        messages = client.new_visual_conversation(SIGHT_PROMPT, frames)
        response = await client.create_message_async(messages, max_tokens=max_tokens)
    except Exception as exc:  # noqa: BLE001 - a look that fails decides nothing
        logger.info("frame check failed: %s", exc)
        return SightVerdict(error=str(exc)[:200], frames_seen=len(frames))
    verdict = _read(response, client)
    verdict.method = "frames"
    verdict.frames_seen = len(frames)
    return verdict


async def watch_video(
    client: Any,
    video_url: str,
    *,
    duration_seconds: float | None = None,
    fps: float | None = WATCH_FPS,
    max_tokens: int = 900,
) -> SightVerdict:
    """Ask the model to watch the video, sampling a frame a minute if it can.

    A provider that honours ``fps`` bills for the frames asked for, which makes
    a whole-video look affordable on any length. One that drops it bills the
    whole video, so a long video is refused rather than silently costing a third
    of a dollar — the frame check's verdict stands instead.
    """
    sampled = bool(getattr(client, "SAMPLING_CONTROLS_HONOURED", True))
    if not sampled and duration_seconds and duration_seconds > MAX_UNSAMPLED_WATCH_SECONDS:
        minutes = duration_seconds / 60
        return SightVerdict(
            error=(
                f"{minutes:.0f} min is too long to watch unsampled "
                f"(this provider ignores fps; the bound is "
                f"{MAX_UNSAMPLED_WATCH_SECONDS // 60} min)"
            )
        )

    try:
        messages = client.new_video_conversation(
            WATCH_PROMPT, video_url, fps=fps if sampled else None
        )
        response = await client.create_message_async(messages, max_tokens=max_tokens)
    except Exception as exc:  # noqa: BLE001
        logger.info("video watch failed for %s: %s", video_url, exc)
        return SightVerdict(error=str(exc)[:200])
    verdict = _read(response, client)
    verdict.method = "watch" if sampled else "watch-unsampled"
    return verdict


async def check_viewpoint(
    client: Any,
    *,
    video_id: str | None = None,
    video_url: str | None = None,
    duration_seconds: float | None = None,
    mode: str = "frames",
) -> SightVerdict:
    """Look at a candidate, by whichever tier was asked for.

    Args:
        client: An LLM client from :func:`~video_searching_agent.api.llm.get_llm_client`.
        video_id: A YouTube id, which is what makes free frames available.
        video_url: The watch URL, needed for watching.
        duration_seconds: Used to refuse an unaffordable watch.
        mode: ``off``, ``frames``, ``escalate`` or ``watch``.

            ``escalate`` is the one worth defaulting to when money allows: the
            frames decide most candidates for $0.002, and only the ones they
            abstain on — a title card, an empty workbench — are worth a watch.
    """
    if mode == "off" or client is None:
        return SightVerdict()
    if mode == "watch":
        if not video_url:
            return SightVerdict(error="watching needs a video URL")
        return await watch_video(client, video_url, duration_seconds=duration_seconds)
    if not video_id:
        return SightVerdict(error="frames are only available for YouTube videos")

    frames = await fetch_frames(frame_urls(video_id))
    verdict = await look_at_frames(client, frames)
    if mode != "escalate" or not video_url:
        return verdict
    if verdict.looked and verdict.viewpoint is not Viewpoint.UNKNOWN:
        return verdict

    # The stills could not say. That is exactly what a watch is for.
    watched = await watch_video(client, video_url, duration_seconds=duration_seconds)
    if not watched.looked:
        # Keep the frame verdict, and say why the escalation did not happen.
        verdict.evidence.append(f"not escalated: {watched.error}")
        return verdict
    watched.frames_seen = verdict.frames_seen
    watched.cost_usd = (verdict.cost_usd or 0.0) + (watched.cost_usd or 0.0)
    watched.evidence.append("escalated after the frames abstained")
    return watched


async def check_many(
    client: Any,
    candidates: list[dict[str, Any]],
    *,
    mode: str = "frames",
    concurrency: int = 6,
) -> list[SightVerdict]:
    """Look at a batch of candidates at once.

    Each candidate is a dict with ``video_id`` and/or ``url``. Order is kept,
    so a verdict lines up with the candidate it came from.
    """
    if mode == "off" or client is None:
        return [SightVerdict() for _ in candidates]

    limit = asyncio.Semaphore(max(1, concurrency))

    async def one(candidate: dict[str, Any]) -> SightVerdict:
        async with limit:
            return await check_viewpoint(
                client,
                video_id=candidate.get("video_id"),
                video_url=candidate.get("url") or candidate.get("webpage_url"),
                duration_seconds=candidate.get("duration_seconds"),
                mode=mode,
            )

    return list(await asyncio.gather(*(one(candidate) for candidate in candidates)))


def _read(response: Any, client: Any) -> SightVerdict:
    """Turn a model response into a verdict, tolerating a fenced JSON block."""

    text = ""
    if hasattr(client, "get_text_response"):
        text = client.get_text_response(response) or ""
    try:
        parsed = parse_json_object(text)
    except (ValueError, json.JSONDecodeError):
        parsed = {}
    raw = str(parsed.get("viewpoint") or "").strip().lower()
    viewpoint = Viewpoint.UNKNOWN
    if raw in ("egocentric", "first_person", "first-person"):
        viewpoint = Viewpoint.EGOCENTRIC
    elif raw in ("exocentric", "third_person", "third-person"):
        viewpoint = Viewpoint.EXOCENTRIC

    confidence = parsed.get("confidence")
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        # An answer with no confidence is taken at middling strength: enough to
        # inform, not enough on its own to reject.
        confidence = 0.5
    hands = parsed.get("hands_visible")

    cost = None
    if hasattr(client, "get_cost_usd"):
        try:
            cost = client.get_cost_usd(response)
        except Exception:  # noqa: BLE001 - cost reporting is not load-bearing
            cost = None

    return SightVerdict(
        viewpoint=viewpoint,
        hands_visible=hands if isinstance(hands, bool) else None,
        confidence=max(0.0, min(1.0, confidence)),
        why=str(parsed.get("why") or "")[:300],
        cost_usd=cost,
        error=None if parsed else f"could not read a verdict from: {text[:120]}",
    )
