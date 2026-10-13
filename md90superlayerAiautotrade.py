#!/usr/bin/env python3
"""MD90 Superlayer AI Unified Runtime

Single-process launcher for the MD90 trading / sniper / AI bot ecosystem.
This file merges the terminal UI, local API surface, config discovery, shell
bridge, and repo module inspection into one local runtime.

Launch:
    python md90superlayerAiautotrade.py

Then open:
    http://127.0.0.1:8899
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shlex
import subprocess
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

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TERMINAL_SESSIONS: Dict[str, subprocess.Popen[Any]] = {}
STARTED_PROCESSES: Dict[str, subprocess.Popen[Any]] = {}


def _safe_relpath(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return path.name


def _discover_repo_files(pattern: str) -> List[str]:
    out: List[str] = []
    for path in sorted(PROJECT_ROOT.rglob(pattern), key=lambda p: str(p).lower()):
        if path.is_file():
            val = _safe_relpath(path)
            if val not in out:
                out.append(val)
    return out


def _discover_json_configs(base: Path) -> List[Dict[str, Any]]:
    """Return JSON files discovered under the project root."""
    if not base.exists():
        return []

    roots: List[Path] = [base]
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
            "json",
        }:
            roots.append(child)

    seen: set[str] = set()
    results: List[Dict[str, Any]] = []
    for root in roots:
        try:
            for path in sorted(root.rglob("*.json"), key=lambda p: str(p).lower()):
                if not path.is_file():
                    continue
                rel = _safe_relpath(path)
                if rel in seen:
                    continue
                seen.add(rel)
                results.append({
                    "name": path.name,
                    "path": rel,
                    "size": path.stat().st_size,
                })
        except Exception:
            continue
    return results


def _discover_python_modules() -> List[str]:
    return _discover_repo_files("*.py")


def _build_runtime_summary() -> Dict[str, Any]:
    py_files = _discover_python_modules()
    json_files = _discover_json_configs(PROJECT_ROOT)
    summary = {
        "name": APP_NAME,
        "project_root": str(PROJECT_ROOT),
        "platform": platform.platform(),
        "host": HOST,
        "port": PORT,
        "python_files_count": len(py_files),
        "json_files_count": len(json_files),
        "python_files": py_files[:200],
        "json_files": [item["path"] for item in json_files[:200]],
    }
    return summary


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
      --line: rgba(121, 240, 208, 0.35);
      --text: #edf7ff;
      --muted: #9bdfe8;
      --accent: #79f0d0;
      --cyan: #6ed6ff;
      --gold: #ffc857;
      --danger: #ff7387;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0; height: 100%;
      background: radial-gradient(circle at top, #0d1b22 0%, #04070a 38%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
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
      background: rgba(7, 13, 15, 0.92);
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
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
    }
    .brand h1 {
      margin: 0;
      font-size: 12px;
      letter-spacing: .22em;
      text-transform: uppercase;
      color: var(--accent);
    }
    .live {
      padding: 5px 8px;
      border: 1px solid rgba(121,240,208,0.4);
      background: rgba(121,240,208,0.08);
      border-radius: 999px;
      color: var(--accent);
      font-size: 10px;
      letter-spacing: .14em;
    }
    .chips { display: flex; flex-direction: column; gap: 8px; }
    .chip {
      border: 1px solid rgba(121,240,208,0.22);
      background: rgba(10,18,18,0.7);
      border-radius: 10px;
      padding: 10px 12px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .hint {
      color: rgba(236,246,255,0.72);
      font-size: 11px;
      letter-spacing: .04em;
    }
    .main { display: flex; flex-direction: column; padding: 12px; gap: 10px; min-width: 0; }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(18,26,30,0.9);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .14em;
      text-transform: uppercase;
    }
    .tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .tab {
      padding: 6px 9px;
      border: 1px solid rgba(110,214,255,0.3);
      border-radius: 7px;
      background: rgba(110,214,255,0.06);
    }
    .terminal-wrap {
      flex: 1;
      background: rgba(5,12,14,0.98);
      border: 1px solid var(--line);
      border-radius: 14px;
      position: relative;
      overflow: hidden;
    }
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
      <div class="hint">Localhost-only and trusted use only. Do not expose to public internet without auth.</div>
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
    term.write('Operator console online. Local shell bridge ready.\r\n');
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
    summary = _build_runtime_summary()
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
        },
        "summary": summary,
        "security": {
            "localhost_only": True,
            "warning": "Do not expose this application publicly without authentication and firewall hardening.",
        },
    })


@app.get("/api/repo")
async def repo_info() -> JSONResponse:
    return JSONResponse({
        "root": str(PROJECT_ROOT),
        "python_files": _discover_python_modules()[:500],
        "json_configs": _discover_json_configs(PROJECT_ROOT)[:500],
        "runtime": _build_runtime_summary(),
    })


@app.get("/api/commands")
async def commands() -> JSONResponse:
    return JSONResponse({
        "commands": [
            {"name": "health", "description": "Check live runtime health"},
            {"name": "status", "description": "Inspect unified runtime metadata"},
            {"name": "repo", "description": "Inspect repo modules and JSON autodiscovery"},
            {"name": "launch api_server.py", "description": "Start the legacy API server"},
            {"name": "launch cli.py", "description": "Start the legacy CLI if present"},
            {"name": "exec command", "description": "Execute a local command via the runtime shell bridge"},
        ]
    })


@app.post("/api/exec")
async def api_exec(request: Request) -> JSONResponse:
    """Execute a shell command locally with localhost-only safety."""
    body = await request.json()
    command = str(body.get("command", "")).strip()
    if not command:
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


@app.post("/api/launch")
async def api_launch(request: Request) -> JSONResponse:
    """Launch a legacy module (CLI or API server) as a background process."""
    body = await request.json()
    target = str(body.get("target", "")).strip().lower()
    if target not in {"cli", "cli.py", "api_server", "api_server.py"}:
        return JSONResponse({"status": "error", "message": "Unsupported target"}, status_code=400)

    if target in {"cli", "cli.py"}:
        script = PROJECT_ROOT / "cli.py"
        name = "cli"
    else:
        script = PROJECT_ROOT / "api_server.py"
        name = "api_server"

    if not script.exists():
        return JSONResponse({"status": "error", "message": f"Missing script: {script.name}"}, status_code=404)

    try:
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
        )
        STARTED_PROCESSES[name] = proc
        return JSONResponse({
            "status": "started",
            "target": name,
            "pid": proc.pid,
            "script": script.name,
        })
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


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


if __name__ == "__main__":
    import uvicorn

    print("=" * 64)
    print(f"  {APP_NAME}")
    print(f"  MD90 unified runtime: web terminal + API + shell + repo scanning")
    print(f"  URL: http://{HOST}:{PORT}")
    print(f"  Project root: {PROJECT_ROOT}")
    print("=" * 64)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
