"""End-to-end research pipeline coordinator.

This module coordinates existing research components. It does not fetch data,
place orders, or promote candidates by itself.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alfa_omega.research.candidate_bridge import ResearchCandidate
from alfa_omega.research.cost_aware import CostAwareResult, ExecutionCostModel, evaluate_costs
from alfa_omega.research.experiment_evaluator import EvaluationSnapshot, evaluate_experiment
from alfa_omega.research.experiment_runner import ExperimentSpec
from alfa_omega.research.regime_stress import evaluate_regime_stress
from alfa_omega.research.research_policy import ResearchGate, classify_research_candidate
from alfa_omega.research.strategy_discovery import StrategyCandidate
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
        long_conditions=(),
        short_conditions=(),
        horizon_bars=5,
        stop_atr=1.0,
        target_atr=2.0,
    )


def _evaluation_frame(
    frame: pd.DataFrame,
    strategy: StrategyCandidate,
) -> pd.DataFrame:
    return frame


def run_research_pipeline(
    *,
    candidate: ResearchCandidate,
    spec: ExperimentSpec,
    frame: pd.DataFrame,
    regimes: pd.Series,
    gate: ResearchGate,
    cost_model: ExecutionCostModel | None = None,
) -> ResearchPipelineResult:
    """Run the existing validation layers without changing live policy."""
    strategy = _strategy_candidate(candidate)
    evaluation_frame = _evaluation_frame(frame, strategy)

    validation = validate_experiment(
        spec,
        evaluation_frame,
        strategy,
    )
    walk_forward = walk_forward_validate(
        evaluation_frame,
        strategy,
    )

    snapshot: EvaluationSnapshot = evaluate_experiment(
        spec,
        evaluation_frame,
        strategy,
    )
    cost_aware = evaluate_costs(
        snapshot.r_outcomes,
        model=cost_model or ExecutionCostModel(),
    )
    regime_result = evaluate_regime_stress(
        snapshot.r_outcomes,
        regimes.reindex(snapshot.r_outcomes.index),
    )

    final_state = classify_research_candidate(
        gate=gate,
        validation_passed=validation.status == "OOS_EVALUATED",
        walk_forward_passed=walk_forward.status == "WF_ALL_FOLDS_POSITIVE",
        cost_aware_passed=cost_aware.status == "COST_AWARE_POSITIVE",
        regime_stress_passed=regime_result.status == "REGIME_STRESS_ALL_POSITIVE",
    )

    return ResearchPipelineResult(
        candidate_id=candidate.candidate_id,
        validation=validation,
        walk_forward=walk_forward,
        cost_aware=cost_aware,
        regime_status=regime_result.status,
        final_state=final_state,
    )
