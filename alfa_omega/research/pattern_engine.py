"""Causal pattern discovery for ALFA OMEGA.

Patterns are statistical state descriptions, not hand-waved chart names.
The engine records recurrence and forward outcomes so the model can later
learn which states matter across markets and regimes.
"""

from __future__ import annotations

import hashlib
from typing import Sequence

import pandas as pd


DEFAULT_PATTERN_COLUMNS: tuple[str, ...] = (
    "trend_bias",
    "structure_bias",
    "breakout_high_20",
    "breakdown_low_20",
    "liquidity_sweep_high",
    "liquidity_sweep_low",
    "fvg_bullish_smc",
    "fvg_bearish_smc",
    "range_expansion",
)


def pattern_key(row: pd.Series, columns: Sequence[str]) -> str:
    values = []
    for column in columns:
        value = row.get(column, 0)
        if pd.isna(value):
            value = 0
        values.append(f"{column}={int(value) if isinstance(value, (int, float)) else value}")
    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def encode_patterns(
    df: pd.DataFrame,
    columns: Sequence[str] = DEFAULT_PATTERN_COLUMNS,
) -> pd.DataFrame:
    out = df.copy()
    available = [c for c in columns if c in out.columns]
    if not available:
        raise ValueError("No pattern columns are available")
    out["market_pattern_id"] = out.apply(
        lambda row: pattern_key(row, available),
        axis=1,
    )
    return out


def pattern_statistics(
    df: pd.DataFrame,
    outcome_column: str = "label_long_r",
) -> pd.DataFrame:
    if "market_pattern_id" not in df.columns:
        df = encode_patterns(df)
    if outcome_column not in df.columns:
        raise ValueError(f"Missing outcome column: {outcome_column}")

    grouped = df.groupby("market_pattern_id", dropna=False)[outcome_column]
    stats = grouped.agg(
        occurrences="count",
        mean_r="mean",
        median_r="median",
        std_r="std",
    )
    stats["positive_rate"] = grouped.apply(lambda s: float((s > 0).mean()))
    return stats.reset_index()
