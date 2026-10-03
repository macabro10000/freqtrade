"""End-to-end decision-to-Paper execution coordinator for ALFA OMEGA.

The coordinator joins analysis, risk authorization and the controlled broker
adapter. It never enables execution by itself. LIVE remains impossible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from alfa_omega.execution.execution_service import ExecutionRequest, ExecutionService
from alfa_omega.intelligence.trade_decision import TradeDecision


class PaperAdapter(Protocol):
    def submit_market_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: float,
        client_order_id: str | None = None,
    ) -> dict[str, Any]: ...

    def submit_stop_limit_exit(
        self,
        *,
        symbol: str,
        qty: float,
        stop_price: float,
        limit_price: float,
        client_order_id: str | None = None,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class TradeCycleResult:
    action: str
    status: str
    authorized: bool
    authorization: dict[str, Any]
    order: dict[str, Any] | None
    protective_order: dict[str, Any] | None
    reason: str | None = None


class TradeCycle:
    """Connect decision -> risk/safety -> explicit Paper submission."""

    def __init__(
        self,
        *,
        execution_service: ExecutionService | None = None,
        adapter: PaperAdapter | None = None,
    ) -> None:
        self.execution = execution_service or ExecutionService()
        self.adapter = adapter

    def authorize(
        self,
        decision: TradeDecision,
        *,
        equity: float,
        open_positions: int = 0,
        daily_pnl: float = 0.0,
        broker_healthy: bool = True,
        data_fresh: bool = True,
        kill_switch: bool = True,
    ) -> TradeCycleResult:
        if decision.action == "HOLD":
            return TradeCycleResult(
                action="HOLD",
                status="NO_TRADE",
                authorized=False,
                authorization={},
                order=None,
                protective_order=None,
                reason="Decision is HOLD.",
            )

        if decision.entry_price is None or decision.stop_price is None:
            return TradeCycleResult(
                action=decision.action,
                status="REJECTED",
                authorized=False,
                authorization={},
                order=None,
                protective_order=None,
                reason="Decision has incomplete risk geometry.",
            )

        side = "LONG" if decision.action == "BUY" else "SHORT"
        authorization = self.execution.authorize(
            ExecutionRequest(
                market=decision.market,
                side=side,
                entry_price=decision.entry_price,
                stop_loss=decision.stop_price,
                take_profit=decision.target_price or 0.0,
                quantity=None,
                equity=equity,
                open_positions=open_positions,
                daily_pnl=daily_pnl,
                mode="PAPER",
                broker_healthy=broker_healthy,
                data_fresh=data_fresh,
                kill_switch=kill_switch,
            )
        )
        if not authorization["authorized"]:
            return TradeCycleResult(
                action=decision.action,
                status="RISK_OR_SAFETY_REJECTED",
                authorized=False,
                authorization=authorization,
                order=None,
                protective_order=None,
                reason="Risk or safety gate rejected the trade.",
            )

        return TradeCycleResult(
            action=decision.action,
            status="AUTHORIZED_PAPER",
            authorized=True,
            authorization=authorization,
            order=None,
            protective_order=None,
        )

    def execute_paper(
        self,
        decision: TradeDecision,
        *,
        equity: float,
        open_positions: int = 0,
        daily_pnl: float = 0.0,
        broker_healthy: bool = True,
        data_fresh: bool = True,
        kill_switch: bool = True,
        client_order_id: str | None = None,
    ) -> TradeCycleResult:
        """Submit a BUY entry only after all gates approve.

        SELL remains a directional SHORT hypothesis in the decision engine,
        but the current controlled Alpaca adapter does not open short crypto
        positions. It is therefore rejected rather than misrepresented as an
        entry sell.
        """
        authorized = self.authorize(
            decision,
            equity=equity,
            open_positions=open_positions,
            daily_pnl=daily_pnl,
            broker_healthy=broker_healthy,
            data_fresh=data_fresh,
            kill_switch=kill_switch,
        )
        if not authorized.authorized:
            return authorized

        if decision.action != "BUY":
            return TradeCycleResult(
                action=decision.action,
                status="PAPER_SHORT_NOT_SUPPORTED",
                authorized=True,
                authorization=authorized.authorization,
                order=None,
                protective_order=None,
                reason="Controlled Alpaca Paper phase does not open short crypto positions.",
            )

        if self.adapter is None:
            return TradeCycleResult(
                action="BUY",
                status="EXECUTION_ADAPTER_MISSING",
                authorized=True,
                authorization=authorized.authorization,
                order=None,
                protective_order=None,
                reason="Paper adapter is required for order submission.",
            )

        quantity = float(authorized.authorization["risk"]["quantity"])
        order = self.adapter.submit_market_order(
            symbol=decision.market,
            side="buy",
            qty=quantity,
            client_order_id=client_order_id,
        )

        # Alpaca crypto has no native bracket/OCO. Protective stop is submitted
        # separately, so a future implementation must reconcile both orders.
        stop = decision.stop_price
        entry = decision.entry_price
        if stop is None or entry is None or stop >= entry:
            return TradeCycleResult(
                action="BUY",
                status="ENTRY_SUBMITTED_PROTECTIVE_ORDER_NOT_VALID",
                authorized=True,
                authorization=authorized.authorization,
                order=order,
                protective_order=None,
                reason="Entry was submitted but protective-stop geometry is invalid.",
            )

        limit_price = stop * 0.995
        protective = self.adapter.submit_stop_limit_exit(
            symbol=decision.market,
            qty=quantity,
            stop_price=stop,
            limit_price=limit_price,
            client_order_id=(
                f"{client_order_id}-STOP" if client_order_id else None
            ),
        )
        return TradeCycleResult(
            action="BUY",
            status="PAPER_ENTRY_AND_PROTECTIVE_STOP_SUBMITTED",
            authorized=True,
            authorization=authorized.authorization,
            order=order,
            protective_order=protective,
        )
