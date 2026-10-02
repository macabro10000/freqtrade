"""Market Intelligence Engine for ALFA OMEGA.

Transforms causal features from price, volume, SMC, liquidity, proprietary
indicators and multi-timeframe context into a machine-readable market state.
This layer describes evidence; it does not place orders or declare a trade
winner.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _num(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def _flag(df: pd.DataFrame, column: str) -> pd.Series:
    return _num(df, column).gt(0)


def build_market_intelligence(df: pd.DataFrame) -> pd.DataFrame:
    """Build a causal market-state representation."""
    if df.empty:
        return df.copy()

    out = df.copy().sort_index()

    ema20 = _num(out, "ema_20")
    ema50 = _num(out, "ema_50")
    close = _num(out, "close")
    atr_pct = _num(out, "atr_pct")
    rel_volume = _num(out, "relative_volume_20")
    rsi = _num(out, "rsi_14", 50)

    trend = pd.Series(0, index=out.index, dtype="int64")
    trend = trend.mask((close > ema20) & (ema20 > ema50), 1)
    trend = trend.mask((close < ema20) & (ema20 < ema50), -1)

    structure = _num(out, "structure_bias").astype("int64")
    liquidity_pressure = (
        _flag(out, "liquidity_sweep_low").astype(int)
        - _flag(out, "liquidity_sweep_high").astype(int)
    )

    momentum = pd.Series(0, index=out.index, dtype="int64")
    momentum = momentum.mask(rsi >= 55, 1)
    momentum = momentum.mask(rsi <= 45, -1)

    volume_state = pd.Series(0, index=out.index, dtype="int64")
    volume_state = volume_state.mask(rel_volume >= 1.5, 1)
    volume_state = volume_state.mask(rel_volume <= 0.75, -1)

    volatility_state = pd.Series(0, index=out.index, dtype="int64")
    atr_median = atr_pct.rolling(50, min_periods=20).median()
    volatility_state = volatility_state.mask(atr_pct > atr_median * 1.5, 1)
    volatility_state = volatility_state.mask(atr_pct < atr_median * 0.7, -1)

    event_score = (
        _flag(out, "bos_bullish").astype(int)
        - _flag(out, "bos_bearish").astype(int)
        + _flag(out, "choch_bullish").astype(int)
        - _flag(out, "choch_bearish").astype(int)
        + liquidity_pressure
        + _flag(out, "fvg_bullish_smc").astype(int)
        - _flag(out, "fvg_bearish_smc").astype(int)
        + _flag(out, "displacement").astype(int) * structure
    )

    proprietary_score = (
        _flag(out, "prop_soberania_buy_confluence").astype(int)
        - _flag(out, "prop_soberania_sell_confluence").astype(int)
        + _flag(out, "prop_culebra_absorcion_event").astype(int)
        - _flag(out, "prop_culebra_barrida_event").astype(int)
        + _flag(out, "prop_pro_buy_cross").astype(int)
        - _flag(out, "prop_pro_sell_cross").astype(int)
    )

    # Higher-timeframe evidence is deliberately explicit. A missing timeframe
    # contributes neutral evidence rather than being treated as bearish/bullish.
    htf_columns = [c for c in out.columns if c.startswith("htf_") and c.endswith("_direction")]
    htf_sum = pd.Series(0, index=out.index, dtype="int64")
    htf_count = pd.Series(0, index=out.index, dtype="int64")
    for column in htf_columns:
        values = pd.to_numeric(out[column], errors="coerce")
        direction = values.where(values.isin([0, 1]), pd.NA)
        # htf direction is 1 for bullish and 0 for non-bullish; derive bearish
        # from close/open when available.
        tf = column.removeprefix("htf_").removesuffix("_direction")
        htf_close = _num(out, f"htf_{tf}_close", float("nan"))
        htf_open = _num(out, f"htf_{tf}_open", float("nan"))
        signed = pd.Series(0, index=out.index, dtype="int64")
        signed = signed.mask(htf_close > htf_open, 1)
        signed = signed.mask(htf_close < htf_open, -1)
        valid = htf_close.notna() & htf_open.notna()
        htf_sum += signed
        htf_count += valid.astype(int)

    htf_alignment = (htf_sum / htf_count.replace(0, pd.NA)).fillna(0.0)

    out["mi_trend_state"] = trend
    out["mi_structure_state"] = structure
    out["mi_momentum_state"] = momentum
    out["mi_volume_state"] = volume_state
    out["mi_volatility_state"] = volatility_state
    out["mi_liquidity_pressure"] = liquidity_pressure
    out["mi_event_score"] = event_score
    out["mi_proprietary_score"] = proprietary_score
    out["mi_htf_alignment"] = htf_alignment
    out["mi_evidence_score"] = (
        trend + structure + momentum + volume_state + liquidity_pressure
        + proprietary_score + event_score
    )

    score = out["mi_evidence_score"]
    out["mi_market_bias"] = 0
    out.loc[score >= 3, "mi_market_bias"] = 1
    out.loc[score <= -3, "mi_market_bias"] = -1

    out["mi_regime"] = "NEUTRAL"
    out.loc[(trend != 0) & (volatility_state >= 0), "mi_regime"] = "TREND"
    out.loc[(trend == 0) & (volatility_state == -1), "mi_regime"] = "RANGE_LOW_VOL"
    out.loc[(volatility_state == 1) & (_flag(out, "displacement")), "mi_regime"] = "EXPANSION"
    out.loc[
        _flag(out, "liquidity_sweep_high") | _flag(out, "liquidity_sweep_low"),
        "mi_regime",
    ] = "LIQUIDITY_EVENT"

    out["mi_alignment_quality"] = (
        1.0 - (abs(trend - structure) / 2.0)
    ).clip(0.0, 1.0)

    return out


def latest_market_state(df: pd.DataFrame) -> dict[str, Any]:
    """Return an explainable latest market-state snapshot."""
    if df.empty:
        return {"status": "empty"}
    row = build_market_intelligence(df).iloc[-1]
    fields = [
        "mi_market_bias",
        "mi_regime",
        "mi_evidence_score",
        "mi_htf_alignment",
        "mi_alignment_quality",
        "mi_trend_state",
        "mi_structure_state",
        "mi_momentum_state",
        "mi_volume_state",
        "mi_volatility_state",
        "mi_liquidity_pressure",
        "mi_event_score",
        "mi_proprietary_score",
    ]
    return {
        "status": "ok",
        "state": {field: row.get(field) for field in fields},
    }
