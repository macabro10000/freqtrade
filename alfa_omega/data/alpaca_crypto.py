"""Read-only historical BTC/USD market data from Alpaca Crypto Data API.

No orders are sent from this module. Credentials are read only from environment
variables and are never persisted by this module.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx


class MarketDataConfigurationError(RuntimeError):
    pass


class AlpacaCryptoDataClient:
    BASE_URL = "https://data.alpaca.markets/v1beta3/crypto/us"

    def __init__(self, timeout: float = 20.0) -> None:
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise MarketDataConfigurationError(
                "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY"
            )
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Accept": "application/json",
        }

    def get_bars(
        self,
        symbol: str = "BTC/USD",
        timeframe: str = "5Min",
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> dict[str, Any]:
        if limit < 1 or limit > 10000:
            raise ValueError("limit must be between 1 and 10000")
        params: dict[str, Any] = {
            "symbols": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "sort": "asc",
        }
        if start is not None:
            params["start"] = self._iso(start)
        if end is not None:
            params["end"] = self._iso(end)

        response = httpx.get(
            f"{self.BASE_URL}/bars",
            headers=self._headers(),
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
