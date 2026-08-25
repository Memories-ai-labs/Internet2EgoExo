"""Resolve a platform page URL to fetchable media, through paid providers.

**Why not an extractor.** `yt-dlp` was the download path for everything except
YouTube, and it does not work here. YouTube blocks it from a datacentre address
outright; TikTok fails with `Unexpected response from webpage request` on every
attempt. A run that found good footage then reported `failed` for reasons that
had nothing to do with the footage, after the search had already been paid for.

So downloads go through providers that are paid to solve exactly this, and the
routing is explicit: each provider says which platforms it serves and whether it
is configured, and the router tries them in order until one hands back a URL.

**A provider resolves, it does not download.** Every one of these ends at a
media URL, and there is already one place that streams a URL to disk under a
size bound — :meth:`ClipDownloader._stream_to_disk`. Providers return a
:class:`MediaSource` and that stays the only code that writes a file, so the
size ceiling cannot be bypassed by adding a provider.

**Only Apify is verified.** It is the one with credentials here, and its
YouTube, TikTok, Instagram and X paths were exercised against the live API. The
RapidAPI, Bright Data and Oxylabs providers are written to their documented
shapes and have never been executed, because there is no account to execute them
against; each reports itself unavailable until its key is set, so an unverified
provider cannot silently become the one a run depends on. `DOWNLOAD_PROVIDERS`
sets the order.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse

from video_searching_agent.utils.youtube_urls import is_youtube_url

logger = logging.getLogger(__name__)

YOUTUBE = "youtube"
TIKTOK = "tiktok"
INSTAGRAM = "instagram"
TWITTER = "twitter"

# Hosts, not path patterns: a shortlink is resolved by whoever fetches it, and
# guessing a platform from a path is how a Reel got treated as a Tweet.
_HOSTS: dict[str, str] = {
    "tiktok.com": TIKTOK,
    "vm.tiktok.com": TIKTOK,
    "instagram.com": INSTAGRAM,
    "instagr.am": INSTAGRAM,
    "twitter.com": TWITTER,
    "x.com": TWITTER,
    "t.co": TWITTER,
}


def platform_of(url: str) -> str:
    """Which platform a URL belongs to, or an empty string when it is not one.

    An empty answer is not a failure: a direct `.mp4` link has no platform and
    needs no provider, and the caller streams it straight to disk.
    """
    if is_youtube_url(url):
        return YOUTUBE
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return _HOSTS.get(host, "")


@dataclass
class MediaSource:
    """A fetchable media URL, and whatever the provider knew about the clip."""

    url: str
    provider: str
    headers: dict[str, str] = field(default_factory=dict)
    # Duration, title, uploader, dimensions where the provider reports them.
    # Shaped like the probe result so callers do not need to know the source.
    info: dict[str, Any] = field(default_factory=dict)
    note: str = ""


class ProviderError(RuntimeError):
    """One provider could not resolve one URL. The router tries the next."""


class NotConfiguredError(ProviderError):
    """The provider has no credentials. Not a failure to resolve, an absence."""


@runtime_checkable
class MediaProvider(Protocol):
    """Turns a platform page URL into a media URL."""

    name: str
    platforms: frozenset[str]

    def available(self) -> bool:
        """True when this provider has what it needs to be tried."""

    async def resolve(self, url: str) -> MediaSource:
        """The media URL, or raise :class:`ProviderError`."""

    async def describe(self, url: str) -> dict[str, Any]:
        """Duration, title and id without paying to fetch the file.

        Separate from :meth:`resolve` because resolving costs real money — the
        Apify actors put the video in a store to hand back a link — and the
        length gate has to run before anything is spent.
        """


def _first_media_url(item: dict[str, Any]) -> str:
    """A downloadable URL out of a scraper result, whatever it called the field.

    The actors disagree: TikTok returns `mediaUrls`, Instagram `videoUrl`, the
    tweet scraper nests it under media. Reading several names is cheaper than a
    per-actor mapping that breaks silently when an actor renames one field.
    """
    for key in ("mediaUrls", "videoUrls"):
        value = item.get(key)
        if isinstance(value, list) and value and isinstance(value[0], str):
            return value[0]
    for key in ("videoUrl", "video_url", "downloadUrl", "downloadAddr", "playAddr"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    for key in ("media", "extendedEntities", "video"):
        nested = item.get(key)
        if isinstance(nested, list):
            for entry in nested:
                if isinstance(entry, dict):
                    found = _first_media_url(entry)
                    if found:
                        return found
        elif isinstance(nested, dict):
            found = _first_media_url(nested)
            if found:
                return found
    return ""


def _info_from(item: dict[str, Any]) -> dict[str, Any]:
    """Metadata a scraper result happens to carry, in the probe result's shape."""
    meta = item.get("videoMeta") if isinstance(item.get("videoMeta"), dict) else {}
    identifier = item.get("id") or item.get("videoId") or item.get("shortCode")
    duration = meta.get("duration") or item.get("duration") or item.get("videoDuration")
    info: dict[str, Any] = {}
    if isinstance(identifier, str | int) and str(identifier):
        info["id"] = str(identifier)
    if isinstance(duration, int | float):
        info["duration"] = int(duration)
    for source, target in (("width", "width"), ("height", "height")):
        value = meta.get(source) or item.get(source)
        if isinstance(value, int | float):
            info[target] = int(value)
    for source, target in (
        ("text", "title"),
        ("title", "title"),
        ("caption", "title"),
        ("authorMeta", "uploader"),
        ("ownerUsername", "uploader"),
        ("author", "uploader"),
    ):
        value = item.get(source)
        if isinstance(value, dict):
            value = value.get("name") or value.get("nickName") or value.get("userName")
        if isinstance(value, str) and value and target not in info:
            info[target] = value
    return info


