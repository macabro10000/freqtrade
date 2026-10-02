from alfa_omega.research.cost_aware import ExecutionCostModel, evaluate_costs


def test_costs_reduce_expectancy():
    result = evaluate_costs(
        [2.0, -1.0, 1.0],
        model=ExecutionCostModel(
            fee_bps=5.0,
            spread_bps=2.0,
            slippage_bps=3.0,
        ),
        risk_fraction_price=0.01,
    )
    assert result.trades == 3
    assert result.net_expectancy_r < result.gross_expectancy_r
    assert result.total_cost_r > 0


def test_cost_aware_can_fail_positive_gross_result():
    result = evaluate_costs(
        [0.30, 0.20, 0.10],
        model=ExecutionCostModel(
            fee_bps=10.0,
            spread_bps=10.0,
            slippage_bps=10.0,
        ),
        risk_fraction_price=0.01,
    )
    assert result.gross_expectancy_r > 0
    assert result.net_expectancy_r < 0
    assert result.status == "COST_AWARE_FAILED"


def test_negative_cost_inputs_are_rejected():
    try:
        ExecutionCostModel(fee_bps=-1.0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
