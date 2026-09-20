# External Source Findings — Direct Review

## Cryptoiz

Direct review of https://cryptoiz.org/Home on 23 Aug 2026 exposed a large public route surface beyond a single landing page. The indexed routes include Alpha Scanner, Divergence Scanner/V2, Phoenix Scanner/V4, Bitcoin Direction, News, Alerts, Token Detail, Token Health, Whale Buys/Pro, Best Coins, Fibo Watchlist, Morning Briefing, Achievement Report, Paper Broker, Auto Trade Admin, Binance Scanner/Metrics, and MCP landing/API-key pages. The public description positions CryptoIZ as an AI-powered smart-money signal platform for Solana DEX, with whale accumulation, divergence, breakout phases, and an MCP server. Several routes appear administrative or account-gated; route visibility alone is not proof that their underlying data or execution is accessible. The first browser rendering also showed a malformed/mostly blank visual state, so stability and authenticated behavior require separate verification.

## Dynamic Execution

Direct review of https://dynamicexecution.id redirected to /signals. The visible product surface includes Dashboard, Signals, Bots, Copy Trading, Outlook, Private Analyst, Live Meeting, Course, wallet connection, VIP/VVIP access, LONG/SHORT and PROFIT/LOSS filters, paginated signal history, TradingView connection, running positions, and market side panels. The visible side panel showed aggregate counters and a sample of recent positions, but the page explicitly requested wallet/subscription access for signals. The visible data should therefore be treated as external reference/shadow evidence, not a canonical source for md90 performance. No live order integration was inferred.

## Implication for md90_SuperlayerAi

The main gap is not only visual polish. The external products expose deeper domain surfaces: scanner families, token/market detail, alerts, membership entitlements, bot/copy-trading concepts, signal history, track records, market outlook, and operational dashboards. md90 currently has the safer evidence-first foundations, but needs substantive screen-level workflows and verified adapters for these domains. Any future adapter must preserve provenance, freshness, access scope, licensing, and PAPER/SHADOW status; no external claim, rating, or performance number should be copied into md90 as validated truth.

## Alpha Scanner follow-up

Direct review of https://cryptoiz.org/AlphaScanner returned a `Session Invalid` state with `Auth session missing!` and prompts to upgrade or log in. The page states CryptoIZ is a data/statistics research tool, not investment advice, and discloses that historical win rate/performance does not guarantee future results. This confirms that scanner implementation details and signal rows are gated in the current public session; md90 must not pretend to have imported them. A permissioned adapter or user-provided export would be required for real shadow ingestion.
