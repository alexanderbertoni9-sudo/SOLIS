from __future__ import annotations
import os
from dataclasses import dataclass
from PIL import Image


@dataclass
class EpaperConfig:
    size: tuple[int, int] = (800, 480)
    invert: bool = False
    simulate_path: str = "exports/epaper_latest.png"


class EpaperDisplay:
    """
    E-paper output sink.

    Step C behavior:
      - If SOLIS_EPAPER_SIM=1 (default), writes latest frame to exports/epaper_latest.png.
      - If SOLIS_EPAPER_HW=1, attempts to call a hardware driver hook (stub for Step D).

    This lets the e-paper “refresh” during generation in the exact same places we show snapshots.
    """

    def __init__(self, cfg: EpaperConfig):
        self.cfg = cfg
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sim_path = os.path.join(self.repo_root, cfg.simulate_path)
        os.makedirs(os.path.dirname(self.sim_path), exist_ok=True)

        self.simulate = os.environ.get("SOLIS_EPAPER_SIM", "1").strip() == "1"
        self.use_hw = os.environ.get("SOLIS_EPAPER_HW", "0").strip() == "1"

        if self.use_hw:
            print("[SOLIS] E-paper hardware mode requested (Step D driver needed).")
        else:
            print(f"[SOLIS] E-paper simulation ON -> writing: {self.sim_path}")

    def show(self, img_1bit: Image.Image):
        """
        img_1bit should already be panel-sized and dithered (mode '1' ideally).
        """
        if self.use_hw:
            # Step D: replace this with actual panel driver calls.
            # For now, fall back to simulation so nothing breaks.
            print("[SOLIS] HW driver not wired yet; falling back to simulation.")
            self._write_sim(img_1bit)
            return

        self._write_sim(img_1bit)

    def _write_sim(self, img: Image.Image):
        # Atomic write so viewers never see a partial file.
        # IMPORTANT: PIL needs a known extension OR explicit format.
        tmp = self.sim_path + ".tmp.png"
        img.save(tmp, format="PNG")
        os.replace(tmp, self.sim_path)
