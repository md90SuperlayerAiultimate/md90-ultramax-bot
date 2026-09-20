#!/bin/bash
cd "$(dirname "$0")/.."
export DRY_RUN=true
export PAIR=BTC/USDT
export TIMEFRAME=15m
python main.py
