"""Download candidate clips through paid providers.

Platform page URLs (a youtube.com/watch link, a tiktok.com/@user/video link)
are not fetchable media, so the Datalake cannot ingest them by URL. The
collection path is therefore: download here, then upload the file.

Downloads are bounded on purpose — a collection run should not be able to fill
the disk or stall on one four-hour stream. Callers get back what actually
landed on disk, including the true duration, which is what the manifest and the
cost model are computed from.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from video_searching_agent.pipeline.media_probe import read_mp4_dimensions
from video_searching_agent.pipeline.youtube_fetch import YouTubeFetcher, YouTubeFetchError
from video_searching_agent.utils.youtube_urls import is_youtube_url

logger = logging.getLogger(__name__)


# Some hosts — Wikimedia among them — refuse a request that does not identify
# itself, and yt-dlp's own default is refused by name in places. An honest,
# contactable agent string is both politer and more likely to be served.
DEFAULT_USER_AGENT = (
    "InternetVideoSearch/0.1 (+https://github.com/Memories-ai-labs/Internet-Video-Search)"
)

# A link that is already the media file needs no extractor. Dataset pages, lab
# sites and archives serve these directly, and some of those hosts refuse
# yt-dlp outright — so a plain fetch is tried when the extractor gives up.
MEDIA_EXTENSIONS = (
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
    ".mkv",
    ".avi",
    ".ogv",
    ".mpg",
    ".mpeg",
)


@dataclass
class DownloadedClip:
    """A file that actually landed on disk."""

    url: str
    path: Path
    duration_seconds: int | None = None
    filesize_bytes: int | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    title: str | None = None
    uploader: str | None = None
    extractor: str | None = None
    license_note: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def size_mb(self) -> float:
        return round((self.filesize_bytes or 0) / (1024 * 1024), 2)


class DownloadError(RuntimeError):
    """Raised when a clip could not be downloaded."""


def is_direct_media_url(url: str) -> bool:
    """True when the URL path already names a media file."""
    try:
        path = unquote(urlparse(url).path).lower()
    except ValueError:
        return False
    return path.endswith(MEDIA_EXTENSIONS)


def _configured_user_agent() -> str:
    """The configured agent string, falling back to the default."""
    try:
        from video_searching_agent.config.settings import get_settings

        configured = (get_settings().download_user_agent or "").strip()
    except Exception:  # settings are optional for a bare downloader
        configured = ""
    return configured or DEFAULT_USER_AGENT


def _is_writable(directory: Path) -> bool:
    """Whether a directory can be created and written to, tested by doing it.

    Asking the filesystem is the only reliable answer: a serverless function
    has a read-only project directory and a writable /tmp, and nothing in the
    environment says so outright.
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write-probe"
        probe.write_bytes(b"")
        probe.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def _resolve_download_dir(explicit: str | Path | None) -> Path:
    """Where downloads land, falling back to somewhere that actually works.

    A serverless deployment has a read-only project directory, so the default
    ``./downloads`` raises ``Read-only file system`` at the first fetch — which
    is exactly how the hosted backend managed to look healthy while being
    unable to download anything. The fallback is the system temp directory,
    which is writable there and everywhere else.
    """
    if explicit:
        return Path(explicit)

    configured = ""
    try:
        from video_searching_agent.config.settings import get_settings

        configured = get_settings().download_dir
    except Exception:  # noqa: BLE001 - settings are optional here
        configured = ""
    if configured:
        return Path(configured)

    preferred = Path("downloads")
    if _is_writable(preferred):
        return preferred
    fallback = Path(tempfile.gettempdir()) / "internet-video-search-downloads"
    logger.info("%s is not writable; downloading to %s instead", preferred, fallback)
    return fallback


def _configured_youtube_fetcher() -> YouTubeFetcher | None:
    """A YouTube fetcher built from settings, or nothing if it cannot work.

    Without a Data API key there is nothing to describe a video with, so the
    extractor stays the only path — it still works where YouTube has not
    blocked the address.
    """
    try:
        from video_searching_agent.config.settings import get_settings

        settings = get_settings()
    except Exception:  # noqa: BLE001 - settings are optional here
        return None
    if not settings.youtube_api_key:
        return None
    return YouTubeFetcher(
        youtube_api_key=settings.youtube_api_key,
        apify_token=settings.apify_api_token,
    )


