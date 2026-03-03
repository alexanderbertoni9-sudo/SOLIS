from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import os

from PIL import Image
from model_store import prepare_local_model, verify_local_model


@dataclass
class DiffusionConfig:
    prompt: str
    model_id: str
    model_dir: str | None
    width: int
    height: int
    steps: int
    seed: int
    preview_every: int = 1
    guidance_scale: float = 7.5
    auto_repair_model: bool = True


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
            # MPS float32 is slower but significantly more stable than float16.
            return "mps", torch_module.float32
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
            if self.cfg.model_dir:
                on_status(f"Loading local model: {self.cfg.model_dir}")
            else:
                on_status(f"Loading model: {self.cfg.model_id}")

        width, height = self._prepare_size()
        device, dtype = self._pick_device(torch)

        model_source = self.cfg.model_id
        local_files_only = False
        if self.cfg.model_dir:
            model_source = os.path.abspath(self.cfg.model_dir)
            local_files_only = True
            ok, missing = verify_local_model(model_source)
            if not ok:
                if self.cfg.auto_repair_model:
                    if on_status:
                        on_status("Local model snapshot incomplete. Attempting automatic repair...")
                    prepare_local_model(self.cfg.model_id, model_source, on_status=on_status)
                else:
                    missing_text = "; ".join(missing)
                    raise RuntimeError(
                        "Local model snapshot is incomplete. "
                        "Run ./setup.sh to repair it. "
                        f"Missing: {missing_text}"
                    )

        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                model_source,
                torch_dtype=dtype,
                local_files_only=local_files_only,
                safety_checker=None,
                requires_safety_checker=False,
            )
            pipe = pipe.to(device)
            pipe.enable_attention_slicing()
            pipe.set_progress_bar_config(disable=True)
        except Exception as exc:
            details = f"{type(exc).__name__}: {exc}"
            if local_files_only:
                raise RuntimeError(
                    f"Local model load failed from '{model_source}'. "
                    "Run ./setup.sh to repair/re-download model files. "
                    f"Details: {details}"
                ) from exc
            raise RuntimeError(
                f"Model load failed for '{self.cfg.model_id}'. "
                "Check first-run download access and disk space. "
                f"Details: {details}"
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

        def run_inference():
            return pipe(
                prompt=self.cfg.prompt,
                width=width,
                height=height,
                num_inference_steps=total_steps,
                guidance_scale=self.cfg.guidance_scale,
                generator=generator,
                callback=callback,
                callback_steps=1,
            )

        try:
            result = run_inference()
        except Exception as exc:
            # On macOS/MPS, fallback to CPU for reliability when kernel failures occur.
            if device == "mps":
                if on_status:
                    on_status("MPS generation failed; retrying on CPU for stability...")
                details = f"{type(exc).__name__}: {exc}"
                try:
                    pipe = pipe.to("cpu")
                    device = "cpu"
                    try:
                        generator = torch.Generator(device=device).manual_seed(self.cfg.seed)
                    except Exception:
                        generator = torch.Generator().manual_seed(self.cfg.seed)
                    result = run_inference()
                except Exception as exc2:
                    details2 = f"{type(exc2).__name__}: {exc2}"
                    raise RuntimeError(
                        "Generation failed on MPS and CPU fallback. "
                        "Try --width 512 --height 512 --steps 12. "
                        f"MPS details: {details} | CPU details: {details2}"
                    ) from exc2
            else:
                raise RuntimeError(
                    "Generation failed. Try --width 512 --height 512 --steps 15. "
                    f"Details: {type(exc).__name__}: {exc}"
                ) from exc

        return result.images[0].convert("RGB")
