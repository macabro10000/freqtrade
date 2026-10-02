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
from alfa_omega.research.event_labels import (
    EventLabelArtifact,
    build_event_label_artifact,
)
from alfa_omega.research.experiment_evaluator import evaluate_experiment
from alfa_omega.research.experiment_runner import ExperimentSpec
from alfa_omega.research.regime_stress import evaluate_regime_stress
from alfa_omega.research.research_policy import (
    ResearchGate,
    classify_research_candidate,
)
from alfa_omega.research.strategy_discovery import StrategyCandidate
from alfa_omega.research.validation_engine import (
    ValidationResult,
    validate_experiment,
)
from alfa_omega.research.walk_forward import (
    WalkForwardResult,
    walk_forward_validate,
)


@dataclass(frozen=True)
class ResearchPipelineResult:
    candidate_id: str
    validation: ValidationResult
    walk_forward: WalkForwardResult
    cost_aware: CostAwareResult
    regime_status: str
    final_state: str


def _strategy_candidate(
    candidate: ResearchCandidate,
    spec: ExperimentSpec,
) -> StrategyCandidate:
    return StrategyCandidate(
        strategy_id=candidate.hypothesis_id,
        long_conditions=candidate.conditions,
        short_conditions=(),
        horizon_bars=spec.horizon_bars,
        stop_atr=spec.stop_atr,
        target_atr=spec.target_atr,
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


def _regime_mask(
    frame: pd.DataFrame,
    candidate_regime: str,
    regimes: pd.Series | None,
) -> pd.Series:
    if candidate_regime in {"", "ALL", "ANY"}:
        return pd.Series(True, index=frame.index)

    source = regimes
    if source is None:
        if "mi_regime" not in frame.columns:
            raise ValueError("regime data required for regime-specific research")
        source = frame["mi_regime"]

    aligned = source.reindex(frame.index)
    return aligned.eq(candidate_regime).fillna(False)


def _oos_outcomes(
    frame: pd.DataFrame,
    strategy: StrategyCandidate,
    event_labels: EventLabelArtifact,
    candidate: ResearchCandidate,
    regimes: pd.Series | None,
    test_fraction: float,
) -> tuple[pd.Series, pd.Series]:
    test_start_pos = max(1, int(len(frame) * (1.0 - test_fraction)))
    test_start = frame.index[test_start_pos]

    # Labels were computed once on the full timeline before context filtering.
    test = frame.loc[frame.index >= test_start]
    context_mask = (
        _condition_mask(test, strategy)
        & _session_mask(test, candidate.session)
        & _regime_mask(test, candidate.regime, regimes)
    )
    selected = test.loc[context_mask.fillna(False)]
    labels = event_labels.labels.reindex(selected.index)
    valid = labels["label_long_r"].notna()
    selected = selected.loc[valid]
    labels = labels.loc[valid]

    return labels["label_long_r"], (
        regimes.reindex(selected.index)
        if regimes is not None
        else selected["mi_regime"]
    )


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

    strategy = _strategy_candidate(candidate, spec)
    event_labels = build_event_label_artifact(
        frame,
        horizon_bars=spec.horizon_bars,
        stop_atr=spec.stop_atr,
        target_atr=spec.target_atr,
    )
    validation = validate_experiment(
        spec,
        frame,
        strategy,
        test_fraction=test_fraction,
        event_labels=event_labels,
    )
    walk_forward = walk_forward_validate(
        spec,
        frame,
        strategy,
        event_labels=event_labels,
    )
    snapshot = evaluate_experiment(
        spec,
        frame,
        strategy,
        event_labels=event_labels,
    )

    r_values, inferred_regimes = _oos_outcomes(
        frame,
        strategy,
        event_labels,
        candidate,
        regimes,
        test_fraction,
    )
    regime_result = evaluate_regime_stress(
        inferred_regimes.tolist(),
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
    # Evidence sufficiency is a higher-level gate than a downstream metric
    # failure. A small sample must remain INSUFFICIENT_EVIDENCE rather than
    # being misclassified as an OOS expectancy failure.
    if snapshot.rows < 200:
        final_state = "INSUFFICIENT_EVIDENCE"
    elif validation.status != "OOS_EVALUATED":
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
