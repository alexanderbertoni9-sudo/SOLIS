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
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png` (new unique file each run)
- `output/solis_latest.png` (always updated copy of newest image)
- `./run.sh` opens the image in fullscreen on Raspberry Pi desktop.
- Press `Esc` or `q` to close fullscreen.

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

## Beginner Flow
1. Run `./setup.sh` once.
2. Run `./run.sh` each time you want a new image.
3. Type a prompt when asked (or press Enter for default).
