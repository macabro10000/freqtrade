from alfa_omega.data.huggingface_catalog import HuggingFaceFile
from alfa_omega.data.market_file_classifier import classify_file, classify_inventory


def test_classify_btc_5m_csv():
    candidate = classify_file(
        HuggingFaceFile(path="btc/BTCUSD_5m.csv", size=100, kind="file")
    )
    assert candidate.market == "BTC/USD"
    assert candidate.timeframe == "5m"
    assert candidate.format == "csv"
    assert candidate.classification == "MARKET_DATA_CANDIDATE"


def test_classify_xau_1m_parquet():
    candidate = classify_file(
        HuggingFaceFile(path="XAUUSD/2024/1m.parquet", size=200, kind="file")
    )
    assert candidate.market == "XAU/USD"
    assert candidate.timeframe == "1m"
    assert candidate.format == "parquet"


def test_unresolved_file_is_not_treated_as_market_data():
    candidate = classify_file(
        HuggingFaceFile(path="models/readme.md", size=10, kind="file")
    )
    assert candidate.classification == "UNRESOLVED"
    assert candidate.market is None
    assert candidate.timeframe is None


def test_ambiguous_timeframe_is_unresolved():
    candidate = classify_file(
        HuggingFaceFile(path="btc/1m_to_5m.csv", size=10, kind="file")
    )
    assert candidate.classification == "RELATED_BUT_UNRESOLVED"
    assert candidate.timeframe is None


def test_inventory_is_sorted_and_serializable():
    files = [
        HuggingFaceFile(path="xau/1h.csv", size=2, kind="file"),
        HuggingFaceFile(path="btc/5m.csv", size=1, kind="file"),
    ]
    result = classify_inventory(files)
    assert [item["path"] for item in result] == ["btc/5m.csv", "xau/1h.csv"]
