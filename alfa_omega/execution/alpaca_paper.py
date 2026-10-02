"""Controlled Alpaca Paper adapter for ALFA OMEGA.

Read-only operations are always available. Order submission requires two
independent explicit gates:
- ALPACA_PAPER=true
- ALFA_OMEGA_PAPER_EXECUTION_ENABLE=true

LIVE credentials are never accepted by this adapter.
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timezone
from typing import Any

from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    StopLimitOrderRequest,
)


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
            "timestamp": datetime.now(UTC).isoformat(),
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
        notional_usd: float = 20.0,
        max_notional_usd: float = 25.0,
        client_prefix: str = "AO-SMOKE",
    ) -> dict[str, Any]:
        """Submit a marketable Paper BUY and close it with a SELL.

        This is a connectivity smoke test, not a trading strategy. It is
        separately gated and capped so it cannot become a normal execution
        path accidentally.

        The BUY deliberately uses an explicit BTC quantity and a marketable
        limit price instead of a notional market order. Alpaca documents that
        crypto supports fractional qty/limit orders and that Paper fills only
        marketable orders. This makes the test deterministic enough to
        validate the broker path while remaining strictly Paper-only.
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

        import math
        import time
        from decimal import Decimal, ROUND_DOWN
        from uuid import uuid4

        symbol = "BTC/USD"
        increment = Decimal("0.0001")

        # Reconciliation must preserve pre-existing holdings. The previous
        # implementation incorrectly required the total BTC position to become
        # zero, which is invalid when the account already owns BTC.
        baseline_qty = Decimal("0")
        baseline_position_found = False
        for position in self._trading.get_all_positions():
            if position.symbol == symbol:
                baseline_qty = Decimal(str(position.qty))
                baseline_position_found = True
                break

        latest = self.get_latest_crypto_trade(symbol)
        reference_price = float(latest["price"])
        if reference_price <= 0:
            raise RuntimeError("Invalid BTC/USD latest trade price.")

        # Alpaca documents BTC/USD min_order_size/min_trade_increment as 0.0001.
        # Use the largest quantity that stays below the $20/$25 smoke cap while
        # never dropping below the broker minimum.
        raw_qty = Decimal(str(notional_usd)) / Decimal(str(reference_price))
        qty = raw_qty.quantize(increment, rounding=ROUND_DOWN)
        if qty < increment:
            qty = increment
        effective_notional = float(qty) * reference_price
        if effective_notional > max_notional_usd:
            qty = (
                Decimal(str(max_notional_usd))
                / Decimal(str(reference_price))
            ).quantize(increment, rounding=ROUND_DOWN)
        if qty < increment:
            raise RuntimeError("Smoke notional is below the minimum BTC/USD order size.")

        # A buy limit above the latest trade is immediately marketable in Paper.
        # Price increment for BTC/USD is $1 according to the asset metadata.
        buy_limit_price = float(math.ceil(reference_price * 1.01))
        client_id = f"{client_prefix}-{uuid4().hex[:12]}"
        buy_request = LimitOrderRequest(
            symbol=symbol,
            qty=float(qty),
            limit_price=buy_limit_price,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            client_order_id=client_id,
        )
        buy = self._trading.submit_order(buy_request)
        buy_id = str(buy.id)

        deadline = time.monotonic() + 30.0
        filled = 0.0
        current_buy = buy
        while time.monotonic() < deadline:
            current_buy = self._trading.get_order_by_id(buy.id)
            status = str(current_buy.status).lower()
            filled = float(current_buy.filled_qty or 0.0)
            if filled > 0 and status in {"filled", "partially_filled"}:
                break
            if status in {"canceled", "cancelled", "rejected", "expired"}:
                break
            time.sleep(1.0)

        if filled <= 0:
            try:
                self._trading.cancel_order_by_id(buy.id)
            except Exception:
                pass
            raise RuntimeError(
                f"Paper smoke BUY did not fill. order_id={buy_id}; "
                f"reference_price={reference_price}; "
                f"limit_price={buy_limit_price}; requested_qty={float(qty)}"
            )

        # If the BUY only partially filled, cancel the remaining BUY quantity
        # before submitting the exit. The final position check remains the
        # source of truth if a residual race occurs.
        latest_buy = self._trading.get_order_by_id(buy.id)
        latest_buy_status = str(latest_buy.status).lower()
        buy_cancel_requested = False
        if latest_buy_status == "partially_filled":
            try:
                self._trading.cancel_order_by_id(buy.id)
                buy_cancel_requested = True
            except Exception:
                pass

        sell_id = f"{client_prefix}-EXIT-{uuid4().hex[:12]}"
        sell_request = MarketOrderRequest(
            symbol=symbol,
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
                "symbol": symbol,
                "notional_usd": notional_usd,
                "buy_order": self._order_to_dict(latest_buy),
                "sell_order": self._order_to_dict(final_sell),
                "filled_buy_qty": filled,
                "buy_cancel_requested": buy_cancel_requested,
                "purpose": "paper_connectivity_smoke_test_only",
                "requires_manual_reconciliation": True,
            }

        # Reconcile against the position that existed BEFORE this test.
        # Expected post-test position = baseline + filled BUY - filled SELL.
        # This preserves unrelated/pre-existing holdings and avoids float
        # equality problems by comparing Decimal quantities to the broker
        # increment.
        filled_sell_qty = Decimal(str(final_sell.filled_qty or 0.0))
        expected_post_qty = baseline_qty + Decimal(str(filled)) - filled_sell_qty

        observed_post_qty = None
        position_error = None
        position_deadline = time.monotonic() + 15.0
        while time.monotonic() < position_deadline:
            try:
                observed_post_qty = Decimal("0")
                for position in self._trading.get_all_positions():
                    if position.symbol == symbol:
                        observed_post_qty = Decimal(str(position.qty))
                        break
                position_error = None
                if abs(observed_post_qty - expected_post_qty) <= increment:
                    break
            except Exception as exc:
                position_error = str(exc)
            time.sleep(1.0)

        reconciled = (
            position_error is None
            and observed_post_qty is not None
            and abs(observed_post_qty - expected_post_qty) <= increment
        )

        if not reconciled:
            return {
                "status": (
                    "EXIT_RECONCILIATION_FAILED"
                    if position_error is None
                    else "EXIT_FILLED_RECONCILIATION_PENDING"
                ),
                "symbol": symbol,
                "notional_usd": notional_usd,
                "buy_order": self._order_to_dict(latest_buy),
                "sell_order": self._order_to_dict(final_sell),
                "filled_buy_qty": filled,
                "filled_sell_qty": float(filled_sell_qty),
                "baseline_position_qty": float(baseline_qty),
                "baseline_position_found": baseline_position_found,
                "expected_post_position_qty": float(expected_post_qty),
                "observed_post_position_qty": (
                    float(observed_post_qty) if observed_post_qty is not None else None
                ),
                "position_error": position_error,
                "buy_cancel_requested": buy_cancel_requested,
                "purpose": "paper_connectivity_smoke_test_only",
                "requires_manual_reconciliation": True,
            }

        return {
            "status": "CYCLE_FILLED_AND_RECONCILED",
            "symbol": symbol,
            "notional_usd": notional_usd,
            "effective_buy_notional": effective_notional,
            "reference_price": reference_price,
            "buy_limit_price": buy_limit_price,
            "requested_qty": float(qty),
            "buy_order": self._order_to_dict(latest_buy),
            "filled_buy_qty": filled,
            "sell_order": self._order_to_dict(final_sell),
            "filled_sell_qty": float(final_sell.filled_qty or 0.0),
            "baseline_position_qty": float(baseline_qty),
            "expected_post_position_qty": float(expected_post_qty),
            "observed_post_position_qty": float(observed_post_qty),
            "position_delta": float(observed_post_qty - baseline_qty),
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
