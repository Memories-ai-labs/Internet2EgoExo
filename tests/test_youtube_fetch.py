"""Reaching YouTube without an extractor.

yt-dlp stopped working against YouTube from a datacentre address — it returns
"Sign in to confirm you're not a bot" — so metadata now comes from the Data API
and the file comes through an Apify actor. These tests pin the parts that are
easy to get subtly wrong: which URLs carry an id, how the Data API's fields map
onto the shape the pipeline already speaks, and that a credential never reaches
a log line.
"""

from __future__ import annotations

import pytest

from video_searching_agent.pipeline.youtube_fetch import (
    YouTubeFetcher,
    YouTubeFetchError,
)
from video_searching_agent.utils.youtube_urls import (
    is_youtube_url,
    parse_iso_duration,
    youtube_video_id,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=abc123XYZ_-", "abc123XYZ_-"),
        ("https://youtube.com/watch?v=abc&t=42", "abc"),
        ("https://youtu.be/abc123", "abc123"),
        ("https://www.youtube.com/shorts/abc123", "abc123"),
        ("https://www.youtube.com/embed/abc123", "abc123"),
        ("https://www.youtube.com/live/abc123", "abc123"),
        ("https://m.youtube.com/watch?v=abc123", "abc123"),
        ("https://www.youtube.com/watch", None),
        ("https://vimeo.com/12345", None),
        ("not a url at all", None),
    ],
)
def test_the_video_id_is_read_from_every_shape_of_link(url: str, expected: str | None) -> None:
    assert youtube_video_id(url) == expected


def test_only_youtube_hosts_are_youtube() -> None:
    assert is_youtube_url("https://youtu.be/x")
    assert not is_youtube_url("https://notyoutube.com/watch?v=x")
    assert not is_youtube_url("")


@pytest.mark.parametrize(
    ("iso", "seconds"),
    [
        ("PT30S", 30),
        ("PT1M30S", 90),
        ("PT2H5M1S", 7501),
        ("P1DT2H", 93600),
        ("PT0S", 0),
        ("nonsense", None),
        ("", None),
    ],
)
def test_iso_durations_become_seconds(iso: str, seconds: int | None) -> None:
    assert parse_iso_duration(iso) == seconds


def test_the_fetcher_never_prints_a_credential() -> None:
    """Its repr lands in log lines and tracebacks, so it must not carry keys."""

    fetcher = YouTubeFetcher(youtube_api_key="AIzaSECRET", apify_token="apify_api_SECRET")
    printed = repr(fetcher)
    assert "AIzaSECRET" not in printed
    assert "apify_api_SECRET" not in printed
    assert "data_api=set" in printed and "apify=set" in printed


def test_a_video_cannot_be_fetched_without_an_apify_token() -> None:
    fetcher = YouTubeFetcher(youtube_api_key="key", apify_token=None)
    assert fetcher.can_download is False
    with pytest.raises(YouTubeFetchError, match="APIFY_API_TOKEN"):
        fetcher.download_url("https://www.youtube.com/watch?v=abc")


def test_probing_something_that_is_not_a_youtube_video_says_so() -> None:
    fetcher = YouTubeFetcher(youtube_api_key="key")
    with pytest.raises(YouTubeFetchError, match="Not a YouTube video URL"):
        fetcher.probe("https://vimeo.com/12345")


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    """Stands in for httpx.Client, recording what was asked for."""

    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.params: dict | None = None

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def get(self, url: str, params: dict | None = None) -> _FakeResponse:
        self.params = params
        return _FakeResponse(self.payload)


def _probe_with(monkeypatch: pytest.MonkeyPatch, payload: dict) -> dict:
    import httpx

    fake = _FakeClient(payload)
    monkeypatch.setattr(httpx, "Client", lambda **_: fake)
    fetcher = YouTubeFetcher(youtube_api_key="key")
    return fetcher.probe("https://www.youtube.com/watch?v=abc123")


def test_a_creative_commons_video_is_reported_as_reusable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Data API is the only source that states this outright."""

    info = _probe_with(
        monkeypatch,
        {
            "items": [
                {
                    "snippet": {"title": "POV cooking", "channelTitle": "Someone"},
                    "contentDetails": {"duration": "PT10M", "definition": "hd"},
                    "status": {"license": "creativeCommon"},
                    "statistics": {"viewCount": "1234"},
                }
            ]
        },
    )
    assert info["license"] == "Creative Commons Attribution"
    assert info["duration"] == 600
    assert info["height"] == 720
    assert info["view_count"] == 1234
    assert info["_source"] == "youtube-data-api"


def test_the_standard_youtube_licence_is_not_dressed_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    info = _probe_with(
        monkeypatch,
        {
            "items": [
                {
                    "snippet": {"title": "A video"},
                    "contentDetails": {"duration": "PT30S", "definition": "sd"},
                    "status": {"license": "youtube"},
                }
            ]
        },
    )
    assert info["license"] == "youtube"
    assert info["height"] == 480


def test_a_missing_video_is_named_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    monkeypatch.setattr(httpx, "Client", lambda **_: _FakeClient({"items": []}))
    fetcher = YouTubeFetcher(youtube_api_key="key")
    with pytest.raises(YouTubeFetchError, match="private, or removed"):
        fetcher.probe("https://www.youtube.com/watch?v=abc123")
