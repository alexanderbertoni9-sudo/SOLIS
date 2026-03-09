from __future__ import annotations

import argparse
import hashlib
import math
import os
import random
import subprocess
import sys
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

DEFAULT_PROMPT = "A clean, futuristic city powered by renewable energy at sunrise"
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "output")


@dataclass
class LocalImageModel:
    prompt: str
    width: int
    height: int
    seed: int

    def _digest(self) -> bytes:
        return hashlib.sha256(f"{self.prompt}|{self.seed}".encode("utf-8")).digest()

    def _palette(self) -> list[tuple[int, int, int]]:
        d = self._digest()
        return [
            (30 + d[0] % 120, 20 + d[1] % 120, 60 + d[2] % 140),
            (100 + d[3] % 120, 70 + d[4] % 120, 20 + d[5] % 120),
            (160 + d[6] % 95, 130 + d[7] % 100, 70 + d[8] % 100),
            (210 + d[9] % 45, 180 + d[10] % 60, 120 + d[11] % 70),
        ]

    def _gradient(self, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        for y in range(self.height):
            t = y / max(self.height - 1, 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            draw.line((0, y, self.width, y), fill=(r, g, b))
        return img

    def _draw_energy_arcs(self, img: Image.Image, rng: random.Random) -> None:
        draw = ImageDraw.Draw(img, "RGBA")
        wave_count = 6 + int(self.width / 180)
        for i in range(wave_count):
            amp = rng.randint(self.height // 12, self.height // 5)
            freq = rng.uniform(0.004, 0.012)
            phase = rng.uniform(0, math.tau)
            y_mid = int(self.height * (0.25 + 0.1 * i))
            points = []
            for x in range(0, self.width, 8):
                y = y_mid + int(amp * math.sin((x * freq) + phase))
                points.append((x, y))
            alpha = 80 + i * 8
            color = (255, 220 - i * 12, 140 + i * 8, min(alpha, 180))
            draw.line(points, fill=color, width=2 + (i % 2))

    def _draw_orbs(self, img: Image.Image, rng: random.Random, colors: list[tuple[int, int, int]]) -> None:
        draw = ImageDraw.Draw(img, "RGBA")
        orb_count = 30 + int(self.width / 40)
        for _ in range(orb_count):
            radius = rng.randint(self.width // 60, self.width // 14)
            x = rng.randint(0, self.width)
            y = rng.randint(0, self.height)
            color = colors[rng.randint(0, len(colors) - 1)]
            alpha = rng.randint(35, 120)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=(color[0], color[1], color[2], alpha),
            )

    def render(self) -> Image.Image:
        rng = random.Random(self.seed)
        colors = self._palette()
        base = self._gradient(colors[0], colors[1])

        # Add soft texture to avoid flat backgrounds while staying lightweight.
        noise = Image.effect_noise((self.width // 3, self.height // 3), 48).convert("L")
        noise = noise.resize((self.width, self.height), Image.BICUBIC)
        texture = ImageOps.colorize(noise, colors[2], colors[3])
        mixed = Image.blend(base, texture, alpha=0.24).convert("RGBA")

        self._draw_energy_arcs(mixed, rng)
        self._draw_orbs(mixed, rng, colors)

        glow = mixed.filter(ImageFilter.GaussianBlur(radius=8))
        merged = ImageChops.screen(mixed, glow)
        merged = ImageEnhance.Contrast(merged).enhance(1.12)
        merged = ImageEnhance.Color(merged).enhance(1.08)
        return merged.convert("RGB")


def generate_image(
    prompt: str,
    width: int,
    height: int,
    seed: int,
    output_path: str | None = None,
) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model = LocalImageModel(prompt=prompt, width=width, height=height, seed=seed)
    image = model.render()

    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "solis_latest.png")

    image.save(output_path, format="PNG")
    return output_path


def open_image(path: str) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
            return True
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
            return True
        subprocess.Popen(
            ["xdg-open", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one image with a lightweight local model."
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Text description of the image to generate.",
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Image width in pixels.")
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help="Image height in pixels.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for repeatability.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output file path. Example: output/my_image.jpg",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the generated image after saving.",
    )

    args = parser.parse_args()
    seed = args.seed if args.seed is not None else random.randint(1, 99999999)
    prompt = args.prompt
    if prompt is None:
        if sys.stdin.isatty():
            typed = input(
                f'Prompt (press Enter for default: "{DEFAULT_PROMPT}"): '
            ).strip()
            prompt = typed or DEFAULT_PROMPT
        else:
            prompt = DEFAULT_PROMPT

    print("Generating image locally...")
    print(f"Prompt: {prompt}")
    print("Model: local-lightweight-v1")
    print(f"Size: {args.width}x{args.height}")
    print(f"Seed: {seed}")

    path = generate_image(
        prompt=prompt,
        width=args.width,
        height=args.height,
        seed=seed,
        output_path=args.out,
    )

    print(f"Saved: {path}")
    if not args.no_open:
        if open_image(path):
            print("Opened image viewer.")
        else:
            print("Could not auto-open viewer. Open the file manually.")


if __name__ == "__main__":
    main()
