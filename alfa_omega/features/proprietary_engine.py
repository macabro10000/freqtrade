"""Causal implementations of the three ALFA OMEGA proprietary indicators.

The original Pine indicators are treated as feature definitions, not as
guaranteed evidence of institutional participants. Their names are preserved
only for provenance. The outputs are continuous measurements and event flags;
they do not place orders.
"""

from __future__ import annotations

import pandas as pd


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.where(avg_loss > 0)
    return (100 - 100 / (1 + rs)).mask(
        (avg_loss == 0) & (avg_gain > 0), 100.0
    )


def _require(df: pd.DataFrame) -> None:
    missing = {"open", "high", "low", "close", "volume"}.difference(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")


def build_proprietary_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build all three proprietary indicator feature families causally."""
    _require(df)
    out = df.copy().sort_index()
    eps = 1e-12

    # ------------------------------------------------------------------
    # 1. SOBERANÍA INSTITUCIONAL - neutralized feature representation
    # ------------------------------------------------------------------
    out["prop_soberania_rel_volume_20"] = (
        out["volume"]
        / out["volume"].rolling(20, min_periods=20).mean().replace(0, pd.NA)
    )
    out["prop_soberania_rsi_7"] = _rsi(out["close"], 7)
    out["prop_soberania_rsi_extreme_high"] = (
        out["prop_soberania_rsi_7"] >= 70
    ).astype("Int64")
    out["prop_soberania_rsi_extreme_low"] = (
        out["prop_soberania_rsi_7"] <= 30
    ).astype("Int64")
    out["prop_soberania_ema_50"] = out["close"].ewm(
        span=50, adjust=False, min_periods=50
    ).mean()
    out["prop_soberania_ema_50_distance"] = (
        out["close"] / out["prop_soberania_ema_50"].replace(0, pd.NA) - 1
    )
    out["prop_soberania_ema_50_slope"] = out["prop_soberania_ema_50"].pct_change(3)
    candle_range = (out["high"] - out["low"]).clip(lower=eps)
    out["prop_soberania_body_ratio"] = (
        (out["close"] - out["open"]).abs() / candle_range
    )
    out["prop_soberania_bull_candle"] = (
        out["close"] > out["open"]
    ).astype("Int64")
    out["prop_soberania_bear_candle"] = (
        out["close"] < out["open"]
    ).astype("Int64")
    out["prop_soberania_high_volume"] = (
        out["prop_soberania_rel_volume_20"] >= 1.5
    ).astype("Int64")
    out["prop_soberania_buy_confluence"] = (
        (out["prop_soberania_high_volume"] == 1)
        & (out["prop_soberania_bull_candle"] == 1)
        & (out["prop_soberania_rsi_7"] > 50)
        & (out["close"] > out["prop_soberania_ema_50"])
    ).astype("Int64")
    out["prop_soberania_sell_confluence"] = (
        (out["prop_soberania_high_volume"] == 1)
        & (out["prop_soberania_bear_candle"] == 1)
        & (out["prop_soberania_rsi_7"] < 50)
        & (out["close"] < out["prop_soberania_ema_50"])
    ).astype("Int64")

    # ------------------------------------------------------------------
    # 2. CHOQUE DE CULEBRAS 369T
    # ------------------------------------------------------------------
    retail = _rsi(out["close"], 9)
    vol_mean_18 = out["volume"].rolling(18, min_periods=18).mean()
    vol_mean_36 = out["volume"].rolling(36, min_periods=36).mean()
    pressure_18 = 100 * (
        out["volume"] / vol_mean_18.replace(0, pd.NA)
    ).clip(upper=3) / 3
    pressure_36 = 100 * (
        out["volume"] / vol_mean_36.replace(0, pd.NA)
    ).clip(upper=3) / 3
    # Preserve causal behavior while making the two pressure series distinct
    # from the raw volume ratio.
    wholesale = pressure_18.ewm(span=5, adjust=False).mean()
    megawhale = pressure_36.ewm(span=18, adjust=False).mean()

    out["prop_culebra_retail_rsi_9"] = retail
    out["prop_culebra_wholesale_pressure"] = wholesale
    out["prop_culebra_megawhale_pressure"] = megawhale
    out["prop_culebra_retail_wholesale_distance"] = retail - wholesale
    out["prop_culebra_wholesale_megawhale_distance"] = wholesale - megawhale
    out["prop_culebra_retail_megawhale_distance"] = retail - megawhale
    out["prop_culebra_wholesale_slope"] = wholesale.diff()
    out["prop_culebra_megawhale_slope"] = megawhale.diff()
    out["prop_culebra_barrida_event"] = (
        (retail < wholesale)
        & (retail.shift(1) >= wholesale.shift(1))
        & (wholesale > 75)
    ).astype("Int64")
    out["prop_culebra_absorcion_event"] = (
        (retail > wholesale)
        & (retail.shift(1) <= wholesale.shift(1))
        & (wholesale < 25)
    ).astype("Int64")

    # ------------------------------------------------------------------
    # 3. SOBERANÍA INSTITUCIONAL PRO
    # ------------------------------------------------------------------
    rsi9 = _rsi(out["close"], 9)
    rsi_sma18 = rsi9.rolling(18, min_periods=18).mean()
    rsi_sma36 = rsi9.rolling(36, min_periods=36).mean()
    rel_volume = (
        out["volume"]
        / out["volume"].rolling(20, min_periods=20).mean().replace(0, pd.NA)
    )

    out["prop_pro_rsi_9"] = rsi9
    out["prop_pro_rsi_sma_18"] = rsi_sma18
    out["prop_pro_rsi_sma_36"] = rsi_sma36
    out["prop_pro_rsi_sma18_distance"] = rsi9 - rsi_sma18
    out["prop_pro_rsi_sma36_distance"] = rsi9 - rsi_sma36
    out["prop_pro_sma18_sma36_distance"] = rsi_sma18 - rsi_sma36
    out["prop_pro_rsi_slope"] = rsi9.diff(3)
    out["prop_pro_relative_volume_20"] = rel_volume
    out["prop_pro_overbought"] = (rsi9 >= 70).astype("Int64")
    out["prop_pro_oversold"] = (rsi9 <= 30).astype("Int64")
    out["prop_pro_high_volume"] = (rel_volume >= 1.5).astype("Int64")
    out["prop_pro_buy_cross"] = (
        (rsi9 > rsi_sma18)
        & (rsi9.shift(1) <= rsi_sma18.shift(1))
    ).astype("Int64")
    out["prop_pro_sell_cross"] = (
        (rsi9 < rsi_sma18)
        & (rsi9.shift(1) >= rsi_sma18.shift(1))
    ).astype("Int64")

    return out
