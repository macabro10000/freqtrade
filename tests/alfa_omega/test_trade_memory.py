"""Tests for auditable trade lifecycle memory."""

from pathlib import Path

from alfa_omega.intelligence.trade_lifecycle import calculate_trade_outcome
from alfa_omega.memory.memory_store import MemoryStore
from alfa_omega.memory.trade_memory import TradeMemory


def test_trade_outcome_is_persisted_and_deduplicated(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "memory.jsonl")
    memory = TradeMemory(store)
    outcome = calculate_trade_outcome(
        trade_id="T-1",
        market="BTC/USD",
        side="LONG",
        entry_price=100.0,
        exit_price=102.0,
        quantity=1.0,
        fees=0.1,
        slippage=0.2,
        entry_reason="BUY",
        exit_reason="THESIS_INVALIDATED",
        expected_target=104.0,
        expected_stop=98.0,
        regime="TREND",
    )

    first = memory.remember_outcome(outcome, model_version="M1", feature_version="F1")
    second = memory.remember_outcome(outcome, model_version="M1", feature_version="F1")

    assert first.record_id == second.record_id
    assert store.count(TradeMemory.OUTCOME_KIND) == 1
    assert first.payload["net_pnl"] == 1.7
    assert first.payload["training_eligible"] is False
    assert first.payload["model_version"] == "M1"


def test_decision_and_execution_are_kept_as_separate_observations(
    tmp_path: Path,
) -> None:
    memory = TradeMemory(MemoryStore(tmp_path / "memory.jsonl"))

    decision = memory.remember_decision(
        {"decision_id": "D1", "action": "BUY", "confidence": 0.8}
    )
    execution = memory.remember_execution(
        {"execution_id": "E1", "status": "FILLED", "fill_price": 100.0}
    )

    assert decision.kind == TradeMemory.DECISION_KIND
    assert execution.kind == TradeMemory.EXECUTION_KIND
    assert memory.store.count() == 2
    assert decision.payload["training_eligible"] is False
    assert execution.payload["training_eligible"] is False
