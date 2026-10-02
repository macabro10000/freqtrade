from alfa_omega.memory.memory_store import MemoryStore


def test_memory_persists_and_deduplicates(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    payload = {
        "market": "BTC/USD",
        "timeframe": "5m",
        "regime": "TREND",
        "pattern_ids": ["P-427"],
        "realized_r": -1.0,
    }
    first = store.remember("EXPERIENCE", payload, source="TEST")
    second = store.remember("EXPERIENCE", payload, source="TEST")
    assert first.record_id == second.record_id
    assert store.count() == 1

    recovered = MemoryStore(tmp_path / "memory")
    records = recovered.search(
        record_type="EXPERIENCE",
        market="BTC/USD",
        timeframe="5m",
        pattern_id="P-427",
    )
    assert len(records) == 1
    assert records[0].payload["realized_r"] == -1.0
