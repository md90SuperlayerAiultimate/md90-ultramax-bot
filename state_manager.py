"""
MD90 v4 — State Manager
Thread-safe shared state antara engine dan dashboard.
"""
import json, threading, os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

WITA = timezone(timedelta(hours=8))

class StateManager:
    FILE = Path("/tmp/md90_v4_state.json")
    DEFAULT = {
        "status": "STOPPED",
        "wita_time": "",
        "pairs": {},       # per-pair state
        "equity": 0.0,
        "balance": 0.0,
        "daily_pnl": 0.0,
        "session": "OTHER",
        "regime": "UNDEFINED",
        "drawdown_pct": 0.0,
        "positions": [],
        "trade_history": [],
        "errors": [],
        "uptime_start": None,
    }

    def __init__(self):
        self._s = dict(self.DEFAULT)
        self._s["uptime_start"] = str(datetime.now(WITA))
        self._lock = threading.Lock()

    def update(self, key: str, value: Any):
        with self._lock:
            self._s[key] = value
            self._save()

    def update_pair(self, pair: str, data: dict):
        with self._lock:
            self._s["pairs"][pair] = data
            self._save()

    def get(self, key=None):
        with self._lock:
            return dict(self._s) if key is None else self._s.get(key)

    def append_trade(self, trade: dict):
        with self._lock:
            hist = self._s.get("trade_history", [])
            hist.append(trade)
            if len(hist) > 500:
                hist = hist[-500:]
            self._s["trade_history"] = hist
            self._save()

    def _save(self):
        try:
            with open(self.FILE, "w") as f:
                json.dump(self._s, f, default=str, indent=2)
        except:
            pass

    @classmethod
    def load(cls) -> dict:
        try:
            if cls.FILE.exists():
                return json.loads(cls.FILE.read_text())
        except:
            pass
        return dict(cls.DEFAULT)
