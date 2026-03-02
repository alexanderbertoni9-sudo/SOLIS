from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import math
import os
import random
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

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


def _style_id(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()[:8]


def _slug_prompt(prompt: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", prompt.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:36] if slug else "scene"


def verify_generated_image(path: str) -> tuple[bool, str, int]:
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return False, "File was not created.", 0

    try:
        size_bytes = os.path.getsize(abs_path)
    except OSError as exc:
        return False, f"Could not read file size: {exc}", 0

    if size_bytes <= 0:
        return False, "File was created but is empty.", size_bytes

    try:
        with Image.open(abs_path) as img:
            img.verify()
    except Exception as exc:
        return False, f"Generated file is not a valid image: {exc}", size_bytes

    return True, "Image file is valid.", size_bytes


def manual_open_command(path: str) -> str:
    abs_path = os.path.abspath(path)
    if sys.platform == "darwin":
        return f"open {shlex.quote(abs_path)}"
    if os.name == "nt":
        return f'start "" "{abs_path}"'
    return f'xdg-open "{abs_path}"'


def detect_display_context() -> tuple[bool, str]:
    if sys.platform.startswith("linux"):
        display = os.environ.get("DISPLAY")
        wayland = os.environ.get("WAYLAND_DISPLAY")
        if not display and not wayland:
            return False, "DISPLAY/WAYLAND_DISPLAY is not set in this terminal session."

    try:
        import tkinter as tk
    except Exception as exc:
        return False, f"tkinter import failed: {exc}"

    try:
        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return True, "Display context is available."
    except Exception as exc:
        return False, f"Tk display initialization failed: {exc}"


def try_attach_linux_desktop_display() -> tuple[bool, str]:
    if not sys.platform.startswith("linux"):
        return False, "Auto-attach is only supported on Linux."

    x11_socket = "/tmp/.X11-unix/X0"
    if not os.path.exists(x11_socket):
        return False, "No X11 desktop socket found at /tmp/.X11-unix/X0."

    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"

    xauthority = os.path.expanduser("~/.Xauthority")
    if os.path.exists(xauthority) and not os.environ.get("XAUTHORITY"):
        os.environ["XAUTHORITY"] = xauthority

    ok, reason = detect_display_context()
    if ok:
        return True, f'Attached to desktop display (DISPLAY={os.environ.get("DISPLAY", "")}).'
    return False, f"Auto-attach attempt failed: {reason}"


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
        d = self._prompt_digest()
        renewable = self._contains_any(
            ("renewable", "clean energy", "green energy", "sustainable", "solar", "wind")
        )
        futuristic = self._contains_any(("futuristic", "future", "sci-fi", "cyberpunk", "neon"))
        stormy = self._contains_any(("storm", "rain", "thunder", "dark clouds"))
        cloudy = stormy or self._contains_any(("cloud", "mist", "fog", "overcast"))
        has_ocean = self._contains_any(("ocean", "sea", "coast", "beach", "shore"))
        has_mountains = self._contains_any(("mountain", "alps", "peaks", "cliff"))
        has_hills = self._contains_any(("hill", "valley", "meadow", "grassland"))
        has_city = self._contains_any(("city", "urban", "skyline", "buildings", "downtown")) or futuristic
        has_wind = self._contains_any(("wind turbine", "wind farm", "turbine", "windmill"))
        has_solar = self._contains_any(("solar", "solar panel", "photovoltaic", "pv"))
        has_temple = self._contains_any(("temple", "shrine", "pagoda"))

        if renewable and not (has_city or has_wind or has_solar):
            has_city = True
            has_wind = True
            has_solar = True

        has_time_word = self._contains_any(
            ("night", "moon", "stars", "midnight", "sunset", "dusk", "evening", "golden hour", "sunrise", "dawn", "morning")
        )
        if self._contains_any(("night", "moon", "stars", "midnight")):
            time_of_day = "night"
        elif self._contains_any(("sunset", "dusk", "evening", "golden hour")):
            time_of_day = "sunset"
        elif self._contains_any(("sunrise", "dawn", "morning")):
            time_of_day = "sunrise"
        else:
            time_of_day = "day"

        # If prompt does not specify enough scene info, use prompt hash fallback
        # so different prompts still create clearly different scenes.
        if not has_time_word:
            time_of_day = ("day", "sunrise", "sunset", "night")[d[0] % 4]
        if not (stormy or cloudy):
            cloudy = d[1] % 3 == 0
        if not (has_ocean or has_mountains or has_hills):
            terrain_choice = d[2] % 3
            if terrain_choice == 0:
                has_ocean = True
            elif terrain_choice == 1:
                has_mountains = True
            else:
                has_hills = True
        if not (has_city or has_wind or has_solar or has_temple):
            object_choice = d[3] % 4
            has_city = object_choice == 0
            has_wind = object_choice == 1
            has_solar = object_choice == 2
            has_temple = object_choice == 3
        if not has_hills and not has_ocean and not has_mountains:
            has_hills = True

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

    def render(
        self,
        progress_cb: Callable[[int, str], None] | None = None,
    ) -> Image.Image:
        rng = random.Random(self._effective_seed())
        if progress_cb:
            progress_cb(5, "Analyzing prompt")
        profile = self._profile()
        sky_top, sky_bottom, sun_color = self._sky_palette(profile)
        shift = self._color_shift()
        sky_top = self._shift_color(sky_top, shift)
        sky_bottom = self._shift_color(sky_bottom, shift)
        sun_color = self._shift_color(sun_color, shift)

        if progress_cb:
            progress_cb(15, "Painting sky")
        scene = self._build_gradient(sky_top, sky_bottom).convert("RGBA")
        if progress_cb:
            progress_cb(25, "Drawing sun/moon and clouds")
        self._draw_sun_or_moon(scene, profile, rng, sun_color)
        self._draw_clouds(scene, profile, rng)
        if profile.time_of_day == "night":
            self._draw_stars(scene, rng)

        d = ImageDraw.Draw(scene, "RGBA")
        horizon_base = 0.57 if not profile.has_ocean else 0.54
        horizon_jitter = (self._prompt_digest()[11] % 11 - 5) / 100.0
        horizon_y = int(self.height * (horizon_base + horizon_jitter))
        if progress_cb:
            progress_cb(35, "Building landscape")
        if profile.has_ocean:
            self._draw_ocean(d, horizon_y, rng)
        else:
            d.rectangle((0, horizon_y, self.width, self.height), fill=(70, 126, 82, 255))

        if progress_cb:
            progress_cb(50, "Drawing scene objects")
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
        if progress_cb:
            progress_cb(75, "Applying texture")
        grain = Image.effect_noise((self.width // 2, self.height // 2), 14).convert("L")
        grain = grain.resize((self.width, self.height), Image.Resampling.BICUBIC)
        grain_rgb = ImageOps.colorize(grain, (40, 40, 40), (200, 200, 200)).convert("RGBA")
        scene = ImageChops.soft_light(scene, grain_rgb)

        if progress_cb:
            progress_cb(90, "Final polish")
        polished = scene.filter(ImageFilter.GaussianBlur(radius=0.35))
        polished = ImageEnhance.Contrast(polished).enhance(1.10)
        polished = ImageEnhance.Color(polished).enhance(1.12)
        if progress_cb:
            progress_cb(100, "Done")
        return polished.convert("RGB")


def generate_image(
    prompt: str,
    width: int,
    height: int,
    seed: int,
    output_path: str | None = None,
    progress_cb: Callable[[int, str], None] | None = None,
) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model = LocalImageModel(prompt=prompt, width=width, height=height, seed=seed)
    image = model.render(progress_cb=progress_cb)

    style_id = _style_id(prompt)
    if output_path is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        slug = _slug_prompt(prompt)
        nonce = os.urandom(2).hex()
        base_name = f"solis_{stamp}_{slug}_s{seed}_{style_id}_{nonce}"
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}.png")
        n = 1
        while os.path.exists(output_path):
            output_path = os.path.join(OUTPUT_DIR, f"{base_name}_{n}.png")
            n += 1

    image.save(output_path, format="PNG")
    latest_path = os.path.join(OUTPUT_DIR, "solis_latest.png")
    if output_path != latest_path:
        image.save(latest_path, format="PNG")

    valid, reason, _ = verify_generated_image(output_path)
    if not valid:
        raise RuntimeError(f"Image generation failed verification. {reason}")

    return output_path


def open_image(path: str) -> tuple[bool, str]:
    abs_path = os.path.abspath(path)
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", abs_path])
            return True, "Opened with macOS open."
        if os.name == "nt":
            os.startfile(abs_path)  # type: ignore[attr-defined]
            return True, "Opened with Windows startfile."
        subprocess.Popen(
            ["xdg-open", abs_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True, "Opened with xdg-open."
    except Exception as exc:
        return False, str(exc)


def show_image_fullscreen(path: str) -> tuple[bool, str]:
    try:
        import tkinter as tk
        from PIL import ImageTk
    except Exception as exc:
        return False, f"Fullscreen viewer dependency error: {exc}"

    try:
        root = tk.Tk()
        root.configure(bg="black")
        root.attributes("-fullscreen", True)
        root.bind("<Escape>", lambda _event: root.destroy())
        root.bind("q", lambda _event: root.destroy())

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        img = Image.open(os.path.abspath(path)).convert("RGB")
        fitted = ImageOps.contain(img, (sw, sh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(fitted)

        canvas = tk.Canvas(root, width=sw, height=sh, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(sw // 2, sh // 2, image=tk_img, anchor="center")
        canvas.image = tk_img

        root.mainloop()
        return True, "Fullscreen viewer closed normally."
    except Exception as exc:
        return False, str(exc)


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
    print(f"Style ID: {_style_id(prompt)}")
    print(f"Size: {args.width}x{args.height}")
    print(f"Seed: {seed}")

    is_tty = sys.stdout.isatty()

    def report_progress(percent: int, stage: str) -> None:
        if is_tty:
            print(f"\r[{percent:3d}%] {stage:<24}", end="", flush=True)
        else:
            print(f"[{percent:3d}%] {stage}")

    try:
        path = generate_image(
            prompt=prompt,
            width=args.width,
            height=args.height,
            seed=seed,
            output_path=args.out,
            progress_cb=report_progress,
        )
    except RuntimeError as exc:
        if is_tty:
            print()
        print(f"Image generation failed: {exc}")
        raise SystemExit(1) from exc
    if is_tty:
        print()

    abs_path = os.path.abspath(path)
    valid, verify_reason, size_bytes = verify_generated_image(abs_path)
    if not valid:
        print(f"Image verification failed after save: {verify_reason}")
        raise SystemExit(1)

    size_kb = size_bytes / 1024.0
    print(f"Image generated successfully: {abs_path}")
    print(f"File size: {size_kb:.1f} KB")
    if not args.no_open:
        context_ok, context_reason = detect_display_context()
        if not context_ok and sys.platform.startswith("linux"):
            attached, attach_reason = try_attach_linux_desktop_display()
            if attached:
                context_ok, context_reason = True, attach_reason
            else:
                context_reason = f"{context_reason} {attach_reason}"
        if not context_ok:
            print(f"Image generated successfully; viewer skipped: {context_reason}")
            print(f'Open from desktop session with: {manual_open_command(abs_path)}')
        else:
            print(context_reason)
            print("Opening fullscreen viewer (Esc or q to close)...")
            fullscreen_ok, fullscreen_reason = show_image_fullscreen(abs_path)
            if fullscreen_ok:
                print("Closed fullscreen viewer.")
            else:
                print(f"Fullscreen viewer failed: {fullscreen_reason}")
                print("Trying non-fullscreen image viewer...")
                opened, open_reason = open_image(abs_path)
                if opened:
                    print("Opened non-fullscreen image viewer.")
                else:
                    print(f"Could not auto-open viewer: {open_reason}")
                    print(f'Open manually with: {manual_open_command(abs_path)}')


if __name__ == "__main__":
    main()
