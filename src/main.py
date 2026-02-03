from __future__ import annotations

import os
import sys
import time
from typing import Optional
import pygame

# --- Make imports reliable no matter where you run from ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))          # .../project/src
ROOT = os.path.dirname(SRC_DIR)                               # .../project
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from export_epaper import to_epaper_1bit
from preview import LivePreview, PreviewConfig

# E-paper realism helpers
from epaper_ui import overlay_progress, should_snapshot

# Fixed prompt for competition mode (we can make configurable later)
PROMPT = "A picture of renewable energy, solar panels, and wind turbines in a beautiful landscape."
BANK_DIR = os.path.join(ROOT, "image_bank")
EXPORT_DIR = os.path.join(ROOT, "exports")

# Example e-paper size (we'll update later to match your real panel)
EPAPER_SIZE = (800, 480)


def init_pygame_for_preview():
    """
    Ensures pygame is initialized before LivePreview tries to use it.
    Safe to call multiple times.
    """
    try:
        import pygame
    except Exception as e:
        raise RuntimeError(
            "pygame is not installed in this Python environment.\n"
            "Install it with: python3 -m pip install pygame"
        ) from e

    # Initialize core modules used by most preview windows
    if not pygame.get_init():
        pygame.init()

    # These are the usual culprits if 'not initialized' appears:
    if not pygame.display.get_init():
        pygame.display.init()

    if not pygame.font.get_init():
        pygame.font.init()


def run_bank():
    from generator_bank import ImageBankGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    gen = ImageBankGenerator(BANK_DIR)

    # ✅ FIX: initialize pygame before constructing LivePreview
    init_pygame_for_preview()
    preview = LivePreview(PreviewConfig(title=f"SOLIS (bank) — {PROMPT}"))

    last: Optional[object] = None
    try:
        for frame in gen.generate(total_steps=25):
            if not preview.pump():
                return

            # Some generators may yield a "loading" frame with image=None
            if frame.image is None:
                continue

            preview.show(frame.image, frame.step, frame.total_steps)
            last = frame.image

        if last is None:
            raise RuntimeError("Bank generator produced no image frames (last is None).")

        final = to_epaper_1bit(last, EPAPER_SIZE)
        out = os.path.join(EXPORT_DIR, f"solis_bank_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        preview.close()
        # Optional cleanup (keeps things tidy if you rerun a lot)
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass


def run_diffusion():
    from generator_diffusion import DiffusionGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    gen = DiffusionGenerator(prompt=PROMPT)

    # ✅ FIX: initialize pygame before constructing LivePreview
    init_pygame_for_preview()
    preview = LivePreview(PreviewConfig(title=f"SOLIS (diffusion) — {PROMPT}"))

    last: Optional[object] = None

    # E-paper realism knobs (judge-friendly)
    SNAPSHOTS = 8         # total visible updates during generation
    HIDE_FRAC = 0.18      # hide first ~18% of steps (very noisy)

    last_bucket = -1

    try:
        for frame in gen.generate_stream(steps=30, preview_every=4):
            if not preview.pump():
                return

            # If the generator yields an empty frame, skip safely
            if frame.image is None:
                continue

            # Always keep most recent image for final export
            last = frame.image

            # Step 0 is the immediate "loading" frame
            if frame.step == 0:
                img_with_ui = overlay_progress(frame.image, frame.step, frame.total_steps)
                preview.show(img_with_ui, frame.step, frame.total_steps)
                continue

            do_update, last_bucket = should_snapshot(
                frame.step,
                frame.total_steps,
                SNAPSHOTS,
                last_bucket,
                hide_frac=HIDE_FRAC,
            )

            if do_update:
                img_with_ui = overlay_progress(frame.image, frame.step, frame.total_steps)
                preview.show(img_with_ui, frame.step, frame.total_steps)

        if last is None:
            raise RuntimeError("Diffusion generator produced no image frames (last is None).")

        final = to_epaper_1bit(last, EPAPER_SIZE)
        out = os.path.join(EXPORT_DIR, f"solis_diffusion_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        preview.close()
        # Optional cleanup
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass


if __name__ == "__main__":
    # Choose mode with an environment variable:
    #   SOLIS_MODE=diffusion python3 src/main.py
    # default: bank
    mode = os.environ.get("SOLIS_MODE", "bank").strip().lower()
    if mode == "diffusion":
        run_diffusion()
    else:
        run_bank()
