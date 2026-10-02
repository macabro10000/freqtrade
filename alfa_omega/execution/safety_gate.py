"""ALFA OMEGA Safety Gate.

Final pre-execution barrier. No broker calls.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyContext:
    mode: str
    market: str
    allowed_markets: tuple[str, ...]
    broker_healthy: bool
    data_fresh: bool
    kill_switch: bool
    risk_approved: bool
    stop_loss_valid: bool
    take_profit_valid: bool


@dataclass(frozen=True)
class SafetyDecision:
    approved: bool
    reasons: tuple[str, ...]


class SafetyGate:
    """Rejects unsafe execution requests before any broker adapter is called."""

    def evaluate(self, context: SafetyContext) -> SafetyDecision:
        reasons: list[str] = []

        if context.mode not in {"PAPER", "LIVE"}:
            reasons.append("INVALID_EXECUTION_MODE")

        if context.market not in context.allowed_markets:
            reasons.append("MARKET_NOT_ALLOWED")

        if not context.broker_healthy:
            reasons.append("BROKER_UNHEALTHY")

        if not context.data_fresh:
            reasons.append("STALE_DATA")

        if not context.kill_switch:
            reasons.append("KILL_SWITCH_ACTIVE")

        if not context.risk_approved:
            reasons.append("RISK_NOT_APPROVED")

        if not context.stop_loss_valid:
            reasons.append("INVALID_STOP_LOSS")

        if not context.take_profit_valid:
            reasons.append("INVALID_TAKE_PROFIT")

        # Live is deliberately blocked until a later, explicit promotion.
        if context.mode == "LIVE":
            reasons.append("LIVE_EXECUTION_BLOCKED")

        return SafetyDecision(approved=not reasons, reasons=tuple(reasons))
