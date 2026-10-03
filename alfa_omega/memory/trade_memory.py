"""Structured persistence for ALFA OMEGA trade lifecycle memory.

Trade outcomes are retained as auditable observations. They are not silently
promoted to model-training data.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from alfa_omega.intelligence.trade_lifecycle import TradeOutcome
from alfa_omega.memory.memory_store import MemoryRecord, MemoryStore


class TradeMemory:
    """Persist decision, execution, and outcome observations in append-only memory."""

    OUTCOME_KIND = "TRADE_OUTCOME"
    DECISION_KIND = "TRADE_DECISION"
    EXECUTION_KIND = "TRADE_EXECUTION"

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def remember_outcome(
        self,
        outcome: TradeOutcome,
        *,
        source: str = "trade_lifecycle",
        model_version: str = "UNKNOWN",
        feature_version: str = "UNKNOWN",
        decision_id: str = "",
    ) -> MemoryRecord:
        payload: dict[str, Any] = outcome.to_dict()
        payload.update(
            {
                "model_version": model_version,
                "feature_version": feature_version,
                "decision_id": decision_id,
                "training_eligible": False,
            }
        )
        return self.store.remember(self.OUTCOME_KIND, payload, source=source)

    def remember_decision(
        self,
        decision: Mapping[str, object],
        *,
        source: str = "trade_decision",
    ) -> MemoryRecord:
        return self._remember_mapping(self.DECISION_KIND, decision, source)

    def remember_execution(
        self,
        execution: Mapping[str, object],
        *,
        source: str = "execution",
    ) -> MemoryRecord:
        return self._remember_mapping(self.EXECUTION_KIND, execution, source)

    def _remember_mapping(
        self,
        kind: str,
        payload: Mapping[str, object],
        source: str,
    ) -> MemoryRecord:
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")
        normalized = dict(payload)
        normalized.setdefault("training_eligible", False)
        return self.store.remember(kind, normalized, source=source)
