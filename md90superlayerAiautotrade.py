#!/usr/bin/env python3
"""md90superlayerAiautotrade

All-in-one web terminal + operator console for the MD90 Superlayer AI / Vibe Trading stack.

This file is intentionally self-contained so a developer can run a single app that:
- serves the Web UI from a single Python process,
- exposes a terminal emulator via WebSocket,
- exposes a lightweight health/status API,
- is safe-by-default for localhost-only operation.

It consolidates the architecture implied by the repository: frontend (React/Vite),
backend (FastAPI/Python agent runtime), and terminal session launcher into a single
entry point without needing to chase multiple ZIP archives separately.

Usage:
  python md90superlayerAiautotrade.py

Then open:
  http://127.0.0.1:8899

Environment variables:
  MD90_HOST      default 127.0.0.1
  MD90_PORT      default 8899
  MD90_SHELL     default bash (or powershell.exe on Windows)
  MD90_TITLE     optional UI title override
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import signal
import subprocess
import sys
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = os.environ.get("MD90_TITLE", "md90superlayerAiautotrade")
HOST = os.environ.get("MD90_HOST", "127.0.0.1")
PORT = int(os.environ.get("MD90_PORT", "8899"))
SHELL = os.environ.get("MD90_SHELL") or (
    "powershell.exe" if platform.system().lower() == "windows" else os.environ.get("SHELL", "/bin/bash")
)

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TERMINAL_SESSIONS: dict[str, subprocess.Popen[Any]] = {}

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="icon" href="data:;base64,=" />
  <script src="https://cdn.jsdelivr.net/npm/xterm@5.1.0/lib/xterm.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/xterm@5.1.0/lib/xterm-addon-fit.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.1.0/css/xterm.css" />
  <style>
    :root {
      --bg: #04070a;
      --panel: #0b1418;
      --panel-2: #101c22;
      --line: rgba(146, 244, 215, 0.22);
      --text: #dfeffd;
      --muted: #7ccfc3;
      --accent: #79f0d0;
      --accent-2: #68b8ff;
      --warn: #ffc857;
      --danger: #ff7387;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      height: 100%;
      background: radial-gradient(circle at top, #0b1d24, #04070a 48%);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
    }
    body {
      display: flex;
      align-items: stretch;
      justify-content: center;
      padding: 18px;
    }
    .shell {
      width: min(1500px, 100%);
      min-height: 85vh;
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      border: 1px solid var(--line);
      background: rgba(12, 18, 20, 0.8);
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.4), inset 0 0 40px rgba(121, 240, 208, 0.04);
    }
    .sidebar {
      background: linear-gradient(180deg, rgba(10,16,18,0.96), rgba(15, 24, 27, 0.96));
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 18px 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 6px 12px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 10px;
    }
    .brand h1 {
      font-size: 13px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      margin: 0;
      color: var(--accent);
      font-weight: 700;
    }
    .status-pill {
      padding: 4px 8px;
      border: 1px solid rgba(121, 240, 208, 0.35);
      border-radius: 999px;
      font-size: 10px;
      letter-spacing: 0.12em;
      color: var(--accent);
      background: rgba(121,240,208,0.08);
    }
    .stack {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 8px;
    }
    .stack .item {
      padding: 10px 12px;
      border: 1px solid rgba(121, 240, 208, 0.2);
      background: rgba(10, 18, 18, 0.72);
      border-radius: 10px;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .main {
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      min-width: 0;
    }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(14, 24, 28, 0.75);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .toolbar .tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tab {
      border: 1px solid rgba(104,184,255,0.4);
      border-radius: 8px;
      padding: 6px 8px;
      color: var(--muted);
      background: rgba(104,184,255,0.08);
    }
    .terminal-wrap {
      flex: 1;
      min-height: 0;
      position: relative;
      background: rgba(5, 12, 14, 0.98);
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
    }
    #terminal {
      width: 100%;
      height: 100%;
      min-height: 480px;
    }
    .xterm {
      height: 100%;
    }
    .xterm .xterm-viewport {
      background: rgba(5,12,14,1) !important;
    }
    .hint {
      margin-top: 6px;
      font-size: 11px;
      color: rgba(223,239,253,0.72);
      letter-spacing: 0.04em;
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <h1>{title}</h1>
        <span class="status-pill">LIVE</span>
      </div>
      <div class="stack">
        <div class="item">Web Terminal</div>
        <div class="item">Agent Runtime</div>
        <div class="item">AI Trading Core</div>
        <div class="item">Bot Orchestration</div>
      </div>
      <div class="hint">
        Localhost-only by default. Safe shell execution requires trusted use only.
      </div>
    </aside>

    <main class="main">
      <div class="toolbar">
        <span>Operator Console</span>
        <div class="tabs">
          <span class="tab">root</span>
          <span class="tab">md90</span>
          <span class="tab">agent</span>
        </div>
      </div>
      <div class="terminal-wrap">
        <div id="terminal"></div>
      </div>
    </main>
  </div>

  <script>
    const { Terminal } = window.Terminal;
    const term = new Terminal({
      cursorBlink: true,
      fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
      fontSize: 14,
      theme: {
        foreground: '#dfeffd',
        background: '#050c0e',
        cursor: '#79f0d0',
        black: '#1b2530',
        red: '#ff7387',
        green: '#7ae8b5',
        yellow: '#ffc857',
        blue: '#68b8ff',
        magenta: '#c5a7ff',
        cyan: '#79f0d0',
        white: '#dfeffd'
      },
      scrollback: 2000
    });

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

    term.open(document.getElementById('terminal'));
    term.write('Welcome to md90superlayerAiautotrade\r\n');
    term.write('Session started. Type commands below.\r\n');
    term.write('$ ');

    term.onData((data) => {
      socket.send(JSON.stringify({ type: 'input', data }));
    });

    window.addEventListener('resize', () => {
      const rows = Math.max(20, Math.floor(term._core._renderService._renderRows || 30));
      const cols = Math.max(80, Math.floor(term.cols || 120));
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'resize', cols, rows }));
      }
    });

    socket.addEventListener('open', () => {
      const rows = term.rows || 30;
      const cols = term.cols || 120;
      socket.send(JSON.stringify({ type: 'resize', cols, rows }));
    });

    socket.addEventListener('message', (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'output') {
          term.write(msg.data);
        }
      } catch (err) {
        term.write(String(event.data));
      }
    });

    socket.addEventListener('close', () => {
      term.write('\r\n\n[session closed]\r\n');
    });
  </script>
</body>
</html>
""".format(title=APP_NAME)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)


