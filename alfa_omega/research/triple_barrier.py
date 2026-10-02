"""Causal event-based labels for ALFA OMEGA.

The label is determined by the first barrier touched after entry: target,
stop, or time horizon. Future bars are labels only and must never be exposed
as model features at the prediction timestamp.
"""

from __future__ import annotations

import pandas as pd


def triple_barrier_labels(
    df: pd.DataFrame,
    *,
    horizon_bars: int = 12,
    stop_atr: float = 1.0,
    target_atr: float = 2.0,
    include_unresolved: bool = False,
) -> pd.DataFrame:
    """Generate long/short first-touch outcomes from candle OHLC.

    Conservative ambiguity rule: if target and stop are both touched inside
    the same candle, the stop is assumed to have occurred first. This avoids
    granting the label information unavailable from OHLC alone.
    """
    required = {"open", "high", "low", "close", "atr_14"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    if stop_atr <= 0 or target_atr <= 0:
        raise ValueError("barrier distances must be positive")

    out = df.copy()
    index = out.index
    rows: list[dict[str, object]] = []

    for i, timestamp in enumerate(index):
        if i + 1 >= len(out):
            continue
        entry = float(out["close"].iloc[i])
        atr = float(out["atr_14"].iloc[i])
        if not pd.notna(atr) or atr <= 0 or not pd.notna(entry):
            continue

        long_stop = entry - atr * stop_atr
        long_target = entry + atr * target_atr
        short_stop = entry + atr * stop_atr
        short_target = entry - atr * target_atr

        end = min(i + horizon_bars, len(out) - 1)
        outcome_long = "TIME"
        outcome_short = "TIME"
        long_exit = float(out["close"].iloc[end])
        short_exit = long_exit
        long_event = index[end]
        short_event = index[end]

        for j in range(i + 1, end + 1):
            high = float(out["high"].iloc[j])
            low = float(out["low"].iloc[j])
            if not pd.notna(high) or not pd.notna(low):
                continue

            if low <= long_stop and high >= long_target:
                outcome_long = "STOP"
                long_exit = long_stop
                long_event = index[j]
                break
            if low <= long_stop:
                outcome_long = "STOP"
                long_exit = long_stop
                long_event = index[j]
                break
            if high >= long_target:
                outcome_long = "TARGET"
                long_exit = long_target
                long_event = index[j]
                break

        for j in range(i + 1, end + 1):
            high = float(out["high"].iloc[j])
            low = float(out["low"].iloc[j])
            if not pd.notna(high) or not pd.notna(low):
                continue

            if low <= short_target and high >= short_stop:
                outcome_short = "STOP"
                short_exit = short_stop
                short_event = index[j]
                break
            if high >= short_stop:
                outcome_short = "STOP"
                short_exit = short_stop
                short_event = index[j]
                break
            if low <= short_target:
                outcome_short = "TARGET"
                short_exit = short_target
                short_event = index[j]
                break

        long_r = (long_exit - entry) / (entry - long_stop)
        short_r = (entry - short_exit) / (short_stop - entry)

        if outcome_long == "TIME":
            long_r = (long_exit - entry) / (entry - long_stop)
        if outcome_short == "TIME":
            short_r = (entry - short_exit) / (short_stop - entry)

        rows.append(
            {
                "timestamp": timestamp,
                "label_long_outcome": outcome_long,
                "label_short_outcome": outcome_short,
                "label_long_r": long_r,
                "label_short_r": short_r,
                "label_long_event_time": long_event,
                "label_short_event_time": short_event,
                "label_horizon_bars": end - i,
            }
        )

    labels = pd.DataFrame(rows).set_index("timestamp") if rows else pd.DataFrame()
    if labels.empty:
        return labels

    if not include_unresolved:
        # TIME is a valid outcome; only rows that could not be evaluated are absent.
        pass
    return labels.reindex(index)


def merge_event_labels(
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    """Attach labels by exact prediction timestamp without forward filling."""
    if labels.empty:
        return features.copy()
    return features.join(labels, how="left")
