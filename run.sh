#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Missing .venv. Run ./setup.sh first."
  exit 1
fi

source .venv/bin/activate
mkdir -p output

python src/main.py "$@"
