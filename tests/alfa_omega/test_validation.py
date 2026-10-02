import pandas as pd

from alfa_omega.research.validation import (
    audit_feature_names,
    label_intervals,
    purged_train_mask,
)


def test_label_intervals_define_future_end_without_using_future_as_feature():
    idx = pd.date_range("2026-01-01", periods=10, freq="5min", tz="UTC")
    intervals = label_intervals(idx, 2)
    assert intervals.loc[idx[0], "prediction_time"] == idx[0]
    assert intervals.loc[idx[0], "label_end"] == idx[2]
    assert pd.isna(intervals.loc[idx[-1], "label_end"])


def test_purging_removes_overlapping_train_samples():
    idx = pd.date_range("2026-01-01", periods=20, freq="5min", tz="UTC")
    intervals = label_intervals(idx, 3)
    mask = purged_train_mask(intervals, idx[10], idx[12])
    assert not mask.loc[idx[9]]
    assert not mask.loc[idx[10]]
    assert mask.loc[idx[0]]


def test_feature_name_audit():
    result = audit_feature_names(["rsi_14", "ema_20", "future_return", "volume"])
    assert result["ok"] is False
    assert "future_return" in result["flagged_columns"]
