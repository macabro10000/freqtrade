"""ALFA OMEGA Render service.

Research/control-plane service only.
Paper broker access is read-only until execution controls are explicitly enabled.
No endpoint in this module submits broker orders.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from alfa_omega.execution.alpaca_paper import AlpacaPaperAdapter

app = FastAPI(
    title="ALFA OMEGA",
    version="0.1.0",
    description="ALFA OMEGA research and execution-control service.",
)

STARTED_AT = datetime.now(UTC)
adapter = AlpacaPaperAdapter()


def _safe_health() -> dict[str, Any]:
    """Return health without exposing credentials or account secrets."""
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


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "ALFA OMEGA",
        "status": "online",
        "mode": "PAPER",
        "execution": "READ_ONLY",
        "message": "ALFA OMEGA control service is running.",
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
        "phase": "RESEARCH_FOUNDATION",
        "mode": "PAPER",
        "paper_provider": "alpaca",
        "paper_market": "BTC/USD",
        "order_execution_enabled": False,
        "live_execution_enabled": False,
        "risk_engine": True,
        "safety_gate": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/v1/account")
def account() -> JSONResponse:
    """Read Paper account metadata; never exposes API credentials."""
    try:
        account = adapter.get_account()
        return JSONResponse(status_code=200, content=account)
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "error": str(exc)},
        )


@app.get("/api/v1/positions")
def positions() -> JSONResponse:
    """Read Paper positions; no order mutation."""
    try:
        return JSONResponse(status_code=200, content=adapter.get_positions())
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "error": str(exc)},
        )


@app.get("/api/v1/market/btc-usd")
def btc_usd() -> JSONResponse:
    """Read the latest BTC/USD Paper market trade."""
    try:
        return JSONResponse(
            status_code=200,
            content=adapter.get_latest_crypto_trade("BTC/USD"),
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "error": str(exc)},
        )


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
