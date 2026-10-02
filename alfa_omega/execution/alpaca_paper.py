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
from alpaca.trading.enums import OrderSide, TimeInForce
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


    def run_smoke_cycle(
        self,
        *,
        notional_usd: float = 10.0,
        max_notional_usd: float = 25.0,
        client_prefix: str = "AO-SMOKE",
    ) -> dict[str, Any]:
        """Submit a tiny Paper BUY and close it with a SELL.

        This is a connectivity smoke test, not a trading strategy. It is
        separately gated and capped so it cannot become a normal execution
        path accidentally.
        """
        self._require_execution_enabled()
        smoke_raw = os.getenv("ALFA_OMEGA_PAPER_SMOKE_TEST_ENABLE", "false").strip().lower()
        if smoke_raw not in {"true", "1", "yes"}:
            raise AlpacaPaperExecutionDisabled(
                "Paper smoke test is disabled. Set "
                "ALFA_OMEGA_PAPER_SMOKE_TEST_ENABLE=true explicitly."
            )
        if notional_usd <= 0 or notional_usd > max_notional_usd:
            raise ValueError(f"notional_usd must be between 0 and {max_notional_usd}")

        import time
        from uuid import uuid4

        client_id = f"{client_prefix}-{uuid4().hex[:12]}"
        buy_request = MarketOrderRequest(
            symbol="BTC/USD",
            notional=notional_usd,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            client_order_id=client_id,
        )
        buy = self._trading.submit_order(buy_request)
        buy_id = str(buy.id)

        deadline = time.monotonic() + 30.0
        filled = None
        while time.monotonic() < deadline:
            current = self._trading.get_order_by_id(buy.id)
            status = str(current.status).lower()
            if status in {"filled", "partially_filled"}:
                filled = float(current.filled_qty or 0.0)
                if filled > 0:
                    break
            if status in {"canceled", "cancelled", "rejected", "expired"}:
                break
            time.sleep(1.0)

        if not filled:
            try:
                self._trading.cancel_order_by_id(buy.id)
            except Exception:
                pass
            raise RuntimeError(
                f"Paper smoke BUY did not fill. order_id={buy_id}"
            )

        # If the BUY only partially filled, cancel the remaining BUY quantity
        # before submitting the exit. The final position check below is the
        # source of truth if a residual race occurs.
        latest_buy = self._trading.get_order_by_id(buy.id)
        latest_buy_status = str(latest_buy.status).lower()
        buy_cancel_requested = False
        if latest_buy_status == "partially_filled":
            try:
                self._trading.cancel_order_by_id(buy.id)
                buy_cancel_requested = True
            except Exception:
                # A cancel race is reconciled by the position check.
                pass

        sell_id = f"{client_prefix}-EXIT-{uuid4().hex[:12]}"
        sell_request = MarketOrderRequest(
            symbol="BTC/USD",
            qty=filled,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            client_order_id=sell_id,
        )
        sell = self._trading.submit_order(sell_request)
        sell_deadline = time.monotonic() + 30.0
        sell_filled = False
        final_sell = sell
        while time.monotonic() < sell_deadline:
            final_sell = self._trading.get_order_by_id(sell.id)
            status = str(final_sell.status).lower()
            if status == "filled":
                sell_filled = True
                break
            if status in {"canceled", "cancelled", "rejected", "expired"}:
                break
            time.sleep(1.0)

        if not sell_filled:
            return {
                "status": "EXIT_NOT_CONFIRMED",
                "symbol": "BTC/USD",
                "notional_usd": notional_usd,
                "buy_order": self._order_to_dict(latest_buy),
                "sell_order": self._order_to_dict(final_sell),
                "filled_buy_qty": filled,
                "buy_cancel_requested": buy_cancel_requested,
                "purpose": "paper_connectivity_smoke_test_only",
                "requires_manual_reconciliation": True,
            }

        # A filled SELL is not sufficient evidence by itself: verify the
        # broker reports no residual BTC/USD position.
        remaining_qty = None
        position_deadline = time.monotonic() + 15.0
        while time.monotonic() < position_deadline:
            positions = self._trading.get_all_positions()
            remaining_qty = 0.0
            for position in positions:
                if position.symbol == "BTC/USD":
                    remaining_qty = float(position.qty)
                    break
            if abs(remaining_qty) < 1e-12:
                break
            time.sleep(1.0)

        if remaining_qty is None or abs(remaining_qty) >= 1e-12:
            return {
                "status": "EXIT_FILLED_POSITION_REMAINS",
                "symbol": "BTC/USD",
                "notional_usd": notional_usd,
                "buy_order": self._order_to_dict(latest_buy),
                "sell_order": self._order_to_dict(final_sell),
                "filled_buy_qty": filled,
                "filled_sell_qty": float(final_sell.filled_qty or 0.0),
                "remaining_qty": remaining_qty,
                "buy_cancel_requested": buy_cancel_requested,
                "purpose": "paper_connectivity_smoke_test_only",
                "requires_manual_reconciliation": True,
            }

        return {
            "status": "CYCLE_FILLED_AND_EXITED",
            "symbol": "BTC/USD",
            "notional_usd": notional_usd,
            "buy_order": self._order_to_dict(latest_buy),
            "filled_buy_qty": filled,
            "sell_order": self._order_to_dict(final_sell),
            "filled_sell_qty": float(final_sell.filled_qty or 0.0),
            "remaining_qty": 0.0,
            "buy_cancel_requested": buy_cancel_requested,
            "purpose": "paper_connectivity_smoke_test_only",
        }

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
