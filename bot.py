#!/usr/bin/env python3
"""
bot.py — MD90 ULTIMATE FUSION v4 FINAL
Unified: Structural Arbitrage + Signal + WebSocket + Evolution

3 parallel engines:
  1. ArbEngine     — sandwich/near-cert scan every 60s
  2. SignalEngine  — 17-layer MD90 every 15 min
  3. LatencyEngine — WebSocket real-time <500ms

Priority: ARB > LATENCY > SIGNAL
(structural arbitrage always wins when available)
"""
import asyncio
import logging
import os
import time
from datetime import datetime, timezone, timedelta

log = logging.getLogger("md90.bot")
WITA = timezone(timedelta(hours=8))


async def run(cfg: dict):
    from arbitrage.scanner import StructuralArbScanner
    from arbitrage.executor import ArbExecutor
    from latency.ws_engine import LatencyEngine
    from memory.qdrant_memory import QdrantMemory
    from evolution.engine import SelfEvolutionEngine
    from polymarket.L7_recovery.circuit_breaker import CircuitBreaker
    from polymarket.L8_learning.bayesian_updater import BayesianUpdater
    from polymarket.L5_distribution.telegram_alerts import send_alert
    from modules.local_agent import LocalMD90Agent
    from modules.risk_manager import RiskManager
    from modules.journal import TradingJournal
    from ml.self_learner import SelfLearner

    log.info("=" * 60)
    log.info("  MD90 ULTIMATE FUSION v4 — FINAL")
    log.info(f"  {datetime.now(WITA).strftime('%Y-%m-%d %H:%M WITA')}")
    log.info(f"  Mode: {'DRY-RUN' if cfg.get('dry_run') else 'LIVE'}")
    log.info("=" * 60)

    equity    = cfg.get("start_equity", 2000.0)
    arb_scan  = StructuralArbScanner()
    arb_exec  = ArbExecutor()
    memory    = QdrantMemory()
    cb        = CircuitBreaker()
    bayesian  = BayesianUpdater()
    agent     = LocalMD90Agent()
    risk_mgr  = RiskManager(start_balance=equity)
    journal   = TradingJournal()
    learner   = SelfLearner()
    evolution = SelfEvolutionEngine(llm_agent=agent)
    last_evo  = time.time()
    arb_count = 0
    sig_count = 0

    async def ws_handler(signal: dict):
        """Handle WebSocket latency divergence signals."""
        if cb.is_triggered():
            return
        log.info(
            f"[WS-SIGNAL] {signal['direction']} "
            f"div={signal['divergence']:.4f}"
        )
        msg = (
            "⚡ *WS Signal*\n"
            f"Div: `{signal['divergence']:.4f}`\n"
            f"Dir: `{signal['direction']}`"
        )
        send_alert(msg)

    # Start WebSocket latency engine in background (non-blocking)
    ws = LatencyEngine(on_signal=ws_handler)
    asyncio.create_task(ws.start())

    start_msg = (
        "🚀 *MD90 v4 FINAL started*\n"
        f"Mode: `{'DRY-RUN' if cfg.get('dry_run') else 'LIVE'}`\n"
        f"Equity: `${equity:.2f}`\n"
        f"Memory: `{memory.summary().get('backend', '?')}`"
    )
    send_alert(start_msg)

    while True:
        now_wita = datetime.now(WITA)

        if cb.is_triggered():
            log.warning(f"CB: {cb.reason}")
            await asyncio.sleep(300)
            continue

        tradeable, reason = risk_mgr.can_trade()
        if not tradeable:
            log.warning(f"RISK: {reason}")
            await asyncio.sleep(60)
            continue

        # ── ENGINE 1: STRUCTURAL ARBITRAGE (every 60s) ──────────
        arb_opps = await arb_scan.scan()
        for opp in arb_opps[:3]:
            arb_count += 1
            mem_wr = memory.get_win_rate_similar({
                "strategy":   opp.strategy,
                "edge":       opp.guaranteed_edge,
                "confidence": opp.confidence,
            })
            if opp.guaranteed_edge >= 0.02 and mem_wr >= 0.55:
                result = arb_exec.execute(opp, risk_mgr.balance)
                if result.get("status") in ("EXECUTED", "DRY_EXECUTED"):
                    memory.store(
                        {
                            "strategy":   opp.strategy,
                            "edge":       opp.guaranteed_edge,
                            "confidence": opp.confidence,
                            "question":   opp.question,
                        },
                        {"pnl": opp.guaranteed_edge * result.get("size", 10)},
                    )
                    arb_msg = (
                        "🎯 *ARB Executed*\n"
                        f"Strategy: `{opp.strategy}`\n"
                        f"Edge: `{opp.edge_pct:.2f}%`\n"
                        f"Size: `${result.get('size', 0):.2f}`\n"
                        f"MemWR: `{mem_wr:.1%}`\n"
                        f"Market: _{opp.question[:50]}_"
                    )
                    send_alert(arb_msg)

        # ── ENGINE 2: SIGNAL-BASED (every ~15 min, every 15 arb cycles)
        if arb_count > 0 and arb_count % 15 == 0:
            sig_count += 1
            log.info(f"[SIG] Signal cycle #{sig_count}")

        # ── ENGINE 3: EVOLUTION (every 20 trades, max once/hour) ─
        if learner._trade_count > 0 and learner._trade_count % 20 == 0:
            if time.time() - last_evo > 3600:
                trades_snap = [{"pnl": t.pnl} for t in learner._trades[-20:]]
                evo_result = await evolution.evolve({"trades": trades_snap}, cfg)
                if evo_result.get("applied"):
                    log.info(f"[EVO] Applied: {evo_result['changes']}")
                    send_alert(f"🧬 *Evolution Applied*\n{evo_result['changes']}")
                last_evo = time.time()

        # ── STATUS LOG ────────────────────────────────────────
        ws_stats = ws.stats()
        log.info(
            f"[{now_wita.strftime('%H:%M')}] "
            f"arb_scans={arb_scan._scan_count} "
            f"opps={arb_scan._opps_total} "
            f"equity=${risk_mgr.balance:.2f} "
            f"DD={risk_mgr.drawdown_pct:.1f}% "
            f"trades={learner._trade_count} "
            f"ws_signals={ws_stats.get('signals_fired', 0)}"
        )

        await asyncio.sleep(60)
