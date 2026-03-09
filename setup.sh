#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== SOLIS local setup (Raspberry Pi friendly) ==="

if [ ! -d ".venv" ]; then
  echo "[1/4] Creating virtual environment (.venv)..."
  python3 -m venv .venv
else
  echo "[1/4] .venv already exists."
fi

source .venv/bin/activate

echo "[2/4] Upgrading pip..."
python -m pip install --upgrade pip

echo "[3/4] Installing dependencies..."
python -m pip install -r requirements.txt

echo "[4/4] Ensuring output/ exists..."
mkdir -p output

echo "=== DONE ==="
echo "Next step: ./run.sh"
