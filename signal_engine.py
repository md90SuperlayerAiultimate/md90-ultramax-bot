"""
MD90 Unified — Signal Engine (v4-accurate)
Semua 17 layer, port exact dari v4 source:
  L1  SNR        — SwingDetector S/R
  L2  EMA        — EMA8>EMA21>EMA50>EMA200 full stack (v4 EMABullStack)
  L3  RSI        — RSI + Momentum (v4 MomentumIndicators::GetRSISignal)
  L4  Stochastic — Stoch crossover (v4 GetStochSignal)
  L5  OrderBlock — OB w/ displacement+volume (v4 accurate)
  L6  Volume     — OBV rising/falling (v4 GetOBVSignal)
  L7  MTF        — 5-TF EMA21 alignment
  L8  Sentiment  — buy_pressure / MFI (v4 GetMFISignal)
  L9  UltraScalper — LiquiditySweep confirmed
  L10 PrimeSwing — CHoCH/BOS + PD Zone
  L11 MacroFlow  — Daily EMA200 + ADX
  L12 VWAP       — Price vs VWAP
  L13 ATR        — Volatility context
  L14 OTE        — Optimal Trade Entry fib
  L15 IDM/FVG    — FVG confluence
  L16 MasterCall — Candle pattern (engulfing/pin/hammer)
  L17 TimeStop   — Session killzone filter
"""
from typing import List
from datetime import datetime, timezone

from .types import LayerSignal, MarketData, SignalDirection
from .constants import (
    LAYER_NAMES, LAYER_WEIGHTS,
    LAYER_SNR, LAYER_EMA, LAYER_RSI, LAYER_STOCHASTIC, LAYER_ORDER_BLOCK,
    LAYER_VOLUME, LAYER_MTF, LAYER_SENTIMENT, LAYER_ULTRA_SCALPER,
    LAYER_PRIME_SWING, LAYER_MACRO_FLOW, LAYER_VWAP, LAYER_ATR_CONTEXT,
    LAYER_OTE, LAYER_IDM_FVG, LAYER_MASTER_CALL, LAYER_TIMESTOP,
    TOTAL_LAYERS, KILLZONE_HOURS,
)
from .smc import (
    SwingDetector, OrderBlockDetector, FVGDetector,
    LiquiditySweepDetector, PDZoneCalculator,
)

BUY     = int(SignalDirection.BUY)
SELL    = int(SignalDirection.SELL)
NEUTRAL = int(SignalDirection.NEUTRAL)


def _ls(lid, dir_, strength, reason) -> LayerSignal:
    return LayerSignal(
        layer_id=lid+1, layer_name=LAYER_NAMES[lid],
        direction=dir_, strength=max(0.0, min(1.0, strength)), reason=reason)


