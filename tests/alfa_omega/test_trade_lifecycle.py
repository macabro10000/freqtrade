import pandas as pd
import pytest

from alfa_omega.intelligence.trade_lifecycle import calculate_trade_outcome, decide_exit


def _frame(price, bias=1):
    return pd.DataFrame([{"close": price, "mi_market_bias": bias}])


def test_long_profit_target_exits():
    decision = decide_exit(
        _frame(104),
        side="LONG",
        entry_price=100,
        stop_price=98,
        target_price=104,
    )
    assert decision.action == "EXIT"
    assert decision.reason == "PROFIT_TARGET_REACHED"


def test_long_thesis_invalidation_exits():
    decision = decide_exit(
        _frame(99, bias=-1),
        side="LONG",
        entry_price=100,
        stop_price=98,
        target_price=104,
    )
    assert decision.reason == "THESIS_INVALIDATED_BEARISH_BIAS"


def test_long_hold_when_thesis_valid():
    decision = decide_exit(
        _frame(101, bias=1),
        side="LONG",
        entry_price=100,
        stop_price=98,
        target_price=104,
    )
    assert decision.action == "HOLD"


def test_outcome_includes_costs():
    outcome = calculate_trade_outcome(
        trade_id="T1",
        market="BTC/USD",
        side="LONG",
        entry_price=100,
        exit_price=104,
        quantity=2,
        fees=1,
        slippage=1,
    )
    assert outcome.gross_pnl == pytest.approx(8)
    assert outcome.net_pnl == pytest.approx(6)
    assert outcome.outcome == "WIN"


def test_short_loss_is_negative():
    outcome = calculate_trade_outcome(
        trade_id="T2",
        market="BTC/USD",
        side="SHORT",
        entry_price=100,
        exit_price=103,
        quantity=2,
    )
    assert outcome.net_pnl == pytest.approx(-6)
    assert outcome.outcome == "LOSS"
