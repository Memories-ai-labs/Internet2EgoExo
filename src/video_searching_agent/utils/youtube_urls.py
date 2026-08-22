"""Reading a YouTube URL. A leaf module on purpose.

Both halves of the system need to turn a URL into a video id — the fetcher, to
ask the Data API about it, and the pre-download frame check, to find its
stills. Putting the parsing in either one would make the pipeline and the
curation packages import each other, so it lives here, importing nothing.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}

_ISO_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def is_youtube_url(url: str) -> bool:
    """Whether this URL is one YouTube serves."""

    try:
        return (urlparse(url).hostname or "").lower() in _HOSTS
    except ValueError:
        return False


def youtube_video_id(url: str) -> str | None:
    """The video id in a watch, short-link, shorts, live or embed URL."""

    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if host not in _HOSTS:
        return None
    if host.endswith("youtu.be"):
        candidate = parsed.path.strip("/").split("/")[0]
        return candidate or None
    if parsed.path == "/watch":
        values = parse_qs(parsed.query).get("v") or []
        return values[0] if values else None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] in ("shorts", "embed", "live", "v"):
        return parts[1]
    return None


def parse_iso_duration(value: str) -> int | None:
    """Seconds from an ISO 8601 duration, which is what the Data API returns."""

    match = _ISO_DURATION.match(value or "")
    if not match:
        return None
    parts = {key: int(raw or 0) for key, raw in match.groupdict().items()}
    return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]
