"""
MD90 — Dynamic Risk Calculator
Port dari MQL5 Section 16 CalculateDynamicRisk()

Formula:
  final_risk = base_risk
             × session_multiplier
             × regime_multiplier
             × consecutive_adj
             × drawdown_adj
  clamped ke [MIN_RISK, MAX_RISK]
"""
from dataclasses import dataclass

from .session_manager import SessionState, TradingSession, SESSION_RISK_MULT
from .regime_engine   import RegimeState, MarketRegime, REGIME_RISK_MULT


BASE_RISK    = 0.01    # 1%
MAX_RISK     = 0.03    # 3%
MIN_RISK     = 0.003   # 0.3%
MAX_DAILY_LOSS_PCT = 10.0
MAX_DRAWDOWN_PCT   = 25.0
MAX_DAILY_TRADES   = 10
CONSECUTIVE_LOSS_LIMIT = 3
CONSECUTIVE_WIN_LIMIT  = 5


@dataclass
class RiskState:
    final_risk_pct:       float = 1.0     # percent (0-100 scale not 0-1)
    session_mult:         float = 1.0
    regime_mult:          float = 1.0
    consecutive_adj:      float = 1.0
    drawdown_adj:         float = 1.0
    trading_allowed:      bool  = True
    block_reason:         str   = ""
    # Counters
    trades_today:         int   = 0
    consecutive_losses:   int   = 0
    consecutive_wins:     int   = 0
    daily_pnl:            float = 0.0
    current_drawdown_pct: float = 0.0


class DynamicRiskCalculator:
    """
    Menghitung risk % per trade berdasarkan:
    - Session saat ini
    - Regime saat ini
    - Consecutive win/loss
    - Current drawdown
    - Daily trade/loss limits
    """

    def __init__(self,
                 base_risk:   float = BASE_RISK,
                 max_risk:    float = MAX_RISK,
                 min_risk:    float = MIN_RISK):
        self.base  = base_risk
        self.max   = max_risk
        self.min   = min_risk

        # Live counters
        self._consecutive_losses = 0
        self._consecutive_wins   = 0
        self._trades_today       = 0
        self._daily_pnl          = 0.0
        self._equity_peak        = 0.0
        self._current_equity     = 0.0

    # ── Update live state ────────────────────────────────────────────
    def update_equity(self, equity: float):
        if equity > self._equity_peak:
            self._equity_peak = equity
        self._current_equity = equity

    def record_trade_result(self, pnl: float):
        """Call setelah setiap trade ditutup"""
        self._daily_pnl  += pnl
        self._trades_today += 1
        if pnl > 0:
            self._consecutive_wins  += 1
            self._consecutive_losses = 0
        else:
            self._consecutive_losses += 1
            self._consecutive_wins   = 0

    def reset_daily(self):
        """Reset daily counters (call saat hari baru)"""
        self._trades_today = 0
        self._daily_pnl    = 0.0

    # ── Core calculation ─────────────────────────────────────────────
    def calculate(self,
                  session: SessionState,
                  regime:  RegimeState,
                  equity:  float = 0.0,
                  balance: float = 0.0) -> RiskState:
        """
        Port of MQL5 CalculateDynamicRisk() + IsTradingAllowed()
        """
        if equity > 0:
            self.update_equity(equity)

        rs = RiskState(
            trades_today       = self._trades_today,
            consecutive_losses = self._consecutive_losses,
            consecutive_wins   = self._consecutive_wins,
            daily_pnl          = self._daily_pnl,
        )

        # ── Gate: Weekend / inactive ──────────────────────────────────
        if session.session == TradingSession.WEEKEND:
            rs.trading_allowed = False
            rs.block_reason    = "Weekend — no trading"
            rs.final_risk_pct  = 0.0
            return rs

        if not session.is_active:
            rs.trading_allowed = False
            rs.block_reason    = f"Session {session.name} not active"
            rs.final_risk_pct  = 0.0
            return rs

        # ── Gate: Regime confidence ───────────────────────────────────
        if regime.confidence < 50.0:
            rs.trading_allowed = False
            rs.block_reason    = f"Regime confidence too low: {regime.confidence:.1f}%"
            rs.final_risk_pct  = 0.0
            return rs

        # ── Gate: Daily limits ────────────────────────────────────────
        if self._trades_today >= MAX_DAILY_TRADES:
            rs.trading_allowed = False
            rs.block_reason    = f"Max daily trades reached: {self._trades_today}"
            rs.final_risk_pct  = 0.0
            return rs

        if balance > 0:
            daily_loss_pct = self._daily_pnl / balance * 100
            if daily_loss_pct <= -MAX_DAILY_LOSS_PCT:
                rs.trading_allowed = False
                rs.block_reason    = f"Daily loss limit: {daily_loss_pct:.1f}%"
                rs.final_risk_pct  = 0.0
                return rs

        # ── Gate: Total drawdown ──────────────────────────────────────
        dd_pct = 0.0
        if self._equity_peak > 0 and self._current_equity > 0:
            dd_pct = (self._equity_peak - self._current_equity) / self._equity_peak * 100
        rs.current_drawdown_pct = dd_pct
        if dd_pct >= MAX_DRAWDOWN_PCT:
            rs.trading_allowed = False
            rs.block_reason    = f"Max drawdown reached: {dd_pct:.1f}%"
            rs.final_risk_pct  = 0.0
            return rs

        # ── Dynamic risk calculation ──────────────────────────────────
        risk = self.base

        # Session multiplier
        sm = SESSION_RISK_MULT.get(session.session, 0.5)
        risk *= sm
        rs.session_mult = sm

        # Regime multiplier
        rm = REGIME_RISK_MULT.get(regime.regime, 0.8)
        risk *= rm
        rs.regime_mult = rm

        # Consecutive loss adjustment (port: *0.5 after N losses)
        if self._consecutive_losses >= CONSECUTIVE_LOSS_LIMIT:
            ca = 0.5
        elif self._consecutive_wins >= CONSECUTIVE_WIN_LIMIT:
            ca = 1.2
        else:
            ca = 1.0
        risk *= ca
        rs.consecutive_adj = ca

        # Drawdown-based reduction (port: reduce proportionally)
        if dd_pct > 10.0:
            da = max(1.0 - (dd_pct / MAX_DRAWDOWN_PCT), 0.3)
        else:
            da = 1.0
        risk *= da
        rs.drawdown_adj = da

        # Clamp
        risk = max(self.min, min(self.max, risk))

        rs.final_risk_pct  = round(risk * 100, 3)   # as percent (e.g. 1.5%)
        rs.trading_allowed = True
        return rs
