"""24/7 research runtime for ALFA OMEGA.

The runtime is intentionally separate from FastAPI and broker execution.
It plans research work, records heartbeats, and can be stopped gracefully.
It never submits orders and never enables execution.
"""

from __future__ import annotations

import signal
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Callable

from alfa_omega.control.control_service import ControlService
from alfa_omega.memory.memory_store import MemoryStore
from alfa_omega.research.research_orchestrator import (
    ResearchTask,
    plan_research_tasks,
)


@dataclass(frozen=True)
class ResearchRuntimeStatus:
    worker_id: str
    status: str
    started_at: str
    heartbeat_at: str
    cycle: int
    tasks_planned: int
    research_enabled: bool
    execution_enabled: bool
    last_error: str | None = None


class ResearchRuntime:
    """Long-running, execution-independent research process."""

    def __init__(
        self,
        control_service: ControlService,
        *,
        memory_store: MemoryStore | None = None,
        worker_id: str = "research-worker-1",
        interval_seconds: float = 30.0,
        planner: Callable[[], list[ResearchTask]] | None = None,
        clock: Callable[[], str] | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.control_service = control_service
        self.memory_store = memory_store or MemoryStore(
            "alfa_omega/logs/research_runtime.jsonl"
        )
        self.worker_id = worker_id
        self.interval_seconds = interval_seconds
        self._planner = planner or self._default_planner
        self._clock = clock or (lambda: datetime.now(UTC).isoformat())
        self._stop_event = threading.Event()
        self._status_lock = threading.Lock()
        now = self._clock()
        self._status = ResearchRuntimeStatus(
            worker_id=worker_id,
            status="STARTING",
            started_at=now,
            heartbeat_at=now,
            cycle=0,
            tasks_planned=0,
            research_enabled=control_service.get_state().research_enabled,
            execution_enabled=control_service.get_state().execution_enabled,
        )

    def _default_planner(self) -> list[ResearchTask]:
        state = self.control_service.get_state()
        return plan_research_tasks(
            markets=(state.selected_market,),
            timeframes=(state.execution_timeframe,),
        )

    def status(self) -> ResearchRuntimeStatus:
        with self._status_lock:
            return self._status

    def _set_status(self, **changes: object) -> None:
        with self._status_lock:
            data = asdict(self._status)
            data.update(changes)
            self._status = ResearchRuntimeStatus(**data)

    def heartbeat(self) -> ResearchRuntimeStatus:
        state = self.control_service.get_state()
        now = self._clock()
        status = self.status()
        self._set_status(
            status="RESEARCHING" if state.research_enabled else "PAUSED",
            heartbeat_at=now,
            cycle=status.cycle + 1,
            research_enabled=state.research_enabled,
            execution_enabled=state.execution_enabled,
            last_error=None,
        )
        current = self.status()
        self.memory_store.remember(
            "RESEARCH_RUNTIME_HEARTBEAT",
            asdict(current),
            source="research_runtime",
        )
        return current

    def run_cycle(self) -> ResearchRuntimeStatus:
        state = self.control_service.get_state()
        if not state.research_enabled:
            return self.heartbeat()

        try:
            tasks = self._planner()
            status = self.status()
            now = self._clock()
            self._set_status(
                status="RESEARCHING",
                heartbeat_at=now,
                cycle=status.cycle + 1,
                tasks_planned=len(tasks),
                research_enabled=True,
                execution_enabled=state.execution_enabled,
                last_error=None,
            )
            current = self.status()
            self.memory_store.remember(
                "RESEARCH_RUNTIME_CYCLE",
                {
                    **asdict(current),
                    "task_ids": [task.task_id for task in tasks],
                },
                source="research_runtime",
            )
            return current
        except Exception as exc:
            status = self.status()
            self._set_status(
                status="ERROR",
                heartbeat_at=self._clock(),
                cycle=status.cycle + 1,
                research_enabled=state.research_enabled,
                execution_enabled=state.execution_enabled,
                last_error=f"{type(exc).__name__}: {exc}",
            )
            current = self.status()
            self.memory_store.remember(
                "RESEARCH_RUNTIME_ERROR",
                asdict(current),
                source="research_runtime",
            )
            return current

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._install_signal_handlers()
        self._set_status(status="RUNNING")
        while not self._stop_event.is_set():
            self.run_cycle()
            self._stop_event.wait(self.interval_seconds)
        self._set_status(status="STOPPED", heartbeat_at=self._clock())

    def _install_signal_handlers(self) -> None:
        def handle_stop(signum: int, _frame: object) -> None:
            self.memory_store.remember(
                "RESEARCH_RUNTIME_SHUTDOWN",
                {
                    "worker_id": self.worker_id,
                    "signal": signum,
                    "timestamp": self._clock(),
                },
                source="research_runtime",
            )
            self.stop()

        try:
            signal.signal(signal.SIGTERM, handle_stop)
            signal.signal(signal.SIGINT, handle_stop)
        except ValueError:
            # Signal registration is only permitted from the main thread.
            pass
