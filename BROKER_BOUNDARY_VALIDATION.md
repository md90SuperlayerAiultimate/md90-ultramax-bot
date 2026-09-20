# Broker Boundary Validation

## Code paths

The broker route is `appRouter.broker.publicTicker` in `server/routers.ts`. It calls only `fetchBinancePublicTicker("BTCUSDT")` from `server/brokerMarketData.ts`.

The adapter uses Binance's public market-data endpoint `https://data-api.binance.vision/api/v3/ticker/bookTicker`. It does not read environment credentials, does not accept API keys from the client, and does not expose a private account or order mutation. The normalized payload always carries `venue: BINANCE_PUBLIC` and `orderRoute: DISABLED`.

Freshness is derived from the response `Date` header when present, with the receive time as fallback. A source age above 15 seconds is classified `STALE`. The adapter retries one time after a transient failure, aborts an individual request after the production timeout, and surfaces final failure as `BINANCE_PUBLIC_BLOCKED`.

## Test evidence

`server/brokerMarketData.test.ts` covers valid normalization, crossed/malformed quotes, stale source timestamps, HTTP 429 followed by retry success, absence of API-key material in the public request, timeout/abort, incomplete payload, and disabled order route. The broader suite passes with 35 tests.

## Live boundary

The adapter is market-data-only. Paper execution remains in the deterministic paper broker. Shadow observations remain non-executable. Live venue adapters and credential-based trading are still marked `LIVE BLOCKED`; this file does not authorize or implement live trading.

## Network smoke check

A direct request to `https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=BTCUSDT` returned HTTP 200 on 23 Aug 2026, with JSON content type, `x-mbx-used-weight: 2`, and no authentication requirement. The adapter remains read-only and does not infer account or execution capability from this response.
