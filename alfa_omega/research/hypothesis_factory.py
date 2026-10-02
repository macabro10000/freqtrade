"""Hypothesis factory for ALFA OMEGA research.

Generates reproducible, interpretable research hypotheses from observed
pattern lessons. It never promotes a hypothesis, changes live code, or places
orders. Every generated hypothesis must pass the existing validation gates.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from itertools import combinations

from alfa_omega.research.learning_loop import PatternLesson


@dataclass(frozen=True)
class ResearchHypothesis:
    hypothesis_id: str
    market: str
    timeframe: str
    regime: str
    conditions: tuple[str, ...]
    question: str
    rationale: tuple[str, ...]
    source_patterns: tuple[str, ...]
    state: str = "RESEARCH_CANDIDATE"


def _hypothesis_id(
    market: str,
    timeframe: str,
    regime: str,
    conditions: Sequence[str],
) -> str:
    payload = "|".join(
        [market, timeframe, regime, *sorted(str(x) for x in conditions)]
    )
    return "H-" + sha256(payload.encode("utf-8")).hexdigest()[:12].upper()


def generate_hypotheses(
    lessons: Iterable[PatternLesson],
    *,
    market: str,
    timeframe: str,
    regime: str,
    min_occurrences: int = 20,
    min_expectancy_r: float = 0.0,
    max_conditions: int = 3,
) -> list[ResearchHypothesis]:
    """Generate small, reproducible hypotheses from empirical pattern lessons.

    Only lessons meeting the supplied evidence floor become inputs to the
    hypothesis generator. The output remains a research candidate.
    """
    eligible = [
        lesson
        for lesson in lessons
        if lesson.occurrences >= min_occurrences
        and lesson.expectancy_r > min_expectancy_r
    ]
    if not eligible:
        return []

    names = sorted({lesson.pattern_key for lesson in eligible})
    evidence = {lesson.pattern_key: lesson for lesson in eligible}
    hypotheses: list[ResearchHypothesis] = []

    for size in range(1, min(max_conditions, len(names)) + 1):
        for combo in combinations(names, size):
            source = tuple(combo)
            rationale = tuple(
                f"{name}: n={evidence[name].occurrences}, "
                f"expectancy={evidence[name].expectancy_r:.4f}R"
                for name in combo
            )
            question = (
                f"Does {market} {timeframe} in regime {regime} show a repeatable "
                f"edge when {' + '.join(combo)} occur together?"
            )
            hypotheses.append(
                ResearchHypothesis(
                    hypothesis_id=_hypothesis_id(
                        market, timeframe, regime, combo
                    ),
                    market=market,
                    timeframe=timeframe,
                    regime=regime,
                    conditions=source,
                    question=question,
                    rationale=rationale,
                    source_patterns=source,
                )
            )

    return hypotheses


def hypothesis_to_dict(
    hypothesis: ResearchHypothesis,
) -> dict[str, object]:
    return asdict(hypothesis)
