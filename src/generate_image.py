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
class PromptProfile:
    time_of_day: str
    has_ocean: bool
    has_hills: bool
    has_mountains: bool
    has_city: bool
    has_wind: bool
    has_solar: bool
    has_temple: bool
    futuristic: bool
    cloudy: bool
    stormy: bool


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(a[0] * (1 - t) + b[0] * t),
        int(a[1] * (1 - t) + b[1] * t),
        int(a[2] * (1 - t) + b[2] * t),
    )


def _clamp(v: int, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, v))


@dataclass
class LocalImageModel:
    prompt: str
    width: int
    height: int
    seed: int

    def _prompt_digest(self) -> bytes:
        return hashlib.sha256(self.prompt.strip().lower().encode("utf-8")).digest()

    def _effective_seed(self) -> int:
        prompt_bits = int.from_bytes(self._prompt_digest()[:8], byteorder="big")
        return (self.seed ^ prompt_bits) & 0x7FFFFFFFFFFFFFFF

    def _color_shift(self) -> tuple[int, int, int]:
        d = self._prompt_digest()
        return ((d[8] % 41) - 20, (d[9] % 41) - 20, (d[10] % 41) - 20)

    def _shift_color(self, color: tuple[int, int, int], shift: tuple[int, int, int]) -> tuple[int, int, int]:
        return (
            _clamp(color[0] + shift[0]),
            _clamp(color[1] + shift[1]),
            _clamp(color[2] + shift[2]),
        )

    def _contains_any(self, words: tuple[str, ...]) -> bool:
        p = self.prompt.lower()
        return any(w in p for w in words)

    def _profile(self) -> PromptProfile:
        renewable = self._contains_any(
            ("renewable", "clean energy", "green energy", "sustainable", "solar", "wind")
        )
        futuristic = self._contains_any(("futuristic", "future", "sci-fi", "cyberpunk", "neon"))
        stormy = self._contains_any(("storm", "rain", "thunder", "dark clouds"))
        cloudy = stormy or self._contains_any(("cloud", "mist", "fog", "overcast"))
        has_ocean = self._contains_any(("ocean", "sea", "coast", "beach", "shore"))
        has_mountains = self._contains_any(("mountain", "alps", "peaks", "cliff"))
        has_hills = self._contains_any(("hill", "valley", "meadow", "grassland")) or not has_mountains
        has_city = self._contains_any(("city", "urban", "skyline", "buildings", "downtown")) or futuristic
        has_wind = self._contains_any(("wind turbine", "wind farm", "turbine", "windmill"))
        has_solar = self._contains_any(("solar", "solar panel", "photovoltaic", "pv"))
        has_temple = self._contains_any(("temple", "shrine", "pagoda"))

        if renewable and not (has_city or has_wind or has_solar):
            has_city = True
            has_wind = True
            has_solar = True

        if self._contains_any(("night", "moon", "stars", "midnight")):
            time_of_day = "night"
        elif self._contains_any(("sunset", "dusk", "evening", "golden hour")):
            time_of_day = "sunset"
        elif self._contains_any(("sunrise", "dawn", "morning")):
            time_of_day = "sunrise"
        else:
            time_of_day = "day"

        if not (has_city or has_wind or has_solar or has_temple):
            has_city = True

        return PromptProfile(
            time_of_day=time_of_day,
            has_ocean=has_ocean,
            has_hills=has_hills,
            has_mountains=has_mountains,
            has_city=has_city,
            has_wind=has_wind,
            has_solar=has_solar,
            has_temple=has_temple,
            futuristic=futuristic,
            cloudy=cloudy,
            stormy=stormy,
        )

    def _sky_palette(
        self, profile: PromptProfile
    ) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        if profile.time_of_day == "night":
            return (18, 24, 58), (58, 76, 120), (220, 225, 245)
        if profile.time_of_day == "sunset":
            return (44, 28, 66), (255, 142, 92), (255, 214, 138)
        if profile.time_of_day == "sunrise":
            return (58, 66, 118), (252, 179, 123), (255, 236, 160)
        return (66, 134, 210), (170, 225, 255), (255, 248, 188)

    def _build_gradient(self, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
        strip = Image.new("RGB", (1, self.height))
        pix = strip.load()
        for y in range(self.height):
            t = y / max(self.height - 1, 1)
            pix[0, y] = _mix(top, bottom, t)
        return strip.resize((self.width, self.height), Image.Resampling.BILINEAR)

    def _draw_sun_or_moon(
        self, img: Image.Image, profile: PromptProfile, rng: random.Random, sun_color: tuple[int, int, int]
    ) -> None:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        cx = int(self.width * (0.22 + rng.random() * 0.56))
        cy = int(self.height * (0.14 + rng.random() * 0.16))
        r = int(min(self.width, self.height) * 0.07)

        if profile.time_of_day == "night":
            moon = (226, 232, 248, 255)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=moon)
            d.ellipse((cx - int(r * 0.45), cy - r, cx + int(r * 0.75), cy + r), fill=(0, 0, 0, 0))
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*sun_color, 235))
            for i in range(3):
                rr = r + int((i + 1) * r * 0.9)
                alpha = max(18, 60 - i * 18)
                d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(*sun_color, alpha), width=2)

        img.alpha_composite(layer)

    def _draw_clouds(self, img: Image.Image, profile: PromptProfile, rng: random.Random) -> None:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        cloud_count = 6 if profile.cloudy else 3
        for _ in range(cloud_count):
            cx = rng.randint(0, self.width)
            cy = rng.randint(int(self.height * 0.08), int(self.height * 0.40))
            w = rng.randint(self.width // 9, self.width // 4)
            h = rng.randint(self.height // 20, self.height // 11)
            alpha = rng.randint(70, 128) if profile.cloudy else rng.randint(42, 88)
            cloud_color = (238, 241, 246, alpha)
            if profile.stormy:
                cloud_color = (158, 168, 185, alpha + 18)
            for i in range(5):
                ox = int((i - 2) * w * 0.22)
                oy = rng.randint(-h // 4, h // 4)
                rr = rng.randint(h // 2, h)
                d.ellipse((cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr), fill=cloud_color)
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius=2)))

    def _draw_stars(self, img: Image.Image, rng: random.Random) -> None:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        for _ in range(max(60, self.width // 8)):
            x = rng.randint(0, self.width - 1)
            y = rng.randint(0, int(self.height * 0.45))
            size = 1 if rng.random() < 0.85 else 2
            a = rng.randint(120, 220)
            d.ellipse((x, y, x + size, y + size), fill=(255, 255, 240, a))
        img.alpha_composite(layer)

    def _draw_mountains(self, d: ImageDraw.ImageDraw, horizon_y: int, rng: random.Random) -> None:
        for i in range(2):
            base = horizon_y + i * (self.height // 26)
            color = (70 + i * 24, 84 + i * 28, 96 + i * 28, 255)
            points = [(0, self.height), (0, base)]
            x = 0
            while x < self.width:
                peak = base - rng.randint(self.height // 8, self.height // 4)
                points.append((x, peak))
                x += rng.randint(self.width // 10, self.width // 5)
            points.extend([(self.width, base), (self.width, self.height)])
            d.polygon(points, fill=color)

    def _draw_hills(self, d: ImageDraw.ImageDraw, horizon_y: int, rng: random.Random) -> None:
        for i in range(2):
            base = horizon_y + i * (self.height // 16)
            color = (74 - i * 6, 124 - i * 8, 80 - i * 4, 255)
            points = [(0, self.height), (0, base)]
            for x in range(0, self.width + 1, max(10, self.width // 25)):
                wave = int(math.sin((x / self.width) * math.tau * (1.0 + i * 0.5) + rng.random()) * (self.height * 0.03))
                points.append((x, base - wave - rng.randint(0, self.height // 24)))
            points.extend([(self.width, base), (self.width, self.height)])
            d.polygon(points, fill=color)

    def _draw_ocean(self, d: ImageDraw.ImageDraw, horizon_y: int, rng: random.Random) -> None:
        d.rectangle((0, horizon_y, self.width, self.height), fill=(44, 110, 162, 255))
        for _ in range(max(50, self.width // 6)):
            y = rng.randint(horizon_y, self.height - 1)
            x = rng.randint(0, self.width - 1)
            line_w = rng.randint(self.width // 40, self.width // 12)
            d.line((x, y, min(self.width, x + line_w), y), fill=(170, 210, 230, 45), width=1)

    def _draw_city(self, d: ImageDraw.ImageDraw, horizon_y: int, rng: random.Random, futuristic: bool) -> None:
        base = horizon_y + self.height // 20
        color = (36, 46, 60, 255)
        glow = (115, 220, 255, 170) if futuristic else (252, 216, 148, 150)
        x = 0
        while x < self.width:
            w = rng.randint(self.width // 45, self.width // 16)
            h = rng.randint(self.height // 14, self.height // 4)
            y = base - h
            d.rectangle((x, y, x + w, base), fill=color)
            rows = max(3, h // 12)
            cols = max(2, w // 10)
            for row in range(rows):
                wy = y + 4 + row * max(6, h // rows)
                for col in range(cols):
                    wx = x + 3 + col * max(6, w // cols)
                    if rng.random() > 0.45:
                        d.rectangle((wx, wy, wx + 2, wy + 3), fill=glow)
            x += w + rng.randint(2, self.width // 80 + 2)

    def _draw_single_turbine(self, d: ImageDraw.ImageDraw, x: int, y: int, size: int, angle: float) -> None:
        mast_top = y - size
        d.line((x, y, x, mast_top), fill=(236, 239, 242, 255), width=max(2, size // 20))
        hub_r = max(2, size // 14)
        d.ellipse((x - hub_r, mast_top - hub_r, x + hub_r, mast_top + hub_r), fill=(245, 245, 245, 255))
        for i in range(3):
            blade_angle = angle + i * (math.tau / 3)
            x2 = x + int(math.cos(blade_angle) * size * 0.48)
            y2 = mast_top + int(math.sin(blade_angle) * size * 0.48)
            d.line((x, mast_top, x2, y2), fill=(248, 248, 248, 255), width=max(1, size // 22))

    def _draw_wind_farm(self, d: ImageDraw.ImageDraw, horizon_y: int, rng: random.Random) -> None:
        count = max(4, self.width // 170)
        for i in range(count):
            x = int((i + 0.7) * self.width / (count + 1))
            y = horizon_y + rng.randint(self.height // 35, self.height // 12)
            size = rng.randint(self.height // 8, self.height // 5)
            self._draw_single_turbine(d, x, y, size, angle=rng.random() * math.tau)

    def _draw_solar_panels(self, d: ImageDraw.ImageDraw, horizon_y: int, rng: random.Random) -> None:
        rows = 3
        start_y = horizon_y + self.height // 8
        for r in range(rows):
            y = start_y + r * (self.height // 16)
            left = self.width // 10 + r * (self.width // 40)
            right = self.width - self.width // 10 - r * (self.width // 40)
            panel_h = max(10, self.height // 24 - r * 2)
            panels = 6
            span = max(1, right - left)
            panel_w = max(20, span // panels - self.width // 90)
            for i in range(panels):
                x = left + i * (panel_w + self.width // 90)
                p1 = (x, y)
                p2 = (x + panel_w, y)
                p3 = (x + panel_w - panel_h // 2, y + panel_h)
                p4 = (x - panel_h // 2, y + panel_h)
                d.polygon((p1, p2, p3, p4), fill=(42, 68, 112, 245), outline=(96, 146, 220, 230))
                if rng.random() > 0.35:
                    d.line((p1[0] + 4, p1[1] + 2, p2[0] - 4, p2[1] + 2), fill=(168, 214, 255, 120), width=1)

    def _draw_temple(self, d: ImageDraw.ImageDraw, horizon_y: int) -> None:
        base_y = horizon_y + self.height // 10
        cx = self.width // 2
        w = self.width // 4
        h = self.height // 4
        d.polygon(((cx - w, base_y), (cx + w, base_y), (cx + w - 10, base_y + 24), (cx - w + 10, base_y + 24)), fill=(78, 62, 54, 255))
        d.rectangle((cx - w // 2, base_y - h // 2, cx + w // 2, base_y), fill=(108, 88, 74, 255))
        d.polygon(((cx - w // 2 - 20, base_y - h // 2), (cx + w // 2 + 20, base_y - h // 2), (cx, base_y - h)), fill=(134, 108, 88, 255))
        col_w = max(10, w // 12)
        for i in range(-2, 3):
            x = cx + i * (w // 6)
            d.rectangle((x - col_w // 2, base_y - h // 2, x + col_w // 2, base_y), fill=(164, 146, 128, 255))

    def render(self) -> Image.Image:
        rng = random.Random(self._effective_seed())
        profile = self._profile()
        sky_top, sky_bottom, sun_color = self._sky_palette(profile)
        shift = self._color_shift()
        sky_top = self._shift_color(sky_top, shift)
        sky_bottom = self._shift_color(sky_bottom, shift)
        sun_color = self._shift_color(sun_color, shift)

        scene = self._build_gradient(sky_top, sky_bottom).convert("RGBA")
        self._draw_sun_or_moon(scene, profile, rng, sun_color)
        self._draw_clouds(scene, profile, rng)
        if profile.time_of_day == "night":
            self._draw_stars(scene, rng)

        d = ImageDraw.Draw(scene, "RGBA")
        horizon_base = 0.57 if not profile.has_ocean else 0.54
        horizon_jitter = (self._prompt_digest()[11] % 11 - 5) / 100.0
        horizon_y = int(self.height * (horizon_base + horizon_jitter))
        if profile.has_ocean:
            self._draw_ocean(d, horizon_y, rng)
        else:
            d.rectangle((0, horizon_y, self.width, self.height), fill=(70, 126, 82, 255))

        if profile.has_mountains:
            self._draw_mountains(d, horizon_y, rng)
        if profile.has_hills:
            self._draw_hills(d, horizon_y, rng)
        if profile.has_city:
            self._draw_city(d, horizon_y, rng, profile.futuristic)
        if profile.has_wind:
            self._draw_wind_farm(d, horizon_y, rng)
        if profile.has_solar:
            self._draw_solar_panels(d, horizon_y, rng)
        if profile.has_temple:
            self._draw_temple(d, horizon_y)

        # Add subtle photographic grain + polish for a less flat result.
        grain = Image.effect_noise((self.width // 2, self.height // 2), 14).convert("L")
        grain = grain.resize((self.width, self.height), Image.Resampling.BICUBIC)
        grain_rgb = ImageOps.colorize(grain, (40, 40, 40), (200, 200, 200)).convert("RGBA")
        scene = ImageChops.soft_light(scene, grain_rgb)

        polished = scene.filter(ImageFilter.GaussianBlur(radius=0.35))
        polished = ImageEnhance.Contrast(polished).enhance(1.10)
        polished = ImageEnhance.Color(polished).enhance(1.12)
        return polished.convert("RGB")


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
    print(f"Style ID: {hashlib.sha256(prompt.strip().lower().encode('utf-8')).hexdigest()[:8]}")
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
