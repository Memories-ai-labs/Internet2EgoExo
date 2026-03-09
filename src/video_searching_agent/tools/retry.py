"""Retry mechanism with exponential backoff for tool execution."""

import asyncio
import logging
from typing import Any

from video_searching_agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class RetryExecutor:
    """Executes tools with retry logic and fallback support.

    Implements exponential backoff for transient failures to achieve
    the PRD target of ≥99% tool invocation success rate.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
    ):
        """Initialize the retry executor.

        Args:
            max_retries: Maximum number of retry attempts.
            base_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
            backoff_factor: Multiplier for exponential backoff.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self._tool_retry_overrides = {
            # Instagram Apify 400/run-failed errors are typically malformed-input
            # or actor-level run failures; retries tend to stall completion.
            "instagram_search": 0,
            # MAI transcript can block for minutes; retries risk exceeding
            # OpenClaw skill timeout budgets.
            "social_media_mai_transcript": 0,
        }

    async def execute_with_retry(
        self,
        tool: BaseTool,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a tool with retry logic.

        Uses exponential backoff for transient failures.

        Args:
            tool: Tool to execute.
            **kwargs: Tool input parameters.

        Returns:
            ToolResult from successful execution or final failure.
        """
        last_error = None
        delay = self.base_delay
        max_retries = self._max_retries_for_tool(tool.name)

        for attempt in range(max_retries + 1):
            try:
                result = await tool.execute(**kwargs)

                # Check if result indicates a retryable error
                if result.success or not self._is_retryable_error(result):
                    return result

                last_error = result.data
                logger.warning(
                    f"Tool {tool.name} failed (attempt {attempt + 1}/{max_retries + 1}): "
                    f"{result.data}"
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Tool {tool.name} raised exception "
                    f"(attempt {attempt + 1}/{max_retries + 1}): "
                    f"{e}"
                )

                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    return ToolResult.fail(f"Non-retryable error: {e}")

            # Don't delay after last attempt
            if attempt < max_retries:
                logger.info(
                    "retry_sleep tool=%s attempt=%d delay_seconds=%.1f",
                    tool.name,
                    attempt + 1,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * self.backoff_factor, self.max_delay)

        return ToolResult.fail(f"Failed after {max_retries + 1} attempts: {last_error}")

    async def execute_with_fallback(
        self,
        primary_tool: BaseTool,
        fallback_tools: list[BaseTool],
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a tool with fallback to alternative tools.

        Tries the primary tool first (with retries), then falls back
        to alternative tools in order.

        Args:
            primary_tool: Primary tool to try first.
            fallback_tools: List of fallback tools to try if primary fails.
            **kwargs: Tool input parameters.

        Returns:
            ToolResult from first successful execution.
        """
        # Track all errors for detailed failure message
        all_errors: list[tuple[str, str]] = []

        # Try primary tool with retries
        result = await self.execute_with_retry(primary_tool, **kwargs)
        if result.success:
            return result

        primary_error = result.error or str(result.data)
        all_errors.append((primary_tool.name, primary_error))
        logger.info(
            f"Primary tool {primary_tool.name} failed, trying fallbacks: "
            f"{[t.name for t in fallback_tools]}"
        )

        # Try fallback tools
        for fallback in fallback_tools:
            try:
                # Adapt kwargs for fallback tool if needed
                adapted_kwargs = self._adapt_kwargs_for_tool(fallback, kwargs)

                result = await self.execute_with_retry(fallback, **adapted_kwargs)
                if result.success:
                    logger.info(f"Fallback tool {fallback.name} succeeded")
                    # Add warning that fallback was used
                    warnings = list(result.warnings) if result.warnings else []
                    warnings.append(
                        f"Used fallback tool {fallback.name} after {primary_tool.name} failed"
                    )
                    return ToolResult.ok(
                        result.data,
                        parse_stats=result.parse_stats,
                        warnings=warnings,
                    )

                fallback_error = result.error or str(result.data)
                all_errors.append((fallback.name, fallback_error))
                logger.warning(f"Fallback tool {fallback.name} also failed: {fallback_error}")

            except Exception as e:
                all_errors.append((fallback.name, str(e)))
                logger.warning(f"Fallback tool {fallback.name} raised exception: {e}")

        # Build detailed error message with all failures
        error_details = "; ".join([f"{name}: {err}" for name, err in all_errors])
        return ToolResult.fail(
            f"All tools failed. Errors: [{error_details}]"
        )

    def _is_retryable_error(self, result: ToolResult) -> bool:
        """Determine if a tool result indicates a retryable error.

        Args:
            result: Tool result to check.

        Returns:
            True if the error is retryable.
        """
        if result.success:
            return False

        # Check both error and data fields for error message
        error_msg = (str(result.error or "") + str(result.data or "")).lower()

        non_retryable_patterns = [
            "run-failed",
            "bad request",
            "400",
            "invalid input",
            "malformed input",
            "validation error",
            "unprocessable entity",
        ]
        if any(pattern in error_msg for pattern in non_retryable_patterns):
            return False

        # Retryable patterns
        retryable_patterns = [
            "timeout",
            "timed out",
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "connection",
            "network",
            "502",
            "503",
            "504",
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Determine if an exception is retryable.

        Args:
            exception: Exception to check.

        Returns:
            True if the exception is retryable.
        """
        error_msg = str(exception).lower()
        exception_type = type(exception).__name__.lower()

        non_retryable_patterns = [
            "run-failed",
            "bad request",
            "invalid input",
            "malformed input",
            "validation error",
            "unprocessable entity",
        ]
        if any(pattern in error_msg for pattern in non_retryable_patterns):
            return False

        # Retryable exception types
        retryable_types = [
            "timeout",
            "connection",
            "temporary",
            "browsertimeout",
        ]

        if any(t in exception_type for t in retryable_types):
            return True

        # Retryable error messages
        retryable_patterns = [
            "timeout",
            "connection",
            "network",
            "rate limit",
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    def _max_retries_for_tool(self, tool_name: str) -> int:
        """Resolve retry count for a specific tool."""
        override = self._tool_retry_overrides.get(tool_name)
        if override is None:
            return self.max_retries
        return max(0, int(override))

    def _adapt_kwargs_for_tool(
        self,
        tool: BaseTool,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Adapt input kwargs for a different tool.

        Args:
            tool: Target tool.
            kwargs: Original kwargs.

        Returns:
            Adapted kwargs for the target tool.
        """
        # Get the tool's input schema to know what parameters it accepts
        schema = tool.input_schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        adapted = {}

        # Map common parameter names
        param_mappings = {
            "query": ["query", "search_query", "q"],
            "max_results": ["max_results", "limit", "count", "num_results"],
            "search_type": ["search_type", "filter", "content_type"],
        }

        for target_param in properties:
            # Check direct match
            if target_param in kwargs:
                adapted[target_param] = kwargs[target_param]
                continue

            # Check mappings
            for canonical, aliases in param_mappings.items():
                if target_param in aliases:
                    for alias in aliases:
                        if alias in kwargs:
                            adapted[target_param] = kwargs[alias]
                            break

        # Ensure required params are present
        for req in required:
            if req not in adapted:
                # Try to find a value from mappings
                for canonical, aliases in param_mappings.items():
                    if req in aliases:
                        for alias in aliases:
                            if alias in kwargs:
                                adapted[req] = kwargs[alias]
                                break

        return adapted


# Tool fallback configuration
# Note: TikTok and Instagram tools now handle fallbacks internally,
# so they don't need entries here. Only tools that rely on external
# fallback chains are listed.
TOOL_FALLBACKS: dict[str, list[str]] = {
    # Twitter: twscrape primary (handled in tool), exa fallback
    "twitter_search": ["exa_search"],
    "twitter_profile_info": [],

    # Exa internal fallbacks
    "exa_find_similar": ["exa_search"],
    "exa_research": ["exa_search"],
    "exa_get_content": [],
}


def get_fallback_tools(tool_name: str) -> list[str]:
    """Get fallback tool names for a given tool.

    Args:
        tool_name: Name of the primary tool.

    Returns:
        List of fallback tool names.
    """
    return TOOL_FALLBACKS.get(tool_name, [])
