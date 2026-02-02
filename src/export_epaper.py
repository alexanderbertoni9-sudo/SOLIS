from __future__ import annotations
from PIL import Image, ImageOps

def to_epaper_1bit(img: Image.Image, out_size: tuple[int, int], invert: bool = False) -> Image.Image:
    img = img.convert("RGB")
    img = ImageOps.contain(img, out_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", out_size, (255, 255, 255))
    x = (out_size[0] - img.size[0]) // 2
    y = (out_size[1] - img.size[1]) // 2
    canvas.paste(img, (x, y))

    gray = canvas.convert("L")
    bw = gray.convert("1")
    if invert:
        bw = ImageOps.invert(bw.convert("L")).convert("1")
    return bw
