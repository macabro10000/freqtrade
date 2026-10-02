import pandas as pd

from alfa_omega.research.candidate_bridge import ResearchCandidate
from alfa_omega.research.experiment_runner import ExperimentSpec
from alfa_omega.research.research_pipeline import run_research_pipeline
from alfa_omega.research.research_policy import ResearchGate


def test_pipeline_rejects_insufficient_evidence_without_trading():
    idx = pd.date_range("2026-01-01", periods=30, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": 99.5,
            "high": 100.0,
            "low": 99.0,
            "close": 99.5,
            "atr_14": 1.0,
            "rsi14": 1.0,
            "mi_regime": "TREND",
        },
        index=idx,
    )
    candidate = ResearchCandidate(
        candidate_id="C-1",
        task_id="T-1",
        hypothesis_id="H-1",
        market="BTC/USD",
        timeframe="5m",
        session="OFF_SESSION",
        regime="TREND",
        topic="PATTERN_DISCOVERY",
        source_finding_ids=(),
        conditions=("rsi14",),
    )
    spec = ExperimentSpec(
        experiment_id="E-1",
        hypothesis_id="H-1",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        dataset_fingerprint="D",
        feature_version="F",
        label_version="L",
        validation_plan=("OUT_OF_SAMPLE",),
        horizon_bars=5,
        stop_atr=1.0,
        target_atr=2.0,
    )
    gate = ResearchGate(True, True, True, True, True, True, True, True)
    result = run_research_pipeline(
        candidate=candidate,
        spec=spec,
        frame=frame,
        regimes=None,
        gate=gate,
    )
    assert result.final_state == "INSUFFICIENT_EVIDENCE"
