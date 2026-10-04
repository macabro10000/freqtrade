""""ALFA OMEGA Render service.

Research/control-plane service with an explicitly gated Paper smoke-cycle
endpoint. Normal trading signals still cannot submit orders directly.
"""
from __future__ import annotations

import hmac
import os
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from alfa_omega.control.control_service import ControlService
from alfa_omega.control.control_store import MongoControlStateStore
from alfa_omega.data.alpaca_crypto import AlpacaCryptoDataClient
from alfa_omega.execution.alpaca_paper import AlpacaPaperAdapter
from alfa_omega.features.feature_engine import build_features
from alfa_omega.features.multi_timeframe import build_market_map, describe_hierarchy
from alfa_omega.features.proprietary_engine import build_proprietary_features
from alfa_omega.intelligence.market_intelligence import (
    build_market_intelligence,
    latest_market_state,
)
from alfa_omega.research.runtime_store import MongoResearchRuntimeStore
from alfa_omega.smc.structure_engine import build_structure_features


app = FastAPI(
    title="ALFA OMEGA",
    version="0.2.0",
    description="ALFA OMEGA research and execution-control service.",
)

STARTED_AT = datetime.now(UTC)
adapter = AlpacaPaperAdapter()
data_client = AlpacaCryptoDataClient()


def _build_control_service() -> ControlService:
    store = MongoControlStateStore.from_environment()
    return ControlService(store=store) if store is not None else ControlService()


control_service = _build_control_service()
research_runtime_store = MongoResearchRuntimeStore.from_environment()


class PaperSmokeRequest(BaseModel):
    confirmation: str


class MarketRequest(BaseModel):
    market: str


class TimeframeRequest(BaseModel):
    timeframe: str


def _control_authorized(token: str | None) -> bool:
    expected = os.getenv("ALFA_OMEGA_CONTROL_TOKEN")
    return bool(expected and token and hmac.compare_digest(token, expected))


def _safe_health() -> dict[str, Any]:
    result = adapter.health_check()
    return {
        "service": "ALFA OMEGA",
        "status": "ok" if result.get("healthy") else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "started_at": STARTED_AT.isoformat(),
        "mode": "PAPER",
        "paper": True,
        "order_execution_enabled": adapter.order_execution_enabled,
        "provider": "alpaca",
        "broker": result,
    }


def _bars_to_frame(payload: dict[str, Any], symbol: str) -> pd.DataFrame:
    bars = payload.get("bars", {}).get(symbol, [])
    if not bars:
        return pd.DataFrame()
    frame = pd.DataFrame(bars)
    rename = {
        "t": "timestamp", "o": "open", "h": "high", "l": "low",
        "c": "close", "v": "volume", "n": "trade_count",
    }
    frame = frame.rename(columns=rename)
    if "timestamp" in frame:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame.set_index("timestamp")
    for column in ("open", "high", "low", "close", "volume"):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.sort_index()


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "ALFA OMEGA",
        "status": "online",
        "mode": "PAPER",
        "execution": "READ_ONLY",
        "research_data": "ENABLED",
        "message": "ALFA OMEGA control and research service is running.",
    }


@app.get("/health")
def health() -> JSONResponse:
    payload = _safe_health()
    code = 200 if payload["status"] == "ok" else 503
    return JSONResponse(status_code=code, content=payload)


@app.get("/api/v1/status")
def status() -> dict[str, Any]:
    return {
        "project": "ALFA OMEGA TRADING",
        "phase": "RESEARCH_FOUNDATION_DATA_FEATURES",
        "mode": "PAPER",
        "paper_provider": "alpaca",
        "paper_market": "BTC/USD",
        "control": control_service.snapshot(),
        "order_execution_enabled": adapter.order_execution_enabled,
        "live_execution_enabled": False,
        "risk_engine": True,
        "safety_gate": True,
        "data_engine": True,
        "feature_engine": True,
        "smc_engine": True,
        "liquidity_engine": True,
        "multi_timeframe_engine": True,
        "proprietary_indicator_engine": True,
        "proprietary_indicator_count": 3,
        "market_intelligence_engine": True,
        "market_hierarchy": describe_hierarchy(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/v1/account")
def account() -> JSONResponse:
    try:
        return JSONResponse(status_code=200, content=adapter.get_account())
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(exc)})


