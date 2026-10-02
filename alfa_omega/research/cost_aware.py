"""Cost-aware research evaluation for ALFA OMEGA.

Applies deterministic execution-cost assumptions to gross R results. This is
research accounting only; it never places orders or changes live risk policy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ExecutionCostModel:
    fee_bps: float = 5.0
    spread_bps: float = 2.0
    slippage_bps: float = 3.0
    latency_bps: float = 0.0

    def __post_init__(self) -> None:
        values = (self.fee_bps, self.spread_bps, self.slippage_bps, self.latency_bps)
        if any(value < 0 for value in values):
            raise ValueError("execution cost components must be non-negative")

    @property
    def round_trip_bps(self) -> float:
        return 2.0 * self.fee_bps + self.spread_bps + self.slippage_bps + self.latency_bps


@dataclass(frozen=True)
class CostAwareResult:
    gross_expectancy_r: float
    net_expectancy_r: float
    gross_profit_factor: float
    net_profit_factor: float
    trades: int
    cost_r_per_trade: float
    total_cost_r: float
    status: str
    notes: tuple[str, ...] = ()


def evaluate_costs(
    gross_r_values: list[float] | tuple[float, ...],
    *,
    model: ExecutionCostModel | None = None,
    risk_fraction_price: float = 0.01,
) -> CostAwareResult:
    """Convert basis-point execution cost into R and subtract it."""
    if risk_fraction_price <= 0:
        raise ValueError("risk_fraction_price must be positive")

    model = model or ExecutionCostModel()
    values = [float(value) for value in gross_r_values]
    trades = len(values)

    if trades == 0:
        return CostAwareResult(
            gross_expectancy_r=0.0,
            net_expectancy_r=0.0,
            gross_profit_factor=0.0,
            net_profit_factor=0.0,
            trades=0,
            cost_r_per_trade=0.0,
            total_cost_r=0.0,
            status="NO_TRADES",
        )

    cost_r = (model.round_trip_bps / 10_000.0) / risk_fraction_price
    net_values = [value - cost_r for value in values]

    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    net_profit = sum(value for value in net_values if value > 0)
    net_loss = -sum(value for value in net_values if value < 0)

    gross_pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    net_pf = net_profit / net_loss if net_loss > 0 else float("inf")
    net_expectancy = sum(net_values) / trades

    status = "COST_AWARE_POSITIVE" if net_expectancy > 0 else "COST_AWARE_FAILED"
    notes = (
        "Costs are assumptions, not broker-measured execution.",
        "Instrument-specific spread/slippage/fee calibration is required before promotion.",
    )

    return CostAwareResult(
        gross_expectancy_r=sum(values) / trades,
        net_expectancy_r=net_expectancy,
        gross_profit_factor=gross_pf,
        net_profit_factor=net_pf,
        trades=trades,
        cost_r_per_trade=cost_r,
        total_cost_r=cost_r * trades,
        status=status,
        notes=notes,
    )


def cost_aware_to_dict(value: CostAwareResult) -> dict[str, object]:
    return asdict(value)
