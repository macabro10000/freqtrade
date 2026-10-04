"""Render entrypoint for the ALFA OMEGA research worker."""
from __future__ import annotations

import os
import uuid
from dataclasses import asdict

from alfa_omega.control.control_service import ControlService
from alfa_omega.control.control_store import MongoControlStateStore
from alfa_omega.research.runtime import ResearchRuntime, ResearchRuntimeStatus
from alfa_omega.research.runtime_store import MongoResearchRuntimeStore


def main() -> None:
    control_store = MongoControlStateStore.from_environment()
    control_service = ControlService(store=control_store)
    runtime_store = MongoResearchRuntimeStore.from_environment()
    worker_id = os.getenv("ALFA_OMEGA_RESEARCH_WORKER_ID") or (
        f"research-{uuid.uuid4().hex[:12]}"
    )
    interval = float(os.getenv("ALFA_OMEGA_RESEARCH_INTERVAL_SECONDS", "30"))
    lease_ttl = int(os.getenv("ALFA_OMEGA_RESEARCH_LEASE_TTL_SECONDS", "120"))

    if runtime_store is not None and not runtime_store.acquire_lease(
        worker_id, lease_ttl
    ):
        raise SystemExit("Another healthy ALFA OMEGA research worker owns the lease")

    runtime = ResearchRuntime(
        control_service,
        worker_id=worker_id,
        interval_seconds=interval,
    )

    def persist_cycle(status: ResearchRuntimeStatus) -> None:
        if runtime_store is None:
            return
        runtime_store.save_status(asdict(status))
        if not runtime_store.renew_lease(worker_id, lease_ttl):
            runtime.stop()
            raise SystemExit("Research worker lease was lost")

    try:
        runtime.run(on_cycle=persist_cycle)
    finally:
        if runtime_store is not None:
            runtime_store.release_lease(worker_id)


if __name__ == "__main__":
    main()
