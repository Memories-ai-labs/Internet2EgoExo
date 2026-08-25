"""What the download routing must decide, without touching a network.

The routing is the whole point of the module: which provider gets asked, in what
order, and what is reported when none of them can answer. A wrong answer here
spends money at the wrong vendor or reports a failure that names the wrong
cause, which is how the TikTok problem stayed invisible for so long.
"""

from __future__ import annotations

import pytest

from video_searching_agent.pipeline.media_providers import (
    INSTAGRAM,
    TIKTOK,
    TWITTER,
    YOUTUBE,
    MediaSource,
    NotConfiguredError,
    ProviderError,
    ProviderRouter,
    _first_media_url,
    _info_from,
    platform_of,
)


class Fake:
    """A provider that records being asked, and answers however the test says."""

    def __init__(self, name, platforms, *, ready=True, media="", fail=""):
        self.name = name
        self.platforms = frozenset(platforms)
        self._ready = ready
        self._media = media
        self._fail = fail
        self.asked: list[str] = []

    def available(self) -> bool:
        return self._ready

    async def resolve(self, url: str) -> MediaSource:
        self.asked.append(url)
        if self._fail:
            raise ProviderError(self._fail)
        return MediaSource(url=self._media, provider=self.name)

    async def describe(self, url: str) -> dict:
        self.asked.append(url)
        if self._fail:
            raise ProviderError(self._fail)
        return {"duration": 12}


class TestWhichPlatformAUrlIs:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://www.youtube.com/watch?v=abc", YOUTUBE),
            ("https://youtu.be/abc", YOUTUBE),
            ("https://www.tiktok.com/@chef/video/123", TIKTOK),
            ("https://vm.tiktok.com/ZM123/", TIKTOK),
            ("https://www.instagram.com/reel/abc/", INSTAGRAM),
            ("https://x.com/someone/status/1", TWITTER),
            ("https://twitter.com/someone/status/1", TWITTER),
        ],
    )
    def test_the_host_decides(self, url, expected):
        assert platform_of(url) == expected

    def test_a_direct_file_has_no_platform(self):
        """Not a failure: it needs no provider, it is already the media."""
        assert platform_of("https://example.com/clip.mp4") == ""

    def test_an_unknown_host_has_no_platform(self):
        assert platform_of("https://vimeo.com/12345") == ""


class TestOrderAndAvailability:
    @pytest.mark.asyncio
    async def test_the_configured_order_is_the_order_tried(self):
        first = Fake("first", [TIKTOK], media="https://cdn/a.mp4")
        second = Fake("second", [TIKTOK], media="https://cdn/b.mp4")
        source = await ProviderRouter([first, second]).resolve(
            "https://www.tiktok.com/@a/video/1"
        )
        assert source.provider == "first"
        assert second.asked == [], "the second provider should not have been paid"

    @pytest.mark.asyncio
    async def test_a_failure_falls_through_to_the_next(self):
        broken = Fake("broken", [TIKTOK], fail="actor returned nothing")
        working = Fake("working", [TIKTOK], media="https://cdn/b.mp4")
        source = await ProviderRouter([broken, working]).resolve(
            "https://www.tiktok.com/@a/video/1"
        )
        assert source.provider == "working"
        assert broken.asked, "the first provider must actually have been tried"

    @pytest.mark.asyncio
    async def test_an_unconfigured_provider_is_never_asked(self):
        """An unverified provider must not become the one a run depends on."""
        unconfigured = Fake("unconfigured", [TIKTOK], ready=False)
        working = Fake("working", [TIKTOK], media="https://cdn/b.mp4")
        await ProviderRouter([unconfigured, working]).resolve(
            "https://www.tiktok.com/@a/video/1"
        )
        assert unconfigured.asked == []

    def test_a_provider_that_does_not_serve_the_platform_is_not_offered(self):
        youtube_only = Fake("youtube_only", [YOUTUBE], media="x")
        router = ProviderRouter([youtube_only])
        assert router.for_url("https://www.tiktok.com/@a/video/1") == []
        assert router.for_url("https://youtu.be/abc") == [youtube_only]


class TestWhatItSaysWhenNobodyCan:
    @pytest.mark.asyncio
    async def test_every_attempt_is_named(self):
        """A single "download failed" is what hid the real cause."""
        router = ProviderRouter(
            [
                Fake("alpha", [TIKTOK], fail="rate limited"),
                Fake("beta", [TIKTOK], fail="no media URL"),
            ]
        )
        with pytest.raises(ProviderError) as caught:
            await router.resolve("https://www.tiktok.com/@a/video/1")
        message = str(caught.value)
        assert "alpha: rate limited" in message
        assert "beta: no media URL" in message

    @pytest.mark.asyncio
    async def test_no_provider_for_the_platform_says_what_is_configured(self):
        router = ProviderRouter([Fake("apify", [YOUTUBE], media="x")])
        with pytest.raises(ProviderError, match="no configured download provider"):
            await router.resolve("https://www.instagram.com/reel/abc/")

    @pytest.mark.asyncio
    async def test_missing_credentials_are_an_absence_not_a_refusal(self):
        assert issubclass(NotConfiguredError, ProviderError)


class TestReadingAScraperResult:
    def test_a_list_of_media_urls(self):
        assert _first_media_url({"mediaUrls": ["https://cdn/a.mp4"]}) == "https://cdn/a.mp4"

    def test_a_single_video_url(self):
        assert _first_media_url({"videoUrl": "https://cdn/b.mp4"}) == "https://cdn/b.mp4"

    def test_a_url_nested_under_media(self):
        item = {"media": [{"videoUrl": "https://cdn/c.mp4"}]}
        assert _first_media_url(item) == "https://cdn/c.mp4"

    def test_an_empty_media_list_is_not_a_url(self):
        """The TikTok actor returns `mediaUrls: []` unless asked to download,
        and treating that as a URL is what an empty download looks like."""
        assert _first_media_url({"mediaUrls": []}) == ""

    def test_a_non_http_value_is_refused(self):
        assert _first_media_url({"videoUrl": "/relative/path.mp4"}) == ""

    def test_duration_and_id_come_out_in_the_probe_shape(self):
        info = _info_from(
            {"id": "123", "videoMeta": {"duration": 142, "width": 576, "height": 1024}}
        )
        assert info["id"] == "123"
        assert info["duration"] == 142
        assert (info["width"], info["height"]) == (576, 1024)

    def test_an_uploader_can_be_a_nested_author(self):
        assert _info_from({"authorMeta": {"name": "foodporn"}})["uploader"] == "foodporn"

    def test_nothing_usable_is_an_empty_dict_not_a_guess(self):
        assert _info_from({"unrelated": "value"}) == {}
