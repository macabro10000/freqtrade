"""Executable bridge for one ALFA OMEGA research candidate.

This module binds a planned research task to the existing causal pipeline.
It performs research only: no broker calls, no execution authorization and
no live configuration changes.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alfa_omega.research.candidate_bridge import ResearchCandidate
from alfa_omega.research.experiment_runner import ExperimentSpec
from alfa_omega.research.research_orchestrator import ResearchTask
from alfa_omega.research.research_pipeline import ResearchPipelineResult, run_research_pipeline
from alfa_omega.research.research_policy import ResearchGate


@dataclass(frozen=True)
class ResearchCycleJob:
    task: ResearchTask
    candidate: ResearchCandidate
    spec: ExperimentSpec
    frame: pd.DataFrame
    regimes: pd.Series | None
    gate: ResearchGate


def execute_research_cycle(job: ResearchCycleJob) -> ResearchPipelineResult:
    """Execute the existing OOS/WF/cost/regime pipeline for one candidate."""
    if job.task.task_id != job.candidate.task_id:
        raise ValueError("task and candidate do not belong to the same research job")
    if job.candidate.hypothesis_id != job.spec.hypothesis_id:
        raise ValueError("candidate and experiment hypothesis IDs do not match")
    if job.candidate.market != job.spec.market:
        raise ValueError("candidate and experiment markets do not match")
    if job.candidate.timeframe != job.spec.timeframe:
        raise ValueError("candidate and experiment timeframes do not match")
    return run_research_pipeline(
        candidate=job.candidate,
        spec=job.spec,
        frame=job.frame,
        regimes=job.regimes,
        gate=job.gate,
    )
