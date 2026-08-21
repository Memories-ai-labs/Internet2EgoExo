"""Download candidate clips with yt-dlp.

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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Progressive MP4 up to 1080p: one file, no ffmpeg merge step required.
DEFAULT_FORMAT = "best[ext=mp4][height<=1080]/best[height<=1080]/best"


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
        format_selector: str = DEFAULT_FORMAT,
    ) -> None:
        """Initialize the downloader.

        Args:
            output_dir: Where files land. Defaults to ``./downloads``.
            max_duration_seconds: Skip anything longer (default 3h).
            max_filesize_mb: Skip anything larger (default 2 GB).
            format_selector: yt-dlp format string.
        """
        self.output_dir = Path(output_dir or "downloads")
        self.max_duration_seconds = max_duration_seconds
        self.max_filesize_mb = max_filesize_mb
        self.format_selector = format_selector

    def probe(self, url: str) -> dict[str, Any]:
        """Read a clip's metadata without downloading it.

        Cheap enough to run before committing disk and Datalake spend, and it
        is how duration/licence get checked up front.
        """
        from yt_dlp import YoutubeDL

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:  # yt-dlp raises a wide range of errors
            raise DownloadError(f"Could not read {url}: {exc}") from exc

        if not isinstance(info, dict):
            raise DownloadError(f"Could not read {url}: no metadata returned")
        return _select_info(info)

    async def probe_async(self, url: str) -> dict[str, Any]:
        """Off-thread :meth:`probe`, so the event loop keeps serving."""
        return await asyncio.to_thread(self.probe, url)

    def download(self, url: str) -> DownloadedClip:
        """Download one clip, respecting the duration and size bounds.

        Raises:
            DownloadError: On a failed fetch, or when the clip breaches a bound.
        """
        from yt_dlp import YoutubeDL

        info = self.probe(url)

        duration = info.get("duration")
        if isinstance(duration, int | float) and duration > self.max_duration_seconds:
            raise DownloadError(
                f"Clip is {int(duration)}s, over the {self.max_duration_seconds}s limit"
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        template = str(self.output_dir / "%(extractor)s-%(id)s.%(ext)s")
        warnings: list[str] = []

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "outtmpl": template,
            "format": self.format_selector,
            "max_filesize": self.max_filesize_mb * 1024 * 1024,
            "retries": 2,
            "socket_timeout": 30,
        }

        try:
            with YoutubeDL(options) as ydl:
                result = _select_info(ydl.extract_info(url, download=True) or {})
                path_str = ydl.prepare_filename(result)
        except Exception as exc:
            raise DownloadError(f"Download failed for {url}: {exc}") from exc

        path = Path(path_str)
        if not path.is_file():
            # yt-dlp may have remuxed to a different extension.
            candidates = sorted(self.output_dir.glob(f"{path.stem}.*"))
            if not candidates:
                raise DownloadError(
                    f"Download reported success but no file was written for {url}"
                )
            path = candidates[0]
            warnings.append(f"file landed as {path.name}")

        licence = result.get("license")
        return DownloadedClip(
            url=url,
            path=path,
            duration_seconds=int(duration) if isinstance(duration, int | float) else None,
            filesize_bytes=path.stat().st_size,
            width=result.get("width"),
            height=result.get("height"),
            fps=result.get("fps"),
            title=result.get("title"),
            uploader=result.get("uploader") or result.get("channel"),
            extractor=result.get("extractor_key") or result.get("extractor"),
            license_note=str(licence) if licence else None,
            warnings=warnings,
        )

    async def download_async(self, url: str) -> DownloadedClip:
        """Off-thread :meth:`download`."""
        return await asyncio.to_thread(self.download, url)

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
