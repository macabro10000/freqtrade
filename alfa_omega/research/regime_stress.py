"""Regime-stress evaluation for ALFA OMEGA.

Measures whether a research result remains viable across market regimes.
This module is descriptive only and never promotes or deploys a strategy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RegimeMetrics:
    regime: str
    trades: int
    expectancy_r: float
    win_rate: float
    profit_factor: float


@dataclass(frozen=True)
class RegimeStressResult:
    status: str
    regimes: tuple[RegimeMetrics, ...]
    regimes_positive: int
    regimes_tested: int
    worst_expectancy_r: float
    mean_expectancy_r: float
    notes: tuple[str, ...] = ()


def evaluate_regime_stress(
    regimes: list[str] | tuple[str, ...],
    r_values: list[float] | tuple[float, ...],
    *,
    min_trades_per_regime: int = 5,
) -> RegimeStressResult:
    """Evaluate per-regime R outcomes without reordering or shuffling data."""
    if len(regimes) != len(r_values):
        raise ValueError("regimes and r_values must have equal length")
    if min_trades_per_regime < 1:
        raise ValueError("min_trades_per_regime must be positive")

    grouped: dict[str, list[float]] = {}
    for regime, value in zip(regimes, r_values, strict=True):
        grouped.setdefault(str(regime), []).append(float(value))

    metrics: list[RegimeMetrics] = []
    for regime in sorted(grouped):
        values = grouped[regime]
        if len(values) < min_trades_per_regime:
            continue
        wins = sum(value > 0 for value in values)
        gross_profit = sum(value for value in values if value > 0)
        gross_loss = -sum(value for value in values if value < 0)
        pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        metrics.append(
            RegimeMetrics(
                regime=regime,
                trades=len(values),
                expectancy_r=sum(values) / len(values),
                win_rate=wins / len(values),
                profit_factor=pf,
            )
        )

    if not metrics:
        return RegimeStressResult(
            status="REGIME_STRESS_INSUFFICIENT_DATA",
            regimes=(),
            regimes_positive=0,
            regimes_tested=0,
            worst_expectancy_r=0.0,
            mean_expectancy_r=0.0,
            notes=("No regime reached the minimum trade threshold.",),
        )

    expectancies = [item.expectancy_r for item in metrics]
    positive = sum(value > 0 for value in expectancies)
    status = (
        "REGIME_STRESS_ALL_POSITIVE"
        if positive == len(metrics)
        else "REGIME_STRESS_MIXED"
    )

    return RegimeStressResult(
        status=status,
        regimes=tuple(metrics),
        regimes_positive=positive,
        regimes_tested=len(metrics),
        worst_expectancy_r=min(expectancies),
        mean_expectancy_r=sum(expectancies) / len(expectancies),
        notes=(
            "Regime results are descriptive evidence, not an automatic promotion decision.",
            "Regime labels must be generated causally from information available at the decision timestamp.",
        ),
    )


def regime_stress_to_dict(value: RegimeStressResult) -> dict[str, object]:
    return asdict(value)
