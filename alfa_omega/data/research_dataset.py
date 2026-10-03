"""Build auditable research datasets from validated market files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import pandas as pd

from alfa_omega.data.huggingface_market_reader import read_market_data_file
from alfa_omega.data.market_file_classifier import MarketDataFileCandidate


@dataclass(frozen=True)
class ResearchDatasetArtifact:
    frame: pd.DataFrame
    market: str
    timeframe: str
    source_repository: str
    source_files: tuple[dict[str, object], ...]
    dataset_sha256: str
    status: str = "READY"

    @property
    def rows(self) -> int:
        return len(self.frame)

    @property
    def time_start(self) -> str | None:
        return self.frame.index.min().isoformat() if len(self.frame) else None

    @property
    def time_end(self) -> str | None:
        return self.frame.index.max().isoformat() if len(self.frame) else None

    def to_dict(self) -> dict[str, object]:
        return {
            "market": self.market,
            "timeframe": self.timeframe,
            "source_repository": self.source_repository,
            "source_files": list(self.source_files),
            "dataset_sha256": self.dataset_sha256,
            "rows": self.rows,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "status": self.status,
        }


def _dataset_sha256(frame: pd.DataFrame) -> str:
    canonical = frame.sort_index().to_csv(
        index=True,
        index_label="timestamp",
        date_format="%Y-%m-%dT%H:%M:%S.%f%z",
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_candidates(
    candidates: tuple[MarketDataFileCandidate, ...],
    *,
    market: str,
    timeframe: str,
) -> None:
    if not candidates:
        raise ValueError("at least one market-data candidate is required")
    for candidate in candidates:
        if candidate.market != market:
            raise ValueError("all candidates must belong to the requested market")
        if candidate.timeframe != timeframe:
            raise ValueError(
                "all candidates must belong to the requested timeframe"
            )
        if candidate.classification != "MARKET_DATA_CANDIDATE":
            raise ValueError("all candidates must be validated market-data candidates")


def build_research_dataset(
    api: Any,
    *,
    repository: str,
    market: str,
    timeframe: str,
    candidates: tuple[MarketDataFileCandidate, ...],
) -> ResearchDatasetArtifact:
    """Load selected files and produce one deterministic research artifact."""
    if not repository.strip():
        raise ValueError("repository must not be empty")
    _validate_candidates(candidates, market=market, timeframe=timeframe)

    frames: list[pd.DataFrame] = []
    source_files: list[dict[str, object]] = []

    for candidate in candidates:
        frame, provenance = read_market_data_file(
            api,
            repository=repository,
            candidate=candidate,
        )
        frames.append(frame)
        source_files.append(dict(provenance))

    combined = pd.concat(frames, axis=0).sort_index()
    duplicate_count = int(combined.index.duplicated(keep=False).sum())
    if duplicate_count:
        raise ValueError(
            f"research dataset contains {duplicate_count} duplicate timestamps"
        )
    if not isinstance(combined.index, pd.DatetimeIndex):
        raise ValueError("research dataset requires a DatetimeIndex")
    if combined.index.tz is None or str(combined.index.tz) != "UTC":
        raise ValueError("research dataset timestamps must be UTC")
    if not combined.index.is_monotonic_increasing:
        raise ValueError("research dataset must be chronologically ordered")

    status = "READY"
    if any(
        item.get("quality", {}).get("status") == "READY_WITH_WARNINGS"
        for item in source_files
    ):
        status = "READY_WITH_WARNINGS"

    return ResearchDatasetArtifact(
        frame=combined,
        market=market,
        timeframe=timeframe,
        source_repository=repository,
        source_files=tuple(source_files),
        dataset_sha256=_dataset_sha256(combined),
        status=status,
    )
