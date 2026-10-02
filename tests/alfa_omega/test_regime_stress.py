from alfa_omega.research.regime_stress import evaluate_regime_stress


def test_regime_stress_reports_each_qualified_regime():
    result = evaluate_regime_stress(
        ["TREND"] * 5 + ["RANGE_LOW_VOL"] * 5 + ["EXPANSION"] * 5,
        [1.0, 0.5, -0.2, 0.8, 0.4, -0.1, 0.2, -0.2, 0.1, 0.3, 1.2, 0.8, 0.4, -0.1, 0.2],
    )
    assert result.regimes_tested == 3
    assert result.regimes_positive == 3
    assert result.status == "REGIME_STRESS_ALL_POSITIVE"


def test_regime_stress_detects_mixed_behavior():
    result = evaluate_regime_stress(
        ["TREND"] * 5 + ["EXPANSION"] * 5,
        [1.0, 0.5, 0.2, 0.8, 0.4, -1.0, -0.5, 0.1, -0.8, -0.4],
    )
    assert result.status == "REGIME_STRESS_MIXED"
    assert result.worst_expectancy_r < 0


def test_regime_stress_rejects_insufficient_data():
    result = evaluate_regime_stress(
        ["TREND", "TREND", "TREND"],
        [1.0, -0.5, 0.5],
        min_trades_per_regime=5,
    )
    assert result.status == "REGIME_STRESS_INSUFFICIENT_DATA"
