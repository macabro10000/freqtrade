import pandas as pd
import pytest

from alfa_omega.features.market_sessions import add_session_features, session_context


def test_session_context_requires_timezone():
    with pytest.raises(ValueError, match="timezone-aware"):
        session_context(pd.Timestamp("2026-01-01 12:00"))


def test_session_context_handles_london_new_york_overlap():
    ts = pd.Timestamp("2026-06-15 14:00", tz="UTC")
    context = session_context(ts)
    assert "LONDON" in context["session_active"]
    assert "NEW_YORK" in context["session_active"]
    assert context["session_overlap"] == "LONDON_NEW_YORK"


def test_session_features_are_causal_timestamp_metadata():
    index = pd.date_range("2026-06-15 12:00", periods=3, freq="h", tz="UTC")
    result = add_session_features(pd.DataFrame({"close": [1, 2, 3]}, index=index))
    assert list(result["close"]) == [1, 2, 3]
    assert result["session_active_count"].tolist() == [2, 2, 2]
