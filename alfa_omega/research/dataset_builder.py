"""Versioned, leakage-resistant research dataset builder for ALFA OMEGA.

Research labels may use future information to describe the eventual outcome, but
those labels are never permitted to become prediction features. The builder is
strict about timestamp alignment, duplicate timestamps, and suspicious feature
names. It does not train models or execute trades.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class DatasetSpec:
    dataset_version: str
    market: str
    timeframe: str
    feature_columns: tuple[str, ...]
    label_columns: tuple[str, ...]
    horizon_bars: int
    stop_atr: float
    target_atr: float


_SUSPICIOUS_FEATURE_TOKENS = (
    "future",
    "target",
    "label",
    "outcome",
    "forward",
    "next_",
)


def _fingerprint_columns(columns: list[str]) -> str:
    payload = json.dumps(sorted(columns), separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _fingerprint_dataset(df: pd.DataFrame) -> str:
    if df.empty:
        return hashlib.sha256(b"EMPTY_DATASET").hexdigest()[:16]
    payload = pd.util.hash_pandas_object(df, index=True).values.tobytes()
    return hashlib.sha256(payload).hexdigest()[:16]


def _validate_index(df: pd.DataFrame, name: str) -> None:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError(f"{name} index must be DatetimeIndex")
    if df.index.has_duplicates:
        raise ValueError(f"{name} index contains duplicate timestamps")
    if df.index.tz is None:
        raise ValueError(f"{name} index must be timezone-aware")
    if str(df.index.tz) != "UTC":
        raise ValueError(f"{name} index must be normalized to UTC")
    if not df.index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be sorted ascending")


def build_research_dataset(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    market: str,
    timeframe: str,
    dataset_version: str = "v1",
    horizon_bars: int = 12,
    stop_atr: float = 1.0,
    target_atr: float = 2.0,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Join exact-timestamp labels and produce an auditable research manifest."""
    _validate_index(features, "features")
    _validate_index(labels, "labels")

    label_cols = [c for c in labels.columns if c.startswith("label_")]
    if not label_cols:
        raise ValueError("labels must contain label_* columns")

    feature_cols: list[str] = []
    rejected_columns: dict[str, str] = {}
    for column in features.columns:
        lowered = column.lower()
        if any(token in lowered for token in _SUSPICIOUS_FEATURE_TOKENS):
            rejected_columns[column] = "suspicious_future_or_label_token"
            continue
        feature_cols.append(column)

    if not feature_cols:
        raise ValueError("no causal feature columns remain after leakage audit")

    dataset = features[feature_cols].join(labels[label_cols], how="inner").sort_index()

    spec = DatasetSpec(
        dataset_version=dataset_version,
        market=market,
        timeframe=timeframe,
        feature_columns=tuple(feature_cols),
        label_columns=tuple(label_cols),
        horizon_bars=horizon_bars,
        stop_atr=stop_atr,
        target_atr=target_atr,
    )
    manifest = {
        "dataset": asdict(spec),
        "rows": int(len(dataset)),
        "feature_count": len(feature_cols),
        "label_count": len(label_cols),
        "feature_fingerprint": _fingerprint_columns(feature_cols),
        "dataset_fingerprint": _fingerprint_dataset(dataset),
        "time_start": dataset.index.min().isoformat() if len(dataset) else None,
        "time_end": dataset.index.max().isoformat() if len(dataset) else None,
        "exact_timestamp_join": True,
        "future_labels_are_not_features": True,
        "rejected_feature_columns": rejected_columns,
        "timezone": "UTC",
        "source_of_truth": "ALFA_OMEGA",
    }
    return dataset, manifest
