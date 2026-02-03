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


def _get_profile():
    """
    Step C profiles: keep them simple + explainable.
    """
    profile = os.environ.get("SOLIS_PROFILE", "desktop").strip().lower()

    if profile == "pi":
        return {
            "steps": 24,                 # fewer steps = more reliable / lower power
            "preview_every": 6,          # decode fewer intermediate frames
            "epaper_min_refresh": 10.0,  # real e-paper feels ~slow; reduces power + ghosting
            "headless_default": True,    # Pi often runs without a monitor
        }

    # desktop defaults
    return {
        "steps": 30,
        "preview_every": 4,
        "epaper_min_refresh": 8.0,
        "headless_default": False,
    }


def run_bank():
    from generator_bank import ImageBankGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    gen = ImageBankGenerator(BANK_DIR)

    profile = _get_profile()

    # Headless override:
    #   SOLIS_HEADLESS=1 ...
    headless = os.environ.get("SOLIS_HEADLESS", "0").strip() == "1" or profile["headless_default"]

    preview = None
    if not headless:
        preview = LivePreview(PreviewConfig(title=f"SOLIS (bank) — {PROMPT}"))

    epaper = EpaperDisplay(EpaperConfig(size=EPAPER_SIZE, invert=False, min_refresh_seconds=profile["epaper_min_refresh"]))

    last = None
    try:
        for frame in gen.generate(total_steps=25):
            last = frame.image
            if preview:
                if not preview.pump():
                    return
                preview.show(frame.image, frame.step, frame.total_steps)

        final = to_epaper_1bit(last, EPAPER_SIZE)
        epaper.show(final, force=True)
        out = os.path.join(EXPORT_DIR, f"solis_bank_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        if preview:
            preview.close()


def run_diffusion():
    from generator_diffusion import DiffusionGenerator

    os.makedirs(EXPORT_DIR, exist_ok=True)
    profile = _get_profile()

    steps = int(os.environ.get("SOLIS_STEPS", str(profile["steps"])))
    preview_every = int(os.environ.get("SOLIS_PREVIEW_EVERY", str(profile["preview_every"])))

    headless = os.environ.get("SOLIS_HEADLESS", "0").strip() == "1" or profile["headless_default"]

    gen = DiffusionGenerator(prompt=PROMPT)

    preview = None
    if not headless:
        preview = LivePreview(PreviewConfig(title=f"SOLIS (diffusion) — {PROMPT}"))

    epaper = EpaperDisplay(EpaperConfig(size=EPAPER_SIZE, invert=False, min_refresh_seconds=profile["epaper_min_refresh"]))

    last = None
    last_bucket = -1

    try:
        for frame in gen.generate_stream(steps=steps, preview_every=preview_every):
            last = frame.image

            # Optional desktop preview
            if preview:
                if not preview.pump():
                    return

            # Step 0: show "loading" on preview, but DO NOT refresh e-paper yet
            if frame.step == 0:
                if preview:
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
                if preview:
                    img_with_ui = overlay_progress(frame.image, frame.step, frame.total_steps)
                    preview.show(img_with_ui, frame.step, frame.total_steps)

                # 2) e-paper refresh on the SAME schedule
                epaper_img = to_epaper_1bit(frame.image, EPAPER_SIZE)
                epaper.show(epaper_img)

        # Final: always push final frame to e-paper + export
        final = to_epaper_1bit(last, EPAPER_SIZE)
        epaper.show(final, force=True)

        out = os.path.join(EXPORT_DIR, f"solis_diffusion_{int(time.time())}.png")
        final.save(out)
        print("Saved:", out)
    finally:
        if preview:
            preview.close()


if __name__ == "__main__":
    mode = os.environ.get("SOLIS_MODE", "diffusion").strip().lower()
    if mode == "bank":
        run_bank()
    else:
        run_diffusion()
