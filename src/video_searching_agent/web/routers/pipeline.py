"""Collection and curation streaming router.

Three endpoints for the second half of the product — everything that happens
after the search has found candidates, and the one that keeps looking until it
has:

* ``POST /api/v1/collect/stream`` — download candidates, index them into the
  Video Datalake, clean them and annotate what survives. Each clip's stage is
  streamed as it changes, because indexing can take minutes and a progress bar
  that only moves at the end is not a progress bar.
* ``POST /api/v1/curate/stream`` — run the curation agent over a worklist that
  is already indexed, and stream each clip's verdict as it lands.
* ``POST /api/v1/search-loop/stream`` — search, screen the candidates on their
  frames, tell the agent what the frames said, and let it search again. Rounds
  stream as they finish, because the reasons are what a caller needs to see:
  a run that found nothing because every phrasing hit the wrong genre reads
  very differently from one that found nothing at all.

Both stream Server-Sent Events. Both are bounded: a request cannot queue more
clips than `MAX_URLS_PER_REQUEST`, because every clip costs real money to
index.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from video_searching_agent.agent.curation_agent import CurationAgent
from video_searching_agent.config.settings import get_settings
from video_searching_agent.pipeline.ingest import IngestPipeline
from video_searching_agent.web import demo
from video_searching_agent.web.credentials import RequestCredentials
from video_searching_agent.web.schemas.events import ErrorEvent
from video_searching_agent.web.schemas.requests import (
    AnnotateCleanRequest,
    CollectRequest,
    CurateRequest,
    ExportRequest,
    RefineRequest,
    SearchLoopRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

# A sentinel that closes the progress queue.
_DONE = object()


def _pipeline_for(credentials: RequestCredentials) -> IngestPipeline:
    """A pipeline wired to the caller's keys where they supplied them.

    Built per request: the whole point of bring-your-own-key is that the
    caller's key is used for their run and nobody else's.
    """
    datalake = credentials.datalake_client()
    llm = credentials.llm_client()
    if datalake is None and llm is None:
        return IngestPipeline()

    from video_searching_agent.agent.annotation_agent import AnnotationAgent
    from video_searching_agent.agent.cleaning_agent import CleaningAgent

    # A None client means "resolve from settings on first use", which is what
    # a caller who brought only a model key should get for the Datalake.
    return IngestPipeline(
        client=datalake,
        cleaning_agent=CleaningAgent(client=datalake),
        annotation_agent=AnnotationAgent(client=datalake, gemini=llm),
    )


def _curation_agent_for(credentials: RequestCredentials) -> CurationAgent:
    """A curation agent wired to the caller's keys where they supplied them."""
    datalake = credentials.datalake_client()
    llm = credentials.llm_client()
    if datalake is None and llm is None:
        return CurationAgent()

    from video_searching_agent.agent.annotation_agent import AnnotationAgent
    from video_searching_agent.agent.cleaning_agent import CleaningAgent

    return CurationAgent(
        client=datalake,
        cleaning_agent=CleaningAgent(client=datalake),
        annotation_agent=AnnotationAgent(client=datalake, gemini=llm),
    )


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
    if get_settings().demo_mode:
        async for frame in demo.frames(demo.collect_events(body)):
            yield frame
        return

    pipeline = _pipeline_for(RequestCredentials.from_headers(request.headers))
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    yield {
        "event": "started",
        "data": json.dumps({"urls": len(body.urls), "annotate": body.annotate}),
    }

    already_looked = set(body.viewpoint_verified_urls)

    # One deadline for the whole request, shared across the clips. A clip that
    # cannot be finished inside it returns `pending` with its video_id rather
    # than being cut off mid-stage — and once the budget is gone, the clips
    # behind it say so immediately instead of spending on work that will be
    # killed.
    budget = get_settings().request_budget_seconds
    deadline = (time.monotonic() + budget) if budget else None

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
                viewpoint_verified=url in already_looked,
                deadline=deadline,
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
                "video_ids": [clip["video_id"] for clip in accepted if clip.get("video_id")],
            }
        ),
    }


