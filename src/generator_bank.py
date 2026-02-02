from __future__ import annotations
import os, random
from dataclasses import dataclass
from typing import Iterable, List, Optional
from PIL import Image, ImageFilter, ImageEnhance

@dataclass
class GenFrame:
    step: int
    total_steps: int
    image: Image.Image

class ImageBankGenerator:
    def __init__(self, bank_dir: str):
        self.bank_dir = bank_dir
        self.paths = self._scan_images(bank_dir)
        if not self.paths:
            raise FileNotFoundError(
                f"No images found in '{bank_dir}'. Put images in image_bank/."
            )

    def _scan_images(self, bank_dir: str) -> List[str]:
        exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
        if not os.path.isdir(bank_dir):
            return []
        return [
            os.path.join(bank_dir, f)
            for f in os.listdir(bank_dir)
            if f.lower().endswith(exts)
        ]

    def generate(self, total_steps: int = 25, seed: Optional[int] = None) -> Iterable[GenFrame]:
        rng = random.Random(seed)
        path = rng.choice(self.paths)
        base = Image.open(path).convert("RGB")

        for step in range(total_steps):
            t = (step + 1) / total_steps
            img = base.copy()

            blur_radius = (1.0 - t) * 10.0
            if blur_radius > 0.05:
                img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            img = ImageEnhance.Contrast(img).enhance(0.55 + 0.45 * t)
            img = ImageEnhance.Brightness(img).enhance(0.85 + 0.15 * t)

            yield GenFrame(step=step + 1, total_steps=total_steps, image=img)

        yield GenFrame(step=total_steps, total_steps=total_steps, image=base)
