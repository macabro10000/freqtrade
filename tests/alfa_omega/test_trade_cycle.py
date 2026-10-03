from dataclasses import dataclass

import pandas as pd

from alfa_omega.execution.trade_cycle import TradeCycle
from alfa_omega.intelligence.trade_decision import decide_trade


def _buy():
    return decide_trade(
        pd.DataFrame([{
            "mi_evidence_score": 6,
            "mi_market_bias": 1,
            "mi_alignment_quality": 1.0,
            "mi_regime": "TREND",
            "close": 100.0,
            "atr_14": 2.0,
        }]),
        market="BTC/USD",
        timeframe="5m",
    )


@dataclass
class FakeAdapter:
    market_orders: list
    stop_orders: list

    def submit_market_order(self, **kwargs):
        self.market_orders.append(kwargs)
        return {"id": "ENTRY-1", "status": "accepted"}

    def submit_stop_limit_exit(self, **kwargs):
        self.stop_orders.append(kwargs)
        return {"id": "STOP-1", "status": "accepted"}


def test_hold_does_not_authorize_trade():
    result = TradeCycle().authorize(
        decide_trade(
            pd.DataFrame([{
                "mi_evidence_score": 1,
                "mi_market_bias": 1,
                "mi_alignment_quality": 1.0,
                "mi_regime": "TREND",
                "close": 100.0,
                "atr_14": 2.0,
            }]),
            market="BTC/USD",
            timeframe="5m",
        ),
        equity=1000.0,
    )
    assert result.status == "NO_TRADE"


def test_buy_is_authorized_but_not_submitted_by_authorize():
    result = TradeCycle().authorize(_buy(), equity=100000.0)
    assert result.status == "AUTHORIZED_PAPER"
    assert result.order is None


def test_buy_paper_submission_places_entry_then_protective_stop():
    adapter = FakeAdapter([], [])
    result = TradeCycle(adapter=adapter).execute_paper(
        _buy(),
        equity=100000.0,
        client_order_id="AO-TEST-ENTRY",
    )
    assert result.status == "PAPER_ENTRY_AND_PROTECTIVE_STOP_SUBMITTED"
    assert adapter.market_orders[0]["side"] == "buy"
    assert adapter.stop_orders[0]["stop_price"] == 98.0
    assert adapter.stop_orders[0]["limit_price"] == 98.0 * 0.995


def test_short_is_not_misrepresented_as_sell_entry():
    decision = _buy()
    decision = decision.__class__(
        action="SELL",
        market=decision.market,
        timeframe=decision.timeframe,
        confidence=decision.confidence,
        evidence_score=-6,
        thesis="bearish",
        entry_price=100.0,
        stop_price=102.0,
        target_price=96.0,
        risk_fraction=0.005,
        reasons=("BEARISH_EVIDENCE",),
    )
    result = TradeCycle().execute_paper(decision, equity=100000.0)
    assert result.status == "PAPER_SHORT_NOT_SUPPORTED"
