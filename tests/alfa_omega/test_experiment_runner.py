from alfa_omega.research.experiment_runner import (
    build_experiment,
    record_experiment_result,
)
from alfa_omega.research.hypothesis_factory import ResearchHypothesis


def hypothesis():
    return ResearchHypothesis(
        hypothesis_id="H-ABC123",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        conditions=("CHOCH_BULL", "FVG_BULL"),
        question="test",
        rationale=("evidence",),
        source_patterns=("CHOCH_BULL", "FVG_BULL"),
    )


def test_experiment_is_reproducible():
    kwargs = {
        dataset_fingerprint="DATA-1",
        feature_version="F-1",
        label_version="L-1",
    }
    a = build_experiment(hypothesis(), **kwargs)
    b = build_experiment(hypothesis(), **kwargs)
    assert a.experiment_id == b.experiment_id
    assert a.status == "PLANNED"
    assert "WALK_FORWARD" in a.validation_plan


def test_result_preserves_metrics():
    spec = build_experiment(
        hypothesis(),
        dataset_fingerprint="DATA-1",
        feature_version="F-1",
        label_version="L-1",
    )
    result = record_experiment_result(
        spec,
        status="OOS_REQUIRED",
        metrics={"expectancy_r": 0.21, "max_drawdown": 0.08},
        notes=["needs more evidence"],
    )
    assert result.experiment_id == spec.experiment_id
    assert ("expectancy_r", 0.21) in result.metrics
    assert result.status == "OOS_REQUIRED"
