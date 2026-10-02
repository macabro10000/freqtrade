import pytest

from alfa_omega.execution.execution_service import ExecutionRequest, ExecutionService


def test_safe_paper_request_is_authorized_without_broker_call():
    service = ExecutionService()

    result = service.authorize(
        ExecutionRequest(
            market="BTC/USD",
            side="LONG",
            entry_price=100_000.0,
            stop_loss=99_000.0,
            quantity=0.5,
            equity=100_000.0,
            mode="PAPER",
        )
    )

    assert result["authorized"] is True


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"stop_loss": 0.0}, "INVALID_STOP_LOSS"),
        ({"market": "XAU/USD"}, "MARKET_NOT_ALLOWED"),
        ({"mode": "LIVE"}, "LIVE_EXECUTION_BLOCKED"),
    ],
)
def test_safety_rejects_unsafe_requests(kwargs, reason):
    base = dict(
        market="BTC/USD",
        side="LONG",
        entry_price=100_000.0,
        stop_loss=99_000.0,
        quantity=0.5,
        equity=100_000.0,
        mode="PAPER",
    )
    base.update(kwargs)

    result = ExecutionService().authorize(ExecutionRequest(**base))

    assert reason in result["safety"]["reasons"] or reason in result["risk"]["reasons"]
