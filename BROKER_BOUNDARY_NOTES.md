# Broker Boundary Notes

## Binance public market data

Binance's official Spot REST documentation lists `https://data-api.binance.vision` as the base endpoint for APIs that only send public market data and points to a Market Data Only policy page. The same documentation states that timestamps are milliseconds by default, responses are chronological unless otherwise noted, and API requests have a 10-second processing timeout; a timeout can leave execution status unknown, which is relevant to any future order path. The adapter design therefore uses public market data first, records source timestamp and receive timestamp separately, and treats timeout/unknown status as a hard non-executable state.

## Security boundary

The first implementation target is read-only market data and health/freshness telemetry. No API key is needed for public market data. If a future private account adapter is ever introduced, it must use a separate credential scope and must not share credentials with the paper engine. Trading, withdrawal, transfer, and signing permissions remain disabled in the current project.

Source: https://developers.binance.com/en/docs/products/spot/rest-api
Source: https://developers.binance.com/en/docs/products/spot/faqs/market_data_only
