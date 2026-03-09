"""Utility functions for the video searching agent."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from video_searching_agent.models.query import TimeFrame


def get_current_year() -> int:
    """Get the current year."""
    return datetime.now().year


def get_current_date_iso() -> str:
    """Get current date in ISO format (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")


def get_recent_years(count: int = 2) -> list[str]:
    """Get list of recent years as strings for pattern matching.

    Args:
        count: Number of years to include (current year and previous).

    Returns:
        List of year strings, e.g., ["2026", "2025"] if current year is 2026.
    """
    current_year = get_current_year()
    return [str(current_year - i) for i in range(count)]


def get_date_context() -> str:
    """Get a formatted string describing the current date context.

    Returns:
        Human-readable date context for prompts.
    """
    now = datetime.now()
    return f"Today is {now.strftime('%B %d, %Y')}. The current year is {now.year}."


def _get_time_delta(time_range: str) -> timedelta | None:
    """Get timedelta for a time range string.

    Args:
        time_range: Time range string (TimeFrame enum value or legacy format).

    Returns:
        timedelta for the time range, or None for "all_time" or unknown values.
    """
    delta_map = {
        # TimeFrame enum values (used by parsed query)
        "past_24_hours": timedelta(days=1),
        "past_48_hours": timedelta(days=2),
        "past_week": timedelta(weeks=1),
        "past_month": timedelta(days=30),
        "past_year": timedelta(days=365),
        "all_time": None,
        # Legacy string formats (for backwards compatibility)
        "past day": timedelta(days=1),
        "past week": timedelta(weeks=1),
        "past month": timedelta(days=30),
        "past year": timedelta(days=365),
    }
    return delta_map.get(time_range)


def get_published_after_date(time_range: str) -> str | None:
    """Convert a time range string to an ISO 8601 date for API filtering.

    Args:
        time_range: Time range string (TimeFrame enum value or legacy format).
            Supported values: "past_24_hours", "past_48_hours", "past_week",
            "past_month", "past_year", "all_time", and legacy formats like
            "past day", "past week", etc.

    Returns:
        ISO 8601 formatted date string (e.g., "2026-01-21T00:00:00Z") or None
        for "all_time" or unknown values.
    """
    delta = _get_time_delta(time_range)
    if delta is None:
        return None
    target_date = datetime.now(UTC) - delta
    return target_date.strftime("%Y-%m-%dT00:00:00Z")


def get_cutoff_datetime(time_frame: "TimeFrame | str") -> datetime | None:
    """Get cutoff datetime for filtering videos by time frame.

    This function is useful for post-filtering video results that don't
    support date filtering at the API level.

    Args:
        time_frame: TimeFrame enum value or string representation.

    Returns:
        Cutoff datetime (timezone-aware UTC) or None for "all_time".
    """
    # Handle TimeFrame enum by getting its value
    if hasattr(time_frame, "value"):
        time_range = time_frame.value
    else:
        time_range = str(time_frame)

    delta = _get_time_delta(time_range)
    if delta is None:
        return None
    return datetime.now(UTC) - delta
