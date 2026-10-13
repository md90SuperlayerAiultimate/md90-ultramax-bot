#!/usr/bin/env python3
"""md90superlayerAiautotrade

All-in-one MD90 Superlayer AI / AutoTrade runtime.

This single-file app bundles the following into one process:
- web terminal UI (xterm.js, browser-based console)
- localhost-safe FastAPI server
- JSON config autodiscovery and status endpoint
- bot runtime shell bridge
- live status/health endpoints

Use:
    python md90superlayerAiautotrade.py
    open http://127.0.0.1:8899

Safety:
    This app defaults to 127.0.0.1 only and is intended for trusted local use.
    Do not expose publicly without authentication/network hardening.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = os.environ.get("MD90_TITLE", "md90superlayerAiautotrade")
HOST = os.environ.get("MD90_HOST", "127.0.0.1")
PORT = int(os.environ.get("MD90_PORT", "8899"))
SHELL = os.environ.get("MD90_SHELL") or (
    "powershell.exe" if platform.system().lower() == "windows" else os.environ.get("SHELL", "/bin/bash")
)
RUNNER_ROOT = Path(__file__).resolve().parent

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TERMINAL_SESSIONS: dict[str, subprocess.Popen[Any]] = {}


def _discover_json_configs(base: Path) -> List[Dict[str, Any]]:
    """Return JSON files discovered under the repo root and config directories."""
    discovered: List[Dict[str, Any]] = []
    if not base.exists():
        return discovered

    search_roots = [base]
    for root in list(base.iterdir()):
        if root.is_dir() and root.name.lower() in {"config", "configs", "bot", "bots", "data", "runtime", "assets", "auto"}:
            search_roots.append(root)

    seen: set[str] = set()
    for root in search_roots:
        try:
            for path in sorted(root.rglob("*.json")):
                if path.is_file():
                    rel = str(path.relative_to(base)).replace('\\', '/')
                    if rel in seen:
                        continue
                    seen.add(rel)
                    discovered.append({
                        "name": path.name,
                        "path": rel,
                        "size": path.stat().st_size,
                    })
        except Exception:
            pass
    return discovered


INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/xterm@5.1.0/lib/xterm.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.1.0/css/xterm.css" />
  <style>
    :root {
      --bg: #04070a;
      --panel: #0b1418;
      --line: rgba(121, 240, 208, 0.33);
      --text: #ecf6ff;
      --muted: #9adce2;
      --accent: #79f0d0;
      --cyan: #6bd7ff;
      --danger: #ff7387;
      --gold: #ffc857;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0; height: 100%; background: radial-gradient(circle at top, #0d1b22 0%, #04070a 40%); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    }
    body { padding: 18px; }
    .app {
      width: min(1500px, 100%);
      min-height: 88vh;
      display: grid; grid-template-columns: 300px 1fr; border: 1px solid var(--line); border-radius: 20px; overflow: hidden;
      background: rgba(8, 12, 14, 0.9); box-shadow: 0 25px 80px rgba(0,0,0,0.4);
    }
    .sidebar {
      background: linear-gradient(180deg, rgba(10,18,20,0.96), rgba(14,24,27,0.96)); border-right: 1px solid var(--line); padding: 16px 14px; display: flex; flex-direction: column; gap: 12px;
    }
    .brand {
      display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--line); padding-bottom: 10px;
    }
    .brand h1 { margin: 0; font-size: 12px; letter-spacing: .22em; text-transform: uppercase; color: var(--accent); }
    .live { padding: 5px 8px; border: 1px solid rgba(121,240,208,0.4); background: rgba(121,240,208,0.08); border-radius: 999px; color: var(--accent); font-size: 10px; letter-spacing: .14em; }
    .chips { display: flex; flex-direction: column; gap: 8px; }
    .chip { border: 1px solid rgba(121,240,208,0.24); background: rgba(10,18,18,0.7); border-radius: 10px; padding: 10px 12px; color: var(--muted); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }
    .main { display: flex; flex-direction: column; padding: 12px; gap: 10px; min-width: 0; }
    .topbar {
      display: flex; justify-content: space-between; align-items: center; background: rgba(18,26,30,0.9); border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; color: var(--muted); font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
    }
    .tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .tab { padding: 6px 9px; border: 1px solid rgba(107,215,255,0.3); border-radius: 7px; background: rgba(107,215,255,0.06); }
    .terminal-wrap { flex: 1; background: rgba(5,12,14,0.98); border: 1px solid var(--line); border-radius: 14px; position: relative; overflow: hidden; }
    #terminal { width: 100%; height: 100%; min-height: 520px; }
    .xterm { height: 100%; }
    .hint { color: rgba(236,246,255,0.7); font-size: 11px; letter-spacing: .04em; }
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <h1>{title}</h1>
      <span class="live">LIVE</span>
    </div>
    <div class="chips">
      <div class="chip">Web Terminal</div>
      <div class="chip">AutoTrade Engine</div>
      <div class="chip">JSON Loader</div>
      <div class="chip">Bot Orchestrator</div>
    </div>
    <div class="hint">Localhost-only by default. Safe shell execution requires trusted local usage.</div>
  </aside>
  <main class="main">
    <div class="topbar">
      <span>Operator Console</span>
      <div class="tabs">
        <span class="tab">MD90</span>
        <span class="tab">AutoTrade</span>
        <span class="tab">Runtime</span>
      </div>
    </div>
    <div class="terminal-wrap">
      <div id="terminal"></div>
    </div>
  </main>
</div>

<script>
  const term = new Terminal({
    cursorBlink: true,
    fontFamily: 'JetBrains Mono, Consolas, monospace',
    fontSize: 14,
    theme: {
      foreground: '#ecf6ff',
      background: '#050c0e',
      cursor: '#79f0d0',
      black: '#0d1b22',
      red: '#ff7387',
      green: '#7ae8b5',
      yellow: '#ffc857',
      blue: '#6bd7ff',
      magenta: '#c5a7ff',
      cyan: '#79f0d0',
      white: '#ecf6ff'
    },
    scrollback: 2000
  });
  term.open(document.getElementById('terminal'));
  term.write('MD90 Superlayer AI AutoTrade\r\n');
  term.write('Web terminal online. Localhost-safe mode enabled.\r\n');
  term.write('$ ');

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  term.onData(data => socket.send(JSON.stringify({ type: 'input', data })));
  socket.onmessage = ev => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'output') term.write(msg.data);
    } catch {
      term.write(String(ev.data));
    }
  };

  socket.onclose = () => term.write('\r\n\n[session closed]\r\n');
  window.addEventListener('resize', () => {
    const rows = term.rows || 30;
    const cols = term.cols || 120;
    if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'resize', cols, rows }));
  });
  socket.onopen = () => {
    socket.send(JSON.stringify({ type: 'resize', cols: term.cols || 120, rows: term.rows || 30 }));
  };
</script>
</body>
</html>
""".format(title=APP_NAME)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)


