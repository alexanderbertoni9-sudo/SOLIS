from __future__ import annotations
import os

from preview import LivePreview, PreviewConfig

PROMPT = "A picture of renewable energy"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "solis_latest.png")


def _get_profile():
    profile = os.environ.get("SOLIS_PROFILE", "desktop").strip().lower()

    if profile == "pi":
        return {
            "steps": 24,
            "preview_every": 2,
            "headless_default": True,
        }

    return {
        "steps": 30,
        "preview_every": 1,
        "headless_default": False,
    }


def run_diffusion():
    from generator_diffusion import DiffusionGenerator

    profile = _get_profile()
    steps = int(os.environ.get("SOLIS_STEPS", str(profile["steps"])))
    preview_every = int(os.environ.get("SOLIS_PREVIEW_EVERY", str(profile["preview_every"])))
    headless = os.environ.get("SOLIS_HEADLESS", "0").strip() == "1" or profile["headless_default"]
    save_final = os.environ.get("SOLIS_SAVE_FINAL", "1").strip() == "1"

    gen = DiffusionGenerator(prompt=PROMPT)
    preview = None
    if not headless:
        preview = LivePreview(PreviewConfig(title=f"SOLIS — {PROMPT}"))

    last = None
    try:
        for frame in gen.generate_stream(steps=steps, preview_every=preview_every):
            last = frame.image
            if preview:
                if not preview.pump():
                    return
                preview.show(frame.image, frame.step, frame.total_steps, show_status=True)

        if last is None:
            return

        if save_final:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            last.save(OUTPUT_FILE, format="PNG")
            print("Saved:", OUTPUT_FILE)

        if preview:
            preview.show_final_fullscreen(last)
            preview.wait_until_exit()
    finally:
        if preview:
            preview.close()


if __name__ == "__main__":
    run_diffusion()
