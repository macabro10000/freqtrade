import pytest

from alfa_omega.control.control_service import ControlService
from alfa_omega.control.control_state import ControlState


def test_control_defaults_to_research_on_execution_off_paper_only():
    state = ControlState()
    assert state.research_enabled is True
    assert state.execution_enabled is False
    assert state.selected_market == "BTC/USD"
    assert state.execution_timeframe == "5m"
    assert state.mode == "PAPER"
    assert state.kill_switch is True
    assert state.public_dict()["live_execution_enabled"] is False


def test_connect_and_stop_only_change_execution_authorization():
    service = ControlService()
    connected = service.connect_execution()
    assert connected.research_enabled is True
    assert connected.execution_enabled is True
    assert connected.mode == "PAPER"

    stopped = service.stop_execution()
    assert stopped.research_enabled is True
    assert stopped.execution_enabled is False


def test_market_and_timeframe_are_validated():
    service = ControlService()
    assert service.set_market("XAU/USD").selected_market == "XAU/USD"
    assert service.set_timeframe("15m").execution_timeframe == "15m"

    with pytest.raises(ValueError):
        service.set_market("EUR/USD")
    with pytest.raises(ValueError):
        service.set_timeframe("30m")
    with pytest.raises(ValueError):
        ControlState(mode="LIVE")


def test_kill_switch_stops_new_execution():
    service = ControlService()
    service.connect_execution()
    state = service.activate_kill_switch()
    assert state.kill_switch is False
    assert state.execution_enabled is False
