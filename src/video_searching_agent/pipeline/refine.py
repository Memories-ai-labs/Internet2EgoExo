"""Step three: cut the accepted spans, clean them, and give them their own collection.

The pipeline's first two steps put whole web videos into the Datalake and found
the spans worth having inside them. This step makes those spans into a corpus:
each one is cut for real, measured on its pixels, and the survivors are uploaded
to a *second* collection that contains nothing but clean clips.

Why a second collection rather than a tag on the first. The first collection is
what the web gave us — whole videos, most of them mostly useless, with the good
spans marked. The second is the deliverable, and it is a different kind of thing:
every video in it is a clip that passed the media gates and the pixel pass, its
provenance points back at the source, and annotating it means annotating footage
that is already known good. That is the difference between a list of spans over
someone else's videos and a dataset.

**Provenance goes under `custom`.** The upload endpoint validates metadata: `title`
and `custom` are accepted top-level keys and anything else is rejected — with the
message "json part is not valid JSON", which is not what it means. Every clip
here carries `custom.source_video_id`, `custom.source_start` and
`custom.source_end`, so a clip in the clean collection can always be traced to
the frame it came from. Without that the clean collection would fail G0-PROV by
construction.

**What it costs, per anchor.** A cut is $0.005. An upload is billed per minute of
video, so a 30-second clip indexes for about a fortieth of what its source video
did. Nothing here is free and nothing here is implicit: the caller passes the
anchors it wants and gets back a record of what each one cost, including the ones
that were cut and then thrown away, because a clip rejected after cutting has
still been paid for.

**Off unless asked for**, like every other step that spends money and makes
network calls. And it needs a writable directory and a decoder, neither of which
a serverless function has, so it degrades to "not attempted" with a reason rather
than failing a request.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.pipeline.clip_quality import ClipVerdict, judge_clip, measure_clip

logger = logging.getLogger(__name__)

# A cut is a real ffmpeg job on their side and it is priced as one.
CUT_COST_USD = 0.005

# Anchors shorter than this are not worth a cut: too short to train on, and the
# per-clip overhead of indexing dominates.
MIN_CLIP_SECONDS = 3.0

# And longer than this is not a clip any more, it is the video again.
MAX_CLIP_SECONDS = 300.0

# Leave this much of the budget for the upload after a cut. Cutting a clip and
# then running out of time before uploading it wastes the cut.
UPLOAD_FLOOR_SECONDS = 30.0


@dataclass
class RefinedClip:
    """One anchor, cut and judged, and where it ended up."""

    source_video_id: str
    start: float
    end: float
    verdict: ClipVerdict | None = None
    uploaded_video_id: str | None = None
    operation_id: str | None = None
    bytes_downloaded: int = 0
    cut_cost_usd: float = 0.0
    stage: str = "pending"
    error: str | None = None

    @property
    def seconds(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def uploaded(self) -> bool:
        return bool(self.uploaded_video_id)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_video_id": self.source_video_id,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "seconds": round(self.seconds, 2),
            "stage": self.stage,
            "uploaded_video_id": self.uploaded_video_id,
            "cut_cost_usd": round(self.cut_cost_usd, 5),
            "bytes": self.bytes_downloaded,
            "error": self.error,
            "verdict": self.verdict.as_dict() if self.verdict else None,
        }


@dataclass
class RefineResult:
    """What a refinement pass produced."""

    collection_id: str | None = None
    collection_name: str = ""
    clips: list[RefinedClip] = field(default_factory=list)
    cut_cost_usd: float = 0.0
    skipped_reason: str | None = None

    @property
    def uploaded(self) -> list[RefinedClip]:
        return [clip for clip in self.clips if clip.uploaded]

    @property
    def rejected(self) -> list[RefinedClip]:
        return [clip for clip in self.clips if clip.verdict is not None and not clip.verdict.usable]

    @property
    def uploaded_seconds(self) -> float:
        return sum(clip.seconds for clip in self.uploaded)

    def as_dict(self) -> dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "collection_name": self.collection_name,
            "attempted": len(self.clips),
            "uploaded": len(self.uploaded),
            "rejected_by_the_pixel_pass": len(self.rejected),
            "uploaded_seconds": round(self.uploaded_seconds, 1),
            # Every cut is charged for, including the ones whose clip was then
            # thrown away. Reporting only the survivors' cuts would make a
            # strict pass look cheaper than a lax one.
            "cut_cost_usd": round(self.cut_cost_usd, 4),
            "skipped_reason": self.skipped_reason,
            "clips": [clip.as_dict() for clip in self.clips],
        }


def _writable_dir() -> str | None:
    """Somewhere to put a cut clip, or None on a read-only host.

    Probes by writing, because a serverless filesystem answers "yes" to every
    question about a path right up until you write to it.
    """
    import tempfile

    from video_searching_agent.config.settings import get_settings

    candidates = [get_settings().download_dir, "downloads", tempfile.gettempdir()]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            os.makedirs(candidate, exist_ok=True)
            probe = os.path.join(candidate, ".refine-probe")
            with open(probe, "wb") as handle:
                handle.write(b"x")
            os.unlink(probe)
            return candidate
        except OSError:
            continue
    return None


# The endpoint caps `limit` at 100 and returns 400 for anything larger. Asking
# for 200 cost five duplicate collections: the error was swallowed, the listing
# came back empty, and "no collection of that name exists" is indistinguishable
# from "the lookup failed" unless you keep them apart — which is what the
# `looked` flag below is for.
COLLECTIONS_PAGE = 100


async def ensure_clean_collection(lake: Any, name: str) -> str | None:
    """The collection cleaned clips go into, reusing it when it exists.

    A lookup that *failed* must never fall through to creating a collection.
    Doing so turned one clean collection into six in ten minutes, each holding a
    slice of the output, because every call believed it was the first.
    """
    looked = False
    try:
        listing = await lake.list_collections(limit=COLLECTIONS_PAGE)
        looked = True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "could not list collections, so not creating %r either: %s", name, exc
        )
        return None

    rows = listing.get("collections") or listing.get("data") or []
    if isinstance(rows, list):
        # Oldest first, so a name that already has duplicates resolves to the
        # same one every time rather than drifting to the newest.
        matches = [
            row
            for row in rows
            if isinstance(row, dict) and row.get("name") == name
        ]
        matches.sort(key=lambda row: str(row.get("created_at") or ""))
        if len(matches) > 1:
            logger.warning(
                "%d collections are named %r; using the oldest. Consolidate them.",
                len(matches),
                name,
            )
        for row in matches:
            found = row.get("collection_id") or row.get("id")
            if found:
                return str(found)

    if not looked:  # unreachable today, kept so the invariant is explicit
        return None
    try:
        made = await lake.create_collection(name)
    except Exception as exc:  # noqa: BLE001
        logger.info("could not create collection %r: %s", name, exc)
        return None
    inner = made.get("collection") if isinstance(made.get("collection"), dict) else made
    created = inner.get("collection_id") or inner.get("id")
    return str(created) if created else None


async def refine_anchor(
    lake: Any,
    source_video_id: str,
    start: float,
    end: float,
    *,
    clean_collection_id: str,
    work_dir: str,
    source_title: str = "",
    source_url: str = "",
    http: Any | None = None,
) -> RefinedClip:
    """Cut one anchor, judge its pixels, and upload it if it survives."""
    clip = RefinedClip(source_video_id=source_video_id, start=start, end=end)
    if clip.seconds < MIN_CLIP_SECONDS:
        clip.stage = "skipped"
        clip.error = f"{clip.seconds:.1f}s is shorter than {MIN_CLIP_SECONDS:.0f}s"
        return clip
    if clip.seconds > MAX_CLIP_SECONDS:
        clip.stage = "skipped"
        clip.error = f"{clip.seconds:.0f}s is longer than {MAX_CLIP_SECONDS:.0f}s"
        return clip

    import httpx

    clip.stage = "cutting"
    try:
        cut = await lake.get_clip(source_video_id, start, end)
    except Exception as exc:  # noqa: BLE001
        clip.error = f"cut failed: {str(exc)[:160]}"
        return clip
    clip.cut_cost_usd = CUT_COST_USD
    url = cut.get("url") or cut.get("clip_url") or (cut.get("data") or {}).get("url")
    if not url:
        clip.error = f"the cut returned no url (keys: {sorted(cut)[:6]})"
        return clip

    clip.stage = "downloading"
    path = os.path.join(work_dir, f"clip_{source_video_id[-10:]}_{int(start)}_{int(end)}.mp4")
    own_client = http is None
    client = http or httpx.AsyncClient(timeout=300, follow_redirects=True)
    try:
        response = await client.get(str(url))
        if response.status_code >= 400:
            clip.error = f"clip download returned {response.status_code}"
            return clip
        with open(path, "wb") as handle:
            handle.write(response.content)
        clip.bytes_downloaded = len(response.content)
    except Exception as exc:  # noqa: BLE001
        clip.error = f"clip download failed: {str(exc)[:160]}"
        return clip
    finally:
        if own_client:
            await client.aclose()

    try:
        clip.stage = "measuring"
        clip.verdict = judge_clip(measure_clip(path))
        if not clip.verdict.usable:
            clip.stage = "rejected"
            return clip

        clip.stage = "uploading"
        # `custom` is the only place arbitrary keys are accepted, and without
        # these three a clip in the clean collection cannot be traced back.
        metadata = {
            "title": (source_title or f"{source_video_id} {start:.0f}-{end:.0f}s")[:300],
            "custom": {
                "source_video_id": source_video_id,
                "source_start": round(start, 2),
                "source_end": round(end, 2),
                "source_url": source_url,
                "refined_by": "clip_quality",
            },
        }
        try:
            uploaded = await lake.upload_video_file(
                path, collection_id=clean_collection_id, metadata=metadata
            )
        except Exception as exc:  # noqa: BLE001
            clip.error = f"upload failed: {str(exc)[:160]}"
            return clip
        clip.uploaded_video_id = uploaded.get("video_id") or (uploaded.get("video") or {}).get(
            "video_id"
        )
        operation = uploaded.get("operation")
        clip.operation_id = (
            operation.get("operation_id") if isinstance(operation, dict) else operation
        )
        clip.stage = "uploaded" if clip.uploaded_video_id else "upload-returned-no-id"
        return clip
    finally:
        # The bytes were the means, not the product. The clip lives in the
        # Datalake now, and leaving copies on a container that gets reclaimed is
        # how a disk allowance disappears mid-run.
        try:
            os.unlink(path)
        except OSError:
            pass


def record_refined(result: RefineResult, *, query: str = "", store: Any = None) -> int:
    """Write the uploaded clips into the annotation store.

    A clip row lands as soon as the clip exists, with no tree on it yet: cut and
    cleaned but not annotated is a real state and the browse UI should be able to
    show it rather than pretending the clip does not exist until somebody labels
    it. The tree is attached later, keyed on the same `video_id`.
    """
    from video_searching_agent.store.annotations import Clip, open_store

    target = store or open_store()
    written = 0
    for clip in result.uploaded:
        measurement = clip.verdict.measurement if clip.verdict else None
        target.put(
            Clip(
                video_id=str(clip.uploaded_video_id),
                collection_id=result.collection_id or "",
                source_video_id=clip.source_video_id,
                source_start=clip.start,
                source_end=clip.end,
                duration_seconds=clip.seconds,
                query=query,
                motion_mean=getattr(measurement, "motion_mean", None),
                sharpness_mean=getattr(measurement, "sharpness_mean", None),
                payload={"refine": clip.as_dict()},
            )
        )
        written += 1
    logger.info("recorded %d refined clip(s) in the annotation store", written)
    return written


async def refine_anchors(
    lake: Any,
    anchors: list[dict[str, Any]],
    *,
    collection_name: str = "egoexo-clean-clips",
    deadline: float | None = None,
    max_clips: int | None = None,
    record: bool = True,
) -> RefineResult:
    """Cut, clean and re-house a list of anchors.

    Args:
        lake: A Datalake client.
        anchors: Dicts with ``video_id``, ``start`` and ``end``; ``title`` and
            ``url`` are carried into the clip's provenance when present.
        collection_name: The clean collection to fill, created on first use.
        deadline: A ``time.monotonic()`` value to stop before. A cut that cannot
            be followed by an upload is not made.
        max_clips: Stop after this many anchors.

    Returns:
        A :class:`RefineResult`. Never raises for one bad anchor: each clip
        carries its own error, because a run that stops at the first failure
        wastes every cut it already paid for.
    """
    result = RefineResult(collection_name=collection_name)

    work_dir = _writable_dir()
    if not work_dir:
        result.skipped_reason = (
            "no writable directory for cut clips; a serverless host cannot do this step"
        )
        return result

    collection_id = await ensure_clean_collection(lake, collection_name)
    if not collection_id:
        result.skipped_reason = f"could not open the {collection_name!r} collection"
        return result
    result.collection_id = collection_id

    import httpx

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as http:
        for index, anchor in enumerate(anchors):
            if max_clips is not None and index >= max_clips:
                break
            if deadline is not None and (deadline - time.monotonic()) < UPLOAD_FLOOR_SECONDS:
                result.skipped_reason = (
                    f"out of time after {index} of {len(anchors)} anchors; the "
                    "remaining cuts were not made rather than paid for and dropped"
                )
                break
            video_id = str(anchor.get("video_id") or "")
            try:
                start = float(anchor.get("start"))
                end = float(anchor.get("end"))
            except (TypeError, ValueError):
                clip = RefinedClip(source_video_id=video_id, start=0.0, end=0.0)
                clip.error = "anchor has no numeric start and end"
                result.clips.append(clip)
                continue
            if not video_id:
                clip = RefinedClip(source_video_id="", start=start, end=end)
                clip.error = "anchor has no video_id"
                result.clips.append(clip)
                continue

            clip = await refine_anchor(
                lake,
                video_id,
                start,
                end,
                clean_collection_id=collection_id,
                work_dir=work_dir,
                source_title=str(anchor.get("title") or ""),
                source_url=str(anchor.get("url") or ""),
                http=http,
            )
            result.clips.append(clip)
            result.cut_cost_usd += clip.cut_cost_usd

    if record and result.uploaded:
        try:
            record_refined(result)
        except Exception as exc:  # noqa: BLE001 - the clips are uploaded either way
            logger.warning("could not record refined clips: %s", exc)

    logger.info(
        "refine: %d of %d anchors uploaded to %s, %.1fs of footage, $%.3f in cuts",
        len(result.uploaded),
        len(result.clips),
        collection_name,
        result.uploaded_seconds,
        result.cut_cost_usd,
    )
    return result


async def wait_for_clean_clips(
    lake: Any, result: RefineResult, *, timeout: float = 600.0
) -> dict[str, str]:
    """Wait for the uploaded clips to finish indexing.

    Returns a map of video id to final status. Annotation cannot start on a clip
    that is still indexing, and the whole point of the clean collection is that
    it is the thing annotated next.
    """
    statuses: dict[str, str] = {}
    pending = [clip for clip in result.uploaded if clip.operation_id]
    if not pending:
        return statuses

    async def one(clip: RefinedClip) -> None:
        try:
            # `max_wait_seconds`, not `timeout`. Calling it `timeout` raised a
            # TypeError that this function then caught and reported as "still
            # indexing", so a wait that never happened looked like a slow index.
            await lake.wait_for_operation(clip.operation_id, max_wait_seconds=timeout)
            statuses[str(clip.uploaded_video_id)] = "ready"
        except Exception as exc:  # noqa: BLE001 - a slow index is not a failure
            statuses[str(clip.uploaded_video_id)] = f"still indexing: {str(exc)[:80]}"

    await asyncio.gather(*(one(clip) for clip in pending))
    return statuses
