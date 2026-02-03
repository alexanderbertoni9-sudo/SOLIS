from __future__ import annotations
import os
import time
from dataclasses import dataclass
from PIL import Image


@dataclass
class EpaperConfig:
    size: tuple[int, int] = (800, 480)
    invert: bool = False
    simulate_path: str = "exports/epaper_latest.png"
    # New: minimum seconds between e-paper refreshes (prevents over-refreshing)
    min_refresh_seconds: float = 0.0  # set e.g. 8.0 on real e-paper


class EpaperDisplay:
    """
    E-paper output sink with refresh pacing.

    Step C behavior:
      - Default is simulation -> writes exports/epaper_latest.png
      - Optional pacing to match real e-paper refresh time (min_refresh_seconds)
    """

    def __init__(self, cfg: EpaperConfig):
        self.cfg = cfg
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sim_path = os.path.join(self.repo_root, cfg.simulate_path)
        os.makedirs(os.path.dirname(self.sim_path), exist_ok=True)

        self.use_hw = os.environ.get("SOLIS_EPAPER_HW", "0").strip() == "1"
        self._last_refresh = 0.0

        if self.use_hw:
            print("[SOLIS] E-paper hardware mode requested (Step D driver needed).")
        else:
            print(f"[SOLIS] E-paper simulation ON -> writing: {self.sim_path}")

        if cfg.min_refresh_seconds > 0:
            print(f"[SOLIS] E-paper refresh pacing: >= {cfg.min_refresh_seconds:.1f}s between refreshes")

    def show(self, img_1bit: Image.Image, *, force: bool = False):
        """
        img_1bit should already be panel-sized and dithered (mode '1' ideally).
        If force=True, bypass pacing (use for final frame).
        """
        if (not force) and self.cfg.min_refresh_seconds > 0:
            now = time.time()
            if (now - self._last_refresh) < self.cfg.min_refresh_seconds:
                return

        if self.use_hw:
            # Step D: replace with real driver calls.
            # For now, fall back to simulation so nothing breaks.
            print("[SOLIS] HW driver not wired yet; falling back to simulation.")
            self._write_sim(img_1bit)
        else:
            self._write_sim(img_1bit)

        self._last_refresh = time.time()

    def _write_sim(self, img: Image.Image):
        # Atomic write so viewers never see a partial file.
        tmp = self.sim_path + ".tmp.png"
        img.save(tmp, format="PNG")
        os.replace(tmp, self.sim_path)
