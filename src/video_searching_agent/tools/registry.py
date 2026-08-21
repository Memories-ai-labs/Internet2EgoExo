"""Tool registry for managing and executing tools."""

import logging
from collections.abc import Iterator
from typing import Any

from video_searching_agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing all available tools."""

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register.
        """
        self._tools[tool.name] = tool

    def register_all(self, tools: list[BaseTool]) -> None:
        """Register multiple tools.

        Args:
            tools: List of tool instances to register.
        """
        for tool in tools:
            self.register(tool)

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool by name.

        Args:
            tool_name: Name of tool to unregister.
        """
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            tool_name: Name of tool to retrieve.

        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(tool_name)

    def has(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of tool to check.

        Returns:
            True if tool is registered.
        """
        return tool_name in self._tools

    def list_tools(self) -> list[str]:
        """Get list of registered tool names.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for function calling.

        Returns:
            List of tool definition dicts.
        """
        return [tool.to_tool_definition() for tool in self._tools.values()]

    def check_health(self) -> dict[str, dict[str, Any]]:
        """Check health of all registered tools.

        Returns:
            Dict mapping tool name to health status:
            {
                "tool_name": {
                    "healthy": bool,
                    "error": str | None
                }
            }
        """
        results: dict[str, dict[str, Any]] = {}
        for name, tool in self._tools.items():
            is_healthy, error = tool.health_check()
            results[name] = {
                "healthy": is_healthy,
                "error": error,
            }
        return results

    def get_unhealthy_tools(self) -> list[tuple[str, str]]:
        """Get list of tools that failed health check.

        Returns:
            List of (tool_name, error_message) tuples for unhealthy tools.
        """
        unhealthy = []
        for name, tool in self._tools.items():
            is_healthy, error = tool.health_check()
            if not is_healthy and error:
                unhealthy.append((name, error))
        return unhealthy

    def log_health_status(self) -> None:
        """Log health status of all tools, warning about misconfigured ones."""
        unhealthy = self.get_unhealthy_tools()
        if unhealthy:
            # Group tools by error message for cleaner logging
            errors_to_tools: dict[str, list[str]] = {}
            for tool_name, error in unhealthy:
                if error not in errors_to_tools:
                    errors_to_tools[error] = []
                errors_to_tools[error].append(tool_name)

            for error, tools in errors_to_tools.items():
                tool_list = ", ".join(tools)
                logger.warning(f"Tool health check failed: {error} (affects: {tool_list})")

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name with given input.

        Args:
            tool_name: Name of tool to execute.
            **kwargs: Tool input parameters.

        Returns:
            ToolResult from execution.
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        # Validate input
        is_valid, error = tool.validate_input(**kwargs)
        if not is_valid:
            return ToolResult.fail(error or "Invalid input")

        # Execute tool
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult.fail(f"Tool execution error: {str(e)}")

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered."""
        return tool_name in self._tools

    def __iter__(self) -> Iterator[BaseTool]:
        """Iterate over tools."""
        return iter(self._tools.values())


def create_default_registry() -> ToolRegistry:
    """Create a registry with all default tools.

    Returns:
        ToolRegistry with standard tools registered.
    """
    from video_searching_agent.tools.exa import (
        ExaContentTool,
        ExaResearchTool,
        ExaSearchTool,
        ExaSimilarTool,
    )
    from video_searching_agent.tools.memories_datalake import (
        VideoAnalysisTool,
        VideoIndexTool,
        VideoMomentSearchTool,
    )
    from video_searching_agent.tools.youtube import YouTubeSearchTool

    registry = ToolRegistry()
    registry.register_all([
        YouTubeSearchTool(),
        ExaSearchTool(),
        ExaSimilarTool(),
        ExaContentTool(),
        ExaResearchTool(),
        # Memories.ai Video Datalake
        VideoIndexTool(),
        VideoAnalysisTool(),
        VideoMomentSearchTool(),
    ])
    return registry
