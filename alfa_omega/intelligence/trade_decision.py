"""Explainable trade decision engine for ALFA OMEGA.

This layer converts market evidence into a BUY/SELL/HOLD decision and a
bounded risk plan. It does not submit orders. Execution remains a separate,
explicitly gated layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class TradeDecision:
    action: str
    market: str
    timeframe: str
    confidence: float
    evidence_score: float
    thesis: str
    entry_price: float | None
    stop_price: float | None
    target_price: float | None
    risk_fraction: float
    reasons: tuple[str, ...]
    status: str = "DECISION_ONLY"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _latest_number(row: pd.Series, name: str) -> float | None:
    value = row.get(name)
    if value is None or pd.isna(value):
        return None
    return float(value)


def _decision_confidence(score: float, alignment: float) -> float:
    raw = (abs(score) / 10.0) * 0.7 + max(0.0, min(1.0, alignment)) * 0.3
    return max(0.0, min(1.0, raw))


def decide_trade(
    frame: pd.DataFrame,
    *,
    market: str,
    timeframe: str,
    min_score: float = 4.0,
    max_risk_fraction: float = 0.005,
) -> TradeDecision:
    """Evaluate the latest causal intelligence row without submitting an order."""
    if frame.empty:
        return TradeDecision(
            action="HOLD",
            market=market,
            timeframe=timeframe,
            confidence=0.0,
            evidence_score=0.0,
            thesis="No market data available.",
            entry_price=None,
            stop_price=None,
            target_price=None,
            risk_fraction=0.0,
            reasons=("EMPTY_DATA",),
        )

    row = frame.iloc[-1]
    score = _latest_number(row, "mi_evidence_score") or 0.0
    bias = _latest_number(row, "mi_market_bias") or 0.0
    alignment = _latest_number(row, "mi_alignment_quality") or 0.0
    atr = _latest_number(row, "atr_14")
    close = _latest_number(row, "close")
    regime = str(row.get("mi_regime", "NEUTRAL"))

    reasons: list[str] = []
    if bias > 0:
        reasons.append("BULLISH_EVIDENCE")
    elif bias < 0:
        reasons.append("BEARISH_EVIDENCE")
    else:
        reasons.append("NEUTRAL_EVIDENCE")

    if alignment >= 0.75:
        reasons.append("STRUCTURE_TREND_ALIGNED")
    elif alignment < 0.5:
        reasons.append("STRUCTURE_TREND_MISALIGNED")

    reasons.append(f"REGIME_{regime}")

    confidence = _decision_confidence(score, alignment)
    risk = max(0.0, min(max_risk_fraction, max_risk_fraction * confidence))

    if close is None or atr is None or atr <= 0:
        return TradeDecision(
            action="HOLD",
            market=market,
            timeframe=timeframe,
            confidence=confidence,
            evidence_score=score,
            thesis="Insufficient price/ATR data to define a bounded trade.",
            entry_price=close,
            stop_price=None,
            target_price=None,
            risk_fraction=0.0,
            reasons=tuple(reasons + ["MISSING_RISK_GEOMETRY"]),
        )

    if regime == "RANGE_LOW_VOL":
        reasons.append("LOW_VOLATILITY_RANGE")
        return TradeDecision(
            action="HOLD",
            market=market,
            timeframe=timeframe,
            confidence=confidence,
            evidence_score=score,
            thesis="Range regime is not sufficient for directional entry.",
            entry_price=close,
            stop_price=None,
            target_price=None,
            risk_fraction=0.0,
            reasons=tuple(reasons),
        )

    if score >= min_score and bias > 0:
        reasons.append("LONG_THRESHOLD_MET")
        return TradeDecision(
            action="BUY",
            market=market,
            timeframe=timeframe,
            confidence=confidence,
            evidence_score=score,
            thesis="Causal evidence supports a bullish directional hypothesis.",
            entry_price=close,
            stop_price=close - atr,
            target_price=close + (2.0 * atr),
            risk_fraction=risk,
            reasons=tuple(reasons),
        )

    if score <= -min_score and bias < 0:
        reasons.append("SHORT_THRESHOLD_MET")
        return TradeDecision(
            action="SELL",
            market=market,
            timeframe=timeframe,
            confidence=confidence,
            evidence_score=score,
            thesis="Causal evidence supports a bearish directional hypothesis.",
            entry_price=close,
            stop_price=close + atr,
            target_price=close - (2.0 * atr),
            risk_fraction=risk,
            reasons=tuple(reasons),
        )

    reasons.append("THRESHOLD_NOT_MET")
    return TradeDecision(
        action="HOLD",
        market=market,
        timeframe=timeframe,
        confidence=confidence,
        evidence_score=score,
        thesis="Evidence is not strong enough for directional entry.",
        entry_price=close,
        stop_price=None,
        target_price=None,
        risk_fraction=0.0,
        reasons=tuple(reasons),
    )


def decision_from_market_state(
    state: dict[str, Any],
    *,
    market: str,
    timeframe: str,
) -> TradeDecision:
    """Create a decision from a previously generated market-state snapshot."""
    values = state.get("state", {})
    frame = pd.DataFrame([values])
    return decide_trade(
        frame,
        market=market,
        timeframe=timeframe,
    )
