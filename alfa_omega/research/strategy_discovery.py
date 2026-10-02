"""Strategy discovery primitives for ALFA OMEGA.

This module does not place orders. It creates candidate strategies from
measurable market conditions, evaluates them with causal forward outcomes,
and keeps the search space explicit so candidates can later be validated by
OOS and walk-forward tests.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class StrategyCandidate:
    strategy_id: str
    long_conditions: tuple[str, ...]
    short_conditions: tuple[str, ...]
    horizon_bars: int
    stop_atr: float
    target_atr: float


def _future_extrema(df: pd.DataFrame, horizon: int) -> tuple[pd.Series, pd.Series]:
    future_high = pd.concat(
        [df["high"].shift(-i) for i in range(1, horizon + 1)], axis=1
    ).max(axis=1)
    future_low = pd.concat(
        [df["low"].shift(-i) for i in range(1, horizon + 1)], axis=1
    ).min(axis=1)
    return future_high, future_low


def label_forward_outcomes(
    df: pd.DataFrame,
    horizon_bars: int = 12,
    stop_atr: float = 1.0,
    target_atr: float = 2.0,
) -> pd.DataFrame:
    """Create research labels from future prices.

    Labels are for training/evaluation only and must never be features at the
    same timestamp. The function deliberately uses shifted future rows.
    """
    required = {"high", "low", "close", "atr_14"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    out = df.copy()
    future_high, future_low = _future_extrema(out, horizon_bars)
    entry = out["close"]
    risk = out["atr_14"] * stop_atr
    reward = out["atr_14"] * target_atr

    out["label_long_target"] = (future_high >= entry + reward).astype("Int64")
    out["label_long_stop"] = (future_low <= entry - risk).astype("Int64")
    out["label_short_target"] = (future_low <= entry - reward).astype("Int64")
    out["label_short_stop"] = (future_high >= entry + risk).astype("Int64")

    out["label_long_r"] = (
        (future_high - entry) / risk.replace(0, pd.NA)
    )
    out["label_short_r"] = (
        (entry - future_low) / risk.replace(0, pd.NA)
    )
    return out


def _condition_mask(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df.columns:
        raise KeyError(f"Unknown feature condition: {name}")
    series = df[name]
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0) > 0
    raise TypeError(f"Condition must be boolean/numeric: {name}")


def discover_candidates(
    df: pd.DataFrame,
    conditions: Iterable[str],
    max_conditions: int = 3,
    horizon_bars: int = 12,
) -> list[StrategyCandidate]:
    """Generate small, interpretable candidate rule sets.

    This is discovery, not acceptance. Every candidate must later pass
    validation, OOS and walk-forward gates.
    """
    names = [name for name in conditions if name in df.columns]
    candidates: list[StrategyCandidate] = []
    serial = 0

    for size in range(1, max_conditions + 1):
        for combo in combinations(names, size):
            serial += 1
            sid = f"DISC-{serial:05d}"
            candidates.append(
                StrategyCandidate(
                    strategy_id=sid,
                    long_conditions=tuple(combo),
                    short_conditions=tuple(),
                    horizon_bars=horizon_bars,
                    stop_atr=1.0,
                    target_atr=2.0,
                )
            )
    return candidates


def evaluate_candidate(
    df: pd.DataFrame,
    candidate: StrategyCandidate,
) -> dict[str, float | int | str]:
    """Evaluate a candidate on causal entry conditions.

    Future outcomes are only used as labels/evaluation targets. No acceptance
    decision is made here.
    """
    mask = pd.Series(True, index=df.index)
    for condition in candidate.long_conditions:
        mask &= _condition_mask(df, condition)

    sample = df.loc[mask]
    if sample.empty:
        return {
            "strategy_id": candidate.strategy_id,
            "trades": 0,
            "win_rate": 0.0,
            "expectancy_r": 0.0,
            "profit_factor": 0.0,
        }

    labeled = label_forward_outcomes(
        df,
        horizon_bars=candidate.horizon_bars,
        stop_atr=candidate.stop_atr,
        target_atr=candidate.target_atr,
    ).loc[sample.index]

    wins = (labeled["label_long_target"] == 1) & (labeled["label_long_stop"] == 0)
    losses = (labeled["label_long_stop"] == 1) & (labeled["label_long_target"] == 0)
    r = labeled["label_long_r"].clip(-candidate.stop_atr, candidate.target_atr)

    gross_profit = float(r.where(r > 0, 0).sum())
    gross_loss = float(-r.where(r < 0, 0).sum())

    return {
        "strategy_id": candidate.strategy_id,
        "trades": int(len(labeled)),
        "win_rate": float(wins.mean()),
        "expectancy_r": float(r.mean()),
        "profit_factor": (
            gross_profit / gross_loss if gross_loss > 0 else float("inf")
        ),
        "wins": int(wins.sum()),
        "losses": int(losses.sum()),
    }


def candidate_to_dict(candidate: StrategyCandidate) -> dict[str, object]:
    return asdict(candidate)
