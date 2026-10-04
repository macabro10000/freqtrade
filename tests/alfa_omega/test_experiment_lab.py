from alfa_omega.lab.experiment import (
    ExperimentProposal,
    can_promote,
    validate_proposal,
)


def make_proposal() -> ExperimentProposal:
    return ExperimentProposal(
        experiment_id="LAB-0001",
        title="Test hypothesis",
        hypothesis="A causal feature may improve OOS expectancy.",
        motivation="Research idea.",
        market="BTC/USD",
        timeframe="15m",
        dataset_fingerprint="sha256:test",
        feature_version="features-v1",
        label_version="labels-v1",
        validation_plan=(
            "STRICT_TEMPORAL_SPLIT",
            "PURGED_EMBARGO",
            "OUT_OF_SAMPLE",
            "WALK_FORWARD",
            "COST_AWARE",
            "REGIME_STRESS",
        ),
    )


def test_valid_lab_proposal():
    proposal = make_proposal()
    validate_proposal(proposal)
    assert proposal.status == "PLANNED"


def test_empty_hypothesis_is_rejected():
    proposal = make_proposal()
    invalid = ExperimentProposal(
        **{**proposal.to_dict(), "hypothesis": ""},
    )
    try:
        validate_proposal(invalid)
    except ValueError as exc:
        assert "hypothesis" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_promotion_requires_research_verdict():
    assert can_promote("PLANNED") is False
    assert can_promote("REJECTED") is False
    assert can_promote("PROMOTE_TO_CANDIDATE") is True
