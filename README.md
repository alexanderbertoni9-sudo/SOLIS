# SOLIS

SOLIS is a local text-to-image generator built for Raspberry Pi with live fullscreen preview.

## What You Run
- `./setup.sh` installs everything once.
- `./run.sh` starts generation and displays the image live in fullscreen.

## Quick Start
```bash
./setup.sh
./run.sh
```

`./setup.sh` now installs Python deps and downloads/repairs a verified local model snapshot into `models/segmind-tiny-sd`.
After setup completes, `./run.sh` uses local model files by default (no network needed for normal runs).

## What You See
- Fullscreen window opens first.
- A prompt is chosen randomly from the built-in renewable-energy prompt list.
- You see the image being constructed during diffusion.
- Final image stays fullscreen until you press `Esc` or `q`.

## Output Files
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png`
- `output/solis_latest.png` (latest copy)

## Defaults
- Model: `segmind/tiny-sd`
- Model directory: `models/segmind-tiny-sd`
- Size: `512x512`
- Steps: `20`
- Live preview: every step

## Prompt Mode
- Custom prompt input is disabled for now.
- Each run auto-selects one prompt from a built-in list of 10 renewable-energy scenes.

## Notes For Pi
- First setup is slower because model files download once.
- For lower memory usage:
```bash
./run.sh --width 512 --height 512 --steps 15
```

## Repair Model Snapshot
If model files were interrupted/corrupted:
```bash
rm -rf models/segmind-tiny-sd
./setup.sh
```
