"""Utility functions for chat automation."""

from datetime import datetime
from typing import Optional


def format_timestamp(timestamp_str: Optional[str]) -> Optional[str]:
    """
    Convert ISO timestamp string to human-readable format.

    Args:
        timestamp_str: ISO format timestamp string (e.g., "2023-01-01T14:30:00")

    Returns:
        Human-readable timestamp string (e.g., "Jan 1, 2023, 2:30 PM") or None
    """
    if not timestamp_str:
        return None

    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Format as human-readable: "Jan 1, 2023, 2:30 PM"
        return dt.strftime("%b %d, %Y, %I:%M %p")
    except Exception:
        # Return original string if parsing fails
        return timestamp_str
