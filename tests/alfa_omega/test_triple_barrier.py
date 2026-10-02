import pandas as pd

from alfa_omega.research.triple_barrier import triple_barrier_labels


def _frame():
    idx = pd.date_range("2026-01-01", periods=5, freq="5min", tz="UTC")
    close = pd.Series([100, 100, 100, 100, 100], index=idx)
    return pd.DataFrame(
        {
            "open": close,
            "high": [100, 103, 101, 101, 101],
            "low": [100, 99, 99, 99, 99],
            "close": close,
            "atr_14": 1.0,
        },
        index=idx,
    )


def test_first_touch_target():
    labels = triple_barrier_labels(
        _frame(), horizon_bars=3, stop_atr=1, target_atr=2
    )
    assert labels.loc[_frame().index[0], "label_long_outcome"] == "TARGET"
    assert labels.loc[_frame().index[0], "label_long_r"] == 2.0


def test_same_candle_ambiguity_is_conservative_stop():
    frame = _frame()
    frame.iloc[1, frame.columns.get_loc("high")] = 103
    frame.iloc[1, frame.columns.get_loc("low")] = 98
    labels = triple_barrier_labels(frame, horizon_bars=3)
    assert labels.loc[frame.index[0], "label_long_outcome"] == "STOP"


def test_time_barrier():
    frame = _frame()
    frame["high"] = 100.5
    frame["low"] = 99.5
    labels = triple_barrier_labels(frame, horizon_bars=2)
    assert labels.loc[frame.index[0], "label_long_outcome"] == "TIME"
