# Video reference product brief

## Product direction

md90_superlayerAi mengambil pola terminal multi-panel dari referensi video: equity curve, order tape, whale/on-chain flow, daily scanner, edge scanner, macro/news, agent state, FSM/state tracker, dan API health. Produk tidak akan menampilkan ROI atau profit sebagai bukti tanpa periode, sample size, benchmark, fees, slippage, funding, dan provenance.

## Features to integrate

| Feature | md90 treatment | Operating mode |
|---|---|---|
| Equity curve | Realized/unrealized split, drawdown, fees, slippage, timestamp | Paper/shadow |
| Order tape | Immutable simulated fills with clientOrderId and fill status | Paper |
| Whale flow | External observation with source, freshness, and confidence | Shadow |
| Macro/news | Source-tagged headline, relevance, sentiment, stale state | Shadow |
| Edge scanner | Candidate ranking with evidence stack and policy result | Paper/shadow |
| Agent brain | Explanation only; no direct order authority | Experimental |
| FSM/state tracker | Explicit state transitions and audit log | Integrated |
| API health | Latency, freshness, reconnect, rate-limit, and error counters | Shadow |

## Live 24/7 policy

The product must progress through paper, shadow, and live-restricted stages. A live-restricted stage requires authenticated approval, bounded exposure, venue-level kill switch, heartbeat/reconnect monitoring, reconciliation, persistent journal, incident alerts, and rollback. The video claims about automatic consistency are treated as unverified marketing until independently reproduced with out-of-sample and forward data.
