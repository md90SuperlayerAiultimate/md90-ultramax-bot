"""
MD90 Unified — SMC Detectors (v4-accurate)
Port EXACT dari:
  - OrderBlockDetector.mqh  v4 (displacement_factor=0.6, volume_spike 1.5x)
  - FVGDetector.mqh         v4 (body/range >= 0.5 filter, same gap formula)
  - LiquiditySweepDetector  v4 (wick >= 0.5 ATR + volume >= 1.5x + reversal)
  - PDZoneCalculator        v4
"""
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════════════
# ORDER BLOCK — v4 ACCURATE
# ══════════════════════════════════════════════════════════════════════

@dataclass
class OrderBlock:
    high:         float
    low:          float
    mid:          float
    is_bullish:   bool
    bar_index:    int
    strength:     float = 0.7
    is_mitigated: bool  = False


class OrderBlockDetector:
    DISPLACEMENT_FACTOR = 0.6
    VOLUME_FACTOR       = 1.5
    MIN_OB_BODY_ATR     = 0.3

    def __init__(self, max_obs: int = 20, lookback: int = 100):
        self.max_obs  = max_obs
        self.lookback = lookback
        self._bull_obs: List[OrderBlock] = []
        self._bear_obs: List[OrderBlock] = []

    def _is_displacement(self, opens, closes, highs, lows,
                         i: int, bullish: bool, atr: float) -> bool:
        body = abs(closes[i] - opens[i])
        rng  = highs[i] - lows[i]
        if rng <= 0 or body / rng < self.DISPLACEMENT_FACTOR:
            return False
        if body < self.MIN_OB_BODY_ATR * atr:
            return False
        return closes[i] > opens[i] if bullish else closes[i] < opens[i]

    def _volume_spike(self, volumes: List[float], i: int) -> bool:
        if not volumes or i < 1:
            return True
        avg_vols = [volumes[j] for j in range(max(0, i - 10), i) if volumes[j] > 0]
        if not avg_vols:
            return True
        return volumes[i] >= (sum(avg_vols) / len(avg_vols)) * self.VOLUME_FACTOR

    def update(self, opens, highs, lows, closes, volumes, atr: float):
        n = len(closes)
        if n < 5:
            return
        new_bull, new_bear = [], []

        for i in range(2, min(n - 1, self.lookback)):
            ip1 = i + 1
            if ip1 >= n:
                continue

            # Bullish OB: prev bearish + displacement bullish + close > prev high
            if (closes[ip1] < opens[ip1] and
                    self._is_displacement(opens, closes, highs, lows, i, True, atr) and
                    self._volume_spike(volumes, i) and
                    closes[i] > highs[ip1]):
                new_bull.append(OrderBlock(
                    high=highs[ip1], low=lows[ip1],
                    mid=(highs[ip1]+lows[ip1])/2,
                    is_bullish=True, bar_index=ip1,
                    strength=min(1.0, (highs[ip1]-lows[ip1])/(atr*2))
                ))

            # Bearish OB: prev bullish + displacement bearish + close < prev low
            if (closes[ip1] > opens[ip1] and
                    self._is_displacement(opens, closes, highs, lows, i, False, atr) and
                    self._volume_spike(volumes, i) and
                    closes[i] < lows[ip1]):
                new_bear.append(OrderBlock(
                    high=highs[ip1], low=lows[ip1],
                    mid=(highs[ip1]+lows[ip1])/2,
                    is_bullish=False, bar_index=ip1,
                    strength=min(1.0, (highs[ip1]-lows[ip1])/(atr*2))
                ))

        price = closes[-1]
        self._bull_obs = self._mitigate(new_bull[-self.max_obs:], price, True)
        self._bear_obs = self._mitigate(new_bear[-self.max_obs:], price, False)

    def _mitigate(self, obs, price, bullish):
        return [ob for ob in obs
                if not (bullish and price < ob.low)
                and not (not bullish and price > ob.high)]

    def is_inside_bullish_ob(self, price: float) -> Tuple[bool, float]:
        for ob in reversed(self._bull_obs):
            if ob.low <= price <= ob.high:
                return True, ob.strength
        return False, 0.0

    def is_inside_bearish_ob(self, price: float) -> Tuple[bool, float]:
        for ob in reversed(self._bear_obs):
            if ob.low <= price <= ob.high:
                return True, ob.strength
        return False, 0.0


# ══════════════════════════════════════════════════════════════════════
# FVG — v4 ACCURATE
# ══════════════════════════════════════════════════════════════════════

@dataclass
class FVG:
    upper:     float
    lower:     float
    mid:       float
    is_bull:   bool
    bar_index: int
    size_atr:  float
    is_filled: bool = False


