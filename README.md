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

## What You See
- Fullscreen window opens first.
- You see the image being constructed during diffusion.
- Final image stays fullscreen until you press `Esc` or `q`.

## Output Files
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png`
- `output/solis_latest.png` (latest copy)

## Defaults
- Model: `segmind/tiny-sd`
- Size: `512x512`
- Steps: `20`
- Live preview: every step

## Example
```bash
./run.sh --prompt "a cat and a dog on a couch"
```

## Notes For Pi
- First run is slower because model files download once.
- For lower memory usage:
```bash
./run.sh --width 512 --height 512 --steps 15
```
