import pandas as pd

from alfa_omega.research.indicator_factory import (
    compute_indicator,
    generate_indicator_candidates,
)
from alfa_omega.research.learning_loop import (
    LearningObservation,
    assess_observation,
    record_error,
)
from alfa_omega.research.pattern_engine import encode_patterns, pattern_statistics
from alfa_omega.research.strategy_discovery import (
    discover_candidates,
    evaluate_candidate,
    label_forward_outcomes,
)


def _sample() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=300, freq="5min", tz="UTC")
    close = pd.Series(range(300), index=idx, dtype=float) + 100
    out = pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100.0,
            "atr_14": 1.0,
            "trend_bias": 1,
            "structure_bias": 1,
            "breakout_high_20": 0,
            "breakdown_low_20": 0,
            "liquidity_sweep_high": 0,
            "liquidity_sweep_low": 1,
            "fvg_bullish_smc": 1,
            "fvg_bearish_smc": 0,
            "range_expansion": 1,
        },
        index=idx,
    )
    return out


def test_labels_use_future_only_for_outcomes():
    df = _sample()
    labeled = label_forward_outcomes(df, horizon_bars=5)
    assert "label_long_r" in labeled
    assert labeled.iloc[0]["label_long_r"] > 0


def test_strategy_discovery_and_evaluation():
    df = _sample()
    candidates = discover_candidates(df, ["trend_bias", "structure_bias"], max_conditions=2)
    assert candidates
    result = evaluate_candidate(df, candidates[0])
    assert result["trades"] > 0


def test_pattern_engine():
    df = encode_patterns(_sample())
    stats = pattern_statistics(
        df.assign(label_long_r=1.0)
    )
    assert "occurrences" in stats
    assert len(stats) >= 1


def test_generated_indicator_is_causal():
    df = _sample()
    candidates = generate_indicator_candidates(df, ["close", "volume"])
    assert candidates
    original = compute_indicator(df, candidates[0])
    changed = df.copy()
    changed.iloc[-1, changed.columns.get_loc("close")] += 1000
    updated = compute_indicator(changed, candidates[0])
    assert original.iloc[:-1].equals(updated.iloc[:-1])


def test_learning_loop_rejects_bad_oos():
    observation = LearningObservation(
        experiment_id="x",
        strategy_id="s",
        regime="trend",
        sample_size=500,
        expectancy_r=0.2,
        profit_factor=1.2,
        max_drawdown=0.1,
        oos_expectancy_r=-0.1,
        walk_forward_pass=True,
    )
    decision = assess_observation(observation)
    assert decision.status == "OOS_FAILED"


def test_errors_are_recorded():
    error = record_error("x", "OVERFIT", "OOS failed", -0.1)
    assert error.category == "OVERFIT"
