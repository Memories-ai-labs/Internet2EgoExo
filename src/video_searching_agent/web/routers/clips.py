"""Browsing the clean clips: the footage in the Datalake, the tree in the store.

Every clip in the clean collection has a Datalake `video_id`, and that id is the
join. The Datalake holds the pixels and can hand back a playable URL; the
annotation store holds the tree and can be searched. Neither can do the other's
job, so these endpoints read both and return one object.

The search is the reason the store exists. "fold" finds a clip whose *action* is
folding even when its title never says so, because the segments are rows rather
than a blob hanging off a video record.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from video_searching_agent.config.settings import get_settings
from video_searching_agent.store.annotations import open_store, store_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/clips", tags=["clips"])

MAX_LIMIT = 200

# A still is 320px wide and taken a third of the way in. The first frame of a
# cut is often a wipe or a hand still entering, and the middle is where the
# manipulation actually is; a third in is the cheapest approximation of that
# which does not need to know anything about the clip.
THUMBNAIL_WIDTH = 320
THUMBNAIL_AT = 0.33


def thumbnail_dir() -> Path:
    """Where rendered stills are kept, beside the store that lists them.

    Cached because generating one costs an ffmpeg invocation against a signed
    URL, and a library page asks for two dozen at once. Nothing here is
    authoritative: deleting the directory costs a re-render and nothing else.
    """
    configured = os.environ.get("THUMBNAIL_CACHE_PATH", "")
    if configured:
        return Path(configured)
    store = store_path()
    base = Path(store).parent if store != ":memory:" else Path("data")
    return base / "thumbnails"


@router.get("")
async def list_clips(
    q: str = Query("", description="Match a title, an action label or a narration"),
    viewpoint: str = Query("", description="egocentric | exocentric | unknown"),
    grade: str = Query("", description="A | B | C | D"),
    hier_level: str = Query("", description="Only clips with a segment at this level"),
    hands_only: bool = Query(False, description="Only clips with a hands-visible segment"),
    accepted_only: bool = Query(False, description="Only clips the gates accepted"),
    source_video_id: str = Query("", description="Every clip cut from one source video"),
    limit: int = Query(50, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Search the clean clips.

    Returns the page, and the total that matched — separately, because a page
    size is not a result count and conflating them is how a UI ends up claiming
    a corpus is fifty clips.
    """
    if get_settings().demo_mode:
        from video_searching_agent.web import demo

        return demo.library_page(
            q=q.strip(),
            viewpoint=viewpoint.strip(),
            hands_only=hands_only,
            accepted_only=accepted_only,
            limit=limit,
            offset=offset,
        )

    store = open_store()
    clips, total = store.search(
        text=q.strip(),
        viewpoint=viewpoint.strip(),
        grade=grade.strip().upper(),
        hier_level=hier_level.strip(),
        hands_only=hands_only,
        accepted_only=accepted_only,
        source_video_id=source_video_id.strip(),
        limit=limit,
        offset=offset,
    )
    return {
        "clips": [clip.as_dict(with_segments=False) for clip in clips],
        "total": total,
        "limit": limit,
        "offset": offset,
        # Where the store is, and whether it persists. A caller seeing an empty
        # corpus deserves to know whether that is because nothing was collected
        # or because this host forgets between requests.
        "store": {"path": store.path, "persists": store.path != ":memory:"},
    }


@router.get("/facets")
async def clip_facets() -> dict[str, Any]:
    """What is in the store: totals, and the label vocabulary it actually has.

    The vocabulary is read from the data rather than declared, so the filters a
    UI offers are always filters that match something.
    """
    if get_settings().demo_mode:
        from video_searching_agent.web import demo

        return demo.library_facets()

    store = open_store()
    return {
        "totals": store.totals(),
        "action_labels": store.labels(hier_level="action"),
        "task_labels": store.labels(hier_level="task", limit=30),
        # What was actually handled. The facet a buyer reaches for first: they
        # ask for footage of a drill, not for footage labelled "drive the screw".
        "objects": store.object_vocabulary(),
    }


