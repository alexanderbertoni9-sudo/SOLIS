from __future__ import annotations
from PIL import Image, ImageDraw


def overlay_progress(img: Image.Image, step: int, total: int) -> Image.Image:
    """
    E-paper friendly overlay:
    - Big stable top band (good for partial refresh)
    - Large progress text
    - Thick progress bar
    """
    img = img.convert("RGB").copy()
    w, h = img.size
    d = ImageDraw.Draw(img)

    frac = 0 if total <= 0 else max(0.0, min(1.0, step / total))
    pct = int(frac * 100)

    # Big top band
    band_h = 72
    d.rectangle((0, 0, w, band_h), fill=(0, 0, 0))

    # Text
    d.text((16, 14), f"SOLIS • generating {pct}%  ({step}/{total})", fill=(255, 255, 255))

    # Thick progress bar
    bar_x0, bar_y0 = 16, 42
    bar_x1, bar_y1 = w - 16, 62
    d.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), outline=(255, 255, 255), width=2)

    fill_w = int((bar_x1 - bar_x0 - 4) * frac)
    d.rectangle((bar_x0 + 2, bar_y0 + 2, bar_x0 + 2 + fill_w, bar_y1 - 2), fill=(255, 255, 255))

    return img


def should_snapshot(
    step: int,
    total: int,
    snapshots: int,
    last_bucket: int,
    hide_frac: float = 0.18,
) -> tuple[bool, int]:
    """
    Snapshot scheduler for "gallery-like" generation on slow e-paper.

    - Hides early noisy diffusion steps (hide_frac of total).
    - Then emits ~`snapshots` updates evenly across remaining steps.
    - Always emits the final step (100%).
    - Uses `last_bucket` to prevent duplicate updates.

    Returns:
      (should_update, new_bucket)
    """
    if total <= 0:
        return True, last_bucket

    # Always show the final frame
    if step >= total:
        return True, snapshots

    # Hide early noisy steps
    hide_until = int(total * hide_frac)
    if step < hide_until:
        return False, last_bucket

    remaining = max(1, total - hide_until)       # steps available after hide
    progressed = max(0, step - hide_until)       # progress within remaining

    # Bucket index goes 0..snapshots-1 during generation, then snapshots at final
    frac = max(0.0, min(1.0, progressed / remaining))
    bucket = int(frac * snapshots)               # 0..snapshots (but final handled above)
    if bucket >= snapshots:
        bucket = snapshots - 1

    if bucket > last_bucket:
        return True, bucket
    return False, last_bucket