class ApifyProvider:
    """Every platform, through the actors this project already pays for.

    YouTube goes through the dedicated downloader actor, which is what the
    existing YouTube path used. The rest go through the same scrapers the search
    already calls, with their download flag on — the flag is the only reason
    TikTok could not be fetched before: the actor was asked for metadata and
    the media URL it can return was never requested.
    """

    name = "apify"
    platforms = frozenset({YOUTUBE, TIKTOK, INSTAGRAM, TWITTER})

    # Per platform: the actor, and how to ask it about one URL.
    _ACTORS: dict[str, tuple[str, str]] = {
        TIKTOK: ("clockworks/tiktok-scraper", "postURLs"),
        INSTAGRAM: ("apify/instagram-scraper", "directUrls"),
        TWITTER: ("apidojo/tweet-scraper", "startUrls"),
    }

    def __init__(self, token: str = "", youtube: Any = None) -> None:
        self._token = token
        self._youtube = youtube

    def available(self) -> bool:
        return bool(self._token)

    async def resolve(self, url: str) -> MediaSource:
        platform = platform_of(url)
        if platform == YOUTUBE:
            return self._resolve_youtube(url)
        actor = self._ACTORS.get(platform)
        if actor is None:
            raise ProviderError(f"apify has no actor for {platform or 'this host'}")
        if not self._token:
            raise NotConfiguredError("APIFY_API_TOKEN is not set")
        return await self._resolve_via_actor(url, platform, *actor)

    def _resolve_youtube(self, url: str) -> MediaSource:
        if self._youtube is None or not getattr(self._youtube, "can_download", False):
            raise NotConfiguredError("the Apify YouTube downloader is not configured")
        stored, headers = self._youtube.download_url(url)
        return MediaSource(
            url=stored,
            provider="apify/youtube-video-downloader",
            headers=headers or {},
            note="YouTube refuses direct extraction from a datacentre address",
        )

    async def describe(self, url: str) -> dict[str, Any]:
        platform = platform_of(url)
        if platform == YOUTUBE:
            if self._youtube is None:
                raise NotConfiguredError("no YouTube fetcher configured")
            return dict(self._youtube.probe(url))
        actor = self._ACTORS.get(platform)
        if actor is None:
            raise ProviderError(f"apify has no actor for {platform or 'this host'}")
        if not self._token:
            raise NotConfiguredError("APIFY_API_TOKEN is not set")
        item = await self._run_actor(url, actor[0], actor[1], download=False)
        info = _info_from(item)
        if not info:
            raise ProviderError(f"{actor[0]} described {url} with nothing usable")
        return info

    async def _run_actor(
        self, url: str, actor: str, url_field: str, *, download: bool
    ) -> dict[str, Any]:
        from video_searching_agent.api.apify_client import ApifyClient

        client = ApifyClient(api_token=self._token)
        payload: dict[str, Any] = {
            url_field: [url],
            # With this off the actor returns metadata and no file, which is
            # what a probe wants and what made every TikTok *download* fail
            # back when it was the only mode ever used.
            "shouldDownloadVideos": download,
            "resultsPerPage": 1,
        }
        try:
            items = await client.run_actor(actor, payload)
        except Exception as exc:  # noqa: BLE001 - the router reports every attempt
            raise ProviderError(f"{actor} failed for {url}: {str(exc)[:200]}") from exc
        if not items:
            raise ProviderError(f"{actor} returned nothing for {url}")
        return items[0] if isinstance(items[0], dict) else {}

    async def _resolve_via_actor(
        self, url: str, platform: str, actor: str, url_field: str
    ) -> MediaSource:
        item = await self._run_actor(url, actor, url_field, download=True)
        media = _first_media_url(item)
        if not media:
            raise ProviderError(
                f"{actor} returned a result for {url} with no media URL "
                f"(fields: {sorted(item)[:12]})"
            )
        return MediaSource(
            url=media,
            provider=f"apify/{actor.split('/')[-1]}",
            info=_info_from(item),
            note=f"fetched through Apify's {platform} actor",
        )


