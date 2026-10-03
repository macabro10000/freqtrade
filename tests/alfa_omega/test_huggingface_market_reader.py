from pathlib import Path

import pandas as pd
import pytest

from alfa_omega.data.huggingface_market_reader import read_market_data_file
from alfa_omega.data.market_file_classifier import MarketDataFileCandidate


def _candidate(path="btc/BTCUSD_5m.csv", file_format="csv"):
    return MarketDataFileCandidate(
        path=path,
        size=None,
        market="BTC/USD",
        timeframe="5m",
        format=file_format,
        classification="MARKET_DATA_CANDIDATE",
    )


class FakeApi:
    def __init__(self, source: Path):
        self.source = source
        self.downloads = []

    def hf_hub_download(self, **kwargs):
        self.downloads.append(kwargs)
        return str(self.source)


def _csv(tmp_path, body=None):
    source = tmp_path / "data.csv"
    source.write_text(
        body
        or "timestamp,open,high,low,close,volume\n"
        "2026-01-01 00:00:00,100,101,99,100.5,10\n"
        "2026-01-01 00:05:00,100.5,102,100,101.5,12\n",
        encoding="utf-8",
    )
    return source


def test_reads_one_selected_csv_and_normalizes_utc(tmp_path):
    source = _csv(tmp_path)
    api = FakeApi(source)

    frame, catalog = read_market_data_file(
        api,
        repository="Macabro10000/trading-data",
        candidate=_candidate(),
    )

    assert api.downloads[0]["filename"] == "btc/BTCUSD_5m.csv"
    assert frame.index.tz is not None
    assert str(frame.index.tz) == "UTC"
    assert frame.index.name == "timestamp"
    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert catalog["market"] == "BTC/USD"
    assert catalog["timeframe"] == "5m"
    assert catalog["source_path"] == "btc/BTCUSD_5m.csv"
    assert len(catalog["source_sha256"]) == 64


def test_converts_aware_non_utc_timestamps_to_utc(tmp_path):
    source = _csv(
        tmp_path,
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01 00:00:00-05:00,100,101,99,100.5,10\n",
    )
    frame, _ = read_market_data_file(
        FakeApi(source),
        repository="Macabro10000/trading-data",
        candidate=_candidate(),
    )
    assert str(frame.index.tz) == "UTC"
    assert frame.index[0] == pd.Timestamp("2026-01-01 05:00:00", tz="UTC")


def test_rejects_missing_timestamp(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text(
        "open,high,low,close,volume\n100,101,99,100,10\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="timestamp"):
        read_market_data_file(
            FakeApi(source),
            repository="Macabro10000/trading-data",
            candidate=_candidate(),
        )


def test_rejects_invalid_ohlc(tmp_path):
    source = _csv(
        tmp_path,
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01 00:00:00,100,90,99,100,10\n",
    )
    with pytest.raises(ValueError, match="quality validation"):
        read_market_data_file(
            FakeApi(source),
            repository="Macabro10000/trading-data",
            candidate=_candidate(),
        )


def test_rejects_unsupported_format():
    candidate = _candidate(path="btc/5m.json", file_format="json")
    with pytest.raises(ValueError, match="unsupported format"):
        read_market_data_file(
            FakeApi(Path("/does/not/matter")),
            repository="Macabro10000/trading-data",
            candidate=candidate,
        )


def test_rejects_non_candidate():
    candidate = MarketDataFileCandidate(
        path="notes/readme.md",
        size=10,
        market=None,
        timeframe=None,
        format="md",
        classification="UNRESOLVED",
    )
    with pytest.raises(ValueError, match="validated market-data candidate"):
        read_market_data_file(
            FakeApi(Path("/does/not/matter")),
            repository="Macabro10000/trading-data",
            candidate=candidate,
        )


def test_rejects_missing_ohlcv(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text(
        "timestamp,open,high,low,close\n"
        "2026-01-01 00:00:00,100,101,99,100\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="OHLCV"):
        read_market_data_file(
            FakeApi(source),
            repository="Macabro10000/trading-data",
            candidate=_candidate(),
        )
