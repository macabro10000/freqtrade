"""Build an auditable market-data catalog from a Hugging Face inventory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from alfa_omega.data.huggingface_catalog import HuggingFaceFile, HuggingFaceInventory
from alfa_omega.data.market_file_classifier import classify_inventory


@dataclass(frozen=True)
class MarketDataCatalog:
    repository: str
    inventory_version: str
    files: tuple[dict[str, object], ...]
    market_data_candidates: int
    unresolved_files: int

    @property
    def markets(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    str(item["market"])
                    for item in self.files
                    if item["classification"] == "MARKET_DATA_CANDIDATE"
                    and item["market"] is not None
                }
            )
        )

    @property
    def timeframes(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    str(item["timeframe"])
                    for item in self.files
                    if item["classification"] == "MARKET_DATA_CANDIDATE"
                    and item["timeframe"] is not None
                }
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "inventory_version": self.inventory_version,
            "files": list(self.files),
            "market_data_candidates": self.market_data_candidates,
            "unresolved_files": self.unresolved_files,
            "markets": list(self.markets),
            "timeframes": list(self.timeframes),
        }


def build_market_data_catalog(
    inventory: HuggingFaceInventory,
) -> MarketDataCatalog:
    """Create a classification-only catalog; no data files are downloaded."""
    classified = classify_inventory(inventory.files)
    candidates = sum(
        item["classification"] == "MARKET_DATA_CANDIDATE"
        for item in classified
    )
    unresolved = len(classified) - candidates
    return MarketDataCatalog(
        repository=inventory.repository,
        inventory_version=inventory.inventory_version,
        files=tuple(classified),
        market_data_candidates=candidates,
        unresolved_files=unresolved,
    )
