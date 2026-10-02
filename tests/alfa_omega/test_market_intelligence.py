import pandas as pd

from alfa_omega.intelligence.market_intelligence import build_market_intelligence


def _frame():
    idx = pd.date_range("2026-01-01", periods=100, freq="5min", tz="UTC")
    close = pd.Series(range(100, 200), index=idx, dtype=float)
    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
            "ema_20": close - 1,
            "ema_50": close - 2,
            "atr_pct": 0.01,
            "relative_volume_20": 1.0,
            "rsi_14": 60.0,
            "structure_bias": 1,
            "bos_bullish": 1,
            "bos_bearish": 0,
            "choch_bullish": 0,
            "choch_bearish": 0,
            "liquidity_sweep_low": 1,
            "liquidity_sweep_high": 0,
            "fvg_bullish_smc": 1,
            "fvg_bearish_smc": 0,
            "displacement": 1,
            "prop_soberania_buy_confluence": 1,
            "prop_soberania_sell_confluence": 0,
            "prop_culebra_absorcion_event": 1,
            "prop_culebra_barrida_event": 0,
            "prop_pro_buy_cross": 1,
            "prop_pro_sell_cross": 0,
        },
        index=idx,
    )


def test_market_intelligence_contains_state():
    out = build_market_intelligence(_frame())
    required = {
        "mi_market_bias",
        "mi_regime",
        "mi_evidence_score",
        "mi_htf_alignment",
        "mi_alignment_quality",
    }
    assert required.issubset(out.columns)
    assert out["mi_market_bias"].iloc[-1] == 1


def test_market_intelligence_is_causal():
    base = build_market_intelligence(_frame())
    changed = _frame()
    changed.iloc[-1, changed.columns.get_loc("close")] = 9999.0
    updated = build_market_intelligence(changed)
    for col in ("mi_market_bias", "mi_evidence_score", "mi_regime"):
        assert base[col].iloc[:-1].equals(updated[col].iloc[:-1])
