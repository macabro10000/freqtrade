# ALFA OMEGA — Experiment Lab

## Purpose

The Experiment Lab is an isolated research area for ideas that may improve ALFA OMEGA without directly modifying production behavior.

It is for:

- new indicators;
- alternative feature definitions;
- new pattern detectors;
- alternative decision rules;
- execution-control improvements;
- data-quality ideas;
- model candidates;
- research tooling;
- performance improvements;
- hypotheses inspired by external research;
- failed ideas that should be preserved as negative knowledge.

## Isolation rule

A Lab experiment is **not production code**.

An experiment must not:

- submit broker orders;
- enable LIVE;
- modify execution policy;
- bypass RiskEngine or SafetyGate;
- silently modify production features;
- silently become training data;
- be promoted because an in-sample backtest looks good.

## Experiment lifecycle

```
IDEA
  ↓
HYPOTHESIS
  ↓
EXPERIMENT SPEC
  ↓
IMPLEMENTATION ISOLATED
  ↓
UNIT/INTEGRATION TEST
  ↓
BACKTEST
  ↓
OOS
  ↓
WALK-FORWARD
  ↓
COST / SLIPPAGE
  ↓
REGIME STRESS
  ↓
SELECTION-BIAS REVIEW
  ↓
FINAL HOLDOUT
  ↓
VERDICT
  ├── REJECTED
  ├── INSUFFICIENT_EVIDENCE
  ├── PROMOTE_TO_CANDIDATE
  └── READY_FOR_PAPER_REVIEW
```

## Required experiment record

Every experiment should identify:

- unique experiment ID;
- hypothesis;
- motivation/source;
- affected market/timeframe;
- code/artifacts;
- dataset fingerprint;
- feature/label versions;
- validation plan;
- metrics;
- failure modes;
- verdict;
- promotion decision;
- provenance.

## Promotion rule

The Lab can produce a candidate for the main research pipeline. It does **not** directly promote code into execution.

Promotion must produce a reviewable artifact and pass the same research gates used by the main pipeline.

A failed experiment is retained when useful because it can become:

- negative knowledge;
- a regression test;
- a constraint;
- evidence against a hypothesis;
- input to a future experiment.

## Business objective

The commercial objective of ALFA OMEGA is to build a system with a durable, measurable trading edge while controlling downside and avoiding false confidence.

The Lab therefore optimizes for **validated evidence**, not for producing the largest backtest number.

No experiment can guarantee profit or future returns.
