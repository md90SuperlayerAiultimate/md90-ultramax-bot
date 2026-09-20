"""
MD90 ULTIMATE FUSION v4 — Config
Pure Python, no MT5, no MetaTrader.
Exchange: Binance (ccxt) for OHLCV + signal engine.
Execution: Polymarket CLOB (prediction markets) OR Binance spot.
"""
import os
from dotenv import load_dotenv
load_dotenv()

CFG = {
    # ── EXCHANGE (data source) ────────────────────────────────────
    "exchange":   os.getenv("EXCHANGE",   "binance"),
    "api_key":    os.getenv("API_KEY",    ""),
    "api_secret": os.getenv("API_SECRET", ""),

    # ── MARKET ───────────────────────────────────────────────────
    "symbol":     os.getenv("SYMBOL",     "BTC/USDT"),
    "timeframe":  os.getenv("TIMEFRAME",  "15m"),
    "symbols":    os.getenv("SYMBOLS",    "BTC/USDT,ETH/USDT,BNB/USDT").split(","),

    # ── MODE ─────────────────────────────────────────────────────
    "mode":     os.getenv("MODE",     "polymarket"),  # polymarket | binance | backtest
    "dry_run":  os.getenv("DRY_RUN",  "true").lower() == "true",
    "loop_sec": int(os.getenv("LOOP_SEC", "60")),

    # ── SIGNAL THRESHOLDS (exact MQL5 port) ──────────────────────
    "fusion_score_min": float(os.getenv("FUSION_SCORE_MIN", "0.55")),
    "confidence_min":   float(os.getenv("CONFIDENCE_MIN",   "75.0")),
    "rr_minimum":       float(os.getenv("RR_MINIMUM",       "2.0")),
    "composite_allin":  float(os.getenv("COMPOSITE_ALLIN",  "0.72")),
    "composite_wait":   float(os.getenv("COMPOSITE_WAIT",   "0.55")),

    # ── RISK ─────────────────────────────────────────────────────
    "start_equity":   float(os.getenv("START_EQUITY",   "2000")),
    "base_risk":      float(os.getenv("BASE_RISK",       "0.01")),
    "max_risk":       float(os.getenv("MAX_RISK",        "0.03")),
    "min_risk":       float(os.getenv("MIN_RISK",        "0.003")),
    "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS",  "0.05")),
    "kelly_fraction": float(os.getenv("KELLY_FRACTION",  "0.25")),
    "max_positions":  int(os.getenv("MAX_POSITIONS",     "3")),

    # ── POLYMARKET ────────────────────────────────────────────────
    "poly_private_key":    os.getenv("POLY_PRIVATE_KEY",   ""),
    "poly_api_key":        os.getenv("POLY_API_KEY",       ""),
    "poly_api_secret":     os.getenv("POLY_API_SECRET",    ""),
    "poly_api_passphrase": os.getenv("POLY_PASSPHRASE",    ""),
    "poly_min_liquidity":  float(os.getenv("POLY_MIN_LIQ", "5000")),
    "poly_min_volume":     float(os.getenv("POLY_MIN_VOL", "10000")),
    "poly_max_spread":     float(os.getenv("POLY_MAX_SPREAD", "0.05")),
    "poly_keywords":       os.getenv("POLY_KEYWORDS",
                           "btc,bitcoin,eth,ethereum,crypto,price,above,below").split(","),
    "poly_min_size_usd":   float(os.getenv("POLY_MIN_SIZE", "10")),
    "poly_max_size_usd":   float(os.getenv("POLY_MAX_SIZE", "500")),

    # ── BACKTEST ──────────────────────────────────────────────────
    "bt_start":   os.getenv("BT_START",  "2024-01-01"),
    "bt_end":     os.getenv("BT_END",    "2024-12-31"),
    "bt_capital": float(os.getenv("BT_CAPITAL", "10000")),

    # ── NOTIFICATIONS ─────────────────────────────────────────────
    "telegram_token":   os.getenv("TELEGRAM_TOKEN",   ""),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),

    # ── TIMEZONE ──────────────────────────────────────────────────
    "mode_exec": os.getenv("MODE_EXEC", "binance"),  # for backtest cost model
    "timezone": "Asia/Makassar",
}
