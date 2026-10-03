"""Position exit intelligence and trade-outcome capture for ALFA OMEGA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import pandas as pd


@dataclass(frozen=True)
class ExitDecision:
    action: str
    reason: str
    price: float | None
    thesis_valid: bool
    status: str = "DECISION_ONLY"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TradeOutcome:
    trade_id: str
    market: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees: float
    slippage: float
    net_pnl: float
    entry_reason: str
    exit_reason: str
    expected_target: float | None
    expected_stop: float | None
    regime: str
    outcome: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def decide_exit(
    frame: pd.DataFrame,
    *,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float | None,
) -> ExitDecision:
    """Reevaluate an open position using the latest causal market evidence."""
    if frame.empty:
        return ExitDecision("HOLD", "NO_DATA", None, True)

    row = frame.iloc[-1]
    close = row.get("close")
    if close is None or pd.isna(close):
        return ExitDecision("HOLD", "NO_CURRENT_PRICE", None, True)

    price = float(close)
    normalized = side.upper()
    if normalized == "LONG":
        if price <= stop_price:
            return ExitDecision("EXIT", "HARD_STOP_REACHED", price, False)
        if target_price is not None and price >= target_price:
            return ExitDecision("EXIT", "PROFIT_TARGET_REACHED", price, True)
        if float(row.get("mi_market_bias", 0)) < 0:
            return ExitDecision("EXIT", "THESIS_INVALIDATED_BEARISH_BIAS", price, False)
    elif normalized == "SHORT":
        if price >= stop_price:
            return ExitDecision("EXIT", "HARD_STOP_REACHED", price, False)
        if target_price is not None and price <= target_price:
            return ExitDecision("EXIT", "PROFIT_TARGET_REACHED", price, True)
        if float(row.get("mi_market_bias", 0)) > 0:
            return ExitDecision("EXIT", "THESIS_INVALIDATED_BULLISH_BIAS", price, False)
    else:
        raise ValueError("side must be LONG or SHORT")

    return ExitDecision("HOLD", "THESIS_STILL_VALID", price, True)


def calculate_trade_outcome(
    *,
    trade_id: str,
    market: str,
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    fees: float = 0.0,
    slippage: float = 0.0,
    entry_reason: str = "",
    exit_reason: str = "",
    expected_target: float | None = None,
    expected_stop: float | None = None,
    regime: str = "UNKNOWN",
) -> TradeOutcome:
    if entry_price <= 0 or exit_price <= 0 or quantity <= 0:
        raise ValueError("entry_price, exit_price and quantity must be positive")
    direction = 1.0 if side.upper() == "LONG" else -1.0
    gross = (exit_price - entry_price) * quantity * direction
    net = gross - abs(fees) - abs(slippage)
    outcome = "WIN" if net > 0 else "LOSS" if net < 0 else "BREAKEVEN"
    return TradeOutcome(
        trade_id=trade_id,
        market=market,
        side=side.upper(),
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        gross_pnl=gross,
        fees=abs(fees),
        slippage=abs(slippage),
        net_pnl=net,
        entry_reason=entry_reason,
        exit_reason=exit_reason,
        expected_target=expected_target,
        expected_stop=expected_stop,
        regime=regime,
        outcome=outcome,
    )
