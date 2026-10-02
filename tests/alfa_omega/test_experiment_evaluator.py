import pandas as pd

from alfa_omega.research.experiment_evaluator import (
    evaluate_experiment,
    snapshot_to_result,
)
from alfa_omega.research.experiment_runner import build_experiment
from alfa_omega.research.hypothesis_factory import ResearchHypothesis
from alfa_omega.research.strategy_discovery import StrategyCandidate


def test_experiment_evaluator_uses_supplied_slice():
    idx = pd.date_range("2026-01-01", periods=30, freq="5min", tz="UTC")
    df = pd.DataFrame({
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.0,
        "atr_14": 1.0,
        "setup": True,
    }, index=idx)
    df.loc[idx[1], ["high", "close"]] = [103.0, 100.0]

    h = ResearchHypothesis(
        hypothesis_id="H-1",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        conditions=("setup",),
        question="test",
        rationale=("test",),
        source_patterns=("setup",),
    )
    spec = build_experiment(
        h,
        dataset_fingerprint="D1",
        feature_version="F1",
        label_version="L1",
    )
    candidate = StrategyCandidate("S1", ("setup",), (), 3, 1.0, 2.0)
    snapshot = evaluate_experiment(spec, df, candidate)
    assert snapshot.experiment_id == spec.experiment_id
    assert snapshot.rows == 30
    assert snapshot.trades >= 1
    result = snapshot_to_result(snapshot)
    assert result.experiment_id == spec.experiment_id
    assert result.status == "EVALUATED"
