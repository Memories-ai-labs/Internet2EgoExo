"""Looking at the footage before paying to download it.

The screening step used to read only words *about* a video, which is how a run
came back with clips that were licence clear and completely off topic. This is
the layer that looks at pixels, and these tests pin the two things that make it
safe to run on every candidate: it abstains rather than guesses, and an
abstention never throws footage away.
"""

from __future__ import annotations

import pytest

from video_searching_agent.curation.frame_viewpoint import (
    SightVerdict,
    check_many,
    check_viewpoint,
    frame_urls,
    look_at_frames,
)
from video_searching_agent.curation.viewpoint import Viewpoint


class _FakeClient:
    """An LLM client that answers with whatever text it was given."""

    def __init__(self, text: str, cost: float | None = 0.002) -> None:
        self.text = text
        self.cost = cost
        self.calls: list[dict] = []

    def new_visual_conversation(self, prompt: str, images: list[bytes]) -> list[dict]:
        self.calls.append({"prompt": prompt, "images": len(images)})
        return [{"role": "user", "content": prompt}]

    def new_video_conversation(self, prompt: str, video_url: str) -> list[dict]:
        self.calls.append({"prompt": prompt, "video": video_url})
        return [{"role": "user", "content": prompt}]

    async def create_message_async(self, messages: list[dict], **_: object) -> dict:
        return {"text": self.text}

    def get_text_response(self, response: dict) -> str:
        return response["text"]

    def get_cost_usd(self, response: dict) -> float | None:
        return self.cost


def test_the_frames_asked_for_are_stills_from_inside_the_video_first() -> None:
    """Cover art is chosen to attract a click; a storyboard still is not."""

    urls = frame_urls("abc123")
    assert urls[0].endswith("/abc123/1.jpg")
    assert all("abc123" in url for url in urls)


@pytest.mark.asyncio
async def test_a_fenced_json_answer_is_read() -> None:
    client = _FakeClient(
        '```json\n{"viewpoint": "egocentric", "hands_visible": true, '
        '"confidence": 0.9, "why": "hands enter from the bottom"}\n```'
    )
    verdict = await look_at_frames(client, [b"x" * 3000])
    assert verdict.viewpoint is Viewpoint.EGOCENTRIC
    assert verdict.hands_visible is True
    assert verdict.confidence == pytest.approx(0.9)
    assert verdict.method == "frames"
    assert verdict.frames_seen == 1
    assert verdict.cost_usd == pytest.approx(0.002)


@pytest.mark.asyncio
async def test_an_answer_clipped_by_the_token_limit_still_counts() -> None:
    """The limit is set for cost, so this happens; losing the verdict is worse."""

    client = _FakeClient('{"viewpoint": "exocentric", "confidence": 0.8, "why": "a face is vis')
    verdict = await look_at_frames(client, [b"x" * 3000])
    assert verdict.viewpoint is Viewpoint.EXOCENTRIC
    assert verdict.confidence == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_an_unreadable_answer_decides_nothing() -> None:
    verdict = await look_at_frames(_FakeClient("I could not tell, sorry."), [b"x" * 3000])
    assert verdict.viewpoint is Viewpoint.UNKNOWN
    assert verdict.error
    assert verdict.contradicts(Viewpoint.EGOCENTRIC) is False


@pytest.mark.asyncio
async def test_no_frames_means_no_verdict() -> None:
    verdict = await look_at_frames(_FakeClient("{}"), [])
    assert verdict.looked is False
    assert verdict.error == "no frames could be fetched"


@pytest.mark.parametrize(
    ("seen", "confidence", "wanted", "blocks"),
    [
        (Viewpoint.EXOCENTRIC, 0.95, Viewpoint.EGOCENTRIC, True),
        (Viewpoint.EXOCENTRIC, 0.59, Viewpoint.EGOCENTRIC, False),
        (Viewpoint.UNKNOWN, 1.0, Viewpoint.EGOCENTRIC, False),
        (Viewpoint.EGOCENTRIC, 1.0, Viewpoint.EGOCENTRIC, False),
        (Viewpoint.EXOCENTRIC, 1.0, None, False),
    ],
)
def test_only_a_confident_opposite_reading_rejects_a_candidate(
    seen: Viewpoint, confidence: float, wanted: Viewpoint | None, blocks: bool
) -> None:
    """Three stills are weak evidence; the caption pass gets the last word."""

    verdict = SightVerdict(viewpoint=seen, confidence=confidence, method="frames")
    assert verdict.contradicts(wanted) is blocks


def test_a_verdict_that_never_looked_cannot_reject_anything() -> None:
    assert SightVerdict().looked is False
    assert SightVerdict(method="frames", error="429").looked is False
    assert (
        SightVerdict(
            viewpoint=Viewpoint.EXOCENTRIC, confidence=1.0, method="frames", error="429"
        ).contradicts(Viewpoint.EGOCENTRIC)
        is False
    )


@pytest.mark.asyncio
async def test_the_watch_tier_sends_the_video_rather_than_frames() -> None:
    client = _FakeClient('{"viewpoint": "egocentric", "confidence": 0.99, "why": "worn camera"}')
    verdict = await check_viewpoint(
        client, video_url="https://www.youtube.com/watch?v=abc", mode="watch"
    )
    assert verdict.method == "watch"
    assert client.calls[0]["video"] == "https://www.youtube.com/watch?v=abc"


@pytest.mark.asyncio
async def test_the_check_can_be_turned_off_entirely() -> None:
    client = _FakeClient("{}")
    verdict = await check_viewpoint(client, video_id="abc", mode="off")
    assert verdict.method == "none"
    assert client.calls == []


@pytest.mark.asyncio
async def test_frames_are_only_available_for_youtube() -> None:
    verdict = await check_viewpoint(_FakeClient("{}"), video_id=None, mode="frames")
    assert verdict.error and "YouTube" in verdict.error


@pytest.mark.asyncio
async def test_a_batch_keeps_its_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """A verdict lining up with the wrong candidate would reject good footage."""

    import video_searching_agent.curation.frame_viewpoint as module

    async def fake_fetch(urls: list[str], limit: int = 4) -> list[bytes]:
        return [b"x" * 3000]

    monkeypatch.setattr(module, "fetch_frames", fake_fetch)

    answers = {
        "one": '{"viewpoint": "egocentric", "confidence": 0.9, "why": "a"}',
        "two": '{"viewpoint": "exocentric", "confidence": 0.9, "why": "b"}',
    }

    class Router(_FakeClient):
        def new_visual_conversation(self, prompt: str, images: list[bytes]) -> list[dict]:
            return [{"role": "user", "content": self.text}]

        async def create_message_async(self, messages: list[dict], **_: object) -> dict:
            return {"text": messages[0]["content"]}

    verdicts = []
    for key in ("one", "two"):
        got = await check_many(Router(answers[key]), [{"video_id": key}], mode="frames")
        verdicts.extend(got)
    assert [v.viewpoint for v in verdicts] == [Viewpoint.EGOCENTRIC, Viewpoint.EXOCENTRIC]


@pytest.mark.asyncio
async def test_no_client_means_no_look() -> None:
    verdicts = await check_many(None, [{"video_id": "a"}, {"video_id": "b"}], mode="frames")
    assert [v.method for v in verdicts] == ["none", "none"]
