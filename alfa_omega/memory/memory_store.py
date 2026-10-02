"""Append-only local memory store for ALFA OMEGA research.

This is a local cache. Durable production knowledge belongs in the database
layer and must retain provenance and versioning.
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
    kind: str
    payload: dict[str, Any]
    created_at: str
    source: str
    schema_version: int = 1


class MemoryStore:
    """Append-only JSONL memory with deterministic IDs and deduplication."""

    def __init__(
        self,
        path: str | Path = "alfa_omega/logs/memory.jsonl",
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _canonical(payload: dict[str, Any]) -> str:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def _record_id(
        cls,
        kind: str,
        payload: dict[str, Any],
        source: str,
    ) -> str:
        raw = "|".join((kind, source, cls._canonical(payload)))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return "MEM-" + digest

    def _read(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        records: list[MemoryRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(MemoryRecord(**json.loads(line)))
        return records

    def remember(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        source: str = "unknown",
    ) -> MemoryRecord:
        if not kind:
            raise ValueError("kind is required")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")

        record = MemoryRecord(
            record_id=self._record_id(kind, payload, source),
            kind=kind,
            payload=dict(payload),
            created_at=datetime.now(timezone.utc).isoformat(),
            source=source,
        )

        for existing in self._read():
            if existing.record_id == record.record_id:
                return existing

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    asdict(record),
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
        return record

    def all(self) -> list[MemoryRecord]:
        return self._read()

    def count(self, kind: str | None = None) -> int:
        records = self._read()
        if kind is None:
            return len(records)
        return sum(record.kind == kind for record in records)

    def search(
        self,
        *,
        kind: str | None = None,
        query: str | None = None,
    ) -> list[MemoryRecord]:
        records = self._read()
        needle = query.casefold() if query else None
        result: list[MemoryRecord] = []
        for record in records:
            if kind is not None and record.kind != kind:
                continue
            if needle is not None:
                payload = self._canonical(record.payload).casefold()
                if needle not in payload:
                    continue
            result.append(record)
        return result

    def snapshot(
        self,
        *,
        kinds: Iterable[str] | None = None,
    ) -> tuple[MemoryRecord, ...]:
        allowed = set(kinds) if kinds is not None else None
        records = self._read()
        if allowed is not None:
            records = [record for record in records if record.kind in allowed]
        return tuple(records)
