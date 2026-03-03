from __future__ import annotations

import argparse
import os

from model_store import prepare_local_model


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_ID = "segmind/tiny-sd"
DEFAULT_MODEL_DIR = os.path.join(ROOT, "models", "segmind-tiny-sd")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download/repair and verify a local Hugging Face model snapshot."
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="Hugging Face model id.")
    parser.add_argument(
        "--model-dir",
        default=DEFAULT_MODEL_DIR,
        help="Local directory where model files should be stored.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = os.path.abspath(args.model_dir)
    print(f"Preparing local model: {args.model_id}")
    print(f"Target directory: {model_dir}")

    try:
        resolved = prepare_local_model(args.model_id, model_dir, on_status=print)
    except Exception as exc:
        print(f"Model preparation failed: {exc}")
        raise SystemExit(1)

    print(f"Model is ready: {resolved}")


if __name__ == "__main__":
    main()
