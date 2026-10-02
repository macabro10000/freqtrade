import pandas as pd

from alfa_omega.research.dataset_builder import build_research_dataset


def test_dataset_builder_separates_labels():
    idx = pd.date_range("2026-01-01", periods=3, freq="5min", tz="UTC")
    features = pd.DataFrame({"rsi_14": [50, 55, 60], "future_bad": [1, 2, 3]}, index=idx)
    labels = pd.DataFrame({"label_long_r": [1.0, -1.0, 0.0]}, index=idx)
    ds, manifest = build_research_dataset(
        features, labels, market="BTC/USD", timeframe="5m"
    )
    assert "rsi_14" in ds.columns
    assert "future_bad" not in ds.columns
    assert "label_long_r" in ds.columns
    assert manifest["future_labels_are_not_features"] is True


def test_dataset_builder_requires_datetime():
    features = pd.DataFrame({"rsi_14": [50]})
    labels = pd.DataFrame({"label_long_r": [1.0]})
    try:
        build_research_dataset(features, labels, market="BTC/USD", timeframe="5m")
    except TypeError:
        return
    raise AssertionError("expected TypeError")
