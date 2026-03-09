"""Deterministic tool-call policy helpers for the video searching agent."""

from __future__ import annotations

from typing import Any

from video_searching_agent.models.query import MetricType, ParsedQuery, QueryType

DEEP_ANALYSIS_TOOLS = frozenset({
    "social_media_transcript",
    "social_media_mai_transcript",
    "vlm_video_analysis",
})

DISCOVERY_QUERY_TYPES = frozenset({
    QueryType.GENERAL,
    QueryType.INDUSTRY_TOPIC,
    QueryType.CREATOR_DISCOVERY,
    QueryType.PRODUCT_SEARCH,
})

DISCOVERY_SEARCH_TOOLS = frozenset({
    "video_search",
    "youtube_search",
    "tiktok_search",
    "instagram_search",
    "twitter_search",
    "exa_search",
    "exa_find_similar",
    "exa_research",
})


def _metric_to_video_search_sort(metric: MetricType) -> str:
    if metric == MetricType.HIGHEST_ENGAGEMENT:
        return "engagement"
    if metric == MetricType.MOST_LIKED:
        return "likes"
    if metric == MetricType.MOST_RECENT:
        return "recent"
    return "views"


def allows_deep_video_analysis(parsed_query: ParsedQuery) -> bool:
    """True when the user explicitly requested video-content analysis."""
    return (
        parsed_query.needs_video_analysis
        or parsed_query.query_type == QueryType.VIDEO_ANALYSIS
    )


def is_discovery_query(parsed_query: ParsedQuery) -> bool:
    """True for broad discovery queries where speed is preferred."""
    return (
        parsed_query.query_type in DISCOVERY_QUERY_TYPES
        and not allows_deep_video_analysis(parsed_query)
        and not parsed_query.is_comparison
        and not parsed_query.creators
        and not parsed_query.video_urls
    )


def build_video_search_input(user_query: str, parsed_query: ParsedQuery) -> dict[str, Any]:
    """Build stable fallback input for Exa-backed `video_search`."""
    max_results = max(1, min(parsed_query.quantity or 10, 50))
    tool_input: dict[str, Any] = {
        "query": user_query,
        "sort_by": _metric_to_video_search_sort(parsed_query.metric),
        "time_frame": parsed_query.time_frame.value,
        "max_results": max_results,
    }
    if parsed_query.platforms:
        tool_input["platforms"] = parsed_query.platforms
    return tool_input


def apply_tool_call_policy(
    tool_calls: list[dict[str, Any]],
    *,
    parsed_query: ParsedQuery,
    user_query: str,
    current_step: int,
) -> tuple[list[dict[str, Any]], list[str], bool]:
    """Apply deterministic tool policy and return filtered calls + metadata.

    Returns:
        tuple(
            filtered_tool_calls,
            blocked_tool_names,
            forced_video_search
        )
    """
    blocked_tools: list[str] = []
    filtered: list[dict[str, Any]] = []
    allow_deep = allows_deep_video_analysis(parsed_query)

    for call in tool_calls:
        tool_name = call.get("name")
        if isinstance(tool_name, str) and tool_name in DEEP_ANALYSIS_TOOLS and not allow_deep:
            blocked_tools.append(tool_name)
            continue
        filtered.append(call)

    forced_video_search = False
    if is_discovery_query(parsed_query) and current_step == 0:
        unknown_tools = [
            call.get("name")
            for call in filtered
            if isinstance(call.get("name"), str)
            and call.get("name") not in DISCOVERY_SEARCH_TOOLS
        ]
        # Keep unknown/custom tool plans untouched.
        if unknown_tools:
            return filtered, blocked_tools, forced_video_search

        video_search_calls = [call for call in filtered if call.get("name") == "video_search"]
        if video_search_calls:
            # First discovery step stays Exa-first.
            filtered = [video_search_calls[0]]
        else:
            filtered = [{
                "name": "video_search",
                "input": build_video_search_input(user_query, parsed_query),
            }]
            forced_video_search = True

    return filtered, blocked_tools, forced_video_search
