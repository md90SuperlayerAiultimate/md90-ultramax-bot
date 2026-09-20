"""
MD90 Unified — SMC SwingDetector
Port dari MQL5 SwingDetector.mqh

Deteksi:
- Swing High / Swing Low (pivot method)
- CHoCH  (Change of Character)
- BOS    (Break of Structure)
- Bullish / Bearish market structure
- Premium / Discount zone (via PDZoneCalculator)
"""
from typing import List, Tuple, Optional
import math


class SwingDetector:
    """
    Deteksi swing structure dari OHLCV array.
    Gunakan rolling pivot dengan swing_len bars di setiap sisi.
    """

    def __init__(self, swing_len: int = 5):
        self.swing_len = swing_len
        self._highs: List[float] = []
        self._lows: List[float] = []
        self._swing_highs: List[Tuple[int, float]] = []   # (index, price)
        self._swing_lows:  List[Tuple[int, float]] = []
        self._is_bullish_structure: bool = False
        self._is_bearish_structure: bool = False
        self._choch_bullish: bool = False
        self._choch_bearish: bool = False

    # ------------------------------------------------------------------
    def update(self, highs: List[float], lows: List[float]):
        """Call dengan full OHLCV arrays setiap bar baru."""
        self._highs = highs
        self._lows  = lows
        self._compute_swings()
        self._compute_structure()

    # ------------------------------------------------------------------
    def _compute_swings(self):
        n   = len(self._highs)
        sl  = self.swing_len
        shs = []
        sls = []

        for i in range(sl, n - sl):
            # Swing High: highest in window
            window_h = self._highs[i - sl: i + sl + 1]
            if self._highs[i] == max(window_h):
                shs.append((i, self._highs[i]))
            # Swing Low: lowest in window
            window_l = self._lows[i - sl: i + sl + 1]
            if self._lows[i] == min(window_l):
                sls.append((i, self._lows[i]))

        # Keep most recent 20 each
        self._swing_highs = shs[-20:]
        self._swing_lows  = sls[-20:]

    # ------------------------------------------------------------------
    def _compute_structure(self):
        if len(self._swing_highs) < 2 or len(self._swing_lows) < 2:
            self._is_bullish_structure = False
            self._is_bearish_structure = False
            self._choch_bullish = False
            self._choch_bearish = False
            return

        # Higher Highs + Higher Lows → Bullish
        hh = self._swing_highs[-1][1] > self._swing_highs[-2][1]
        hl = self._swing_lows[-1][1]  > self._swing_lows[-2][1]
        # Lower Highs + Lower Lows → Bearish
        lh = self._swing_highs[-1][1] < self._swing_highs[-2][1]
        ll = self._swing_lows[-1][1]  < self._swing_lows[-2][1]

        was_bearish = self._is_bearish_structure
        was_bullish = self._is_bullish_structure

        self._is_bullish_structure = hh and hl
        self._is_bearish_structure = lh and ll

        # CHoCH: structure flip
        curr_price = self._highs[-1] if self._highs else 0

        # Bullish CHoCH: was bearish, now broke above last swing high → BOS
        if was_bearish and self._swing_highs:
            last_sh = self._swing_highs[-1][1]
            self._choch_bullish = curr_price > last_sh
        else:
            self._choch_bullish = False

        # Bearish CHoCH: was bullish, now broke below last swing low
        if was_bullish and self._swing_lows:
            last_sl = self._swing_lows[-1][1]
            self._choch_bearish = curr_price < last_sl
        else:
            self._choch_bearish = False

    # ------------------------------------------------------------------
    def get_last_swing_high(self) -> float:
        return self._swing_highs[-1][1] if self._swing_highs else 0.0

    def get_last_swing_low(self) -> float:
        return self._swing_lows[-1][1] if self._swing_lows else float("inf")

    def is_bullish_structure(self) -> bool:
        return self._is_bullish_structure

    def is_bearish_structure(self) -> bool:
        return self._is_bearish_structure

    def is_choch_bullish(self) -> bool:
        return self._choch_bullish

    def is_choch_bearish(self) -> bool:
        return self._choch_bearish

    def swing_range(self) -> float:
        """High - Low of last swing range"""
        sh = self.get_last_swing_high()
        sl = self.get_last_swing_low()
        return max(0.0, sh - sl)
