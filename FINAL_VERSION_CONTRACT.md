# md90_SuperlayerAi — Final Version Contract

## Product definition

**md90_SuperlayerAi** is one institutional market-intelligence cockpit with one canonical event vocabulary, one policy boundary, one paper broker, one persistence trail, and explicit separation between integrated, paper-only, external, experimental, and live-blocked components. “All-in-one” describes the unified control surface and audit model; it does not mean unverified third-party signals are silently promoted to execution.

## Component coverage

| Domain | Canonical implementation | Surface | Status | Safety boundary |
|---|---|---|---|---|
| Market data and venue events | `server/botContracts.ts`, `server/shadowAdapters.ts`, `server/paperEngine.ts` | Overview, shadow feed, Signal Room | Integrated/paper/shadow | Normalize provenance, prices, timestamps, and quality before promotion |
| Alfa Quant hypotheses | Paper signal/evidence layers in `server/paperEngine.ts` | Signal Room evidence stack | Paper-only | Replay and calibration required |
| MD90 Fusion | Paper signal score/confidence and evidence layers | Primary signal and evidence stack | Paper-only | Cannot bypass risk policy |
| Cryptoiz / Solana DEX | External shadow observation contract | Shadow feed, market map, news provenance | External/pending | No wallet or order route |
| Dynamic Execution | External shadow signal contract | Shadow feed and system map | External/pending | Not an execution authority |
| Crypto, FX, and gold coverage | Canonical signal and instrument metadata | Watchlist and market map | Paper/shadow | Venue/live credentials absent |
| Replay and backtest | Deterministic replay prices/equity curve | Replay, chart, Signal Room | Integrated | Fees, spread, slippage, partial fill, and idempotency are explicit |
| Paper broker | `server/paperBroker.ts` | Order Tape, positions, risk | Integrated | No network order path |
| Risk policy | `evaluatePaperRisk` and risk checks | Risk Gate, Signal Room | Integrated | Fail closed on exposure, loss, drawdown, freshness, and live approval |
| Persistence | `server/paperPersistence.ts`, Drizzle schema | History/audit backend | Integrated | User-scoped sessions, signals, orders, fills, positions, journal, equity, shadow/news |
| News intelligence | `server/shadowAdapters.ts`, freshness classifier, `intel.news` | News Intelligence | Shadow | FRESH/STALE and SHADOW/PENDING_REVIEW are visible |
| AI/LLM explanation | Evidence-derived note and documented boundary | AI note, protocol | Experimental | Explanation only; never order authority |
| Open-source patterns | `OPEN_SOURCE_AUDIT.md`, `OPEN_SOURCE_DEEP_AUDIT.md` | Integration matrix/docs | Reference/isolated | No blind cloning; license and security review required |
| 24/7 operations | `LIVE_24_7_READINESS.md` | System map/runbook | Paper-only/planned | Heartbeat, reconnect, monitoring, reconciliation, backup, kill switch |
| Live venues | Explicitly disabled | Locked mode and system map | Live-blocked | Requires separate approval, credential isolation, reconciliation, and soak tests |

## Route and test coverage

The public routes expose read-only paper overview, shadow observations, and news intelligence; authenticated `paper.ingest` is the protected persistence entry point. Test coverage includes deterministic broker behavior, risk limits, full-history persistence with a fake DB, authenticated router scope, anonymous rejection, public shadow/news boundaries, freshness expiry, bilingual labels, and bot execution boundaries.

## Final non-claims

This version does not claim guaranteed returns, superior profitability, verified third-party performance, or live execution. Video references and external websites are product/UX inputs only. Any future live-restricted stage requires new evidence and explicit approval; it is not enabled by this checkpoint.
