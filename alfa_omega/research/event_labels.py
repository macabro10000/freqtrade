"""Reusable causal event-label artifact for ALFA OMEGA research.

Labels are computed once on the full chronological dataset. Context filters
must be applied to prediction timestamps after this artifact is built; they
must never redefine the future event horizon.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alfa_omega.research.triple_barrier import triple_barrier_labels


@dataclass(frozen=True)
class EventLabelArtifact:
    labels: pd.DataFrame
    horizon_bars: int
    stop_atr: float
    target_atr: float
    source_rows: int

    def for_timestamps(self, timestamps: pd.Index) -> pd.DataFrame:
        """Return labels for exact decision timestamps only."""
        return self.labels.reindex(timestamps)


def build_event_label_artifact(
    frame: pd.DataFrame,
    *,
    horizon_bars: int,
    stop_atr: float,
    target_atr: float,
) -> EventLabelArtifact:
    """Compute labels on the complete timeline before context filtering."""
    labels = triple_barrier_labels(
        frame,
        horizon_bars=horizon_bars,
        stop_atr=stop_atr,
        target_atr=target_atr,
    )
    return EventLabelArtifact(
        labels=labels,
        horizon_bars=horizon_bars,
        stop_atr=stop_atr,
        target_atr=target_atr,
        source_rows=len(frame),
    )


def apply_decision_context(
    artifact: EventLabelArtifact,
    frame: pd.DataFrame,
    decision_mask: pd.Series,
) -> pd.DataFrame:
    """Attach precomputed labels to selected decision timestamps."""
    if not decision_mask.index.equals(frame.index):
        raise ValueError("decision_mask index must exactly match frame index")
    selected = frame.loc[decision_mask.fillna(False)]
    labels = artifact.for_timestamps(selected.index)
    return selected.join(labels, how="left")
