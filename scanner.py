"""
arbitrage/scanner.py — Structural Arbitrage Scanner
Strategy 1: YES+NO Sandwich  (combined < 0.97 = guaranteed profit)
Strategy 2: Near-Certainty   (YES > 0.93, buy limit at 0.985)
Source: $40M extracted from Polymarket 2024-2025 using these methods
"""
import asyncio, logging, time, json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Tuple
import aiohttp

log = logging.getLogger("MD90.Arb")
WITA = timezone(timedelta(hours=8))

GAMMA_BASE       = "https://gamma-api.polymarket.com"
CLOB_BASE        = "https://clob.polymarket.com"
YES_NO_MAX_COMB  = 0.97
NEAR_CERT_MIN    = 0.93
NEAR_CERT_LIMIT  = 0.985
MIN_LIQUIDITY    = 3000.0
MIN_VOLUME       = 5000.0


@dataclass
class ArbOpportunity:
    strategy:        str
    market_id:       str
    question:        str
    yes_token_id:    str
    no_token_id:     str
    yes_price:       float
    no_price:        float
    combined:        float
    guaranteed_edge: float
    edge_pct:        float
    volume:          float
    liquidity:       float
    end_date:        str
    confidence:      float
    max_size_usd:    float
    action:          str
    limit_price:     float
    expires_hrs:     float
    score:           float
    found_at: str = field(default_factory=lambda: datetime.now(WITA).isoformat())

    def to_dict(self) -> dict:
        return {**self.__dict__}


