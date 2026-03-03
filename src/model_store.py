from __future__ import annotations

from pathlib import Path
from typing import Callable
import shutil


def _has_any(root: Path, files: tuple[str, ...]) -> bool:
    return any((root / rel).exists() for rel in files)


def _has_all(root: Path, files: tuple[str, ...]) -> bool:
    return all((root / rel).exists() for rel in files)


def verify_local_model(model_dir: str | Path) -> tuple[bool, list[str]]:
    root = Path(model_dir)
    if not root.exists():
        return False, [f"directory not found: {root}"]
    if not root.is_dir():
        return False, [f"not a directory: {root}"]

    missing: list[str] = []

    required_single = (
        "model_index.json",
        "scheduler/scheduler_config.json",
        "tokenizer/tokenizer_config.json",
        "text_encoder/config.json",
        "unet/config.json",
        "vae/config.json",
    )
    for rel in required_single:
        if not (root / rel).exists():
            missing.append(rel)

    if not _has_any(root, ("text_encoder/model.safetensors", "text_encoder/pytorch_model.bin")):
        missing.append("one of: text_encoder/model.safetensors | text_encoder/pytorch_model.bin")
    if not _has_any(root, ("unet/diffusion_pytorch_model.safetensors", "unet/diffusion_pytorch_model.bin")):
        missing.append(
            "one of: unet/diffusion_pytorch_model.safetensors | unet/diffusion_pytorch_model.bin"
        )
    if not _has_any(root, ("vae/diffusion_pytorch_model.safetensors", "vae/diffusion_pytorch_model.bin")):
        missing.append(
            "one of: vae/diffusion_pytorch_model.safetensors | vae/diffusion_pytorch_model.bin"
        )

    has_spiece = _has_all(root, ("tokenizer/spiece.model",))
    has_bpe = _has_all(root, ("tokenizer/vocab.json", "tokenizer/merges.txt"))
    if not (has_spiece or has_bpe):
        missing.append("tokenizer/spiece.model OR both tokenizer/vocab.json + tokenizer/merges.txt")

    return len(missing) == 0, missing


def prepare_local_model(
    model_id: str,
    model_dir: str | Path,
    on_status: Callable[[str], None] | None = None,
) -> Path:
    root = Path(model_dir)
    ok, missing = verify_local_model(root)
    if ok:
        if on_status:
            on_status(f"Model snapshot already complete: {root}")
        return root

    if on_status:
        on_status(
            f"Model snapshot missing files; downloading/repairing {model_id} into {root}"
        )
        if missing:
            on_status("Missing before download: " + "; ".join(missing))

    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise RuntimeError(
            "huggingface_hub is not available. Run ./setup.sh to install dependencies. "
            f"Details: {type(exc).__name__}: {exc}"
        ) from exc

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=str(root),
            ignore_patterns=["*.onnx", "*.tflite", "*.ckpt", "*.msgpack"],
        )
    except Exception as exc:
        raise RuntimeError(
            f"Model download failed for '{model_id}'. "
            "Check internet access and free disk space, then run ./setup.sh again. "
            f"Details: {type(exc).__name__}: {exc}"
        ) from exc

    ok, missing = verify_local_model(root)
    if not ok:
        raise RuntimeError(
            "Downloaded model snapshot is still incomplete. "
            f"Missing: {'; '.join(missing)}"
        )

    if on_status:
        on_status(f"Model snapshot verified: {root}")
    return root
