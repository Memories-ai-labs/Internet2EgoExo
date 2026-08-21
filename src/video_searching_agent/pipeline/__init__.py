"""Collection pipeline: screen, download, upload, index, clean, annotate."""

from video_searching_agent.pipeline.download import (
    ClipDownloader,
    DownloadedClip,
    DownloadError,
)
from video_searching_agent.pipeline.ingest import IngestPipeline, IngestResult

__all__ = [
    "ClipDownloader",
    "DownloadError",
    "DownloadedClip",
    "IngestPipeline",
    "IngestResult",
]
