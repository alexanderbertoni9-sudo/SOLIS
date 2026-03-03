#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== SOLIS local text-to-image setup (Raspberry Pi) ==="
MODEL_ID="${SOLIS_MODEL_ID:-segmind/tiny-sd}"
MODEL_DIR="${SOLIS_MODEL_DIR:-models/segmind-tiny-sd}"

if [ ! -d ".venv" ]; then
  echo "[1/6] Creating virtual environment (.venv)..."
  python3 -m venv .venv
else
  echo "[1/6] .venv already exists."
fi

source .venv/bin/activate

echo "[2/6] Upgrading pip..."
python -m pip install --upgrade pip

echo "[3/6] Installing dependencies..."
python -m pip install -r requirements.txt

echo "[3.5/6] Removing conflicting optional Torch packages (if present)..."
python -m pip uninstall -y torchvision torchaudio >/dev/null 2>&1 || true

echo "[4/6] Preparing local model snapshot..."
python src/prepare_model.py --model-id "$MODEL_ID" --model-dir "$MODEL_DIR"

echo "[5/6] Ensuring output/ exists..."
mkdir -p output

echo "[6/6] Running dependency compatibility checks..."
python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

def major(pkg: str) -> int:
    return int(version(pkg).split(".")[0])

try:
    t_major = major("transformers")
    d_major = major("diffusers")
    _ = version("huggingface_hub")
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
