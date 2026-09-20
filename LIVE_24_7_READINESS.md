# 24/7 operating readiness

## Stage policy

`PAPER` is deterministic replay with simulated fills. `SHADOW` ingests external observations and compares expected versus observed outcomes without orders. `LIVE-RESTRICTED` is an explicitly approved stage with venue-scoped credentials, hard exposure caps, and an immediate kill switch. No stage implies profitability.

## Current status

Per 23 Agustus 2026, md90_SuperlayerAi berada pada **PAPER/SHADOW only**. TypeScript, 21 automated tests, production build, responsive screenshots, dan keyboard-focus audit lulus. Authenticated browser E2E masih pending karena preview session belum memiliki OAuth cookie; test authenticated-router dan fake-DB persistence memvalidasi kontrak, tetapi tidak menggantikan penulisan database dari browser yang benar-benar login. Cryptoiz dan Dynamic Execution tetap berstatus shadow/pending review tanpa order authority.

## Gate ledger

| Gate | Evidence | Status |
|---|---|---|
| Deterministic paper/replay | Paper engine dan broker tests | PASS |
| Risk and live lock | Fail-closed boundary dan live-blocked route tests | PASS |
| Full-history persistence contract | Fake-DB persistence dan authenticated router tests | PASS / browser E2E pending |
| Shadow/news freshness | Fresh/stale/expiry tests dan status UI | PASS |
| Responsive and keyboard UX | Desktop/mobile screenshots dan focus audits | PASS |
| Real authenticated database E2E | Sesi browser OAuth nyata diperlukan | PENDING |
| External source accuracy certification | Shadow soak dan replay comparison diperlukan | PENDING |
| Restricted live approval | Credential isolation, reconciliation, kill switch, operator approval | LOCKED |

## Required controls

| Control | Required behavior | Current status |
|---|---|---|
| Heartbeat | Record adapter liveness, latency, last event, and stale threshold | UI/contract foundation; continuous worker pending |
| Reconnect | Exponential backoff, bounded retries, circuit breaker, resync from checkpoint | Design required before live |
| Reconciliation | Compare internal orders/fills/positions with venue state; halt on mismatch | Paper-only currently |
| Persistence | UTC event history for signals, snapshots, orders, fills, positions, risk, journal, shadow, news | Database schema and mapper present |
| Alerting | Stale data, risk breach, disconnect, fill mismatch, drawdown, and kill-switch alerts | Alert delivery pending |
| Backup | Scheduled database backup and restore drill with retention policy | Operational setup pending |
| Kill switch | Venue-level cancel/flatten control with RBAC and confirmation | Live route remains blocked |
| Promotion | Paper → shadow → live-restricted only after out-of-sample and forward validation | Approval process pending |

## Non-negotiable live gates

Before live-restricted operation, the system must pass authenticated E2E persistence tests, multi-session replay comparison, failure injection, stale/reconnect simulation, fill reconciliation, fee/slippage validation, access-control review, credential rotation drill, backup restore drill, and a signed human approval. A 24/7 process must run on persistent infrastructure with monitored logs; a serverless preview alone is not an adequate trading runtime.
