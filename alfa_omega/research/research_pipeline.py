"""Coordinate the existing research validation layers.

This module is deliberately orchestration-only: it does not place orders,
change live configuration, or promote a candidate without the research gate.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alfa_omega.research.candidate_bridge import ResearchCandidate
from alfa_omega.research.cost_aware import (
    CostAwareResult,
    ExecutionCostModel,
    evaluate_costs,
)
from alfa_omega.research.experiment_evaluator import evaluate_experiment
from alfa_omega.research.experiment_runner import ExperimentSpec
from alfa_omega.research.regime_stress import evaluate_regime_stress
from alfa_omega.research.research_policy import (
    ResearchGate,
    classify_research_candidate,
)
from alfa_omega.research.strategy_discovery import (
    StrategyCandidate,
    triple_barrier_labels,
)
from alfa_omega.research.validation_engine import ValidationResult, validate_experiment
from alfa_omega.research.walk_forward import WalkForwardResult, walk_forward_validate


@dataclass(frozen=True)
class ResearchPipelineResult:
    candidate_id: str
    validation: ValidationResult
    walk_forward: WalkForwardResult
    cost_aware: CostAwareResult
    regime_status: str
    final_state: str


def _strategy_candidate(candidate: ResearchCandidate) -> StrategyCandidate:
    return StrategyCandidate(
        strategy_id=candidate.hypothesis_id,
        long_conditions=candidate.conditions,
        short_conditions=(),
        horizon_bars=5,
        stop_atr=1.0,
        target_atr=2.0,
    )


def _condition_mask(
    frame: pd.DataFrame,
    candidate: StrategyCandidate,
) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for name in candidate.long_conditions:
        if name not in frame.columns:
            raise KeyError(f"Unknown candidate condition: {name}")
        series = frame[name]
        if pd.api.types.is_bool_dtype(series):
            mask &= series.fillna(False)
        elif pd.api.types.is_numeric_dtype(series):
            mask &= series.fillna(0) > 0
        else:
            raise TypeError(f"Candidate condition must be boolean/numeric: {name}")
    return mask


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    if session == "OFF_SESSION":
        if "session_primary" not in frame.columns:
            return pd.Series(True, index=frame.index)
        return frame["session_primary"].eq("OFF_SESSION")
    if session == "LONDON_NEW_YORK":
        if "session_overlap" not in frame.columns:
            raise ValueError("session features required for overlap research")
        return frame["session_overlap"].eq("LONDON_NEW_YORK")
    if "session_primary" not in frame.columns:
        raise ValueError("session features required for session-specific research")
    return frame["session_primary"].eq(session)


def _oos_outcomes(
    frame: pd.DataFrame,
    strategy: StrategyCandidate,
    session: str,
    test_fraction: float,
) -> tuple[pd.Series, pd.Series]:
    test_start = frame.index[max(1, int(len(frame) * (1.0 - test_fraction)))]
    test = frame.loc[frame.index >= test_start]
    mask = _condition_mask(test, strategy) & _session_mask(test, session)
    labels = triple_barrier_labels(
        test,
        horizon_bars=strategy.horizon_bars,
        stop_atr=strategy.stop_atr,
        target_atr=strategy.target_atr,
    ).loc[mask]
    labels = labels.loc[labels["label_long_r"].notna()]
    return labels["label_long_r"], test.loc[labels.index, "mi_regime"]


def run_research_pipeline(
    *,
    candidate: ResearchCandidate,
    spec: ExperimentSpec,
    frame: pd.DataFrame,
    regimes: pd.Series | None,
    gate: ResearchGate,
    cost_model: ExecutionCostModel | None = None,
    test_fraction: float = 0.20,
) -> ResearchPipelineResult:
    """Run OOS, walk-forward, cost and regime evidence for one candidate."""
    if frame.empty:
        raise ValueError("research frame is empty")
    strategy = _strategy_candidate(candidate)
    validation = validate_experiment(spec, frame, strategy, test_fraction=test_fraction)
    walk_forward = walk_forward_validate(frame, strategy)
    snapshot = evaluate_experiment(spec, frame, strategy)

    r_values, inferred_regimes = _oos_outcomes(
        frame,
        strategy,
        candidate.session,
        test_fraction,
    )
    regime_values = inferred_regimes
    if regimes is not None:
        regime_values = regimes.reindex(r_values.index)
    regime_result = evaluate_regime_stress(
        regime_values.tolist(),
        r_values.tolist(),
    )
    cost_aware = evaluate_costs(
        r_values.tolist(),
        model=cost_model or ExecutionCostModel(),
    )

    final_state = classify_research_candidate(
        gate=gate,
        sample_size=int(snapshot.rows),
    )
    if validation.status != "OOS_EVALUATED":
        final_state = validation.status
    elif walk_forward.status != "WF_ALL_FOLDS_POSITIVE":
        final_state = walk_forward.status
    elif cost_aware.status != "COST_AWARE_POSITIVE":
        final_state = cost_aware.status
    elif regime_result.status != "REGIME_STRESS_ALL_POSITIVE":
        final_state = regime_result.status

    return ResearchPipelineResult(
        candidate_id=candidate.candidate_id,
        validation=validation,
        walk_forward=walk_forward,
        cost_aware=cost_aware,
        regime_status=regime_result.status,
        final_state=final_state,
    )
