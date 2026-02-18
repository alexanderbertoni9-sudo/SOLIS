from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import pygame
from PIL import Image

@dataclass
class PreviewConfig:
    window_size: Tuple[int, int] = (820, 520)
    title: str = "SOLIS — Generating..."
    max_fps: int = 0

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
        if self.cfg.max_fps > 0:
            self.clock.tick(self.cfg.max_fps)

    def show_final_fullscreen(self, img: Image.Image):
        """
        Present final generated image in fullscreen until the user exits.
        """
        display_info = pygame.display.Info()
        fullscreen_size = (display_info.current_w, display_info.current_h)

        self.screen = pygame.display.set_mode(fullscreen_size, pygame.FULLSCREEN)
        pygame.display.set_caption("SOLIS — Final Image")

        final_img = img.convert("RGB").resize(fullscreen_size, Image.Resampling.LANCZOS)
        surf = pygame.image.fromstring(final_img.tobytes(), final_img.size, final_img.mode)
        self.screen.blit(surf, (0, 0))
        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return

            if self.cfg.max_fps > 0:
                self.clock.tick(self.cfg.max_fps)

    def close(self):
        pygame.quit()
