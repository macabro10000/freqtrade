from alfa_omega.research.candidate_bridge import build_candidate, candidate_key
from alfa_omega.research.hypothesis_factory import ResearchHypothesis
from alfa_omega.research.research_orchestrator import plan_research_tasks


def test_candidate_preserves_research_context():
    task = plan_research_tasks(
        markets=("BTC/USD",),
        timeframes=("5m",),
        sessions=("NEW_YORK",),
        regimes=("TREND",),
        topics=("INDICATOR_DISCOVERY",),
    )[0]
    hypothesis = ResearchHypothesis(
        hypothesis_id="H-001",
        market="BTC/USD",
        timeframe="5m",
        regime="TREND",
        conditions=("rsi14",),
        question="Does the condition improve expectancy?",
        rationale=("Research candidate only.",),
        source_patterns=("PATTERN-1",),
    )
    candidate = build_candidate(task, hypothesis)
    assert candidate.state == "RESEARCH_CANDIDATE"
    assert candidate.market == "BTC/USD"
    assert candidate.session == "NEW_YORK"
    assert candidate.conditions == ("rsi14",)
    assert candidate_key(candidate)[4] == "H-001"
