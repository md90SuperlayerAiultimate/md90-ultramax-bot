# MD90 ULTIMATE FUSION v4

## Quick Start (3 commands)
```bash
cp .env.example .env        # 1. Edit credentials
pip install -r requirements.txt  # 2. Install
python main.py --mode backtest   # 3. Validate first
```

## Architecture
```
ccxt (Binance OHLCV)
  → MD90 17-Layer Signal (ICT/SMC exact MQL5 port)
  → HMM 6-state Regime
  → MiroFish NetworkX Graph
  → Ollama Agent (local/free) + Claude API (fallback)
  → 8-stage Cognitive Pipeline
  → Polymarket CLOB V2 Execution
  → SelfLearner (online SGD + Optuna + Meta-Learning)
  → GitHub model push every 24h
  → n8n webhook integration
```

## Modes
| Mode | Command |
|------|---------|
| Polymarket bot | `MODE=polymarket python main.py` |
| Binance spot   | `MODE=binance python main.py` |
| Backtest       | `python main.py --mode backtest` |
| Dashboard      | `streamlit run dashboard/app.py` |
| Webhook server | `uvicorn n8n.webhook_server:app --port 8080` |
| ML tuning      | `python ml/tuner.py --github` |

## Docker (bot + dashboard + webhook + ollama)
```bash
docker-compose up -d
```

## n8n Integration
1. Import `n8n/workflow_export.json` into n8n
2. Set env vars: `MD90_WEBHOOK_URL`, `WEBHOOK_SECRET`
3. Start webhook: `MODE=webhook bash run.sh`

## n8n Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status`          | GET  | Bot status + equity |
| `/signal`          | GET  | Live signals |
| `/ml_stats`        | GET  | ML win rate + thresholds |
| `/research`        | POST | Push news/research data |
| `/command`         | POST | FLATTEN/PAUSE/RESUME/STOP |
| `/market_resolved` | POST | Notify market resolution |

## Self-Learning Pipeline
- **L1 Online** : SGD weight update every trade
- **L2 Optuna** : Bayesian threshold search every 50 trades
- **L3 Meta**   : Per-regime weights every 100 trades
- **GitHub**    : Auto-push model every 24h

## Signal Layers (17, sum=100%)
L1 SNR | L2 EMA | L3 RSI | L4 Stoch | L5 OB | L6 Vol | L7 MTF
L8 Sentiment | L9 UltraScalp | L10 PrimeSwing | L11 Macro
L12 VWAP | L13 ATR | L14 OTE | L15 FVG | L16 MasterCall | L17 TimeStop
