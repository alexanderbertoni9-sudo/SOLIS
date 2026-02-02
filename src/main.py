from __future__ import annotations
import os, time

from export_epaper import to_epaper_1bit
from preview import LivePreview, PreviewConfig

# E-paper realism helpers
from epaper_ui import overlay_progress, should_snapshot

# Fixed prompt for competition mode (we can make configurable later)
PROMPT = "A picture of renewable energy"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_DIR = os.path.join(ROOT, "image_bank")
EXPORT_DIR = os.path.join(ROOT, "exports")

# Example e-paper size (we'll update later to match your real panel)
EPAPER_SIZE = (800, 480)


def run_bank():
    from generator_bank import ImageBankGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    gen = ImageBankGenerator(BANK_DIR)
    preview = LivePreview(PreviewConfig(title=f"SOLIS (bank) — {PROMPT}"))

    last = None
    try:
        for frame in gen.generate(total_steps=25):
            if not preview.pump():
                return
            preview.show(frame.image, frame.step, frame.total_steps)
            last = frame.image

        final = to_epaper_1bit(last, EPAPER_SIZE)
        out = os.path.join(EXPORT_DIR, f"solis_bank_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        preview.close()


def run_diffusion():
    from generator_diffusion import DiffusionGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    gen = DiffusionGenerator(prompt=PROMPT)
    preview = LivePreview(PreviewConfig(title=f"SOLIS (diffusion) — {PROMPT}"))

    last = None

    # E-paper realism knobs
    SNAPSHOTS = 8          # total updates during generation
    MIN_STEP_TO_SHOW = 6   # hide early super-noisy steps
    last_bucket = -1

    try:
        for frame in gen.generate_stream(steps=30, preview_every=4):
            if not preview.pump():
                return

            # Always keep most recent image for final export
            last = frame.image

            # Step 0 is the immediate "loading" frame from generator_diffusion.py
            if frame.step == 0:
                img_with_ui = overlay_progress(frame.image, frame.step, frame.total_steps)
                preview.show(img_with_ui, frame.step, frame.total_steps)
                continue

            # Only snapshot at percent buckets (and not too early)
            do_update, last_bucket = should_snapshot(frame.step, frame.total_steps, SNAPSHOTS, last_bucket)
            if do_update and frame.step >= MIN_STEP_TO_SHOW:
                img_with_ui = overlay_progress(frame.image, frame.step, frame.total_steps)
                preview.show(img_with_ui, frame.step, frame.total_steps)

        final = to_epaper_1bit(last, EPAPER_SIZE)
        out = os.path.join(EXPORT_DIR, f"solis_diffusion_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        preview.close()


if __name__ == "__main__":
    # Choose mode with an environment variable:
    #   SOLIS_MODE=diffusion python3 src/main.py
    # default: bank
    mode = os.environ.get("SOLIS_MODE", "bank").strip().lower()
    if mode == "diffusion":
        run_diffusion()
    else:
        run_bank()