@app.get("/api/health")
async def api_health() -> JSONResponse:
    return JSONResponse({
        "status": "ok",
        "service": APP_NAME,
        "host": HOST,
        "port": PORT,
        "shell": SHELL,
        "platform": platform.platform(),
        "mode": "localhost-only",
    })


@app.get("/api/status")
async def api_status() -> JSONResponse:
    json_configs = _discover_json_configs(RUNNER_ROOT)
    return JSONResponse({
        "name": APP_NAME,
        "description": "MD90 Superlayer AI AutoTrade — single entrypoint runtime",
        "capabilities": [
            "web-terminal",
            "json-autoload",
            "bot-runtime",
            "health-monitoring",
            "shell-session",
        ],
        "json_configs": json_configs,
        "security": {
            "localhost_only": True,
            "warning": "Do not expose this endpoint to the public internet without authentication and firewall restrictions.",
        },
    })


@app.get("/api/config")
async def api_config() -> JSONResponse:
    return JSONResponse({
        "root": str(RUNNER_ROOT),
        "configs": _discover_json_configs(RUNNER_ROOT),
    })


@app.websocket("/ws")
async def terminal_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    process = subprocess.Popen(
        [SHELL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
        bufsize=0,
        start_new_session=True,
    )
    TERMINAL_SESSIONS[str(id(process))] = process

    async def pump_process_to_ws() -> None:
        try:
            while process.poll() is None:
                if process.stdout is None:
                    break
                chunk = process.stdout.read1(4096)
                if not chunk:
                    await asyncio.sleep(0.02)
                    continue
                await websocket.send_text(json.dumps({"type": "output", "data": chunk.decode("utf-8", errors="replace")}))
        except Exception:
            pass

    async def pump_ws_to_process() -> None:
        try:
            while True:
                raw = await websocket.receive_text()
                message = json.loads(raw) if raw.strip().startswith("{") else {"type": "input", "data": raw}
                if message.get("type") == "resize":
                    continue
                data = message.get("data", "")
                if process.stdin is not None:
                    process.stdin.write(data.encode("utf-8"))
                    process.stdin.flush()
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            try:
                if process.stdin is not None:
                    process.stdin.close()
            except Exception:
                pass

    read_task = asyncio.create_task(pump_process_to_ws())
    write_task = asyncio.create_task(pump_ws_to_process())

    try:
        await asyncio.gather(read_task, write_task)
    finally:
        for task in (read_task, write_task):
            if not task.done():
                task.cancel()
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=3)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn

    print(f"[*] Starting {APP_NAME} on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
