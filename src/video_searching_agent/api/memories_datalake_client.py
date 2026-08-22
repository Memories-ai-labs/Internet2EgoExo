"""Memories.ai Video Datalake API client.

Wraps the Datalake REST API (``https://api.memories.ai/serve/datalake/v1``):
index a video, poll the async ingest operation, then read derived content
(title, summary, captions, transcription) or search indexed moments.

Auth is the raw API key in the ``Authorization`` header (``sk-mai-...``) — no
``Bearer`` prefix. See https://docs.memories.ai/authentication
"""

from __future__ import annotations

import asyncio
import logging
from json import dumps as json_dumps
from pathlib import Path
from typing import Any

import httpx

from video_searching_agent.config.settings import get_settings

logger = logging.getLogger(__name__)

# Search targets accepted by POST /search.
SEARCH_TARGETS = ("caption", "transcription", "summary", "title", "frame_embedding", "event")


def _as_dict(response: httpx.Response, label: str) -> dict[str, Any]:
    """Decode a JSON object body, or fail loudly."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise MemoriesDatalakeError(f"{label} returned non-JSON body") from exc
    if not isinstance(payload, dict):
        raise MemoriesDatalakeError(f"{label} returned {type(payload).__name__}")
    return payload


class MemoriesDatalakeError(RuntimeError):
    """Raised when the Datalake API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MemoriesDatalakeClient:
    """Async client for the Memories.ai Video Datalake API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        collection_id: str | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: Datalake API key (``sk-mai-...``). Defaults to settings.
            collection_id: Index into this collection instead of the configured
                one — used when a request brings its own key.
            base_url: API base URL. Defaults to settings.
            timeout: Per-request timeout in seconds. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.memories_api_key
        self.base_url = (base_url or settings.memories_base_url).rstrip("/")
        self.timeout = float(timeout or settings.api_timeout_seconds)
        # Resolved lazily by ensure_collection() and cached per client instance.
        # A caller-supplied collection wins: a request that brings its own key
        # must index into its own collection, not the server's.
        self._collection_id: str | None = (
            collection_id or settings.memories_collection_id or None
        )

    # ------------------------------------------------------------------ plumbing

    def _headers(self) -> dict[str, str]:
        """Build request headers. The API key goes in verbatim."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Send a request and return the decoded JSON body.

        Raises:
            MemoriesDatalakeError: On transport failures, non-2xx responses,
                or a body that is not a JSON object.
        """
        if not self.api_key:
            raise MemoriesDatalakeError("MEMORIES_API_KEY is not configured")

        url = f"{self.base_url}/{path.lstrip('/')}"
        request_timeout = float(timeout or self.timeout)

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                    params={k: v for k, v in (params or {}).items() if v is not None},
                )
        except httpx.HTTPError as exc:
            raise MemoriesDatalakeError(f"{method} {path} failed: {exc}") from exc

        if response.status_code >= 400:
            raise MemoriesDatalakeError(
                f"{method} {path} returned {response.status_code}: {response.text[:300]}",
                status_code=response.status_code,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MemoriesDatalakeError(f"{method} {path} returned non-JSON body") from exc

        if not isinstance(payload, dict):
            raise MemoriesDatalakeError(f"{method} {path} returned {type(payload).__name__}")

        return payload

    # ---------------------------------------------------------------- collections

    async def create_collection(self, name: str) -> dict[str, Any]:
        """Create a collection (free)."""
        return await self._request("POST", "/collections", json={"name": name})

    async def list_collections(self, limit: int = 100) -> dict[str, Any]:
        """List collections (free)."""
        return await self._request("GET", "/collections", params={"limit": limit})

    async def ensure_collection(self, name: str | None = None) -> str:
        """Return the collection id to index into, creating it on first use.

        A configured ``MEMORIES_COLLECTION_ID`` short-circuits this. Otherwise
        the collection named ``name`` is reused when it already exists.

        Args:
            name: Collection name. Defaults to the configured name.

        Returns:
            The collection id.
        """
        if self._collection_id:
            return self._collection_id

        settings = get_settings()
        collection_name = name or settings.memories_collection_name

        listing = await self.list_collections()
        for collection in listing.get("collections") or []:
            if isinstance(collection, dict) and collection.get("name") == collection_name:
                collection_id = collection.get("id")
                if isinstance(collection_id, str) and collection_id:
                    self._collection_id = collection_id
                    return collection_id

        created = await self.create_collection(collection_name)
        collection_id = created.get("id")
        if not isinstance(collection_id, str) or not collection_id:
            raise MemoriesDatalakeError("Collection creation returned no id")

        self._collection_id = collection_id
        logger.info("datalake_collection_created name=%s id=%s", collection_name, collection_id)
        return collection_id

    # -------------------------------------------------------------------- videos

    async def index_video_url(
        self,
        source_url: str,
        collection_id: str | None = None,
        fps: float | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Index a video from a URL.

        Billed per minute of video. Returns ``{video_id, operation, status}``.
        """
        settings = get_settings()
        body: dict[str, Any] = {
            "collection_id": collection_id or await self.ensure_collection(),
            "source_url": source_url,
            "fps": fps if fps is not None else settings.memories_index_fps,
        }
        if metadata:
            body["metadata"] = metadata
        if idempotency_key:
            body["idempotency_key"] = idempotency_key

        return await self._request("POST", "/videos", json=body)

    async def get_video(self, video_id: str) -> dict[str, Any]:
        """Get video details: status, duration, AI title, tags (free)."""
        return await self._request("GET", f"/videos/{video_id}")

    async def upload_video_file(
        self,
        file_path: str | Path,
        collection_id: str | None = None,
        fps: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upload a local file with multipart/form-data.

        Recommended up to ~100 MB; use the resumable flow above that. Billed per
        minute of video. Returns ``{video_id, operation}``.
        """
        settings = get_settings()
        path = Path(file_path)
        if not path.is_file():
            raise MemoriesDatalakeError(f"No such file: {path}")

        body: dict[str, Any] = {
            "collection_id": collection_id or await self.ensure_collection(),
            "fps": fps if fps is not None else settings.memories_index_fps,
        }
        if metadata:
            body["metadata"] = metadata

        # Uploads are large; give them their own, longer timeout.
        timeout = max(self.timeout, 300.0)
        url = f"{self.base_url}/videos"
        headers = {"Authorization": self.api_key}

        try:
            with path.open("rb") as handle:
                files = {
                    "json": (None, json_dumps(body), "application/json"),
                    "file": (path.name, handle, "application/octet-stream"),
                }
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, files=files)
        except httpx.HTTPError as exc:
            raise MemoriesDatalakeError(f"POST /videos (multipart) failed: {exc}") from exc
        except OSError as exc:
            raise MemoriesDatalakeError(f"Could not read {path}: {exc}") from exc

        if response.status_code >= 400:
            raise MemoriesDatalakeError(
                f"POST /videos (multipart) returned {response.status_code}: {response.text[:300]}",
                status_code=response.status_code,
            )
        return _as_dict(response, "POST /videos (multipart)")

    async def start_resumable_upload(
        self,
        collection_id: str | None = None,
        fps: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Open a resumable upload session for a large file.

        Returns ``{video_id, upload_url, chunk_size}``. The caller PUTs the file
        to the GCS session URI, then calls :meth:`finalize_upload`.
        """
        settings = get_settings()
        body: dict[str, Any] = {
            "collection_id": collection_id or await self.ensure_collection(),
            "fps": fps if fps is not None else settings.memories_index_fps,
        }
        if metadata:
            body["metadata"] = metadata
        return await self._request(
            "POST", "/videos", json=body, params={"upload": "resumable"}
        )

    async def finalize_upload(self, video_id: str) -> dict[str, Any]:
        """Confirm a resumable upload finished and start indexing (free)."""
        return await self._request("POST", f"/videos/{video_id}:finalize")

    async def update_video(
        self,
        video_id: str,
        tags: list[str] | None = None,
        custom: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Write a verdict back onto a video as tags and metadata (free).

        Tags become filters for the next query, which is what makes the
        curation loop compound: each pass narrows the next one.
        """
        metadata: dict[str, Any] = {}
        if tags is not None:
            metadata["tags"] = list(tags)
        if custom is not None:
            metadata["custom"] = custom
        if title is not None:
            metadata["title"] = title

        if not metadata:
            raise MemoriesDatalakeError("update_video needs tags, custom or title")

        return await self._request("PATCH", f"/videos/{video_id}", json={"metadata": metadata})

    async def list_videos(
        self,
        collection_id: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List videos, optionally filtered by status or exact tag (free).

        This is the curation worklist: `tag="first_person_view"` is the ego
        subset, `status="failed"` is everything that never finished indexing.
        """
        return await self._request(
            "GET",
            "/videos",
            params={
                "collection_id": collection_id or await self.ensure_collection(),
                "status": status,
                "tag": tag,
                "cursor": cursor,
                "limit": limit,
            },
        )

    async def get_clip(self, video_id: str, start: float, end: float) -> dict[str, Any]:
        """Cut a span and get a signed download link ($0.005 + egress)."""
        return await self._request(
            "GET",
            f"/videos/{video_id}/clip",
            params={"start": start, "end": end},
        )

    async def get_events(
        self,
        video_id: str,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        """Read detector events for a video ($0.001/call)."""
        return await self._request(
            "GET",
            f"/videos/{video_id}/events",
            params={"event_type": event_type},
        )

    # ---------------------------------------------------------------- operations

    async def get_operation(self, operation_id: str) -> dict[str, Any]:
        """Poll an async operation (free)."""
        return await self._request("GET", f"/operations/{operation_id}")

    async def wait_for_operation(
        self,
        operation_id: str,
        max_wait_seconds: float | None = None,
        poll_interval_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Poll an operation until it is done or the wait budget runs out.

        Indexing runs ``preprocess → index → derive`` and can take minutes, so
        the wait is deliberately bounded: the last operation payload is returned
        either way and ``done`` tells the caller which happened.

        Args:
            operation_id: Operation to poll.
            max_wait_seconds: Total wait budget. Defaults to settings.
            poll_interval_seconds: Delay between polls. Defaults to settings.

        Returns:
            The most recent operation payload.
        """
        settings = get_settings()
        budget = float(
            max_wait_seconds if max_wait_seconds is not None
            else settings.memories_index_wait_seconds
        )
        interval = float(
            poll_interval_seconds if poll_interval_seconds is not None
            else settings.memories_index_poll_seconds
        )

        loop = asyncio.get_running_loop()
        deadline = loop.time() + budget
        operation = await self.get_operation(operation_id)

        while not operation.get("done"):
            if loop.time() + interval > deadline:
                return operation
            await asyncio.sleep(interval)
            operation = await self.get_operation(operation_id)

        return operation

    # ------------------------------------------------------------------ derived

    async def get_title(self, video_id: str) -> dict[str, Any]:
        """Get the AI title ($0.001/call)."""
        return await self._request("GET", f"/videos/{video_id}/title")

    async def get_summary(self, video_id: str) -> dict[str, Any]:
        """Get the AI summary ($0.001/call)."""
        return await self._request("GET", f"/videos/{video_id}/summary")

    async def get_caption(
        self,
        video_id: str,
        start: float | None = None,
        end: float | None = None,
    ) -> dict[str, Any]:
        """Get visual captions, whole-video or for a time window ($0.001/call)."""
        return await self._request(
            "GET",
            f"/videos/{video_id}/caption",
            params={"start": start, "end": end},
        )

    async def get_transcription(
        self,
        video_id: str,
        start: float | None = None,
        end: float | None = None,
    ) -> dict[str, Any]:
        """Get the audio transcription, whole-video or windowed ($0.001/call)."""
        return await self._request(
            "GET",
            f"/videos/{video_id}/transcription",
            params={"start": start, "end": end},
        )

    async def get_moment(self, ref: str, expand: list[str] | None = None) -> dict[str, Any]:
        """Get a time-slice aggregate for ``video_id@start-end`` ($0.008/call)."""
        return await self._request(
            "GET",
            f"/moments/{ref}",
            params={"expand": ",".join(expand) if expand else None},
        )

    # ------------------------------------------------------------------- search

    async def search(
        self,
        query: str,
        collection_id: str | None = None,
        targets: list[str] | None = None,
        top_k: int = 10,
        mode: str = "semantic",
        group_by: str | None = None,
        rerank: bool = False,
    ) -> dict[str, Any]:
        """Search indexed moments ($0.008/call, more with rerank).

        Args:
            query: Natural language (or keyword) query.
            collection_id: Collection to search. Defaults to the resolved one.
            targets: Content to match against. Defaults to caption + transcription.
            top_k: Maximum results.
            mode: ``semantic``, ``keyword`` or ``hybrid``.
            group_by: ``moment`` or ``video``.
            rerank: Run the extra cross-encoder pass.

        Returns:
            Search payload with ``results`` and ``next_cursor``.
        """
        body: dict[str, Any] = {
            "collection_id": collection_id or await self.ensure_collection(),
            "query": query,
            "targets": list(targets) if targets else ["caption", "transcription"],
            "mode": mode,
            "top_k": top_k,
        }
        if group_by:
            body["group_by"] = group_by
        if rerank:
            body["rerank"] = True

        return await self._request("POST", "/search", json=body)
