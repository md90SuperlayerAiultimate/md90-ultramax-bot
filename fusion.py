"""
MD90 Unified — Fusion Score + Gate Filter + Confidence Engine
Port PRESISI dari:
  - MQL5 CFusionScore::Calculate()
  - MQL5 CGateFilter::Evaluate*()
  - MQL5 CSignalEngine::DetermineExecutionStatus()  ← EXACT logic
  - MQL5 CConfidenceEngine::Calculate()
"""
from typing import List
from .types import LayerSignal, FusionSignal, ConfidenceLevel, SignalDirection
from .constants import (
    LAYER_WEIGHTS, TOTAL_LAYERS,
    # Gate 1: EMA(L2=idx1) + MTF(L7=idx6) + PrimeSwing(L10=idx9)
    LAYER_EMA, LAYER_MTF, LAYER_PRIME_SWING,
    # Gate 2: OTE(L14=idx13) + IDM_FVG(L15=idx14)
    LAYER_OTE, LAYER_IDM_FVG,
    # Gate 3: RSI(L3=idx2) + Stoch(L4=idx3) + Volume(L6=idx5) + VWAP(L12=idx11)
    LAYER_RSI, LAYER_STOCHASTIC, LAYER_VOLUME, LAYER_VWAP,
    # Gate 4: MasterCall(L16=idx15) + UltraScalper(L9=idx8)
    LAYER_MASTER_CALL, LAYER_ULTRA_SCALPER,
    # Gate 5: TimeStop(L17=idx16)
    LAYER_TIMESTOP,
    ATR_SL_MULT, ATR_TP_MULTS,
    FUSION_SCORE_MIN, CONFIDENCE_MIN, RR_MINIMUM,
)

BUY     = int(SignalDirection.BUY)
SELL    = int(SignalDirection.SELL)
NEUTRAL = int(SignalDirection.NEUTRAL)


# ══════════════════════════════════════════════════════════════════════
# FUSION SCORE (port dari CFusionScore::Calculate)
# ══════════════════════════════════════════════════════════════════════

def calculate_fusion_score(layers: List[LayerSignal]) -> FusionSignal:
    sig = FusionSignal()
    w_buy = w_sell = w_total = 0.0
    for i, ls in enumerate(layers):
        w = LAYER_WEIGHTS[i]
        s = ls.strength
        w_total += w
        if ls.direction == BUY:
            w_buy  += w * s
            sig.buy_votes += 1
        elif ls.direction == SELL:
            w_sell += w * s
            sig.sell_votes += 1
        else:
            sig.neutral_votes += 1
    if w_total > 0:
        bs = w_buy  / w_total
        ss = w_sell / w_total
        if bs > ss:
            sig.direction    = BUY
            sig.fusion_score = bs
        elif ss > bs:
            sig.direction    = SELL
            sig.fusion_score = ss
        else:
            sig.direction    = NEUTRAL
            sig.fusion_score = 0.0
    sig.layer_signals = layers
    return sig


# ══════════════════════════════════════════════════════════════════════
# GATE FILTER (port PRESISI dari CGateFilter + DetermineExecutionStatus)
# Indices di sini = 0-based (sesuai list Python)
# MQL5 m_layer_signals[0..16] = Layer1..17
# ══════════════════════════════════════════════════════════════════════

def evaluate_gates(sig: FusionSignal, layers: List[LayerSignal],
                   rr_tp1: float) -> FusionSignal:
    L = layers
    target = sig.direction

    # Gate 1 (MQL5 idx 1,6,9) → LAYER_EMA=1, LAYER_MTF=6, LAYER_PRIME_SWING=9
    l_ema = L[LAYER_EMA]
    l_mtf = L[LAYER_MTF]
    l_sw  = L[LAYER_PRIME_SWING]
    sig.gate1_passed = (
        l_ema.direction != NEUTRAL and
        l_ema.direction == l_mtf.direction and
        l_mtf.direction == l_sw.direction
    )

    # Gate 2 (MQL5 idx 13,14) → LAYER_OTE=13, LAYER_IDM_FVG=14
    l_ote    = L[LAYER_OTE]
    l_idmfvg = L[LAYER_IDM_FVG]
    sig.gate2_passed = (
        (l_ote.direction != NEUTRAL and l_ote.direction == l_idmfvg.direction) or
        l_idmfvg.strength > 0.8
    )

    # Gate 3 (MQL5 idx 2,3,5,11) → RSI=2, Stoch=3, Volume=5, VWAP=11
    agree = sum([
        L[LAYER_RSI].direction        == target,
        L[LAYER_STOCHASTIC].direction == target,
        L[LAYER_VOLUME].direction     == target,
        L[LAYER_VWAP].direction       == target,
    ])
    sig.gate3_passed = agree >= 3

    # Gate 4 (MQL5 idx 15,8) → MasterCall=15, UltraScalper=8
    l_mc = L[LAYER_MASTER_CALL]
    l_sc = L[LAYER_ULTRA_SCALPER]
    sig.gate4_passed = (
        l_mc.direction == target and
        (l_sc.direction == target or l_mc.strength > 0.8)
    )

    # Gate 5 (MQL5 idx 16) → TimeStop=16 + RR
    l_ts = L[LAYER_TIMESTOP]
    sig.gate5_passed = (l_ts.strength >= 0.5 and rr_tp1 >= RR_MINIMUM)

    sig.all_gates_passed = all([
        sig.gate1_passed, sig.gate2_passed, sig.gate3_passed,
        sig.gate4_passed, sig.gate5_passed,
    ])
    return sig


