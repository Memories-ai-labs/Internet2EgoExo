"""Tests for utility functions."""

from datetime import datetime

from video_searching_agent.tools.base import ToolResult
from video_searching_agent.utils import (
    get_current_date_iso,
    get_current_year,
    get_date_context,
    get_published_after_date,
    get_recent_years,
)


class TestDateUtils:
    """Tests for date utility functions."""

    def test_get_current_year(self):
        """Test getting current year."""
        year = get_current_year()
        assert isinstance(year, int)
        assert year >= 2024  # Sanity check

    def test_get_current_date_iso(self):
        """Test ISO date format."""
        date_str = get_current_date_iso()
        # Should be parseable as YYYY-MM-DD
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        assert parsed is not None

    def test_get_recent_years_default(self):
        """Test getting recent years with default count."""
        years = get_recent_years()
        assert len(years) == 2
        assert all(isinstance(y, str) for y in years)
        # Current year should be first
        assert years[0] == str(get_current_year())
        # Previous year should be second
        assert years[1] == str(get_current_year() - 1)

    def test_get_recent_years_custom_count(self):
        """Test getting different counts of years."""
        years = get_recent_years(3)
        assert len(years) == 3
        current = get_current_year()
        assert years == [str(current), str(current - 1), str(current - 2)]

    def test_get_recent_years_single(self):
        """Test getting just the current year."""
        years = get_recent_years(1)
        assert len(years) == 1
        assert years[0] == str(get_current_year())

    def test_get_date_context_format(self):
        """Test date context contains expected elements."""
        context = get_date_context()
        current_year = str(get_current_year())
        assert current_year in context
        assert "Today is" in context
        assert "current year is" in context

    def test_get_published_after_date_past_day(self):
        """Test published after date for past day."""
        result = get_published_after_date("past day")
        assert result is not None
        assert result.endswith("T00:00:00Z")
        # Should be parseable
        date_part = result.replace("T00:00:00Z", "")
        datetime.strptime(date_part, "%Y-%m-%d")

    def test_get_published_after_date_past_week(self):
        """Test published after date for past week."""
        result = get_published_after_date("past week")
        assert result is not None
        assert result.endswith("T00:00:00Z")

    def test_get_published_after_date_past_month(self):
        """Test published after date for past month."""
        result = get_published_after_date("past month")
        assert result is not None
        assert result.endswith("T00:00:00Z")

    def test_get_published_after_date_past_year(self):
        """Test published after date for past year."""
        result = get_published_after_date("past year")
        assert result is not None
        assert result.endswith("T00:00:00Z")

    def test_get_published_after_date_invalid(self):
        """Test published after date for invalid range."""
        result = get_published_after_date("invalid range")
        assert result is None

    def test_get_published_after_date_empty(self):
        """Test published after date for empty string."""
        result = get_published_after_date("")
        assert result is None


class TestToolResultFormatting:
    """Tests for ToolResult string formatting."""

    def test_to_string_uses_compact_json(self):
        """ToolResult JSON payload should be compact for token efficiency."""
        result = ToolResult.ok({"videos": [{"id": "1", "title": "A"}], "total_results": 1})
        output = result.to_string()

        assert "\n" not in output
        assert '"videos":[{"id":"1","title":"A"}]' in output
