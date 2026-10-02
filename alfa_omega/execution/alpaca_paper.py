"""Controlled Alpaca Paper adapter for ALFA OMEGA.

Read-only operations are always available. Order submission requires two
independent explicit gates:
- ALPACA_PAPER=true
- ALFA_OMEGA_PAPER_EXECUTION_ENABLE=true

LIVE credentials are never accepted by this adapter.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest, StopLimitOrderRequest


class AlpacaPaperConfigurationError(RuntimeError):
    """Raised when the adapter is not configured for safe Paper use."""


class AlpacaPaperExecutionDisabled(RuntimeError):
    """Raised when an order is requested before explicit Paper enablement."""


class AlpacaPaperAdapter:
    provider = "alpaca"
    mode = "PAPER"
    live_enabled = False

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("ALPACA_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        paper_raw = os.getenv("ALPACA_PAPER", "true").strip().lower()
        execution_raw = os.getenv("ALFA_OMEGA_PAPER_EXECUTION_ENABLE", "false").strip().lower()

        if not self._api_key or not self._secret_key:
            raise AlpacaPaperConfigurationError(
                "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY."
            )
        if paper_raw not in {"true", "1", "yes"}:
            raise AlpacaPaperConfigurationError("ALPACA_PAPER=true is mandatory.")
        if execution_raw not in {"true", "1", "yes"}:
            self.order_execution_enabled = False
        else:
            self.order_execution_enabled = True

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

    def _require_execution_enabled(self) -> None:
        if not self.order_execution_enabled:
            raise AlpacaPaperExecutionDisabled(
                "Paper order execution is disabled. "
                "Set ALFA_OMEGA_PAPER_EXECUTION_ENABLE=true only after "
                "Signal, Risk and Safety validation."
            )

    def submit_market_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: float,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_execution_enabled()
        if symbol != "BTC/USD":
            raise ValueError("Controlled Paper phase currently permits BTC/USD only.")
        if qty <= 0:
            raise ValueError("qty must be positive")
        normalized_side = side.lower()
        if normalized_side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")

        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if normalized_side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            client_order_id=client_order_id,
        )
        order = self._trading.submit_order(request)
        return self._order_to_dict(order)

    def submit_stop_limit_exit(
        self,
        *,
        symbol: str,
        qty: float,
        stop_price: float,
        limit_price: float,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_execution_enabled()
        if symbol != "BTC/USD":
            raise ValueError("Controlled Paper phase currently permits BTC/USD only.")
        if qty <= 0 or stop_price <= 0 or limit_price <= 0:
            raise ValueError("qty and prices must be positive")
        if limit_price >= stop_price:
            raise ValueError("For a long-position stop-limit exit, limit_price must be below stop_price")

        request = StopLimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            stop_price=stop_price,
            limit_price=limit_price,
            client_order_id=client_order_id,
        )
        order = self._trading.submit_order(request)
        return self._order_to_dict(order)

    def submit_take_profit(
        self,
        *,
        symbol: str,
        qty: float,
        limit_price: float,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_execution_enabled()
        if symbol != "BTC/USD":
            raise ValueError("Controlled Paper phase currently permits BTC/USD only.")
        if qty <= 0 or limit_price <= 0:
            raise ValueError("qty and limit_price must be positive")

        request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            limit_price=limit_price,
            client_order_id=client_order_id,
        )
        order = self._trading.submit_order(request)
        return self._order_to_dict(order)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        self._require_execution_enabled()
        self._trading.cancel_order_by_id(order_id)
        return {"order_id": order_id, "status": "cancel_requested"}

    @staticmethod
    def _order_to_dict(order: Any) -> dict[str, Any]:
        return {
            "id": str(order.id),
            "client_order_id": str(order.client_order_id),
            "symbol": str(order.symbol),
            "side": str(order.side),
            "type": str(order.type),
            "status": str(order.status),
            "qty": float(order.qty) if order.qty is not None else None,
            "filled_qty": float(order.filled_qty) if order.filled_qty is not None else None,
            "filled_avg_price": (
                float(order.filled_avg_price)
                if order.filled_avg_price is not None
                else None
            ),
        }
