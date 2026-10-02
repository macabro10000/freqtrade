"""Controlled experiment runner for ALFA OMEGA research.

This layer orchestrates hypothesis evaluation without trading or self-modifying
production code. It records the experiment contract and delegates actual
backtest/validation work to explicit research components.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Mapping, Sequence

from alfa_omega.research.hypothesis_factory import ResearchHypothesis


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    hypothesis_id: str
    market: str
    timeframe: str
    regime: str
    dataset_fingerprint: str
    feature_version: str
    label_version: str
    validation_plan: tuple[str, ...]
    status: str = "PLANNED"


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: str
    status: str
    metrics: tuple[tuple[str, float], ...]
    notes: tuple[str, ...] = ()


def build_experiment(
    hypothesis: ResearchHypothesis,
    *,
    dataset_fingerprint: str,
    feature_version: str,
    label_version: str,
    validation_plan: Sequence[str] = (
        "STRICT_TEMPORAL_SPLIT",
        "PURGED_EMBARGO",
        "OUT_OF_SAMPLE",
        "WALK_FORWARD",
        "COST_AWARE",
        "REGIME_STRESS",
    ),
) -> ExperimentSpec:
    payload = "|".join([
        hypothesis.hypothesis_id,
        dataset_fingerprint,
        feature_version,
        label_version,
        *validation_plan,
    ])
    experiment_id = "EXP-" + sha256(payload.encode("utf-8")).hexdigest()[:12].upper()
    return ExperimentSpec(
        experiment_id=experiment_id,
        hypothesis_id=hypothesis.hypothesis_id,
        market=hypothesis.market,
        timeframe=hypothesis.timeframe,
        regime=hypothesis.regime,
        dataset_fingerprint=dataset_fingerprint,
        feature_version=feature_version,
        label_version=label_version,
        validation_plan=tuple(validation_plan),
    )


def record_experiment_result(
    spec: ExperimentSpec,
    *,
    status: str,
    metrics: Mapping[str, float],
    notes: Sequence[str] = (),
) -> ExperimentResult:
    return ExperimentResult(
        experiment_id=spec.experiment_id,
        status=status,
        metrics=tuple(sorted((str(k), float(v)) for k, v in metrics.items())),
        notes=tuple(notes),
    )


def experiment_to_dict(
    value: ExperimentSpec | ExperimentResult,
) -> dict[str, object]:
    return asdict(value)
