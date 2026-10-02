"""Causal event-based labels for ALFA OMEGA.

Labels are computed on the complete chronological timeline. A prediction
timestamp is only resolved when the requested future horizon is fully
available. Incomplete horizons are marked UNRESOLVED when requested or
excluded from the returned label set.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class _BarrierOutcome:
    outcome: str
    exit_price: float
    event_time: object


def _validate_input(
    df: pd.DataFrame,
    horizon_bars: int,
    stop_atr: float,
    target_atr: float,
) -> None:
    required = {"open", "high", "low", "close", "atr_14"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    if stop_atr <= 0 or target_atr <= 0:
        raise ValueError("barrier distances must be positive")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("df index must be a DatetimeIndex")
    if not df.index.is_monotonic_increasing:
        raise ValueError("df index must be sorted ascending")
    if df.index.has_duplicates:
        raise ValueError("df index must not contain duplicates")


def _resolve_long(
    frame: pd.DataFrame,
    start: int,
    end: int,
    stop: float,
    target: float,
) -> _BarrierOutcome:
    for j in range(start + 1, end + 1):
        high = float(frame["high"].iloc[j])
        low = float(frame["low"].iloc[j])
        if not pd.notna(high) or not pd.notna(low):
            continue
        if low <= stop:
            return _BarrierOutcome("STOP", stop, frame.index[j])
        if high >= target:
            return _BarrierOutcome("TARGET", target, frame.index[j])
    exit_price = float(frame["close"].iloc[end])
    return _BarrierOutcome("TIME", exit_price, frame.index[end])


def _resolve_short(
    frame: pd.DataFrame,
    start: int,
    end: int,
    stop: float,
    target: float,
) -> _BarrierOutcome:
    for j in range(start + 1, end + 1):
        high = float(frame["high"].iloc[j])
        low = float(frame["low"].iloc[j])
        if not pd.notna(high) or not pd.notna(low):
            continue
        if high >= stop:
            return _BarrierOutcome("STOP", stop, frame.index[j])
        if low <= target:
            return _BarrierOutcome("TARGET", target, frame.index[j])
    exit_price = float(frame["close"].iloc[end])
    return _BarrierOutcome("TIME", exit_price, frame.index[end])


def _unresolved_row(timestamp: object, horizon_bars: int) -> dict[str, object]:
    return {
        "timestamp": timestamp,
        "label_long_outcome": "UNRESOLVED",
        "label_short_outcome": "UNRESOLVED",
        "label_long_r": float("nan"),
        "label_short_r": float("nan"),
        "label_long_event_time": pd.NaT,
        "label_short_event_time": pd.NaT,
        "label_horizon_bars": horizon_bars,
    }


def _resolved_row(
    timestamp: object,
    horizon_bars: int,
    entry: float,
    long_stop: float,
    long_result: _BarrierOutcome,
    short_stop: float,
    short_result: _BarrierOutcome,
) -> dict[str, object]:
    long_r = (long_result.exit_price - entry) / (entry - long_stop)
    short_r = (entry - short_result.exit_price) / (short_stop - entry)
    return {
        "timestamp": timestamp,
        "label_long_outcome": long_result.outcome,
        "label_short_outcome": short_result.outcome,
        "label_long_r": long_r,
        "label_short_r": short_r,
        "label_long_event_time": long_result.event_time,
        "label_short_event_time": short_result.event_time,
        "label_horizon_bars": horizon_bars,
    }


def triple_barrier_labels(
    df: pd.DataFrame,
    *,
    horizon_bars: int = 12,
    stop_atr: float = 1.0,
    target_atr: float = 2.0,
    include_unresolved: bool = False,
) -> pd.DataFrame:
    """Generate first-touch long/short labels without shortened horizons.

    If target and stop are both touched in the same OHLC candle, STOP wins
    conservatively because OHLC data cannot establish the intrabar sequence.
    The final horizon_bars rows do not have enough future observations;
    they are excluded by default or explicitly returned as UNRESOLVED.
    """
    _validate_input(df, horizon_bars, stop_atr, target_atr)

    rows: list[dict[str, object]] = []
    last_resolvable = len(df) - 1 - horizon_bars

    for i, timestamp in enumerate(df.index):
        if i > last_resolvable:
            if include_unresolved:
                rows.append(_unresolved_row(timestamp, horizon_bars))
            continue

        entry = float(df["close"].iloc[i])
        atr = float(df["atr_14"].iloc[i])
        if not pd.notna(atr) or atr <= 0 or not pd.notna(entry):
            continue

        long_stop = entry - atr * stop_atr
        long_target = entry + atr * target_atr
        short_stop = entry + atr * stop_atr
        short_target = entry - atr * target_atr
        end = i + horizon_bars

        long_result = _resolve_long(df, i, end, long_stop, long_target)
        short_result = _resolve_short(df, i, end, short_stop, short_target)
        rows.append(
            _resolved_row(
                timestamp,
                horizon_bars,
                entry,
                long_stop,
                long_result,
                short_stop,
                short_result,
            )
        )

    if not rows:
        return pd.DataFrame()

    labels = pd.DataFrame(rows).set_index("timestamp")
    return labels.reindex(
        columns=[
            "label_long_outcome",
            "label_short_outcome",
            "label_long_r",
            "label_short_r",
            "label_long_event_time",
            "label_short_event_time",
            "label_horizon_bars",
        ]
    )


def merge_event_labels(
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    """Attach labels by exact prediction timestamp without forward filling."""
    if labels.empty:
        return features.copy()
    return features.join(labels, how="left")
