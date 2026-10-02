"""Research-generated indicator primitives.

The system may evolve indicators from existing causal features. Generated
indicators are expressions with provenance, not executable trading commands.
A generated indicator must be evaluated OOS and walk-forward before use.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IndicatorCandidate:
    indicator_id: str
    expression: str
    inputs: tuple[str, ...]
    transform: str


def safe_zscore(series: pd.Series, window: int = 50) -> pd.Series:
    mean = series.rolling(window, min_periods=window).mean()
    std = series.rolling(window, min_periods=window).std()
    return (series - mean) / std.replace(0, pd.NA)


def generate_indicator_candidates(
    df: pd.DataFrame,
    inputs: Sequence[str],
) -> list[IndicatorCandidate]:
    available = [c for c in inputs if c in df.columns]
    candidates: list[IndicatorCandidate] = []
    serial = 0

    for i, left in enumerate(available):
        for right in available[i + 1:]:
            serial += 1
            candidates.append(
                IndicatorCandidate(
                    indicator_id=f"GEN-IND-{serial:04d}",
                    expression=f"zscore({left}) - zscore({right})",
                    inputs=(left, right),
                    transform="difference_of_rolling_zscores",
                )
            )

    return candidates


def compute_indicator(
    df: pd.DataFrame,
    candidate: IndicatorCandidate,
    window: int = 50,
) -> pd.Series:
    left, right = candidate.inputs
    if left not in df.columns or right not in df.columns:
        raise ValueError("Indicator input is missing")
    return safe_zscore(df[left], window) - safe_zscore(df[right], window)
