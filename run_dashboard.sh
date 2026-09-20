#!/bin/bash
cd "$(dirname "$0")/.."
streamlit run dashboard/app.py --server.port 8501
