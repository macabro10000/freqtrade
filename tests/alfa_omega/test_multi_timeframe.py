import pandas as pd

from alfa_omega.features.multi_timeframe import (
    build_market_map,
    child_count,
    describe_hierarchy,
)


def _frame(start: str, periods: int, freq: str, base: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range(start, periods=periods, freq=freq, tz="UTC")
    close = pd.Series(range(periods), index=idx, dtype=float) + base
    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1.0,
        },
        index=idx,
    )


def test_hierarchy_counts():
    assert child_count("1w", "1d") == 7
    assert child_count("1d", "4h") == 6
    assert child_count("4h", "1h") == 4
    assert child_count("1h", "15m") == 4
    assert child_count("15m", "5m") == 3
    assert child_count("5m", "1m") == 5


def test_higher_timeframe_is_not_visible_before_close():
    weekly = _frame("2026-01-05 00:00", 2, "7D", 100)
    daily = _frame("2026-01-05 00:00", 10, "1D", 200)
    mapped = build_market_map(
        {"1w": weekly, "1d": daily},
        target_timeframe="1d",
    )

    # The weekly candle opened Monday and closes the following Monday.
    assert pd.isna(mapped.loc[pd.Timestamp("2026-01-05", tz="UTC"), "htf_1w_close"])
    assert mapped.loc[
        pd.Timestamp("2026-01-12", tz="UTC"), "htf_1w_close"
    ] == weekly.iloc[0]["close"]


def test_higher_timeframe_context_is_causal():
    daily = _frame("2026-01-01", 10, "1D", 200)
    four_hour = _frame("2026-01-01", 60, "4h", 100)
    mapped = build_market_map(
        {"1d": daily, "4h": four_hour},
        target_timeframe="4h",
    )
    assert "htf_1d_close" in mapped.columns
    first = pd.Timestamp("2026-01-01 00:00", tz="UTC")
    assert pd.isna(mapped.loc[first, "htf_1d_close"])


def test_description():
    data = describe_hierarchy()
    assert data["order"] == ["1w", "1d", "4h", "1h", "15m", "5m", "1m"]
