from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import pygame
from PIL import Image

@dataclass
class PreviewConfig:
    window_size: Tuple[int, int] = (820, 520)
    title: str = "SOLIS — Generating..."

class LivePreview:
    def __init__(self, cfg: PreviewConfig = PreviewConfig()):
        pygame.init()
        self.cfg = cfg
        self.screen = pygame.display.set_mode(cfg.window_size)
        pygame.display.set_caption(cfg.title)

        # Keep these (even if unused) so your environment stays identical/stable
        # and we don’t risk breaking anything subtle.
        self.font = pygame.font.SysFont("monospace", 18)

        self.clock = pygame.time.Clock()

    def _pil_to_surface(self, img: Image.Image) -> pygame.Surface:
        img = img.convert("RGB").resize(self.cfg.window_size, Image.Resampling.LANCZOS)
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def pump(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def show(self, img: Image.Image, step: int, total: int):
        # Extra safety: pump events here too, so the window stays responsive
        # even if something upstream skips pump() occasionally.
        pygame.event.pump()

        surf = self._pil_to_surface(img)
        self.screen.blit(surf, (0, 0))

        # IMPORTANT:
        # Do NOT draw any progress UI here.
        # Progress is already baked into the incoming image by epaper_ui.overlay_progress().

        pygame.display.flip()
        self.clock.tick(30)

    def close(self):
        pygame.quit()
