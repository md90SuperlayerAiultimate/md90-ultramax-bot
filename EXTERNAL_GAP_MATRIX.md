# External Capability Gap Matrix

## Assessment

Audit langsung menunjukkan bahwa sumber eksternal memiliki **surface area produk** yang lebih luas daripada dashboard md90 saat ini. Perbedaannya terutama berada pada kedalaman workflow dan akses data, bukan sekadar tema visual.

| Capability | Cryptoiz / Dynamic Execution evidence | md90 status | Required treatment |
|---|---|---|---|
| Signal scanners | Alpha, Divergence, Phoenix, Bitcoin Direction, Binance and MA scanners are publicly enumerated by Cryptoiz | Partial: canonical signals and shadow adapters exist | Add scanner registry and provenance per strategy family; keep external values shadow until verified |
| Token / market detail | Cryptoiz exposes Token Detail, Token Health, Best Coins, Whale Buy surfaces | Partial: multi-asset market map and Signal Room | Add evidence drawer with liquidity, freshness, regime, and source lineage |
| Signal history / track record | Dynamic Execution exposes paginated signals with LONG/SHORT and PROFIT/LOSS filters; Cryptoiz lists track-record pages | Partial: paper ledger and demo statistics | Add attribution views that compute outcomes from md90 ledger, never copy external claims |
| Alerts / notifications | Cryptoiz exposes Alerts and news routes; Dynamic Execution exposes notifications | Partial: news freshness and shadow feed | Add alert queue state and acknowledgement audit, no auto-order side effect |
| Bots / copy trading | Dynamic Execution exposes Bots and Copy Trading navigation | Intentionally blocked for live; paper engine only | Add paper strategy templates and approval workflow, not wallet/order execution |
| Outlook / analyst context | Dynamic Execution exposes Outlook and Private Analyst; Cryptoiz exposes Morning Briefing | Partial: News Intelligence and agent state | Add research context panel with confidence, timestamp, and pending-review state |
| Membership / entitlement | Both sources show gated VIP/VVIP or account/wallet surfaces | Not applicable to core trading safety | Represent as external access metadata only; never bypass login or copy gated data |
| MCP / agent integration | Cryptoiz public description and routes mention MCP | Experimental / documented | Keep MCP as a future read-only connector until credential and scope review |

## Product conclusion

The md90 advantage is the safety and audit foundation: canonical data lineage, deterministic paper fills, persistent history, adaptive policy, and live-blocked boundaries. The missing layer is a richer **research operating system** around those primitives: scanner registry, evidence drawer, alert queue, attribution, paper strategy templates, and operational workflow surfaces. These should be built from md90-owned data contracts and verified adapters, not from copied pages or unsupported performance claims.

## Non-negotiable boundary

External pages may be unavailable, gated, unstable, or subject to terms that prohibit automated extraction. Therefore, md90 will not claim that Cryptoiz or Dynamic Execution is integrated merely because its public navigation is visible. Integration requires an explicit adapter contract, provenance, freshness, permission scope, persistence test, and PAPER/SHADOW classification.
