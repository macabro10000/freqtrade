"""ALFA OMEGA risk controls.

Pure decision layer: no broker calls and no credentials.
Position size is derived from the maximum allowed loss, not the other way
around.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_position_risk_fraction: float = 0.005
    max_daily_loss_fraction: float = 0.02
    max_open_positions: int = 1
    max_notional_fraction: float = 0.10


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...]
    quantity: float
    risk_amount: float
    notional: float


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def calculate_quantity(
        self,
        *,
        equity: float,
        entry_price: float,
        stop_loss: float,
    ) -> float:
        if equity <= 0 or entry_price <= 0 or stop_loss <= 0:
            return 0.0
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            return 0.0
        risk_budget = equity * self.limits.max_position_risk_fraction
        return risk_budget / stop_distance

    def evaluate(
        self,
        *,
        equity: float,
        entry_price: float,
        stop_loss: float,
        requested_quantity: float | None = None,
        open_positions: int,
        daily_pnl: float = 0.0,
    ) -> RiskDecision:
        reasons: list[str] = []

        if equity <= 0:
            reasons.append("INVALID_EQUITY")
        if entry_price <= 0 or stop_loss <= 0:
            reasons.append("INVALID_PRICE")
        if entry_price == stop_loss:
            reasons.append("INVALID_STOP_DISTANCE")
        if open_positions >= self.limits.max_open_positions:
            reasons.append("MAX_OPEN_POSITIONS")
        if daily_pnl <= -(equity * self.limits.max_daily_loss_fraction):
            reasons.append("MAX_DAILY_LOSS")

        stop_distance = abs(entry_price - stop_loss)
        risk_budget = max(equity, 0.0) * self.limits.max_position_risk_fraction
        calculated_quantity = self.calculate_quantity(
            equity=equity,
            entry_price=entry_price,
            stop_loss=stop_loss,
        )
        notional_cap = (
            equity * self.limits.max_notional_fraction / entry_price
            if equity > 0 and entry_price > 0
            else 0.0
        )
        calculated_quantity = min(calculated_quantity, notional_cap) if notional_cap > 0 else 0.0
        quantity = calculated_quantity if requested_quantity is None else requested_quantity

        if quantity <= 0:
            reasons.append("INVALID_QUANTITY")

        risk_amount = stop_distance * max(quantity, 0.0)
        notional = entry_price * max(quantity, 0.0)

        if risk_amount > risk_budget and equity > 0:
            reasons.append("MAX_POSITION_RISK")
        if notional > equity * self.limits.max_notional_fraction and equity > 0:
            reasons.append("MAX_NOTIONAL")

        approved = not reasons
        return RiskDecision(
            approved=approved,
            reasons=tuple(reasons),
            quantity=quantity if approved else 0.0,
            risk_amount=risk_amount,
            notional=notional,
        )
