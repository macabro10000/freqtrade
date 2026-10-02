from alfa_omega.memory.learning_memory import (
    recall_errors,
    recall_similar_experiences,
    remember_error,
    remember_experience,
    remember_pattern_lessons,
)
from alfa_omega.memory.memory_store import MemoryStore
from alfa_omega.research.learning_loop import (
    ExperienceRecord,
    PatternLesson,
    ResearchError,
)


def test_learning_memory_round_trip(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    experience = ExperienceRecord(
        experience_id="EXP-1",
        timestamp="2026-01-01T00:00:00+00:00",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        decision="NO_TRADE",
        pattern_ids=("P-1",),
        feature_snapshot=(("rvol", 1.5),),
        expected_r=0.5,
        realized_r=-1.0,
        outcome="STOP",
        error_categories=("ENTRY_LATE",),
    )
    error = ResearchError(
        experiment_id="EX-1",
        category="REGIME_FAILURE",
        message="pattern failed in expansion",
    )
    lesson = PatternLesson(
        pattern_key="P-1",
        occurrences=10,
        wins=6,
        losses=4,
        expectancy_r=0.2,
        failure_categories=("ENTRY_LATE",),
    )

    remember_experience(store, experience)
    remember_error(store, error)
    assert remember_pattern_lessons(store, [lesson]) == 1

    matches = recall_similar_experiences(
        store,
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        pattern_id="P-1",
    )
    assert len(matches) == 1
    assert matches[0].payload["outcome"] == "STOP"

    failures = recall_errors(store, experiment_id="EX-1")
    assert len(failures) == 1
    assert failures[0].payload["category"] == "REGIME_FAILURE"