class _KeyedProvider:
    """Shared shape for the providers with no account here.

    Written to the documented API and never executed. `available()` is false
    without credentials, so one of these cannot quietly become the provider a
    run depends on — and if a key is set, the first run is the first test, which
    is why each says so in its error.
    """

    name = "unnamed"
    platforms = frozenset({YOUTUBE, TIKTOK, INSTAGRAM, TWITTER})
    _unverified = "this provider has never been run against a live account"

    def __init__(self, **credentials: str) -> None:
        self._credentials = {k: v for k, v in credentials.items() if v}

    def available(self) -> bool:
        return len(self._credentials) == len(self._required)

    @property
    def _required(self) -> tuple[str, ...]:
        raise NotImplementedError

    async def describe(self, url: str) -> dict[str, Any]:
        raise ProviderError(
            f"{self.name} has no metadata-only mode wired up, so it cannot be probed "
            "without paying to fetch"
        )

    def _missing(self) -> NotConfiguredError:
        missing = [k for k in self._required if k not in self._credentials]
        return NotConfiguredError(f"{self.name} needs {', '.join(missing)}")


class RapidApiProvider(_KeyedProvider):
    """A RapidAPI-hosted downloader. One key, one host per platform."""

    name = "rapidapi"

    @property
    def _required(self) -> tuple[str, ...]:
        return ("key", "host")

    async def resolve(self, url: str) -> MediaSource:
        if not self.available():
            raise self._missing()
        import httpx

        host = self._credentials["host"]
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(
                    f"https://{host}/",
                    params={"url": url},
                    headers={
                        "x-rapidapi-key": self._credentials["key"],
                        "x-rapidapi-host": host,
                    },
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"rapidapi ({host}) failed for {url}: {str(exc)[:200]}") from exc

        media = _first_media_url(body if isinstance(body, dict) else {})
        if not media:
            raise ProviderError(f"rapidapi ({host}) returned no media URL — {self._unverified}")
        return MediaSource(url=media, provider=f"rapidapi/{host}", info=_info_from(body))


class BrightDataProvider(_KeyedProvider):
    """Bright Data's Web Unlocker, returning the media through a proxy fetch."""

    name = "brightdata"

    @property
    def _required(self) -> tuple[str, ...]:
        return ("token", "zone")

    async def resolve(self, url: str) -> MediaSource:
        if not self.available():
            raise self._missing()
        import httpx

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    "https://api.brightdata.com/request",
                    headers={"Authorization": f"Bearer {self._credentials['token']}"},
                    json={"zone": self._credentials["zone"], "url": url, "format": "json"},
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"brightdata failed for {url}: {str(exc)[:200]}") from exc

        media = _first_media_url(body if isinstance(body, dict) else {})
        if not media:
            raise ProviderError(f"brightdata returned no media URL — {self._unverified}")
        return MediaSource(url=media, provider="brightdata", info=_info_from(body))


