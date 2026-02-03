#!/usr/bin/env bash
set -e

echo "=== SOLIS setup ==="

# 1) Create venv if missing
if [ ! -d ".venv" ]; then
  echo "[1/4] Creating virtual environment (.venv)..."
  python3 -m venv .venv
else
  echo "[1/4] .venv already exists."
fi

# 2) Activate venv
echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

# 3) Install dependencies
echo "[3/4] Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4) Ensure exports folder
echo "[4/4] Ensuring exports/ exists..."
mkdir -p exports

echo "=== DONE ==="
echo "Desktop:"
echo "  SOLIS_PROFILE=desktop SOLIS_MODE=diffusion python3 src/main.py"
echo "Pi / headless:"
echo "  SOLIS_PROFILE=pi SOLIS_MODE=diffusion SOLIS_HEADLESS=1 python3 src/main.py"