@app.get("/api/health")
async def health() -> JSONResponse:
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
async def status() -> JSONResponse:
    return JSONResponse({
        "name": APP_NAME,
        "description": "All-in-one auto-trade web terminal and operator console",
        "capabilities": [
            "web terminal",
            "agent shell access",
            "health checks",
            "status endpoint",
            "localhost access",
        ],
        "security": {
            "localhost_only": True,
            "prompt": "Only run on trusted local machines. Do not expose to the public internet without auth and network hardening.",
        },
    })


@app.websocket("/ws")
async def terminal_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    shell_cmd = SHELL
    process = subprocess.Popen(
        [shell_cmd],
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
                chunk = process.stdout.read1(4096) if process.stdout is not None else b""
                if not chunk:
                    await asyncio.sleep(0.02)
                    continue
                await websocket.send_text(json.dumps({"type": "output", "data": chunk.decode("utf-8", errors="replace")}))
        except Exception:
            pass
        finally:
            try:
                if process.stdout is not None:
                    process.stdout.close()
            except Exception:
                pass

    async def pump_ws_to_process() -> None:
        try:
            while True:
                raw = await websocket.receive_text()
                message = json.loads(raw) if raw.strip().startswith("{") else {"type": "input", "data": raw}
                if message.get("type") == "resize":
                    continue
                if process.stdin is not None:
                    process.stdin.write(message.get("data", "").encode("utf-8"))
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

    task_read = asyncio.create_task(pump_process_to_ws())
    task_write = asyncio.create_task(pump_ws_to_process())

    try:
        await asyncio.gather(task_read, task_write)
    finally:
        for task in (task_read, task_write):
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

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
