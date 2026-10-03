from types import SimpleNamespace

import pytest

from alfa_omega.data.huggingface_catalog import inventory_dataset


class FakeApi:
    def list_repo_tree(self, **kwargs):
        assert kwargs["repo_id"] == "Macabro10000/trading-data"
        assert kwargs["repo_type"] == "dataset"
        assert kwargs["recursive"] is True
        return [
            SimpleNamespace(path="xau/1m.csv", size=120),
            SimpleNamespace(path="btc/5m.parquet", size=80),
        ]


def test_inventory_is_read_only_and_deterministic():
    inventory = inventory_dataset(
        FakeApi(),
        repository="Macabro10000/trading-data",
    )
    assert inventory.file_count == 2
    assert inventory.total_bytes == 200
    assert [item.path for item in inventory.files] == [
        "btc/5m.parquet",
        "xau/1m.csv",
    ]
    assert inventory.to_dict()["repository"] == "Macabro10000/trading-data"


def test_inventory_rejects_empty_repository():
    with pytest.raises(ValueError, match="repository"):
        inventory_dataset(FakeApi(), repository=" ")


def test_inventory_rejects_non_dataset_repo_type():
    with pytest.raises(ValueError, match="repo_type"):
        inventory_dataset(
            FakeApi(),
            repository="Macabro10000/trading-data",
            repo_type="model",
        )
