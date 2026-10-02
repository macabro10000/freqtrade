"""Alpaca Paper adapter for ALFA OMEGA.

This adapter intentionally exposes read-only operations first.
Order submission is not implemented in this phase.

Security:
- credentials are read only from environment variables;
- credentials are never persisted by this module;
- paper mode is explicit and mandatory;
- live mode is rejected;
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest
from alpaca.trading.client import TradingClient


class AlpacaPaperConfigurationError(RuntimeError):
    """Raised when the adapter is not configured for safe Paper use."""


class AlpacaPaperAdapter:
    """Read-only Alpaca Paper adapter used by ALFA OMEGA."""

    provider = "alpaca"
    mode = "PAPER"
    live_enabled = False
    order_execution_enabled = False

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("ALPACA_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        paper_raw = os.getenv("ALPACA_PAPER", "true").strip().lower()

        if not self._api_key or not self._secret_key:
            raise AlpacaPaperConfigurationError(
                "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY."
            )

        if paper_raw not in {"true", "1", "yes"}:
            raise AlpacaPaperConfigurationError(
                "Alpaca adapter requires ALPACA_PAPER=true. "
                "Live mode is blocked."
            )

        self._trading = TradingClient(
            api_key=self._api_key,
            secret_key=self._secret_key,
            paper=True,
        )
        self._crypto = CryptoHistoricalDataClient()

    def health_check(self) -> dict[str, Any]:
        account = self.get_account()
        return {
            "provider": self.provider,
            "mode": self.mode,
            "live_enabled": self.live_enabled,
            "order_execution_enabled": self.order_execution_enabled,
            "account_status": account["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_account(self) -> dict[str, Any]:
        account = self._trading.get_account()
        return {
            "id": str(account.id),
            "status": str(account.status),
            "currency": str(account.currency),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
        }

    def get_positions(self) -> list[dict[str, Any]]:
        positions = self._trading.get_all_positions()
        return [
            {
                "symbol": position.symbol,
                "qty": float(position.qty),
                "market_value": float(position.market_value),
                "avg_entry_price": float(position.avg_entry_price),
                "unrealized_pl": float(position.unrealized_pl),
            }
            for position in positions
        ]

    def get_latest_crypto_trade(self, symbol: str = "BTC/USD") -> dict[str, Any]:
        request = CryptoLatestTradeRequest(symbol_or_symbols=symbol)
        latest = self._crypto.get_crypto_latest_trade(request)
        trade = latest[symbol]
        return {
            "symbol": symbol,
            "price": float(trade.price),
            "size": float(trade.size),
            "timestamp": str(trade.timestamp),
        }

    def submit_order(self, *_args: Any, **_kwargs: Any) -> None:
        """Explicitly blocked until the execution phase is approved."""
        raise RuntimeError(
            "ORDER EXECUTION IS DISABLED. "
            "Use the Risk Engine and Safety Gate before enabling Paper orders."
        )

    def cancel_order(self, *_args: Any, **_kwargs: Any) -> None:
        """Explicitly blocked until the execution phase is approved."""
        raise RuntimeError(
            "ORDER CANCELLATION IS NOT ENABLED IN THE READ-ONLY PHASE."
        )
