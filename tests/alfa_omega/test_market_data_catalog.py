from datetime import UTC, datetime

from alfa_omega.data.huggingface_catalog import (
    HuggingFaceFile,
    HuggingFaceInventory,
)
from alfa_omega.data.market_data_catalog import build_market_data_catalog


def _inventory():
    return HuggingFaceInventory(
        repository="Macabro10000/trading-data",
        repo_type="dataset",
        files=(
            HuggingFaceFile("xau/1m.csv", 10, "file"),
            HuggingFaceFile("btc/5m.parquet", 20, "file"),
            HuggingFaceFile("models/readme.md", 5, "file"),
        ),
        generated_at=datetime.now(UTC).isoformat(),
    )


def test_build_market_data_catalog():
    catalog = build_market_data_catalog(_inventory())

    assert catalog.market_data_candidates == 2
    assert catalog.unresolved_files == 1
    assert catalog.markets == ("BTC/USD", "XAU/USD")
    assert catalog.timeframes == ("1m", "5m")
    assert catalog.to_dict()["repository"] == "Macabro10000/trading-data"


def test_catalog_preserves_all_inventory_files():
    catalog = build_market_data_catalog(_inventory())
    assert [item["path"] for item in catalog.files] == [
        "btc/5m.parquet",
        "models/readme.md",
        "xau/1m.csv",
    ]
