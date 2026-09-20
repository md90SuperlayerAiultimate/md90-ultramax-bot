#!/bin/bash
cd "$(dirname "$0")/.."
echo "=== MD90 v4 — Running Tests ==="
python -m pytest tests/ -v --tb=short 2>&1
