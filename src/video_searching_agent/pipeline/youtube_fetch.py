"""Fetch YouTube videos without an extractor, because the extractor is blocked.

yt-dlp no longer works against YouTube from a datacentre address. It fails with
"Sign in to confirm you're not a bot", which is not a transient error: it is
YouTube declining to serve any IP range that looks like a server. Every host
this pipeline can realistically run on — a container, a CI runner, a serverless
function — sits in one of those ranges, so the extractor path is dead for
YouTube even though it still works for other platforms.

Two replacements, both of which do their job better than the extractor did:

**Metadata comes from the YouTube Data API.** It is free, it answers in one
round trip, and it reports the one field the extractor was always vague about —
``status.license``, which says outright whether a video is Creative Commons.
Licence is a Gate 0 question, so reading it from the platform of record rather
than inferring it from a page is a straight gain.

**The file comes from Apify.** A downloader actor fetches the video from a
residential address and leaves it in Apify's key-value store, which this
process then streams to disk. It costs money per video, unlike the extractor,
so it is used for YouTube and only for YouTube.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from video_searching_agent.utils.youtube_urls import (
    parse_iso_duration,
    youtube_video_id,
)

logger = logging.getLogger(__name__)

# The actor. Chosen for being the most-run YouTube downloader on the store with
# a plain contract: give it URLs, get back a key-value-store link per video.
DOWNLOAD_ACTOR = "streamers/youtube-video-downloader"

# 480p is the resolution the quality standard asks for as a floor, and a
# smaller file is a faster upload into the Datalake. G1-RES is judged on the
# footage the Datalake indexes, so this is the resolution that must clear it.
DEFAULT_QUALITY = "480p"


class YouTubeFetchError(RuntimeError):
    """Raised when neither the Data API nor the actor could serve a video."""


@dataclass(repr=False)
class YouTubeFetcher:
    """Metadata from the Data API, files from an Apify actor."""

    youtube_api_key: str
    apify_token: str | None = None
    quality: str = DEFAULT_QUALITY
    actor: str = DOWNLOAD_ACTOR
    timeout_seconds: float = 600.0

    def __repr__(self) -> str:
        """Say what is configured without printing either credential.

        The default dataclass repr would put both keys in every log line and
        traceback that mentions the fetcher.
        """
        return (
            f"YouTubeFetcher(data_api={'set' if self.youtube_api_key else 'missing'}, "
            f"apify={'set' if self.apify_token else 'missing'}, quality={self.quality!r})"
        )

    @property
    def can_download(self) -> bool:
        """Whether a file can be fetched at all, as opposed to described."""

        return bool(self.apify_token)

    def probe(self, url: str) -> dict[str, Any]:
        """Describe a video from the Data API, in yt-dlp's own dict shape.

        Returning the extractor's shape keeps the caller from having to know
        which path served it.
        """
        import httpx

        video_id = youtube_video_id(url)
        if not video_id:
            raise YouTubeFetchError(f"Not a YouTube video URL: {url}")
        if not self.youtube_api_key:
            raise YouTubeFetchError("YOUTUBE_API_KEY is not configured")

        params = {
            "part": "snippet,contentDetails,status,statistics",
            "id": video_id,
            "key": self.youtube_api_key,
        }
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get("https://www.googleapis.com/youtube/v3/videos", params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # httpx raises several unrelated types
            raise YouTubeFetchError(f"Could not read {url}: {exc}") from exc

        items = payload.get("items") or []
        if not items:
            raise YouTubeFetchError(f"YouTube has no video {video_id} (private, or removed)")
        item = items[0]
        snippet = item.get("snippet") or {}
        details = item.get("contentDetails") or {}
        status = item.get("status") or {}

        # "creativeCommon" is the only value that means reusable. Anything else
        # is the standard YouTube licence, and Gate 0 treats it as such.
        licence = status.get("license")
        definition = (details.get("definition") or "").lower()

        return {
            "id": video_id,
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "uploader": snippet.get("channelTitle"),
            "channel": snippet.get("channelTitle"),
            "upload_date": (snippet.get("publishedAt") or "")[:10].replace("-", "") or None,
            "duration": parse_iso_duration(details.get("duration") or ""),
            "license": "Creative Commons Attribution" if licence == "creativeCommon" else licence,
            "extractor": "youtube",
            "extractor_key": "Youtube",
            "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": ((snippet.get("thumbnails") or {}).get("high") or {}).get("url"),
            "view_count": _as_int((item.get("statistics") or {}).get("viewCount")),
            # The Data API reports hd/sd rather than a pixel size. Reporting the
            # floor of the bucket is honest; the indexed video gives the truth.
            "height": 720 if definition == "hd" else 480 if definition == "sd" else None,
            "_source": "youtube-data-api",
        }

    def download_url(self, url: str) -> tuple[str, dict[str, str]]:
        """Run the actor and return a fetchable link to the file it downloaded.

        Returns:
            The URL of the stored file, and the headers needed to read it.
        """
        import httpx

        if not self.apify_token:
            raise YouTubeFetchError(
                "APIFY_API_TOKEN is not configured, and YouTube refuses direct extraction "
                "from a datacentre address"
            )

        actor_path = self.actor.replace("/", "~")
        endpoint = (
            f"https://api.apify.com/v2/acts/{actor_path}/run-sync-get-dataset-items"
            f"?timeout={int(self.timeout_seconds)}"
        )
        body = {
            "videos": [{"url": url}],
            "storeInKVStore": True,
            "preferredQuality": self.quality,
            "preferredFormat": "mp4",
        }
        headers = {"Authorization": f"Bearer {self.apify_token}"}
        try:
            with httpx.Client(timeout=self.timeout_seconds + 30) as client:
                response = client.post(endpoint, json=body, headers=headers)
                response.raise_for_status()
                items = response.json()
        except Exception as exc:
            raise YouTubeFetchError(f"Apify could not download {url}: {exc}") from exc

        if not isinstance(items, list) or not items:
            raise YouTubeFetchError(f"Apify returned nothing for {url}")
        stored = items[0].get("downloadedFileUrl")
        if not stored:
            # The actor reports its own failures in the dataset item.
            reason = items[0].get("error") or items[0].get("errorMessage") or "no file URL"
            raise YouTubeFetchError(f"Apify did not store a file for {url}: {reason}")
        return str(stored), headers


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
