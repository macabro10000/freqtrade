# ALFA OMEGA — Engineering & Research Integrity Audit

Date: 2026-10-02

## Critical findings

1. Triple-barrier horizon integrity: incomplete future windows must be UNRESOLVED, not valid TIME outcomes.
2. Context-specific validation: labels must be computed on the complete chronological timeline, then filtered by session/regime; never recompute N bars after filtering the timeline.
3. Experiment parameters are partially hard-coded (horizon/barriers) and must be immutable fields of the experiment contract.
4. Internet research currently ingests specified URLs; it is not yet a full search/research agent with provider abstraction, provenance, deduplication and reproducible search runs.
5. SSRF hardening needs allowlists, redirect controls, DNS-rebinding protection and parser-consistency checks.
6. Candidate selection bias is not yet measured. Candidate counts, rejected candidates, selection process and a final untouched holdout are required.
7. Cost-aware evaluation is simplified. Production-grade research needs instrument-specific fees, quote-derived spread, slippage/latency distributions, partial fills and Paper-measured execution costs.
8. Regime labels require causal provenance and versioning.
9. JSONL memory is a local persistent cache, not yet a durable distributed knowledge store. Target: local cache -> MongoDB durable store -> immutable research artifacts.
10. Alpaca Crypto has a hard capability constraint: current docs list market, limit and stop_limit with gtc/ioc and Crypto order_class simple. Do not assume crypto bracket/OCO emergency protection. Stop-limit is conditional protection but is not equivalent to guaranteed stop-market execution.

## Target research pipeline

SEARCH -> SOURCE VALIDATION -> SOURCE SNAPSHOT -> CLAIM EXTRACTION -> HYPOTHESIS -> PRE-REGISTRATION -> DATASET SNAPSHOT -> CAUSAL FEATURES -> EVENT LABELS -> TEMPORAL/OOS -> PURGED VALIDATION -> WALK-FORWARD -> COST MODEL -> REGIME STRESS -> SELECTION-BIAS REVIEW -> FINAL HOLDOUT -> RESEARCH GATE -> PAPER

## Target learning pipeline

PAPER RESULT -> RECONCILIATION -> EXPERIENCE -> ERROR CLASSIFICATION -> PATTERN LESSON -> DRIFT DETECTION -> FAILURE INVESTIGATION -> NEW HYPOTHESIS -> NEW EXPERIMENT

## Target execution pipeline

SIGNAL -> RISK -> SAFETY -> BROKER CAPABILITY CHECK -> ENTRY -> BROKER-SIDE PROTECTION -> POSITION MONITOR -> INTELLIGENT EXIT -> RECONCILIATION -> EXECUTION LEDGER

The intelligent exit and emergency protection are separate mechanisms.

## Production gates

- pytest research suite green
- Ruff green
- unresolved-horizon tests
- context-specific event-label tests
- immutable experiment protocol/versioning
- candidate-selection accounting
- untouched final holdout
- versioned cost model
- durable memory synchronization
- broker/instrument capability matrix
- continuous Paper reconciliation
- LIVE explicitly disabled until all gates pass

This audit does not authorize live trading.