# ALFA OMEGA — Render deployment

## Current deployment target

- Service: `alfa-omega-trading`
- Branch: `alfa-omega-rebuild`
- Runtime: Python 3.13.15
- Start command: `uvicorn alfa_omega.render_service:app --host 0.0.0.0 --port $PORT`
- Health: `/health`
- Mode: PAPER
- Provider: Alpaca
- Market read path: BTC/USD
- Broker order submission: DISABLED
- Live execution: DISABLED

## Required Render environment variables

Secrets must be entered in Render, never committed to GitHub:

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`

Non-secret configuration:

- `ALPACA_PAPER=true`
- `ALPACA_TRADING_URL=https://paper-api.alpaca.markets`

## What this service does now

1. Starts the ALFA OMEGA control service.
2. Exposes health and status endpoints.
3. Connects to Alpaca Paper when credentials are available.
4. Reads account, positions and BTC/USD market data.
5. Keeps broker order submission blocked.
6. Keeps live execution blocked.

## What it does not do yet

It does not place Paper or Live orders. The execution path remains:

SIGNAL → RISK ENGINE → SAFETY GATE → BROKER ADAPTER

and the final broker mutation step is intentionally disabled.

Before enabling Paper orders we still require OrderIntent validation, execution logging, idempotent client order IDs, fill reconciliation, integration tests and a controlled Paper execution test.
