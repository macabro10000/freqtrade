from types import SimpleNamespace

from alfa_omega.data.huggingface_market_discovery import (
    DEFAULT_REPOSITORY,
    discover_market_data_catalog,
)


class FakeApi:
    def list_repo_tree(self, **kwargs):
        assert kwargs["repo_id"] == DEFAULT_REPOSITORY
        assert kwargs["repo_type"] == "dataset"
        assert kwargs["recursive"] is True
        return [
            SimpleNamespace(path="xau/1m.csv", size=10),
            SimpleNamespace(path="btc/5m.parquet", size=20),
            SimpleNamespace(path="notes/readme.md", size=5),
        ]


def test_discover_market_data_catalog():
    catalog = discover_market_data_catalog(api=FakeApi())

    assert catalog.repository == DEFAULT_REPOSITORY
    assert catalog.market_data_candidates == 2
    assert catalog.unresolved_files == 1
    assert catalog.markets == ("BTC/USD", "XAU/USD")
