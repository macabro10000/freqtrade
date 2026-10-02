import pytest

from alfa_omega.execution.alpaca_paper import (
    AlpacaPaperAdapter,
    AlpacaPaperConfigurationError,
    AlpacaPaperExecutionDisabled,
)


def test_order_submission_is_blocked_without_broker_call(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALPACA_PAPER", "true")
    monkeypatch.setenv("ALFA_OMEGA_PAPER_EXECUTION_ENABLE", "false")

    adapter = object.__new__(AlpacaPaperAdapter)
    adapter._api_key = "test-key"
    adapter._secret_key = "test-secret"
    adapter.order_execution_enabled = False

    with pytest.raises(AlpacaPaperExecutionDisabled, match="Paper order execution is disabled"):
        adapter.submit_market_order(symbol="BTC/USD", side="buy", qty=0.0001)


def test_live_configuration_is_rejected(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALPACA_PAPER", "false")

    with pytest.raises(AlpacaPaperConfigurationError):
        AlpacaPaperAdapter()
