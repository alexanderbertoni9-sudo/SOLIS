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


def should_snapshot(step: int, total: int, snapshots: int, last_bucket: int) -> tuple[bool, int]:
    """
    Robust snapshot scheduler based on percent buckets.

    Returns:
      (should_update, new_bucket)

    Example: snapshots=8 -> buckets 1..8 at ~12.5%, 25%, ... 100%
    """
    if total <= 0:
        return True, last_bucket

    frac = max(0.0, min(1.0, step / total))
    bucket = int(frac * snapshots)  # 0..snapshots

    if bucket > last_bucket:
        return True, bucket
    return False, last_bucket
