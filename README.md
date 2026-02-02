# SOLIS — Solar-Operated Local Image Synthesizer

SOLIS is a solar-powered, Raspberry Pi–based sustainable art installation that generates images using a local/private AI pipeline and displays them on a monochrome e-paper (e-ink) display.

**Prompt (fixed):** “A picture of renewable energy”

## Core experience
- A physical button triggers a reset and a new image is generated.
- The system aims to feel “live” while generating by showing progressive updates (snapshots/progress indicator), adapted to slow e-paper refresh.

## Repository layout
- `src/` — Python prototype + (later) Raspberry Pi code
- `image_bank/` — optional pre-generated images for fast prototyping (not committed)
- `exports/` — generated output images (not committed)
- `docs/` — build notes, diagrams, competition documentation

## Build order
1. Desktop software prototype
2. Raspberry Pi port + optimization
3. Hardware integration (e-paper, button, solar + battery)
