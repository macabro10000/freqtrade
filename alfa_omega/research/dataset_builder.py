"""Versioned research dataset builder for ALFA OMEGA.

Keeps causal features separate from future event labels and records provenance.
It does not train models or execute trades.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

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


def _fingerprint_columns(columns: list[str]) -> str:
    payload = json.dumps(sorted(columns), separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


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
    """Join exact-timestamp labels and audit the resulting research dataset."""
    if not isinstance(features.index, pd.DatetimeIndex):
        raise TypeError("features index must be DatetimeIndex")
    if not isinstance(labels.index, pd.DatetimeIndex):
        raise TypeError("labels index must be DatetimeIndex")

    label_cols = [c for c in labels.columns if c.startswith("label_")]
    if not label_cols:
        raise ValueError("labels must contain label_* columns")

    feature_cols = [
        c for c in features.columns
        if not c.startswith("label_")
        and not c.startswith("target_")
        and not c.startswith("future_")
        and not c.startswith("outcome_")
    ]

    dataset = features[feature_cols].join(labels[label_cols], how="inner")
    dataset = dataset.sort_index()

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
        "time_start": dataset.index.min().isoformat() if len(dataset) else None,
        "time_end": dataset.index.max().isoformat() if len(dataset) else None,
        "exact_timestamp_join": True,
        "future_labels_are_not_features": True,
        "source_of_truth": "ALFA_OMEGA",
    }
    return dataset, manifest
