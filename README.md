# SOLIS

Local text-to-image generator for Raspberry Pi with live fullscreen diffusion preview.

## Quick Start

```bash
cd /Users/alexander.bertoni/Documents/GitHub/SOLIS
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

## How It Works

- `./setup.sh` (run once):
  - creates `.venv`
  - installs pinned dependencies
  - downloads/repairs a local model snapshot at `models/segmind-tiny-sd`
- `./run.sh` (run each time):
  - starts fullscreen viewer
  - generates image locally with live step previews
  - holds final image until you press `Esc` or `q`

## Prompt Behavior (Current)

- Manual prompt typing is disabled for now.
- Each run randomly picks 1 prompt from a built-in list of 10 renewable-energy scenes.

Built-in scene set includes:
- wind turbines producing renewable energy at sunrise
- wind turbines and solar panels on a green field
- modern solar farm across rolling hills
- offshore wind + coastal renewable hub
- futuristic eco-city with solar + vertical wind
- hydroelectric dam powering a smart city
- community microgrid with battery storage
- desert renewable plant with mirrors + panels
- renewable energy control center monitoring the grid
- EV transport charging from renewable stations

## Useful Run Commands

Default run:
```bash
./run.sh
```

Lower memory / faster on Pi:
```bash
./run.sh --width 512 --height 512 --steps 15
```

Deterministic output:
```bash
./run.sh --seed 1234
```

Generate only (no fullscreen viewer):
```bash
./run.sh --no-open
```

## Output Files

- unique file per run:
  - `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png`
- latest copy:
  - `output/solis_latest.png`
- automatic cleanup:
  - keeps the 4 newest generated `solis_*.png` files and deletes older ones

## Controls

- `Esc` or `q`: cancel generation (if running) and close fullscreen

## Raspberry Pi Notes

- First setup is slower (one-time model download/verification).
- After setup, generation runs from local model files by default.

## Repair Commands

If model files are broken/incomplete:
```bash
rm -rf models/segmind-tiny-sd
./setup.sh
```

If your virtual environment is broken:
```bash
rm -rf .venv
./setup.sh
```