@router.get("/{video_id}")
async def get_clip(video_id: str) -> dict[str, Any]:
    """One clip, its whole tree, and a playable URL for the footage.

    The URL comes from the Datalake at read time rather than being stored: a
    signed URL expires, and a stored one is a link that works until it quietly
    does not.
    """
    if get_settings().demo_mode:
        from video_searching_agent.web import demo

        found = demo.library_clip(video_id)
        if found is None:
            raise HTTPException(status_code=404, detail=f"no clip {video_id}")
        return found

    store = open_store()
    clip = store.get(video_id)
    if clip is None:
        raise HTTPException(status_code=404, detail=f"no clip {video_id} in the store")

    payload = clip.as_dict(with_segments=True)
    payload["playback"] = await _playback(video_id)
    return payload


@router.get("/{video_id}/thumbnail")
async def get_thumbnail(video_id: str) -> FileResponse:
    """One still from the clip, rendered once and cached.

    The Datalake can hand back a frame, and charges for it — before the lookup,
    and not refunded on a miss. A library page showing two dozen clips would
    bill two dozen times, every time somebody scrolled. So the still is cut
    locally with ffmpeg from the same signed URL the player uses, and kept.

    ffmpeg reads the URL directly and stops after one frame, so this transfers
    a few hundred kilobytes rather than the whole clip.
    """
    cache = thumbnail_dir()
    cached = cache / f"{video_id}.jpg"
    if cached.exists() and cached.stat().st_size > 0:
        return FileResponse(cached, media_type="image/jpeg")

    clip = open_store().get(video_id)
    if clip is None:
        raise HTTPException(status_code=404, detail=f"no clip {video_id} in the store")

    playback = await _playback(video_id)
    url = playback.get("url")
    if not url:
        raise HTTPException(
            status_code=404,
            detail=playback.get("error") or "the Datalake returned no URL for this clip",
        )

    at = max(0.0, (clip.duration_seconds or 0.0) * THUMBNAIL_AT)
    rendered = await _render_still(str(url), cached, at)
    if not rendered:
        raise HTTPException(status_code=503, detail="could not render a still for this clip")
    return FileResponse(cached, media_type="image/jpeg")


async def _render_still(url: str, dest: Path, at: float) -> bool:
    """Cut one frame out of a URL. False when this host cannot."""
    from video_searching_agent.agent.eyes import Eyes

    ffmpeg = Eyes().ffmpeg
    if not ffmpeg:
        logger.info("no ffmpeg on this host, so no thumbnails")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Written under a temporary name: a half-written jpg that the next request
    # finds and serves is worse than no thumbnail at all.
    tmp = dest.with_suffix(".part.jpg")
    command = [
        ffmpeg,
        "-nostdin",
        "-y",
        # Before -i, so ffmpeg seeks rather than decoding up to the timestamp.
        "-ss",
        f"{at:.3f}",
        "-i",
        url,
        "-frames:v",
        "1",
        "-q:v",
        "4",
        "-vf",
        f"scale={THUMBNAIL_WIDTH}:-2",
        str(tmp),
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _out, err = await asyncio.wait_for(process.communicate(), timeout=60)
    except (TimeoutError, OSError) as exc:
        logger.info("thumbnail render failed for %s: %s", dest.stem, exc)
        tmp.unlink(missing_ok=True)
        return False

    if process.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        logger.info(
            "ffmpeg could not still %s: %s", dest.stem, (err or b"").decode()[-200:].strip()
        )
        tmp.unlink(missing_ok=True)
        return False

    tmp.replace(dest)
    return True


async def _playback(video_id: str) -> dict[str, Any]:
    """A URL for the clip's own footage, or why there is not one."""
    try:
        from video_searching_agent.api.memories_datalake_client import (
            MemoriesDatalakeClient,
        )
        from video_searching_agent.config.settings import get_settings

        lake = MemoriesDatalakeClient(api_key=get_settings().memories_api_key)
        record = await lake.get_video(video_id)
    except Exception as exc:  # noqa: BLE001 - a missing URL is not a missing clip
        logger.info("no playback for %s: %s", video_id, exc)
        return {"url": None, "error": str(exc)[:200]}

    video = record.get("video") if isinstance(record.get("video"), dict) else record
    url = video.get("url") or video.get("playback_url") or video.get("source_url")
    return {
        "url": url,
        "status": video.get("status"),
        "duration_seconds": video.get("duration_seconds"),
        # The Datalake's own auto-tags. Worth surfacing: they are what named the
        # Unity-editor clip `unity_editor`, `inspector_panel`, `hierarchy_panel`
        # when no caption phrase list caught it.
        "tags": (video.get("metadata") or {}).get("tags") or [],
    }
