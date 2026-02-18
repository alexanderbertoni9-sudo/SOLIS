#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[SOLIS] Creating virtual environment"
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt >/dev/null
mkdir -p output

python src/main.py