@app.get("/api/v1/positions")
def positions() -> JSONResponse:
    try:
        return JSONResponse(status_code=200, content=adapter.get_positions())
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(exc)})


@app.get("/api/v1/market/btc-usd")
def btc_usd() -> JSONResponse:
    try:
        return JSONResponse(status_code=200, content=adapter.get_latest_crypto_trade("BTC/USD"))
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(exc)})


@app.get("/api/v1/data/btc-usd")
def btc_usd_bars(limit: int = 100) -> JSONResponse:
    """Read recent BTC/USD bars and return a causal feature snapshot.

    This endpoint only reads market data and computes features. It cannot place
    or modify an order.
    """
    try:
        payload = data_client.get_bars(symbol="BTC/USD", timeframe="5Min", limit=limit)
        frame = _bars_to_frame(payload, "BTC/USD")
        if frame.empty:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "error": "No BTC/USD bars returned"},
            )
        features = build_features(frame)
        features = build_structure_features(features)
        features = build_proprietary_features(features)
        features = build_market_intelligence(features)
        latest = features.iloc[-1].replace({pd.NA: None}).to_dict()
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "symbol": "BTC/USD",
                "timeframe": "5Min",
                "bars_received": len(frame),
                "latest_timestamp": features.index[-1].isoformat(),
                "latest_features": latest,
                "market_state": latest_market_state(features),
            },
        )
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(exc)})


@app.get("/api/v1/data/btc-usd/multi-timeframe")
def btc_usd_multi_timeframe(limit: int = 1000) -> JSONResponse:
    """Build a causal top-down market map from 1W through 1M BTC/USD data.

    Higher-timeframe candles are exposed to the target 5m context only after
    the higher-timeframe candle has closed. This endpoint is read-only.
    """
    if limit < 50 or limit > 10000:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": "limit must be between 50 and 10000"},
        )

    timeframes = {
        "1w": "1Week",
        "1d": "1Day",
        "4h": "4Hour",
        "1h": "1Hour",
        "15m": "15Min",
        "5m": "5Min",
        "1m": "1Min",
    }

    try:
        frames: dict[str, pd.DataFrame] = {}
        for key, alpaca_tf in timeframes.items():
            payload = data_client.get_bars(
                symbol="BTC/USD",
                timeframe=alpaca_tf,
                limit=limit,
            )
            frame = _bars_to_frame(payload, "BTC/USD")
            if not frame.empty:
                frames[key] = frame

        if "5m" not in frames:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "error": "No BTC/USD 5m bars returned"},
            )

        mapped = build_market_map(frames, target_timeframe="5m")
        latest = mapped.iloc[-1].replace({pd.NA: None}).to_dict()

        available = {tf: len(frame) for tf, frame in frames.items()}

        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "symbol": "BTC/USD",
                "target_timeframe": "5m",
                "bars_available": available,
                "hierarchy": describe_hierarchy(),
                "latest_timestamp": mapped.index[-1].isoformat(),
                "latest_market_map": latest,
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "error": str(exc)},
        )


@app.get("/api/v1/research/status")
def research_status() -> dict[str, Any]:
    """Return durable research-worker status plus current control state."""
    control = control_service.snapshot()
    durable_status = research_runtime_store.load_status() if research_runtime_store else None
    return {
        "status": "ok" if durable_status is not None else "unavailable",
        "durable": research_runtime_store is not None,
        "control": control,
        "research_enabled": control["research_enabled"],
        "execution_enabled": control["execution_enabled"],
        "worker": durable_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/v1/control/state")
def control_state() -> dict[str, Any]:
    """Return current control-plane state without broker access."""
    return control_service.snapshot()


@app.post("/api/v1/control/market")
def control_market(
    request: MarketRequest,
    x_alfa_omega_control_token: str | None = Header(default=None),
) -> JSONResponse:
    if not _control_authorized(x_alfa_omega_control_token):
        return JSONResponse(
            status_code=403,
            content={"status": "forbidden", "reason": "INVALID_CONTROL_TOKEN"},
        )
    try:
        return JSONResponse(
            status_code=200,
            content=control_service.set_market(request.market).public_dict(),
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "rejected", "reason": str(exc)})


