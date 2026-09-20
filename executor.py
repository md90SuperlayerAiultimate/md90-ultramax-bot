"""
arbitrage/executor.py — Arbitrage Order Executor
Executes sandwich + near-certainty orders via CLOB V2.
Fast path: minimal overhead, direct to CLOB.
"""
import logging, os
from typing import Optional
from arbitrage.scanner import ArbOpportunity

log = logging.getLogger("MD90.Arb.Exec")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


class ArbExecutor:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            try:
                from polymarket.core.polymarket_client import PolyClient
                self._client = PolyClient()
            except Exception as e:
                log.error(f"Client init: {e}")
        return self._client

    def execute(self, opp: ArbOpportunity, equity: float) -> dict:
        size = min(opp.max_size_usd, equity * 0.15)  # max 15% equity per trade
        if size < 5:
            return {"status": "SKIP", "reason": "size<$5"}

        if DRY_RUN:
            log.info(f"[DRY-ARB] {opp.strategy} {opp.action} ${size:.2f} "
                     f"edge={opp.edge_pct:.2f}% '{opp.question[:40]}'")
            return {"status": "DRY_EXECUTED", "strategy": opp.strategy,
                    "action": opp.action, "size": size, "edge": opp.edge_pct}

        c = self._get_client()
        if not c:
            return {"status": "FAIL", "reason": "No client"}

        results = []
        if opp.action == "BUY_BOTH":
            # Sandwich: buy YES + NO simultaneously
            for token_id, side_name in [
                    (opp.yes_token_id, "YES"), (opp.no_token_id, "NO")]:
                if not token_id:
                    continue
                price = opp.yes_price if side_name == "YES" else opp.no_price
                price = max(0.01, min(0.99, price))
                tokens = int(size / price) if price > 0 else 0
                if tokens < 1:
                    continue
                r = c.place_limit_order(token_id, price, tokens, "BUY")
                results.append({"side": side_name, "result": r})
        else:
            token_id = opp.yes_token_id if opp.action == "BUY_YES" else opp.no_token_id
            if not token_id:
                return {"status": "FAIL", "reason": "No token"}
            tokens = int(size / opp.limit_price) if opp.limit_price > 0 else 0
            if tokens < 1:
                return {"status": "FAIL", "reason": "tokens<1"}
            r = c.place_limit_order(token_id, opp.limit_price, tokens, "BUY")
            results.append({"side": opp.action, "result": r})

        success = all("error" not in str(r.get("result", "")) for r in results)
        log.info(f"[ARB-EXEC] {opp.strategy} {'OK' if success else 'FAIL'} "
                 f"${size:.2f} edge={opp.edge_pct:.2f}%")
        return {"status": "EXECUTED" if success else "PARTIAL",
                "strategy": opp.strategy, "size": size, "results": results}
