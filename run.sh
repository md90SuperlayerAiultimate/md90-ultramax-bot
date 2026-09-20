#!/bin/bash
MODE=${MODE:-polymarket}
case "$MODE" in
  polymarket)  python main.py --mode polymarket ;;
  omni)        python main.py --mode omni ;;
  binance)     python main.py --mode binance ;;
  backtest)    python main.py --mode backtest ;;
  dashboard)   streamlit run dashboard/app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 ;;
  webhook)     uvicorn n8n.webhook_server:app --host 0.0.0.0 --port 8080 ;;
  ml_tune)     python ml/tuner.py ${GITHUB:+--github} ;;
  arb_only)    python -c "import asyncio; from arbitrage.scanner import StructuralArbScanner; asyncio.run(StructuralArbScanner().scan())" ;;
  *) echo "Modes: polymarket|binance|backtest|dashboard|webhook|ml_tune|arb_only"; exit 1 ;;
esac
