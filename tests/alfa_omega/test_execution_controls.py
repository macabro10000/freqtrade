import pytest

from alfa_omega.execution.execution_service import ExecutionRequest, ExecutionService
from alfa_omega.execution.risk_engine import RiskEngine, RiskLimits


def test_risk_engine_sizes_from_risk_budget():
    engine = RiskEngine(RiskLimits(
        max_position_risk_fraction=0.005,
        max_daily_loss_fraction=0.02,
        max_open_positions=1,
        max_notional_fraction=0.10,
    ))
    decision = engine.evaluate(
        equity=100_000.0, entry_price=100_000.0, stop_loss=99_000.0,
        requested_quantity=None, open_positions=0,
    )
    assert decision.approved is True
    assert decision.quantity == pytest.approx(0.1)
    assert decision.risk_amount == pytest.approx(100.0)
    assert decision.notional == pytest.approx(10_000.0)


def test_safe_paper_request_is_authorized_without_broker_call():
    result = ExecutionService().authorize(ExecutionRequest(
        market="BTC/USD", side="LONG", entry_price=100_000.0,
        stop_loss=99_000.0, take_profit=101_000.0, quantity=0.1,
        equity=100_000.0, mode="PAPER",
    ))
    assert result["authorized"] is True


def test_risk_budget_rejects_oversized_requested_quantity():
    result = ExecutionService().authorize(ExecutionRequest(
        market="BTC/USD", side="LONG", entry_price=100_000.0,
        stop_loss=99_000.0, take_profit=101_000.0, quantity=0.6,
        equity=100_000.0, mode="PAPER",
    ))
    assert result["authorized"] is False
    assert "MAX_POSITION_RISK" in result["risk"]["reasons"]


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"stop_loss": 0.0}, "INVALID_STOP_LOSS"),
        ({"market": "XAU/USD"}, "MARKET_NOT_ALLOWED"),
        ({"mode": "LIVE"}, "LIVE_EXECUTION_BLOCKED"),
        ({"side": "LONG", "stop_loss": 101_000.0}, "INVALID_STOP_LOSS"),
        ({"take_profit": 99_000.0}, "INVALID_TAKE_PROFIT"),
        ({"broker_healthy": False}, "BROKER_UNHEALTHY"),
        ({"data_fresh": False}, "STALE_DATA"),
        ({"kill_switch": False}, "KILL_SWITCH_ACTIVE"),
    ],
)
def test_safety_rejects_unsafe_requests(kwargs, reason):
    base = {
        "market": "BTC/USD", "side": "LONG", "entry_price": 100_000.0,
        "stop_loss": 99_000.0, "take_profit": 101_000.0, "quantity": 0.1,
        "equity": 100_000.0, "mode": "PAPER",
    }
    base.update(kwargs)
    result = ExecutionService().authorize(ExecutionRequest(**base))
    assert reason in result["safety"]["reasons"] or reason in result["risk"]["reasons"]


def test_no_quantity_uses_risk_derived_size():
    result = ExecutionService().authorize(ExecutionRequest(
        market="BTC/USD", side="LONG", entry_price=100_000.0,
        stop_loss=99_000.0, take_profit=101_000.0, quantity=None,
        equity=100_000.0, mode="PAPER",
    ))
    assert result["authorized"] is True
    assert result["risk"]["quantity"] == pytest.approx(0.1)
