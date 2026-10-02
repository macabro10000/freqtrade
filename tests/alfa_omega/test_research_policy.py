from alfa_omega.research.research_policy import (
    ResearchGate,
    classify_research_candidate,
)


def _gate() -> ResearchGate:
    return ResearchGate(
        causal_features=True,
        strict_temporal_split=True,
        purged_embargo=True,
        out_of_sample=True,
        walk_forward=True,
        cost_aware=True,
        regime_stress=True,
        execution_safety=True,
    )


def test_full_gate_allows_only_paper_candidate():
    assert _gate().passed is True
    assert classify_research_candidate(_gate(), sample_size=200) == "CANDIDATE_FOR_PAPER"


def test_insufficient_evidence_blocks_candidate():
    assert classify_research_candidate(_gate(), sample_size=199) == "INSUFFICIENT_EVIDENCE"


def test_leakage_failure_rejects_candidate():
    gate = ResearchGate(
        causal_features=False,
        strict_temporal_split=True,
        purged_embargo=True,
        out_of_sample=True,
        walk_forward=True,
        cost_aware=True,
        regime_stress=True,
        execution_safety=True,
    )
    assert classify_research_candidate(gate, sample_size=1000) == "REJECTED_LEAKAGE_RISK"
