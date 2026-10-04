"""Immutable experiment contracts for the ALFA OMEGA Experiment Lab.

The Lab records ideas and verdicts without touching broker execution.
Promotion is an explicit research decision, never an automatic deployment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

ExperimentVerdict = Literal[
    "PLANNED",
    "RUNNING",
    "REJECTED",
    "INSUFFICIENT_EVIDENCE",
    "PROMOTE_TO_CANDIDATE",
    "READY_FOR_PAPER_REVIEW",
]


@dataclass(frozen=True)
class ExperimentProposal:
    experiment_id: str
    title: str
    hypothesis: str
    motivation: str
    market: str
    timeframe: str
    dataset_fingerprint: str
    feature_version: str
    label_version: str
    validation_plan: tuple[str, ...]
    status: ExperimentVerdict = "PLANNED"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentVerdictRecord:
    experiment_id: str
    verdict: ExperimentVerdict
    evidence: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()
    next_action: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_proposal(proposal: ExperimentProposal) -> None:
    """Validate the research contract; never execute or promote an experiment."""
    if not proposal.experiment_id.strip():
        raise ValueError("experiment_id must not be empty")
    if not proposal.title.strip():
        raise ValueError("title must not be empty")
    if not proposal.hypothesis.strip():
        raise ValueError("hypothesis must not be empty")
    if not proposal.market.strip():
        raise ValueError("market must not be empty")
    if not proposal.timeframe.strip():
        raise ValueError("timeframe must not be empty")
    if not proposal.dataset_fingerprint.strip():
        raise ValueError("dataset_fingerprint must not be empty")
    if not proposal.feature_version.strip():
        raise ValueError("feature_version must not be empty")
    if not proposal.label_version.strip():
        raise ValueError("label_version must not be empty")
    if not proposal.validation_plan:
        raise ValueError("validation_plan must not be empty")


def can_promote(verdict: ExperimentVerdict) -> bool:
    """Return whether the verdict is eligible for the next research gate."""
    return verdict in {"PROMOTE_TO_CANDIDATE", "READY_FOR_PAPER_REVIEW"}
