"""Tests for durable ALFA OMEGA control-state persistence."""

from __future__ import annotations

from alfa_omega.control.control_service import ControlService
from alfa_omega.control.control_state import ControlState
from alfa_omega.control.control_store import (
    ControlStateConflict,
    InMemoryControlStateStore,
)


def test_control_state_store_survives_service_reconstruction() -> None:
    store = InMemoryControlStateStore()
    first = ControlService(store=store)

    updated = first.set_timeframe("15m")

    second = ControlService(store=store)

    assert second.get_state() == updated
    assert second.get_state().version == 2


def test_control_state_store_rejects_stale_writes() -> None:
    store = InMemoryControlStateStore(ControlState())
    first = ControlService(store=store)
    stale = ControlState()

    first.set_market("XAU/USD")

    try:
        store.save(stale, expected_version=stale.version)
    except ControlStateConflict:
        pass
    else:
        raise AssertionError("stale control state write was accepted")


def test_control_service_increments_version_on_every_change() -> None:
    store = InMemoryControlStateStore()
    service = ControlService(store=store)

    assert service.get_state().version == 1
    assert service.set_market("XAU/USD").version == 2
    assert service.set_timeframe("1h").version == 3
