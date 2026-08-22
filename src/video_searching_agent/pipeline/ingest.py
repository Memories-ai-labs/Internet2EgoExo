"""Take a candidate URL all the way into a clean, annotated corpus.

One clip's journey, and which agent owns each leg:

    screen      cleaning agent    metadata only — licence, length, viewpoint
    download    yt-dlp            platform pages are not fetchable media
    upload      Datalake          multipart, or resumable over 100 MB
    index       Datalake          captions, transcription, embeddings
    clean       cleaning agent    hands, other people, editing, resolution
                                  then the action anchors inside the video
    annotate    annotation agent  task -> action -> event narration
    tag         both              the verdict, written back as filters

Rejected clips are reported with a reason and their local file is deleted — the
point of the gates is to spend the download but not keep the junk. Costs are
real at every step, so each stage reports what it did and the caller can stop
early.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.annotation_agent import AnnotationAgent, AnnotationRun
from video_searching_agent.agent.cleaning_agent import (
    CleaningAgent,
    CleaningVerdict,
    ScreeningVerdict,
)
from video_searching_agent.api.memories_datalake_client import (
    MemoriesDatalakeClient,
    MemoriesDatalakeError,
)
from video_searching_agent.config.settings import get_settings
from video_searching_agent.curation.frame_check import FrameCheck
from video_searching_agent.curation.viewpoint import Viewpoint
from video_searching_agent.pipeline.download import (
    ClipDownloader,
    DownloadedClip,
    DownloadError,
)

logger = logging.getLogger(__name__)

# Files above this go through the resumable upload path.
RESUMABLE_THRESHOLD_MB = 100

# Called as each stage begins, so a caller can stream progress. A clip can sit
# in `indexing` for minutes; without this the UI would show nothing until the
# whole pipeline finished.
StageCallback = Callable[["IngestResult"], Awaitable[None]]

# What each remaining stage needs, roughly, so the pipeline can tell whether
# starting one is honest. These are floors, not estimates: a download of a
# forty-minute video takes far longer than 45s, but starting one with less than
# that left is certainly pointless.
#
# The reason any of this exists: a serverless request has a hard wall (300s on
# this deployment), and being killed at it means the stream is cut with no
# summary event — the caller sees a clip stopped at "downloading" with no error,
# which is indistinguishable from a crash. Knowing the budget lets the pipeline
# stop *itself* and say what happened, handing back the video_id so curation can
# finish the job.
DOWNLOAD_FLOOR_SECONDS = 45.0
INDEX_FLOOR_SECONDS = 20.0
JUDGEMENT_FLOOR_SECONDS = 25.0


@dataclass
class IngestResult:
    """What happened to one candidate."""

    url: str
    stage: str = "queued"
    accepted: bool = False

    video_id: str | None = None
    operation: str | None = None
    duration_seconds: int | None = None
    size_mb: float | None = None
    downloaded_title: str | None = None

    screening: ScreeningVerdict | None = None
    cleaning: CleaningVerdict | None = None
    annotation: AnnotationRun | None = None

    rejection_reason: str | None = None
    # Set when the run stopped without a verdict either way — the clip is
    # indexed or indexing, and can be curated later. Distinct from a rejection,
    # which is a judgement, and from an error, which is a fault.
    pending_reason: str | None = None
    tags_written: list[str] = field(default_factory=list)
    error: str | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def frame_check(self) -> FrameCheck | None:
        """The frame verdict, which the cleaning agent owns."""
        return self.cleaning.frame_check if self.cleaning else None

    @property
    def annotation_level(self) -> str | None:
        return self.annotation.annotation_level.value if self.annotation else None

    def as_dict(self) -> dict[str, Any]:
        """Flat, JSON-safe view for SSE and tool results."""
        payload: dict[str, Any] = {
            "url": self.url,
            "stage": self.stage,
            "accepted": self.accepted,
            "video_id": self.video_id,
            "duration_seconds": self.duration_seconds,
            "size_mb": self.size_mb,
            "title": self.downloaded_title,
            "tags_written": self.tags_written,
            "rejection_reason": self.rejection_reason,
            "pending_reason": self.pending_reason,
            "error": self.error,
            "notes": self.notes,
            "annotation_level": self.annotation_level,
        }
        if self.screening:
            payload["screening"] = self.screening.as_dict()
        if self.cleaning:
            cleaning = self.cleaning.as_dict()
            payload["cleaning"] = cleaning
            # Kept flat as well: the UI reads frame_check directly.
            payload["frame_check"] = cleaning["frame_check"]
            payload["quality"] = cleaning["quality"]
            payload["segments"] = cleaning["segments"]
        if self.annotation:
            payload["annotation"] = self.annotation.as_dict()
        return payload


class IngestPipeline:
    """Screen → download → upload → index → clean → annotate, one clip at a time."""

    def __init__(
        self,
        client: MemoriesDatalakeClient | None = None,
        downloader: ClipDownloader | None = None,
        cleaning_agent: CleaningAgent | None = None,
        annotation_agent: AnnotationAgent | None = None,
        keep_files: bool = False,
    ) -> None:
        """Initialize the pipeline.

        Args:
            client: Datalake client. Created on first use when omitted.
            downloader: Download strategy. Created on first use when omitted.
            cleaning_agent: Filtering and clipping. Created when omitted.
            annotation_agent: Narration. Created when omitted.
            keep_files: Keep downloaded files after upload. Off by default —
                a run can pull hundreds of clips.
        """
        self._client = client
        self._downloader = downloader
        self._cleaning = cleaning_agent
        self._annotation = annotation_agent
        self.keep_files = keep_files

    @property
    def client(self) -> MemoriesDatalakeClient:
        if self._client is None:
            self._client = MemoriesDatalakeClient()
        return self._client

    @property
    def downloader(self) -> ClipDownloader:
        if self._downloader is None:
            self._downloader = ClipDownloader()
        return self._downloader

    @property
    def cleaning(self) -> CleaningAgent:
        if self._cleaning is None:
            self._cleaning = CleaningAgent(client=self.client)
        return self._cleaning

    @property
    def annotation(self) -> AnnotationAgent:
        if self._annotation is None:
            self._annotation = AnnotationAgent(client=self.client)
        return self._annotation

    async def ingest(
        self,
        url: str,
        require_hands: bool = True,
        wanted_viewpoint: Viewpoint | None = None,
        min_duration_seconds: int | None = None,
        wait_seconds: float | None = None,
        annotate: bool = True,
        on_stage: StageCallback | None = None,
        viewpoint_verified: bool = False,
        deadline: float | None = None,
    ) -> IngestResult:
        """Run one candidate through the whole pipeline.

        Args:
            url: Candidate page URL (YouTube, TikTok, Instagram, X, …).
            require_hands: Reject clips whose footage shows no hands.
            wanted_viewpoint: Reject clips the captions place elsewhere.
            min_duration_seconds: Skip before downloading if too short.
            wait_seconds: Indexing wait budget. Defaults to settings.
            annotate: Run the annotation agent on what survives cleaning.
            on_stage: Awaited as each stage begins, for progress streaming.
            viewpoint_verified: The search already looked at this candidate's
                frames and it survived, so the look is skipped rather than
                paid for twice. A URL pasted by hand never has this.
            deadline: A `time.monotonic()` value this run must finish by,
                usually the host's request limit minus a margin. The pipeline
                stops at the last stage it can honestly start and returns
                `pending` with the video_id, instead of being killed mid-stage
                with nothing reported.

        Returns:
            An IngestResult; `accepted` is True only for a clip that is indexed
            and cleared the cleaning agent's gates.
        """
        result = IngestResult(url=url)

        async def stage(name: str) -> None:
            result.stage = name
            if on_stage is not None:
                await on_stage(result)

        def remaining() -> float:
            """Seconds left in the budget, or infinity when there is none."""

            if deadline is None:
                return float("inf")
            return deadline - time.monotonic()

        async def out_of_time(what: str, floor: float) -> bool:
            """Stop before a stage that cannot finish, and say so."""

            left = remaining()
            if left >= floor:
                return False
            await stage("pending")
            result.pending_reason = (
                f"stopped before {what}: {max(0.0, left):.0f}s left of the request "
                f"budget and it needs at least {floor:.0f}s. "
                + (
                    f"Curate {result.video_id} later — the footage is in the lake."
                    if result.video_id
                    else "Nothing was spent; send this URL again with more headroom."
                )
            )
            result.notes.append(result.pending_reason)
            return True

        # --- 1. probe and screen before spending disk or money -------------
        await stage("probing")
        try:
            info = await self.downloader.probe_async(url)
        except DownloadError as exc:
            await stage("failed")
            result.error = str(exc)
            return result

        duration = info.get("duration")
        result.duration_seconds = int(duration) if isinstance(duration, int | float) else None
        result.downloaded_title = info.get("title")

        screening = self.cleaning.screen(
            {**info, "url": url},
            wanted_viewpoint=wanted_viewpoint,
            min_duration_seconds=min_duration_seconds,
        )
        result.screening = screening
        if screening.accepted and not viewpoint_verified:
            # Everything above read words about the video. This looks at it.
            await stage("looking")
            screening = await self.cleaning.look(
                screening,
                {**info, "url": url},
                wanted_viewpoint=wanted_viewpoint,
            )
        elif screening.accepted:
            # The search already looked and this survived it. Looking again
            # would cost the same money to reach the same verdict.
            screening.notes.append("viewpoint checked at search time")
        if not screening.accepted:
            await stage("skipped")
            result.rejection_reason = "; ".join(screening.reasons)
            return result

        # --- 2. download ---------------------------------------------------
        if await out_of_time("the download", DOWNLOAD_FLOOR_SECONDS):
            return result
        await stage("downloading")
        try:
            clip = await self.downloader.download_async(url)
        except DownloadError as exc:
            await stage("failed")
            result.error = str(exc)
            return result

        result.size_mb = clip.size_mb
        result.duration_seconds = clip.duration_seconds or result.duration_seconds
        result.downloaded_title = clip.title or result.downloaded_title
        result.notes.extend(clip.warnings)

        # --- 3. upload and index ------------------------------------------
        # The file is on disk and paid for by now, so this check is about not
        # starting an upload that will be cut halfway — which leaves a partial
        # video in the lake with no id handed back.
        if await out_of_time("the upload", INDEX_FLOOR_SECONDS):
            if not self.keep_files:
                self.downloader.discard(clip)
            return result
        await stage("uploading")
        try:
            uploaded = await self._upload(clip)
            result.video_id = uploaded.get("video_id")
            result.operation = uploaded.get("operation")
            if not result.video_id:
                raise MemoriesDatalakeError("upload returned no video_id")
        except MemoriesDatalakeError as exc:
            await stage("failed")
            result.error = str(exc)
            return result
        finally:
            if not self.keep_files:
                self.downloader.discard(clip)

        await stage("indexing")
        try:
            if result.operation:
                # Wait for as long as there is, not for a fixed budget that may
                # outlast the request. Leaving room for the judgement stages
                # means a clip that indexes in time still gets cleaned.
                budget = wait_seconds
                left = remaining()
                if left != float("inf"):
                    allowed = max(0.0, left - JUDGEMENT_FLOOR_SECONDS)
                    budget = allowed if budget is None else min(budget, allowed)
                operation = await self.client.wait_for_operation(
                    result.operation, max_wait_seconds=budget
                )
                if not operation.get("done"):
                    # Neither accepted nor rejected: the footage is fine, the
                    # index just has not caught up. Saying so plainly matters —
                    # returning with the stage still "indexing" and no reason
                    # made a clip look like it silently vanished, which is
                    # exactly how a whole-pipeline run reported "nothing
                    # survived collection" with an empty list of reasons.
                    await stage("pending")
                    budget = (
                        f"inside {wait_seconds:.0f}s"
                        if isinstance(wait_seconds, int | float)
                        else "inside the wait budget"
                    )
                    result.pending_reason = (
                        f"indexing did not finish {budget}; the Datalake is still "
                        "working on it. Curate this video_id later — nothing is lost."
                    )
                    result.notes.append(result.pending_reason)
                    return result
                if operation.get("error"):
                    await stage("failed")
                    result.error = f"indexing failed: {operation['error']}"
                    return result
        except MemoriesDatalakeError as exc:
            await stage("failed")
            result.error = str(exc)
            return result

        # --- 4. clean: filter on the frames, then find the anchors ---------
        if await out_of_time("the cleaning pass", JUDGEMENT_FLOOR_SECONDS):
            return result
        await stage("cleaning")
        verdict = await self.cleaning.clean(
            str(result.video_id),
            title=result.downloaded_title,
            require_hands=require_hands,
            wanted_viewpoint=wanted_viewpoint,
            media=self._media_facts(clip),
        )
        result.cleaning = verdict
        result.tags_written = list(verdict.tags_written)
        result.rejection_reason = verdict.rejection_reason
        result.accepted = verdict.accepted
        result.notes.extend(verdict.errors)

        if not verdict.accepted:
            await stage("rejected")
            return result

        # --- 5. annotate what survived ------------------------------------
        if annotate and verdict.segments:
            await stage("annotating")
            run = await self.annotation.annotate_video(
                str(result.video_id),
                verdict.segments,
                require_hands=require_hands,
            )
            result.annotation = run
            result.tags_written.extend(
                tag for tag in run.tags_written if tag not in result.tags_written
            )
            result.notes.extend(run.errors)

        await stage("accepted")
        return result

    @staticmethod
    def _media_facts(clip: DownloadedClip) -> dict[str, Any]:
        """What the download knows that the index cannot tell us."""
        return {
            "source_url": clip.url,
            "uploader": clip.uploader,
            "license": clip.license_note,
            "width": clip.width,
            "height": clip.height,
            "fps": clip.fps,
            "duration_seconds": clip.duration_seconds,
            "container": clip.path.suffix.lstrip(".") or None,
            "title": clip.title,
        }

    async def _upload(self, clip: DownloadedClip) -> dict[str, Any]:
        """Upload a file, picking multipart or resumable by size."""
        metadata = {
            "title": clip.title,
            "custom": {
                "source_url": clip.url,
                "uploader": clip.uploader,
                "extractor": clip.extractor,
                "license_note": clip.license_note,
                "width": clip.width,
                "height": clip.height,
            },
        }

        if clip.size_mb <= RESUMABLE_THRESHOLD_MB:
            return await self.client.upload_video_file(clip.path, metadata=metadata)

        session = await self.client.start_resumable_upload(metadata=metadata)
        video_id = session.get("video_id")
        upload_url = session.get("upload_url")
        if not video_id or not upload_url:
            raise MemoriesDatalakeError("resumable upload returned no session")

        await asyncio.to_thread(_put_resumable, str(upload_url), clip.path)
        finalized = await self.client.finalize_upload(str(video_id))
        finalized.setdefault("video_id", video_id)
        return finalized


def _put_resumable(upload_url: str, path: Any) -> None:
    """PUT a file to a GCS resumable session.

    Two steps per the Datalake docs: POST with ``x-goog-resumable: start`` to
    open the session, then PUT the bytes to the URI in the Location header.
    """
    import httpx

    settings = get_settings()
    timeout = max(float(settings.api_timeout_seconds), 600.0)

    with httpx.Client(timeout=timeout) as client:
        opened = client.post(
            upload_url,
            headers={"x-goog-resumable": "start", "Content-Type": "video/mp4"},
        )
        if opened.status_code >= 400:
            raise MemoriesDatalakeError(
                f"opening the resumable session returned {opened.status_code}"
            )

        session_uri = opened.headers.get("Location")
        if not session_uri:
            raise MemoriesDatalakeError("resumable session returned no Location header")

        with open(path, "rb") as handle:
            put = client.put(session_uri, content=handle.read())
        if put.status_code >= 400:
            raise MemoriesDatalakeError(f"resumable PUT returned {put.status_code}")
