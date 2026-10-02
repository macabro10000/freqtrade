from __future__ import annotations

import pandas as pd

from alfa_omega.features.feature_engine import build_features


def test_feature_engine_is_causal_and_contains_core_features() -> None:
    index = pd.date_range("2026-01-01", periods=80, freq="5min", tz="UTC")
    close = pd.Series(range(100, 180), index=index, dtype=float)
    frame = pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=index,
    )
    features = build_features(frame)
    required = {
        "rsi_7",
        "ema_20",
        "ema_50",
        "atr_14",
        "relative_volume_20",
        "vwap",
        "breakout_high_20",
        "sweep_high_20",
        "fvg_bullish",
        "data_quality_ok",
    }
    assert required.issubset(features.columns)
    assert bool(features["data_quality_ok"].iloc[-1])


def test_future_row_change_does_not_change_prior_feature() -> None:
    index = pd.date_range("2026-01-01", periods=80, freq="5min", tz="UTC")
    close = pd.Series(range(100, 180), index=index, dtype=float)
    frame = pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=index,
    )
    base = build_features(frame)
    changed = frame.copy()
    changed.iloc[-1, changed.columns.get_loc("close")] = 9999.0
    changed_features = build_features(changed)
    check_row = -2
    for column in ("ema_20", "ema_50", "rsi_7", "atr_14", "vwap", "relative_volume_20"):
        assert base[column].iloc[check_row] == changed_features[column].iloc[check_row]
