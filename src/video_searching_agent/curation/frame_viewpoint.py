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
watches it, honouring ``fps``: a ten-minute video at one frame a minute is
about 2,800 input tokens, where default sampling on an 89-minute video was
488,504 and $0.367. So the price is not the reason it is not the default.

The reason is that it does not measurably decide more than the frames do.
Escalated on four candidates the frames could not settle, a watch left two
unchanged, read one better than the frames had — correctly calling a static
composed shot of a finished build "not somebody doing this" — and read one
*worse*, flipping a fixed camera pointed at a suitcase to egocentric when the
frames had it right. One better, one worse, two the same, at ten to fourteen
seconds each, is not an upgrade. It is offered because a deployment may have
candidates the frames genuinely cannot call, and it is off by default.

A watch also has a failure mode with no error in it. When the model cannot
fetch the video — private, removed, region-locked, or simply gone —
``gemini-3.1-pro-preview`` raises 403, but the 2.5 models accept the request,
silently drop the video part, and answer from the URL and the prompt: one reply
described a robot dog unlocking a door, billed as eight tokens of text. Those
candidates are not exotic; a search hands them over every day. So
:func:`watch_video` checks the bill for media tokens and throws away any verdict
reached without the video.

Two questions, not one, because the second is free. Whether the camera is worn
and whether the frames show the activity that was asked for are independent,
and a video can pass the first and fail the second: "How To Use a Laundromat"
is worn-camera footage of a tour of the machines. Across 16 candidates from two
requests, three passed the viewpoint question and failed the task question —
two product adverts and that tour — and each one would otherwise have cost a
download, an upload, an index pass and a caption pass.

Every verdict is advisory in one direction only: it can say *this is not what
you asked for* and stop a download, and it can raise confidence in a match. It
never overrides the post-index caption evidence, which sees all of the footage
rather than three moments of it.
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

# The same look, asked one more question. A video can be perfectly egocentric and
# still be the wrong activity, and that is just as useless — "How To Use a
# Laundromat" reads as worn-camera footage because it is, and it is a captioned
# tour of the machines rather than anybody doing the laundry. Measured over 16
# candidates across two requests, three passed the viewpoint question and failed
# this one: two product ads and that tour. Three downloads, uploads, index
# passes and caption passes not spent, for no extra money — it is the same call.
TASK_CLAUSE = """
The footage is wanted for this task:

TASK: {task}

That is a second, separate judgement, and it has three answers, not two.

"doing" — the frames show somebody performing this task.

"other_kind" — this is a different *kind* of video and no amount of it will \
show the task being performed: a review of the tools, an advert for the parts, \
a tour of the equipment, a presenter talking to camera, an animation, a \
product shot.

"unclear" — this may well be a video of the task; these particular frames just \
do not show it. Somebody between jobs, a wide shot of the room, a moment of \
something else. Three frames out of an hour miss most of what happens.

The line between "other_kind" and "unclear" is the whole point. Only \
"other_kind" throws the video away, and it must be a claim about the video, \
never about these three frames.

And one more, separately: is this footage of the physical world at all?

"screen" means the footage *is* a screen's contents — a software tutorial, an \
editor, a game, a slide deck, a phone recording of a phone. Not merely that a \
screen appears: somebody typing at a laptop, or working while a monitor sits on \
the desk, is physical-world footage and the screen in it is furniture.

"physical" means a camera pointed at the world. "unclear" when the frames \
cannot say. Only "screen" throws the video away."""

TASK_FIELDS = """
 "world": "physical" | "screen" | "unclear",
 "task": "doing" | "other_kind" | "unclear",
 "task_confidence": 0.0-1.0,
 "task_why": "one clause naming what in the frames decided the activity","""

WATCH_PROMPT = SIGHT_PROMPT.replace("frames sampled from one video", "an entire video").replace(
    'Say "unknown" when the frames genuinely do not show',
    'Say "unknown" when the video genuinely does not show',
)


