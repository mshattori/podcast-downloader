from __future__ import annotations

import re


def parse_duration(raw: str | None) -> int | None:
    """Parse an RSS duration string into total seconds.

    Supported formats:
      "3600"    -> 3600  (seconds only)
      "60:00"   -> 3600  (MM:SS)
      "1:00:00" -> 3600  (HH:MM:SS)
      "90:30"   -> 5430  (minutes >= 60 are normalised)
    Returns None if the input cannot be parsed or represents a negative value.
    """
    if not raw or not isinstance(raw, str):
        return None

    raw = raw.strip()
    if not raw:
        return None

    # Seconds-only integer
    if re.fullmatch(r"\d+", raw):
        seconds = int(raw)
        return seconds if seconds >= 0 else None

    # MM:SS or HH:MM:SS
    parts = raw.split(":")
    if len(parts) == 2:
        try:
            minutes, secs = int(parts[0]), int(parts[1])
            total = minutes * 60 + secs
            return total if total >= 0 else None
        except ValueError:
            return None

    if len(parts) == 3:
        try:
            hours, minutes, secs = int(parts[0]), int(parts[1]), int(parts[2])
            total = hours * 3600 + minutes * 60 + secs
            return total if total >= 0 else None
        except ValueError:
            return None

    return None


def format_duration(seconds: int | None) -> str:
    """Format a duration in seconds to a Japanese display string.

    Examples:
      None  -> "不明"
      45    -> "45秒"
      2730  -> "45分30秒"
      5400  -> "1時間30分00秒"
    """
    if seconds is None:
        return "不明"

    seconds = max(0, seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h}時間{m:02d}分{s:02d}秒"
    if m > 0:
        return f"{m}分{s:02d}秒"
    return f"{s}秒"
