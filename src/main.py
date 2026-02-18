from __future__ import annotations

import os

from generator_diffusion import DiffusionGenerator
from preview import LivePreview, PreviewConfig

PROMPT = "A picture of renewable energy"
STEPS = 30
PREVIEW_EVERY = 1
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "solis_latest.png")


def run() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    preview = LivePreview(PreviewConfig(title="SOLIS — Live Installation"))
    generator = DiffusionGenerator(prompt=PROMPT)

    final_image = None
    try:
        for frame in generator.generate_stream(steps=STEPS, preview_every=PREVIEW_EVERY):
            final_image = frame.image
            if not preview.pump():
                return
            preview.show(frame.image, frame.step, frame.total_steps, show_status=True)

        if final_image is None:
            return

        final_image.save(OUTPUT_FILE, format="PNG")
        print("Saved:", OUTPUT_FILE)

        preview.show_final_fullscreen(final_image)
        preview.wait_until_exit()
    finally:
        preview.close()


if __name__ == "__main__":
    run()
