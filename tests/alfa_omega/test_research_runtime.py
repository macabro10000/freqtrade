from __future__ import annotations

from pathlib import Path

from alfa_omega.control.control_service import ControlService
from alfa_omega.control.control_state import ControlState
from alfa_omega.memory.memory_store import MemoryStore
from alfa_omega.research.runtime import ResearchRuntime


def test_runtime_plans_research_without_enabling_execution(tmp_path: Path) -> None:
    service = ControlService(ControlState(execution_enabled=False))
    runtime = ResearchRuntime(
        service,
        memory_store=MemoryStore(tmp_path / "memory.jsonl"),
        interval_seconds=1,
    )

    status = runtime.run_cycle()

    assert status.status == "RESEARCHING"
    assert status.research_enabled is True
    assert status.execution_enabled is False
    assert status.tasks_planned > 0
    assert service.get_state().execution_enabled is False


def test_runtime_respects_research_switch(tmp_path: Path) -> None:
    service = ControlService(ControlState(research_enabled=False))
    runtime = ResearchRuntime(
        service,
        memory_store=MemoryStore(tmp_path / "memory.jsonl"),
        interval_seconds=1,
    )

    status = runtime.run_cycle()

    assert status.status == "PAUSED"
    assert status.tasks_planned == 0
    assert status.research_enabled is False


def test_runtime_records_planning_error(tmp_path: Path) -> None:
    service = ControlService()
    runtime = ResearchRuntime(
        service,
        memory_store=MemoryStore(tmp_path / "memory.jsonl"),
        planner=lambda: (_ for _ in ()).throw(RuntimeError("planner failed")),
        interval_seconds=1,
    )

    status = runtime.run_cycle()

    assert status.status == "ERROR"
    assert "planner failed" in (status.last_error or "")
    assert status.execution_enabled is False


def test_runtime_publishes_cycles_through_public_callback(tmp_path: Path) -> None:
    service = ControlService(ControlState(execution_enabled=False))
    runtime = ResearchRuntime(
        service,
        memory_store=MemoryStore(tmp_path / "memory.jsonl"),
        interval_seconds=60,
    )
    published = []

    def on_cycle(status: object) -> None:
        published.append(status)
        runtime.stop()

    runtime.run(on_cycle=on_cycle)

    assert len(published) == 1
    assert published[0].status == "RESEARCHING"
    assert runtime.status().status == "STOPPED"
