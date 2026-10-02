"""Closed-loop research learning for ALFA OMEGA.

The learning loop learns from measured outcomes and explicit failure reasons.
It does not self-modify live trading code or enable live execution. New
strategies/indicators remain candidates until independently validated.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class ResearchError:
    experiment_id: str
    category: str
    message: str
    metric: float | None = None
    created_at: str = ""


@dataclass(frozen=True)
class LearningObservation:
    experiment_id: str
    strategy_id: str
    regime: str
    sample_size: int
    expectancy_r: float
    profit_factor: float
    max_drawdown: float
    oos_expectancy_r: float | None
    walk_forward_pass: bool
    failure_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchDecision:
    status: str
    reason: str
    next_action: str


def record_error(
    experiment_id: str,
    category: str,
    message: str,
    metric: float | None = None,
) -> ResearchError:
    return ResearchError(
        experiment_id=experiment_id,
        category=category,
        message=message,
        metric=metric,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def assess_observation(
    observation: LearningObservation,
    min_sample_size: int = 200,
) -> ResearchDecision:
    """Turn measured evidence into a research state, never a live order."""
    if observation.sample_size < min_sample_size:
        return ResearchDecision(
            "INSUFFICIENT_EVIDENCE",
            "Sample size below research threshold.",
            "Collect more data and repeat OOS/walk-forward validation.",
        )
    if observation.failure_categories:
        return ResearchDecision(
            "REJECT_AND_LEARN",
            "Observed failure modes require a new experiment.",
            "Modify features/labels/regime filters and rerun validation.",
        )
    if observation.oos_expectancy_r is None:
        return ResearchDecision(
            "OOS_REQUIRED",
            "Out-of-sample evidence is missing.",
            "Run strict temporal OOS validation.",
        )
    if not observation.walk_forward_pass:
        return ResearchDecision(
            "WALK_FORWARD_FAILED",
            "Walk-forward robustness gate failed.",
            "Change or discard the candidate and test again.",
        )
    if observation.oos_expectancy_r <= 0:
        return ResearchDecision(
            "OOS_FAILED",
            "Out-of-sample expectancy is non-positive.",
            "Search alternative features, regimes or strategy structure.",
        )
    return ResearchDecision(
        "CANDIDATE_FOR_PAPER",
        "Research gates passed; candidate may enter controlled paper evaluation.",
        "Paper-test with independent monitoring before any live consideration.",
    )


def summarize_failures(errors: Iterable[ResearchError]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for error in errors:
        counts[error.category] = counts.get(error.category, 0) + 1
    return counts


def to_dict(value: ResearchError | LearningObservation | ResearchDecision) -> dict[str, object]:
    return asdict(value)
