"""Causal multi-timeframe market map for ALFA OMEGA.

The market is hierarchical: higher-timeframe candles contain lower-timeframe
candles. This module does not treat those relationships as independent signals;
it builds a time-aligned context map that can be consumed by feature/model
layers without leaking information from an unfinished higher-timeframe candle.

Hierarchy supported by the current ALFA OMEGA data contract:
1w -> 1d -> 4h -> 1h -> 15m -> 5m -> 1m

A higher-timeframe feature is only allowed to become available to a lower
timeframe after the higher-timeframe candle has CLOSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd


TIMEFRAME_MINUTES: dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}

PARENT_TIMEFRAME: dict[str, str | None] = {
    "1m": "5m",
    "5m": "15m",
    "15m": "1h",
    "1h": "4h",
    "4h": "1d",
    "1d": "1w",
    "1w": None,
}


@dataclass(frozen=True)
class TimeframeNode:
    timeframe: str
    minutes: int
    parent: str | None
    child: str | None


def hierarchy() -> tuple[TimeframeNode, ...]:
    ordered = sorted(TIMEFRAME_MINUTES, key=TIMEFRAME_MINUTES.get)
    return tuple(
        TimeframeNode(
            timeframe=tf,
            minutes=TIMEFRAME_MINUTES[tf],
            parent=PARENT_TIMEFRAME[tf],
            child=ordered[i - 1] if i else None,
        )
        for i, tf in enumerate(ordered)
    )


def _validate_frame(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    required = {"open", "high", "low", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{timeframe}: missing OHLC columns: {sorted(missing)}")
    if df.empty:
        return df.copy()
    out = df.copy().sort_index()
    if not isinstance(out.index, pd.DatetimeIndex):
        raise TypeError(f"{timeframe}: index must be a DatetimeIndex")
    if out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    return out


def child_count(parent: str, child: str) -> int:
    """Return the ideal number of child candles inside a parent interval."""
    if parent not in TIMEFRAME_MINUTES or child not in TIMEFRAME_MINUTES:
        raise ValueError("Unsupported timeframe")
    parent_minutes = TIMEFRAME_MINUTES[parent]
    child_minutes = TIMEFRAME_MINUTES[child]
    if parent_minutes <= child_minutes or parent_minutes % child_minutes:
        raise ValueError(f"{child} is not a direct uniform child of {parent}")
    return parent_minutes // child_minutes


def _completed_parent_features(
    parent_df: pd.DataFrame,
    child_index: pd.DatetimeIndex,
    parent: str,
) -> pd.DataFrame:
    """Align CLOSED parent candles to child timestamps only.

    Parent timestamps are interpreted as candle OPEN timestamps. A parent
    candle opened at T is therefore usable by a child candle only from its
    CLOSE timestamp onward.
    """
    parent_df = _validate_frame(parent_df, parent)
    if parent_df.empty:
        return pd.DataFrame(index=child_index)

    duration = pd.Timedelta(minutes=TIMEFRAME_MINUTES[parent])
    completed_at = parent_df.index + duration

    source = parent_df.copy()
    source["_parent_close_time"] = completed_at
    source["_parent_open_time"] = parent_df.index

    numeric = source.select_dtypes(include="number").copy()
    if numeric.empty:
        return pd.DataFrame(index=child_index)

    numeric.columns = [f"htf_{parent}_{c}" for c in numeric.columns]
    numeric["_parent_close_time"] = completed_at
    numeric["_parent_open_time"] = parent_df.index

    left = pd.DataFrame({"child_time": child_index}).sort_values("child_time")
    right = numeric.sort_values("_parent_close_time")

    aligned = pd.merge_asof(
        left,
        right,
        left_on="child_time",
        right_on="_parent_close_time",
        direction="backward",
        allow_exact_matches=True,
    ).set_index("child_time")

    # The source parent candle must have completed strictly at or before the
    # child timestamp. merge_asof already enforces this via right_on.
    aligned = aligned.drop(columns=["_parent_close_time"], errors="ignore")
    aligned = aligned.rename(columns={"_parent_open_time": f"htf_{parent}_open_time"})
    return aligned


def build_market_map(
    frames: Mapping[str, pd.DataFrame],
    target_timeframe: str = "5m",
) -> pd.DataFrame:
    """Build a causal top-down market map for one target timeframe.

    Example:
        map_5m = build_market_map(
            {"1w": weekly, "1d": daily, "4h": h4, "1h": h1,
             "15m": m15, "5m": m5, "1m": m1},
            target_timeframe="5m",
        )

    The returned frame keeps the target candle data and adds completed
    higher-timeframe context. It intentionally does not forward-fill an
    unfinished weekly/daily/etc. candle.
    """
    if target_timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe: {target_timeframe}")
    if target_timeframe not in frames:
        raise ValueError(f"Missing target timeframe: {target_timeframe}")

    target = _validate_frame(frames[target_timeframe], target_timeframe)
    if target.empty:
        return target.copy()

    out = target.copy()
    target_minutes = TIMEFRAME_MINUTES[target_timeframe]

    for tf in TIMEFRAME_MINUTES:
        if tf == target_timeframe:
            continue
        if TIMEFRAME_MINUTES[tf] <= target_minutes:
            continue
        if tf not in frames:
            continue

        aligned = _completed_parent_features(frames[tf], out.index, tf)
        for column in aligned.columns:
            if column not in out.columns:
                out[column] = aligned[column]

    # Explicit regime/context flags make the hierarchy usable by ML and
    # explainability layers without pretending that it is a trading signal.
    for tf in TIMEFRAME_MINUTES:
        if TIMEFRAME_MINUTES[tf] <= target_minutes:
            continue
        close_col = f"htf_{tf}_close"
        open_col = f"htf_{tf}_open"
        if close_col in out.columns and open_col in out.columns:
            out[f"htf_{tf}_direction"] = (
                out[close_col] > out[open_col]
            ).astype("Int64")
            out[f"htf_{tf}_range_pct"] = (
                (out[f"htf_{tf}_high"] - out[f"htf_{tf}_low"])
                / out[close_col].replace(0, pd.NA)
            )

    return out


def describe_hierarchy() -> dict[str, object]:
    """Return a machine-readable description of the market nesting."""
    return {
        "order": ["1w", "1d", "4h", "1h", "15m", "5m", "1m"],
        "relationships": {
            "1w": {"contains": ["1d"], "child_count": 7},
            "1d": {"contains": ["4h"], "child_count": 6},
            "4h": {"contains": ["1h"], "child_count": 4},
            "1h": {"contains": ["15m"], "child_count": 4},
            "15m": {"contains": ["5m"], "child_count": 3},
            "5m": {"contains": ["1m"], "child_count": 5},
            "1m": {"contains": [], "child_count": None},
        },
        "causal_rule": "higher_timeframe_context_only_after_parent_close",
        "source_of_truth": "ALFA_OMEGA",
    }
