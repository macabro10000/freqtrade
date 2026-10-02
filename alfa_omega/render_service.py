"""ALFA OMEGA Render service.

Research/control-plane service only. Paper broker access is read-only until
execution controls are explicitly enabled. No endpoint submits broker orders.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from alfa_omega.data.alpaca_crypto import AlpacaCryptoDataClient
from alfa_omega.execution.alpaca_paper import AlpacaPaperAdapter
from alfa_omega.features.feature_engine import build_features

app = FastAPI(
    title="ALFA OMEGA",
    version="0.2.0",
    description="ALFA OMEGA research and execution-control service.",
)

STARTED_AT = datetime.now(UTC)
adapter = AlpacaPaperAdapter()
data_client = AlpacaCryptoDataClient()


def _safe_health() -> dict[str, Any]:
    result = adapter.health_check()
    return {
        "service": "ALFA OMEGA",
        "status": "ok" if result.get("healthy") else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "started_at": STARTED_AT.isoformat(),
        "mode": "PAPER",
        "paper": True,
        "order_execution_enabled": False,
        "provider": "alpaca",
        "broker": result,
    }


def _bars_to_frame(payload: dict[str, Any], symbol: str) -> pd.DataFrame:
    bars = payload.get("bars", {}).get(symbol, [])
    if not bars:
        return pd.DataFrame()
    frame = pd.DataFrame(bars)
    rename = {"t": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", "n": "trade_count"}
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
        "order_execution_enabled": False,
        "live_execution_enabled": False,
        "risk_engine": True,
        "safety_gate": True,
        "data_engine": True,
        "feature_engine": True,
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
            return JSONResponse(status_code=503, content={"status": "unavailable", "error": "No BTC/USD bars returned"})
        features = build_features(frame)
        latest = features.iloc[-1].replace({pd.NA: None}).to_dict()
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "symbol": "BTC/USD",
                "timeframe": "5Min",
                "bars_received": int(len(frame)),
                "latest_timestamp": features.index[-1].isoformat(),
                "latest_features": latest,
            },
        )
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(exc)})


@app.get("/api/v1/execution")
def execution_status() -> dict[str, Any]:
    return {
        "mode": "PAPER",
        "provider": "alpaca",
        "read_only": True,
        "order_submission": False,
        "risk_engine": "ENABLED",
        "safety_gate": "ENABLED",
        "live": False,
        "message": "Broker order submission remains intentionally disabled.",
    }


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "service": "ALFA OMEGA"}
