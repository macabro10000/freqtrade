"""Causal SMC and liquidity feature engine.

Every feature at candle t uses only candle t or earlier. Structure events are
confirmed on the candle where the relevant prior swing is broken; no future
bars are used to retroactively label an earlier candle.
"""
from __future__ import annotations

import pandas as pd


def build_structure_features(df: pd.DataFrame, swing_window: int = 3) -> pd.DataFrame:
    """Add causal HH/HL/LH/LL, BOS/CHOCH, liquidity and FVG features."""
    required = {"open", "high", "low", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing OHLC columns: {sorted(missing)}")
    if swing_window < 1:
        raise ValueError("swing_window must be >= 1")
    if df.empty:
        return df.copy()

    out = df.copy().sort_index()
    w = int(swing_window)

    # Confirm a pivot only after w bars have elapsed. The pivot price itself
    # comes from the historical window ending at t-w, so no future value leaks.
    pivot_high = out["high"].shift(w).rolling(2 * w + 1, min_periods=2 * w + 1).max()
    pivot_low = out["low"].shift(w).rolling(2 * w + 1, min_periods=2 * w + 1).min()
    pivot_high_confirmed = (out["high"].shift(w) == pivot_high).astype(int)
    pivot_low_confirmed = (out["low"].shift(w) == pivot_low).astype(int)

    ph_price = out["high"].shift(w).where(pivot_high_confirmed.eq(1))
    pl_price = out["low"].shift(w).where(pivot_low_confirmed.eq(1))
    last_ph = ph_price.ffill()
    last_pl = pl_price.ffill()
    prev_ph = ph_price.where(ph_price.notna()).shift(1).ffill()
    prev_pl = pl_price.where(pl_price.notna()).shift(1).ffill()

    out["swing_high_confirmed"] = pivot_high_confirmed
    out["swing_low_confirmed"] = pivot_low_confirmed
    out["swing_high_price"] = last_ph
    out["swing_low_price"] = last_pl
    out["hh"] = (ph_price > prev_ph).fillna(False).astype(int)
    out["lh"] = (ph_price < prev_ph).fillna(False).astype(int)
    out["hl"] = (pl_price > prev_pl).fillna(False).astype(int)
    out["ll"] = (pl_price < prev_pl).fillna(False).astype(int)

    prior_structure_high = last_ph.shift(1)
    prior_structure_low = last_pl.shift(1)
    out["bos_bullish"] = (out["close"] > prior_structure_high).fillna(False).astype(int)
    out["bos_bearish"] = (out["close"] < prior_structure_low).fillna(False).astype(int)

    direction = pd.Series(0, index=out.index, dtype="int64")
    direction = direction.mask(out["bos_bullish"].eq(1), 1)
    direction = direction.mask(out["bos_bearish"].eq(1), -1)
    direction = direction.replace(0, pd.NA).ffill().fillna(0).astype(int)
    prev_direction = direction.shift(1).fillna(0)
    out["choch_bullish"] = ((direction == 1) & (prev_direction == -1)).astype(int)
    out["choch_bearish"] = ((direction == -1) & (prev_direction == 1)).astype(int)
    out["structure_bias"] = direction

    out["liquidity_high_20"] = out["high"].rolling(20, min_periods=20).max().shift(1)
    out["liquidity_low_20"] = out["low"].rolling(20, min_periods=20).min().shift(1)
    out["liquidity_sweep_high"] = ((out["high"] > out["liquidity_high_20"]) & (out["close"] < out["liquidity_high_20"])).astype(int)
    out["liquidity_sweep_low"] = ((out["low"] < out["liquidity_low_20"]) & (out["close"] > out["liquidity_low_20"])).astype(int)

    # Three-candle fair-value-gap conditions. Only the current candle and two
    # already closed candles are referenced.
    out["fvg_bullish_smc"] = (out["low"] > out["high"].shift(2)).astype(int)
    out["fvg_bearish_smc"] = (out["high"] < out["low"].shift(2)).astype(int)
    out["fvg_bullish_size"] = (out["low"] - out["high"].shift(2)).clip(lower=0.0)
    out["fvg_bearish_size"] = (out["low"].shift(2) - out["high"]).clip(lower=0.0)

    out["displacement"] = (
        (out["high"] - out["low"]) >
        (out["high"] - out["low"]).rolling(20, min_periods=20).mean().shift(1) * 1.5
    ).astype(int)

    return out