class StructuralArbScanner:
    def __init__(self, min_liq: float = MIN_LIQUIDITY, min_vol: float = MIN_VOLUME):
        self.min_liq = min_liq
        self.min_vol = min_vol
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers = {"User-Agent": "MD90-Arb/4.0", "Accept": "application/json",
                          "Origin": "https://polymarket.com"}
        self._scan_count = 0
        self._opps_total = 0

    async def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._headers, timeout=aiohttp.ClientTimeout(total=12))
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_markets(self, limit: int = 100) -> List[Dict]:
        try:
            s = await self._sess()
            async with s.get(f"{GAMMA_BASE}/markets",
                              params={"active": "true", "closed": "false", "limit": limit}) as r:
                if r.status != 200:
                    return []
                data = await r.json(content_type=None)
                mkts = data if isinstance(data, list) else []
                mkts.sort(key=lambda m: float(m.get("volume", 0) or 0), reverse=True)
                return mkts
        except Exception as e:
            log.error(f"fetch_markets: {e}")
            return []

    async def get_prices(self, yes_tid: str, no_tid: str) -> Tuple[float, float]:
        s = await self._sess()
        yes_p = no_p = 0.5
        for tid, is_yes in [(yes_tid, True), (no_tid, False)]:
            if not tid:
                continue
            try:
                async with s.get(f"{CLOB_BASE}/midpoint", params={"token_id": tid}) as r:
                    if r.status == 200:
                        d = await r.json(content_type=None)
                        p = float(d.get("mid", 0.5) or 0.5)
                        if is_yes:
                            yes_p = p
                        else:
                            no_p = p
            except Exception:
                pass
            await asyncio.sleep(0.05)
        return yes_p, no_p

    @staticmethod
    def token_ids(market: dict) -> Tuple[str, str]:
        ids = market.get("clobTokenIds", [])
        if isinstance(ids, str):
            try:
                ids = json.loads(ids)
            except Exception:
                return "", ""
        return (str(ids[0]), str(ids[1])) if isinstance(ids, list) and len(ids) >= 2 else ("", "")

    @staticmethod
    def est_hours(market: dict) -> float:
        end = market.get("endDate") or market.get("end_date_iso", "")
        try:
            from datetime import datetime as DT
            dt = DT.fromisoformat(str(end).replace("Z", "+00:00"))
            return max(0.0, round((dt - datetime.now(timezone.utc)).total_seconds() / 3600, 1))
        except Exception:
            return 24.0

    # ── STRATEGY 1: SANDWICH ──────────────────────────────────────

    def _sandwich(self, m: dict, yes_p: float, no_p: float) -> Optional[ArbOpportunity]:
        combined = yes_p + no_p
        if combined >= YES_NO_MAX_COMB:
            return None
        edge = 1.0 - combined
        vol  = float(m.get("volume", 0) or 0)
        liq  = float(m.get("liquidity", 0) or 0)
        ytid, ntid = self.token_ids(m)
        return ArbOpportunity(
            strategy="SANDWICH",
            market_id=str(m.get("conditionId") or m.get("id", "")),
            question=m.get("question", ""), yes_token_id=ytid, no_token_id=ntid,
            yes_price=yes_p, no_price=no_p, combined=round(combined, 4),
            guaranteed_edge=round(edge, 4), edge_pct=round(edge * 100, 2),
            volume=vol, liquidity=liq, end_date=str(m.get("endDate", "")),
            confidence=min(0.99, 0.80 + edge * 2), max_size_usd=min(liq * 0.10, 200.0),
            action="BUY_BOTH", limit_price=combined,
            expires_hrs=self.est_hours(m),
            score=round(edge * 10 * min(vol / 50000, 1.0) * min(liq / 10000, 1.0), 4),
        )

    # ── STRATEGY 2: NEAR-CERTAINTY ───────────────────────────────

    def _near_cert(self, m: dict, yes_p: float, no_p: float) -> Optional[ArbOpportunity]:
        for price, action in [(yes_p, "BUY_YES"), (no_p, "BUY_NO")]:
            if price >= NEAR_CERT_MIN:
                edge = 1.0 - NEAR_CERT_LIMIT
                vol  = float(m.get("volume", 0) or 0)
                liq  = float(m.get("liquidity", 0) or 0)
                ytid, ntid = self.token_ids(m)
                return ArbOpportunity(
                    strategy="NEAR_CERT",
                    market_id=str(m.get("conditionId") or m.get("id", "")),
                    question=m.get("question", ""), yes_token_id=ytid, no_token_id=ntid,
                    yes_price=yes_p, no_price=no_p, combined=round(yes_p + no_p, 4),
                    guaranteed_edge=round(edge, 4), edge_pct=round(edge * 100, 2),
                    volume=vol, liquidity=liq, end_date=str(m.get("endDate", "")),
                    confidence=min(0.97, price * 1.03), max_size_usd=min(liq * 0.15, 500.0),
                    action=action, limit_price=NEAR_CERT_LIMIT,
                    expires_hrs=self.est_hours(m),
                    score=round(price * min(vol / 100000, 1.0) * 10, 4),
                )
        return None

    # ── MASTER SCAN ───────────────────────────────────────────────

    async def scan(self) -> List[ArbOpportunity]:
        self._scan_count += 1
        t0 = time.time()
        log.info(f"[ARB] Scan #{self._scan_count}...")
        markets = await self.fetch_markets(100)
        opps: List[ArbOpportunity] = []
        for m in markets:
            if float(m.get("volume", 0) or 0) < self.min_vol:
                continue
            if float(m.get("liquidity", 0) or 0) < self.min_liq:
                continue
            ytid, ntid = self.token_ids(m)
            if not ytid:
                continue
            yes_p, no_p = await self.get_prices(ytid, ntid)
            for fn in [self._sandwich, self._near_cert]:
                opp = fn(m, yes_p, no_p)
                if opp:
                    opps.append(opp)
        opps.sort(key=lambda o: o.score, reverse=True)
        self._opps_total += len(opps)
        log.info(f"[ARB] Done {time.time()-t0:.1f}s | mkts={len(markets)} opps={len(opps)}")
        if opps:
            b = opps[0]
            log.info(f"[ARB] BEST {b.strategy} edge={b.edge_pct:.2f}% "
                     f"${b.max_size_usd:.0f} '{b.question[:50]}'")
        return opps

    def get_stats(self) -> dict:
        return {
            "scan_count": self._scan_count,
            "opps_found": self._opps_total,
            "last_scan":  datetime.now(WITA).isoformat(),
        }
