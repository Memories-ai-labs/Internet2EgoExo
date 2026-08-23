"""Core video searching agent implementation."""

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from video_searching_agent.agent.clarification import ClarificationManager
from video_searching_agent.agent.prompts import build_system_prompt
from video_searching_agent.agent.tool_policy import apply_tool_call_policy
from video_searching_agent.api.llm import get_llm_client
from video_searching_agent.config.pricing import get_pricing
from video_searching_agent.config.settings import get_settings
from video_searching_agent.curation.manifest import (
    curate_references,
    verify_viewpoints,
)
from video_searching_agent.models.cost import (
    GeminiCost,
    TokenUsage,
    ToolUsageCost,
    UsageMetrics,
)
from video_searching_agent.models.query import (
    AgentSession,
    MetricType,
    ParsedQuery,
    TimeFrame,
)
from video_searching_agent.models.result import AgentResponse, VideoReference
from video_searching_agent.router.query_parser import QueryParser
from video_searching_agent.tools.base import BaseTool, ToolResult
from video_searching_agent.tools.exa import (
    ExaContentTool,
    ExaResearchTool,
    ExaSearchTool,
    ExaSimilarTool,
)
from video_searching_agent.tools.instagram_apify import (
    InstagramApifyCreatorTool,
    InstagramApifySearchTool,
)
from video_searching_agent.tools.memories_datalake import (
    VideoAnalysisTool,
    VideoIndexTool,
    VideoMomentSearchTool,
)
from video_searching_agent.tools.registry import ToolRegistry
from video_searching_agent.tools.retry import RetryExecutor, get_fallback_tools
from video_searching_agent.tools.tiktok_apify import (
    TikTokApifyCreatorTool,
    TikTokApifySearchTool,
)
from video_searching_agent.tools.twitter_apify import (
    TwitterApifyProfileTool,
    TwitterApifySearchTool,
)
from video_searching_agent.tools.video_search import VideoSearchTool
from video_searching_agent.tools.youtube import YouTubeChannelTool, YouTubeSearchTool

logger = logging.getLogger(__name__)

# Told to the model when the tool policy blocks paid video indexing.
POLICY_NOTE = (
    "Policy note: video content analysis is disabled for this query because no "
    "specific video was given. Continue with discovery/search tools."
)


def _coerce_token_count(value: Any, default: int = 0) -> int:
    """Coerce token usage values to integers with safe fallback."""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


