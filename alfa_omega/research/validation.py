"""Leakage-resistant validation primitives for ALFA OMEGA.

Designed for financial time series where labels may depend on future bars.
Provides temporal splits, purging and embargo, plus a small feature leakage
audit. It is intentionally independent of model choice.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TimeInterval:
    start: pd.Timestamp
    end: pd.Timestamp


def label_intervals(
    index: pd.DatetimeIndex,
    horizon_bars: int,
) -> pd.DataFrame:
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError("index must be a DatetimeIndex")
    end = pd.Series(index, index=index).shift(-horizon_bars)
    return pd.DataFrame({"prediction_time": index, "label_end": end}, index=index)


def purged_train_mask(
    samples: pd.DataFrame,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    embargo: pd.Timedelta = pd.Timedelta(0),
) -> pd.Series:
    """Keep training labels whose information interval does not touch test."""
    if not {"prediction_time", "label_end"}.issubset(samples.columns):
        raise ValueError("samples requires prediction_time and label_end")

    prediction = pd.to_datetime(samples["prediction_time"], utc=True)
    label_end = pd.to_datetime(samples["label_end"], utc=True)
    ts = pd.Timestamp(test_start)
    te = pd.Timestamp(test_end) + embargo

    overlap = (prediction <= te) & (label_end >= ts)
    return ~overlap.fillna(True)


def temporal_train_test_split(
    samples: pd.DataFrame,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    embargo: pd.Timedelta = pd.Timedelta(0),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return train/test with overlapping training labels purged."""
    mask = purged_train_mask(samples, test_start, test_end, embargo)
    prediction = pd.to_datetime(samples["prediction_time"], utc=True)
    ts = pd.Timestamp(test_start)
    te = pd.Timestamp(test_end)
    test_mask = prediction.between(ts, te, inclusive="both")
    return samples.loc[mask], samples.loc[test_mask]


def audit_feature_names(feature_columns: list[str]) -> dict[str, object]:
    """Flag suspicious naming; this is a review aid, not a proof of safety."""
    suspicious_tokens = (
        "future",
        "forward",
        "target",
        "label",
        "outcome",
        "next_",
        "next-",
    )
    flagged = [
        column for column in feature_columns
        if any(token in column.lower() for token in suspicious_tokens)
    ]
    return {
        "ok": not flagged,
        "flagged_columns": flagged,
        "rule": "feature names suggesting future/label information require review",
    }
