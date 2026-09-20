"""
claude_agent/agent.py
MD90 Claude Agent — Final Arbiter
Role: LLM layer for contextual reasoning, news sentiment, Bayesian
probability recalibration, dynamic strategy adjustment.
"Intelligence wick" yang menghubungkan HMM + MiroFish dengan real-world.

Uses Anthropic API (claude-sonnet-4-6).
Temperature: 0.1 (deterministic outputs).
Output: strict JSON schema.
"""
import os, json, logging
from datetime import datetime, timezone, timedelta
from typing import Optional

log = logging.getLogger(__name__)
WITA = timezone(timedelta(hours=8))


class ClaudeAgent:
    """
    Claude as final arbiter for trading decisions.
    Combines: HMM regime + MiroFish graph + MD90 signal + Bayesian prior + news.
    """

    SYSTEM_PROMPT = """You are Claude Quant Agent inside MD90 Ultimate Fusion Bot.

Role: Provide deterministic trading decisions for Polymarket prediction markets.

Context you receive:
- MD90 Signal: 17-layer ICT/SMC fusion (BUY/SELL/NEUTRAL, score 0-1, confidence 0-100%)
- HMM Regime: statistical regime (TRENDING_UP/DOWN, VOLATILE, SIDEWAYS, BREAKOUT)
- MiroFish Graph: network cluster score and conviction level
- Bayesian Prior: historical win rate for this market type
- Market data: question, current probability, volume, liquidity
- News summary (if available)

Output MUST be valid JSON with this exact schema:
{
  "action": "EXECUTE" | "MONITOR" | "FLATTEN" | "INCREASE_SIZE",
  "side": "YES" | "NO" | "NONE",
  "confidence": 0-100,
  "edge_strength": 0-100,
  "entry_price": float,
  "sl_level": float,
  "tp_level": float,
  "risk_warning": "string or null",
  "reasoning": "1-2 sentences max"
}

Rules:
- EXECUTE only if edge_strength > 60 AND confidence > 70 AND no critical risk warning
- FLATTEN if regime transitions or news contradicts signal
- Temperature 0.1 — be deterministic, not creative"""

    def __init__(self, model:str="claude-sonnet-4-6"):
        self.model   = model
        self._client = None
        api_key = os.getenv("ANTHROPIC_API_KEY","")
        if not api_key:
            log.warning("ANTHROPIC_API_KEY not set — Claude Agent disabled")
            return
        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
            log.info(f"Claude Agent initialized: {model}")
        except ImportError:
            log.warning("anthropic package not installed — pip install anthropic")

    def _build_prompt(self, ctx:dict) -> str:
        now = datetime.now(WITA).strftime("%Y-%m-%d %H:%M WITA")
        md90 = ctx.get("md90_signal",{})
        return f"""
Current Time: {now}

MD90 SIGNAL:
  Direction: {md90.get('direction_str','NEUTRAL')}
  Fusion Score: {md90.get('fusion_score',0):.3f}
  Confidence: {md90.get('confidence',0):.1f}%
  Status: {md90.get('execution_status','ABORT')}
  Gates: G1={md90.get('gate1',False)} G2={md90.get('gate2',False)} G3={md90.get('gate3',False)}

HMM REGIME: {ctx.get('regime','UNDEFINED')} | Persistence: {ctx.get('persistence',0):.2f}
MIROFISH GRAPH: Clusters={ctx.get('clusters',0)} | Score={ctx.get('network_score',0):.2f}
BAYESIAN PRIOR: {ctx.get('bayesian_prior',0.5):.3f} | Trades={ctx.get('total_trades',0)}

MARKET:
  Question: {ctx.get('question','N/A')}
  Current Prob: {ctx.get('market_prob',0.5):.3f} ({ctx.get('market_prob',0.5)*100:.1f}%)
  Volume: ${ctx.get('volume',0):,.0f}
  Liquidity: ${ctx.get('liquidity',0):,.0f}
  Our Edge: {ctx.get('edge',0):.4f} ({ctx.get('edge_pct',0):.1f}%)

NEWS: {ctx.get('news','No recent news available')}

RECENT PERFORMANCE: {ctx.get('recent_pnl',0):+.2f} USDC last 5 trades

Task: Analyze this setup and provide trading decision as JSON.
"""

    def get_decision(self, context:dict) -> dict:
        """Get Claude's final trading decision. Falls back to rule-based if API unavailable."""
        if not self._client:
            return self._rule_based_fallback(context)

        try:
            resp = self._client.messages.create(
                model      = self.model,
                max_tokens = 800,
                temperature= 0.1,  # deterministic
                system     = self.SYSTEM_PROMPT,
                messages   = [{"role":"user","content":self._build_prompt(context)}]
            )
            text = resp.content[0].text.strip()
            # Strip markdown if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"): text = text[4:]
            decision = json.loads(text)
            log.info(f"Claude: {decision.get('action')} conf={decision.get('confidence')}%")
            return decision
        except json.JSONDecodeError as e:
            log.error(f"Claude JSON parse error: {e}")
            return self._rule_based_fallback(context)
        except Exception as e:
            log.error(f"Claude API error: {e}")
            return {"action":"MONITOR","confidence":40,"reason":f"API error: {e}"}

    def _rule_based_fallback(self, ctx:dict) -> dict:
        """Rule-based fallback when Claude API unavailable."""
        md90    = ctx.get("md90_signal",{})
        edge    = ctx.get("edge",0)
        fs      = md90.get("fusion_score",0)
        conf    = md90.get("confidence",0)
        status  = md90.get("execution_status","ABORT")
        bayesian= ctx.get("bayesian_prior",0.5)

        if status == "ABORT" or fs < 0.55:
            return {"action":"MONITOR","side":"NONE","confidence":35,
                    "edge_strength":int(edge*100),"entry_price":ctx.get("market_prob",0.5),
                    "sl_level":0,"tp_level":0,"risk_warning":"Fusion ABORT",
                    "reasoning":"Signal below threshold"}

        if status == "ALL-IN" and conf >= 75 and edge > 0.06 and bayesian > 0.55:
            side = "YES" if md90.get("direction",0) == 1 else "NO"
            return {"action":"EXECUTE","side":side,"confidence":int(conf),
                    "edge_strength":int(abs(edge)*100),
                    "entry_price":ctx.get("market_prob",0.5),
                    "sl_level":0,"tp_level":0,"risk_warning":None,
                    "reasoning":"ALL-IN + edge + Bayesian confirms"}

        return {"action":"MONITOR","side":"NONE","confidence":int(conf*0.7),
                "edge_strength":int(abs(edge)*100),"entry_price":ctx.get("market_prob",0.5),
                "sl_level":0,"tp_level":0,"risk_warning":None,
                "reasoning":"WAITING — insufficient confluence"}