class SignalEngine:

    def __init__(self, swing_len: int = 5):
        self.swing = SwingDetector(swing_len)
        self.ob    = OrderBlockDetector()
        self.fvg   = FVGDetector()
        self.liq   = LiquiditySweepDetector()
        self.pd    = PDZoneCalculator()

    def _update_smc(self, md: MarketData):
        if len(md.closes) < 10:
            return
        self.swing.update(md.highs, md.lows)
        self.ob.update(md.opens, md.highs, md.lows, md.closes, md.volumes, md.atr)
        self.fvg.update(md.highs, md.lows, md.opens, md.closes, md.atr)
        sh  = self.swing.get_last_swing_high()
        sl_ = self.swing.get_last_swing_low()
        self.liq.update(md.highs, md.lows, md.opens, md.closes,
                        md.volumes, md.atr, sh, sl_)
        self.pd.update(sh, sl_)

    def analyze(self, md: MarketData) -> List[LayerSignal]:
        self._update_smc(md)
        signals = [None] * TOTAL_LAYERS
        signals[LAYER_SNR]           = self._l1_snr(md)
        signals[LAYER_EMA]           = self._l2_ema(md)
        signals[LAYER_RSI]           = self._l3_rsi(md)
        signals[LAYER_STOCHASTIC]    = self._l4_stoch(md)
        signals[LAYER_ORDER_BLOCK]   = self._l5_ob(md)
        signals[LAYER_VOLUME]        = self._l6_volume(md)
        signals[LAYER_MTF]           = self._l7_mtf(md)
        signals[LAYER_SENTIMENT]     = self._l8_sentiment(md)
        signals[LAYER_ULTRA_SCALPER] = self._l9_scalper(md)
        signals[LAYER_PRIME_SWING]   = self._l10_primeswing(md)
        signals[LAYER_MACRO_FLOW]    = self._l11_macro(md)
        signals[LAYER_VWAP]          = self._l12_vwap(md)
        signals[LAYER_ATR_CONTEXT]   = self._l13_atr(md)
        signals[LAYER_OTE]           = self._l14_ote(md)
        signals[LAYER_IDM_FVG]       = self._l15_idmfvg(md)
        signals[LAYER_MASTER_CALL]   = self._l16_mastercall(md)
        signals[LAYER_TIMESTOP]      = self._l17_timestop(md)
        return signals

    # ── L1: S/R (SwingDetector) ──────────────────────────────────────
    def _l1_snr(self, md):
        lid = LAYER_SNR
        if md.atr <= 0:
            return _ls(lid, NEUTRAL, 0, "No ATR")
        price = md.current_price
        sh  = self.swing.get_last_swing_high()
        sl_ = self.swing.get_last_swing_low()
        dist_sup = (price - sl_) / md.atr if sl_ < float("inf") else 999
        dist_res = (sh - price)  / md.atr if sh > 0 else 999
        if dist_sup < 0.5:
            return _ls(lid, BUY,  0.7, f"Near support  Δ={dist_sup:.2f}ATR")
        if dist_res < 0.5:
            return _ls(lid, SELL, 0.7, f"Near resistance Δ={dist_res:.2f}ATR")
        return _ls(lid, NEUTRAL, 0, "No clear S/R")

    # ── L2: EMA Stack (v4: EMA8>EMA21>EMA50>EMA200) ─────────────────
    def _l2_ema(self, md):
        lid = LAYER_EMA
        e8, e21, e50, e200 = md.ema8, md.ema21, md.ema50, md.ema200_d
        if not all([e8, e21, e50]):
            return _ls(lid, NEUTRAL, 0, "EMA not ready")
        # v4 EMABullStack: all aligned
        if e8 > e21 > e50:
            str_ = 0.8 if (e200 > 0 and e8 > e200) else 0.6
            return _ls(lid, BUY,  str_, "EMA bull stack 8>21>50")
        if e8 < e21 < e50:
            str_ = 0.8 if (e200 > 0 and e8 < e200) else 0.6
            return _ls(lid, SELL, str_, "EMA bear stack 8<21<50")
        if e8 > e21:
            return _ls(lid, BUY,  0.4, "EMA8>EMA21 partial bull")
        if e8 < e21:
            return _ls(lid, SELL, 0.4, "EMA8<EMA21 partial bear")
        return _ls(lid, NEUTRAL, 0, "EMA flat")

    # ── L3: RSI (v4 GetRSISignal: >50=bull, <50=bear, OB/OS extreme) ─
    def _l3_rsi(self, md):
        lid = LAYER_RSI
        r = md.rsi
        if r <= 30:
            return _ls(lid, BUY,  0.8, f"RSI oversold {r:.1f}")
        if r >= 70:
            return _ls(lid, SELL, 0.8, f"RSI overbought {r:.1f}")
        if r > 50:
            return _ls(lid, BUY,  0.5, f"RSI bullish {r:.1f}")
        if r < 50:
            return _ls(lid, SELL, 0.5, f"RSI bearish {r:.1f}")
        return _ls(lid, NEUTRAL, 0, "RSI neutral")

    # ── L4: Stochastic (v4 GetStochSignal) ───────────────────────────
    def _l4_stoch(self, md):
        lid = LAYER_STOCHASTIC
        k, d = md.stoch_k, md.stoch_d
        if k <= 20 and k > d:
            return _ls(lid, BUY,  0.7, f"Stoch oversold cross-up K={k:.1f}")
        if k >= 80 and k < d:
            return _ls(lid, SELL, 0.7, f"Stoch overbought cross-dn K={k:.1f}")
        if k > d:
            return _ls(lid, BUY,  0.3, "Stoch bullish K>D")
        if k < d:
            return _ls(lid, SELL, 0.3, "Stoch bearish K<D")
        return _ls(lid, NEUTRAL, 0, "Stoch neutral")

    # ── L5: Order Block (v4 accurate) ────────────────────────────────
    def _l5_ob(self, md):
        lid = LAYER_ORDER_BLOCK
        price = md.current_price
        in_bull, str_b = self.ob.is_inside_bullish_ob(price)
        if in_bull:
            return _ls(lid, BUY,  str_b, "Inside bullish OB")
        in_bear, str_s = self.ob.is_inside_bearish_ob(price)
        if in_bear:
            return _ls(lid, SELL, str_s, "Inside bearish OB")
        return _ls(lid, NEUTRAL, 0, "No active OB")

    # ── L6: Volume / OBV (v4 GetOBVSignal) ───────────────────────────
    def _l6_volume(self, md):
        lid = LAYER_VOLUME
        # OBV rising → BUY, OBV falling → SELL (port of VolumeIndicators)
        if md.obv > md.obv_prev and md.obv_prev != 0:
            str_ = 0.7 if md.volume_ratio > 1.5 else 0.4
            return _ls(lid, BUY,  str_, f"OBV rising vol_ratio={md.volume_ratio:.2f}")
        if md.obv < md.obv_prev and md.obv_prev != 0:
            str_ = 0.7 if md.volume_ratio > 1.5 else 0.4
            return _ls(lid, SELL, str_, f"OBV falling vol_ratio={md.volume_ratio:.2f}")
        # Fallback: volume ratio only
        if md.volume_ratio > 1.5:
            dir_ = BUY if md.closes[-1] > md.opens[-1] else SELL
            return _ls(lid, dir_, 0.5, f"Vol spike ratio={md.volume_ratio:.2f}")
        return _ls(lid, NEUTRAL, 0, f"Normal volume ratio={md.volume_ratio:.2f}")

    # ── L7: Multi-Timeframe ───────────────────────────────────────────
    def _l7_mtf(self, md):
        lid = LAYER_MTF
        bull = bear = 0
        for tf in ["5m","15m","1h","4h","1d"]:
            c = md.mtf_close.get(tf, 0)
            e = md.mtf_ema21.get(tf, 0)
            if c > 0 and e > 0:
                if c > e: bull += 1
                else:      bear += 1
        if bull >= 4:
            return _ls(lid, BUY,  0.8, f"MTF {bull}/5 bullish")
        if bear >= 4:
            return _ls(lid, SELL, 0.8, f"MTF {bear}/5 bearish")
        if bull > bear:
            return _ls(lid, BUY,  0.4, f"MTF majority bull {bull}vs{bear}")
        if bear > bull:
            return _ls(lid, SELL, 0.4, f"MTF majority bear {bear}vs{bull}")
        return _ls(lid, NEUTRAL, 0, f"MTF mixed {bull}vs{bear}")

    # ── L8: Sentiment / MFI (v4 GetMFISignal) ────────────────────────
    def _l8_sentiment(self, md):
        lid = LAYER_SENTIMENT
        mfi = md.mfi
        if mfi <= 20:
            return _ls(lid, BUY,  0.7, f"MFI oversold {mfi:.1f}")
        if mfi >= 80:
            return _ls(lid, SELL, 0.7, f"MFI overbought {mfi:.1f}")
        # fallback buy_pressure
        p = md.buy_pressure
        if p > 60:
            return _ls(lid, BUY,  0.4, f"Buy pressure {p:.1f}%")
        if p < 40:
            return _ls(lid, SELL, 0.4, f"Sell pressure {100-p:.1f}%")
        return _ls(lid, NEUTRAL, 0, f"Neutral sentiment MFI={mfi:.1f}")

    # ── L9: UltraScalper / LiqSweep (v4 accurate) ────────────────────
    def _l9_scalper(self, md):
        lid = LAYER_ULTRA_SCALPER
        if not self.liq.has_recent_sweep():
            return _ls(lid, NEUTRAL, 0, "No sweep detected")
        bs = self.liq.get_last_buy_sweep()
        if bs and bs.confirmed:
            return _ls(lid, BUY,  0.8, f"Buy sweep confirmed wick={bs.wick_size:.2f}ATR")
        ss = self.liq.get_last_sell_sweep()
        if ss and ss.confirmed:
            return _ls(lid, SELL, 0.8, f"Sell sweep confirmed wick={ss.wick_size:.2f}ATR")
        return _ls(lid, NEUTRAL, 0, "Sweep unconfirmed")

    # ── L10: PrimeSwing / CHoCH + BOS ────────────────────────────────
    def _l10_primeswing(self, md):
        lid = LAYER_PRIME_SWING
        price = md.current_price
        if self.swing.is_choch_bullish() and self.pd.is_in_discount(price):
            return _ls(lid, BUY,  0.9, "CHoCH bullish at discount")
        if self.swing.is_choch_bearish() and self.pd.is_in_premium(price):
            return _ls(lid, SELL, 0.9, "CHoCH bearish at premium")
        if self.swing.is_bullish_structure():
            return _ls(lid, BUY,  0.5, "Bullish structure HH+HL")
        if self.swing.is_bearish_structure():
            return _ls(lid, SELL, 0.5, "Bearish structure LH+LL")
        return _ls(lid, NEUTRAL, 0, "No clear structure")

    # ── L11: MacroFlow / EMA200 + ADX (v4 accurate) ──────────────────
    def _l11_macro(self, md):
        lid = LAYER_MACRO_FLOW
        close_d = md.mtf_close.get("1d", 0)
        ema200  = md.ema200_d
        adx_trending = md.adx >= 25.0
        if close_d > 0 and ema200 > 0:
            if close_d > ema200:
                str_ = 0.8 if adx_trending and md.di_plus > md.di_minus else 0.5
                return _ls(lid, BUY,  str_, f"Price>EMA200 ADX={md.adx:.1f}")
            else:
                str_ = 0.8 if adx_trending and md.di_minus > md.di_plus else 0.5
                return _ls(lid, SELL, str_, f"Price<EMA200 ADX={md.adx:.1f}")
        # ADX only fallback
        if adx_trending:
            dir_ = BUY if md.di_plus > md.di_minus else SELL
            return _ls(lid, dir_, 0.4, f"ADX trending {md.adx:.1f}")
        return _ls(lid, NEUTRAL, 0, "Macro neutral / ADX weak")

    # ── L12: VWAP ────────────────────────────────────────────────────
    def _l12_vwap(self, md):
        lid = LAYER_VWAP
        if md.vwap <= 0:
            return _ls(lid, NEUTRAL, 0, "VWAP unavailable")
        price = md.current_price
        if price > md.vwap * 1.001:
            return _ls(lid, BUY,  0.5, f"Price>VWAP {md.vwap:.4f}")
        if price < md.vwap * 0.999:
            return _ls(lid, SELL, 0.5, f"Price<VWAP {md.vwap:.4f}")
        return _ls(lid, NEUTRAL, 0, "At VWAP")

    # ── L13: ATR Context ─────────────────────────────────────────────
    def _l13_atr(self, md):
        lid = LAYER_ATR_CONTEXT
        # High ATR ratio = expansion; neutral on direction, context only
        r = md.atr_ratio
        if r > 2.0:
            return _ls(lid, NEUTRAL, 0.1, f"ATR spike ratio={r:.2f} — avoid")
        dir_ = BUY if md.ema8 > md.ema21 else (SELL if md.ema8 < md.ema21 else NEUTRAL)
        return _ls(lid, dir_, 0.3, f"ATR context ratio={r:.2f}")

    # ── L14: OTE (Optimal Trade Entry) ───────────────────────────────
    def _l14_ote(self, md):
        lid = LAYER_OTE
        sh  = self.swing.get_last_swing_high()
        sl_ = self.swing.get_last_swing_low()
        if sh <= 0 or sl_ == float("inf"):
            return _ls(lid, NEUTRAL, 0, "No swing range")
        price = md.current_price
        if self.pd.is_at_ote(price):
            dir_ = BUY if self.swing.is_bullish_structure() else SELL
            return _ls(lid, dir_, 0.8, "At OTE 70.5% fib")
        return _ls(lid, NEUTRAL, 0, "Not at OTE")

    # ── L15: IDM / FVG ───────────────────────────────────────────────
    def _l15_idmfvg(self, md):
        lid = LAYER_IDM_FVG
        price = md.current_price
        in_bull, str_b = self.fvg.is_in_bull_fvg(price)
        if in_bull:
            return _ls(lid, BUY,  str_b, "Inside bullish FVG")
        in_bear, str_s = self.fvg.is_in_bear_fvg(price)
        if in_bear:
            return _ls(lid, SELL, str_s, "Inside bearish FVG")
        if self.fvg.has_any_fvg():
            return _ls(lid, NEUTRAL, 0.3, "FVG exists nearby")
        return _ls(lid, NEUTRAL, 0, "No FVG")

    # ── L16: MasterCall (Candle Pattern) ─────────────────────────────
    def _l16_mastercall(self, md):
        lid = LAYER_MASTER_CALL
        closes, opens, highs, lows = md.closes, md.opens, md.highs, md.lows
        if len(closes) < 3:
            return _ls(lid, NEUTRAL, 0, "Insufficient data")
        # Engulfing
        if (closes[-1]>opens[-1] and closes[-2]<opens[-2] and
                closes[-1]>opens[-2] and opens[-1]<closes[-2]):
            return _ls(lid, BUY,  0.8, "Bullish engulfing")
        if (closes[-1]<opens[-1] and closes[-2]>opens[-2] and
                closes[-1]<opens[-2] and opens[-1]>closes[-2]):
            return _ls(lid, SELL, 0.8, "Bearish engulfing")
        # Pin bar
        body     = abs(closes[-1] - opens[-1])
        body_top = max(opens[-1], closes[-1])
        body_bot = min(opens[-1], closes[-1])
        wick_lo  = body_bot - lows[-1]
        wick_hi  = highs[-1] - body_top
        if wick_lo > 2 * body and body > 0:
            return _ls(lid, BUY,  0.7, "Hammer/bullish pin")
        if wick_hi > 2 * body and body > 0:
            return _ls(lid, SELL, 0.7, "Shooting star/bearish pin")
        # Doji
        if md.atr > 0 and body < md.atr * 0.1:
            return _ls(lid, NEUTRAL, 0.2, "Doji — indecision")
        # Strong close
        if closes[-1] > opens[-1]:
            return _ls(lid, BUY,  0.4, "Bullish close")
        return _ls(lid, SELL, 0.4, "Bearish close")

    # ── L17: TimeStop / Killzone (v4 SessionFilter) ──────────────────
    def _l17_timestop(self, md):
        lid = LAYER_TIMESTOP
        h = datetime.now(timezone.utc).hour
        in_killzone = h in KILLZONE_HOURS
        in_session  = 8 <= h < 22
        if in_killzone:
            dir_ = BUY if h < 12 else SELL
            return _ls(lid, dir_, 0.8, f"Killzone UTC h={h}")
        if in_session:
            return _ls(lid, NEUTRAL, 0.5, f"Session active UTC h={h}")
        return _ls(lid, NEUTRAL, 0.1, f"Off-session UTC h={h}")
