"""Streaming wrapper for VideoSearchingAgent that yields SSE events."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from video_searching_agent.agent.clarification import ClarificationManager
from video_searching_agent.agent.prompts import build_system_prompt
from video_searching_agent.agent.tool_policy import apply_tool_call_policy
from video_searching_agent.api.llm import get_llm_client
from video_searching_agent.config.pricing import get_pricing
from video_searching_agent.config.settings import get_settings
from video_searching_agent.curation.manifest import curate_references
from video_searching_agent.curation.viewpoint import Viewpoint
from video_searching_agent.models.cost import (
    GeminiCost,
    TokenUsage,
    ToolUsageCost,
    UsageMetrics,
)
from video_searching_agent.models.query import AgentSession, ParsedQuery, TimeFrame
from video_searching_agent.models.result import AgentResponse, VideoReference
from video_searching_agent.router.query_parser import QueryParser
from video_searching_agent.tools.base import ToolResult
from video_searching_agent.tools.registry import ToolRegistry
from video_searching_agent.tools.retry import RetryExecutor, get_fallback_tools
from video_searching_agent.web.schemas.events import (
    ClarificationEvent,
    CompleteEvent,
    ErrorEvent,
    ProgressEvent,
    SSEEvent,
    StartedEvent,
    ToolCallEvent,
    ToolResultEvent,
)

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


class StreamingAgentWrapper:
    """Wraps VideoSearchingAgent to yield SSE events during execution."""

    def __init__(
        self,
        google_api_key: str | None = None,
        youtube_api_key: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool = True,
        enable_retry: bool = True,
        llm_client: Any | None = None,
    ):
        """Initialize the streaming agent wrapper.

        Args:
            google_api_key: Google API key for Gemini. Defaults to env var.
            youtube_api_key: YouTube API key. Defaults to env var.
            max_steps: Maximum agent steps per query. Defaults to settings.
            enable_clarification: Whether to enable clarification flow.
            enable_retry: Whether to enable retry with exponential backoff.
            llm_client: A model client to use instead of the configured one —
                how a request that brought its own key gets served.
        """
        settings = get_settings()
        self.max_steps = max_steps or settings.max_agent_steps
        self.enable_clarification = enable_clarification
        self.enable_retry = enable_retry
        self.ping_interval = settings.sse_ping_interval
        configured_concurrency = getattr(settings, "tool_execution_concurrency", 4)
        try:
            self.tool_execution_concurrency = max(1, int(configured_concurrency))
        except (TypeError, ValueError):
            self.tool_execution_concurrency = 4

        # Initialize Gemini client
        # Gemini or OpenRouter, decided by configuration. `gemini` is the
        # historical name for it and is kept because the query parser and the
        # tests reach for that attribute.
        self.llm = llm_client or get_llm_client(google_api_key=google_api_key)
        self.gemini = self.llm

        # Initialize query parser for slot extraction
        self.query_parser = QueryParser(gemini_client=self.gemini)

        # Initialize clarification manager
        self.clarification_manager = ClarificationManager()

        # Initialize retry executor
        self.retry_executor = RetryExecutor(max_retries=3, backoff_factor=2.0)

        # Initialize tool registry
        self.tools = ToolRegistry()
        self._register_tools(youtube_api_key)

    def _register_tools(self, youtube_api_key: str | None = None) -> None:
        """Register all available tools."""
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

        # Note: Some tool classes are untyped in the tools module
        self.tools.register_all([
            YouTubeSearchTool(api_key=youtube_api_key),
            YouTubeChannelTool(api_key=youtube_api_key),
            ExaSearchTool(),
            ExaSimilarTool(),
            ExaContentTool(),
            ExaResearchTool(),
            TikTokApifySearchTool(),
            InstagramApifySearchTool(),
            TwitterApifySearchTool(),
            TikTokApifyCreatorTool(),
            InstagramApifyCreatorTool(),
            TwitterApifyProfileTool(),
            VideoIndexTool(),
            VideoAnalysisTool(),
            VideoMomentSearchTool(),
            VideoSearchTool(),
        ])

    async def stream_query(
        self,
        user_query: str,
        clarification: str | None = None,
        max_steps: int | None = None,
        enable_clarification: bool | None = None,
        sources: list[str] | None = None,
        viewpoint: Viewpoint | None = None,
        min_duration_seconds: int | None = None,
        license_filter: str | None = None,
        target_hours: float | None = None,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Process a query and yield SSE events during execution.

        Args:
            user_query: The user's natural language query.
            clarification: Optional clarification response.
            max_steps: Override default max steps.
            enable_clarification: Override default clarification setting.
            sources: Sources the user pinned in the UI. When set, they replace
                the platforms extracted from the query; when empty or None the
                agent auto-selects sources.
            viewpoint: Required camera viewpoint, overriding what the parser
                inferred from the query text.
            min_duration_seconds: Reject clips shorter than this.
            license_filter: "reusable" to keep only licence-clear footage.
            target_hours: Hours of footage this run should try to collect.

        Yields:
            SSE events representing progress, tool calls, and results.
        """
        session_id = str(uuid4())
        start_time = time.perf_counter()
        max_steps = max_steps or self.max_steps
        do_clarification = (
            enable_clarification if enable_clarification is not None else self.enable_clarification
        )

        # If clarification provided, append it to the query
        query = user_query
        if clarification:
            query = f"{user_query}\n\nUser clarification: {clarification}"

        # Emit started event
        yield StartedEvent.create(session_id=session_id, query=user_query)

        try:
            # Parse query
            yield ProgressEvent.create(step=0, max_steps=max_steps, message="Parsing query...")
            parse_started_at = time.perf_counter()
            parsed_query = await self.query_parser.parse(query)
            parse_duration_ms = int((time.perf_counter() - parse_started_at) * 1000)
            logger.info(
                "stream_agent_parse_complete duration_ms=%d session_id=%s",
                parse_duration_ms,
                session_id,
            )

            # Explicit collection requirements win over the parser's guesses.
            if viewpoint:
                parsed_query.viewpoint = viewpoint
                parsed_query.extraction_confidence["viewpoint"] = 1.0
            if min_duration_seconds:
                parsed_query.min_duration_seconds = min_duration_seconds
            if license_filter:
                parsed_query.license_filter = license_filter
            if target_hours:
                parsed_query.target_hours = target_hours

            requirements = self._describe_requirements(parsed_query)
            if requirements:
                yield ProgressEvent.create(
                    step=0,
                    max_steps=max_steps,
                    message=f"Collecting: {requirements}",
                )

            # User-pinned sources win over whatever the parser inferred.
            if sources:
                parsed_query.platforms = list(sources)
                parsed_query.extraction_confidence["platforms"] = 1.0
                yield ProgressEvent.create(
                    step=0,
                    max_steps=max_steps,
                    message=f"Searching pinned sources: {', '.join(sources)}",
                )

            # Check if clarification is needed
            if do_clarification and self.clarification_manager.needs_clarification(parsed_query):
                clarification_response = self.clarification_manager.build_clarification_response(
                    parsed_query
                )
                yield ClarificationEvent.create(
                    question=clarification_response["question"],
                    options=clarification_response.get("options"),
                )
                return

            # Create session
            session = AgentSession(
                session_id=session_id,
                user_query=user_query,
                parsed_query=parsed_query,
                max_steps=max_steps,
            )
            session.start()

            # Build enhanced query
            enhanced_query = self._build_enhanced_query(
                user_query, parsed_query, pinned_sources=bool(sources)
            )

            # Initialize messages
            messages: list[Any] = self.llm.new_conversation(enhanced_query)

            # Get tool definitions
            tool_definitions = self.tools.get_tool_definitions()
            gemini_tools = self.gemini.convert_tool_definitions(tool_definitions)
            tools_used: set[str] = set()

            # Cost tracking
            total_input_tokens = 0
            total_output_tokens = 0
            gemini_calls = 0
            provider_cost_usd = 0.0
            tool_invocations: dict[str, int] = {}

            # Agentic loop
            while session.current_step < session.max_steps:
                yield ProgressEvent.create(
                    step=session.current_step + 1,
                    max_steps=max_steps,
                    message=f"Step {session.current_step + 1}: Consulting AI...",
                )

                # Call Gemini
                gemini_started_at = time.perf_counter()
                response = await self.gemini.create_message_async(
                    messages=messages,
                    system=build_system_prompt(),
                    tools=gemini_tools,
                )
                gemini_duration_ms = int((time.perf_counter() - gemini_started_at) * 1000)
                logger.info(
                    "stream_agent_gemini_call_complete session_id=%s step=%d duration_ms=%d",
                    session_id,
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

                # Check if Gemini is done
                if self.gemini.is_done(response):
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
                        "stream_agent_tool_policy_blocked session_id=%s step=%d blocked=%s",
                        session_id,
                        session.current_step + 1,
                        ",".join(blocked_tools),
                    )
                if forced_video_search:
                    logger.info(
                        "stream_agent_tool_policy_forced_video_search session_id=%s step=%d",
                        session_id,
                        session.current_step + 1,
                    )

                # Add model response to messages
                self.llm.append_model_response(messages, response)

                # Execute tools
                tool_result_texts: list[tuple[str, str]] = []
                indexed_tool_calls = [
                    (index, call["name"], call["input"])
                    for index, call in enumerate(tool_calls)
                ]
                for _, tool_name, tool_input in indexed_tool_calls:
                    tools_used.add(tool_name)
                    tool_invocations[tool_name] = tool_invocations.get(tool_name, 0) + 1
                    yield ToolCallEvent.create(tool=tool_name, input_data=tool_input)

                if indexed_tool_calls:
                    result_iter = self._iter_tool_call_results_in_order(indexed_tool_calls)
                    async for _, tool_name, tool_input, result in result_iter:
                        # Filter by time frame
                        if (
                            parsed_query
                            and parsed_query.time_frame
                            and parsed_query.time_frame != TimeFrame.ALL_TIME
                        ):
                            result = self._filter_tool_result_by_time(
                                result,
                                parsed_query.time_frame,
                            )

                        # Count videos found, plus Datalake-specific detail
                        videos_found = 0
                        moments_found = None
                        tool_status = None
                        if result.success and isinstance(result.data, dict):
                            videos_found = len(result.data.get("videos", []))
                            moments = result.data.get("moments")
                            if isinstance(moments, list):
                                moments_found = len(moments)
                            status = result.data.get("status")
                            if isinstance(status, str):
                                tool_status = status

                        # Emit tool result event
                        yield ToolResultEvent.create(
                            tool=tool_name,
                            success=result.success,
                            videos_found=videos_found if result.success else None,
                            error=result.error if not result.success else None,
                            status=tool_status,
                            moments_found=moments_found,
                        )

                        # Store result in session
                        session.search_results.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "result": result.data if result.success else result.error,
                            "success": result.success,
                        })

                        # Format result for Gemini
                        result_str = result.to_string()
                        if not result.success:
                            result_str = f"Error: {result_str}"

                        tool_result_texts.append((tool_name, result_str))
                elif blocked_tools:
                    # Steer the model away from paid video indexing on broad queries.
                    self.llm.append_user_text(messages, POLICY_NOTE)

                # Add tool results to messages
                self.llm.append_tool_results(messages, tool_result_texts)

                # Increment step
                if not session.increment_step():
                    session.fail("Maximum steps reached without completing the task.")
                    break

            # Build response
            execution_time = time.perf_counter() - start_time
            logger.info(
                "stream_agent_query_complete session_id=%s duration_ms=%d steps=%d gemini_calls=%d "
                "tool_calls=%d",
                session_id,
                int(execution_time * 1000),
                session.current_step,
                gemini_calls,
                sum(tool_invocations.values()),
            )

            usage_metrics = self._calculate_usage_metrics(
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                gemini_calls=gemini_calls,
                tool_invocations=tool_invocations,
            )

            video_references = self._extract_video_references(
                session.search_results, session.parsed_query
            )

            if parsed_query and parsed_query.time_frame:
                video_references = self._filter_by_time_frame(
                    video_references, parsed_query.time_frame
                )

            # Curate: classify viewpoint, drop what fails the requirements,
            # rank by usability and build the manifest.
            video_references, dataset = curate_references(
                video_references,
                parsed_query,
                query=user_query,
                discovery_usd=usage_metrics.total_cost_usd,
            )

            agent_response = AgentResponse(
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
                confidence_score=None,
                data_freshness=None,
                needs_clarification=False,
                clarification_question=None,
            )

            # Emit complete event
            yield CompleteEvent.create(agent_response.model_dump(mode="json"))

        except Exception as e:
            logger.exception(f"Error during query execution: {e}")
            yield ErrorEvent.create(
                code="agent_error",
                message=str(e),
            )

    async def _execute_tool_call(
        self,
        index: int,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> tuple[int, str, dict[str, Any], ToolResult]:
        """Execute one tool call and return it with its original index."""
        tool_started_at = time.perf_counter()
        result = await self._execute_tool(tool_name, tool_input)
        tool_duration_ms = int((time.perf_counter() - tool_started_at) * 1000)
        logger.info(
            "stream_agent_tool_execution_complete tool=%s duration_ms=%d success=%s",
            tool_name,
            tool_duration_ms,
            result.success,
        )
        return index, tool_name, tool_input, result

    async def _iter_tool_call_results_in_order(
        self,
        indexed_tool_calls: list[tuple[int, str, dict[str, Any]]],
    ) -> AsyncGenerator[tuple[int, str, dict[str, Any], ToolResult], None]:
        """Yield tool call results in original order while running work concurrently."""
        if not indexed_tool_calls:
            return
        if len(indexed_tool_calls) == 1:
            yield await self._execute_tool_call(*indexed_tool_calls[0])
            return

        semaphore = asyncio.Semaphore(self.tool_execution_concurrency)

        async def _execute_bounded(
            tool_call: tuple[int, str, dict[str, Any]]
        ) -> tuple[int, str, dict[str, Any], ToolResult]:
            async with semaphore:
                return await self._execute_tool_call(*tool_call)

        tasks = [
            asyncio.create_task(_execute_bounded(tool_call))
            for tool_call in indexed_tool_calls
        ]
        try:
            for task in tasks:
                yield await task
        except BaseException:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    async def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        """Execute a tool with retry/fallback if enabled."""
        if self.enable_retry:
            tool = self.tools.get(tool_name)
            if tool:
                fallback_names = get_fallback_tools(tool_name)
                fallback_tools_raw = [
                    self.tools.get(name)
                    for name in fallback_names
                    if self.tools.has(name)
                ]
                fallback_tools = [t for t in fallback_tools_raw if t is not None]

                if fallback_tools:
                    return await self.retry_executor.execute_with_fallback(
                        tool, fallback_tools, **tool_input
                    )
                else:
                    return await self.retry_executor.execute_with_retry(tool, **tool_input)
            else:
                return await self.tools.execute(tool_name, **tool_input)
        else:
            return await self.tools.execute(tool_name, **tool_input)

    @staticmethod
    def _describe_requirements(parsed_query: ParsedQuery) -> str:
        """One line naming the collection requirements in force."""
        parts: list[str] = []
        if parsed_query.viewpoint:
            parts.append(f"{parsed_query.viewpoint.value} footage")
        if parsed_query.min_duration_seconds:
            parts.append(f"clips over {parsed_query.min_duration_seconds}s")
        if parsed_query.license_filter == "reusable":
            parts.append("reusable licence only")
        if parsed_query.target_hours:
            parts.append(f"target {parsed_query.target_hours}h")
        return ", ".join(parts)

    def _build_enhanced_query(
        self,
        user_query: str,
        parsed_query: ParsedQuery,
        pinned_sources: bool = False,
    ) -> str:
        """Build enhanced query string with extracted slots for Gemini."""
        parts = [f"User Query: {user_query}"]
        slot_context = []

        if parsed_query.platforms:
            platforms = ", ".join(parsed_query.platforms)
            if pinned_sources:
                slot_context.append(
                    f"Platforms (selected by the user - search only these): {platforms}"
                )
            else:
                slot_context.append(f"Platforms: {platforms}")
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

        return "\n".join(parts)

    def _calculate_usage_metrics(
        self,
        total_input_tokens: int,
        total_output_tokens: int,
        gemini_calls: int,
        tool_invocations: dict[str, int],
    ) -> UsageMetrics:
        """Calculate usage metrics and costs for the session."""
        pricing = get_pricing()

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

        tool_costs: list[ToolUsageCost] = []
        for tool_name, count in tool_invocations.items():
            unit_cost = pricing.tools.get_tool_cost(tool_name)
            quota = pricing.tools.get_youtube_quota(tool_name)
            tool_costs.append(ToolUsageCost(
                tool_name=tool_name,
                invocation_count=count,
                estimated_cost_usd=unit_cost * count,
                quota_used=quota * count if quota > 0 else None,
                token_usage=None,
                details=None,
            ))

        usage_metrics = UsageMetrics(
            gemini=gemini_cost,
            tool_costs=tool_costs,
            gemini_calls=gemini_calls,
            tool_calls=sum(tool_invocations.values()),
            total_cost_usd=0.0,
        )
        usage_metrics.calculate_total()
        return usage_metrics

    def _extract_video_references(
        self, search_results: list[dict[str, Any]], parsed_query: ParsedQuery | None = None
    ) -> list[VideoReference]:
        """Extract video references from search results."""

        references: list[VideoReference] = []
        seen_urls: set[str] = set()

        for result in search_results:
            if not result.get("success"):
                continue

            data = result.get("result", {})
            if not isinstance(data, dict):
                continue

            videos = data.get("videos", [])
            for video in videos:
                if isinstance(video, dict):
                    url = video.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        creator_data = video.get("creator")
                        creator_name = (
                            creator_data.get("username")
                            if isinstance(creator_data, dict)
                            else None
                        )
                        metrics_data = video.get("metrics")
                        views = (
                            metrics_data.get("views")
                            if isinstance(metrics_data, dict)
                            else None
                        )
                        likes = (
                            metrics_data.get("likes")
                            if isinstance(metrics_data, dict)
                            else None
                        )
                        published_at = video.get("published_at")
                        if published_at is not None and not isinstance(published_at, str):
                            published_at = str(published_at)
                        video_id_raw = video.get("id", video.get("platform_id", ""))
                        video_id = str(video_id_raw) if video_id_raw else ""
                        duration_seconds = video.get("duration_seconds")
                        references.append(VideoReference(
                            video_id=video_id,
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
                            relevance_note=None,
                        ))

        if parsed_query and parsed_query.metric:
            references = self._sort_references_by_metric(references, parsed_query.metric)

        return references[:20]

    def _sort_references_by_metric(
        self, references: list[VideoReference], metric: Any
    ) -> list[VideoReference]:
        """Sort video references by the specified metric."""
        from video_searching_agent.models.query import MetricType

        if metric in (MetricType.MOST_POPULAR, MetricType.FASTEST_GROWTH_VIEWS):
            return sorted(references, key=lambda r: r.views or 0, reverse=True)
        elif metric == MetricType.MOST_LIKED:
            return sorted(references, key=lambda r: r.likes or 0, reverse=True)
        return references

    def _filter_by_time_frame(
        self,
        video_references: list[VideoReference],
        time_frame: TimeFrame,
    ) -> list[VideoReference]:
        """Filter video references to only include those within the time frame."""
        from video_searching_agent.utils import get_cutoff_datetime

        cutoff = get_cutoff_datetime(time_frame)
        if cutoff is None:
            return video_references

        filtered: list[VideoReference] = []
        for ref in video_references:
            if not ref.published_at:
                filtered.append(ref)
                continue

            try:
                pub_date_str = ref.published_at
                if "T" in pub_date_str:
                    pub_date_str = pub_date_str.replace("Z", "+00:00")
                    pub_date = datetime.fromisoformat(pub_date_str)
                else:
                    pub_date = datetime.strptime(pub_date_str[:10], "%Y-%m-%d")
                    pub_date = pub_date.replace(tzinfo=UTC)

                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=UTC)

                if pub_date >= cutoff:
                    filtered.append(ref)
            except (ValueError, TypeError):
                filtered.append(ref)

        return filtered

    def _filter_tool_result_by_time(
        self,
        result: ToolResult,
        time_frame: TimeFrame,
    ) -> ToolResult:
        """Filter videos in tool result to only include those within time frame."""
        if not result.success or not result.data:
            return result

        data = result.data
        if not isinstance(data, dict) or "videos" not in data:
            return result

        from video_searching_agent.utils import get_cutoff_datetime

        cutoff = get_cutoff_datetime(time_frame)
        if cutoff is None:
            return result

        videos = data.get("videos", [])
        filtered_videos = []

        for video in videos:
            published_at = video.get("published_at")
            if not published_at:
                continue

            try:
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
                continue

        filtered_data = {**data, "videos": filtered_videos, "total_results": len(filtered_videos)}
        return ToolResult.ok(filtered_data)

    def _extract_platforms(self, search_results: list[dict[str, Any]]) -> list[str]:
        """Extract platforms searched from results."""
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
        """Count total videos found in search results."""
        count = 0
        for result in search_results:
            if not result.get("success"):
                continue
            data = result.get("result", {})
            if isinstance(data, dict):
                count += len(data.get("videos", []))
                count += data.get("total_results", 0)
        return count

    def get_tool_health(self) -> dict[str, dict[str, Any]]:
        """Get health status of all registered tools."""
        return self.tools.check_health()
