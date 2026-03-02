# SOLIS

SOLIS now uses a lightweight local model designed to run on Raspberry Pi.

## Goal
- `setup.sh`: install everything once.
- `run.sh`: generate one image.
- `COPY_PASTE_START.md`: beginner guide with copy/paste commands.

## Quick Start
```bash
./setup.sh
./run.sh
```

Generated file:
- `output/solis_latest.png`

## Example Prompt
```bash
./run.sh --prompt "A glowing wind farm over green hills at sunrise"
```

## Why This Version Is Lightweight
- Fully local generation (no cloud API calls).
- Only one Python dependency: Pillow.
- No `torch`, no `diffusers`, no large model downloads.

## Files You Need
- `setup.sh`
- `run.sh`
- `COPY_PASTE_START.md`

## Optional Arguments
```bash
./run.sh --prompt "Solar panels under neon clouds" --width 640 --height 640 --seed 1234
```
