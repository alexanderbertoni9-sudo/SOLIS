#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== SOLIS local text-to-image setup (Raspberry Pi) ==="

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

echo "[3.5/4] Removing conflicting optional Torch packages (if present)..."
python -m pip uninstall -y torchvision torchaudio >/dev/null 2>&1 || true

echo "[4/4] Ensuring output/ exists..."
mkdir -p output

python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

def major(pkg: str) -> int:
    return int(version(pkg).split(".")[0])

try:
    t_major = major("transformers")
    d_major = major("diffusers")
except Exception as exc:
    print(f"Dependency check failed: {exc}")
    raise SystemExit(1)

if t_major >= 5:
    print("Incompatible transformers major version detected (>=5).")
    print("Re-run setup to install pinned versions from requirements.txt.")
    raise SystemExit(1)

for pkg in ("torchvision", "torchaudio"):
    try:
        _ = version(pkg)
        print(f"Warning: optional package {pkg} is installed and may conflict with torch.")
        print("Run: python -m pip uninstall -y torchvision torchaudio")
    except PackageNotFoundError:
        pass

try:
    from diffusers import StableDiffusionPipeline
except Exception as exc:
    print(f"StableDiffusionPipeline import check failed: {exc}")
    raise SystemExit(1)

try:
    import pygame
except Exception as exc:
    print(f"pygame import check failed: {exc}")
    raise SystemExit(1)

print("Dependency compatibility check passed (diffusers + pygame).")
PY

echo "=== DONE ==="
echo "Next step: ./run.sh"
