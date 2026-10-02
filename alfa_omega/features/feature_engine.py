"""Causal feature engineering for ALFA OMEGA.

All features at row t use row t or earlier. No centered windows and no future
labels are generated here. This module is intentionally deterministic so the
same OHLCV input produces the same feature frame.
"""
from __future__ import annotations

import math

import pandas as pd


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.where(avg_loss > 0.0)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # If losses are zero, RSI is conventionally 100 rather than missing.
    return rsi.mask((avg_loss == 0.0) & (avg_gain > 0.0), 100.0)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the first causal ALFA OMEGA feature set from OHLCV data."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    if df.empty:
        return df.copy()

    out = df.copy().sort_index()
    eps = 1e-12
    prev_close = out["close"].shift(1)
    candle_range = (out["high"] - out["low"]).clip(lower=eps)
    body = out["close"] - out["open"]

    out["return_1"] = out["close"].pct_change()
    ratio = out["close"] / prev_close
    out["log_return_1"] = ratio.where(ratio > 0.0).map(lambda x: math.log(x) if pd.notna(x) else pd.NA)
    out["range_pct"] = candle_range / out["close"].replace(0, pd.NA)
    out["body_pct"] = body / out["close"].replace(0, pd.NA)
    out["body_ratio"] = body.abs() / candle_range
    out["upper_wick_ratio"] = (out["high"] - out[["open", "close"]].max(axis=1)) / candle_range
    out["lower_wick_ratio"] = (out[["open", "close"]].min(axis=1) - out["low"]) / candle_range

    out["ema_20"] = out["close"].ewm(span=20, adjust=False, min_periods=20).mean()
    out["ema_50"] = out["close"].ewm(span=50, adjust=False, min_periods=50).mean()
    out["ema_distance_20"] = out["close"] / out["ema_20"] - 1.0
    out["ema_distance_50"] = out["close"] / out["ema_50"] - 1.0
    out["ema_slope_20"] = out["ema_20"].pct_change(3)
    out["rsi_7"] = _rsi(out["close"], 7)
    out["rsi_14"] = _rsi(out["close"], 14)

    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr_14"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    out["atr_pct"] = out["atr_14"] / out["close"].replace(0, pd.NA)

    out["volume_sma_20"] = out["volume"].rolling(20, min_periods=20).mean()
    out["relative_volume_20"] = out["volume"] / out["volume_sma_20"].replace(0, pd.NA)
    typical = (out["high"] + out["low"] + out["close"]) / 3.0
    out["vwap"] = (typical * out["volume"]).cumsum() / out["volume"].cumsum().replace(0, pd.NA)
    out["vwap_distance"] = out["close"] / out["vwap"] - 1.0

    prior_high_20 = out["high"].rolling(20, min_periods=20).max().shift(1)
    prior_low_20 = out["low"].rolling(20, min_periods=20).min().shift(1)
    prior_high_5 = out["high"].rolling(5, min_periods=5).max().shift(1)
    prior_low_5 = out["low"].rolling(5, min_periods=5).min().shift(1)
    out["breakout_high_20"] = (out["close"] > prior_high_20).astype(int)
    out["breakdown_low_20"] = (out["close"] < prior_low_20).astype(int)
    out["sweep_high_20"] = ((out["high"] > prior_high_20) & (out["close"] < prior_high_20)).astype(int)
    out["sweep_low_20"] = ((out["low"] < prior_low_20) & (out["close"] > prior_low_20)).astype(int)
    out["range_expansion"] = (candle_range > candle_range.rolling(20, min_periods=20).mean().shift(1) * 1.5).astype(int)

    out["fvg_bullish"] = (out["low"] > out["high"].shift(2)).astype(int)
    out["fvg_bearish"] = (out["high"] < out["low"].shift(2)).astype(int)
    out["trend_bias"] = (out["ema_20"] > out["ema_50"]).astype(int)
    out["data_quality_ok"] = (
        out[["open", "high", "low", "close", "volume"]].notna().all(axis=1)
        & (out["high"] >= out[["open", "close"]].max(axis=1))
        & (out["low"] <= out[["open", "close"]].min(axis=1))
        & (out["volume"] >= 0)
    )
    return out
