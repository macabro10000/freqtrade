import pytest

from alfa_omega.execution.alpaca_paper import (
    AlpacaPaperAdapter,
    AlpacaPaperConfigurationError,
)


def test_order_submission_is_blocked_without_broker_call(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALPACA_PAPER", "true")

    adapter = object.__new__(AlpacaPaperAdapter)
    adapter._api_key = "test-key"
    adapter._secret_key = "test-secret"

    with pytest.raises(RuntimeError, match="ORDER EXECUTION IS DISABLED"):
        adapter.submit_order(symbol="BTC/USD")


def test_live_configuration_is_rejected(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALPACA_PAPER", "false")

    with pytest.raises(AlpacaPaperConfigurationError):
        AlpacaPaperAdapter()
