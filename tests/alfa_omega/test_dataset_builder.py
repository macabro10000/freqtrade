import pandas as pd
import pytest

from alfa_omega.research.dataset_builder import build_research_dataset


def _idx():
    return pd.date_range("2026-01-01", periods=3, freq="5min", tz="UTC")


def test_dataset_builder_separates_labels_and_suspicious_features():
    idx = _idx()
    features = pd.DataFrame(
        {"rsi_14": [50, 55, 60], "future_bad": [1, 2, 3]},
        index=idx,
    )
    labels = pd.DataFrame({"label_long_r": [1.0, -1.0, 0.0]}, index=idx)
    ds, manifest = build_research_dataset(
        features, labels, market="BTC/USD", timeframe="5m"
    )
    assert "rsi_14" in ds.columns
    assert "future_bad" not in ds.columns
    assert "label_long_r" in ds.columns
    assert "future_bad" in manifest["rejected_feature_columns"]
    assert manifest["future_labels_are_not_features"] is True


def test_dataset_builder_requires_timezone_aware_utc_index():
    idx = pd.date_range("2026-01-01", periods=1, freq="5min")
    features = pd.DataFrame({"rsi_14": [50]}, index=idx)
    labels = pd.DataFrame({"label_long_r": [1.0]}, index=idx)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_research_dataset(features, labels, market="BTC/USD", timeframe="5m")


def test_dataset_builder_rejects_duplicate_timestamps():
    idx = pd.DatetimeIndex(
        ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"]
    )
    features = pd.DataFrame({"rsi_14": [50, 51]}, index=idx)
    labels = pd.DataFrame(
        {"label_long_r": [1.0, 0.0]},
        index=idx,
    )
    with pytest.raises(ValueError, match="duplicate"):
        build_research_dataset(features, labels, market="BTC/USD", timeframe="5m")
