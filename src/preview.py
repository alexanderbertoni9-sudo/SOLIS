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
        surf = self._pil_to_surface(img)
        self.screen.blit(surf, (0, 0))

        label = self.font.render(f"Generating: {step}/{total}", True, (255, 255, 255))
        self.screen.blit(label, (12, 12))

        bar_w = self.cfg.window_size[0] - 24
        pygame.draw.rect(self.screen, (30, 30, 30), (12, 40, bar_w, 10))
        fill = int(bar_w * (step / max(total, 1)))
        pygame.draw.rect(self.screen, (220, 220, 220), (12, 40, fill, 10))

        pygame.display.flip()
        self.clock.tick(30)

    def close(self):
        pygame.quit()
