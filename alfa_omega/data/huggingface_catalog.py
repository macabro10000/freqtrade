"""Read-only Hugging Face dataset inventory for ALFA OMEGA.

This module inventories a dataset repository without downloading market data.
Credentials are supplied by the runtime environment and are never persisted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class HuggingFaceFile:
    path: str
    size: int | None
    kind: str


@dataclass(frozen=True)
class HuggingFaceInventory:
    repository: str
    repo_type: str
    files: tuple[HuggingFaceFile, ...]
    generated_at: str
    inventory_version: str = "v1"

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(item.size or 0 for item in self.files)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["files"] = [asdict(item) for item in self.files]
        payload["file_count"] = self.file_count
        payload["total_bytes"] = self.total_bytes
        return payload


def _item_value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def inventory_dataset(
    api: Any,
    *,
    repository: str,
    repo_type: str = "dataset",
) -> HuggingFaceInventory:
    """Inventory repository files through an already-authenticated API client."""
    if not repository.strip():
        raise ValueError("repository must not be empty")
    if repo_type != "dataset":
        raise ValueError("repo_type must be 'dataset'")

    items = api.list_repo_tree(
        repo_id=repository,
        repo_type=repo_type,
        recursive=True,
        expand=True,
    )

    files: list[HuggingFaceFile] = []
    for item in items:
        path = str(_item_value(item, "path", "")).strip()
        if not path:
            continue
        size = _item_value(item, "size")
        if size is not None:
            size = int(size)
        kind = type(item).__name__
        files.append(HuggingFaceFile(path=path, size=size, kind=kind))

    files.sort(key=lambda entry: entry.path)

    return HuggingFaceInventory(
        repository=repository,
        repo_type=repo_type,
        files=tuple(files),
        generated_at=datetime.now(UTC).isoformat(),
    )
