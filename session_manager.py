"""
MD90 — Session Manager
Port EXACT dari MQL5 MD90_COMPLETE_ANALYSIS Section 14 + 16 risk multipliers.

Sessions (GMT):
  Asia         00:00 – 09:00  (WITA: 08:00 – 17:00)
  London       07:00 – 16:00  (WITA: 15:00 – 00:00)
  NewYork      13:00 – 22:00  (WITA: 21:00 – 06:00)
  Overlap_LN   13:00 – 16:00  (WITA: 21:00 – 00:00) ← highest priority
  Overlap_AL   07:00 – 09:00  (WITA: 15:00 – 17:00)
  Night        22:00 – 02:00  (WITA: 06:00 – 10:00)
  Weekend      Sat/Sun
  Other        outside all sessions
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import IntEnum
from typing import Optional


WITA = timezone(timedelta(hours=8))   # GMT+8


class TradingSession(IntEnum):
    ASIA        = 1
    LONDON      = 2
    NEWYORK     = 3
    OVERLAP_LN  = 4   # London–NY overlap (best session)
    OVERLAP_AL  = 5   # Asia–London overlap
    NIGHT       = 6
    WEEKEND     = 7
    OTHER       = 8


# ── Session risk multipliers (port dari MQL5 Section 16) ─────────────
SESSION_RISK_MULT = {
    TradingSession.ASIA:       0.5,
    TradingSession.LONDON:     1.5,
    TradingSession.NEWYORK:    1.8,
    TradingSession.OVERLAP_LN: 2.0,
    TradingSession.OVERLAP_AL: 1.2,
    TradingSession.NIGHT:      0.3,
    TradingSession.WEEKEND:    0.0,
    TradingSession.OTHER:      0.5,
}

SESSION_NAMES = {
    TradingSession.ASIA:       "ASIA",
    TradingSession.LONDON:     "LONDON",
    TradingSession.NEWYORK:    "NY",
    TradingSession.OVERLAP_LN: "LN_OVERLAP",
    TradingSession.OVERLAP_AL: "AL_OVERLAP",
    TradingSession.NIGHT:      "NIGHT",
    TradingSession.WEEKEND:    "WEEKEND",
    TradingSession.OTHER:      "OTHER",
}


@dataclass
class SessionState:
    session:       TradingSession = TradingSession.OTHER
    prev_session:  TradingSession = TradingSession.OTHER
    is_active:     bool           = False
    is_overlap:    bool           = False
    risk_mult:     float          = 0.5
    name:          str            = "OTHER"
    wita_hour:     int            = 0


class SessionManager:
    """
    Session detector dengan WITA timezone awareness.
    WITA = UTC+8. Session boundaries dalam GMT.
    """

    def detect(self, dt: Optional[datetime] = None) -> SessionState:
        """
        Detect session untuk waktu dt (default: sekarang UTC).
        """
        if dt is None:
            dt = datetime.now(timezone.utc)

        # Convert to GMT (UTC)
        gmt_h = dt.hour
        gmt_m = dt.minute
        gmt_t = gmt_h * 60 + gmt_m   # minutes since midnight GMT
        dow   = dt.weekday()           # 0=Mon, 6=Sun

        wita_h = (dt.astimezone(WITA)).hour

        prev = TradingSession.OTHER

        # Weekend
        if dow >= 5:   # Sat=5, Sun=6
            return SessionState(
                session=TradingSession.WEEKEND, prev_session=prev,
                is_active=False, is_overlap=False,
                risk_mult=0.0, name="WEEKEND", wita_hour=wita_h)

        # ── Priority order (highest first) ────────────────────────────
        # Overlap LN: GMT 13:00–16:00
        if 780 <= gmt_t < 960:
            sess = TradingSession.OVERLAP_LN
            return SessionState(
                session=sess, prev_session=prev,
                is_active=True, is_overlap=True,
                risk_mult=SESSION_RISK_MULT[sess],
                name=SESSION_NAMES[sess], wita_hour=wita_h)

        # Overlap AL: GMT 07:00–09:00
        if 420 <= gmt_t < 540:
            sess = TradingSession.OVERLAP_AL
            return SessionState(
                session=sess, prev_session=prev,
                is_active=True, is_overlap=True,
                risk_mult=SESSION_RISK_MULT[sess],
                name=SESSION_NAMES[sess], wita_hour=wita_h)

        # Asia: GMT 00:00–09:00
        if 0 <= gmt_t < 540:
            sess = TradingSession.ASIA
            return SessionState(
                session=sess, prev_session=prev,
                is_active=True, is_overlap=False,
                risk_mult=SESSION_RISK_MULT[sess],
                name=SESSION_NAMES[sess], wita_hour=wita_h)

        # London: GMT 07:00–16:00 (non-overlap portion: 09:00–13:00)
        if 540 <= gmt_t < 780:
            sess = TradingSession.LONDON
            return SessionState(
                session=sess, prev_session=prev,
                is_active=True, is_overlap=False,
                risk_mult=SESSION_RISK_MULT[sess],
                name=SESSION_NAMES[sess], wita_hour=wita_h)

        # NY: GMT 13:00–22:00 (non-overlap portion: 16:00–22:00)
        if 960 <= gmt_t < 1320:
            sess = TradingSession.NEWYORK
            return SessionState(
                session=sess, prev_session=prev,
                is_active=True, is_overlap=False,
                risk_mult=SESSION_RISK_MULT[sess],
                name=SESSION_NAMES[sess], wita_hour=wita_h)

        # Night: GMT 22:00–02:00
        if gmt_t >= 1320 or gmt_t < 120:
            sess = TradingSession.NIGHT
            return SessionState(
                session=sess, prev_session=prev,
                is_active=True, is_overlap=False,
                risk_mult=SESSION_RISK_MULT[sess],
                name=SESSION_NAMES[sess], wita_hour=wita_h)

        return SessionState(
            session=TradingSession.OTHER, prev_session=prev,
            is_active=False, is_overlap=False,
            risk_mult=0.5, name="OTHER", wita_hour=wita_h)
