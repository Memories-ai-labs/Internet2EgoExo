"""Tests for deterministic tool-call policy."""

from video_searching_agent.agent.tool_policy import (
    apply_tool_call_policy,
    build_video_search_input,
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
        {"name": "social_media_mai_transcript", "input": {"video_url": "https://x.com/a"}},
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert forced is True
    assert blocked == ["social_media_mai_transcript"]
    assert len(filtered) == 1
    assert filtered[0]["name"] == "video_search"


def test_apply_tool_call_policy_forces_video_search_when_only_deep_tools_requested():
    parsed = ParsedQuery(
        original_query="find top ai videos",
        query_type=QueryType.INDUSTRY_TOPIC,
        needs_video_analysis=False,
    )
    tool_calls = [
        {
            "name": "social_media_mai_transcript",
            "input": {"video_url": "https://instagram.com/reel/abc"},
        },
        {
            "name": "social_media_transcript",
            "input": {"video_url": "https://instagram.com/reel/abc"},
        },
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert sorted(blocked) == ["social_media_mai_transcript", "social_media_transcript"]
    assert forced is True
    assert [call["name"] for call in filtered] == ["video_search"]


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

    assert blocked == []
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

    assert blocked == []
    assert forced is False
    assert [call["name"] for call in filtered] == ["youtube_search", "tiktok_search"]


def test_apply_tool_call_policy_allows_deep_tools_for_explicit_analysis():
    parsed = ParsedQuery(
        original_query="transcribe this video https://instagram.com/reel/abc",
        query_type=QueryType.VIDEO_ANALYSIS,
        needs_video_analysis=True,
    )
    tool_calls = [
        {
            "name": "social_media_mai_transcript",
            "input": {"video_url": "https://instagram.com/reel/abc"},
        }
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert blocked == []
    assert forced is False
    assert filtered[0]["name"] == "social_media_mai_transcript"


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

    assert blocked == []
    assert forced is False
    assert [call["name"] for call in filtered] == ["tool_a", "tool_b"]


def test_apply_tool_call_policy_allows_metadata_for_url_specific_non_analysis_query():
    parsed = ParsedQuery(
        original_query="how many views does this video have? https://www.youtube.com/watch?v=abc123",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
    )
    tool_calls = [
        {
            "name": "social_media_metadata",
            "input": {"video_url": "https://www.youtube.com/watch?v=abc123"},
        }
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert blocked == []
    assert forced is False
    assert [call["name"] for call in filtered] == ["social_media_metadata"]


def test_apply_tool_call_policy_video_urls_without_analysis_intent_still_blocks_deep_tools():
    parsed = ParsedQuery(
        original_query="https://www.youtube.com/watch?v=abc123",
        query_type=QueryType.GENERAL,
        needs_video_analysis=False,
        video_urls=["https://www.youtube.com/watch?v=abc123"],
    )
    tool_calls = [
        {
            "name": "social_media_transcript",
            "input": {"video_url": "https://www.youtube.com/watch?v=abc123"},
        }
    ]

    filtered, blocked, forced = apply_tool_call_policy(
        tool_calls,
        parsed_query=parsed,
        user_query=parsed.original_query,
        current_step=0,
    )

    assert blocked == ["social_media_transcript"]
    assert forced is False
    assert filtered == []


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

    assert blocked == []
    assert forced is False
    assert [call["name"] for call in filtered] == ["youtube_search"]


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
