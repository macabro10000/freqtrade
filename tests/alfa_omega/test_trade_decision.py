import pandas as pd

from alfa_omega.intelligence.trade_decision import decide_trade


def _frame(**overrides):
    values = {
        "mi_evidence_score": 6,
        "mi_market_bias": 1,
        "mi_alignment_quality": 1.0,
        "mi_regime": "TREND",
        "close": 100.0,
        "atr_14": 2.0,
    }
    values.update(overrides)
    return pd.DataFrame([values])


def test_decision_can_produce_buy_without_submitting_order():
    decision = decide_trade(_frame(), market="BTC/USD", timeframe="5m")
    assert decision.action == "BUY"
    assert decision.entry_price == 100.0
    assert decision.stop_price == 98.0
    assert decision.target_price == 104.0
    assert decision.risk_fraction <= 0.005
    assert decision.status == "DECISION_ONLY"


def test_decision_can_produce_sell():
    decision = decide_trade(
        _frame(
            mi_evidence_score=-6,
            mi_market_bias=-1,
            mi_alignment_quality=1.0,
        ),
        market="BTC/USD",
        timeframe="5m",
    )
    assert decision.action == "SELL"
    assert decision.stop_price == 102.0
    assert decision.target_price == 96.0


def test_weak_evidence_is_hold():
    decision = decide_trade(
        _frame(mi_evidence_score=2, mi_market_bias=1),
        market="BTC/USD",
        timeframe="5m",
    )
    assert decision.action == "HOLD"
    assert decision.risk_fraction == 0.0


def test_range_regime_is_hold():
    decision = decide_trade(
        _frame(mi_regime="RANGE_LOW_VOL", mi_evidence_score=8),
        market="BTC/USD",
        timeframe="5m",
    )
    assert decision.action == "HOLD"
