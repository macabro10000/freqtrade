"""ALFA OMEGA control-plane service.

This service owns panel control state and deliberately has no broker dependency.
It can enable/disable execution authorization, but cannot bypass Risk or Safety.
"""
from __future__ import annotations

from threading import RLock
from typing import Any

from .control_state import ControlState


class ControlService:
    def __init__(self, initial_state: ControlState | None = None) -> None:
        self._lock = RLock()
        self._state = initial_state or ControlState()

    def get_state(self) -> ControlState:
        with self._lock:
            return self._state

    def snapshot(self) -> dict[str, Any]:
        return self.get_state().public_dict()

    def set_market(self, market: str) -> ControlState:
        with self._lock:
            self._state = self._state.with_updates(selected_market=market)
            return self._state

    def set_timeframe(self, timeframe: str) -> ControlState:
        with self._lock:
            self._state = self._state.with_updates(execution_timeframe=timeframe)
            return self._state

    def connect_execution(self) -> ControlState:
        with self._lock:
            self._state = self._state.with_updates(
                execution_enabled=True,
                kill_switch=True,
            )
            return self._state

    def stop_execution(self) -> ControlState:
        with self._lock:
            self._state = self._state.with_updates(execution_enabled=False)
            return self._state

    def set_research(self, enabled: bool) -> ControlState:
        with self._lock:
            self._state = self._state.with_updates(research_enabled=bool(enabled))
            return self._state

    def activate_kill_switch(self) -> ControlState:
        with self._lock:
            self._state = self._state.with_updates(
                kill_switch=False,
                execution_enabled=False,
            )
            return self._state
