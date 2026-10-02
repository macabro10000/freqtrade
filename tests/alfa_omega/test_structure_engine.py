import pandas as pd

from alfa_omega.smc.structure_engine import build_structure_features


def _frame(n: int = 80) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC")
    close = pd.Series(range(100, 100 + n), index=idx, dtype=float)
    return pd.DataFrame({
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": 1.0,
    })


def test_structure_features_exist_and_are_causal():
    frame = _frame()
    a = build_structure_features(frame, swing_window=3)
    changed = frame.copy()
    changed.iloc[-1, changed.columns.get_loc("high")] += 10000
    changed.iloc[-1, changed.columns.get_loc("low")] -= 10000
    b = build_structure_features(changed, swing_window=3)
    cols = ["swing_high_confirmed", "swing_low_confirmed", "hh", "lh", "hl", "ll", "bos_bullish", "bos_bearish", "structure_bias"]
    assert a[cols].iloc[:-1].equals(b[cols].iloc[:-1])
    assert {"liquidity_sweep_high", "liquidity_sweep_low", "fvg_bullish_smc", "fvg_bearish_smc", "displacement"}.issubset(a.columns)


def test_no_future_bar_is_used_by_fvg_or_liquidity():
    frame = _frame()
    out = build_structure_features(frame)
    assert out["fvg_bullish_smc"].iloc[0] == 0
    assert out["fvg_bearish_smc"].iloc[0] == 0
    assert pd.isna(out["liquidity_high_20"].iloc[0])
