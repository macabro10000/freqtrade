"""Leakage-resistant experiment validation for ALFA OMEGA.

Runs a deterministic chronological train/OOS evaluation for a research
candidate. It never trains models or executes orders.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import pandas as pd

from alfa_omega.research.experiment_evaluator import evaluate_experiment
from alfa_omega.research.experiment_runner import ExperimentResult, ExperimentSpec
from alfa_omega.research.strategy_discovery import StrategyCandidate
from alfa_omega.research.validation import (
    audit_feature_names,
    label_intervals,
    temporal_train_test_split,
)


@dataclass(frozen=True)
class ValidationResult:
    experiment_id: str
    status: str
    train_rows: int
    test_rows: int
    train_trades: int
    test_trades: int
    train_expectancy_r: float
    test_expectancy_r: float
    train_win_rate: float
    test_win_rate: float
    test_profit_factor: float
    feature_audit_ok: bool
    flagged_features: tuple[str, ...]
    notes: tuple[str, ...] = ()


def _timeframe_delta(index: pd.DatetimeIndex) -> pd.Timedelta:
    if len(index) < 2:
        raise ValueError("validation requires at least two timestamps")
    deltas = index.to_series().diff().dropna()
    delta = deltas.median()
    if pd.isna(delta) or delta <= pd.Timedelta(0):
        raise ValueError("could not infer a positive timeframe interval")
    return pd.Timedelta(delta)


def validate_experiment(
    spec: ExperimentSpec,
    df: pd.DataFrame,
    candidate: StrategyCandidate,
    *,
    test_fraction: float = 0.20,
    embargo_bars: int | None = None,
) -> ValidationResult:
    """Evaluate train/OOS chronologically with purge + embargo.

    The final chronological block is OOS. Training rows whose label interval
    touches the OOS window (plus embargo) are removed before evaluation.
    """
    if not 0.05 <= test_fraction < 0.50:
        raise ValueError("test_fraction must be in [0.05, 0.50)")
    if df.empty:
        raise ValueError("validation dataset is empty")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("validation dataset requires DatetimeIndex")
    if not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("validation index must be sorted and unique")
    if df.index.tz is None:
        raise ValueError("validation index must be timezone-aware")

    audit = audit_feature_names(list(df.columns))
    delta = _timeframe_delta(df.index)
    horizon = max(1, int(candidate.horizon_bars))
    purge_bars = horizon
    embargo = max(0, embargo_bars if embargo_bars is not None else horizon)
    test_start_pos = max(1, int(len(df) * (1.0 - test_fraction)))
    test_start = df.index[test_start_pos]
    test_end = df.index[-1]

    intervals = label_intervals(df.index, horizon)
    samples = intervals.join(df, how="left")
    train, test = temporal_train_test_split(
        samples,
        test_start=test_start,
        test_end=test_end,
        embargo=delta * embargo,
    )

    # Keep only timestamps that belong to the original feature frame.
    train_df = df.loc[df.index.intersection(train.index)]
    test_df = df.loc[df.index.intersection(test.index)]

    train_snapshot = evaluate_experiment(spec, train_df, candidate)
    test_snapshot = evaluate_experiment(spec, test_df, candidate)

    notes: list[str] = [
        "STRICT_TEMPORAL_SPLIT applied",
        f"PURGED_EMBARGO applied: horizon_bars={purge_bars}, embargo_bars={embargo}",
        "OOS is the final chronological block",
    ]
    if not audit["ok"]:
        notes.append("feature-name audit flagged columns for review")

    status = "OOS_EVALUATED"
    if test_snapshot.trades == 0:
        status = "OOS_INSUFFICIENT_TRADES"
        notes.append("OOS contains no evaluated candidate trades")
    elif test_snapshot.expectancy_r <= 0:
        status = "OOS_FAILED_EXPECTANCY"
        notes.append("OOS expectancy is non-positive")

    return ValidationResult(
        experiment_id=spec.experiment_id,
        status=status,
        train_rows=len(train_df),
        test_rows=len(test_df),
        train_trades=train_snapshot.trades,
        test_trades=test_snapshot.trades,
        train_expectancy_r=train_snapshot.expectancy_r,
        test_expectancy_r=test_snapshot.expectancy_r,
        train_win_rate=train_snapshot.win_rate,
        test_win_rate=test_snapshot.win_rate,
        test_profit_factor=test_snapshot.profit_factor,
        feature_audit_ok=bool(audit["ok"]),
        flagged_features=tuple(audit["flagged_columns"]),
        notes=tuple(notes),
    )


def validation_to_result(
    value: ValidationResult,
) -> ExperimentResult:
    metrics = {
        "train_rows": float(value.train_rows),
        "test_rows": float(value.test_rows),
        "train_trades": float(value.train_trades),
        "test_trades": float(value.test_trades),
        "train_expectancy_r": value.train_expectancy_r,
        "test_expectancy_r": value.test_expectancy_r,
        "train_win_rate": value.train_win_rate,
        "test_win_rate": value.test_win_rate,
        "test_profit_factor": value.test_profit_factor,
    }
    return ExperimentResult(
        experiment_id=value.experiment_id,
        status=value.status,
        metrics=tuple(sorted(metrics.items())),
        notes=value.notes,
    )


def validation_to_dict(value: ValidationResult) -> dict[str, object]:
    return asdict(value)
