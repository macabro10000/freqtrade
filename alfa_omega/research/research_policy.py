"""Policy for continuous internet-driven research and candidate promotion.

The internet may generate ideas. Only the ALFA OMEGA validation pipeline can
turn an idea into evidence. No web finding can directly alter execution.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchGate:
    causal_features: bool
    strict_temporal_split: bool
    purged_embargo: bool
    out_of_sample: bool
    walk_forward: bool
    cost_aware: bool
    regime_stress: bool
    execution_safety: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.causal_features,
                self.strict_temporal_split,
                self.purged_embargo,
                self.out_of_sample,
                self.walk_forward,
                self.cost_aware,
                self.regime_stress,
                self.execution_safety,
            )
        )


def classify_research_candidate(
    gate: ResearchGate,
    *,
    sample_size: int,
    min_sample_size: int = 200,
) -> str:
    """Return an evidence state; never enables live execution."""
    if sample_size < min_sample_size:
        return "INSUFFICIENT_EVIDENCE"
    if not gate.causal_features:
        return "REJECTED_LEAKAGE_RISK"
    if not gate.strict_temporal_split or not gate.purged_embargo:
        return "REJECTED_VALIDATION"
    if not gate.out_of_sample:
        return "OOS_REQUIRED"
    if not gate.walk_forward:
        return "WALK_FORWARD_REQUIRED"
    if not gate.cost_aware:
        return "COST_AWARE_REQUIRED"
    if not gate.regime_stress:
        return "REGIME_STRESS_REQUIRED"
    if not gate.execution_safety:
        return "EXECUTION_SAFETY_REQUIRED"
    return "CANDIDATE_FOR_PAPER"
