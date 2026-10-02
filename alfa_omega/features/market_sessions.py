"""Causal global-session and market-calendar context.

Session labels are computed from the timestamp itself using IANA time zones,
so daylight-saving changes are handled without hard-coded UTC offsets.
Session context is descriptive evidence; it does not by itself create a
trade signal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd


@dataclass(frozen=True)
class SessionWindow:
    name: str
    timezone: str
    start: time
    end: time


SESSION_WINDOWS = (
    SessionWindow("SYDNEY", "Australia/Sydney", time(7, 0), time(16, 0)),
    SessionWindow("TOKYO", "Asia/Tokyo", time(9, 0), time(18, 0)),
    SessionWindow("LONDON", "Europe/London", time(8, 0), time(17, 0)),
    SessionWindow("NEW_YORK", "America/New_York", time(8, 0), time(17, 0)),
)


def _local_time(timestamp: pd.Timestamp, zone: str) -> time:
    return timestamp.tz_convert(ZoneInfo(zone)).time()


def _inside(value: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= value < end
    return value >= start or value < end


def session_context(timestamp: pd.Timestamp) -> dict[str, object]:
    """Return all active global sessions and their overlaps at a timestamp."""
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    active: list[str] = []
    for window in SESSION_WINDOWS:
        local = _local_time(ts, window.timezone)
        if _inside(local, window.start, window.end):
            active.append(window.name)

    overlap = "NONE"
    if len(active) >= 2:
        if "LONDON" in active and "NEW_YORK" in active:
            overlap = "LONDON_NEW_YORK"
        elif "TOKYO" in active and "LONDON" in active:
            overlap = "TOKYO_LONDON"
        else:
            overlap = "_".join(active)

    return {
        "session_active": tuple(active),
        "session_primary": active[0] if active else "OFF_SESSION",
        "session_overlap": overlap,
        "is_london_open_window": "LONDON" in active,
        "is_new_york_open_window": "NEW_YORK" in active,
        "utc_timestamp": ts.tz_convert("UTC").isoformat(),
    }


def add_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add causal session context to every row of a UTC-aware market frame."""
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("session features require a DatetimeIndex")
    if df.index.tz is None:
        raise ValueError("session features require a timezone-aware index")

    out = df.copy()
    contexts = [session_context(ts) for ts in out.index]
    out["session_primary"] = [item["session_primary"] for item in contexts]
    out["session_overlap"] = [item["session_overlap"] for item in contexts]
    out["is_london_open_window"] = [item["is_london_open_window"] for item in contexts]
    out["is_new_york_open_window"] = [item["is_new_york_open_window"] for item in contexts]
    out["session_active_count"] = [
        len(item["session_active"]) for item in contexts
    ]
    return out
