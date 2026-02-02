from __future__ import annotations
import os, time
from export_epaper import to_epaper_1bit
from preview import LivePreview, PreviewConfig

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
    try:
        for frame in gen.generate_stream(steps=30, preview_every=4):
            if not preview.pump():
                return
            preview.show(frame.image, frame.step, frame.total_steps)
            last = frame.image

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
