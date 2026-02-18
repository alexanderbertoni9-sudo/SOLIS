#!/usr/bin/env bash
set -e

echo "=== SOLIS setup ==="

if [ ! -d ".venv" ]; then
  echo "[1/4] Creating virtual environment (.venv)..."
  python3 -m venv .venv
else
  echo "[1/4] .venv already exists."
fi

echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

echo "[3/4] Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[4/4] Ensuring output/ exists..."
mkdir -p output

echo "=== DONE ==="
echo "Run:"
echo "  SOLIS_PROFILE=desktop python3 src/main.py"
