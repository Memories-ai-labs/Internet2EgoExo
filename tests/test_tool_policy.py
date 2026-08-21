"""Tests for deterministic tool-call policy."""

from video_searching_agent.agent.tool_policy import (
    apply_tool_call_policy,
    build_video_search_input,
    is_discovery_query,
    may_analyze_video_content,
    wants_video_content_analysis,
)
from video_searching_agent.models.query import MetricType, ParsedQuery, QueryType


def test_apply_tool_call_policy_forces_video_search_first_step_for_discovery():
    parsed = ParsedQuery(
        original_query="find me top ai videos",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
    )
    tool_calls = [
        {"name": "youtube_search", "input": {"query": "ai videos"}},
        {"name": "tiktok_search", "input": {"query": "ai videos"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert forced is True
    assert blocked == []
    assert len(filtered) == 1
    assert filtered[0]["name"] == "video_search"


def test_apply_tool_call_policy_blocks_paid_indexing_without_a_target_video():
    """Indexing is billed per video-minute, so a broad query may not trigger it."""
    parsed = ParsedQuery(
        original_query="find me top ai videos",
        query_type=QueryType.INDUSTRY_TOPIC,
        needs_video_analysis=False,
    )
    tool_calls = [
        {"name": "video_analysis", "input": {"video_url": "https://example.com/a.mp4"}},
        {"name": "video_index", "input": {"video_url": "https://example.com/b.mp4"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert sorted(blocked) == ["video_analysis", "video_index"]
    assert forced is True
    assert [call["name"] for call in filtered] == ["video_search"]


def test_apply_tool_call_policy_allows_indexing_when_a_video_url_is_given():
    parsed = ParsedQuery(
        original_query="add this to the library https://example.com/clip.mp4",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
        video_urls=["https://example.com/clip.mp4"],
    )
    tool_calls = [
        {"name": "video_index", "input": {"video_url": "https://example.com/clip.mp4"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert blocked == []
    assert forced is False
    assert [call["name"] for call in filtered] == ["video_index"]


def test_apply_tool_call_policy_keeps_existing_video_search_first_step():
    parsed = ParsedQuery(
        original_query="find me top ai videos",
        query_type=QueryType.INDUSTRY_TOPIC,
        needs_video_analysis=False,
    )
    tool_calls = [
        {"name": "video_search", "input": {"query": "ai videos"}},
        {"name": "youtube_search", "input": {"query": "ai videos"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert forced is False
    assert len(filtered) == 1
    assert filtered[0]["name"] == "video_search"


def test_apply_tool_call_policy_does_not_force_video_search_after_step_zero():
    parsed = ParsedQuery(
        original_query="find top ai videos",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
    )
    tool_calls = [
        {"name": "youtube_search", "input": {"query": "ai videos"}},
        {"name": "tiktok_search", "input": {"query": "ai videos"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=1,
    )

    assert forced is False
    assert [call["name"] for call in filtered] == ["youtube_search", "tiktok_search"]


def test_apply_tool_call_policy_preserves_unknown_tool_plans():
    parsed = ParsedQuery(
        original_query="parallel tools",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
    )
    tool_calls = [
        {"name": "tool_a", "input": {"q": "a"}},
        {"name": "tool_b", "input": {"q": "b"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert forced is False
    assert [call["name"] for call in filtered] == ["tool_a", "tool_b"]


def test_apply_tool_call_policy_keeps_video_analysis_for_explicit_analysis():
    """A video-analysis query is not a discovery query, so nothing is rewritten."""
    parsed = ParsedQuery(
        original_query="what does this video say? https://example.com/clip.mp4",
        query_type=QueryType.VIDEO_ANALYSIS,
        needs_video_analysis=True,
        video_urls=["https://example.com/clip.mp4"],
    )
    tool_calls = [
        {"name": "video_analysis", "input": {"video_url": "https://example.com/clip.mp4"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert forced is False
    assert [call["name"] for call in filtered] == ["video_analysis"]


def test_apply_tool_call_policy_preserves_youtube_search_for_url_targeted_query():
    parsed = ParsedQuery(
        original_query="how many views does this video have? https://www.youtube.com/watch?v=abc123",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
        video_urls=["https://www.youtube.com/watch?v=abc123"],
    )
    tool_calls = [
        {
            "name": "youtube_search",
            "input": {"query": "https://www.youtube.com/watch?v=abc123"},
        }
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert forced is False
    assert [call["name"] for call in filtered] == ["youtube_search"]


def test_wants_video_content_analysis_flags_explicit_intent():
    explicit = ParsedQuery(
        original_query="transcribe this video",
        query_type=QueryType.VIDEO_ANALYSIS,
        needs_video_analysis=False,
    )
    flagged = ParsedQuery(
        original_query="what happens in this clip",
        query_type=QueryType.GENERAL,
        needs_video_analysis=True,
    )
    discovery = ParsedQuery(
        original_query="top ai videos",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
    )

    assert wants_video_content_analysis(explicit) is True
    assert wants_video_content_analysis(flagged) is True
    assert wants_video_content_analysis(discovery) is False
    assert is_discovery_query(discovery) is True
    assert is_discovery_query(flagged) is False

    # A named video URL is enough to permit paid content analysis.
    with_url = ParsedQuery(
        original_query="index https://example.com/clip.mp4",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
        video_urls=["https://example.com/clip.mp4"],
    )
    assert may_analyze_video_content(with_url) is True
    assert may_analyze_video_content(discovery) is False


def test_build_video_search_input_maps_metric_to_sort():
    parsed = ParsedQuery(
        original_query="latest ai videos",
        query_type=QueryType.GENERAL,
        metric=MetricType.MOST_RECENT,
        quantity=100,
    )

    tool_input = build_video_search_input(parsed.original_query, parsed)

    assert tool_input["sort_by"] == "recent"
    assert tool_input["max_results"] == 50
