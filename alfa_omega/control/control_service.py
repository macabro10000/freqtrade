"""ALFA OMEGA control-plane service.

This service owns panel control state and deliberately has no broker dependency.
It can enable/disable execution authorization, but cannot bypass Risk or Safety.
"""
from __future__ import annotations

from threading import RLock
from typing import Any

from .control_state import ControlState
from .control_store import ControlStateStore


class ControlService:
    def __init__(
        self,
        initial_state: ControlState | None = None,
        store: ControlStateStore | None = None,
    ) -> None:
        self._lock = RLock()
        self._store = store
        loaded = store.load() if store is not None else None
        self._state = loaded or initial_state or ControlState()
        if store is not None and loaded is None:
            store.save(self._state, expected_version=None)

    def get_state(self) -> ControlState:
        with self._lock:
            return self._state

    def snapshot(self) -> dict[str, Any]:
        return self.get_state().public_dict()

    def set_market(self, market: str) -> ControlState:
        with self._lock:
            return self._update(selected_market=market)

    def set_timeframe(self, timeframe: str) -> ControlState:
        with self._lock:
            return self._update(execution_timeframe=timeframe)

    def connect_execution(self) -> ControlState:
        with self._lock:
            return self._update(execution_enabled=True, kill_switch=True)

    def stop_execution(self) -> ControlState:
        with self._lock:
            return self._update(execution_enabled=False)

    def set_research(self, enabled: bool) -> ControlState:
        with self._lock:
            return self._update(research_enabled=bool(enabled))

    def activate_kill_switch(self) -> ControlState:
        with self._lock:
            return self._update(kill_switch=False, execution_enabled=False)

    def _update(self, **changes: Any) -> ControlState:
        current = self._state
        updated = current.with_updates(**changes)
        if self._store is not None:
            self._store.save(updated, expected_version=current.version)
        self._state = updated
        return updated
