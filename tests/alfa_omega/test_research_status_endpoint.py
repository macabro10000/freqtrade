from __future__ import annotations

from alfa_omega.control.control_service import ControlService
from alfa_omega.control.control_state import ControlState
from alfa_omega import render_service


class FakeResearchRuntimeStore:
    def load_status(self) -> dict[str, object]:
        return {
            "worker_id": "research-worker-test",
            "status": "RESEARCHING",
            "cycle": 7,
            "heartbeat_at": "2026-10-04T11:00:00+00:00",
        }


def test_research_status_exposes_control_and_durable_worker(monkeypatch) -> None:
    monkeypatch.setattr(
        render_service,
        "control_service",
        ControlService(ControlState(research_enabled=True, execution_enabled=False)),
    )
    monkeypatch.setattr(render_service, "research_runtime_store", FakeResearchRuntimeStore())

    payload = render_service.research_status()

    assert payload["status"] == "ok"
    assert payload["durable"] is True
    assert payload["research_enabled"] is True
    assert payload["execution_enabled"] is False
    assert payload["worker"]["worker_id"] == "research-worker-test"
    assert payload["worker"]["cycle"] == 7


def test_research_status_reports_unavailable_without_durable_store(monkeypatch) -> None:
    monkeypatch.setattr(
        render_service,
        "control_service",
        ControlService(ControlState(research_enabled=True, execution_enabled=False)),
    )
    monkeypatch.setattr(render_service, "research_runtime_store", None)

    payload = render_service.research_status()

    assert payload["status"] == "unavailable"
    assert payload["durable"] is False
    assert payload["worker"] is None
    assert payload["research_enabled"] is True
    assert payload["execution_enabled"] is False
