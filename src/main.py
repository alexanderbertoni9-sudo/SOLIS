from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
import queue
import random
import re
import shlex
import sys
import threading
from typing import Any

from PIL import Image

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from model import DiffusionConfig, DiffusionModel, GenerationCancelled

DEFAULT_MODEL = "segmind/tiny-sd"
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512
DEFAULT_STEPS = 20
DEFAULT_PREVIEW_EVERY = 1
DEFAULT_GUIDANCE_SCALE = 7.5
PROMPT_POOL: tuple[str, ...] = (
    "Wind turbines producing renewable energy at sunrise.",
    "Wind turbines and solar panels on a green field generating clean power.",
    "A modern solar farm stretching across rolling hills under golden light.",
    "A coastal renewable energy hub with offshore wind turbines and solar arrays.",
    "A futuristic eco-city powered by rooftop solar and vertical wind turbines.",
    "Hydroelectric dam with clean energy flowing to a nearby smart city.",
    "A community microgrid with batteries, solar rooftops, and small wind turbines.",
    "A desert renewable plant with mirrors and solar panels powering the region.",
    "An energy control center monitoring wind, solar, and battery storage.",
    "A clean transportation network of EV buses charging from renewable stations.",
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "output")
DEFAULT_MODEL_DIR = os.environ.get(
    "SOLIS_MODEL_DIR",
    os.path.join(ROOT, "models", "segmind-tiny-sd"),
)


def _style_id(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()[:8]


def _slug_prompt(prompt: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", prompt.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:36] if slug else "scene"


def build_output_path(prompt: str, seed: int) -> str:
    style_id = _style_id(prompt)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    slug = _slug_prompt(prompt)
    nonce = os.urandom(2).hex()
    base_name = f"solis_{stamp}_{slug}_s{seed}_{style_id}_{nonce}"
    output_path = os.path.join(OUTPUT_DIR, f"{base_name}.png")
    n = 1
    while os.path.exists(output_path):
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}_{n}.png")
        n += 1
    return output_path


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
    return True, "Display context appears available."


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a local image with live fullscreen diffusion preview."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id (Hugging Face).")
    parser.add_argument(
        "--model-dir",
        default=None,
        help=(
            "Local model snapshot directory. "
            "Defaults to a pre-downloaded local path for the default model."
        ),
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Image width.")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Image height.")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Inference steps.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducibility.")
    parser.add_argument(
        "--preview-every",
        type=int,
        default=DEFAULT_PREVIEW_EVERY,
        help="Decode/display every N steps.",
    )
    parser.add_argument("--no-open", action="store_true", help="Generate only, no fullscreen viewer.")
    return parser.parse_args()


