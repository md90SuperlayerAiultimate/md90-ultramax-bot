"""
MD90 Unified — Core Types (v4-complete)
Semua fields dari v4 Indicators: EMA8/21/50/200, ADX, MACD, OBV, MFI
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import IntEnum


class SignalDirection(IntEnum):
    SELL    = -1
    NEUTRAL =  0
    BUY     =  1


class ConfidenceLevel(IntEnum):
    LOW    = 0
    MEDIUM = 1
    HIGH   = 2
    ULTRA  = 3


@dataclass
class LayerSignal:
    layer_id:   int   = 0
    layer_name: str   = ""
    direction:  int   = 0
    strength:   float = 0.0
    confidence: float = 0.0
    reason:     str   = ""


@dataclass
class FusionSignal:
    direction:        int   = 0
    fusion_score:     float = 0.0
    confidence:       float = 0.0
    buy_votes:        int   = 0
    sell_votes:       int   = 0
    neutral_votes:    int   = 0
    gate1_passed:     bool  = False
    gate2_passed:     bool  = False
    gate3_passed:     bool  = False
    gate4_passed:     bool  = False
    gate5_passed:     bool  = False
    all_gates_passed: bool  = False
    execution_status: str   = "ABORT"
    entry_price:      float = 0.0
    stop_loss:        float = 0.0
    take_profit:      List[float] = field(default_factory=lambda: [0.0]*6)
    risk_reward:      List[float] = field(default_factory=lambda: [0.0]*6)
    confidence_level: int   = 0
    lot_multiplier:   float = 1.0
    sl_multiplier:    float = 1.0
    layer_signals:    List[LayerSignal] = field(default_factory=list)


@dataclass
class MarketData:
    symbol:        str
    timeframe:     str
    closes:        List[float]
    highs:         List[float]
    lows:          List[float]
    opens:         List[float]
    volumes:       List[float]
    current_price: float

    # ── Volatility ───────────────────────────────────────────────────
    atr:           float = 0.0
    atr_avg:       float = 0.0
    atr_ratio:     float = 1.0

    # ── EMA Stack (v4: EMA8/21/50/200) ──────────────────────────────
    ema8:          float = 0.0
    ema21:         float = 0.0
    ema50:         float = 0.0
    ema200_d:      float = 0.0   # Daily EMA200

    # ── ADX (v4 TrendIndicators) ─────────────────────────────────────
    adx:           float = 0.0
    di_plus:       float = 0.0
    di_minus:      float = 0.0

    # ── Momentum ─────────────────────────────────────────────────────
    rsi:           float = 50.0
    macd_main:     float = 0.0
    macd_signal:   float = 0.0
    macd_hist:     float = 0.0
    stoch_k:       float = 50.0
    stoch_d:       float = 50.0

    # ── Volume (v4: OBV + MFI) ───────────────────────────────────────
    obv:           float = 0.0
    obv_prev:      float = 0.0
    mfi:           float = 50.0
    volume_ratio:  float = 1.0
    buy_pressure:  float = 50.0
    volume_spike:  bool  = False

    # ── VWAP ─────────────────────────────────────────────────────────
    vwap:          float = 0.0

    # ── MTF (key: "5m","15m","1h","4h","1d") ─────────────────────────
    mtf_ema21:     Dict[str, float] = field(default_factory=dict)
    mtf_close:     Dict[str, float] = field(default_factory=dict)

    # ── Bollinger Bands (period=20, dev=2.0) ─────────────────────────
    bb_upper:      float = 0.0
    bb_mid:        float = 0.0
    bb_lower:      float = 0.0
    bb_width_pct:  float = 0.0   # (upper-lower)/mid * 100

    # ── Session ───────────────────────────────────────────────────────
    session_active: bool = True

    # ── Extra (agent results) ─────────────────────────────────────────
    extra:         Dict[str, Any] = field(default_factory=dict)
