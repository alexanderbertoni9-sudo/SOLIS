# SOLIS

SOLIS is a fullscreen local image-generation installation designed for reliable public-space deployment.

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

## Project Structure
- `run.sh`: single launch command.
- `setup.sh`: optional pre-install step.
- `src/main.py`: single entry point.
- `src/preview.py`: fullscreen display pipeline.
- `src/generator_diffusion.py`: generation loop and frame streaming.
- `RUN.md`: operator run reference.
- `TROUBLESHOOTING.md`: setup/runtime fixes.
- `CASE_STUDY_CODEX.md`: before/after transformation summary.