def save_outputs(final_image: Image.Image, output_path: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final_image.save(output_path, format="PNG")
    latest = os.path.join(OUTPUT_DIR, "solis_latest.png")
    if os.path.abspath(output_path) != os.path.abspath(latest):
        final_image.save(latest, format="PNG")


def prune_output_images(keep_recent: int = 4) -> list[str]:
    if keep_recent < 1:
        keep_recent = 1

    entries: list[tuple[float, str]] = []
    if not os.path.isdir(OUTPUT_DIR):
        return []

    for entry in os.scandir(OUTPUT_DIR):
        if not entry.is_file():
            continue
        name = entry.name
        if name == "solis_latest.png":
            continue
        if not (name.startswith("solis_") and name.endswith(".png")):
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        entries.append((mtime, entry.path))

    # Newest first; anything after keep_recent is old enough to delete.
    entries.sort(key=lambda item: item[0], reverse=True)
    to_delete = entries[keep_recent:]

    deleted: list[str] = []
    for _, path in to_delete:
        try:
            os.remove(path)
            deleted.append(os.path.abspath(path))
        except OSError as exc:
            print(f"Warning: could not delete old image: {path} ({exc})")
    return deleted


def main() -> None:
    args = parse_args()
    prompt = random.choice(PROMPT_POOL)
    seed = args.seed if args.seed is not None else random.randint(1, 99999999)
    output_path = build_output_path(prompt, seed)
    model_dir = args.model_dir
    if model_dir is None and args.model == DEFAULT_MODEL:
        model_dir = DEFAULT_MODEL_DIR

    print("Generating image locally...")
    print(f"Prompt: {prompt}")
    print(f"Model: {args.model}")
    if model_dir:
        print(f"Model source: {os.path.abspath(model_dir)}")
    print(f"Style ID: {_style_id(prompt)}")
    print(f"Size: {args.width}x{args.height}")
    print(f"Steps: {args.steps}")
    print(f"Seed: {seed}")

    cfg = DiffusionConfig(
        prompt=prompt,
        model_id=args.model,
        model_dir=model_dir,
        width=args.width,
        height=args.height,
        steps=args.steps,
        seed=seed,
        preview_every=max(1, args.preview_every),
        guidance_scale=DEFAULT_GUIDANCE_SCALE,
    )
    model = DiffusionModel(cfg)

    viewer: Any = None
    display_reason = ""
    display_available = False
    want_viewer = not args.no_open
    if want_viewer:
        context_ok, context_reason = detect_display_context()
        display_available = context_ok
        display_reason = context_reason
        if not context_ok and sys.platform.startswith("linux"):
            attached, attach_reason = try_attach_linux_desktop_display()
            if attached:
                context_ok, context_reason = True, attach_reason
                display_available = True
                display_reason = context_reason
            else:
                display_available = False
                display_reason = f"{context_reason} {attach_reason}"
        if context_ok:
            try:
                from viewer import FullscreenViewer, ViewerConfig
                viewer = FullscreenViewer(ViewerConfig(title="SOLIS - Live Diffusion"))
                viewer.show_loading("Loading model...")
            except Exception as exc:
                display_available = False
                display_reason = f"Fullscreen viewer init failed: {exc}"
                viewer = None

    event_q: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=8)
    cancel_event = threading.Event()

    def enqueue(name: str, data: object) -> None:
        if name == "preview":
            try:
                event_q.put_nowait((name, data))
            except queue.Full:
                try:
                    event_q.get_nowait()
                except queue.Empty:
                    pass
                try:
                    event_q.put_nowait((name, data))
                except queue.Full:
                    pass
            return
        event_q.put((name, data))

    def on_status(message: str) -> None:
        enqueue("status", message)

    def on_step(step: int, total: int) -> None:
        enqueue("step", (step, total))

    def on_preview(image: Image.Image, step: int, total: int) -> None:
        enqueue("preview", (image, step, total))

    def worker() -> None:
        try:
            final = model.generate(
                on_status=on_status,
                on_step=on_step,
                on_preview=on_preview,
                should_cancel=cancel_event.is_set,
            )
            enqueue("final", final)
        except GenerationCancelled:
            enqueue("cancelled", "Generation cancelled by user.")
        except Exception as exc:
            enqueue("error", str(exc))
        finally:
            enqueue("done", None)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    done = False
    final_image: Image.Image | None = None
    error_message: str | None = None
    status_msg = "Loading model..."
    last_step = 0
    last_total = max(1, args.steps)
    last_percent_printed = -1
    spinner = ["|", "/", "-", "\\"]
    spinner_idx = 0
    has_preview_frame = False
    user_cancelled = False

    while not done:
        if viewer and not viewer.pump():
            user_cancelled = True
            cancel_event.set()
            viewer.close()
            viewer = None
            print("Cancel requested by user. Stopping generation...")

        try:
            event, payload = event_q.get(timeout=0.05)
        except queue.Empty:
            if viewer and not has_preview_frame and not user_cancelled:
                viewer.show_loading(f"{status_msg} {spinner[spinner_idx]}")
                spinner_idx = (spinner_idx + 1) % len(spinner)
            continue

        if event == "status":
            status_msg = str(payload)
        elif event == "step":
            last_step, last_total = payload  # type: ignore[misc]
            percent = int((last_step / max(1, last_total)) * 100)
            if not viewer and percent != last_percent_printed:
                print(f"[{percent:3d}%] Diffusion step {last_step}/{last_total}")
                last_percent_printed = percent
        elif event == "preview":
            image, step, total = payload  # type: ignore[misc]
            has_preview_frame = True
            if viewer:
                viewer.show_frame(image, step, total, prompt)
        elif event == "final":
            final_image = payload  # type: ignore[assignment]
        elif event == "error":
            error_message = str(payload)
        elif event == "cancelled":
            user_cancelled = True
        elif event == "done":
            done = True

    thread.join(timeout=5.0)

    if user_cancelled:
        if viewer:
            viewer.close()
            viewer = None
        print("Generation cancelled by user.")
        return

    if error_message is not None:
        if viewer:
            viewer.close()
            viewer = None
        print(f"Image generation failed: {error_message}")
        raise SystemExit(1)
    if final_image is None:
        if viewer:
            viewer.close()
            viewer = None
        print("Image generation failed: no final image returned.")
        raise SystemExit(1)

    save_outputs(final_image, output_path)
    valid, reason, size_bytes = verify_generated_image(output_path)
    if not valid:
        print(f"Image verification failed: {reason}")
        raise SystemExit(1)

    abs_path = os.path.abspath(output_path)
    print(f"Image generated successfully: {abs_path}")
    print(f"File size: {size_bytes / 1024.0:.1f} KB")
    deleted = prune_output_images(keep_recent=4)
    if deleted:
        print(f"Cleanup: deleted {len(deleted)} old image(s) to save space.")

    if args.no_open:
        if viewer:
            viewer.close()
            viewer = None
        return

    if not display_available:
        if viewer:
            viewer.close()
            viewer = None
        print(f"Image generated successfully; viewer skipped: {display_reason}")
        print(f'Open from desktop session with: {manual_open_command(abs_path)}')
        return

    # Hold final image in the existing viewer if still open. Otherwise open once.
    try:
        if viewer is None:
            from viewer import FullscreenViewer, ViewerConfig
            viewer = FullscreenViewer(ViewerConfig(title="SOLIS - Final Image"))
        if display_reason:
            print(display_reason)
        viewer.show_final(final_image, prompt)
        viewer.wait_until_exit()
    except Exception as exc:
        print(f"Fullscreen hold failed: {exc}")
        print(f'Open manually with: {manual_open_command(abs_path)}')
    finally:
        if viewer:
            viewer.close()


if __name__ == "__main__":
    main()
