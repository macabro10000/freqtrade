import pandas as pd

from alfa_omega.research.experiment_runner import build_experiment
from alfa_omega.research.hypothesis_factory import ResearchHypothesis
from alfa_omega.research.strategy_discovery import StrategyCandidate
from alfa_omega.research.walk_forward import walk_forward_to_result, walk_forward_validate


def _frame(periods=120):
    idx = pd.date_range("2026-01-01", periods=periods, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "atr_14": 1.0,
            "setup": True,
        },
        index=idx,
    )


def _spec():
    hypothesis = ResearchHypothesis(
        hypothesis_id="H-WF",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        conditions=("setup",),
        question="walk forward",
        rationale=("test",),
        source_patterns=("setup",),
    )
    return build_experiment(
        hypothesis,
        dataset_fingerprint="D-WF",
        feature_version="F1",
        label_version="L1",
    )


def test_walk_forward_is_expanding_and_chronological():
    df = _frame()
    # Create deterministic target touches in each OOS region.
    for pos in (72, 84, 96, 108, 119):
        df.iloc[pos, df.columns.get_loc("high")] = 103.0

    candidate = StrategyCandidate(
        "S-WF",
        ("setup",),
        (),
        3,
        1.0,
        2.0,
    )

    result = walk_forward_validate(
        _spec(),
        df,
        candidate,
        n_splits=3,
        test_size=10,
        min_train_size=40,
        embargo_bars=3,
    )

    assert result.folds_evaluated == 3
    assert result.total_test_trades >= 0
    assert result.feature_audit_ok is True

    for previous, current in zip(result.folds, result.folds[1:]):
        assert current.test_start > previous.test_start
        assert current.train_rows >= previous.train_rows
        assert current.train_end < current.test_start

    recorded = walk_forward_to_result(result)
    assert recorded.experiment_id == result.experiment_id
    assert recorded.status == result.status


def test_walk_forward_rejects_small_dataset():
    df = _frame(20)
    candidate = StrategyCandidate("S-WF", ("setup",), (), 3, 1.0, 2.0)

    try:
        walk_forward_validate(
            _spec(),
            df,
            candidate,
            n_splits=5,
            test_size=5,
            min_train_size=10,
        )
    except ValueError:
        return
    raise AssertionError("expected ValueError for an undersized walk-forward plan")
