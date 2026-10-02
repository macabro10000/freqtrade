"""Controlled experiment runner for ALFA OMEGA research.

This layer records the complete experiment contract so validation cannot
silently change barrier geometry or horizon parameters.
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
    horizon_bars: int
    stop_atr: float
    target_atr: float
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
    horizon_bars: int = 5,
    stop_atr: float = 1.0,
    target_atr: float = 2.0,
    validation_plan: Sequence[str] = (
        "STRICT_TEMPORAL_SPLIT",
        "PURGED_EMBARGO",
        "OUT_OF_SAMPLE",
        "WALK_FORWARD",
        "COST_AWARE",
        "REGIME_STRESS",
    ),
) -> ExperimentSpec:
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    if stop_atr <= 0 or target_atr <= 0:
        raise ValueError("barrier distances must be positive")

    payload = "|".join(
        [
            hypothesis.hypothesis_id,
            dataset_fingerprint,
            feature_version,
            label_version,
            str(horizon_bars),
            str(stop_atr),
            str(target_atr),
            *validation_plan,
        ]
    )
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
        horizon_bars=horizon_bars,
        stop_atr=stop_atr,
        target_atr=target_atr,
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
