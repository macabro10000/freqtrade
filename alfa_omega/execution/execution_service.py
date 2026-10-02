"""ALFA OMEGA execution orchestration.

This service coordinates Risk Engine and Safety Gate. It does not expose
credentials to signals/models and only calls an adapter after both gates pass.
The current Alpaca adapter remains read-only, so real Paper submission is
still blocked by the adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .risk_engine import RiskEngine
from .safety_gate import SafetyContext, SafetyGate


@dataclass(frozen=True)
class ExecutionRequest:
    market: str
    side: str
    entry_price: float
    stop_loss: float
    quantity: float
    equity: float
    open_positions: int = 0
    daily_pnl: float = 0.0
    mode: str = "PAPER"


class ExecutionService:
    def __init__(
        self,
        risk_engine: RiskEngine | None = None,
        safety_gate: SafetyGate | None = None,
    ) -> None:
        self.risk = risk_engine or RiskEngine()
        self.safety = safety_gate or SafetyGate()

    def authorize(self, request: ExecutionRequest) -> dict[str, Any]:
        risk = self.risk.evaluate(
            equity=request.equity,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            requested_quantity=request.quantity,
            open_positions=request.open_positions,
            daily_pnl=request.daily_pnl,
        )

        safety = self.safety.evaluate(
            SafetyContext(
                mode=request.mode,
                market=request.market,
                allowed_markets=("BTC/USD",),
                broker_healthy=True,
                data_fresh=True,
                kill_switch=True,
                risk_approved=risk.approved,
                stop_loss_valid=(
                    request.stop_loss > 0
                    and request.entry_price > 0
                    and request.stop_loss != request.entry_price
                ),
            )
        )

        return {
            "authorized": risk.approved and safety.approved,
            "risk": {
                "approved": risk.approved,
                "reasons": risk.reasons,
                "quantity": risk.quantity,
                "risk_amount": risk.risk_amount,
            },
            "safety": {
                "approved": safety.approved,
                "reasons": safety.reasons,
            },
        }
