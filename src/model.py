from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PIL import Image


@dataclass
class DiffusionConfig:
    prompt: str
    model_id: str
    width: int
    height: int
    steps: int
    seed: int
    preview_every: int = 1
    guidance_scale: float = 7.5


class DiffusionModel:
    def __init__(self, cfg: DiffusionConfig):
        self.cfg = cfg

    def _prepare_size(self) -> tuple[int, int]:
        # Stable Diffusion dimensions should be divisible by 8.
        width = max(256, (self.cfg.width // 8) * 8)
        height = max(256, (self.cfg.height // 8) * 8)
        return width, height

    def _pick_device(self, torch_module) -> tuple[str, object]:
        if torch_module.cuda.is_available():
            return "cuda", torch_module.float16
        if hasattr(torch_module.backends, "mps") and torch_module.backends.mps.is_available():
            return "mps", torch_module.float16
        return "cpu", torch_module.float32

    def generate(
        self,
        on_status: Callable[[str], None] | None = None,
        on_step: Callable[[int, int], None] | None = None,
        on_preview: Callable[[Image.Image, int, int], None] | None = None,
    ) -> Image.Image:
        try:
            import torch
            from diffusers import StableDiffusionPipeline
        except Exception as exc:
            raise RuntimeError(
                "Dependency import failed. Run ./setup.sh. "
                f"Details: {exc}"
            ) from exc

        if on_status:
            on_status(f"Loading model: {self.cfg.model_id}")

        width, height = self._prepare_size()
        device, dtype = self._pick_device(torch)

        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                self.cfg.model_id,
                torch_dtype=dtype,
                use_safetensors=True,
            )
            pipe = pipe.to(device)
            pipe.set_progress_bar_config(disable=True)
        except Exception as exc:
            raise RuntimeError(
                f"Model load failed for '{self.cfg.model_id}'. "
                "Check first-run download access and disk space."
            ) from exc

        if on_status:
            on_status(f"Running diffusion on {device}")

        try:
            generator = torch.Generator(device=device).manual_seed(self.cfg.seed)
        except Exception:
            generator = torch.Generator().manual_seed(self.cfg.seed)

        total_steps = max(1, self.cfg.steps)
        preview_every = max(1, self.cfg.preview_every)

        def callback(step_index: int, _timestep: int, latents) -> None:
            current_step = step_index + 1
            if on_step:
                on_step(current_step, total_steps)

            if (
                on_preview
                and (current_step % preview_every == 0 or current_step == total_steps)
            ):
                try:
                    with torch.no_grad():
                        img_np = pipe.decode_latents(latents)
                    preview = pipe.numpy_to_pil(img_np)[0].convert("RGB")
                    on_preview(preview, current_step, total_steps)
                except Exception:
                    # Preview decode failures should not kill final generation.
                    pass

        try:
            result = pipe(
                prompt=self.cfg.prompt,
                width=width,
                height=height,
                num_inference_steps=total_steps,
                guidance_scale=self.cfg.guidance_scale,
                generator=generator,
                callback=callback,
                callback_steps=1,
            )
        except Exception as exc:
            raise RuntimeError(
                "Generation failed. Try --width 512 --height 512 --steps 15. "
                f"Details: {exc}"
            ) from exc

        return result.images[0].convert("RGB")
