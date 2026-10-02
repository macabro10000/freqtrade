"""Walk-forward validation for ALFA OMEGA.

Uses chronological expanding windows. Each fold has a strictly earlier training
period and a later test period; samples whose label interval reaches the test
boundary are purged, followed by an explicit embargo. No shuffling occurs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import pandas as pd

from alfa_omega.research.event_labels import EventLabelArtifact, build_event_label_artifact

from alfa_omega.research.experiment_evaluator import evaluate_experiment
from alfa_omega.research.experiment_runner import ExperimentResult, ExperimentSpec
from alfa_omega.research.strategy_discovery import StrategyCandidate
from alfa_omega.research.validation import audit_feature_names, label_intervals


@dataclass(frozen=True)
class WalkForwardFold:
    fold: int
    train_start: str
    train_end: str | None
    test_start: str
    test_end: str
    train_rows: int
    test_rows: int
    trades: int
    expectancy_r: float
    win_rate: float
    profit_factor: float


@dataclass(frozen=True)
class WalkForwardResult:
    experiment_id: str
    status: str
    folds: tuple[WalkForwardFold, ...]
    folds_evaluated: int
    positive_expectancy_folds: int
    total_test_trades: int
    mean_test_expectancy_r: float
    mean_test_win_rate: float
    min_test_expectancy_r: float
    feature_audit_ok: bool
    flagged_features: tuple[str, ...]
    notes: tuple[str, ...] = ()


def _validate_frame(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("walk-forward dataset is empty")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("walk-forward dataset requires DatetimeIndex")
    if df.index.tz is None:
        raise ValueError("walk-forward index must be timezone-aware")
    if not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("walk-forward index must be sorted and unique")


def _fold_bounds(
    n_rows: int,
    *,
    n_splits: int,
    test_size: int,
    min_train_size: int,
) -> list[tuple[int, int, int]]:
    if n_splits < 2:
        raise ValueError("n_splits must be >= 2")
    if test_size < 1:
        raise ValueError("test_size must be >= 1")
    if min_train_size < 1:
        raise ValueError("min_train_size must be >= 1")

    bounds: list[tuple[int, int, int]] = []
    first_test_start = n_rows - n_splits * test_size
    if first_test_start < min_train_size:
        raise ValueError(
            "dataset is too small for requested n_splits/test_size/min_train_size"
        )

    for fold in range(n_splits):
        test_start = first_test_start + fold * test_size
        test_end = min(test_start + test_size, n_rows)
        if test_end <= test_start:
            continue
        bounds.append((fold + 1, test_start, test_end))
    return bounds


def walk_forward_validate(
    spec: ExperimentSpec,
    df: pd.DataFrame,
    candidate: StrategyCandidate,
    *,
    n_splits: int = 5,
    test_size: int | None = None,
    min_train_size: int | None = None,
    embargo_bars: int | None = None,
    event_labels: EventLabelArtifact | None = None,
) -> WalkForwardResult:
    """Run expanding-window walk-forward evaluation.

    The final chronological blocks are reserved as successive OOS folds.
    Training never contains observations at or after a fold's test start.
    """
    _validate_frame(df)
    audit = audit_feature_names(list(df.columns))

    horizon = max(1, int(candidate.horizon_bars))
    if test_size is None:
        test_size = max(1, len(df) // (n_splits + 2))
    if min_train_size is None:
        min_train_size = max(horizon + 1, len(df) // 3)
    embargo = max(0, embargo_bars if embargo_bars is not None else horizon)

    if event_labels is None:
        event_labels = build_event_label_artifact(
            df,
            horizon_bars=candidate.horizon_bars,
            stop_atr=candidate.stop_atr,
            target_atr=candidate.target_atr,
        )

    bounds = _fold_bounds(
        len(df),
        n_splits=n_splits,
        test_size=test_size,
        min_train_size=min_train_size,
    )

    intervals = label_intervals(df.index, horizon)
    folds: list[WalkForwardFold] = []
    notes = [
        "EXPANDING_WINDOW walk-forward applied",
        f"PURGE horizon_bars={horizon}",
        f"EMBARGO embargo_bars={embargo}",
    ]

    for fold_no, test_start_pos, test_end_pos in bounds:
        test_start = df.index[test_start_pos]
        test_end = df.index[test_end_pos - 1]

        # Strictly before the test block. Then purge any training event whose
        # label can reach the boundary, and apply the embargo.
        train_candidates = intervals.index < test_start
        purge_boundary_pos = max(0, test_start_pos - embargo)
        purge_boundary = df.index[purge_boundary_pos]

        train_mask = (
            train_candidates
            & intervals["label_end"].notna()
            & (pd.to_datetime(intervals["label_end"], utc=True) < purge_boundary)
        )

        train_index = intervals.index[train_mask]
        test_index = intervals.index[
            (intervals.index >= test_start) & (intervals.index <= test_end)
        ]

        # Respect the expanding training origin while retaining all valid
        # earlier observations.
        if len(train_index) < min_train_size:
            notes.append(f"fold {fold_no}: insufficient post-purge training rows")
            continue

        train_df = df.loc[train_index]
        test_df = df.loc[test_index]
        snapshot = evaluate_experiment(
            spec, test_df, candidate, event_labels=event_labels
        )

        folds.append(
            WalkForwardFold(
                fold=fold_no,
                train_start=train_df.index[0].isoformat(),
                train_end=train_df.index[-1].isoformat(),
                test_start=test_start.isoformat(),
                test_end=test_end.isoformat(),
                train_rows=len(train_df),
                test_rows=len(test_df),
                trades=snapshot.trades,
                expectancy_r=snapshot.expectancy_r,
                win_rate=snapshot.win_rate,
                profit_factor=snapshot.profit_factor,
            )
        )

    if not folds:
        raise ValueError("no walk-forward folds could be evaluated")

    expectancy = [fold.expectancy_r for fold in folds]
    win_rates = [fold.win_rate for fold in folds]
    total_trades = sum(fold.trades for fold in folds)
    positive = sum(value > 0 for value in expectancy)

    if total_trades == 0:
        status = "WF_INSUFFICIENT_TRADES"
        notes.append("no test trades were produced across walk-forward folds")
    elif positive == len(folds):
        status = "WF_ALL_FOLDS_POSITIVE"
    elif positive >= (len(folds) + 1) // 2:
        status = "WF_MIXED"
        notes.append("not every OOS fold has positive expectancy")
    else:
        status = "WF_FAILED"
        notes.append("fewer than half of evaluated folds have positive expectancy")

    if not audit["ok"]:
        notes.append("feature-name audit flagged columns for review")

    return WalkForwardResult(
        experiment_id=spec.experiment_id,
        status=status,
        folds=tuple(folds),
        folds_evaluated=len(folds),
        positive_expectancy_folds=positive,
        total_test_trades=total_trades,
        mean_test_expectancy_r=float(sum(expectancy) / len(expectancy)),
        mean_test_win_rate=float(sum(win_rates) / len(win_rates)),
        min_test_expectancy_r=float(min(expectancy)),
        feature_audit_ok=bool(audit["ok"]),
        flagged_features=tuple(audit["flagged_columns"]),
        notes=tuple(notes),
    )


def walk_forward_to_result(value: WalkForwardResult) -> ExperimentResult:
    metrics = {
        "folds_evaluated": float(value.folds_evaluated),
        "positive_expectancy_folds": float(value.positive_expectancy_folds),
        "total_test_trades": float(value.total_test_trades),
        "mean_test_expectancy_r": value.mean_test_expectancy_r,
        "mean_test_win_rate": value.mean_test_win_rate,
        "min_test_expectancy_r": value.min_test_expectancy_r,
    }
    return ExperimentResult(
        experiment_id=value.experiment_id,
        status=value.status,
        metrics=tuple(sorted(metrics.items())),
        notes=value.notes,
    )


def walk_forward_to_dict(value: WalkForwardResult) -> dict[str, object]:
    return asdict(value)
