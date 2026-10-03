"""Durable control-state storage for ALFA OMEGA.

The web process may restart or be replaced, so execution authorization must not
depend only on process memory. MongoDB is used when configured; tests and local
runs can inject an in-memory store.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Protocol

from .control_state import ControlState


class ControlStateConflict(RuntimeError):
    """Raised when a stale control-state version attempts an update."""


class ControlStateStore(Protocol):
    """Persistence contract for the single ALFA OMEGA control state."""

    def load(self) -> ControlState | None:
        ...

    def save(
        self,
        state: ControlState,
        *,
        expected_version: int | None,
    ) -> ControlState:
        ...


class InMemoryControlStateStore:
    """Deterministic store for tests and single-process development."""

    def __init__(self, state: ControlState | None = None) -> None:
        self._state = state

    def load(self) -> ControlState | None:
        return self._state

    def save(
        self,
        state: ControlState,
        *,
        expected_version: int | None,
    ) -> ControlState:
        if self._state is not None and expected_version != self._state.version:
            raise ControlStateConflict("Stale control state version")
        if self._state is None and expected_version is not None:
            raise ControlStateConflict("Control state does not exist")
        self._state = state
        return state


class MongoControlStateStore:
    """MongoDB-backed, version-checked control-state store."""

    CONTROL_ID = "ALFA_OMEGA"

    def __init__(
        self,
        uri: str,
        *,
        database: str = "trading_system",
        collection: str = "control_state",
        mongo_client: Any | None = None,
    ) -> None:
        if not uri:
            raise ValueError("MongoDB URI is required")
        if mongo_client is None:
            from pymongo import MongoClient

            mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
        self._client = mongo_client
        self._collection = mongo_client[database][collection]
        self._collection.create_index("control_id", unique=True)

    @classmethod
    def from_environment(cls) -> MongoControlStateStore | None:
        uri = os.getenv("ALFA_OMEGA_CONTROL_MONGODB_URI") or os.getenv("MONGODB_URI")
        if not uri:
            return None
        return cls(
            uri,
            database=os.getenv("ALFA_OMEGA_CONTROL_DB", "trading_system"),
            collection=os.getenv("ALFA_OMEGA_CONTROL_COLLECTION", "control_state"),
        )

    @staticmethod
    def _document(state: ControlState) -> dict[str, Any]:
        return {
            "control_id": MongoControlStateStore.CONTROL_ID,
            **state.public_dict(),
        }

    @staticmethod
    def _state_from_document(document: Mapping[str, Any]) -> ControlState:
        fields = {
            "research_enabled",
            "execution_enabled",
            "selected_market",
            "execution_timeframe",
            "mode",
            "kill_switch",
            "updated_at",
            "version",
        }
        payload = {key: document[key] for key in fields if key in document}
        return ControlState(**payload)

    def load(self) -> ControlState | None:
        document = self._collection.find_one({"control_id": self.CONTROL_ID})
        if document is None:
            return None
        return self._state_from_document(document)

    def save(
        self,
        state: ControlState,
        *,
        expected_version: int | None,
    ) -> ControlState:
        document = self._document(state)
        if expected_version is None:
            result = self._collection.update_one(
                {"control_id": self.CONTROL_ID},
                {"$set": document},
                upsert=True,
            )
        else:
            result = self._collection.update_one(
                {
                    "control_id": self.CONTROL_ID,
                    "version": expected_version,
                },
                {"$set": document},
                upsert=False,
            )
        if expected_version is not None and result.matched_count != 1:
            raise ControlStateConflict("Stale control state version")
        return state
