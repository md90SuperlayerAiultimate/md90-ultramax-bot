# Deep open-source audit — md90_superlayerAi

Dokumen ini melengkapi screening 100 repo. Kebijakan produk adalah **tidak meng-clone dan memasukkan 100 repo secara membabi buta**. Hanya komponen yang lolos kontrak data, lisensi, security review, dependency pinning, reproducibility, dan paper/shadow validation yang boleh masuk runtime.

| Repository | Keputusan | Peran | Lisensi/maintenance note | Security/integration boundary |
|---|---|---|---|---|
| [CCXT](https://github.com/ccxt/ccxt) | USE candidate | Exchange REST/WebSocket adapter | Verifikasi lisensi dan pin versi pada setiap release; adapter eksternal tidak menjadi risk authority | Credential vault only; read-only default; rate-limit, nonce, timeout, reconciliation, and venue capability mapping wajib |
| [Freqtrade](https://github.com/freqtrade/freqtrade) | FORK candidate | MVP backtest, dry-run, strategy lifecycle | Gunakan sebagai controlled derivative; jangan membawa asumsi konfigurasi ke live | Paper broker dan md90 policy harus menjadi satu-satunya order boundary; disable arbitrary strategy mutation |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | USE candidate | Event-driven research/simulation/order-book semantics | Pin release dan audit native dependencies; cocok untuk tahap research-to-live setelah validation | Adapter harus memakai canonical event schema; live adapter tetap disabled sampai gate terpenuhi |
| [VectorBT](https://github.com/polakowo/vectorbt) | USE candidate | Vectorized research and parameter analysis | Research-only dependency; record version and environment for reproducibility | Tidak boleh dipakai sebagai live execution engine; guard against look-ahead and data leakage |
| [Backtrader](https://github.com/mementum/backtrader) | USE candidate | Alternative research/backtest engine | Use only if dataset semantics are normalized and license is confirmed for distribution | No direct exchange credentials; compare outputs against md90 replay engine |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | IDEAS | LLM research/explanation orchestration | Reference architecture only; inspect model/provider terms before reuse | No order authority; prompt/output provenance, deterministic fallback, and policy gate required |
| [Polymarket CLI/agents](https://github.com/Polymarket) | IDEAS | Venue-specific market semantics | Separate venue domain from crypto/FX; license varies per repository | Never map YES/NO condition IDs into Binance/Solana instrument schema without explicit adapter |
| [Nango](https://github.com/NangoHQ/nango) | IDEAS | OAuth/integration patterns | License and deployment model must be verified before production use | Secrets and refresh tokens must remain server-side; not part of trading decision path |

## Decision rule

`USE` means a candidate can be integrated only through a reviewed adapter. `FORK` means the code must be isolated in a controlled branch with md90 contracts. `IDEAS` means conceptual reference only. `REJECT` means unavailable, out of scope, incompatible, or unsafe. No repository receives exchange or wallet credentials automatically.

## Required evidence before production

Each selected dependency needs a pinned commit/release, license record, dependency vulnerability scan, static analysis, unit/contract tests, replay comparison, paper/shadow soak test, failure injection, rollback path, and explicit owner approval. A README or star count is not evidence of trading edge.

## Deep review evidence — 23 Aug 2026

The official repositories were reviewed for architecture, execution boundaries, persistence, testability, and licensing. CCXT describes a unified API for public/private REST and WebSocket exchange access and is MIT-licensed; its correct md90 role is a server-side venue adapter with read-only defaults, normalized timestamps, rate-limit handling, nonce/timeout controls, and reconciliation. It must never become the risk authority or receive unrestricted credentials. [1] [2]

Freqtrade documents dry-run, backtesting, persistence, exchange-specific configuration, and a separation between stable and development branches. It is useful as a controlled research/paper reference, but its GPL-3.0 licensing and strategy/configuration assumptions require isolation rather than direct embedding in the TypeScript runtime. The md90 policy gate and deterministic PaperBroker remain authoritative. [3]

NautilusTrader presents a Rust-native, event-driven, multi-asset and multi-venue architecture with deterministic simulation semantics, modular adapters, and research-to-live parity. Its repository is LGPL-3.0-licensed and includes explicit security/supply-chain artifacts. It is the strongest architectural reference for a future research engine, but its native runtime and license obligations make it a later isolated service, not a dependency to add casually to this web application. [4]

VectorBT is suitable for large-scale vectorized research and parameter analysis, but it must remain research-only in md90. Any adoption requires explicit controls for look-ahead bias, leakage, data versioning, and comparison against the canonical replay engine. It cannot be treated as an execution engine or as evidence of future profitability. [5]

| Candidate | Verified strength | md90 decision | Immediate action |
|---|---|---|---|
| CCXT | Broad unified exchange API; MIT | USE via adapter | Define read-only market-data contract first; keep order path disabled |
| Freqtrade | Dry-run, backtest, persistence, strategy lifecycle; GPL-3.0 | FORK/reference isolation | Borrow test ideas and operational patterns; do not embed unreviewed code |
| NautilusTrader | Deterministic event-driven multi-asset engine; LGPL-3.0 | USE later as isolated research service | Map event model to canonical schema; run parity and supply-chain review |
| VectorBT | High-throughput vectorized research | USE research-only | Add leakage/look-ahead controls and replay comparison |

## Per-candidate data model and observability review

| Candidate | Data model fit | Observability fit | Integration conclusion |
|---|---|---|---|
| CCXT | Exchange-specific responses are normalized into unified tickers, order books, trades, balances, and orders; venue capability differences remain material. | Requires md90-owned request IDs, latency, rate-limit, nonce, raw-response hash, error class, and reconciliation events because the library is an adapter, not an audit ledger. | Use only behind a canonical venue-event mapper and server-side credential boundary. |
| Freqtrade | Strategy, trade, pairlist, wallet, order, and persistence concepts are useful for dry-run, but its configuration and Python/SQLite assumptions do not match the md90 canonical MySQL schema. | Strong operational surface through bot status, Telegram/WebUI, logs, and backtest reports, but md90 must add immutable provenance, policy decisions, and user-scoped audit events. | Keep as isolated reference/FORK candidate; translate concepts into md90 contracts rather than embedding runtime. |
| NautilusTrader | Rich typed instruments, quotes, trades, bars, orders, positions, accounts, events, and cache semantics fit an event-driven research plane; native identifiers and nanosecond time need explicit mapping to md90 UTC millisecond persistence. | Strong event bus, logs, reports, reconciliation, and deterministic replay concepts; md90 would need an adapter telemetry envelope and correlation IDs at the service boundary. | Best later isolated research/simulation service; do not mix its live engine into the current web runtime. |
| VectorBT | Array/DataFrame-oriented signals and portfolio outputs are excellent for research matrices but are not an order/event ledger and can hide execution sequencing if used carelessly. | Notebook/plot/report observability is useful for research, but md90 needs dataset fingerprints, parameter manifests, run IDs, leakage checks, and replay diffs. | Research-only adapter with no credentials and no execution authority. |

### Patterns adopted without copying source code

The platform adopts **concepts**, not wholesale repository code: venue-neutral normalized events, deterministic replay, dry-run separation, explicit order lifecycle states, reconciliation, provenance, pinned dependencies, failure injection, and research-to-paper parity tests. The platform does not copy exchange credentials, arbitrary strategy mutation, unreviewed live adapters, or performance claims from any repository. All live paths remain blocked until separate credentials, approvals, reconciliation, kill-switch, and soak-test gates exist.

### References

[1]: https://github.com/ccxt/ccxt "CCXT official repository"
[2]: https://github.com/ccxt/ccxt/wiki/manual "CCXT manual"
[3]: https://github.com/freqtrade/freqtrade "Freqtrade official repository"
[4]: https://github.com/nautechsystems/nautilus_trader "NautilusTrader official repository"
[5]: https://github.com/polakowo/vectorbt "VectorBT official repository"
