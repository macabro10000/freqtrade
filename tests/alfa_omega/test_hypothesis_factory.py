import pandas as pd

from alfa_omega.research.hypothesis_factory import (
    generate_hypotheses,
    hypothesis_to_dict,
)
from alfa_omega.research.learning_loop import PatternLesson


def test_hypothesis_factory_is_reproducible():
    lessons = [
        PatternLesson("CHOCH_BULL", 50, 32, 18, 0.24),
        PatternLesson("FVG_BULL", 45, 29, 16, 0.18),
        PatternLesson("RVOL_HIGH", 60, 36, 24, 0.11),
        PatternLesson("WEAK", 100, 40, 60, -0.05),
    ]
    first = generate_hypotheses(
        lessons,
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        min_occurrences=20,
        max_conditions=2,
    )
    second = generate_hypotheses(
        lessons,
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        min_occurrences=20,
        max_conditions=2,
    )
    assert first
    assert [hyp.hypothesis_id for hyp in first] == [
        hyp.hypothesis_id for hyp in second
    ]
    assert all(hyp.state == "RESEARCH_CANDIDATE" for hyp in first)
    assert all("WEAK" not in hyp.conditions for hyp in first)
    assert "hypothesis_id" in hypothesis_to_dict(first[0])


def test_hypothesis_factory_requires_evidence_floor():
    lessons = [
        PatternLesson("LOW_N", 5, 4, 1, 0.8),
        PatternLesson("NEGATIVE", 30, 10, 20, -0.2),
    ]
    hypotheses = generate_hypotheses(
        lessons,
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        min_occurrences=20,
    )
    assert hypotheses == []