class OxylabsProvider(_KeyedProvider):
    """Oxylabs Web Scraper API, username and password rather than a token."""

    name = "oxylabs"

    @property
    def _required(self) -> tuple[str, ...]:
        return ("username", "password")

    async def resolve(self, url: str) -> MediaSource:
        if not self.available():
            raise self._missing()
        import httpx

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    "https://realtime.oxylabs.io/v1/queries",
                    auth=(self._credentials["username"], self._credentials["password"]),
                    json={"source": "universal", "url": url, "parse": True},
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"oxylabs failed for {url}: {str(exc)[:200]}") from exc

        results = body.get("results") if isinstance(body, dict) else None
        first = results[0] if isinstance(results, list) and results else {}
        content = first.get("content") if isinstance(first, dict) else {}
        media = _first_media_url(content if isinstance(content, dict) else {})
        if not media:
            raise ProviderError(f"oxylabs returned no media URL — {self._unverified}")
        return MediaSource(url=media, provider="oxylabs", info=_info_from(content))


class ProviderRouter:
    """Try the configured providers in order until one resolves the URL.

    Every attempt is reported when they all fail. A single "download failed" was
    what made the TikTok problem take so long to see: the message named the
    extractor, not the fact that nothing else had been tried.
    """

    def __init__(self, providers: Sequence[MediaProvider]) -> None:
        self.providers = list(providers)

    def for_url(self, url: str) -> list[MediaProvider]:
        """The providers that serve this URL's platform and are configured."""
        platform = platform_of(url)
        if not platform:
            return []
        return [p for p in self.providers if platform in p.platforms and p.available()]

    async def describe(self, url: str) -> dict[str, Any]:
        """Metadata from the first provider that can give it without spending."""
        candidates = self.for_url(url)
        if not candidates:
            raise ProviderError(
                f"no configured provider describes {platform_of(url) or 'this host'}"
            )
        attempts: list[str] = []
        for provider in candidates:
            try:
                info = await provider.describe(url)
            except ProviderError as exc:
                attempts.append(f"{provider.name}: {exc}")
                continue
            if info:
                return info
        raise ProviderError(f"no provider could describe {url} — " + " | ".join(attempts))

    async def resolve(self, url: str) -> MediaSource:
        candidates = self.for_url(url)
        if not candidates:
            platform = platform_of(url) or "this host"
            configured = [p.name for p in self.providers if p.available()] or ["none"]
            raise ProviderError(
                f"no configured download provider serves {platform}. "
                f"Configured: {', '.join(configured)}. Set DOWNLOAD_PROVIDERS and the "
                "matching credentials."
            )

        attempts: list[str] = []
        for provider in candidates:
            try:
                source = await provider.resolve(url)
            except ProviderError as exc:
                attempts.append(f"{provider.name}: {exc}")
                logger.info("provider %s could not resolve %s: %s", provider.name, url, exc)
                continue
            if attempts:
                logger.info(
                    "resolved %s with %s after %d failure(s)",
                    url,
                    provider.name,
                    len(attempts),
                )
            return source
        raise ProviderError(f"every provider failed for {url} — " + " | ".join(attempts))


def build_router(youtube: Any = None) -> ProviderRouter:
    """The router the settings ask for, in the order they ask for it."""
    from video_searching_agent.config.settings import get_settings

    settings = get_settings()
    built: dict[str, MediaProvider] = {
        "apify": ApifyProvider(token=settings.apify_api_token or "", youtube=youtube),
        "rapidapi": RapidApiProvider(
            key=getattr(settings, "rapidapi_key", "") or "",
            host=getattr(settings, "rapidapi_host", "") or "",
        ),
        "brightdata": BrightDataProvider(
            token=getattr(settings, "brightdata_token", "") or "",
            zone=getattr(settings, "brightdata_zone", "") or "",
        ),
        "oxylabs": OxylabsProvider(
            username=getattr(settings, "oxylabs_username", "") or "",
            password=getattr(settings, "oxylabs_password", "") or "",
        ),
    }
    wanted = [
        name.strip().lower()
        for name in (getattr(settings, "download_providers", "") or "apify").split(",")
        if name.strip()
    ]
    ordered = [built[name] for name in wanted if name in built]
    unknown = [name for name in wanted if name not in built]
    if unknown:
        logger.warning("ignoring unknown download provider(s): %s", ", ".join(unknown))
    return ProviderRouter(ordered or [built["apify"]])
