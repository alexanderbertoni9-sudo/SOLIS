from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional
import threading, queue
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw

@dataclass
class GenFrame:
    step: int
    total_steps: int
    image: Image.Image  # RGB preview frame

class DiffusionGenerator:
    """
    Local, private diffusion-based generator that STREAMS preview frames live.
    """

    def __init__(
        self,
        prompt: str,
        model_id: str = "runwayml/stable-diffusion-v1-5",
        device: Optional[str] = None,
    ):
        self.prompt = prompt

        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"   # Apple Silicon
            elif torch.cuda.is_available():
                device = "cuda"  # NVIDIA
            else:
                device = "cpu"

        self.device = device

        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            safety_checker=None,
            torch_dtype=torch.float16 if device in ("cuda", "mps") else torch.float32,
        ).to(device)

    def _loading_image(self, w: int = 768, h: int = 512) -> Image.Image:
        img = Image.new("RGB", (w, h), (15, 15, 15))
        d = ImageDraw.Draw(img)
        d.text((20, 20), "SOLIS: loading model / generating...", fill=(230, 230, 230))
        d.text((20, 50), "This is local (private) diffusion.", fill=(180, 180, 180))
        return img

    def generate_stream(
        self,
        steps: int = 30,
        seed: Optional[int] = None,
        preview_every: int = 4,
    ) -> Iterable[GenFrame]:
        """
        Yields frames LIVE while diffusion runs.
        """
        q: "queue.Queue[object]" = queue.Queue(maxsize=8)
        DONE = object()

        # Yield an immediate "loading" frame so the preview window shows instantly.
        yield GenFrame(step=0, total_steps=steps, image=self._loading_image())

        generator = None
        if seed is not None:
            generator = torch.Generator(self.device).manual_seed(seed)

        def worker():
            try:
                def cb(step: int, timestep: int, latents):
                    # Decode only sometimes (decoding is expensive)
                    if step % preview_every != 0 and step != steps - 1:
                        return
                    with torch.no_grad():
                        img_np = self.pipe.decode_latents(latents)
                        img = self.pipe.numpy_to_pil(img_np)[0]
                    # Don’t block forever if UI is slow; drop frames if needed.
                    try:
                        q.put((step + 1, img), timeout=0.2)
                    except queue.Full:
                        pass

                self.pipe(
                    self.prompt,
                    num_inference_steps=steps,
                    generator=generator,
                    callback=cb,
                    callback_steps=1,
                )
            finally:
                q.put(DONE)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        while True:
            item = q.get()
            if item is DONE:
                break
            step, img = item
            yield GenFrame(step=step, total_steps=steps, image=img)