@app.post("/api/v1/control/timeframe")
def control_timeframe(
    request: TimeframeRequest,
    x_alfa_omega_control_token: str | None = Header(default=None),
) -> JSONResponse:
    if not _control_authorized(x_alfa_omega_control_token):
        return JSONResponse(
            status_code=403,
            content={"status": "forbidden", "reason": "INVALID_CONTROL_TOKEN"},
        )
    try:
        return JSONResponse(
            status_code=200,
            content=control_service.set_timeframe(request.timeframe).public_dict(),
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "rejected", "reason": str(exc)})


@app.post("/api/v1/control/execution/connect")
def control_connect(
    x_alfa_omega_control_token: str | None = Header(default=None),
) -> JSONResponse:
    if not _control_authorized(x_alfa_omega_control_token):
        return JSONResponse(
            status_code=403,
            content={"status": "forbidden", "reason": "INVALID_CONTROL_TOKEN"},
        )
    return JSONResponse(status_code=200, content=control_service.connect_execution().public_dict())


@app.post("/api/v1/control/execution/stop")
def control_stop(
    x_alfa_omega_control_token: str | None = Header(default=None),
) -> JSONResponse:
    if not _control_authorized(x_alfa_omega_control_token):
        return JSONResponse(
            status_code=403,
            content={"status": "forbidden", "reason": "INVALID_CONTROL_TOKEN"},
        )
    return JSONResponse(status_code=200, content=control_service.stop_execution().public_dict())


@app.get("/api/v1/execution")
def execution_status() -> dict[str, Any]:
    return {
        "mode": "PAPER",
        "provider": "alpaca",
        "read_only": not adapter.order_execution_enabled,
        "order_submission": adapter.order_execution_enabled,
        "paper_smoke_test": "EXPLICITLY_GATED",
        "paper_smoke_trigger": "POST /api/v1/execution/paper-smoke",
        "risk_engine": "ENABLED",
        "safety_gate": "ENABLED",
        "live": False,
    }


@app.post("/api/v1/execution/paper-smoke")
def paper_smoke(
    request: PaperSmokeRequest,
    x_alfa_omega_smoke_token: str | None = Header(default=None),
) -> JSONResponse:
    """Run one explicitly confirmed Alpaca Paper BUY→SELL smoke cycle.

    The route is intentionally POST-only and requires a dedicated runtime
    secret plus an exact confirmation string. It never enables LIVE trading.
    """
    expected_token = os.getenv("ALFA_OMEGA_PAPER_SMOKE_TRIGGER_TOKEN")
    if not expected_token:
        return JSONResponse(
            status_code=503,
            content={"status": "disabled", "reason": "PAPER_SMOKE_TRIGGER_TOKEN_NOT_CONFIGURED"},
        )
    if not x_alfa_omega_smoke_token or not hmac.compare_digest(
        x_alfa_omega_smoke_token, expected_token
    ):
        return JSONResponse(
            status_code=403,
            content={"status": "forbidden", "reason": "INVALID_SMOKE_TRIGGER_TOKEN"},
        )
    if request.confirmation != "PAPER_SMOKE_BUY_SELL":
        return JSONResponse(
            status_code=400,
            content={"status": "rejected", "reason": "EXPLICIT_CONFIRMATION_REQUIRED"},
        )

    try:
        result = adapter.run_smoke_cycle()
        return JSONResponse(status_code=200, content=result)
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "failed", "error": str(exc)},
        )


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "service": "ALFA OMEGA"}
