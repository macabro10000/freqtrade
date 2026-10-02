# ALFA OMEGA — ALPACA PAPER

## Purpose

Alpaca is the first validated Paper provider for **BTC/USD**.

The provider was verified from the development environment before integration:

- Paper account reachable;
- account status active;
- account balance readable;
- positions readable;
- BTC/USD latest trade readable;
- no order submitted during validation.

## Security

Credentials are never stored in this repository.

Required environment variables:

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_PAPER=true`

The adapter rejects non-Paper configuration.

## Current capability

The adapter currently supports only:

- health check;
- account information;
- positions;
- latest crypto trade.

Order submission and cancellation are deliberately blocked.

## Next phase

Before enabling Paper orders, ALFA OMEGA must implement and validate:

1. OrderIntent validation;
2. Risk Engine;
3. Safety Gate;
4. position sizing;
5. stop-loss validation;
6. execution logging;
7. idempotent client order IDs;
8. order/fill reconciliation;
9. kill switch;
10. Paper-only integration test.

Only after those controls pass will the adapter receive an enabled order path.