async def _curate_events(
    request: Request,
    body: CurateRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one curation pass."""
    if get_settings().demo_mode:
        async for frame in demo.frames(demo.curate_events(body)):
            yield frame
        return

    agent = _curation_agent_for(RequestCredentials.from_headers(request.headers))

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
                report = payload.as_dict()
                report["storage"] = await _where_it_landed(agent, report)
                yield {"event": "complete", "data": json.dumps(report)}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("curation failed")
        error = ErrorEvent.create(code="internal_error", message=str(exc))
        yield {"event": error.event, "data": json.dumps(error.data)}


async def _where_it_landed(agent: Any, report: dict[str, Any]) -> dict[str, Any]:
    """Say where the graded videos actually are, and what does not exist yet.

    A grade with no location is half an answer: the panel that reports "1 of 5
    accepted" was read as "there is a clip somewhere", and there is not — this
    path indexes whole source videos and marks spans on them. Cutting those
    spans into files is `pipeline/refine.py`, which is deliberately not an API
    route (it needs a writable directory and a decoder), so nothing reached
    the clean collection here and nothing was written to disk.

    Saying so is the point. A UI that shows only the grade lets somebody
    conclude the deliverable exists.
    """
    clips = report.get("clips") or []
    video_ids = [c.get("video_id") for c in clips if c.get("video_id")]
    storage: dict[str, Any] = {
        "kind": "source_videos",
        "collection_id": "",
        "collection_name": "",
        "video_ids": video_ids,
        "clips_cut": 0,
        "on_disk": False,
        "note": (
            "These are whole source videos with spans marked on them, indexed in the "
            "Video Datalake. No clip files were cut: that is step three (refine), which "
            "runs from eval/run.sh rather than over the API. Nothing was written to this "
            "machine's disk."
        ),
    }
    if not video_ids:
        return storage

    lake = getattr(agent, "client", None)
    if lake is None:
        return storage
    try:
        record = await lake.get_video(video_ids[0])
        video = record.get("video") if isinstance(record.get("video"), dict) else record
        storage["collection_id"] = str(video.get("collection_id") or "")
        listing = await lake.list_collections()
        for collection in listing.get("collections") or []:
            if collection.get("id") == storage["collection_id"]:
                storage["collection_name"] = str(collection.get("name") or "")
                break
    except Exception as exc:  # noqa: BLE001 - a missing name is not a failed run
        logger.info("could not resolve where the curated videos live: %s", exc)
    return storage


@router.post("/search-loop/stream")
async def stream_search_loop(
    request: Request,
    body: SearchLoopRequest,
) -> EventSourceResponse:
    """Search, screen on frames, learn from the rejections, search again.

    Events: `started`, `round` (one per round, with what the frames said),
    `complete`, `error`. The rounds are the point: a caller watching only the
    final answer cannot tell a loop that found five things from one that gave
    up, and the reasons are what say which.
    """
    settings = get_settings()
    return EventSourceResponse(
        _search_loop_events(request, body),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )


async def _search_loop_events(
    request: Request,
    body: SearchLoopRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one search loop, a round at a time."""
    from video_searching_agent.agent.search_loop import run_search_loop

    wanted = body.viewpoint.value if body.viewpoint else "egocentric"
    yield {
        "event": "started",
        "data": json.dumps(
            {
                "query": body.query,
                "viewpoint": wanted,
                "target": body.target,
                "verify": body.verify,
            }
        ),
    }

    rounds: list[dict[str, Any]] = []

    async def on_round(number: int, observation: str, partial: Any) -> None:
        rounds.append(
            {
                "round": number,
                "observation": observation,
                "found": len(partial.kept),
                "screened": len(partial.candidates),
                "cost_usd": round(partial.cost_usd, 4),
                "verify_usd": round(partial.verify_usd, 4),
            }
        )

    try:
        # The loop is one long await, so the rounds are drained after it rather
        # than during: `on_round` fills a list and the generator hands over
        # whatever has accumulated between yields. A caller that disconnects
        # stops being sent to; the loop's own bounds stop the spending.
        task = asyncio.create_task(
            run_search_loop(
                body.query,
                wanted=wanted,
                target=body.target,
                min_duration_seconds=body.min_duration_seconds,
                max_rounds=body.rounds,
                budget_usd=body.budget_usd,
                verify=body.verify,
                verify_budget_usd=body.verify_budget_usd,
                on_round=on_round,
            )
        )
        sent = 0
        while not task.done():
            await asyncio.sleep(0.5)
            while sent < len(rounds):
                if await request.is_disconnected():
                    task.cancel()
                    return
                yield {"event": "round", "data": json.dumps(rounds[sent])}
                sent += 1
        while sent < len(rounds):
            yield {"event": "round", "data": json.dumps(rounds[sent])}
            sent += 1
        yield {"event": "complete", "data": json.dumps((await task).as_dict())}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("the search loop failed")
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


async def _export_events(body: ExportRequest) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one export. Two events, because the work is one call.

    It is a stream rather than a plain POST so the connection carries SSE pings:
    downloading twenty clips takes minutes, and a proxy that times out a silent
    request turns a working export into an error the user cannot explain.
    """
    from video_searching_agent.pipeline.dataset import export_dataset

    out_dir = Path(get_settings().dataset_dir).expanduser().resolve()
    yield {
        "event": "started",
        "data": json.dumps(
            {"out_dir": str(out_dir), "clips": len(body.video_ids), "media": body.media}
        ),
    }
    try:
        report = await export_dataset(
            out_dir,
            collection_id=body.collection_id.strip(),
            video_ids=body.video_ids,
            media=body.media,
            refresh_media=body.refresh_media,
            viewpoint=body.viewpoint,
        )
    except Exception as exc:  # noqa: BLE001 - the UI has to be told, not left spinning
        logger.exception("export failed")
        yield {"event": "error", "data": ErrorEvent(error=str(exc)).model_dump_json()}
        return

    payload = report.as_dict()
    # An absolute path, because the point of this endpoint is to answer "where",
    # and "./dataset" is only an answer if you know the working directory.
    payload["out_dir"] = str(out_dir)
    yield {"event": "complete", "data": json.dumps(payload)}


@router.post("/export/stream")
async def stream_export(body: ExportRequest) -> EventSourceResponse:
    """Write a run's clips, trees and manifest to this machine's disk.

    Events: `started`, `complete`, `error`. `complete` carries the absolute
    directory and what was actually written, including what was held back and
    why — a count of files is not the same claim as a count of clips.
    """
    settings = get_settings()
    return EventSourceResponse(
        _export_events(body),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )


async def _refine_events(
    request: Request, body: RefineRequest
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one refine pass: cut the anchors, re-house them, record them.

    This is the step that turns "a source video with spans marked on it" into
    clip files, and it is the step whose absence made the library look empty
    after a run that had clearly worked. It needs a writable directory to hold
    a cut before uploading it; when the host has none, `refine_anchors` says so
    in `skipped_reason` rather than pretending nothing was asked for.
    """
    from video_searching_agent.pipeline.refine import record_refined, refine_anchors

    credentials = RequestCredentials.from_headers(request.headers)
    lake = credentials.datalake_client()
    if lake is None:
        from video_searching_agent.api.memories_datalake_client import (
            MemoriesDatalakeClient,
        )

        lake = MemoriesDatalakeClient(api_key=get_settings().memories_api_key)

    anchors = [a.model_dump() for a in body.anchors]
    yield {"event": "started", "data": json.dumps({"anchors": len(anchors)})}
    try:
        result = await refine_anchors(
            lake,
            anchors,
            collection_name=body.collection_name,
            max_clips=body.max_clips,
        )
        recorded = record_refined(result, query=body.query)
    except Exception as exc:  # noqa: BLE001 - the UI has to be told
        logger.exception("refine failed")
        yield {"event": "error", "data": ErrorEvent(error=str(exc)).model_dump_json()}
        return

    payload = result.as_dict()
    payload["recorded"] = recorded
    # The ids of the clips that now exist, so the caller can ask the library for
    # exactly them instead of for everything the store has ever held.
    payload["clip_ids"] = [
        clip.uploaded_video_id for clip in result.uploaded if clip.uploaded_video_id
    ]
    yield {"event": "complete", "data": json.dumps(payload)}


@router.post("/refine/stream")
async def stream_refine(request: Request, body: RefineRequest) -> EventSourceResponse:
    """Cut a curated run's action anchors into clips of their own.

    Events: `started`, `complete`, `error`. `complete` carries `clip_ids`, the
    clips that now exist, and `skipped_reason` when the host could not do it.
    """
    settings = get_settings()
    return EventSourceResponse(
        _refine_events(request, body),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )


async def _annotate_clean_events(
    request: Request, body: AnnotateCleanRequest
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream one annotation pass over the cut clips."""
    from video_searching_agent.pipeline.annotate_clean import annotate_clean_collection

    credentials = RequestCredentials.from_headers(request.headers)
    kwargs: dict[str, Any] = {
        "limit": body.limit,
        "only_missing": body.only_missing,
        "write_back": body.write_back,
        "wanted_viewpoint": body.wanted_viewpoint,
    }
    if body.collection_id.strip():
        kwargs["collection_id"] = body.collection_id.strip()
    lake = credentials.datalake_client()
    if lake is not None:
        kwargs["lake"] = lake
    llm = credentials.llm_client()
    if llm is not None:
        kwargs["llm"] = llm

    yield {"event": "started", "data": json.dumps({"limit": body.limit})}
    try:
        report = await annotate_clean_collection(**kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.exception("annotating the clean clips failed")
        yield {"event": "error", "data": ErrorEvent(error=str(exc)).model_dump_json()}
        return

    payload = report.as_dict()
    payload["clip_ids"] = [
        r.video_id for r in report.annotated if getattr(r, "video_id", "")
    ]
    yield {"event": "complete", "data": json.dumps(payload)}


@router.post("/annotate-clean/stream")
async def stream_annotate_clean(
    request: Request, body: AnnotateCleanRequest
) -> EventSourceResponse:
    """Give the cut clips their own task, action and event trees.

    Events: `started`, `complete`, `error`. A clip whose frames do not confirm
    the wanted viewpoint is refused rather than annotated, and counted as such.
    """
    settings = get_settings()
    return EventSourceResponse(
        _annotate_clean_events(request, body),
        media_type="text/event-stream",
        ping=settings.sse_ping_interval,
    )
