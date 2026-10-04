"""Validated runtime state for the ALFA OMEGA control plane.

The control plane governs authorization state; it never submits broker orders.
State is intentionally process-local in this first increment. Durable/shared
state will be introduced through the database layer before multi-instance use.
"""
from __future__ import annotations

from typing import Any

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

ALLOWED_MARKETS = ("BTC/USD", "XAU/USD")
ALLOWED_TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h", "1d")
PAPER_MODE = "PAPER"


@dataclass(frozen=True)
class ControlState:
    research_enabled: bool = True
    execution_enabled: bool = False
    selected_market: str = "BTC/USD"
    execution_timeframe: str = "5m"
    mode: str = PAPER_MODE
    kill_switch: bool = True
    updated_at: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if self.selected_market not in ALLOWED_MARKETS:
            raise ValueError(f"Unsupported market: {self.selected_market}")
        if self.execution_timeframe not in ALLOWED_TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {self.execution_timeframe}")
        if self.mode != PAPER_MODE:
            raise ValueError("Control plane only permits PAPER mode")
        if self.version < 1:
            raise ValueError("Invalid control state version")

    def with_updates(self, **changes: Any) -> ControlState:
        data = asdict(self)
        data.update(changes)
        data["version"] = self.version + 1
        data["updated_at"] = datetime.now(UTC).isoformat()
        return ControlState(**data)

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["live_execution_enabled"] = False
        return data