def _slug(value: str) -> str:
    """A filename-safe piece of a provider or video id."""
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in value).strip("-") or "clip"


def _select_info(info: dict[str, Any]) -> dict[str, Any]:
    """Unwrap playlist results to the single entry yt-dlp actually fetched."""
    if info.get("_type") == "playlist":
        entries = [entry for entry in (info.get("entries") or []) if entry]
        if not entries:
            raise DownloadError("Playlist contained no downloadable entries")
        return entries[0]
    return info


class ClipDownloader:
    """Fetch clips to a working directory, with bounds that keep a run sane."""

    def __init__(
        self,
        output_dir: str | Path | None = None,
        max_duration_seconds: int = 3 * 60 * 60,
        max_filesize_mb: int = 2048,
        user_agent: str | None = None,
        youtube: YouTubeFetcher | bool | None = None,
    ) -> None:
        """Initialize the downloader.

        Args:
            output_dir: Where files land. Defaults to ``DOWNLOAD_DIR``, then
                ``./downloads``, then the system temp directory when neither
                is writable — which is the case on a serverless host.
            max_duration_seconds: Skip anything longer (default 3h).
            max_filesize_mb: Skip anything larger (default 2 GB).
            user_agent: Identify the fetcher. Defaults to settings, which
                default to :data:`DEFAULT_USER_AGENT`.
            youtube: How to reach YouTube, which the extractor can no longer
                do from a server address. Defaults to a fetcher built from
                settings; pass ``False`` to insist on the extractor.
        """
        self.output_dir = _resolve_download_dir(output_dir)
        self.max_duration_seconds = max_duration_seconds
        self.max_filesize_mb = max_filesize_mb
        self.user_agent = user_agent or _configured_user_agent()
        self.youtube = _configured_youtube_fetcher() if youtube is None else (youtube or None)

    def probe(self, url: str) -> dict[str, Any]:
        """Read a clip's metadata without downloading it.

        Cheap enough to run before committing disk and Datalake spend, and it is
        how the duration and licence gates get their answer.

        There is no extractor here either. A TikTok probe through `yt-dlp` fails
        for the same reason the download did, so a candidate died before any
        provider was asked — which made the download routing pointless. YouTube
        is described by the Data API; the rest by whichever provider can answer
        without paying to fetch the file.
        """
        return asyncio.run(self._probe(url))

    async def probe_async(self, url: str) -> dict[str, Any]:
        """:meth:`probe` from an event loop that is already running."""
        return await self._probe(url)

    async def _probe(self, url: str) -> dict[str, Any]:
        if self.youtube and is_youtube_url(url):
            try:
                return self.youtube.probe(url)
            except YouTubeFetchError as exc:
                raise DownloadError(f"Could not read {url}: {exc}") from exc

        if is_direct_media_url(url):
            return self._probe_direct(url)

        from video_searching_agent.pipeline.media_providers import ProviderError, build_router

        try:
            info = await build_router(youtube=self.youtube).describe(url)
        except ProviderError as exc:
            # A direct file that does not look like one by its extension is the
            # one case worth a second guess: the headers settle it for nothing.
            try:
                return self._probe_direct(url)
            except DownloadError:
                raise DownloadError(f"Could not read {url}: {exc}") from exc
        return info

    def _probe_direct(self, url: str) -> dict[str, Any]:
        """Describe a direct media link from its own headers.

        Duration is unknown here — reading it would mean decoding the file — so
        it is left out rather than guessed, and the indexed video supplies it.
        """
        import httpx

        name = Path(unquote(urlparse(url).path)).name
        headers = {"User-Agent": self.user_agent}
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                response = client.head(url, headers=headers)
                if response.status_code >= 400:
                    # Some hosts only answer GET; ask for one byte.
                    response = client.get(url, headers={**headers, "Range": "bytes=0-0"})
        except httpx.HTTPError as exc:
            raise DownloadError(f"Could not read {url}: {exc}") from exc

        if response.status_code >= 400:
            raise DownloadError(f"Could not read {url}: host returned {response.status_code}")

        content_type = response.headers.get("content-type", "")
        if content_type and not content_type.startswith(("video/", "application/octet-stream")):
            raise DownloadError(f"{url} is {content_type or 'not a video'}, not a video file")

        size = response.headers.get("content-range") or response.headers.get("content-length")
        filesize = None
        if size:
            tail = str(size).split("/")[-1]
            filesize = int(tail) if tail.isdigit() else None

        return {
            "_direct": True,
            "id": Path(name).stem,
            "title": Path(name).stem.replace("_", " "),
            "ext": Path(name).suffix.lstrip(".") or "mp4",
            "webpage_url": url,
            "url": url,
            "filesize": filesize,
            "extractor_key": "direct",
        }

    def download(self, url: str) -> DownloadedClip:
        """Download one clip, respecting the duration and size bounds.

        Raises:
            DownloadError: On a failed fetch, or when the clip breaches a bound.
        """
        return asyncio.run(self._download(url))

    async def download_async(self, url: str) -> DownloadedClip:
        """:meth:`download` from an event loop that is already running."""
        return await self._download(url)

    async def _download(self, url: str) -> DownloadedClip:
        """Resolve the bytes through a provider, then stream them to disk.

        There is no extractor path any more. `yt-dlp` is blocked on YouTube from
        a datacentre address and fails outright on TikTok, so a run that leaned
        on it reported failures that said nothing about the footage. Providers
        are asked in the configured order and every attempt is reported when
        they all refuse.
        """
        info = await self.probe_async(url)
        if info.get("_direct"):
            return self._download_direct(url, info)

        duration = info.get("duration")
        if isinstance(duration, int | float) and duration > self.max_duration_seconds:
            raise DownloadError(
                f"Clip is {int(duration)}s, over the {self.max_duration_seconds}s limit"
            )

        from video_searching_agent.pipeline.media_providers import ProviderError, build_router

        try:
            source = await build_router(youtube=self.youtube).resolve(url)
        except ProviderError as exc:
            raise DownloadError(f"Download failed for {url}: {exc}") from exc

        merged = {**info, **{k: v for k, v in source.info.items() if v not in (None, "")}}
        video_id = merged.get("id") or "video"
        path = self.output_dir / f"{_slug(source.provider)}-{_slug(str(video_id))}.mp4"
        written = self._stream_to_disk(source.url, path, headers=source.headers)

        # The file is the only reliable source of dimensions: the YouTube Data
        # API reports `hd`/`sd` and the scrapers report the upload's shape, not
        # the delivered one, and without a width orientation cannot be judged.
        measured = read_mp4_dimensions(path)
        merged_duration = merged.get("duration")
        return DownloadedClip(
            url=url,
            path=path,
            duration_seconds=(
                int(merged_duration) if isinstance(merged_duration, int | float) else None
            ),
            filesize_bytes=written,
            width=measured[0] if measured else merged.get("width"),
            height=measured[1] if measured else merged.get("height"),
            fps=merged.get("fps"),
            title=merged.get("title"),
            uploader=merged.get("uploader") or merged.get("channel"),
            extractor=source.provider,
            license_note=str(merged["license"]) if merged.get("license") else None,
            warnings=[source.note] if source.note else [],
        )

    def _download_via_youtube_fetcher(self, url: str, info: dict[str, Any]) -> DownloadedClip:
        """Fetch a YouTube video through Apify and stream it to disk.

        The actor leaves the file in Apify's key-value store and hands back a
        link, so the fetch itself is an ordinary authenticated download. The
        stored copy expires after a few days, which is irrelevant: it is read
        once, here, on the way to the Datalake.
        """
        assert self.youtube is not None
        stored, headers = self.youtube.download_url(url)
        video_id = info.get("id") or "video"
        path = self.output_dir / f"youtube-{video_id}.mp4"
        written = self._stream_to_disk(stored, path, headers=headers)

        duration = info.get("duration")
        # The Data API reports `hd`/`sd` and no dimensions, so the file itself is
        # the only source of a width — and without one, orientation cannot be
        # judged. A 9:16 phone video was being rejected on an uncertain hand
        # density while "is it portrait", which is certain and decisive, went
        # unmeasured.
        measured = read_mp4_dimensions(path)
        return DownloadedClip(
            url=url,
            path=path,
            duration_seconds=int(duration) if isinstance(duration, int | float) else None,
            filesize_bytes=written,
            width=measured[0] if measured else info.get("width"),
            height=measured[1] if measured else info.get("height"),
            fps=info.get("fps"),
            title=info.get("title"),
            uploader=info.get("uploader") or info.get("channel"),
            extractor="youtube+apify",
            license_note=str(info["license"]) if info.get("license") else None,
            warnings=[
                "fetched through Apify: YouTube refuses direct extraction from a datacentre address"
            ],
        )

    def _stream_to_disk(self, url: str, path: Path, headers: dict[str, str] | None = None) -> int:
        """Write a URL to a file, stopping at the size bound. Returns bytes."""
        import httpx

        limit = self.max_filesize_mb * 1024 * 1024
        self.output_dir.mkdir(parents=True, exist_ok=True)
        request_headers = {"User-Agent": self.user_agent, **(headers or {})}
        written = 0
        try:
            with httpx.Client(timeout=None, follow_redirects=True) as client:
                with client.stream("GET", url, headers=request_headers) as response:
                    if response.status_code >= 400:
                        raise DownloadError(
                            f"Download failed for {url}: host returned {response.status_code}"
                        )
                    with open(path, "wb") as handle:
                        for chunk in response.iter_bytes(1024 * 256):
                            written += len(chunk)
                            if written > limit:
                                handle.close()
                                path.unlink(missing_ok=True)
                                raise DownloadError(
                                    f"Clip exceeded the {self.max_filesize_mb} MB limit "
                                    "while downloading"
                                )
                            handle.write(chunk)
        except httpx.HTTPError as exc:
            path.unlink(missing_ok=True)
            raise DownloadError(f"Download failed for {url}: {exc}") from exc
        if not written:
            path.unlink(missing_ok=True)
            raise DownloadError(f"Download failed for {url}: the host sent an empty file")
        return written

    def _download_direct(self, url: str, info: dict[str, Any]) -> DownloadedClip:
        """Stream a direct media link to disk, honouring the size bound."""
        import httpx

        declared = info.get("filesize")
        limit = self.max_filesize_mb * 1024 * 1024
        if isinstance(declared, int) and declared > limit:
            raise DownloadError(
                f"Clip is {declared // (1024 * 1024)} MB, over the {self.max_filesize_mb} MB limit"
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"direct-{info['id']}.{info['ext']}"
        written = 0

        try:
            with httpx.Client(timeout=None, follow_redirects=True) as client:
                with client.stream("GET", url, headers={"User-Agent": self.user_agent}) as response:
                    if response.status_code >= 400:
                        raise DownloadError(
                            f"Download failed for {url}: host returned {response.status_code}"
                        )
                    with open(path, "wb") as handle:
                        for chunk in response.iter_bytes(1024 * 256):
                            written += len(chunk)
                            if written > limit:
                                handle.close()
                                path.unlink(missing_ok=True)
                                raise DownloadError(
                                    f"Clip exceeded the {self.max_filesize_mb} MB limit "
                                    "while downloading"
                                )
                            handle.write(chunk)
        except httpx.HTTPError as exc:
            path.unlink(missing_ok=True)
            raise DownloadError(f"Download failed for {url}: {exc}") from exc

        return DownloadedClip(
            url=url,
            path=path,
            duration_seconds=None,
            filesize_bytes=written,
            title=info.get("title"),
            extractor="direct",
            warnings=["fetched directly: no extractor metadata, duration comes from the index"],
        )

    def discard(self, clip: DownloadedClip) -> None:
        """Delete a downloaded file once it is indexed or rejected.

        A collection run can pull hundreds of clips; keeping them after upload
        is what fills a disk.
        """
        try:
            clip.path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("could not delete %s: %s", clip.path, exc)

    def free_space_mb(self) -> float:
        """Free space on the download volume, for pre-flight checks."""
        target = self.output_dir if self.output_dir.exists() else self.output_dir.parent
        try:
            return round(shutil.disk_usage(target).free / (1024 * 1024), 1)
        except OSError:
            return 0.0
