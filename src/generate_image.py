from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
import random
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

from PIL import Image, ImageOps

DEFAULT_PROMPT = "A clean, futuristic city powered by renewable energy at sunrise"
DEFAULT_MODEL_ID = os.environ.get("SOLIS_MODEL_ID", "segmind/tiny-sd")
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512
DEFAULT_STEPS = 20
DEFAULT_GUIDANCE_SCALE = 7.5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "output")


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
class LocalTextToImageModel:
    prompt: str
    model_id: str
    width: int
    height: int
    steps: int
    guidance_scale: float
    seed: int

    def _prepare_size(self) -> tuple[int, int]:
        # Stable Diffusion models generally require dimensions divisible by 8.
        width = max(256, (self.width // 8) * 8)
        height = max(256, (self.height // 8) * 8)
        return width, height

    def _pick_device(self, torch_module) -> tuple[str, object]:
        if torch_module.cuda.is_available():
            return "cuda", torch_module.float16
        if hasattr(torch_module.backends, "mps") and torch_module.backends.mps.is_available():
            return "mps", torch_module.float16
        return "cpu", torch_module.float32

    def render(self, progress_cb: Callable[[int, str], None] | None = None) -> Image.Image:
        try:
            import torch
            from diffusers import StableDiffusionPipeline
        except Exception as exc:
            raise RuntimeError(
                "Missing or incompatible text-to-image dependencies. "
                "Run ./setup.sh to install pinned versions."
            ) from exc

        width, height = self._prepare_size()
        if progress_cb:
            progress_cb(3, "Loading model")

        device, dtype = self._pick_device(torch)
        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
                use_safetensors=True,
            )
            pipe = pipe.to(device)
            pipe.set_progress_bar_config(disable=True)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load model '{self.model_id}'. "
                "Check first-run model download, disk space, and dependency compatibility."
            ) from exc

        if progress_cb:
            progress_cb(10, f"Model ready on {device}")

        try:
            generator = torch.Generator(device=device).manual_seed(self.seed)
        except Exception:
            # Some backends may not support explicit generator device construction.
            generator = torch.Generator().manual_seed(self.seed)

        steps = max(1, self.steps)
        if progress_cb:
            progress_cb(15, "Running diffusion")

        def _step_percent(step: int) -> int:
            # Map inference steps to 15-95%
            return min(95, 15 + int(((step + 1) / steps) * 80))

        def on_step(_step_index: int, _timestep: int, _latents) -> None:
            if progress_cb:
                progress_cb(
                    _step_percent(_step_index),
                    f"Diffusion step {_step_index + 1}/{steps}",
                )

        try:
            result = pipe(
                prompt=self.prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=self.guidance_scale,
                generator=generator,
                callback=on_step,
                callback_steps=1,
            )
        except Exception as exc:
            raise RuntimeError(
                "Text-to-image generation failed. "
                "Try fewer steps or smaller size (for example 512x512), and ensure setup installed compatible versions."
            ) from exc

        image = result.images[0].convert("RGB")
        if progress_cb:
            progress_cb(100, "Done")
        return image


def generate_image(
    prompt: str,
    model_id: str,
    width: int,
    height: int,
    steps: int,
    guidance_scale: float,
    seed: int,
    output_path: str | None = None,
    progress_cb: Callable[[int, str], None] | None = None,
) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model = LocalTextToImageModel(
        prompt=prompt,
        model_id=model_id,
        width=width,
        height=height,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed,
    )
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
        description="Generate one image with a local text-to-image diffusion model."
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Text prompt to generate.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_ID,
        help=f"Hugging Face model id. Default: {DEFAULT_MODEL_ID}",
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Image width in pixels.")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Image height in pixels.")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Inference steps.")
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=DEFAULT_GUIDANCE_SCALE,
        help="Prompt guidance strength (CFG scale).",
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
        help="Optional output file path. Example: output/my_image.png",
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
    print(f"Model: {args.model}")
    print(f"Style ID: {_style_id(prompt)}")
    print(f"Size: {args.width}x{args.height}")
    print(f"Steps: {args.steps}")
    print(f"Guidance scale: {args.guidance_scale}")
    print(f"Seed: {seed}")

    is_tty = sys.stdout.isatty()

    def report_progress(percent: int, stage: str) -> None:
        if is_tty:
            print(f"\r[{percent:3d}%] {stage:<28}", end="", flush=True)
        else:
            print(f"[{percent:3d}%] {stage}")

    try:
        path = generate_image(
            prompt=prompt,
            model_id=args.model,
            width=args.width,
            height=args.height,
            steps=args.steps,
            guidance_scale=args.guidance_scale,
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

    print(f"Image generated successfully: {abs_path}")
    print(f"File size: {size_bytes / 1024.0:.1f} KB")

    if args.no_open:
        return

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
        return

    print(context_reason)
    print("Opening fullscreen viewer (Esc or q to close)...")
    fullscreen_ok, fullscreen_reason = show_image_fullscreen(abs_path)
    if fullscreen_ok:
        print("Closed fullscreen viewer.")
        return

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
