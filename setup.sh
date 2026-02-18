#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== SOLIS setup ==="

if [ ! -d ".venv" ]; then
  echo "[1/3] Creating virtual environment (.venv)..."
  python3 -m venv .venv
else
  echo "[1/3] .venv already exists."
fi

source .venv/bin/activate

echo "[2/3] Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[3/3] Ensuring output/ exists..."
mkdir -p output

echo "=== DONE ==="
echo "Run SOLIS with: ./run.sh"
