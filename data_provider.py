"""
MD90 Unified — Data Provider (v4-complete)
Fetch OHLCV dari CCXT, hitung semua indicators:
  EMA8, EMA21, EMA50, EMA200(daily)
  ADX + DI+/-
  RSI, MACD, Stochastic
  OBV, MFI, VWAP, VolumeRatio, BuyPressure
  Multi-TF snapshots
"""
import asyncio
from typing import Dict, List, Optional
import ccxt.async_support as ccxt

from md90_brain.types import MarketData


# ══════════════════════════════════════════════════════════════════════
# PURE-PYTHON INDICATOR LIBRARY
# ══════════════════════════════════════════════════════════════════════

def _ema(closes: List[float], period: int) -> float:
    if len(closes) < period:
        return 0.0
    k   = 2.0 / (period + 1)
    val = sum(closes[:period]) / period   # SMA seed
    for c in closes[period:]:
        val = c * k + val * (1 - k)
    return val


def _rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        (gains if d > 0 else losses).__add__  # trick to avoid branching
        if d > 0: gains  += d
        else:     losses -= d
    ag = gains  / period
    al = losses / period
    if al == 0:
        return 100.0
    return 100.0 - 100.0 / (1 + ag / al)


def _atr(highs, lows, closes, period=14) -> float:
    if len(closes) < period + 1:
        return (highs[-1] - lows[-1]) if highs and lows else 0.0
    trs = [max(highs[i]-lows[i],
               abs(highs[i]-closes[i-1]),
               abs(lows[i]-closes[i-1]))
           for i in range(1, len(closes))]
    return sum(trs[-period:]) / period


def _stochastic(highs, lows, closes, k_period=14, d_period=3):
    if len(closes) < k_period:
        return 50.0, 50.0
    ks = []
    for i in range(k_period-1, len(closes)):
        h = max(highs[i-k_period+1:i+1])
        l = min(lows[i-k_period+1:i+1])
        ks.append((closes[i]-l)/(h-l)*100 if h != l else 50.0)
    k_val = ks[-1]
    d_val = sum(ks[-d_period:]) / min(d_period, len(ks))
    return k_val, d_val


def _macd(closes, fast=12, slow=26, sig=9):
    if len(closes) < slow + sig:
        return 0.0, 0.0, 0.0
    fast_ema = [_ema(closes[:i+1], fast) for i in range(fast-1, len(closes))]
    slow_ema = [_ema(closes[:i+1], slow) for i in range(slow-1, len(closes))]
    n = min(len(fast_ema), len(slow_ema))
    hist_line = [fast_ema[-(n-i)] - slow_ema[-(n-i)] for i in range(n)]
    macd_main = hist_line[-1]
    if len(hist_line) >= sig:
        macd_sig_val = _ema(hist_line, sig)
    else:
        macd_sig_val = macd_main
    return macd_main, macd_sig_val, macd_main - macd_sig_val


def _adx(highs, lows, closes, period=14):
    """Returns (adx, di_plus, di_minus)"""
    if len(closes) < period + 2:
        return 0.0, 0.0, 0.0
    tr_list, dm_plus, dm_minus = [], [], []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i],
                 abs(highs[i]-closes[i-1]),
                 abs(lows[i]-closes[i-1]))
        up   = highs[i]  - highs[i-1]
        down = lows[i-1] - lows[i]
        dm_plus.append(up   if up > down and up > 0   else 0.0)
        dm_minus.append(down if down > up and down > 0 else 0.0)
        tr_list.append(tr)
    def smooth(lst, p):
        if len(lst) < p:
            return sum(lst)
        s = sum(lst[:p])
        for v in lst[p:]:
            s = s - s/p + v
        return s
    atr_s   = smooth(tr_list, period)
    dmp_s   = smooth(dm_plus,  period)
    dmm_s   = smooth(dm_minus, period)
    dip = 100 * dmp_s / atr_s if atr_s > 0 else 0.0
    dim = 100 * dmm_s / atr_s if atr_s > 0 else 0.0
    dx  = 100 * abs(dip-dim)/(dip+dim) if (dip+dim) > 0 else 0.0
    return dx, dip, dim


def _obv(closes, volumes) -> float:
    obv = 0.0
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv += volumes[i]
        elif closes[i] < closes[i-1]:
            obv -= volumes[i]
    return obv


def _mfi(highs, lows, closes, volumes, period=14) -> float:
    if len(closes) < period + 1:
        return 50.0
    pos_mf = neg_mf = 0.0
    for i in range(1, period+1):
        idx = len(closes) - period + i - 1
        tp     = (highs[idx] + lows[idx] + closes[idx]) / 3
        tp_prev= (highs[idx-1] + lows[idx-1] + closes[idx-1]) / 3
        mf = tp * volumes[idx]
        if tp > tp_prev:  pos_mf += mf
        else:              neg_mf += mf
    if neg_mf == 0:
        return 100.0
    return 100.0 - 100.0 / (1 + pos_mf / neg_mf)


def _vwap(highs, lows, closes, volumes) -> float:
    pv = tv = 0.0
    for h, l, c, v in zip(highs, lows, closes, volumes):
        tp = (h + l + c) / 3
        pv += tp * v
        tv += v
    return pv / tv if tv > 0 else (closes[-1] if closes else 0)


