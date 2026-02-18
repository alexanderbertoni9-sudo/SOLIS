# SOLIS — Installation Build

SOLIS is now structured as a single-purpose large-space installation runtime: one entry point, one display pipeline, and one generation loop.

## 30-Second Quick Start
```bash
git clone https://github.com/alexanderbertoni9-sudo/SOLIS.git
cd SOLIS
./run.sh
```

## What `./run.sh` does
1. Creates `.venv` if missing.
2. Installs required Python packages.
3. Starts SOLIS fullscreen generation.
4. Keeps the final image on screen when generation finishes.

## Setup Notes
- First run takes longer because models and dependencies are downloaded.
- Output image is saved to `output/solis_latest.png`.
- Exit fullscreen with `Esc` or `q`.

## Repository Structure
- `run.sh` — single launch command for installation use
- `src/main.py` — single entrypoint and generation loop
- `src/preview.py` — fullscreen display pipeline
- `src/generator_diffusion.py` — live diffusion frame stream
- `setup.sh` — optional pre-install script
- `RUN.md` — one-command run reference
- `TROUBLESHOOTING.md` — install/runtime fixes
- `CASE_STUDY_CODEX.md` — before/after transformation story
