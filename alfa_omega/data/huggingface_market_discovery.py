"""Runtime-safe Hugging Face market-data catalog discovery."""

from __future__ import annotations

from typing import Any

from alfa_omega.data.huggingface_catalog import inventory_dataset
from alfa_omega.data.huggingface_client import create_huggingface_api
from alfa_omega.data.market_data_catalog import MarketDataCatalog, build_market_data_catalog


DEFAULT_REPOSITORY = "Macabro10000/trading-data"


def discover_market_data_catalog(
    *,
    repository: str = DEFAULT_REPOSITORY,
    api: Any | None = None,
) -> MarketDataCatalog:
    """Discover candidate market files without downloading their contents."""
    client = api if api is not None else create_huggingface_api()
    inventory = inventory_dataset(client, repository=repository)
    return build_market_data_catalog(inventory)
