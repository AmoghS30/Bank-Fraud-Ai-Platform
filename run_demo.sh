#!/usr/bin/env bash
# Run the Streamlit demo with thread-limit env vars set before any ML library loads.
# These prevent the OpenMP deadlock between LightGBM and PyTorch/sentence-transformers.
set -e
cd "$(dirname "$0")"

source .venv/bin/activate 2>/dev/null || true

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

streamlit run dashboard/app.py "$@"