def sight_prompt(base: str, task: str | None) -> str:
    """The prompt, with the task question folded in when there is a task.

    Kept as a transform of the single-question prompt rather than a second
    prompt, so the viewpoint wording cannot drift apart between the two.
    """
    if not task:
        return base
    body = base.replace(
        ' "hands_visible": true | false,',
        f' "hands_visible": true | false,{TASK_FIELDS}',
    )
    return body + TASK_CLAUSE.format(task=task)


@dataclass
class SightVerdict:
    """What the model saw, and what it cost to look."""

    viewpoint: Viewpoint = Viewpoint.UNKNOWN
    hands_visible: bool | None = None
    confidence: float = 0.0
    why: str = ""
    task_reading: str = ""
    # Whether this is footage of the world at all. A fixed phrase list could not
    # do this job: the Unity-editor clip's caption said "the user is back in the
    # Unity editor, right-clicking in the hierarchy" and matched none of
    # `_NON_FOOTAGE_CUES`, because the cues name the medium ("screen recording")
    # and captions name the application. Asking generalises to software nobody
    # thought to enumerate.
    world: str = ""
    task_confidence: float = 0.0
    task_why: str = ""
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

    @property
    def shows_task(self) -> bool | None:
        """True when the frames caught the task, False for a different kind of
        video, None when these frames simply could not say."""

        return {"doing": True, "other_kind": False}.get(self.task_reading)

    def is_screen_capture(self) -> bool:
        """Whether this is a screen's contents rather than the world.

        No confidence threshold, unlike the other two: "physical" and "screen"
        are a plain either-or that three frames settle, where a viewpoint can be
        genuinely ambiguous and an activity can be off-frame. `unclear` and an
        unanswered field both keep the candidate.
        """
        return self.looked and self.world == "screen"

    def misses_task(self) -> bool:
        """Whether what was seen makes this the wrong video for the task.

        Not the same rule as :meth:`contradicts`, because the two questions do
        not have the same evidence behind them. Viewpoint is a property of the
        whole video — a worn camera stays worn — so three stills settle it.
        Activity is local in time, and three stills out of an hour miss most of
        what happens. Measured: a video honestly titled "folding some laundry |
        first person POV" has stills of a cat, a bookshelf and a hand at a
        laundry basket. The model read those frames correctly; a rule that
        dropped it on "the task is not in these frames" was the thing that was
        wrong, and it threw away good footage three times out of three.

        So this only fires on ``other_kind`` — a claim about the video rather
        than about the frames, of the sort three stills genuinely can support:
        an advert, a review, a presenter, a cartoon. Not being able to see the
        task never loses a candidate.
        """
        if not self.looked or self.task_reading != "other_kind":
            return False
        return self.task_confidence >= 0.6

    def as_dict(self) -> dict[str, Any]:
        return {
            "viewpoint": self.viewpoint.value,
            "hands_visible": self.hands_visible,
            "confidence": round(self.confidence, 2),
            "why": self.why,
            "shows_task": self.shows_task,
            "task_reading": self.task_reading,
            "world": self.world,
            "task_confidence": round(self.task_confidence, 2),
            "task_why": self.task_why,
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
    task: str | None = None,
    max_tokens: int = 900,
) -> SightVerdict:
    """Ask the model what viewpoint some frames show, and whether they show the task."""

    if not frames:
        return SightVerdict(error="no frames could be fetched")
    try:
        messages = client.new_visual_conversation(sight_prompt(SIGHT_PROMPT, task), frames)
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
    task: str | None = None,
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
    # A provider that drops the sampling controls bills the whole video, so
    # prefer one that keeps them if this deployment has a key for it. The frames
    # tier is unaffected — this only matters when watching.
    if not getattr(client, "SAMPLING_CONTROLS_HONOURED", True):
        from video_searching_agent.api.llm import get_video_client

        try:
            better = get_video_client()
        except Exception:  # noqa: BLE001 - falling back is not a failure
            better = None
        if better is not None:
            logger.info("watching through Gemini, which honours the frame-rate hint")
            client = better

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
            sight_prompt(WATCH_PROMPT, task), video_url, fps=fps if sampled else None
        )
        response = await client.create_message_async(messages, max_tokens=max_tokens)
    except Exception as exc:  # noqa: BLE001
        logger.info("video watch failed for %s: %s", video_url, exc)
        return SightVerdict(error=str(exc)[:200])

    # A model sent a video it could not fetch does not say so — it answers
    # anyway, from the URL and the prompt. Asked about a video that does not
    # exist, one reply came back "A robot dog retrieves a key, inserts it into a
    # door lock", with a normal STOP finish and a prompt bill of eight tokens,
    # every one of them text. Private, removed and region-locked candidates
    # reach this line every day, and 3.1-pro raises 403 where 2.5 invents an
    # answer, so the guard cannot be a model-version assumption. An answer about
    # a video that was never delivered is worse than no answer.
    if getattr(client, "saw_media", None) and client.saw_media(response) is False:
        logger.info("watch discarded for %s: the video never reached the model", video_url)
        return SightVerdict(
            error="the video was not ingested (billed as text only) — no verdict from it"
        )

    verdict = _read(response, client)
    verdict.method = "watch" if sampled else "watch-unsampled"
    return verdict


