"""Procedural graphics: block textures, sprites, particles, sky.

Textures are generated once at startup with NumPy noise so the game
ships with zero image assets (fits the single-shot architecture and
keeps the repo tiny for the Pi).
"""
import numpy as np
import pygame

from . import config
from .world import BLOCKS


def _noise_surface(size, base, variance, seed):
    rng = np.random.default_rng(seed)
    noise = rng.integers(-variance, variance + 1, (size, size, 1))
    arr = np.clip(np.array(base) + noise, 0, 255).astype(np.uint8)
    surf = pygame.surfarray.make_surface(np.repeat(arr, 3, axis=2))
    return pygame.transform.scale(surf, (size, size))


class Textures:
    def __init__(self):
        self.blocks = {}
        for i, (bid, (name, color)) in enumerate(BLOCKS.items()):
            if bid == 0 or color is None:
                continue
            tex = pygame.Surface((config.TILE, config.TILE))
            base = pygame.Color(*color)
            tex.fill(base)
            rng = np.random.default_rng(1000 + bid)
            for _ in range(14):
                x = int(rng.integers(0, config.TILE))
                y = int(rng.integers(0, config.TILE))
                w = int(rng.integers(3, 10))
                h = int(rng.integers(3, 10))
                shade = int(rng.integers(-28, 29))
                c = pygame.Color(
                    max(0, min(255, base.r + shade)),
                    max(0, min(255, base.g + shade)),
                    max(0, min(255, base.b + shade)),
                )
                pygame.draw.rect(tex, c, (x, y, w, h))
            pygame.draw.rect(tex, (0, 0, 0), tex.get_rect(), 1)
            self.blocks[bid] = tex


def make_creature_sprite(color, size=26):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r = size // 2 - 2
    pygame.draw.circle(surf, (*color, 255), (size // 2, size // 2), r)
    pygame.draw.circle(
        surf, (255, 255, 255, 255),
        (size // 2 - r // 3, size // 2 - r // 4), 3,
    )
    pygame.draw.circle(
        surf, (40, 40, 60, 255),
        (size // 2 - r // 3, size // 2 - r // 4), 1,
    )
    pygame.draw.circle(
        surf, (255, 255, 255, 255),
        (size // 2 + r // 3, size // 2 - r // 4), 3,
    )
    pygame.draw.circle(
        surf, (40, 40, 60, 255),
        (size // 2 + r // 3, size // 2 - r // 4), 1,
    )
    pygame.draw.arc(
        surf, (40, 40, 60, 255),
        (size // 4, size // 2 - 2, size // 2, size // 3), 3.5, 5.9, 2,
    )
    return pygame.transform.smoothscale(surf, (size, size))


def make_wizard():
    size = config.TILE
    surf = pygame.Surface((size, size + 8), pygame.SRCALPHA)
    pygame.draw.rect(surf, (60, 70, 160, 255), (10, 14, 12, 20))       # robe body
    pygame.draw.circle(surf, (255, 226, 190, 255), (16, 10), 7)       # head
    pygame.draw.polygon(surf, (40, 40, 90, 255), [(6, 12), (26, 12), (16, 0)])  # hat
    pygame.draw.polygon(surf, (150, 220, 255, 255), [(24, 16), (30, 22), (24, 24)])  # wand
    pygame.draw.circle(surf, (255, 250, 180, 255), (30, 22), 3)
    return surf


class Particles:
    def __init__(self):
        self.list = []

    def emit(self, x, y, color, n=8, speed=60, life=0.6, gravity=140):
        for _ in range(n):
            ang = np.random.uniform(0, 2 * np.pi)
            sp = np.random.uniform(0.2, 1.0) * speed
            self.list.append({
                "x": x, "y": y,
                "vx": np.cos(ang) * sp, "vy": np.sin(ang) * sp - 20,
                "life": life * np.random.uniform(0.6, 1.3),
                "t": 0.0, "color": color, "g": gravity,
            })

    def update(self, dt):
        alive = []
        for p in self.list:
            p["t"] += dt
            if p["t"] < p["life"]:
                p["vy"] += p["g"] * dt
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                alive.append(p)
        self.list = alive

    def draw(self, screen, cam):
        for p in self.list:
            alpha = max(0, 1 - p["t"] / p["life"])
            x, y = cam.apply(p["x"], p["y"])
            s = int(2 + 3 * alpha)
            pygame.draw.circle(screen, p["color"], (int(x), int(y)), max(1, s))
