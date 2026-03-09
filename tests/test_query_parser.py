"""Tests for query parser normalization guards."""

from __future__ import annotations

import pytest

from video_searching_agent.router.query_parser import QueryParser


class StubGemini:
    """Minimal Gemini stub for parser tests."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0

    def convert_messages_to_gemini(self, messages):  # noqa: ANN001
        return messages

    async def create_message_async(self, messages, max_tokens=1024):  # noqa: ANN001
        del messages, max_tokens
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return {"text": response}

    def get_text_response(self, response):  # noqa: ANN001
        return response.get("text")


@pytest.mark.asyncio
async def test_parse_discovery_query_never_enables_deep_analysis():
    """Discovery prompts should deterministically keep deep analysis off."""
    responses = [
        '{"query_type":"industry_topic","needs_video_analysis":true,"time_frame":"past_year"}',
        '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_year"}',
    ]
    parser = QueryParser(gemini_client=StubGemini(responses))

    query = "find me the top ai b2b saas ugc videos"
    results = [await parser.parse(query) for _ in range(8)]

    assert all(not parsed.needs_video_analysis for parsed in results)


@pytest.mark.asyncio
async def test_parse_explicit_video_analysis_with_url_enables_analysis():
    """Explicit transcript intent + URL should force deep analysis true."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("transcribe this video https://youtube.com/shorts/abc123")
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://youtube.com/shorts/abc123"]


@pytest.mark.asyncio
async def test_parse_explicit_video_analysis_with_bare_url_enables_analysis():
    """Bare supported video URLs should be recognized as explicit references."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("transcribe this video youtube.com/watch?v=abc123")
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://youtube.com/watch?v=abc123"]


@pytest.mark.asyncio
async def test_parse_explicit_transcript_request_with_url_enables_analysis():
    """Transcript + key points language with a URL should trigger deep analysis."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse(
        "analyze transcript and key points for this video: "
        "https://www.youtube.com/watch?v=0eD62hbXyZc"
    )
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://www.youtube.com/watch?v=0eD62hbXyZc"]


@pytest.mark.asyncio
async def test_parse_direct_video_file_url_enables_analysis():
    """Direct video file URLs should be treated as supported video references."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("analyze this video https://example.com/video.mp4")
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://example.com/video.mp4"]


@pytest.mark.asyncio
async def test_parse_tiktok_vm_share_url_enables_analysis():
    """TikTok vm share links should be treated as supported video URLs."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("transcribe this video https://vm.tiktok.com/ZM123abc/")
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://vm.tiktok.com/ZM123abc/"]


@pytest.mark.asyncio
async def test_parse_tiktok_t_share_url_enables_analysis():
    """TikTok /t/ share links should be treated as supported video URLs."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse(
        "transcribe this video https://www.tiktok.com/t/ZMabcde/"
    )
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://www.tiktok.com/t/ZMabcde/"]


@pytest.mark.asyncio
async def test_parse_what_does_this_video_say_with_url_enables_analysis():
    """Natural language video-transcript asks should stay in analysis mode."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"video_analysis","needs_video_analysis":true,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse(
        "what does this video say? https://www.youtube.com/watch?v=abc123"
    )
    assert parsed.needs_video_analysis is True
    assert parsed.video_urls == ["https://www.youtube.com/watch?v=abc123"]


@pytest.mark.asyncio
async def test_parse_explicit_video_analysis_with_pronoun_enables_analysis():
    """Pronoun-based explicit analysis without URL should still enable deep analysis."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"general","needs_video_analysis":false,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("analyze this video and summarize the key moments")
    assert parsed.needs_video_analysis is True


@pytest.mark.asyncio
async def test_parse_url_without_analysis_intent_keeps_analysis_disabled():
    """A URL alone should not imply deep analysis when analysis intent is absent."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"video_analysis","needs_video_analysis":true,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("find similar videos to https://youtube.com/watch?v=abc123")
    assert parsed.needs_video_analysis is False
    assert parsed.video_urls == ["https://youtube.com/watch?v=abc123"]


@pytest.mark.asyncio
async def test_parse_non_video_url_with_analysis_words_disables_analysis():
    """Analysis wording with unsupported links must not enable deep video analysis."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"video_analysis","needs_video_analysis":true,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("summarize this article https://medium.com/some-post")
    assert parsed.needs_video_analysis is False
    assert parsed.video_urls == []
    assert parsed.query_type.value == "general"


@pytest.mark.asyncio
async def test_parse_bare_non_video_url_with_analysis_words_disables_analysis():
    """Bare non-video links should not trigger deep video analysis."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"video_analysis","needs_video_analysis":true,"time_frame":"past_week"}'
        ])
    )

    parsed = await parser.parse("summarize this article medium.com/some-post")
    assert parsed.needs_video_analysis is False
    assert parsed.video_urls == []
    assert parsed.query_type.value == "general"


@pytest.mark.asyncio
async def test_parse_non_specific_video_analysis_query_downgrades_query_type():
    """Video-analysis classification without specific video reference should be downgraded."""
    parser = QueryParser(
        gemini_client=StubGemini([
            '{"query_type":"video_analysis","needs_video_analysis":true,"time_frame":"past_year"}'
        ])
    )

    parsed = await parser.parse("analyze ai b2b saas ugc trends")
    assert parsed.needs_video_analysis is False
    assert parsed.query_type.value == "general"
