import pandas as pd

from alfa_omega.features.proprietary_engine import build_proprietary_features


def _frame() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=120, freq="5min", tz="UTC")
    close = pd.Series(range(100, 220), index=idx, dtype=float)
    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


def test_three_proprietary_families_exist():
    out = build_proprietary_features(_frame())
    required = {
        "prop_soberania_rel_volume_20",
        "prop_soberania_buy_confluence",
        "prop_culebra_retail_rsi_9",
        "prop_culebra_barrida_event",
        "prop_pro_rsi_9",
        "prop_pro_buy_cross",
    }
    assert required.issubset(out.columns)


def test_proprietary_features_are_causal():
    base = build_proprietary_features(_frame())
    changed = _frame()
    changed.iloc[-1, changed.columns.get_loc("close")] = 9999.0
    updated = build_proprietary_features(changed)
    for column in (
        "prop_soberania_rsi_7",
        "prop_soberania_rel_volume_20",
        "prop_culebra_retail_wholesale_distance",
        "prop_pro_rsi_9",
        "prop_pro_rsi_sma36",
    ):
        pd.testing.assert_series_equal(
            base[column].iloc[:-1],
            updated[column].iloc[:-1],
            check_names=False,
        )
