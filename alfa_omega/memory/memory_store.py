"""Persistent memory engine for ALFA OMEGA research.

Memory is append-only by default. Records are content-addressed, typed, and
recoverable after process/server restarts. The engine stores observations and
lessons; it never grants trading permissions or mutates execution policy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    record_type: str
    created_at: str
    payload: dict[str, Any]
    source: str
    version: int = 1


class MemoryStore:
    """Small durable JSONL memory with deterministic IDs and replay support."""

    def __init__(self, root: str | Path = "state/memory") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "memory.jsonl"

    @staticmethod
    def _record_id(record_type: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            {"record_type": record_type, "payload": payload},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return "MEM-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]

    def remember(
        self,
        record_type: str,
        payload: dict[str, Any],
        *,
        source: str = "ALFA_OMEGA",
    ) -> MemoryRecord:
        if not record_type.strip():
            raise ValueError("record_type is required")
        record = MemoryRecord(
            record_id=self._record_id(record_type, payload),
            record_type=record_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            source=source,
        )
        existing = {item.record_id for item in self.iter_records()}
        if record.record_id not in existing:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        return record

    def iter_records(self) -> Iterable[MemoryRecord]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                data = json.loads(line)
                yield MemoryRecord(**data)

    def search(
        self,
        *,
        record_type: str | None = None,
        market: str | None = None,
        timeframe: str | None = None,
        regime: str | None = None,
        pattern_id: str | None = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        if limit < 1:
            raise ValueError("limit must be positive")
        matches: list[MemoryRecord] = []
        for record in self.iter_records():
            if record_type and record.record_type != record_type:
                continue
            payload = record.payload
            if market and payload.get("market") != market:
                continue
            if timeframe and payload.get("timeframe") != timeframe:
                continue
            if regime and payload.get("regime") != regime:
                continue
            patterns = payload.get("pattern_ids", ())
            if pattern_id and pattern_id not in patterns:
                continue
            matches.append(record)
            if len(matches) >= limit:
                break
        return matches

    def count(self) -> int:
        return sum(1 for _ in self.iter_records())

    def snapshot(self) -> dict[str, int | str]:
        return {
            "records": self.count(),
            "path": str(self.path),
            "status": "PERSISTENT",
        }


def memory_record_to_dict(record: MemoryRecord) -> dict[str, Any]:
    return asdict(record)
