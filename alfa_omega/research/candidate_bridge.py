"""Research candidate bridge for the ALFA OMEGA research orchestrator.

Turns structured research findings into deterministic experiment candidates.
It does not execute trades and does not bypass validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib

from alfa_omega.memory.memory_store import MemoryStore
from alfa_omega.research.hypothesis_factory import ResearchHypothesis
from alfa_omega.research.research_orchestrator import ResearchTask
from alfa_omega.research.web_research import ResearchFinding


@dataclass(frozen=True)
class ResearchCandidate:
    candidate_id: str
    task_id: str
    hypothesis_id: str
    market: str
    timeframe: str
    session: str
    regime: str
    topic: str
    source_finding_ids: tuple[str, ...]
    state: str = "RESEARCH_CANDIDATE"


def _candidate_id(task: ResearchTask, finding_ids: tuple[str, ...]) -> str:
    raw = "|".join((task.task_id, *finding_ids))
    return "CAND-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_candidate(
    task: ResearchTask,
    hypothesis: ResearchHypothesis,
    findings: tuple[ResearchFinding, ...] = (),
) -> ResearchCandidate:
    finding_ids = tuple(finding.finding_id for finding in findings)
    return ResearchCandidate(
        candidate_id=_candidate_id(task, finding_ids),
        task_id=task.task_id,
        hypothesis_id=hypothesis.hypothesis_id,
        market=task.market,
        timeframe=task.timeframe,
        session=task.session,
        regime=task.regime,
        topic=task.topic,
        source_finding_ids=finding_ids,
    )


def remember_candidate(
    store: MemoryStore,
    candidate: ResearchCandidate,
) -> None:
    store.remember(
        "RESEARCH_CANDIDATE",
        asdict(candidate),
        source="research_candidate_bridge",
    )


def candidate_key(candidate: ResearchCandidate) -> tuple[str, str, str, str, str]:
    return (
        candidate.market,
        candidate.timeframe,
        candidate.session,
        candidate.regime,
        candidate.hypothesis_id,
    )