class VideoSearchingAgent:
    """Main agent for sourcing and analyzing videos across platforms."""

    def __init__(
        self,
        google_api_key: str | None = None,
        youtube_api_key: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
        enable_retry: bool = True,
    ):
        """Initialize the video searching agent.

        Args:
            google_api_key: Google API key for Gemini. Defaults to env var.
            youtube_api_key: YouTube API key. Defaults to env var.
            max_steps: Maximum agent steps per query. Defaults to settings.
            enable_clarification: Whether to enable clarification flow.
            enable_retry: Whether to enable retry with exponential backoff.
        """
        settings = get_settings()
        self.max_steps = max_steps or settings.max_agent_steps
        self.enable_clarification = enable_clarification
        self.enable_retry = enable_retry
        configured_concurrency = getattr(settings, "tool_execution_concurrency", 4)
        try:
            self.tool_execution_concurrency = max(1, int(configured_concurrency))
        except (TypeError, ValueError):
            self.tool_execution_concurrency = 4

        # Initialize Gemini client
        # Gemini or OpenRouter, decided by configuration. `gemini` is the
        # historical name for it and is kept because the query parser and the
        # tests reach for that attribute.
        self.llm = get_llm_client(google_api_key=google_api_key)
        self.gemini = self.llm

        # Initialize query parser for slot extraction (LLM-first approach)
        self.query_parser = QueryParser(gemini_client=self.gemini)

        # Initialize clarification manager
        self.clarification_manager = ClarificationManager()

        # Initialize retry executor for robust tool execution
        self.retry_executor = RetryExecutor(max_retries=3, backoff_factor=2.0)

        # Initialize tool registry
        self.tools = ToolRegistry()
        self._register_tools(youtube_api_key)

        # Check tool health and log warnings for misconfigured tools
        self.tools.log_health_status()

    def _register_tools(self, youtube_api_key: str | None = None) -> None:
        """Register all available tools.

        Args:
            youtube_api_key: YouTube API key for YouTube tools.
        """
        self.tools.register_all(
            [
                # YouTube API tools
                YouTubeSearchTool(api_key=youtube_api_key),
                YouTubeChannelTool(api_key=youtube_api_key),
                # Exa.ai tools (neural web search)
                ExaSearchTool(),
                ExaSimilarTool(),
                ExaContentTool(),
                ExaResearchTool(),
                # Platform search tools (Apify-based)
                TikTokApifySearchTool(),
                InstagramApifySearchTool(),
                TwitterApifySearchTool(),
                # Creator info tools (Apify-based)
                TikTokApifyCreatorTool(),
                InstagramApifyCreatorTool(),
                TwitterApifyProfileTool(),
                # Video Datalake (index / analyse / search indexed moments)
                VideoIndexTool(),
                VideoAnalysisTool(),
                VideoMomentSearchTool(),
                # Unified video search (Exa discovery + Apify scraping)
                VideoSearchTool(),
            ]
        )

    async def query(self, user_query: str) -> AgentResponse:
        """Process a user query and return video searching results.

        This is the main entry point for using the agent.

        Args:
            user_query: The user's natural language query.

        Returns:
            AgentResponse with answer and video references.
        """
        start_time = time.perf_counter()

        # Parse query to extract slots (LLM-first approach per PRD)
        parse_started_at = time.perf_counter()
        parsed_query = await self.query_parser.parse(user_query)
        parse_duration_ms = int((time.perf_counter() - parse_started_at) * 1000)
        logger.info(
            "agent_parse_complete duration_ms=%d query_length=%d",
            parse_duration_ms,
            len(user_query),
        )

        # Check if clarification is needed
        if self.enable_clarification and self.clarification_manager.needs_clarification(
            parsed_query
        ):
            clarification_response = self.clarification_manager.build_clarification_response(
                parsed_query
            )
            return AgentResponse(
                session_id="",
                query=user_query,
                answer=clarification_response["question"],
                video_references=[],
                needs_clarification=True,
                clarification_question=clarification_response["question"],
                parsed_query=parsed_query,
                execution_time_seconds=round(time.perf_counter() - start_time, 2),
            )

        # Create session with parsed query
        session = AgentSession(
            user_query=user_query,
            parsed_query=parsed_query,
            max_steps=self.max_steps,
        )
        session.start()

        # Build enhanced query with extracted slots for Gemini
        rewrite = await self._rewrite_searches(user_query, parsed_query)
        enhanced_query = self._build_enhanced_query(user_query, parsed_query, rewrite)

        # Initialize messages with enhanced query
        messages: list[Any] = self.llm.new_conversation(enhanced_query)

        # Get tool definitions and convert to Gemini format
        tool_definitions = self.tools.get_tool_definitions()
        gemini_tools = self.gemini.convert_tool_definitions(tool_definitions)
        tools_used: set[str] = set()

        # Cost tracking variables
        total_input_tokens = 0
        total_output_tokens = 0
        gemini_calls = 0
        provider_cost_usd = 0.0
        tool_invocations: dict[str, int] = {}

        # Agentic loop
        while session.current_step < session.max_steps:
            # Call Gemini
            gemini_started_at = time.perf_counter()
            response = await self.gemini.create_message_async(
                messages=messages,
                system=build_system_prompt(),
                tools=gemini_tools,
            )
            gemini_duration_ms = int((time.perf_counter() - gemini_started_at) * 1000)
            logger.info(
                "agent_gemini_call_complete step=%d duration_ms=%d",
                session.current_step + 1,
                gemini_duration_ms,
            )

            # Track token usage
            gemini_calls += 1
            usage = self.gemini.get_usage_metadata(response)
            reported = self.llm.get_cost_usd(response)
            if reported is not None:
                provider_cost_usd += reported
            total_input_tokens += usage["input_tokens"]
            total_output_tokens += usage["output_tokens"]

            # Check if Gemini is done (no tool calls)
            if self.gemini.is_done(response):
                # Extract final answer
                final_answer = self.gemini.get_text_response(response)
                session.complete(final_answer or "No response generated.")
                break

            # Process tool calls
            tool_calls = self.gemini.get_tool_calls(response)
            tool_calls, blocked_tools, forced_video_search = apply_tool_call_policy(
                tool_calls,
                parsed_query=parsed_query,
                user_query=user_query,
                current_step=session.current_step,
            )
            if blocked_tools:
                logger.info(
                    "agent_tool_policy_blocked step=%d blocked=%s",
                    session.current_step + 1,
                    ",".join(blocked_tools),
                )
            if forced_video_search:
                logger.info(
                    "agent_tool_policy_forced_video_search step=%d",
                    session.current_step + 1,
                )

            # Add model response to messages (preserves thought signatures)
            self.llm.append_model_response(messages, response)

            # Execute tools and collect results as function response parts
            tool_result_texts: list[tuple[str, str]] = []
            indexed_tool_calls = [
                (index, call["name"], call["input"]) for index, call in enumerate(tool_calls)
            ]
            for _, tool_name, _ in indexed_tool_calls:
                tools_used.add(tool_name)
                tool_invocations[tool_name] = tool_invocations.get(tool_name, 0) + 1

            if indexed_tool_calls:
                tool_results = await self._execute_tool_calls_in_order(indexed_tool_calls)
                for _, tool_name, tool_input, result in tool_results:
                    # CRITICAL: Filter tool results by time frame BEFORE Gemini sees them
                    # This ensures Gemini's answer only references videos within the time window
                    if (
                        parsed_query
                        and parsed_query.time_frame
                        and parsed_query.time_frame != TimeFrame.ALL_TIME
                    ):
                        result = self._filter_tool_result_by_time(result, parsed_query.time_frame)

                    # Store result in session (now filtered)
                    session.search_results.append(
                        {
                            "tool": tool_name,
                            "input": tool_input,
                            "result": result.data if result.success else result.error,
                            "success": result.success,
                        }
                    )

                    # Format result for Gemini
                    result_str = result.to_string()
                    if not result.success:
                        result_str = f"Error: {result_str}"

                    tool_result_texts.append((tool_name, result_str))
            elif blocked_tools:
                # Steer the model away from paid video indexing on broad queries.
                self.llm.append_user_text(messages, POLICY_NOTE)

            # Add tool results to messages as user turn
            self.llm.append_tool_results(messages, tool_result_texts)

            # Increment step
            if not session.increment_step():
                # Max steps reached
                session.fail("Maximum steps reached without completing the task.")
                break

        # Build response
        execution_time = time.perf_counter() - start_time
        logger.info(
            "agent_query_complete duration_ms=%d steps=%d gemini_calls=%d tool_calls=%d",
            int(execution_time * 1000),
            session.current_step,
            gemini_calls,
            sum(tool_invocations.values()),
        )

        # Calculate usage metrics
        usage_metrics = self._calculate_usage_metrics(
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            gemini_calls=gemini_calls,
            tool_invocations=tool_invocations,
        )

        # Extract video references
        video_references = self._extract_video_references(
            session.search_results, session.parsed_query
        )

        # Apply time frame filter if specified
        if parsed_query and parsed_query.time_frame:
            video_references = self._filter_by_time_frame(video_references, parsed_query.time_frame)

        # Curate: classify viewpoint, drop what fails the requirements, rank by
        # usability and build the manifest.
        video_references, dataset = curate_references(
            video_references,
            parsed_query,
            query=user_query,
            discovery_usd=usage_metrics.total_cost_usd,
        )

        # What the agent was told to search, so the UI can show it.
        if rewrite is not None and getattr(rewrite, "queries", None):
            dataset.searches_run = [q.as_dict() for q in rewrite.queries]

        # The metadata got its say above; now look at the footage, while the
        # candidate list is still just a list. A tripod pointed at a worktop
        # calls itself "POV" often enough that this is the difference between
        # a list worth queueing and one where every pick gets skipped later.
        video_references = await verify_viewpoints(
            video_references,
            dataset,
            wanted=parsed_query.viewpoint if parsed_query else None,
            # The request itself, not the rewritten searches: the searches
            # are how the footage is titled, and the request is what the
            # footage has to show.
            task=user_query,
        )

        return AgentResponse(
            session_id=session.session_id,
            query=user_query,
            answer=session.final_answer or session.error_message or "Unable to process query.",
            video_references=video_references,
            dataset=dataset,
            platforms_searched=self._extract_platforms(session.search_results),
            total_videos_analyzed=self._count_videos(session.search_results),
            steps_taken=session.current_step,
            tools_used=list(tools_used),
            tool_execution_details=session.search_results,
            execution_time_seconds=round(execution_time, 2),
            usage_metrics=usage_metrics,
            parsed_query=parsed_query,
        )

    async def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        """Execute a tool with retry/fallback if enabled."""
        if self.enable_retry:
            tool = self.tools.get(tool_name)
            if tool:
                fallback_names = get_fallback_tools(tool_name)
                fallback_tools: list[BaseTool] = [
                    t
                    for t in (
                        self.tools.get(name) for name in fallback_names if self.tools.has(name)
                    )
                    if t is not None
                ]

                if fallback_tools:
                    return await self.retry_executor.execute_with_fallback(
                        tool, fallback_tools, **tool_input
                    )
                return await self.retry_executor.execute_with_retry(tool, **tool_input)

            return await self.tools.execute(tool_name, **tool_input)

        return await self.tools.execute(tool_name, **tool_input)

    async def _execute_tool_call(
        self,
        index: int,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> tuple[int, str, dict[str, Any], ToolResult]:
        """Execute a single tool call and return result with original index."""
        tool_started_at = time.perf_counter()
        result = await self._execute_tool(tool_name, tool_input)
        tool_duration_ms = int((time.perf_counter() - tool_started_at) * 1000)
        logger.info(
            "agent_tool_execution_complete tool=%s duration_ms=%d success=%s",
            tool_name,
            tool_duration_ms,
            result.success,
        )
        return index, tool_name, tool_input, result

    async def _execute_tool_calls_in_order(
        self,
        indexed_tool_calls: list[tuple[int, str, dict[str, Any]]],
    ) -> list[tuple[int, str, dict[str, Any], ToolResult]]:
        """Run tool calls concurrently (bounded) and return in call index order."""
        if not indexed_tool_calls:
            return []
        if len(indexed_tool_calls) == 1:
            return [await self._execute_tool_call(*indexed_tool_calls[0])]

        semaphore = asyncio.Semaphore(self.tool_execution_concurrency)

        async def _execute_bounded(
            tool_call: tuple[int, str, dict[str, Any]],
        ) -> tuple[int, str, dict[str, Any], ToolResult]:
            async with semaphore:
                return await self._execute_tool_call(*tool_call)

        tasks = [
            asyncio.create_task(_execute_bounded(tool_call)) for tool_call in indexed_tool_calls
        ]
        ordered_results: list[tuple[int, str, dict[str, Any], ToolResult]] = []
        try:
            for task in tasks:
                ordered_results.append(await task)
            return ordered_results
        except BaseException:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    async def _rewrite_searches(self, user_query: str, parsed_query: ParsedQuery) -> Any:
        """Turn the request into searches that find footage rather than lessons.

        A request describes a task; the footage that shows it is titled by
        whoever recorded it, in different words. Measured on real YouTube
        results judged by their frames: a plain search for "packing a suitcase,
        folding and placing clothes into luggage" returned 0 of 6 first-person
        videos, and the rewritten searches returned 5 of 11. Costs about $0.001.
        """
        from video_searching_agent.curation.query_rewrite import rewrite_query

        try:
            return await rewrite_query(
                user_query,
                viewpoint=parsed_query.viewpoint,
                # `self.gemini`, not `self.llm`: they alias the same object in
                # production, but the loop calls this one and so do the tests
                # that replace it. Using the other reached the real network from
                # a unit test and took it from 0.4s to 4.7.
                llm=self.gemini,
            )
        except Exception as exc:  # noqa: BLE001 - the plain query still works
            logger.info("query rewrite unavailable: %s", exc)
            return None

    def _build_enhanced_query(
        self,
        user_query: str,
        parsed_query: ParsedQuery,
        rewrite: Any | None = None,
    ) -> str:
        """Build enhanced query string with extracted slots for Gemini.

        Args:
            user_query: Original user query.
            parsed_query: Parsed query with extracted slots.
            rewrite: Footage-shaped searches to suggest, when one was made.

        Returns:
            Enhanced query string with slot context.
        """
        parts = [f"User Query: {user_query}"]

        # Add extracted slots context
        slot_context = []

        if parsed_query.platforms:
            slot_context.append(f"Platforms: {', '.join(parsed_query.platforms)}")

        if parsed_query.video_category:
            slot_context.append(f"Category: {parsed_query.video_category}")

        if parsed_query.topics:
            slot_context.append(f"Topics: {', '.join(parsed_query.topics)}")

        if parsed_query.hashtags:
            slot_context.append(f"Hashtags: {', '.join(['#' + h for h in parsed_query.hashtags])}")

        if parsed_query.creators:
            slot_context.append(f"Creators: {', '.join(['@' + c for c in parsed_query.creators])}")

        if parsed_query.metric.value != "most_popular":
            slot_context.append(f"Sort by: {parsed_query.metric.value}")

        if parsed_query.time_frame.value != "past_week":
            slot_context.append(f"Time frame: {parsed_query.time_frame.value}")

        if parsed_query.quantity != 10:
            slot_context.append(f"Results requested: {parsed_query.quantity}")

        if parsed_query.needs_video_analysis:
            slot_context.append("Video analysis needed: YES")

        if slot_context:
            parts.append("\nExtracted Parameters:")
            parts.extend([f"- {ctx}" for ctx in slot_context])

        queries = getattr(rewrite, "queries", None) if rewrite else None
        if queries:
            parts.append(
                "\nSuggested searches. The request's own words select for tutorials "
                "and reviews; these are how the footage is actually titled. Run "
                "several of them and merge the results — one phrasing does not "
                "cover the space:"
            )
            parts.extend(f"- [{q.angle}] {q.text}" for q in queries[:6])

        return "\n".join(parts)

    def _calculate_usage_metrics(
        self,
        total_input_tokens: int,
        total_output_tokens: int,
        gemini_calls: int,
        tool_invocations: dict[str, int],
    ) -> UsageMetrics:
        """Calculate usage metrics and costs for the session.

        Args:
            total_input_tokens: Total input tokens used across all Gemini calls.
            total_output_tokens: Total output tokens used across all Gemini calls.
            gemini_calls: Number of Gemini API calls made.
            tool_invocations: Dict of tool_name -> invocation count.

        Returns:
            UsageMetrics with cost breakdown.
        """
        pricing = get_pricing()

        # Calculate Gemini costs
        input_cost, output_cost, gemini_total = pricing.gemini.calculate_cost(
            total_input_tokens, total_output_tokens
        )

        token_usage = TokenUsage(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
        )

        gemini_cost = GeminiCost(
            token_usage=token_usage,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            total_cost_usd=gemini_total,
        )

        # Calculate tool costs
        tool_costs: list[ToolUsageCost] = []
        for tool_name, count in tool_invocations.items():
            unit_cost = pricing.tools.get_tool_cost(tool_name)
            quota = pricing.tools.get_youtube_quota(tool_name)

            tool_costs.append(
                ToolUsageCost(
                    tool_name=tool_name,
                    invocation_count=count,
                    estimated_cost_usd=unit_cost * count,
                    quota_used=quota * count if quota > 0 else None,
                )
            )

        # Build usage metrics
        usage_metrics = UsageMetrics(
            gemini=gemini_cost,
            tool_costs=tool_costs,
            gemini_calls=gemini_calls,
            tool_calls=sum(tool_invocations.values()),
        )
        usage_metrics.calculate_total()

        return usage_metrics

    def _extract_video_references(
        self, search_results: list[dict[str, Any]], parsed_query: ParsedQuery | None = None
    ) -> list[VideoReference]:
        """Extract video references from search results.

        Args:
            search_results: List of search result dicts.
            parsed_query: Parsed query with metric for sorting.

        Returns:
            List of VideoReference objects.
        """
        references: list[VideoReference] = []
        seen_urls: set[str] = set()
        failed_searches: list[tuple[str, str]] = []  # (tool_name, error)

        for result in search_results:
            if not result.get("success"):
                tool_name = result.get("tool", "unknown")
                error = result.get("result", "Unknown error")
                failed_searches.append((tool_name, str(error)))
                continue

        # Log warning if searches failed
        if failed_searches:
            failed_summary = ", ".join([f"{name}: {err[:50]}..." for name, err in failed_searches])
            logger.warning(
                f"{len(failed_searches)} search(es) failed during "
                f"video extraction: {failed_summary}"
            )

        for result in search_results:
            if not result.get("success"):
                continue

            data = result.get("result", {})
            if not isinstance(data, dict):
                continue

            # Handle YouTube search results
            videos = data.get("videos", [])
            for video in videos:
                if isinstance(video, dict):
                    url = video.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        creator_data = video.get("creator")
                        creator_name = (
                            creator_data.get("username") if isinstance(creator_data, dict) else None
                        )
                        metrics_data = video.get("metrics")
                        views = (
                            metrics_data.get("views") if isinstance(metrics_data, dict) else None
                        )
                        likes = (
                            metrics_data.get("likes") if isinstance(metrics_data, dict) else None
                        )
                        # Extract published_at - handle both string and datetime formats
                        published_at = video.get("published_at")
                        if published_at is not None and not isinstance(published_at, str):
                            # Convert datetime to string if needed
                            published_at = str(published_at)
                        duration_seconds = video.get("duration_seconds")
                        references.append(
                            VideoReference(
                                video_id=str(video.get("id") or video.get("platform_id") or ""),
                                url=url,
                                title=video.get("title"),
                                platform=video.get("platform", "youtube"),
                                creator=creator_name,
                                thumbnail_url=video.get("thumbnail_url"),
                                views=views,
                                likes=likes,
                                duration_seconds=(
                                    int(duration_seconds)
                                    if isinstance(duration_seconds, int | float)
                                    else None
                                ),
                                license=video.get("license"),
                                published_at=published_at,
                            )
                        )

        # Sort by metric from parsed query before limiting
        if parsed_query and parsed_query.metric:
            references = self._sort_references_by_metric(references, parsed_query.metric)

        return references[:20]  # Limit to 20 references

    def _sort_references_by_metric(
        self, references: list[VideoReference], metric: MetricType
    ) -> list[VideoReference]:
        """Sort video references by the specified metric.

        Args:
            references: List of video references.
            metric: Metric type from parsed query.

        Returns:
            Sorted list of video references.
        """
        if metric in (MetricType.MOST_POPULAR, MetricType.FASTEST_GROWTH_VIEWS):
            return sorted(references, key=lambda r: r.views or 0, reverse=True)
        elif metric == MetricType.MOST_LIKED:
            return sorted(references, key=lambda r: r.likes or 0, reverse=True)
        # Default: keep original order
        return references

    def _filter_by_time_frame(
        self,
        video_references: list[VideoReference],
        time_frame: TimeFrame,
    ) -> list[VideoReference]:
        """Filter video references to only include those within the time frame.

        This is a post-filtering step that removes videos outside the requested
        time window. It handles cases where APIs don't support date filtering
        or return stale data.

        Args:
            video_references: List of video references to filter.
            time_frame: Time frame constraint from parsed query.

        Returns:
            Filtered list of video references within the time frame.
        """
        from datetime import datetime

        from video_searching_agent.utils import get_cutoff_datetime

        # Get cutoff datetime
        cutoff = get_cutoff_datetime(time_frame)
        if cutoff is None:  # all_time - no filtering needed
            return video_references

        original_count = len(video_references)
        filtered: list[VideoReference] = []

        for ref in video_references:
            if not ref.published_at:
                # If no publish date, include the video (benefit of the doubt)
                filtered.append(ref)
                continue

            # Parse the published_at string to datetime
            try:
                # Handle various date formats
                pub_date_str = ref.published_at
                pub_date: datetime | None = None

                # Try ISO 8601 format first
                if "T" in pub_date_str:
                    pub_date_str = pub_date_str.replace("Z", "+00:00")
                    pub_date = datetime.fromisoformat(pub_date_str)
                else:
                    # Try simple date format (YYYY-MM-DD)
                    pub_date = datetime.strptime(pub_date_str[:10], "%Y-%m-%d")
                    pub_date = pub_date.replace(tzinfo=UTC)

                # Make sure cutoff is timezone-aware for comparison
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=UTC)

                # Include if published after cutoff
                if pub_date >= cutoff:
                    filtered.append(ref)

            except (ValueError, TypeError) as e:
                # If we can't parse the date, include the video
                logger.debug(f"Could not parse date '{ref.published_at}': {e}")
                filtered.append(ref)

        if len(filtered) < original_count:
            logger.info(
                f"Time filter: kept {len(filtered)}/{original_count} videos "
                f"(cutoff: {cutoff.isoformat()}, time_frame: {time_frame.value})"
            )

        return filtered

    def _filter_tool_result_by_time(
        self,
        result: ToolResult,
        time_frame: TimeFrame,
    ) -> ToolResult:
        """Filter videos in tool result to only include those within time frame.

        This ensures Gemini only sees relevant videos when generating its answer.
        This is called INSIDE the agentic loop, before sending results back to Gemini.

        Args:
            result: Tool execution result.
            time_frame: Time frame constraint from parsed query.

        Returns:
            New ToolResult with filtered videos (or original if no filtering needed).
        """
        if not result.success or not result.data:
            return result

        data = result.data
        if not isinstance(data, dict) or "videos" not in data:
            return result

        from video_searching_agent.utils import get_cutoff_datetime

        cutoff = get_cutoff_datetime(time_frame)
        if cutoff is None:  # all_time - no filtering needed
            return result

        videos = data.get("videos", [])
        original_count = len(videos)

        filtered_videos = []
        for video in videos:
            published_at = video.get("published_at")
            if not published_at:
                # Skip videos without dates when time filtering is active
                continue

            try:
                # Parse the date string
                if isinstance(published_at, str):
                    if "T" in published_at:
                        pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    else:
                        pub_date = datetime.strptime(published_at[:10], "%Y-%m-%d")
                        pub_date = pub_date.replace(tzinfo=UTC)

                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=UTC)

                    if pub_date >= cutoff:
                        filtered_videos.append(video)
            except (ValueError, TypeError):
                # Skip unparseable dates when time filtering is active
                continue

        if len(filtered_videos) < original_count:
            logger.info(
                f"Time filter on tool result: kept {len(filtered_videos)}/{original_count} "
                f"videos (cutoff: {cutoff.isoformat()})"
            )

        # Return new ToolResult with filtered videos
        filtered_data = {**data, "videos": filtered_videos, "total_results": len(filtered_videos)}
        return ToolResult.ok(filtered_data)

    def _extract_platforms(self, search_results: list[dict[str, Any]]) -> list[str]:
        """Extract platforms searched from results.

        Args:
            search_results: List of search result dicts.

        Returns:
            List of platform names.
        """
        platforms: set[str] = set()
        for result in search_results:
            tool = result.get("tool", "")
            if "youtube" in tool:
                platforms.add("youtube")
            elif "tiktok" in tool:
                platforms.add("tiktok")
            elif "instagram" in tool:
                platforms.add("instagram")
            elif "twitter" in tool:
                platforms.add("twitter")
            elif "exa" in tool:
                platforms.add("web")
        return list(platforms)

    def _count_videos(self, search_results: list[dict[str, Any]]) -> int:
        """Count total videos found in search results.

        Args:
            search_results: List of search result dicts.

        Returns:
            Total video count.
        """
        count = 0
        for result in search_results:
            if not result.get("success"):
                continue
            data = result.get("result", {})
            if isinstance(data, dict):
                count += len(data.get("videos", []))
                count += data.get("total_results", 0)
        return count

    async def find_trending(
        self,
        topic: str,
        platform: str = "youtube",
    ) -> AgentResponse:
        """Find trending videos on a topic.

        Convenience method for trend discovery.

        Args:
            topic: Topic or niche to search.
            platform: Platform to search on.

        Returns:
            AgentResponse with trending videos.
        """
        query = f"""Find the most trending and viral {topic} videos on {platform}.

Look for:
1. Recent videos with high engagement
2. Videos that are gaining views quickly
3. Common themes and patterns in successful content
4. Top creators in this space

Provide specific video examples with metrics."""

        return await self.query(query)

    async def analyze_creator(self, username: str, platform: str = "youtube") -> AgentResponse:
        """Analyze a content creator's profile and content.

        Convenience method for creator analysis.

        Args:
            username: Creator's username/handle.
            platform: Platform the creator is on.

        Returns:
            AgentResponse with creator analysis.
        """
        query = f"""Analyze the content creator @{username} on {platform}.

Provide:
1. What type of creator they are (niche, content focus)
2. Their follower/subscriber count and growth
3. Average video performance (views, engagement)
4. Content themes and posting patterns
5. Top performing videos
6. Their unique style or approach"""

        return await self.query(query)

    async def compare(self, entities: list[str], platform: str = "youtube") -> AgentResponse:
        """Compare multiple brands, creators, or products.

        Convenience method for comparisons.

        Args:
            entities: List of entities to compare.
            platform: Platform to compare on.

        Returns:
            AgentResponse with comparison.
        """
        entities_str = " vs ".join(entities)
        query = f"""Compare {entities_str} on {platform}.

For each, analyze:
1. Content volume and posting frequency
2. Engagement metrics (views, likes, comments)
3. Content style and themes
4. Top performing content
5. Overall presence and performance

Provide a side-by-side comparison with clear winner indicators."""

        return await self.query(query)
