"""ALFA OMEGA execution authorization orchestration.

No broker call occurs unless Risk Engine and Safety Gate both approve.
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
    take_profit: float
    quantity: float | None
    equity: float
    open_positions: int = 0
    daily_pnl: float = 0.0
    mode: str = "PAPER"
    allowed_markets: tuple[str, ...] = ("BTC/USD",)
    broker_healthy: bool = True
    data_fresh: bool = True
    kill_switch: bool = True


class ExecutionService:
    def __init__(
        self,
        risk_engine: RiskEngine | None = None,
        safety_gate: SafetyGate | None = None,
    ) -> None:
        self.risk = risk_engine or RiskEngine()
        self.safety = safety_gate or SafetyGate()

    def authorize(self, request: ExecutionRequest) -> dict[str, Any]:
        side = request.side.upper()
        risk = self.risk.evaluate(
            equity=request.equity,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            requested_quantity=request.quantity,
            open_positions=request.open_positions,
            daily_pnl=request.daily_pnl,
        )

        stop_direction_valid = (
            (side == "LONG" and request.stop_loss < request.entry_price)
            or (side == "SHORT" and request.stop_loss > request.entry_price)
        )
        take_profit_direction_valid = (
            (side == "LONG" and request.take_profit > request.entry_price)
            or (side == "SHORT" and request.take_profit < request.entry_price)
        )
        safety = self.safety.evaluate(
            SafetyContext(
                mode=request.mode,
                market=request.market,
                allowed_markets=request.allowed_markets,
                broker_healthy=request.broker_healthy,
                data_fresh=request.data_fresh,
                kill_switch=request.kill_switch,
                risk_approved=risk.approved,
                take_profit_valid=(
                    side in {"LONG", "SHORT"}
                    and take_profit_direction_valid
                    and request.take_profit > 0
                ),
                stop_loss_valid=(
                    side in {"LONG", "SHORT"}
                    and stop_direction_valid
                    and request.entry_price > 0
                    and request.stop_loss > 0
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
                "notional": risk.notional,
            },
            "safety": {
                "approved": safety.approved,
                "reasons": safety.reasons,
            },
        }
