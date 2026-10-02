"""Experiment evaluation bridge for ALFA OMEGA.

Connects a research hypothesis to the existing causal strategy-discovery
engine. It produces descriptive metrics only; promotion remains gated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from alfa_omega.research.experiment_runner import ExperimentResult, ExperimentSpec
from alfa_omega.research.strategy_discovery import StrategyCandidate, evaluate_candidate


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
) -> EvaluationSnapshot:
    """Evaluate a candidate on an explicitly supplied dataset.

    The caller is responsible for supplying the correct train/validation/OOS
    slice. No random splitting or future-data feature construction occurs.
    """
    metrics: dict[str, Any] = evaluate_candidate(df, candidate)
    return EvaluationSnapshot(
        experiment_id=spec.experiment_id,
        strategy_id=candidate.strategy_id,
        rows=len(df),
        trades=int(metrics["trades"]),
        win_rate=float(metrics["win_rate"]),
        expectancy_r=float(metrics["expectancy_r"]),
        profit_factor=float(metrics["profit_factor"]),
        wins=int(metrics.get("wins", 0)),
        losses=int(metrics.get("losses", 0)),
        time_exits=int(metrics.get("time_exits", 0)),
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
