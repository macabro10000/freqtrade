import pandas as pd

from alfa_omega.research.experiment_runner import build_experiment
from alfa_omega.research.hypothesis_factory import ResearchHypothesis
from alfa_omega.research.strategy_discovery import StrategyCandidate
from alfa_omega.research.validation_engine import validate_experiment, validation_to_result


def _frame(periods=100):
    idx = pd.date_range("2026-01-01", periods=periods, freq="5min", tz="UTC")
    return pd.DataFrame({
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.0,
        "atr_14": 1.0,
        "setup": True,
    }, index=idx)


def _spec():
    h = ResearchHypothesis(
        hypothesis_id="H-VALIDATE",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        conditions=("setup",),
        question="test",
        rationale=("test",),
        source_patterns=("setup",),
    )
    return build_experiment(
        h,
        dataset_fingerprint="D1",
        feature_version="F1",
        label_version="L1",
    )


def test_validation_is_chronological_and_purged():
    df = _frame()
    df.loc[df.index[80], "high"] = 103.0
    spec = _spec()
    candidate = StrategyCandidate("S1", ("setup",), (), 5, 1.0, 2.0)

    result = validate_experiment(
        spec,
        df,
        candidate,
        test_fraction=0.20,
        embargo_bars=5,
    )

    assert result.test_rows > 0
    assert result.train_rows < 80
    assert result.status in {
        "OOS_EVALUATED",
        "OOS_FAILED_EXPECTANCY",
        "OOS_INSUFFICIENT_TRADES",
    }
    assert result.feature_audit_ok is True

    recorded = validation_to_result(result)
    assert recorded.experiment_id == spec.experiment_id
    assert recorded.status == result.status


def test_validation_rejects_naive_index():
    df = _frame().reset_index(drop=True)
    spec = _spec()
    candidate = StrategyCandidate("S1", ("setup",), (), 5, 1.0, 2.0)

    try:
        validate_experiment(spec, df, candidate)
    except TypeError:
        return
    raise AssertionError("expected TypeError for non-DatetimeIndex")
