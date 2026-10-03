"""Continuous research orchestration for ALFA OMEGA.

The orchestrator creates deterministic research work. It does not trade,
modify live policy, or bypass validation gates.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import product

from alfa_omega.memory.memory_store import MemoryStore


@dataclass(frozen=True)
class ResearchTask:
    task_id: str
    market: str
    timeframe: str
    session: str
    regime: str
    topic: str
    status: str = "PLANNED"


@dataclass(frozen=True)
class ResearchRun:
    run_id: str
    started_at: str
    task_ids: tuple[str, ...]
    status: str
    notes: tuple[str, ...] = ()


def _task_id(
    market: str,
    timeframe: str,
    session: str,
    regime: str,
    topic: str,
) -> str:
    raw = f"{market}|{timeframe}|{session}|{regime}|{topic}"
    return "TASK-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def plan_research_tasks(
    *,
    markets: tuple[str, ...] = ("BTC/USD", "XAU/USD"),
    timeframes: tuple[str, ...] = ("5m", "15m", "1h"),
    sessions: tuple[str, ...] = (
        "OFF_SESSION",
        "LONDON",
        "NEW_YORK",
        "LONDON_NEW_YORK",
    ),
    regimes: tuple[str, ...] = (
        "TREND",
        "RANGE_LOW_VOL",
        "EXPANSION",
        "LIQUIDITY_EVENT",
        "NEUTRAL",
    ),
    topics: tuple[str, ...] = (
        "INDICATOR_DISCOVERY",
        "PATTERN_DISCOVERY",
        "SESSION_EFFECT",
        "FAILURE_ANALYSIS",
    ),
) -> list[ResearchTask]:
    """Build deterministic research tasks; it performs no trading."""
    tasks: list[ResearchTask] = []
    fields = ("market", "timeframe", "session", "regime", "topic")
    for values in product(markets, timeframes, sessions, regimes, topics):
        data = dict(zip(fields, values, strict=True))
        tasks.append(
            ResearchTask(
                task_id=_task_id(*values),
                **data,
            )
        )
    return tasks


def create_run(tasks: list[ResearchTask]) -> ResearchRun:
    task_ids = tuple(task.task_id for task in tasks)
    now = datetime.now(UTC).isoformat()
    raw = "|".join(task_ids) + now
    run_id = "RUN-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return ResearchRun(
        run_id=run_id,
        started_at=now,
        task_ids=task_ids,
        status="PLANNED",
    )


def remember_run(store: MemoryStore, run: ResearchRun) -> None:
    store.remember("RESEARCH_RUN", asdict(run), source="research_orchestrator")


def remember_tasks(store: MemoryStore, tasks: list[ResearchTask]) -> None:
    for task in tasks:
        store.remember("RESEARCH_TASK", asdict(task), source="research_orchestrator")
