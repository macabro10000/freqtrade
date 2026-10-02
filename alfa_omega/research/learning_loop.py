"""Closed-loop research learning for ALFA OMEGA.

The learning loop learns from measured outcomes and explicit failure reasons.
It does not self-modify live trading code or enable live execution. New
strategies/indicators remain candidates until independently validated.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime


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
class ExperienceRecord:
    """Immutable market/trade experience retained for future research."""
    experience_id: str
    timestamp: str
    market: str
    timeframe: str
    regime: str
    decision: str
    pattern_ids: tuple[str, ...]
    feature_snapshot: tuple[tuple[str, float], ...]
    expected_r: float | None
    realized_r: float | None
    outcome: str
    error_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternLesson:
    pattern_key: str
    occurrences: int
    wins: int
    losses: int
    expectancy_r: float
    failure_categories: tuple[str, ...] = ()


def build_experience_record(
    *,
    experience_id: str,
    market: str,
    timeframe: str,
    regime: str,
    decision: str,
    pattern_ids: Sequence[str],
    feature_snapshot: dict[str, float],
    expected_r: float | None,
    realized_r: float | None,
    outcome: str,
    error_categories: Sequence[str] = (),
    timestamp: str | None = None,
) -> ExperienceRecord:
    """Create normalized immutable experience; it never changes execution policy."""
    return ExperienceRecord(
        experience_id=experience_id,
        timestamp=timestamp or datetime.now(UTC).isoformat(),
        market=market,
        timeframe=timeframe,
        regime=regime,
        decision=decision,
        pattern_ids=tuple(pattern_ids),
        feature_snapshot=tuple(
            sorted(
                (str(k), float(v))
                for k, v in feature_snapshot.items()
                if v is not None
            )
        ),
        expected_r=expected_r,
        realized_r=realized_r,
        outcome=outcome,
        error_categories=tuple(error_categories),
    )


def learn_pattern_lessons(records: Iterable[ExperienceRecord]) -> list[PatternLesson]:
    """Aggregate outcomes into research lessons; no automatic promotion."""
    buckets: dict[str, list[ExperienceRecord]] = {}
    for record in records:
        for pattern in record.pattern_ids:
            buckets.setdefault(pattern, []).append(record)
    lessons: list[PatternLesson] = []
    for pattern, items in buckets.items():
        realized = [r.realized_r for r in items if r.realized_r is not None]
        wins = sum(1 for r in items if r.realized_r is not None and r.realized_r > 0)
        losses = sum(1 for r in items if r.realized_r is not None and r.realized_r < 0)
        failures = sorted({category for r in items for category in r.error_categories})
        lessons.append(PatternLesson(
            pattern_key=pattern,
            occurrences=len(items),
            wins=wins,
            losses=losses,
            expectancy_r=float(sum(realized) / len(realized)) if realized else 0.0,
            failure_categories=tuple(failures),
        ))
    return sorted(lessons, key=lambda x: (x.expectancy_r, x.occurrences), reverse=True)


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
        created_at=datetime.now(UTC).isoformat(),
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


def to_dict(
    value: ResearchError
    | LearningObservation
    | ResearchDecision
    | ExperienceRecord
    | PatternLesson,
) -> dict[str, object]:
    return asdict(value)
