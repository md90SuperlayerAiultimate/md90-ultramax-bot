"""
MD90 — Regime-Specific Strategy Adapter
Port EXACT dari MQL5 MD90_COMPLETE_ANALYSIS Section 18:
  CalculateSidewaysSignal()
  CalculateTrendingSignal()
  CalculateVolatileSignal()
  CalculateBreakoutSignal()
  ApplySignalFilters()

Integrasi: RegimeStrategy dijalankan setelah 17-layer FusionSignal.
Regime-specific score MENAMBAH atau MENGURANGI fusion_score.
"""
from dataclasses import dataclass
from typing import List
import math

from .regime_engine import MarketRegime, RegimeState
from .types import MarketData, FusionSignal, SignalDirection


BUY  = int(SignalDirection.BUY)
SELL = int(SignalDirection.SELL)
NEUT = int(SignalDirection.NEUTRAL)


@dataclass
class RegimeSignal:
    buy_score:   float = 0.0
    sell_score:  float = 0.0
    direction:   int   = 0
    regime_name: str   = "UNDEFINED"
    reason:      str   = ""
    min_score:   float = 60.0


class RegimeStrategyEngine:
    """
    Regime-aware strategy layer.
    Run SETELAH MarketMind FusionSignal — sebagai confirmer / booster.
    Mengembalikan RegimeSignal yang digunakan untuk final gating.
    """
    MIN_SCORE = 60.0   # port dari MQL5 minScore = 60.0

    def analyze(self, md: MarketData, regime: RegimeState) -> RegimeSignal:
        """
        Dispatch ke strategy yang sesuai dengan regime saat ini.
        """
        sig = RegimeSignal(regime_name=regime.name, min_score=self.MIN_SCORE)

        if regime.regime in (MarketRegime.SIDEWAYS, MarketRegime.RANGING):
            self._sideways(md, regime, sig)

        elif regime.regime in (MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN):
            self._trending(md, regime, sig)

        elif regime.regime == MarketRegime.VOLATILE:
            self._volatile(md, regime, sig)

        elif regime.regime == MarketRegime.BREAKOUT:
            self._breakout(md, regime, sig)

        else:
            # TRANSITION / UNDEFINED → neutral, no regime signal
            sig.reason = f"No strategy for regime {regime.name}"
            return sig

        # Apply filters
        self._filters(md, regime, sig)

        # Determine direction
        if sig.buy_score >= self.MIN_SCORE and sig.buy_score > sig.sell_score:
            sig.direction = BUY
        elif sig.sell_score >= self.MIN_SCORE and sig.sell_score > sig.buy_score:
            sig.direction = SELL
        else:
            sig.direction = NEUT

        return sig

    # ── SIDEWAYS (Mean Reversion) ─────────────────────────────────────
    def _sideways(self, md: MarketData, regime: RegimeState, sig: RegimeSignal):
        """
        Port of CalculateSidewaysSignal():
        BB lower + RSI oversold + Stoch oversold → BUY
        BB upper + RSI overbought + Stoch overbought → SELL
        """
        price   = md.current_price
        rsi     = md.rsi
        stoch_k = md.stoch_k
        stoch_d = md.stoch_d
        bb_u    = regime.bb_upper
        bb_l    = regime.bb_lower
        bb_m    = regime.bb_mid

        rsi_os  = rsi < 30.0
        rsi_ob  = rsi > 70.0
        sk_os   = stoch_k < 20.0
        sk_ob   = stoch_k > 80.0
        sk_x_up = stoch_k > stoch_d   # bullish cross proxy

        # Previous stoch from closes[-2] not available directly; use rsi trend
        rsi_rising  = rsi > 45.0
        rsi_falling = rsi < 55.0

        # BUY conditions (port dari MQL5)
        if price <= bb_l and rsi_os and sk_os:
            sig.buy_score += 40.0
        if sk_x_up and sk_os:
            sig.buy_score += 20.0
        if rsi < 40.0 and rsi_rising:
            sig.buy_score += 15.0

        # SELL conditions
        if price >= bb_u and rsi_ob and sk_ob:
            sig.sell_score += 40.0
        if not sk_x_up and sk_ob:
            sig.sell_score += 20.0
        if rsi > 60.0 and rsi_falling:
            sig.sell_score += 15.0

        # Volume confirmation
        if md.volume_ratio > 1.5:
            sig.buy_score  += 10.0
            sig.sell_score += 10.0

        sig.reason = (
            f"Sideways: BB_l={bb_l:.4f} BB_u={bb_u:.4f} "
            f"RSI={rsi:.1f} Stoch={stoch_k:.1f} "
            f"buy={sig.buy_score:.0f} sell={sig.sell_score:.0f}"
        )

    # ── TRENDING (Trend Following) ────────────────────────────────────
    def _trending(self, md: MarketData, regime: RegimeState, sig: RegimeSignal):
        """
        Port of CalculateTrendingSignal():
        Uptrend: price > EMA21 > EMA50, MACD bull + histogram rising, ADX > 30
        Downtrend: price < EMA21 < EMA50, MACD bear + histogram falling
        """
        is_up  = (regime.regime == MarketRegime.TRENDING_UP)
        price  = md.current_price
        ema21  = md.ema21
        ema50  = md.ema50
        macd_m = md.macd_main
        macd_s = md.macd_signal
        macd_h = md.macd_hist
        adx    = regime.adx

        macd_bull     = macd_m > macd_s
        macd_bear     = macd_m < macd_s
        strong_trend  = adx > 30.0
        close_prev    = md.closes[-2] if len(md.closes) >= 2 else price

        if is_up:
            # BUY in uptrend
            if price > ema21 and ema21 > ema50:
                sig.buy_score += 30.0
            if macd_bull and macd_h > 0:
                sig.buy_score += 25.0
            if strong_trend:
                sig.buy_score += 20.0
            # Pullback entry (bearish candle above slow MA)
            if md.opens and price < md.opens[-1] and price > ema50:
                sig.buy_score += 15.0
        else:
            # SELL in downtrend
            if price < ema21 and ema21 < ema50:
                sig.sell_score += 30.0
            if macd_bear and macd_h < 0:
                sig.sell_score += 25.0
            if strong_trend:
                sig.sell_score += 20.0
            # Rally short entry (bullish candle below slow MA)
            if md.opens and price > md.opens[-1] and price < ema50:
                sig.sell_score += 15.0

        sig.reason = (
            f"Trending({'UP' if is_up else 'DN'}): "
            f"EMA21={ema21:.4f} EMA50={ema50:.4f} "
            f"MACD={macd_m:.6f}/{macd_s:.6f} ADX={adx:.1f} "
            f"buy={sig.buy_score:.0f} sell={sig.sell_score:.0f}"
        )

    # ── VOLATILE (Momentum / ATR Breakout) ───────────────────────────
    def _volatile(self, md: MarketData, regime: RegimeState, sig: RegimeSignal):
        """
        Port of CalculateVolatileSignal():
        ATR channel breakout + volume spike
        """
        atr     = regime.atr or md.atr
        price   = md.current_price
        high    = md.highs[-1] if md.highs else price
        low     = md.lows[-1]  if md.lows  else price

        mult         = 3.0
        upper_ch     = price + atr * mult
        lower_ch     = price - atr * mult
        vol_spike    = md.volume_ratio > 2.0

        if high >= upper_ch and vol_spike:
            sig.buy_score += 50.0
        if low  <= lower_ch and vol_spike:
            sig.sell_score += 50.0

        # Momentum: price change % vs prev close
        if len(md.closes) >= 2 and md.closes[-2] > 0:
            pct_chg = (price - md.closes[-2]) / md.closes[-2] * 100
            if abs(pct_chg) > 0.5:
                if pct_chg > 0: sig.buy_score  += 15.0
                else:           sig.sell_score += 15.0

        sig.reason = (
            f"Volatile: ATR={atr:.4f} VolRatio={md.volume_ratio:.2f} "
            f"buy={sig.buy_score:.0f} sell={sig.sell_score:.0f}"
        )

    # ── BREAKOUT ─────────────────────────────────────────────────────
    def _breakout(self, md: MarketData, regime: RegimeState, sig: RegimeSignal):
        """
        Port of CalculateBreakoutSignal():
        Price breaks above consolidation high (or below low) + volume confirm
        """
        n    = 20
        highs  = md.highs[-n:] if len(md.highs) >= n else md.highs
        lows_  = md.lows[-n:]  if len(md.lows)  >= n else md.lows
        if not highs or not lows_:
            return

        consol_h = max(highs)
        consol_l = min(lows_)
        price    = md.current_price
        high     = md.highs[-1] if md.highs else price
        low      = md.lows[-1]  if md.lows  else price

        if price > 0:
            consol_range_pct = (consol_h - consol_l) / price * 100
        else:
            consol_range_pct = 99

        vol_break = md.volume_ratio > 2.0

        if consol_range_pct < 0.5:
            if high > consol_h and vol_break:
                sig.buy_score += 60.0
            if low  < consol_l and vol_break:
                sig.sell_score += 60.0

        sig.reason = (
            f"Breakout: range={consol_range_pct:.2f}% "
            f"consol_h={consol_h:.4f} consol_l={consol_l:.4f} "
            f"vol={md.volume_ratio:.2f} "
            f"buy={sig.buy_score:.0f} sell={sig.sell_score:.0f}"
        )

    # ── FILTERS ──────────────────────────────────────────────────────
    def _filters(self, md: MarketData, regime: RegimeState, sig: RegimeSignal):
        """
        Port of ApplySignalFilters():
        - HTF trend confirmation (using 1d vs 4h EMA21)
        - Candle pattern booster
        - Volume ratio gate
        """
        # HTF trend (1d vs current price)
        d_close = md.mtf_close.get("1d", 0)
        d_ema   = md.mtf_ema21.get("1d", 0)
        if d_close > 0 and d_ema > 0:
            htf_bull = d_close > d_ema
            if htf_bull:
                sig.buy_score  *= 1.2
            else:
                sig.sell_score *= 1.2

        # Candle patterns
        if len(md.closes) >= 2 and len(md.opens) >= 2:
            c0, o0 = md.closes[-1], md.opens[-1]
            c1, o1 = md.closes[-2], md.opens[-2]
            h0     = md.highs[-1] if md.highs else c0
            l0     = md.lows[-1]  if md.lows  else c0

            # Bullish engulfing
            if c1 < o1 and c0 > o0 and c0 > o1 and o0 < c1:
                sig.buy_score  += 15.0
            # Bearish engulfing
            if c1 > o1 and c0 < o0 and c0 < o1 and o0 > c1:
                sig.sell_score += 15.0

            # Pin bars
            body   = abs(c0 - o0)
            lo_wk  = min(o0, c0) - l0
            hi_wk  = h0 - max(o0, c0)
            tot    = h0 - l0
            if tot > 0 and body < tot * 0.3:
                if lo_wk > body * 2: sig.buy_score  += 10.0
                if hi_wk > body * 2: sig.sell_score += 10.0

        # Volume filter: penalise if vol_ratio out of range
        vr = md.volume_ratio
        if vr < 0.8 or vr > 5.0:
            sig.buy_score  *= 0.5
            sig.sell_score *= 0.5
