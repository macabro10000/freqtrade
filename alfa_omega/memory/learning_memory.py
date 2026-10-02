"""Memory integration for ALFA OMEGA learning.

Converts immutable research experiences/errors into persistent memory and
retrieves comparable historical experiences before new research decisions.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from alfa_omega.memory.memory_store import MemoryStore
from alfa_omega.research.learning_loop import (
    ExperienceRecord,
    PatternLesson,
    ResearchError,
)


def remember_experience(store: MemoryStore, record: ExperienceRecord):
    return store.remember(
        "EXPERIENCE",
        asdict(record),
        source="learning_loop",
    )


def remember_error(store: MemoryStore, error: ResearchError):
    return store.remember(
        "ERROR",
        asdict(error),
        source="learning_loop",
    )


def remember_pattern_lessons(
    store: MemoryStore,
    lessons: Iterable[PatternLesson],
) -> int:
    count = 0
    for lesson in lessons:
        store.remember(
            "PATTERN_LESSON",
            asdict(lesson),
            source="learning_loop",
        )
        count += 1
    return count


def recall_similar_experiences(
    store: MemoryStore,
    *,
    market: str,
    timeframe: str,
    regime: str | None = None,
    pattern_id: str | None = None,
    limit: int = 50,
):
    return store.search(
        record_type="EXPERIENCE",
        market=market,
        timeframe=timeframe,
        regime=regime,
        pattern_id=pattern_id,
        limit=limit,
    )


def recall_errors(
    store: MemoryStore,
    *,
    experiment_id: str | None = None,
    limit: int = 50,
):
    records = store.search(record_type="ERROR", limit=limit)
    if experiment_id is None:
        return records
    return [
        record
        for record in records
        if record.payload.get("experiment_id") == experiment_id
    ]
