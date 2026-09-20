"""
MD90 Unified — Constants
Port dari MQL5 MD90_Fusion/Common/Constants.mqh
"""

# ── Layer IDs (0-indexed untuk list access) ─────────────────────────
LAYER_SNR          = 0
LAYER_EMA          = 1
LAYER_RSI          = 2
LAYER_STOCHASTIC   = 3
LAYER_ORDER_BLOCK  = 4
LAYER_VOLUME       = 5
LAYER_MTF          = 6
LAYER_SENTIMENT    = 7
LAYER_ULTRA_SCALPER = 8
LAYER_PRIME_SWING  = 9
LAYER_MACRO_FLOW   = 10
LAYER_VWAP         = 11
LAYER_ATR_CONTEXT  = 12
LAYER_OTE          = 13
LAYER_IDM_FVG      = 14
LAYER_MASTER_CALL  = 15
LAYER_TIMESTOP     = 16
TOTAL_LAYERS       = 17

LAYER_NAMES = [
    "SNR", "EMA", "RSI", "Stochastic", "OrderBlock",
    "Volume", "MTF", "Sentiment", "UltraScalper", "PrimeSwing",
    "MacroFlow", "VWAP", "ATR", "OTE", "IDM_FVG",
    "MasterCall", "TimeStop",
]

# Weights dari MQL5 CSignalEngine constructor (sum = 1.01, scale ke 1.0)
LAYER_WEIGHTS = [
    0.08, 0.07, 0.06, 0.05, 0.08,
    0.06, 0.07, 0.04, 0.07, 0.08,
    0.07, 0.04, 0.04, 0.06, 0.06,
    0.05, 0.02,
]

# ── Fusion / Confidence Thresholds ──────────────────────────────────
FUSION_SCORE_MIN = 0.55
CONFIDENCE_MIN   = 75.0
RR_MINIMUM       = 2.0

# ── ATR Multipliers ──────────────────────────────────────────────────
ATR_SL_MULT  = 1.5
ATR_TP_MULTS = [2.0, 3.0, 4.0, 5.5, 7.0, 10.0]   # 6 TP levels

# ── Partial Close % per TP ───────────────────────────────────────────
PARTIAL_PCT = [25.0, 25.0, 20.0, 15.0, 10.0]   # TP1–TP5

# ── Sessions (UTC hour) ──────────────────────────────────────────────
SESSION_TOKYO  = (1,  9)
SESSION_LONDON = (8,  17)
SESSION_NY     = (13, 22)
# Killzone hours (London open, NY open + overlap)
KILLZONE_HOURS = {2, 3, 8, 9, 10, 13, 14, 15}

# ── SMC Params ────────────────────────────────────────────────────────
SWING_LEN      = 5     # bars each side for swing detection
OB_MAX_AGE     = 100   # bars
FVG_MAX_AGE    = 50
LIQ_LOOKBACK   = 20
FVG_MIN_ATR    = 0.2   # FVG minimum size in ATR units

# ── Risk Defaults ─────────────────────────────────────────────────────
DEFAULT_RISK_PCT    = 1.0
MAX_DRAWDOWN_PCT    = 10.0
MAX_DAILY_LOSS_PCT  = 5.0
MAX_POSITIONS       = 3

# ── MarketMind Agent Layer Groups ─────────────────────────────────────
# Maps LangGraph agent name → list of layer IDs it computes
AGENT_LAYER_MAP = {
    "price_agent":    [LAYER_SNR, LAYER_EMA, LAYER_MACRO_FLOW],           # L1,L2,L11
    "momentum_agent": [LAYER_RSI, LAYER_STOCHASTIC, LAYER_SENTIMENT],     # L3,L4,L8
    "structure_agent":[LAYER_ORDER_BLOCK, LAYER_OTE, LAYER_IDM_FVG, LAYER_MASTER_CALL],  # L5,L14,L15,L16
    "sweep_agent":    [LAYER_MTF, LAYER_ULTRA_SCALPER, LAYER_PRIME_SWING],# L7,L9,L10
    "risk_agent":     [LAYER_VOLUME, LAYER_ATR_CONTEXT, LAYER_TIMESTOP, LAYER_VWAP],     # L6,L13,L17,L12
}
