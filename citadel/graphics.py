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


def _shift(color, amt):
    return pygame.Color(
        max(0, min(255, color.r + amt)),
        max(0, min(255, color.g + amt)),
        max(0, min(255, color.b + amt)),
    )


def _bevel(tex, base):
    """Light from top-left, shade at bottom-right: instant depth."""
    t = config.TILE
    pygame.draw.line(tex, _shift(base, 34), (0, 0), (t - 1, 0), 2)
    pygame.draw.line(tex, _shift(base, 34), (0, 0), (0, t - 1), 2)
    pygame.draw.line(tex, _shift(base, -38), (0, t - 2), (t - 1, t - 2), 2)
    pygame.draw.line(tex, _shift(base, -38), (t - 2, 0), (t - 2, t - 1), 2)


def _speckle(tex, rng, base, n, lo=-20, hi=20, size=(2, 5)):
    t = config.TILE
    for _ in range(n):
        x = int(rng.integers(0, t - size[0]))
        y = int(rng.integers(0, t - size[1]))
        w = int(rng.integers(size[0], size[0] + 4))
        h = int(rng.integers(size[1], size[1] + 4))
        pygame.draw.rect(tex, _shift(base, int(rng.integers(lo, hi + 1))),
                         (x, y, w, h))


class Textures:
    def __init__(self):
        self.blocks = {}
        for bid, (name, color) in BLOCKS.items():
            if bid == 0 or color is None:
                continue
            self.blocks[bid] = self._make(bid, name, pygame.Color(*color))

    def _make(self, bid, name, base):
        import numpy as np
        t = config.TILE
        tex = pygame.Surface((t, t))
        rng = np.random.default_rng(1000 + bid)
        tex.fill(base)

        if bid == 1:  # grass: dirt below + blade fringe on top
            dirt = pygame.Color(122, 87, 51)
            tex.fill(dirt)
            _speckle(tex, rng, dirt, 10, -18, 14)
            pygame.draw.rect(tex, base, (0, 0, t, 7))
            for x in range(0, t, 3):
                blade_h = int(rng.integers(4, 9))
                pygame.draw.line(tex, _shift(base, int(rng.integers(-15, 20))),
                                 (x, 7), (x + int(rng.integers(-2, 3)),
                                          7 - blade_h), 2)
        elif bid == 2:  # dirt
            _speckle(tex, rng, base, 14, -22, 16)
            for _ in range(4):
                x, y = int(rng.integers(2, t - 6)), int(rng.integers(2, t - 6))
                pygame.draw.circle(tex, _shift(base, -25), (x, y),
                                   int(rng.integers(1, 3)))
        elif bid == 3:  # stone: cracks
            _speckle(tex, rng, base, 8, -18, 12)
            for _ in range(3):
                x = int(rng.integers(2, t - 2))
                y = int(rng.integers(2, t - 2))
                pts = [(x, y)]
                for _ in range(3):
                    x += int(rng.integers(-5, 6))
                    y += int(rng.integers(2, 6))
                    pts.append((max(1, min(t - 2, x)),
                                max(1, min(t - 2, y))))
                pygame.draw.lines(tex, _shift(base, -32), False, pts, 1)
        elif bid == 4:  # ancient oak: vertical grain + knot
            for x in range(0, t, 4):
                pygame.draw.line(tex, _shift(base, int(rng.integers(-14, 12))),
                                 (x, 0), (x + int(rng.integers(-1, 2)), t - 1), 2)
            kx, ky = int(rng.integers(6, t - 6)), int(rng.integers(6, t - 6))
            pygame.draw.circle(tex, _shift(base, -30), (kx, ky), 4)
            pygame.draw.circle(tex, _shift(base, -55), (kx, ky), 2)
        elif bid in (5, 10, 11):  # quartz family: smooth polished sheen
            _speckle(tex, rng, base, 4, -8, 10, size=(3, 6))
            pygame.draw.line(tex, _shift(base, 25), (3, t - 5),
                             (t - 5, 3), 2)
            pygame.draw.line(tex, _shift(base, 18), (6, t - 8),
                             (t - 8, 6), 1)
        elif bid == 6:  # crystal: facets
            cx, cy = t // 2, t // 2
            for (dx, dy) in ((-8, -6), (7, -7), (-6, 8), (8, 7)):
                pygame.draw.polygon(tex, _shift(base, -35),
                                    [(cx, cy), (cx + dx, cy + dy),
                                     (cx + dx, cy)])
            pygame.draw.polygon(tex, _shift(base, 30),
                                [(cx, cy), (cx - 6, cy - 7), (cx + 1, cy - 10)])
            pygame.draw.line(tex, (255, 255, 255), (cx - 4, cy - 4),
                             (cx + 4, cy + 3), 1)
        elif bid == 7:  # starlight: glowing core + sparkle cross
            cx, cy = t // 2, t // 2
            for r, a in ((9, 30), (6, 60), (3, 90)):
                glow = pygame.Surface((t, t), pygame.SRCALPHA)
                pygame.draw.circle(glow, (base.r, base.g, base.b, a),
                                   (cx, cy), r)
                tex.blit(glow, (0, 0))
            pygame.draw.line(tex, (255, 255, 230), (cx - 8, cy),
                             (cx + 8, cy), 1)
            pygame.draw.line(tex, (255, 255, 230), (cx, cy - 8),
                             (cx, cy + 8), 1)
        elif bid == 8:  # dark thorns: jagged spikes
            dark = pygame.Color(45, 30, 45)
            tex.fill(dark)
            for _ in range(6):
                x = int(rng.integers(1, t - 1))
                h = int(rng.integers(8, 18))
                pygame.draw.polygon(tex, base,
                                    [(x, t), (x + 2, t - h),
                                     (x + 4, t)])
            _speckle(tex, rng, dark, 6, -10, 10)
        elif bid == 9:  # berry bush: leafy clumps + berries
            for _ in range(8):
                x, y = int(rng.integers(2, t - 5)), int(rng.integers(2, t - 5))
                pygame.draw.circle(tex, _shift(base, int(rng.integers(-20, 25))),
                                   (x, y), int(rng.integers(3, 6)))
            for _ in range(4):
                x, y = int(rng.integers(4, t - 4)), int(rng.integers(4, t - 4))
                pygame.draw.circle(tex, (255, 90, 120), (x, y), 2)
                pygame.draw.circle(tex, (255, 170, 190), (x - 1, y - 1), 1)
        elif bid == 12:  # rune key shard
            cx, cy = t // 2, t // 2
            pygame.draw.polygon(tex, base,
                                [(cx, 2), (t - 4, cy), (cx, t - 2), (4, cy)])
            pygame.draw.polygon(tex, _shift(base, 40),
                                [(cx, 6), (t - 8, cy), (cx, t - 6)])
            pygame.draw.line(tex, (255, 255, 255), (cx, 6), (cx, t - 6), 1)
        elif bid == 13:  # catalyst bloom: petals
            cx, cy = t // 2, t // 2
            for i in range(6):
                a = i * np.pi / 3
                pygame.draw.ellipse(
                    tex, _shift(base, -18),
                    (int(cx + 6 * np.cos(a)) - 5,
                     int(cy + 6 * np.sin(a)) - 5, 10, 10))
            pygame.draw.circle(tex, (255, 230, 180), (cx, cy), 4)
        else:
            _speckle(tex, rng, base, 10, -20, 20)

        _bevel(tex, base)
        pygame.draw.rect(tex, _shift(base, -55), tex.get_rect(), 1)
        return pygame.Surface.convert(tex)


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
