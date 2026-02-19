# SOLIS

SOLIS is a fullscreen, local image-generation installation that renders energy-inspired art in real time for reliable public-space display.

## What It Is
SOLIS is a self-contained generative artwork system. It runs entirely on the host machine, produces a live evolving image on screen, and then holds the final composition until you exit.

## What It Does
- Generates a single image using a local Stable Diffusion pipeline.
- Streams intermediate frames to the display while the image is being created.
- Saves the final output and keeps it fullscreen for exhibition.

## Why It Exists
SOLIS is built for galleries, public displays, and installations where reliability and privacy matter. Running locally avoids network dependency, keeps prompts and outputs private, and makes the display predictable for long-running sessions.

## How It Shows Energy-Inspired Art
The generator uses a renewable-energy themed prompt (see `src/main.py`) and renders the image through a diffusion process. As the diffusion steps progress, SOLIS shows those intermediate frames live, making the energy-inspired transformation visible in real time before presenting the final artwork.

## 30-Second Quick Start
```bash
git clone https://github.com/alexanderbertoni9-sudo/SOLIS.git
cd SOLIS
./run.sh
```

## What Happens on Run
- Creates `.venv` if needed.
- Installs dependencies from `requirements.txt`.
- Starts one fullscreen live generation session.
- Saves the final image to `output/solis_latest.png`.
- Leaves the final image on screen until you press `Esc` or `q`.

## Installation Notes
- First launch is slower because model files download on demand.
- Keep at least 8-12 GB free disk space for dependencies, cache, and output.
- Recommended Python: 3.10+.

## Platform Notes (Important)
- This setup targets macOS and Linux desktops/laptops with sufficient CPU/GPU resources.
- Raspberry Pi is not a supported target for the default Stable Diffusion pipeline; expect slow performance or failures due to memory and compute limits.
- If you intend to experiment on a Raspberry Pi, treat it as an advanced, custom setup and expect to adapt the model/requirements.

## Project Structure
- `run.sh`: single launch command.
- `setup.sh`: optional pre-install step.
- `src/main.py`: single entry point.
- `src/preview.py`: fullscreen display pipeline.
- `src/generator_diffusion.py`: generation loop and frame streaming.
- `RUN.md`: operator run reference.
- `TROUBLESHOOTING.md`: setup/runtime fixes.
- `CASE_STUDY_CODEX.md`: before/after transformation summary.