def _bollinger(closes: List[float], period: int = 20, dev: float = 2.0):
    """Returns (upper, mid, lower, width_pct)"""
    if len(closes) < period:
        m = closes[-1] if closes else 0.0
        return m * 1.002, m, m * 0.998, 0.4
    window = closes[-period:]
    mid    = sum(window) / period
    var    = sum((x - mid)**2 for x in window) / period
    std    = var**0.5
    upper  = mid + dev * std
    lower  = mid - dev * std
    wpct   = (upper - lower) / mid * 100 if mid > 0 else 0.0
    return upper, mid, lower, wpct


def _volume_ratio(volumes, period=20) -> float:
    if len(volumes) < 2:
        return 1.0
    avg = sum(volumes[-period-1:-1]) / min(period, len(volumes)-1)
    return volumes[-1] / avg if avg > 0 else 1.0


def _buy_pressure(opens, closes, period=14) -> float:
    n    = min(period, len(closes))
    bull = sum(1 for i in range(-n, 0) if closes[i] > opens[i])
    return (bull / n) * 100.0 if n > 0 else 50.0


# ══════════════════════════════════════════════════════════════════════
# DATA PROVIDER
# ══════════════════════════════════════════════════════════════════════

class DataProvider:

    def __init__(self, exchange_id="binance", api_key="", api_secret=""):
        params = {"enableRateLimit": True}
        if api_key:
            params["apiKey"] = api_key
            params["secret"] = api_secret
        self.exchange = getattr(ccxt, exchange_id)(params)

    async def close(self):
        await self.exchange.close()

    async def fetch(self, symbol: str, timeframe: str = "15m",
                    limit: int = 250) -> Optional[MarketData]:
        try:
            raw = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            print(f"[DataProvider] fetch error {symbol}/{timeframe}: {e}")
            return None

        if not raw or len(raw) < 60:
            print(f"[DataProvider] insufficient bars {symbol}/{timeframe}: {len(raw) if raw else 0}")
            return None

        opens   = [c[1] for c in raw]
        highs   = [c[2] for c in raw]
        lows    = [c[3] for c in raw]
        closes  = [c[4] for c in raw]
        volumes = [c[5] for c in raw]
        price   = closes[-1]

        # ── Core indicators ──────────────────────────────────────────
        atr     = _atr(highs, lows, closes)
        atr_avg = _atr(highs[:-14], lows[:-14], closes[:-14]) if len(closes) > 28 else atr
        atr_ratio = atr / atr_avg if atr_avg > 0 else 1.0

        ema8  = _ema(closes, 8)
        ema21 = _ema(closes, 21)
        ema50 = _ema(closes, 50)

        adx_val, dip, dim = _adx(highs, lows, closes)
        rsi_val = _rsi(closes)
        macd_m, macd_s, macd_h = _macd(closes)
        stk, std = _stochastic(highs, lows, closes)

        obv_val      = _obv(closes, volumes)
        obv_prev_val = _obv(closes[:-1], volumes[:-1]) if len(closes) > 1 else 0.0
        mfi_val      = _mfi(highs, lows, closes, volumes)
        vwap_val     = _vwap(highs, lows, closes, volumes)
        vol_ratio    = _volume_ratio(volumes)
        buy_p        = _buy_pressure(opens, closes)
        vol_spike    = vol_ratio > 1.5
        bb_u, bb_m, bb_l, bb_w = _bollinger(closes)

        # ── Multi-TF ─────────────────────────────────────────────────
        mtf_ema21: Dict[str, float] = {}
        mtf_close: Dict[str, float] = {}
        for tf in ["5m", "15m", "1h", "4h", "1d"]:
            if tf == timeframe:
                mtf_ema21[tf] = ema21
                mtf_close[tf] = price
                continue
            try:
                tf_raw = await self.exchange.fetch_ohlcv(symbol, tf, limit=50)
                if tf_raw and len(tf_raw) >= 22:
                    tc = [c[4] for c in tf_raw]
                    mtf_ema21[tf] = _ema(tc, 21)
                    mtf_close[tf] = tc[-1]
            except Exception:
                pass

        # ── Daily EMA200 ─────────────────────────────────────────────
        ema200_d = 0.0
        try:
            d_raw = await self.exchange.fetch_ohlcv(symbol, "1d", limit=220)
            if d_raw and len(d_raw) >= 200:
                dc = [c[4] for c in d_raw]
                ema200_d = _ema(dc, 200)
        except Exception:
            pass

        return MarketData(
            symbol=symbol, timeframe=timeframe,
            closes=closes, highs=highs, lows=lows,
            opens=opens, volumes=volumes,
            current_price=price,
            atr=atr, atr_avg=atr_avg, atr_ratio=atr_ratio,
            ema8=ema8, ema21=ema21, ema50=ema50, ema200_d=ema200_d,
            adx=adx_val, di_plus=dip, di_minus=dim,
            rsi=rsi_val,
            macd_main=macd_m, macd_signal=macd_s, macd_hist=macd_h,
            stoch_k=stk, stoch_d=std,
            obv=obv_val, obv_prev=obv_prev_val, mfi=mfi_val,
            vwap=vwap_val, volume_ratio=vol_ratio,
            buy_pressure=buy_p, volume_spike=vol_spike,
            bb_upper=bb_u, bb_mid=bb_m, bb_lower=bb_l, bb_width_pct=bb_w,
            mtf_ema21=mtf_ema21, mtf_close=mtf_close,
            session_active=True,
        )