async def check_viewpoint(
    client: Any,
    *,
    video_id: str | None = None,
    video_url: str | None = None,
    duration_seconds: float | None = None,
    task: str | None = None,
    mode: str = "frames",
) -> SightVerdict:
    """Look at a candidate, by whichever tier was asked for.

    Args:
        client: An LLM client from :func:`~video_searching_agent.api.llm.get_llm_client`.
        video_id: A YouTube id, which is what makes free frames available.
        video_url: The watch URL, needed for watching.
        duration_seconds: Used to refuse an unaffordable watch.
        task: What the footage is wanted for. Given one, the same look also
            says whether the frames show that activity — a judgement the
            viewpoint question cannot make and which costs nothing extra.
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
        return await watch_video(client, video_url, task=task, duration_seconds=duration_seconds)
    if not video_id:
        return SightVerdict(error="frames are only available for YouTube videos")

    frames = await fetch_frames(frame_urls(video_id))
    verdict = await look_at_frames(client, frames, task=task)
    if mode != "escalate" or not video_url:
        return verdict
    # Escalate on either abstention: the stills that cannot name the viewpoint
    # and the stills that cannot name the activity are both unfinished answers,
    # and a watch is what finishes them.
    undecided = verdict.viewpoint is Viewpoint.UNKNOWN or (
        bool(task) and verdict.task_reading in ("", "unclear")
    )
    if verdict.looked and not undecided:
        return verdict

    # The stills could not say. That is exactly what a watch is for.
    watched = await watch_video(client, video_url, task=task, duration_seconds=duration_seconds)
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
    task: str | None = None,
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
                task=task,
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

    # An unrecognised answer — including one from a model that ignored the new
    # field entirely — reads as no answer, which loses nothing.
    task_reading = str(parsed.get("task") or "").strip().lower()
    if task_reading not in ("doing", "other_kind", "unclear"):
        task_reading = ""
    world = str(parsed.get("world") or "").strip().lower()
    if world not in ("physical", "screen", "unclear"):
        world = ""
    task_confidence = parsed.get("task_confidence")
    try:
        task_confidence = float(task_confidence)
    except (TypeError, ValueError):
        task_confidence = 0.5 if task_reading else 0.0

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
        task_reading=task_reading,
        world=world,
        task_confidence=max(0.0, min(1.0, task_confidence)),
        task_why=str(parsed.get("task_why") or "")[:300],
        cost_usd=cost,
        error=None if parsed else f"could not read a verdict from: {text[:120]}",
    )
