"""
MD90 — Market Regime Engine
Port EXACT dari MQL5 MD90_COMPLETE_ANALYSIS Section 15 DetectMarketRegime()
+ CalculateRegimeConfidence()

8 Regimes:
  UNDEFINED    — belum bisa ditentukan
  SIDEWAYS     — konsolidasi: ADX < 15, range < 1%
  TRENDING_UP  — ADX > 25, DI+ > DI-
  TRENDING_DOWN— ADX > 25, DI- > DI+
  VOLATILE     — ATR% > 0.2% (high volatility, no direction)
  BREAKOUT     — close > rangeHigh atau < rangeLow
  RANGING      — 1% < range < 2%
  TRANSITION   — tidak memenuhi kriteria spesifik
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import List


class MarketRegime(IntEnum):
    UNDEFINED     = 0
    SIDEWAYS      = 1
    TRENDING_UP   = 2
    TRENDING_DOWN = 3
    VOLATILE      = 4
    BREAKOUT      = 5
    RANGING       = 6
    TRANSITION    = 7


# ── Regime risk multipliers (port dari MQL5 Section 16) ──────────────
REGIME_RISK_MULT = {
    MarketRegime.SIDEWAYS:     0.7,
    MarketRegime.RANGING:      0.7,
    MarketRegime.TRENDING_UP:  1.2,
    MarketRegime.TRENDING_DOWN:1.2,
    MarketRegime.VOLATILE:     0.5,
    MarketRegime.BREAKOUT:     1.3,
    MarketRegime.TRANSITION:   0.8,
    MarketRegime.UNDEFINED:    0.5,
}

REGIME_NAMES = {
    MarketRegime.UNDEFINED:    "UNDEFINED",
    MarketRegime.SIDEWAYS:     "SIDEWAYS",
    MarketRegime.TRENDING_UP:  "TREND_UP",
    MarketRegime.TRENDING_DOWN:"TREND_DOWN",
    MarketRegime.VOLATILE:     "VOLATILE",
    MarketRegime.BREAKOUT:     "BREAKOUT",
    MarketRegime.RANGING:      "RANGING",
    MarketRegime.TRANSITION:   "TRANSITION",
}


@dataclass
class RegimeState:
    regime:           MarketRegime = MarketRegime.UNDEFINED
    prev_regime:      MarketRegime = MarketRegime.UNDEFINED
    trend_strength:   float        = 0.0   # ADX value 0–100
    volatility_pct:   float        = 0.0   # ATR / price * 100
    range_pct:        float        = 0.0   # (High-Low)/price * 100 over period
    confidence:       float        = 0.0   # 0–100%
    is_consolidating: bool         = False
    is_breaking_out:  bool         = False
    risk_mult:        float        = 0.8
    name:             str          = "UNDEFINED"
    duration_bars:    int          = 0
    # Indicator values (for regime-specific strategies)
    bb_upper:         float        = 0.0
    bb_mid:           float        = 0.0
    bb_lower:         float        = 0.0
    adx:              float        = 0.0
    di_plus:          float        = 0.0
    di_minus:         float        = 0.0
    atr:              float        = 0.0
    volume_ratio:     float        = 1.0


class RegimeEngine:
    """
    Market Regime Detector.
    Port dari MQL5 DetectMarketRegime() + CalculateRegimeConfidence().
    """
    # Thresholds (port dari MQL5 inputs)
    ADX_TREND_THRESHOLD    = 25.0
    ADX_SIDEWAYS_THRESHOLD = 15.0
    ATR_HIGH_VOL_THRESHOLD = 0.002   # 0.2% of price
    ATR_LOW_VOL_THRESHOLD  = 0.001
    RANGE_THRESHOLD_PCT    = 1.0
    RANGE_PERIOD           = 20

    def __init__(self):
        self._prev_regime  = MarketRegime.UNDEFINED
        self._duration     = 0

    def _bollinger(self, closes: List[float], period: int = 20, dev: float = 2.0):
        """Compute BB: returns (upper, mid, lower)"""
        if len(closes) < period:
            m = closes[-1] if closes else 0
            return m * 1.002, m, m * 0.998
        window = closes[-period:]
        mid    = sum(window) / period
        var    = sum((x - mid)**2 for x in window) / period
        std    = var**0.5
        return mid + dev * std, mid, mid - dev * std

    def analyze(self, closes: List[float], highs: List[float],
                lows: List[float], atr: float, adx: float,
                di_plus: float, di_minus: float,
                volume_ratio: float = 1.0) -> RegimeState:
        """
        Port of MQL5 DetectMarketRegime() + CalculateRegimeConfidence()
        """
        if len(closes) < 21:
            return RegimeState()

        price = closes[-1]

        # ATR as % of price
        atr_pct   = (atr / price) if price > 0 else 0

        # Range over RANGE_PERIOD bars
        n         = self.RANGE_PERIOD
        range_h   = max(highs[-n:]) if len(highs) >= n else max(highs)
        range_l   = min(lows[-n:])  if len(lows)  >= n else min(lows)
        range_pct = ((range_h - range_l) / price * 100) if price > 0 else 0

        # Bollinger Bands
        bb_u, bb_m, bb_l = self._bollinger(closes)

        # ── Regime detection (port exact dari MQL5) ───────────────────
        prev = self._prev_regime

        if adx > self.ADX_TREND_THRESHOLD:
            regime = MarketRegime.TRENDING_UP if di_plus > di_minus \
                     else MarketRegime.TRENDING_DOWN
            is_consol = False
            is_break  = False

        elif adx < self.ADX_SIDEWAYS_THRESHOLD and range_pct < self.RANGE_THRESHOLD_PCT:
            regime    = MarketRegime.SIDEWAYS
            is_consol = True
            is_break  = False

        elif atr_pct > self.ATR_HIGH_VOL_THRESHOLD:
            regime    = MarketRegime.VOLATILE
            is_consol = False
            is_break  = False

        elif price > range_h or price < range_l:
            regime    = MarketRegime.BREAKOUT
            is_consol = False
            is_break  = True

        elif self.RANGE_THRESHOLD_PCT < range_pct < 2.0:
            regime    = MarketRegime.RANGING
            is_consol = True
            is_break  = False

        else:
            regime    = MarketRegime.TRANSITION
            is_consol = False
            is_break  = False

        # ── Duration tracking ─────────────────────────────────────────
        if regime == prev:
            self._duration += 1
        else:
            self._duration = 0
        self._prev_regime = regime

        # ── Confidence score (port dari MQL5 CalculateRegimeConfidence) ──
        confidence = self._calc_confidence(
            regime, adx, range_pct, atr_pct, volume_ratio)

        return RegimeState(
            regime           = regime,
            prev_regime      = prev,
            trend_strength   = adx,
            volatility_pct   = atr_pct * 100,
            range_pct        = range_pct,
            confidence       = confidence,
            is_consolidating = is_consol,
            is_breaking_out  = is_break,
            risk_mult        = REGIME_RISK_MULT[regime],
            name             = REGIME_NAMES[regime],
            duration_bars    = self._duration,
            bb_upper         = bb_u,
            bb_mid           = bb_m,
            bb_lower         = bb_l,
            adx              = adx,
            di_plus          = di_plus,
            di_minus         = di_minus,
            atr              = atr,
            volume_ratio     = volume_ratio,
        )

    def _calc_confidence(self, regime: MarketRegime, adx: float,
                         range_pct: float, atr_pct: float,
                         vol_ratio: float) -> float:
        """
        Port of MQL5 CalculateRegimeConfidence()
        Returns 0–100.
        """
        c = 0.0
        if regime in (MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN):
            # Higher ADX = higher confidence
            c = min(adx / 100.0 * 2.0, 1.0)

        elif regime == MarketRegime.SIDEWAYS:
            c = min((self.ADX_SIDEWAYS_THRESHOLD - adx) /
                    self.ADX_SIDEWAYS_THRESHOLD, 1.0)
            rng_factor = min((self.RANGE_THRESHOLD_PCT - range_pct) /
                             self.RANGE_THRESHOLD_PCT, 1.0)
            c *= max(0, rng_factor)

        elif regime == MarketRegime.VOLATILE:
            c = min(atr_pct / (self.ATR_HIGH_VOL_THRESHOLD * 100), 1.0)

        elif regime == MarketRegime.BREAKOUT:
            c = 0.7
            if vol_ratio > 1.5:
                c = 1.0

        else:
            c = 0.5

        return round(max(0.0, min(1.0, c)) * 100, 1)
