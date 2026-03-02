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

if ! python -c "import tkinter" >/dev/null 2>&1; then
  echo "Tkinter not found (needed for fullscreen display)."
  if command -v apt-get >/dev/null 2>&1; then
    echo "Attempting to install python3-tk (may ask for sudo password)..."
    sudo apt-get update
    sudo apt-get install -y python3-tk
  else
    echo "Install tkinter manually for your OS to enable fullscreen display."
  fi
fi

echo "=== DONE ==="
echo "Next step: ./run.sh"
