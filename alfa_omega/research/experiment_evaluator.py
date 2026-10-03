"""Experiment evaluation bridge for ALFA OMEGA.

Connects a research hypothesis to the existing causal strategy-discovery
engine. It produces descriptive metrics only; promotion remains gated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from alfa_omega.research.event_labels import EventLabelArtifact, build_event_label_artifact
from alfa_omega.research.experiment_runner import ExperimentResult, ExperimentSpec
from alfa_omega.research.strategy_discovery import StrategyCandidate


@dataclass(frozen=True)
class EvaluationSnapshot:
    experiment_id: str
    strategy_id: str
    rows: int
    trades: int
    win_rate: float
    expectancy_r: float
    profit_factor: float
    wins: int
    losses: int
    time_exits: int


def evaluate_experiment(
    spec: ExperimentSpec,
    df: pd.DataFrame,
    candidate: StrategyCandidate,
    *,
    event_labels: EventLabelArtifact | None = None,
) -> EvaluationSnapshot:
    """Evaluate using exact timestamps from a shared event-label artifact."""
    if event_labels is None:
        event_labels = build_event_label_artifact(
            df,
            horizon_bars=candidate.horizon_bars,
            stop_atr=candidate.stop_atr,
            target_atr=candidate.target_atr,
        )
    if (
        event_labels.horizon_bars != candidate.horizon_bars
        or event_labels.stop_atr != candidate.stop_atr
        or event_labels.target_atr != candidate.target_atr
    ):
        raise ValueError("event label artifact does not match candidate barriers")

    mask = pd.Series(True, index=df.index)
    for condition in candidate.long_conditions:
        if condition not in df.columns:
            raise KeyError(f"Unknown feature condition: {condition}")
        series = df[condition]
        if pd.api.types.is_bool_dtype(series):
            mask &= series.fillna(False)
        elif pd.api.types.is_numeric_dtype(series):
            mask &= series.fillna(0) > 0
        else:
            raise TypeError(f"Condition must be boolean/numeric: {condition}")

    labels = event_labels.for_timestamps(df.index[mask.fillna(False)])
    labels = labels.loc[labels["label_long_outcome"].notna()]
    r = pd.to_numeric(labels["label_long_r"], errors="coerce").dropna()

    if r.empty:
        metrics: dict[str, Any] = {
            "trades": 0,
            "win_rate": 0.0,
            "expectancy_r": 0.0,
            "profit_factor": 0.0,
            "wins": 0,
            "losses": 0,
            "time_exits": 0,
        }
    else:
        wins = labels["label_long_outcome"].eq("TARGET")
        losses = labels["label_long_outcome"].eq("STOP")
        gross_profit = float(r.where(r > 0, 0).sum())
        gross_loss = float(-r.where(r < 0, 0).sum())
        metrics = {
            "trades": len(r),
            "win_rate": float(wins.loc[r.index].mean()),
            "expectancy_r": float(r.mean()),
            "profit_factor": (
                gross_profit / gross_loss if gross_loss > 0 else float("inf")
            ),
            "wins": int(wins.loc[r.index].sum()),
            "losses": int(losses.loc[r.index].sum()),
            "time_exits": int(labels["label_long_outcome"].eq("TIME").sum()),
        }

    return EvaluationSnapshot(
        experiment_id=spec.experiment_id,
        strategy_id=candidate.strategy_id,
        rows=len(df),
        trades=int(metrics["trades"]),
        win_rate=float(metrics["win_rate"]),
        expectancy_r=float(metrics["expectancy_r"]),
        profit_factor=float(metrics["profit_factor"]),
        wins=int(metrics["wins"]),
        losses=int(metrics["losses"]),
        time_exits=int(metrics["time_exits"]),
    )

def snapshot_to_result(
    snapshot: EvaluationSnapshot,
    *,
    status: str = "EVALUATED",
) -> ExperimentResult:
    metrics = {
        "rows": float(snapshot.rows),
        "trades": float(snapshot.trades),
        "win_rate": snapshot.win_rate,
        "expectancy_r": snapshot.expectancy_r,
        "profit_factor": snapshot.profit_factor,
        "wins": float(snapshot.wins),
        "losses": float(snapshot.losses),
        "time_exits": float(snapshot.time_exits),
    }
    return ExperimentResult(
        experiment_id=snapshot.experiment_id,
        status=status,
        metrics=tuple(sorted(metrics.items())),
    )


def evaluation_to_dict(
    snapshot: EvaluationSnapshot,
) -> dict[str, object]:
    return asdict(snapshot)
