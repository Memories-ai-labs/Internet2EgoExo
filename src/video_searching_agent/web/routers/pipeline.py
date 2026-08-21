"""Collection and curation streaming router.

Two endpoints for the second half of the product — everything that happens
after the search has found candidates:

* ``POST /api/v1/collect/stream`` — download candidates, index them into the
  Video Datalake, clean them and annotate what survives. Each clip's stage is
  streamed as it changes, because indexing can take minutes and a progress bar
  that only moves at the end is not a progress bar.
* ``POST /api/v1/curate/stream`` — run the curation agent over a worklist that
  is already indexed, and stream each clip's verdict as it lands.

Both stream Server-Sent Events. Both are bounded: a request cannot queue more
clips than `MAX_URLS_PER_REQUEST`, because every clip costs real money to
index.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from video_searching_agent.agent.curation_agent import CurationAgent
from video_searching_agent.config.settings import get_settings
from video_searching_agent.pipeline.ingest import IngestPipeline
from video_searching_agent.web.schemas.events import ErrorEvent
from video_searching_agent.web.schemas.requests import CollectRequest, CurateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

# A sentinel that closes the progress queue.
_DONE = object()


async def _pump(
    work: Callable[[Callable[[Any], Awaitable[None]]], Awaitable[Any]],
) -> AsyncGenerator[tuple[str, Any], None]:
    """Run one long job and yield its progress as it arrives.

    The job is handed an async callback to report progress with; this drains
    that callback's queue while the job runs, then yields the return value
    last. Without this the whole pipeline would finish before the client saw
    anything.

    Yields:
        `("progress", payload)` tuples, then one `("result", value)`.
    """
    queue: asyncio.Queue[Any] = asyncio.Queue()

    async def report(payload: Any) -> None:
        await queue.put(payload)

    async def runner() -> Any:
        try:
            return await work(report)
        finally:
            await queue.put(_DONE)

    task = asyncio.create_task(runner())
    while True:
        item = await queue.get()
        if item is _DONE:
            break
        yield "progress", item
    yield "result", await task


async def _collect_events(
    request: Request,
    body: CollectRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one collection run."""
    pipeline = IngestPipeline()
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    yield {
        "event": "started",
        "data": json.dumps({"urls": len(body.urls), "annotate": body.annotate}),
    }

    for index, url in enumerate(body.urls, start=1):
        if await request.is_disconnected():
            logger.info("client disconnected, stopping collection")
            return

        async def one(report: Callable[[Any], Awaitable[None]], url: str = url) -> Any:
            async def on_stage(result: Any) -> None:
                await report(result.as_dict())

            return await pipeline.ingest(
                url,
                require_hands=body.require_hands,
                wanted_viewpoint=body.viewpoint,
                min_duration_seconds=body.min_duration_seconds,
                annotate=body.annotate,
                on_stage=on_stage,
            )

        try:
            async for kind, payload in _pump(one):
                if kind == "progress":
                    yield {
                        "event": "clip_stage",
                        "data": json.dumps(
                            {"index": index, "total": len(body.urls), "clip": payload}
                        ),
                    }
                else:
                    result = payload.as_dict()
                    (accepted if payload.accepted else rejected).append(result)
                    yield {
                        "event": "clip_done",
                        "data": json.dumps(
                            {"index": index, "total": len(body.urls), "clip": result}
                        ),
                    }
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # one bad clip must not end the run
            logger.exception("collection failed for %s", url)
            rejected.append({"url": url, "stage": "failed", "error": str(exc)})
            yield {
                "event": "clip_done",
                "data": json.dumps(
                    {
                        "index": index,
                        "total": len(body.urls),
                        "clip": {"url": url, "stage": "failed", "error": str(exc)},
                    }
                ),
            }

    yield {
        "event": "complete",
        "data": json.dumps(
            {
                "accepted": accepted,
                "rejected": rejected,
                "accepted_count": len(accepted),
                "rejected_count": len(rejected),
                "video_ids": [
                    clip["video_id"] for clip in accepted if clip.get("video_id")
                ],
            }
        ),
    }


async def _curate_events(
    request: Request,
    body: CurateRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one curation pass."""
    agent = CurationAgent()

    yield {
        "event": "started",
        "data": json.dumps(
            {"video_ids": body.video_ids or [], "tag": body.tag, "query": body.query}
        ),
    }

    async def work(report: Callable[[Any], Awaitable[None]]) -> Any:
        async def on_clip(clip: Any) -> None:
            await report(clip.as_dict())

        return await agent.curate(
            body.video_ids,
            tag=body.tag,
            query=body.query or "",
            require_hands=body.require_hands,
            wanted_viewpoint=body.viewpoint,
            annotate=body.annotate,
            on_clip=on_clip,
        )

    try:
        async for kind, payload in _pump(work):
            if await request.is_disconnected():
                logger.info("client disconnected, stopping curation")
                return
            if kind == "progress":
                yield {"event": "clip_done", "data": json.dumps({"clip": payload})}
            else:
                yield {"event": "complete", "data": json.dumps(payload.as_dict())}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("curation failed")
        error = ErrorEvent.create(code="internal_error", message=str(exc))
        yield {"event": error.event, "data": json.dumps(error.data)}


@router.post("/collect/stream")
async def stream_collection(
    request: Request,
    body: CollectRequest,
) -> EventSourceResponse:
    """Download, index, clean and annotate a list of candidate URLs.

    Events: `started`, `clip_stage` (one per stage), `clip_done`, `complete`, `error`.
    """
    settings = get_settings()
    return EventSourceResponse(
        _collect_events(request, body),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )


@router.post("/curate/stream")
async def stream_curation(
    request: Request,
    body: CurateRequest,
) -> EventSourceResponse:
    """Clean, annotate and grade an already-indexed worklist.

    Events: `started`, `clip_done`, `complete`, `error`.
    """
    settings = get_settings()
    return EventSourceResponse(
        _curate_events(request, body),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )
