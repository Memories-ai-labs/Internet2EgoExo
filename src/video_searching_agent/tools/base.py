"""Base tool interface for Gemini function calling."""

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field


class ParseStats(BaseModel):
    """Statistics for tracking parsing results.

    Useful for tools that parse lists of items where individual
    items may fail while others succeed.
    """

    total_items: int = 0
    successfully_parsed: int = 0
    failed_to_parse: int = 0
    parse_errors: list[str] = Field(default_factory=list)
    _max_errors: int = 5  # Keep first 5 errors to avoid bloat

    def add_success(self) -> None:
        """Record a successfully parsed item."""
        self.total_items += 1
        self.successfully_parsed += 1

    def add_failure(self, error: str) -> None:
        """Record a failed parse with error message.

        Args:
            error: Error message describing the parse failure.
        """
        self.total_items += 1
        self.failed_to_parse += 1
        if len(self.parse_errors) < self._max_errors:
            self.parse_errors.append(error)

    @property
    def success_rate(self) -> float:
        """Calculate the parse success rate as a percentage."""
        if self.total_items == 0:
            return 100.0
        return (self.successfully_parsed / self.total_items) * 100.0

    def has_failures(self) -> bool:
        """Check if any items failed to parse."""
        return self.failed_to_parse > 0

    def summary(self) -> str:
        """Generate a human-readable summary of parsing results."""
        if self.total_items == 0:
            return "No items processed"
        if not self.has_failures():
            return f"All {self.total_items} items parsed successfully"
        return (
            f"Parsed {self.successfully_parsed}/{self.total_items} items "
            f"({self.failed_to_parse} failed, {self.success_rate:.1f}% success rate)"
        )


class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = True
    data: Any = None
    error: str | None = None
    parse_stats: ParseStats | None = None
    warnings: list[str] = Field(default_factory=list)
    result_type: Literal["success", "no_results", "error"] = "success"

    @classmethod
    def ok(
        cls,
        data: Any,
        parse_stats: ParseStats | None = None,
        warnings: list[str] | None = None,
    ) -> "ToolResult":
        """Create a successful result.

        Args:
            data: The result data.
            parse_stats: Optional parsing statistics.
            warnings: Optional list of warnings.

        Returns:
            A successful ToolResult.
        """
        return cls(
            success=True,
            data=data,
            parse_stats=parse_stats,
            warnings=warnings or [],
            result_type="success",
        )

    @classmethod
    def no_results(
        cls,
        message: str,
        parse_stats: ParseStats | None = None,
        warnings: list[str] | None = None,
    ) -> "ToolResult":
        """Create a result indicating no matches found (not an error).

        Use this when a search completes successfully but finds no matching items.
        This is distinct from an error - the tool worked, but nothing matched.

        Args:
            message: Message explaining the empty result.
            parse_stats: Optional parsing statistics.
            warnings: Optional list of warnings.

        Returns:
            A ToolResult with result_type="no_results".
        """
        return cls(
            success=True,  # Search worked, just no matches
            data={"message": message, "videos": [], "total_results": 0},
            parse_stats=parse_stats,
            warnings=warnings or [],
            result_type="no_results",
        )

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error, result_type="error")

    def to_string(self) -> str:
        """Convert result to string for LLM.

        Includes parse statistics and warnings if present.
        """
        parts = []

        if self.success:
            if isinstance(self.data, str):
                parts.append(self.data)
            elif isinstance(self.data, dict | list):
                import json
                parts.append(json.dumps(self.data, separators=(",", ":"), default=str))
            else:
                parts.append(str(self.data))

            # Add parse stats summary if there were failures
            if self.parse_stats and self.parse_stats.has_failures():
                parts.append(f"\n[Parse Stats: {self.parse_stats.summary()}]")

            # Add warnings
            if self.warnings:
                parts.append(f"\n[Warnings: {'; '.join(self.warnings)}]")
        else:
            parts.append(f"Error: {self.error}")

        return "".join(parts)


class BaseTool(ABC):
    """Base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for function calling."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description explaining when and how to use it."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON schema for tool input parameters."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool input parameters.

        Returns:
            ToolResult with success status and data/error.
        """
        pass

    def to_tool_definition(self) -> dict[str, Any]:
        """Convert to tool definition format for function calling.

        Returns:
            Tool definition dict with name, description, and input_schema.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def health_check(self) -> tuple[bool, str | None]:
        """Check if the tool is properly configured and ready to use.

        Override this method in tools that require API keys or other configuration.

        Returns:
            Tuple of (is_healthy, error_message).
            - (True, None) if tool is ready to use
            - (False, "error description") if tool is misconfigured
        """
        return True, None

    def validate_input(self, **kwargs: Any) -> tuple[bool, str | None]:
        """Validate input parameters against schema.

        Args:
            **kwargs: Input parameters to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        schema = self.input_schema
        required = schema.get("required", [])

        # Check required fields
        for field in required:
            if field not in kwargs or kwargs[field] is None:
                return False, f"Missing required field: {field}"

        # Check types and enums
        properties = schema.get("properties", {})
        for key, value in kwargs.items():
            if key in properties:
                prop_schema = properties[key]

                # Type validation
                expected_type = prop_schema.get("type")
                if expected_type and not self._check_type(value, expected_type):
                    return False, f"Invalid type for {key}: expected {expected_type}"

                # Enum validation
                allowed_values = prop_schema.get("enum")
                if allowed_values is not None and value not in allowed_values:
                    return False, (
                        f"Invalid value for {key}: '{value}'. "
                        f"Allowed values: {allowed_values}"
                    )

        return True, None

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, allow
        return isinstance(value, expected)  # type: ignore[arg-type]
