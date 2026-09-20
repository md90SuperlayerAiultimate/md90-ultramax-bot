# md90_superlayerAi — All-in-one Integration Matrix

## Product principle

md90_superlayerAi is one product surface with separated, auditable modules. “All-in-one” means one cockpit, one canonical event vocabulary, one policy gate, and one audit trail. It does not mean every external service is treated as already integrated or every strategy is fused into one uncalibrated score.

## Source-to-system map

| Component | Intended role | Website surface | Backend contract | Status | Boundary |
|---|---|---|---|---|---|
| Alfa Quant levels 0–23 | Feature and decision hypotheses | Signal room / evidence stack | Canonical signal payload | paper-only | Must be calibrated and replay-tested |
| MD90 17-layer fusion | Confluence and evidence scoring | Primary signal / layer stack | `paper.overview` signal + provenance | paper-only | Cannot bypass risk policy |
| Cryptoiz / Solana DEX | Token, liquidity, and flow intelligence | Market map | Future venue adapter | external | Source quality and latency must be measured |
| Dynamic Execution | External signal / service reference | Integration matrix | Future signal adapter | external | Not an execution authority |
| CCXT / exchange adapters | Market data and venue abstraction | Data freshness | Future adapter contract | planned | Credentials must remain server-side |
| Binance | Perpetual venue | Instrument/watchlist label | No live order route | live-blocked | Paper/replay only until approvals |
| Solana DEX | On-chain venue | Market map label | No wallet route | live-blocked | Wallet signing is disabled |
| Polymarket CLOB | Binary market venue | Not used for primary BTC signal | No mixed semantics | live-blocked | Must remain a separate market model |
| Backtest / replay | Historical and deterministic evaluation | Replay nav | Replay dataset / equity curve | integrated | Must include fees, spread, slippage, funding, and rejection |
| Paper broker | Simulated order/fill | Metrics, position, risk | Fee/slippage-aware paper payload | integrated | No network orders |
| Risk engine / policy | Exposure and loss boundaries | Risk gate | Risk checks and locked approval | integrated | Fail closed on stale or invalid data |
| AI / LLM | Explanation and research | AI note | Explanation only | experimental | Never an order authority |
| Self-learning / Optuna | Candidate model improvement | Not promoted | Offline candidate artifacts | live-blocked | Champion/challenger and rollback required |
| Arbitrage | Multi-leg execution hypothesis | Not promoted | Separate future service | live-blocked | Atomicity and venue semantics required |
| n8n / webhook | Automation and notifications | Future operations panel | Signed command ingress only | live-blocked | RBAC, signature, nonce, rate limit required |
| Journal / provenance | Audit and reproducibility | Evidence and system map | `paper_journal`, provenance fields | integrated | Append-only policy required |
| Live execution | Real order submission | Live locked state | No enabled route | live-blocked | Requires explicit staged approval |

## Current data lineage

`deterministic replay prices → paper engine calculations → signal/risk/trade/journal payload → tRPC paper.overview → Home dashboard`.

The current payload is a **deterministic paper replay**, not a live market feed. It includes bid/ask assumptions, fee, slippage, timestamps, signal provenance, one simulated fill, one position, risk checks, equity points, and an integration status map. External Cryptoiz/Dynamic Execution data is intentionally not claimed as connected until adapters and source validation are implemented.

## Readiness gates

1. Research: deterministic replay must reproduce the same payload under the same input.
2. Paper: fee, spread, slippage, partial fills, rejection, stop/target, and idempotency tests must pass.
3. Shadow: external market data may be observed but cannot submit orders.
4. Restricted live: requires credential isolation, order reconciliation, kill switch, operator approval, and rollback procedure.

## Explicit non-claims

The dashboard does not claim profitability, guaranteed edge, verified third-party performance, or live execution. All external services, AI outputs, and experimental features remain labeled by status until their interfaces and evidence meet the relevant gate.
