from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import pygame
from PIL import Image, ImageOps

@dataclass
class PreviewConfig:
    window_size: Tuple[int, int] = (0, 0)
    fullscreen: bool = True
    title: str = "SOLIS — Generating..."
    background: Tuple[int, int, int] = (0, 0, 0)

class LivePreview:
    def __init__(self, cfg: PreviewConfig = PreviewConfig()):
        pygame.init()
        self.cfg = cfg
        flags = 0
        if cfg.fullscreen:
            info = pygame.display.Info()
            self.screen_size = (info.current_w, info.current_h)
            flags |= pygame.FULLSCREEN
        else:
            if cfg.window_size[0] <= 0 or cfg.window_size[1] <= 0:
                self.screen_size = (1280, 720)
            else:
                self.screen_size = cfg.window_size
        self.screen = pygame.display.set_mode(self.screen_size, flags)
        pygame.display.set_caption(cfg.title)
        self.font = pygame.font.SysFont("monospace", 18)
        self.clock = pygame.time.Clock()

    def _pil_to_surface(self, img: Image.Image) -> pygame.Surface:
        fitted = ImageOps.contain(img.convert("RGB"), self.screen_size, Image.Resampling.LANCZOS)
        return pygame.image.fromstring(fitted.tobytes(), fitted.size, fitted.mode)

    def pump(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
        return True

    def show(self, img: Image.Image, step: int, total: int, show_status: bool = True):
        pygame.event.pump()
        surf = self._pil_to_surface(img)
        x = (self.screen_size[0] - surf.get_width()) // 2
        y = (self.screen_size[1] - surf.get_height()) // 2
        self.screen.fill(self.cfg.background)
        self.screen.blit(surf, (x, y))
        if show_status and total > 0:
            status = f"Generating {step}/{total}   Esc/q to quit"
            text = self.font.render(status, True, (255, 255, 255))
            pad = 16
            bg = pygame.Surface((text.get_width() + pad * 2, text.get_height() + pad))
            bg.set_alpha(140)
            bg.fill((0, 0, 0))
            self.screen.blit(bg, (24, self.screen_size[1] - bg.get_height() - 24))
            self.screen.blit(text, (24 + pad, self.screen_size[1] - text.get_height() - 24 - pad // 2))
        pygame.display.flip()

    def show_final_fullscreen(self, img: Image.Image):
        self.show(img, step=0, total=0, show_status=False)

    def wait_until_exit(self):
        while self.pump():
            self.clock.tick(60)

    def close(self):
        pygame.quit()