# ══════════════════════════════════════════════════════════════════════
# EXECUTION STATUS — EXACT port dari MQL5 DetermineExecutionStatus()
# ══════════════════════════════════════════════════════════════════════

def determine_status(sig: FusionSignal) -> str:
    """
    MQL5 exact:
    if (!gate1 || !gate5)           → ABORT
    elif (!gate2 || !gate4)         → WAITING
    elif (score>=0.55 && conf>=75)  → ALL-IN
    else                            → WAITING
    """
    if sig.direction == NEUTRAL:
        return "ABORT"
    if not sig.gate1_passed or not sig.gate5_passed:
        return "ABORT"
    if not sig.gate2_passed or not sig.gate4_passed:
        return "WAITING"
    if sig.fusion_score >= FUSION_SCORE_MIN and sig.confidence >= CONFIDENCE_MIN:
        return "ALL-IN"
    return "WAITING"


# ══════════════════════════════════════════════════════════════════════
# CONFIDENCE ENGINE (port dari CConfidenceEngine::Calculate)
# ══════════════════════════════════════════════════════════════════════

def calculate_confidence(sig: FusionSignal, layers: List[LayerSignal],
                         atr_ratio: float, volume_spike: bool) -> float:
    base    = sig.fusion_score * 100.0
    bonus   = 0.0
    penalty = 0.0
    L = layers

    if L[LAYER_MTF].strength > 0.7:            bonus += 5.0
    if volume_spike:                            bonus += 5.0
    if L[LAYER_IDM_FVG].strength > 0.8:         bonus += 5.0
    if L[LAYER_MASTER_CALL].strength > 0.8:     bonus += 3.0

    conf_count = sum(1 for ls in layers if ls.direction == sig.direction)
    if conf_count >= 12:   bonus += 10.0
    elif conf_count >= 10: bonus += 5.0

    if L[LAYER_MTF].direction != sig.direction:  penalty += 5.0
    if L[LAYER_VOLUME].strength < 0.3:           penalty += 3.0
    if L[LAYER_TIMESTOP].strength < 0.5:         penalty += 10.0
    if atr_ratio > 2.0:                          penalty += 5.0

    conf_val = max(0.0, min(100.0, base + bonus - penalty))

    if conf_val >= 90:
        sig.confidence_level = int(ConfidenceLevel.ULTRA)
        sig.lot_multiplier   = 2.0
        sig.sl_multiplier    = 0.8
    elif conf_val >= 80:
        sig.confidence_level = int(ConfidenceLevel.HIGH)
        sig.lot_multiplier   = 1.5
        sig.sl_multiplier    = 0.9
    elif conf_val >= 65:
        sig.confidence_level = int(ConfidenceLevel.MEDIUM)
        sig.lot_multiplier   = 1.0
        sig.sl_multiplier    = 1.0
    else:
        sig.confidence_level = int(ConfidenceLevel.LOW)
        sig.lot_multiplier   = 0.5
        sig.sl_multiplier    = 1.2

    sig.confidence = conf_val
    return conf_val


# ══════════════════════════════════════════════════════════════════════
# ENTRY/EXIT LEVELS (port dari CStopManager::Calculate)
# ══════════════════════════════════════════════════════════════════════

def calculate_levels(sig: FusionSignal, price: float, atr: float) -> FusionSignal:
    sig.entry_price = price
    sl_dist = atr * ATR_SL_MULT * sig.sl_multiplier

    if sig.direction == BUY:
        sig.stop_loss = price - sl_dist
        for i, mult in enumerate(ATR_TP_MULTS):
            sig.take_profit[i] = price + atr * mult
            risk = price - sig.stop_loss
            sig.risk_reward[i] = (sig.take_profit[i] - price) / risk if risk > 0 else 0
    else:
        sig.stop_loss = price + sl_dist
        for i, mult in enumerate(ATR_TP_MULTS):
            sig.take_profit[i] = price - atr * mult
            risk = sig.stop_loss - price
            sig.risk_reward[i] = (price - sig.take_profit[i]) / risk if risk > 0 else 0
    return sig


# ══════════════════════════════════════════════════════════════════════
# MASTER FUNCTION — dipanggil oleh synthesis_agent
# ══════════════════════════════════════════════════════════════════════

def full_analyze(layers: List[LayerSignal], price: float, atr: float,
                 atr_ratio: float, volume_spike: bool) -> FusionSignal:
    """
    FusionScore → Levels → GateFilter → ConfidenceEngine → Status
    Order ini penting: levels harus ada sebelum gate5 cek RR.
    """
    if len(layers) != TOTAL_LAYERS:
        raise ValueError(f"Expected {TOTAL_LAYERS} layers, got {len(layers)}")

    sig = calculate_fusion_score(layers)

    if sig.direction == NEUTRAL:
        sig.execution_status = "ABORT"
        return sig

    # Calculate levels first (needed for RR in gate5)
    sig = calculate_levels(sig, price, atr)
    rr_tp1 = sig.risk_reward[0] if sig.risk_reward else 0.0

    # Gate evaluation (needs RR)
    sig = evaluate_gates(sig, layers, rr_tp1)

    # Confidence (needs gate results)
    calculate_confidence(sig, layers, atr_ratio, volume_spike)

    # Final status — EXACT MQL5 logic
    sig.execution_status = determine_status(sig)

    return sig
