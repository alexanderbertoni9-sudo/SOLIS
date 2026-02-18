# SOLIS — Screen-First Live Diffusion

SOLIS generates images locally with Stable Diffusion and displays the generation live in fullscreen on a regular monitor.

## Behavior
- Prompt: `A picture of renewable energy`
- Fullscreen window auto-sizes to the current monitor resolution.
- Live updates are shown continuously while diffusion runs.
- When generation completes, the final image remains fullscreen.
- Press `Esc` or `q` to exit.

## Repo layout
- `src/main.py` — runtime entrypoint
- `src/generator_diffusion.py` — local diffusion generator with streamed frames
- `src/preview.py` — fullscreen monitor display + live rendering
- `output/solis_latest.png` — final exported image (overwritten each run)

## Environment variables
- `SOLIS_PROFILE=desktop|pi` (default: `desktop`)
- `SOLIS_STEPS=<int>`
- `SOLIS_PREVIEW_EVERY=<int>`
- `SOLIS_HEADLESS=1` (run without display window)
- `SOLIS_SAVE_FINAL=0|1` (default: `1`)
