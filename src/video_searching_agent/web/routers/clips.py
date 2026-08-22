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

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from video_searching_agent.config.settings import get_settings
from video_searching_agent.store.annotations import open_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/clips", tags=["clips"])

MAX_LIMIT = 200


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
