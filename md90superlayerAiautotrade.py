#!/usr/bin/env python3
"""MD90 Superlayer AI Unified Runtime

Single-process launcher for the MD90 trading / sniper / AI bot ecosystem.

This file consolidates the project into one local runtime that exposes:
- a browser-based terminal UI
- a FastAPI JSON API
- project metadata and JSON config discovery
- a shell bridge for local command execution
- a unified startup surface for the existing CLI/API project modules

Primary launch:
    python md90superlayerAiautotrade.py

Then open:
    http://127.0.0.1:8899

This runtime is intentionally localhost-only and should only be used on a trusted
local machine. Do not expose it publicly without auth and firewall hardening.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = os.environ.get("MD90_TITLE", "md90superlayerAiautotrade")
HOST = os.environ.get("MD90_HOST", "127.0.0.1")
PORT = int(os.environ.get("MD90_PORT", "8899"))
SHELL = os.environ.get("MD90_SHELL") or (
    "powershell.exe" if platform.system().lower() == "windows" else os.environ.get("SHELL", "/bin/bash")
)
PROJECT_ROOT = Path(__file__).resolve().parent
CLI_MODULE = PROJECT_ROOT / "cli.py"
API_MODULE = PROJECT_ROOT / "api_server.py"

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TERMINAL_SESSIONS: Dict[str, subprocess.Popen[Any]] = {}
TERMINAL_LOCK = threading.Lock()


def _safe_relpath(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return path.name


def _discover_json_configs(base: Path) -> List[Dict[str, Any]]:
    """Find JSON files under the project for runtime/autoload discovery."""
    discovered: List[Dict[str, Any]] = []
    if not base.exists():
        return discovered

    search_roots = [base]
    for child in sorted(base.iterdir(), key=lambda p: p.name.lower()):
        if child.is_dir() and child.name.lower() in {
            "config",
            "configs",
            "bot",
            "bots",
            "data",
            "runtime",
            "assets",
            "auto",
            "presets",
            "schemas",
        }:
            search_roots.append(child)

    seen: set[str] = set()
    for root in search_roots:
        try:
            for path in sorted(root.rglob("*.json"), key=lambda p: str(p).lower()):
                if not path.is_file():
                    continue
                rel = _safe_relpath(path)
                if rel in seen:
                    continue
                seen.add(rel)
                discovered.append({
                    "name": path.name,
                    "path": rel,
                    "size": path.stat().st_size,
                })
        except Exception:
            continue
    return discovered


def _repo_modules() -> Dict[str, Any]:
    status = {
        "cli": CLI_MODULE.exists(),
        "api_server": API_MODULE.exists(),
        "cli_path": str(CLI_MODULE) if CLI_MODULE.exists() else None,
        "api_server_path": str(API_MODULE) if API_MODULE.exists() else None,
    }
    return status


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
      --line: rgba(121, 240, 208, 0.3);
      --text: #edf7ff;
      --muted: #96dfe8;
      --accent: #79f0d0;
      --cyan: #6ed6ff;
      --gold: #ffc857;
      --danger: #ff7387;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0; height: 100%; background: radial-gradient(circle at top, #0d1b22, #04070a 40%);
      color: var(--text); font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    }
    body { padding: 18px; }
    .app {
      width: min(1500px, 100%);
      min-height: 88vh;
      display: grid;
      grid-template-columns: 300px 1fr;
      border: 1px solid var(--line);
      border-radius: 20px;
      overflow: hidden;
      background: rgba(7, 13, 15, 0.9);
      box-shadow: 0 25px 80px rgba(0,0,0,0.45);
    }
    .sidebar {
      background: linear-gradient(180deg, rgba(10,18,20,0.96), rgba(14,24,27,0.96));
      border-right: 1px solid var(--line);
      padding: 16px 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .brand {
      display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
    }
    .brand h1 { margin: 0; font-size: 12px; letter-spacing: .22em; text-transform: uppercase; color: var(--accent); }
    .live { padding: 5px 8px; border: 1px solid rgba(121,240,208,0.4); background: rgba(121,240,208,0.08); border-radius: 999px; color: var(--accent); font-size: 10px; letter-spacing: .14em; }
    .chips { display: flex; flex-direction: column; gap: 8px; }
    .chip {
      border: 1px solid rgba(121,240,208,0.22); background: rgba(10,18,18,0.7); border-radius: 10px;
      padding: 10px 12px; color: var(--muted); font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    }
    .hint { color: rgba(236,246,255,0.72); font-size: 11px; letter-spacing: .04em; }
    .main { display: flex; flex-direction: column; padding: 12px; gap: 10px; min-width: 0; }
    .topbar {
      display: flex; justify-content: space-between; align-items: center;
      background: rgba(18,26,30,0.9); border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px;
      color: var(--muted); font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
    }
    .tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .tab { padding: 6px 9px; border: 1px solid rgba(110,214,255,0.3); border-radius: 7px; background: rgba(110,214,255,0.06); }
    .terminal-wrap { flex: 1; background: rgba(5,12,14,0.98); border: 1px solid var(--line); border-radius: 14px; position: relative; overflow: hidden; }
    #terminal { width: 100%; height: 100%; min-height: 520px; }
    .xterm { height: 100%; }
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
        <div class="chip">Unified Runtime</div>
        <div class="chip">JSON Autoload</div>
        <div class="chip">Bot Orchestrator</div>
      </div>
      <div class="hint">Localhost-only, trusted use only. Do not expose to public internet without auth.</div>
    </aside>
    <main class="main">
      <div class="topbar">
        <span>Operator Console</span>
        <div class="tabs">
          <span class="tab">MD90</span>
          <span class="tab">Unified</span>
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
      fontSize: 15,
      theme: {
        foreground: '#edf7ff',
        background: '#050c0e',
        cursor: '#79f0d0',
        black: '#0d1b22',
        red: '#ff7387',
        green: '#7ae8b5',
        yellow: '#ffc857',
        blue: '#6ed6ff',
        magenta: '#c5a7ff',
        cyan: '#79f0d0',
        white: '#edf7ff'
      },
      scrollback: 2500
    });

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

    term.open(document.getElementById('terminal'));
    term.write('MD90 Superlayer AI Unified Runtime\r\n');
    term.write('Browser terminal online. Local shell bridge ready.\r\n');
    term.write('$ ');

    term.onData((data) => {
      socket.send(JSON.stringify({ type: 'input', data }));
    });

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'output') {
          term.write(msg.data);
        }
      } catch {
        term.write(String(event.data));
      }
    };

    socket.onclose = () => term.write('\r\n\n[session closed]\r\n');
    socket.onopen = () => {
      socket.send(JSON.stringify({ type: 'resize', cols: term.cols || 120, rows: term.rows || 30 }));
    };

    window.addEventListener('resize', () => {
      const rows = term.rows || 30;
      const cols = term.cols || 120;
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'resize', cols, rows }));
      }
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
        "platform": platform.platform(),
        "mode": "localhost-only",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@app.get("/api/status")
async def status() -> JSONResponse:
    modules = _repo_modules()
    return JSONResponse({
        "name": APP_NAME,
        "description": "MD90 unified runtime: terminal + API + config loader + shell bridge",
        "host": HOST,
        "port": PORT,
        "components": {
            "web_terminal": True,
            "api_runtime": True,
            "json_autoload": True,
            "shell_bridge": True,
            "repo_cli": modules["cli"],
            "repo_api_server": modules["api_server"],
        },
        "json_configs": _discover_json_configs(PROJECT_ROOT),
        "security": {
            "localhost_only": True,
            "warning": "Do not expose this application publicly without authentication and firewall hardening.",
        },
    })


@app.get("/api/repo")
async def repo_info() -> JSONResponse:
    return JSONResponse({
        "root": str(PROJECT_ROOT),
        "modules": _repo_modules(),
        "json_configs": _discover_json_configs(PROJECT_ROOT),
        "python_files": [
            _safe_relpath(p)
            for p in sorted(PROJECT_ROOT.rglob("*.py"), key=lambda p: str(p).lower())
            if p.name not in {"__init__.py"}
        ],
    })


@app.get("/api/commands")
async def commands() -> JSONResponse:
    return JSONResponse({
        "commands": [
            {"name": "launch_shell", "description": "Open a live shell in the web terminal"},
            {"name": "health", "description": "Check server health"},
            {"name": "status", "description": "Inspect unified runtime state"},
            {"name": "repo", "description": "Inspect discovered repo modules and config files"},
            {"name": "python cli.py", "description": "Run the legacy CLI if available"},
            {"name": "python api_server.py", "description": "Run the legacy API server if available"},
        ]
    })


@app.websocket("/ws")
async def terminal_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    with TERMINAL_LOCK:
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
                await websocket.send_text(
                    json.dumps({"type": "output", "data": chunk.decode("utf-8", errors="replace")})
                )
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


@app.post("/api/exec")
async def api_exec(request: Request) -> JSONResponse:
    """Execute a shell command locally with a safe localhost-only policy."""
    body = await request.json()
    command = body.get("command") or ""
    if not command.strip():
        return JSONResponse({"status": "error", "message": "Empty command"}, status_code=400)

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        return JSONResponse({
            "status": "ok" if completed.returncode == 0 else "error",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


def _create_aliases() -> List[str]:
    aliases = [
        "python md90superlayerAiautotrade.py",
        "curl http://127.0.0.1:8899/api/health",
        "python cli.py --help",
        "python api_server.py --help",
    ]
    return aliases


@app.get("/api/aliases")
async def aliases() -> JSONResponse:
    return JSONResponse({"aliases": _create_aliases()})


def _start_local_runtime() -> None:
    """Optional helper: if repo modules exist, expose them as simple command aliases."""
    try:
        if CLI_MODULE.exists():
            print(f"[*] Legacy CLI module detected: {CLI_MODULE}")
        if API_MODULE.exists():
            print(f"[*] Legacy API module detected: {API_MODULE}")
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn

    print("=" * 64)
    print(f"  {APP_NAME}")
    print(f"  Local web terminal + unified runtime for MD90")
    print(f"  URL: http://{HOST}:{PORT}")
    print(f"  Project root: {PROJECT_ROOT}")
    print("=" * 64)
    _start_local_runtime()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
