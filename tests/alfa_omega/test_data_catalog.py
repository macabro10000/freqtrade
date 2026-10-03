import pandas as pd
import pytest

from alfa_omega.data.data_catalog import (
    build_data_catalog_entry,
    inspect_data_quality,
)


def _frame(index):
    return pd.DataFrame(
        {
            "open": [100.0] * len(index),
            "high": [101.0] * len(index),
            "low": [99.0] * len(index),
            "close": [100.5] * len(index),
            "volume": [10.0] * len(index),
        },
        index=index,
    )


def test_catalog_ready_for_clean_utc_data():
    index = pd.date_range("2026-01-01", periods=3, freq="5min", tz="UTC")
    quality = inspect_data_quality(_frame(index), "5m")
    assert quality.status == "READY"
    assert quality.gap_count == 0


def test_catalog_warns_on_gap():
    index = pd.DatetimeIndex(
        [
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:05:00Z",
            "2026-01-01T00:20:00Z",
        ]
    )
    quality = inspect_data_quality(_frame(index), "5m")
    assert quality.status == "READY_WITH_WARNINGS"
    assert quality.gap_count == 1


def test_catalog_marks_duplicate_timestamp_corrupted():
    index = pd.DatetimeIndex(
        [
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
        ]
    )
    quality = inspect_data_quality(_frame(index), "5m")
    assert quality.status == "CORRUPTED"
    assert quality.duplicate_timestamps == 2


def test_catalog_rejects_invalid_ohlc():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    frame = _frame(index)
    frame.loc[:, "high"] = 98.0
    quality = inspect_data_quality(frame, "5m")
    assert quality.status == "CORRUPTED"
    assert quality.invalid_ohlc == 1


def test_catalog_manifest_contains_identity():
    index = pd.date_range("2026-01-01", periods=2, freq="1h", tz="UTC")
    manifest = build_data_catalog_entry(
        _frame(index),
        market="BTC/USD",
        timeframe="1h",
        source="unit-test",
    )
    assert manifest["market"] == "BTC/USD"
    assert manifest["timeframe"] == "1h"
    assert manifest["source_sha256"] is None
    assert manifest["quality"]["status"] == "READY"


def test_catalog_requires_ohlcv():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    frame = _frame(index).drop(columns="volume")
    with pytest.raises(ValueError, match="missing OHLCV"):
        inspect_data_quality(frame, "5m")
