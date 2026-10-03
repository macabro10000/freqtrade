from pathlib import Path

import pandas as pd
import pytest

from alfa_omega.data.market_file_classifier import MarketDataFileCandidate
from alfa_omega.data.research_dataset import build_research_dataset


class FakeApi:
    def __init__(self, root: Path):
        self.root = root

    def hf_hub_download(self, **kwargs):
        source = self.root / kwargs["filename"]
        destination = Path(kwargs["local_dir"]) / source.name
        destination.write_bytes(source.read_bytes())
        return destination


def _candidate(path: str, market: str = "BTC/USD", timeframe: str = "5m"):
    return MarketDataFileCandidate(
        path=path,
        size=None,
        market=market,
        timeframe=timeframe,
        format="csv",
        classification="MARKET_DATA_CANDIDATE",
    )


def _write_csv(root: Path, name: str, timestamps: list[str]) -> None:
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100.0 + i for i in range(len(timestamps))],
            "high": [101.0 + i for i in range(len(timestamps))],
            "low": [99.0 + i for i in range(len(timestamps))],
            "close": [100.5 + i for i in range(len(timestamps))],
            "volume": [10.0] * len(timestamps),
        }
    )
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def test_build_research_dataset_is_chronological_and_provenanced(tmp_path):
    _write_csv(tmp_path, "btc/a.csv", ["2026-01-01T00:05:00Z"])
    _write_csv(tmp_path, "btc/b.csv", ["2026-01-01T00:00:00Z"])

    artifact = build_research_dataset(
        FakeApi(tmp_path),
        repository="Macabro10000/trading-data",
        market="BTC/USD",
        timeframe="5m",
        candidates=(_candidate("btc/a.csv"), _candidate("btc/b.csv")),
    )

    assert artifact.rows == 2
    assert artifact.status == "READY"
    assert artifact.time_start == "2026-01-01T00:00:00+00:00"
    assert len(artifact.source_files) == 2
    assert artifact.dataset_sha256


def test_build_research_dataset_rejects_duplicate_timestamps(tmp_path):
    _write_csv(tmp_path, "btc/a.csv", ["2026-01-01T00:00:00Z"])
    _write_csv(tmp_path, "btc/b.csv", ["2026-01-01T00:00:00Z"])

    with pytest.raises(ValueError, match="duplicate timestamps"):
        build_research_dataset(
            FakeApi(tmp_path),
            repository="Macabro10000/trading-data",
            market="BTC/USD",
            timeframe="5m",
            candidates=(_candidate("btc/a.csv"), _candidate("btc/b.csv")),
        )


def test_build_research_dataset_rejects_mixed_timeframes(tmp_path):
    with pytest.raises(ValueError, match="timeframe"):
        build_research_dataset(
            FakeApi(tmp_path),
            repository="Macabro10000/trading-data",
            market="BTC/USD",
            timeframe="5m",
            candidates=(_candidate("btc/a.csv", timeframe="1m"),),
        )