class FVGDetector:
    MIN_GAP_ATR = 0.2
    BODY_RATIO  = 0.5

    def __init__(self, max_fvgs: int = 30, lookback: int = 100):
        self.max_fvgs = max_fvgs
        self.lookback = lookback
        self._bull_fvgs: List[FVG] = []
        self._bear_fvgs: List[FVG] = []

    def _check_impulse(self, opens, closes, highs, lows, i, atr):
        """Returns (gap, body_ok, is_bull_impulse, is_bear_impulse)"""
        if i + 2 >= len(lows):
            return 0, False, False, False
        gap   = lows[i+2] - highs[i]
        if gap < self.MIN_GAP_ATR * atr:
            return gap, False, False, False
        body  = abs(closes[i+1] - opens[i+1])
        rng   = highs[i+1] - lows[i+1]
        body_ok = rng > 0 and body / rng >= self.BODY_RATIO
        is_bull = closes[i+1] > opens[i+1]
        is_bear = closes[i+1] < opens[i+1]
        return gap, body_ok, is_bull, is_bear

    def update(self, highs, lows, opens, closes, atr: float):
        n = len(closes)
        curr = closes[-1]
        bull_new, bear_new = [], []

        for i in range(0, min(n - 3, self.lookback)):
            gap, body_ok, is_bull, is_bear = self._check_impulse(
                opens, closes, highs, lows, i, atr)
            if gap <= 0 or not body_ok:
                continue
            fvg_args = dict(
                upper=lows[i+2], lower=highs[i],
                mid=(lows[i+2]+highs[i])/2,
                bar_index=i, size_atr=gap/atr)
            if is_bull:
                bull_new.append(FVG(is_bull=True, **fvg_args))
            elif is_bear:
                bear_new.append(FVG(is_bull=False, **fvg_args))

        def filter_filled(fvgs, is_bull):
            return [f for f in fvgs
                    if not (is_bull and curr <= f.lower)
                    and not (not is_bull and curr >= f.upper)]

        self._bull_fvgs = filter_filled(bull_new[-self.max_fvgs:], True)
        self._bear_fvgs = filter_filled(bear_new[-self.max_fvgs:], False)

    def is_in_bull_fvg(self, price: float) -> Tuple[bool, float]:
        for fvg in reversed(self._bull_fvgs):
            if fvg.lower <= price <= fvg.upper:
                return True, min(1.0, 0.6 + fvg.size_atr * 0.1)
        return False, 0.0

    def is_in_bear_fvg(self, price: float) -> Tuple[bool, float]:
        for fvg in reversed(self._bear_fvgs):
            if fvg.lower <= price <= fvg.upper:
                return True, min(1.0, 0.6 + fvg.size_atr * 0.1)
        return False, 0.0

    def has_any_fvg(self) -> bool:
        return bool(self._bull_fvgs or self._bear_fvgs)


# ══════════════════════════════════════════════════════════════════════
# LIQUIDITY SWEEP — v4 ACCURATE
# ══════════════════════════════════════════════════════════════════════

@dataclass
class LiqSweep:
    direction:  str
    level:      float
    wick_price: float
    wick_size:  float
    confirmed:  bool
    bar_index:  int


class LiquiditySweepDetector:
    SWEEP_THRESHOLD  = 0.5
    VOLUME_THRESHOLD = 1.5

    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self._sweeps: List[LiqSweep] = []

    def _wick(self, highs, lows, opens, closes, i, check_highs) -> float:
        if check_highs:
            return highs[i] - max(opens[i], closes[i])
        return min(opens[i], closes[i]) - lows[i]

    def _vol_ok(self, volumes, i) -> bool:
        if not volumes or i < 1 or volumes[i] <= 0:
            return True
        avg_v = [volumes[j] for j in range(max(0,i-10), i) if volumes[j] > 0]
        if not avg_v:
            return True
        return volumes[i] >= (sum(avg_v)/len(avg_v)) * self.VOLUME_THRESHOLD

    def update(self, highs, lows, opens, closes, volumes, atr,
               swing_high: float, swing_low: float):
        n = len(closes)
        if n < 3:
            return
        self._sweeps = []
        for i in range(max(1, n - self.lookback), n - 1):
            # Buy sweep
            if (lows[i] < swing_low and closes[i] > swing_low and
                    self._wick(highs,lows,opens,closes,i,False) >= self.SWEEP_THRESHOLD*atr and
                    self._vol_ok(volumes, i)):
                confirmed = i+1 < n and closes[i+1] > closes[i]
                self._sweeps.append(LiqSweep(
                    direction="BUY", level=swing_low, wick_price=lows[i],
                    wick_size=self._wick(highs,lows,opens,closes,i,False)/atr,
                    confirmed=confirmed, bar_index=i))

            # Sell sweep
            if (highs[i] > swing_high and closes[i] < swing_high and
                    self._wick(highs,lows,opens,closes,i,True) >= self.SWEEP_THRESHOLD*atr and
                    self._vol_ok(volumes, i)):
                confirmed = i+1 < n and closes[i+1] < closes[i]
                self._sweeps.append(LiqSweep(
                    direction="SELL", level=swing_high, wick_price=highs[i],
                    wick_size=self._wick(highs,lows,opens,closes,i,True)/atr,
                    confirmed=confirmed, bar_index=i))

    def has_recent_sweep(self, bars: int = 5) -> bool:
        return bool(self._sweeps)

    def get_last_buy_sweep(self) -> Optional[LiqSweep]:
        for s in reversed(self._sweeps):
            if s.direction == "BUY":
                return s
        return None

    def get_last_sell_sweep(self) -> Optional[LiqSweep]:
        for s in reversed(self._sweeps):
            if s.direction == "SELL":
                return s
        return None


# ══════════════════════════════════════════════════════════════════════
# PD ZONE
# ══════════════════════════════════════════════════════════════════════

class PDZoneCalculator:
    def __init__(self):
        self._sh = 0.0
        self._sl = float("inf")

    def update(self, swing_high: float, swing_low: float):
        self._sh = swing_high
        self._sl = swing_low

    def equilibrium(self) -> float:
        return self._sl + (self._sh - self._sl) * 0.5

    def ote_level(self) -> float:
        return self._sl + (self._sh - self._sl) * 0.705

    def is_in_discount(self, price: float) -> bool:
        eq = self.equilibrium()
        return price < eq if eq > 0 else False

    def is_in_premium(self, price: float) -> bool:
        eq = self.equilibrium()
        return price > eq if eq > 0 else False

    def is_at_ote(self, price: float, tol: float = 0.001) -> bool:
        ote = self.ote_level()
        return abs(price - ote) / ote <= tol if ote > 0 else False
