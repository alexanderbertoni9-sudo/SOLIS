from __future__ import annotations
import os, time

from export_epaper import to_epaper_1bit
from preview import LivePreview, PreviewConfig
from epaper_ui import overlay_progress, should_snapshot
from epaper_display import EpaperDisplay, EpaperConfig

# Competition prompt (change only when you explicitly want to)
PROMPT = "A picture of renewable energy"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_DIR = os.path.join(ROOT, "image_bank")
EXPORT_DIR = os.path.join(ROOT, "exports")

EPAPER_SIZE = (800, 480)

# Step B realism knobs
SNAPSHOTS = 8
HIDE_FRAC = 0.18


def run_bank():
    from generator_bank import ImageBankGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    gen = ImageBankGenerator(BANK_DIR)

    preview = LivePreview(PreviewConfig(title=f"SOLIS (bank) — {PROMPT}"))
    epaper = EpaperDisplay(EpaperConfig(size=EPAPER_SIZE, invert=False))

    last = None
    try:
        for frame in gen.generate(total_steps=25):
            if not preview.pump():
                return

            preview.show(frame.image, frame.step, frame.total_steps)
            last = frame.image

        final = to_epaper_1bit(last, EPAPER_SIZE)
        epaper.show(final)  # show final on e-paper
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
    epaper = EpaperDisplay(EpaperConfig(size=EPAPER_SIZE, invert=False))

    last = None
    last_bucket = -1

    try:
        for frame in gen.generate_stream(steps=30, preview_every=4):
            if not preview.pump():
                return

            last = frame.image

            # Step 0: show "loading" on preview, but DO NOT refresh e-paper yet
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
                # 1) preview update (with baked overlay)
                img_with_ui = overlay_progress(frame.image, frame.step, frame.total_steps)
                preview.show(img_with_ui, frame.step, frame.total_steps)

                # 2) e-paper refresh on the SAME schedule
                # Tradeoff: converting to 1-bit costs CPU, but only ~8 times total.
                epaper_img = to_epaper_1bit(frame.image, EPAPER_SIZE)
                epaper.show(epaper_img)

        # Final: always push final frame to e-paper + export
        final = to_epaper_1bit(last, EPAPER_SIZE)
        epaper.show(final)
        out = os.path.join(EXPORT_DIR, f"solis_diffusion_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        preview.close()


if __name__ == "__main__":
    mode = os.environ.get("SOLIS_MODE", "diffusion").strip().lower()
    if mode == "bank":
        run_bank()
    else:
        run_diffusion()
