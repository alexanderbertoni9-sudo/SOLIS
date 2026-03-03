from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
from PIL import Image, ImageOps


@dataclass
class ViewerConfig:
    title: str = "SOLIS"
    background: Tuple[int, int, int] = (0, 0, 0)


class FullscreenViewer:
    def __init__(self, cfg: ViewerConfig = ViewerConfig()):
        pygame.init()
        self.cfg = cfg
        info = pygame.display.Info()
        self.screen_size = (info.current_w, info.current_h)
        self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN)
        pygame.display.set_caption(cfg.title)
        self.font = pygame.font.SysFont("monospace", 22)
        self.clock = pygame.time.Clock()

    def close(self) -> None:
        pygame.quit()

    def pump(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
        return True

    def _image_surface(self, image: Image.Image) -> pygame.Surface:
        fitted = ImageOps.contain(
            image.convert("RGB"),
            self.screen_size,
            Image.Resampling.LANCZOS,
        )
        return pygame.image.fromstring(fitted.tobytes(), fitted.size, fitted.mode)

    def _draw_overlay_lines(self, lines: list[str]) -> None:
        if not lines:
            return

        rendered = [self.font.render(line, True, (255, 255, 255)) for line in lines]
        width = max(r.get_width() for r in rendered) + 32
        height = sum(r.get_height() for r in rendered) + 24
        box = pygame.Surface((width, height))
        box.set_alpha(150)
        box.fill((0, 0, 0))
        x = 20
        y = self.screen_size[1] - height - 20
        self.screen.blit(box, (x, y))

        text_y = y + 12
        for r in rendered:
            self.screen.blit(r, (x + 16, text_y))
            text_y += r.get_height()

    def show_loading(self, message: str) -> None:
        self.screen.fill(self.cfg.background)
        text = self.font.render(message, True, (255, 255, 255))
        prompt = self.font.render("Esc/q to exit", True, (210, 210, 210))
        self.screen.blit(
            text,
            ((self.screen_size[0] - text.get_width()) // 2, self.screen_size[1] // 2 - 20),
        )
        self.screen.blit(
            prompt,
            ((self.screen_size[0] - prompt.get_width()) // 2, self.screen_size[1] // 2 + 16),
        )
        pygame.display.flip()

    def show_frame(self, image: Image.Image, step: int, total: int, prompt: str) -> None:
        surface = self._image_surface(image)
        x = (self.screen_size[0] - surface.get_width()) // 2
        y = (self.screen_size[1] - surface.get_height()) // 2
        self.screen.fill(self.cfg.background)
        self.screen.blit(surface, (x, y))
        prompt_short = prompt[:70] + ("..." if len(prompt) > 70 else "")
        self._draw_overlay_lines(
            [
                f"Generating {step}/{total}",
                f'Prompt: "{prompt_short}"',
                "Esc/q to exit",
            ]
        )
        pygame.display.flip()

    def show_final(self, image: Image.Image, prompt: str) -> None:
        surface = self._image_surface(image)
        x = (self.screen_size[0] - surface.get_width()) // 2
        y = (self.screen_size[1] - surface.get_height()) // 2
        self.screen.fill(self.cfg.background)
        self.screen.blit(surface, (x, y))
        prompt_short = prompt[:70] + ("..." if len(prompt) > 70 else "")
        self._draw_overlay_lines(
            [
                "Final image ready",
                f'Prompt: "{prompt_short}"',
                "Esc/q to exit",
            ]
        )
        pygame.display.flip()

    def wait_until_exit(self) -> None:
        while self.pump():
            self.clock.tick(60)
