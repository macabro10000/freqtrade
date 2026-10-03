"""Durable runtime heartbeat and single-worker lease storage."""
from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any


class MongoResearchRuntimeStore:
    """MongoDB store for worker lease and latest runtime status."""

    def __init__(
        self,
        uri: str,
        *,
        database: str = "trading_system",
        collection: str = "research_runtime",
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
        self._collection = mongo_client[database][collection]

    @classmethod
    def from_environment(cls) -> MongoResearchRuntimeStore | None:
        uri = os.getenv("ALFA_OMEGA_CONTROL_MONGODB_URI") or os.getenv("MONGODB_URI")
        if not uri:
            return None
        return cls(
            uri,
            database=os.getenv("ALFA_OMEGA_RESEARCH_DB", "trading_system"),
            collection=os.getenv(
                "ALFA_OMEGA_RESEARCH_COLLECTION",
                "research_runtime",
            ),
        )

    def acquire_lease(self, worker_id: str, ttl_seconds: int = 120) -> bool:
        now = datetime.now(UTC)
        expires = now + timedelta(seconds=ttl_seconds)
        result = self._collection.update_one(
            {
                "_id": "RESEARCH_LEASE",
                "$or": [
                    {"expires_at": {"$lte": now}},
                    {"worker_id": worker_id},
                ],
            },
            {
                "$set": {
                    "worker_id": worker_id,
                    "acquired_at": now,
                    "expires_at": expires,
                }
            },
            upsert=True,
        )
        return result.matched_count == 1 or result.upserted_id == "RESEARCH_LEASE"

    def renew_lease(self, worker_id: str, ttl_seconds: int = 120) -> bool:
        now = datetime.now(UTC)
        result = self._collection.update_one(
            {"_id": "RESEARCH_LEASE", "worker_id": worker_id},
            {"$set": {"expires_at": now + timedelta(seconds=ttl_seconds)}},
        )
        return result.matched_count == 1

    def release_lease(self, worker_id: str) -> None:
        self._collection.update_one(
            {"_id": "RESEARCH_LEASE", "worker_id": worker_id},
            {"$set": {"expires_at": datetime.now(UTC)}},
        )

    def save_status(self, status: Mapping[str, Any]) -> None:
        self._collection.update_one(
            {"_id": "RESEARCH_STATUS"},
            {"$set": {"updated_at": datetime.now(UTC), **dict(status)}},
            upsert=True,
        )

    def load_status(self) -> dict[str, Any] | None:
        document = self._collection.find_one({"_id": "RESEARCH_STATUS"})
        if document is None:
            return None
        document.pop("_id", None)
        return document
