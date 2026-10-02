"""ALFA OMEGA risk controls.

Pure decision layer: no broker calls and no credentials.
""" 
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RiskLimits:
    max_position_risk_fraction: float = 0.01
    max_daily_loss_fraction: float = 0.03
    max_open_positions: int = 2
    max_notional_fraction: float = 0.25


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...]
    quantity: float
    risk_amount: float


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def evaluate(
        self,
        *,
        equity: float,
        entry_price: float,
        stop_loss: float,
        requested_quantity: float,
        open_positions: int,
        daily_pnl: float = 0.0,
    ) -> RiskDecision:
        reasons: list[str] = []

        if equity <= 0:
            reasons.append("INVALID_EQUITY")
        if entry_price <= 0 or stop_loss <= 0:
            reasons.append("INVALID_PRICE")
        if requested_quantity <= 0:
            reasons.append("INVALID_QUANTITY")
        if open_positions >= self.limits.max_open_positions:
            reasons.append("MAX_OPEN_POSITIONS")
        if daily_pnl <= -(equity * self.limits.max_daily_loss_fraction):
            reasons.append("MAX_DAILY_LOSS")

        stop_distance = abs(entry_price - stop_loss)
        risk_amount = stop_distance * max(requested_quantity, 0.0)

        if equity > 0 and risk_amount > equity * self.limits.max_position_risk_fraction:
            reasons.append("MAX_POSITION_RISK")

        notional = entry_price * max(requested_quantity, 0.0)
        if equity > 0 and notional > equity * self.limits.max_notional_fraction:
            reasons.append("MAX_NOTIONAL")

        approved = not reasons
        return RiskDecision(
            approved=approved,
            reasons=tuple(reasons),
            quantity=requested_quantity if approved else 0.0,
            risk_amount=risk_amount,
        )
