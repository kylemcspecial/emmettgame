"""Unique procedural creature sprites - no two creatures look alike.

Each species gets a distinct silhouette (moth, puffball, deer, wisp,
bird, salamander); each individual then gets a unique size, pattern,
and accessory derived from its id, so every creature in the world is
recognizably different.
"""
import numpy as np
import pygame


def _shade(color, amt):
    return tuple(max(0, min(255, c + amt)) for c in color)


def _draw_pattern(surf, rng, color, rect):
    kind = int(rng.integers(0, 4))
    accent = _shade(color, 60)
    if kind == 0:
        for _ in range(int(rng.integers(2, 5))):
            x = int(rng.uniform(rect.x + 4, rect.right - 8))
            y = int(rng.uniform(rect.y + 4, rect.bottom - 8))
            pygame.draw.circle(surf, accent, (x, y), int(rng.integers(2, 4)))
    elif kind == 1:
        for _ in range(int(rng.integers(2, 4))):
            x = int(rng.uniform(rect.x + 4, rect.right - 10))
            y = int(rng.uniform(rect.y + 4, rect.bottom - 10))
            pygame.draw.line(surf, accent, (x, y), (x + 8, y), 2)
    elif kind == 2:
        pygame.draw.ellipse(surf, accent,
                           (rect.centerx - 6, rect.centery - 4, 12, 8))
    else:
        pygame.draw.line(surf, accent, (rect.x + 3, rect.centery),
                         (rect.right - 3, rect.centery), 2)


def _eyes(surf, cx, cy, r, eye_c=(255, 255, 255), pup=(40, 40, 60)):
    off = max(3, r // 3)
    er = max(2, r // 4)
    for sx in (-off, off):
        pygame.draw.circle(surf, eye_c, (cx + sx, cy - r // 3), er)
        pygame.draw.circle(surf, pup, (cx + sx, cy - r // 3), max(1, er - 1))
    pygame.draw.arc(surf, pup, (cx - r // 2, cy - 2, r, r // 2), 3.6, 5.8, 2)


def _accessory(surf, rng, cx, cy, r, color):
    kind = int(rng.integers(0, 4))
    if kind == 0:
        pygame.draw.circle(surf, (255, 214, 92), (cx, cy - r - 4), 3)
    elif kind == 1:
        pygame.draw.polygon(surf, _shade(color, 90), [
            (cx - 5, cy - r + 1), (cx + 5, cy - r + 1), (cx, cy - r - 7),
        ])
    elif kind == 2:
        pygame.draw.line(surf, (120, 90, 60), (cx + r - 2, cy - 4),
                         (cx + r + 6, cy - 10), 2)
    # kind == 3: no accessory


class CreatureSprite:
    """Builds and caches a small animation set for one creature."""

    def __init__(self, species, color, seed, size=30):
        self.rng = np.random.default_rng(seed)
        self.species = species
        self.color = color
        self.size = int(size * float(self.rng.uniform(0.85, 1.25)))
        self.frames = self._build()

    def _build(self):
        frames = []
        for phase in (0, 1):
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            cx, cy = self.size // 2, self.size // 2 + phase
            r = self.size // 2 - 4
            s = self.species
            if s == "Glimmermoth":
                wing = r + 2 + phase * 2
                for wx in (-1, 1):
                    pygame.draw.ellipse(
                        surf, (*_shade(self.color, 40), 220),
                        (cx + wx * r // 2 - wing, cy - r, wing * 2, r),
                    )
                pygame.draw.ellipse(surf, self.color,
                                   (cx - r // 3, cy - r // 2, r * 2 // 3, r))
                _eyes(surf, cx, cy - r // 4, r // 2)
            elif s == "Pebblepuff":
                pygame.draw.circle(surf, self.color, (cx, cy + phase), r)
                pygame.draw.circle(surf, _shade(self.color, -35),
                                   (cx, cy + phase), r, 2)
                for _ in range(4):
                    a = float(self.rng.uniform(0, 6.28))
                    pygame.draw.circle(
                        surf, _shade(self.color, -25),
                        (int(cx + np.cos(a) * r * 0.6),
                         int(cy + np.sin(a) * r * 0.6)), 3,
                    )
                _eyes(surf, cx, cy - r // 4, r)
                _draw_pattern(surf, self.rng, self.color,
                              pygame.Rect(cx - r, cy - r, 2 * r, 2 * r))
            elif s == "Lumifawn":
                body = pygame.Rect(cx - r // 2, cy - r // 3, r, r + phase)
                pygame.draw.ellipse(surf, self.color, body)
                pygame.draw.rect(surf, _shade(self.color, -30),
                                 (cx - r // 3, cy + r - 2, 4, 4 + phase))
                pygame.draw.rect(surf, _shade(self.color, -30),
                                 (cx + r // 6, cy + r - 2, 4, 4 + phase))
                pygame.draw.circle(surf, _shade(self.color, 20),
                                   (cx, cy - r // 2 - phase), r // 2)
                _eyes(surf, cx, cy - r // 2, r // 2)
                pygame.draw.polygon(surf, _shade(self.color, 80), [
                    (cx - 3, cy - r), (cx + 3, cy - r), (cx, cy - r - 6),
                ])
            elif s == "Sparklewisp":
                pts = []
                for i in range(8):
                    a = i * np.pi / 4 + phase * 0.4
                    rad = r * (0.7 + 0.3 * np.sin(i * 2.7))
                    pts.append((cx + np.cos(a) * rad, cy + np.sin(a) * rad))
                pygame.draw.polygon(surf, (*self.color, 235), pts)
                pygame.draw.circle(surf, (255, 255, 220),
                                   (cx, cy - 1), max(2, r // 3))
                _eyes(surf, cx, cy, r // 2)
            elif s == "Mossgale":
                pygame.draw.ellipse(surf, self.color,
                                   (cx - r, cy - r // 2 - phase, 2 * r, r))
                pygame.draw.circle(surf, _shade(self.color, 25),
                                   (cx + r - 3, cy - phase), r // 2)
                pygame.draw.polygon(surf, (240, 240, 220), [
                    (cx + r - 3, cy - r // 2 - phase),
                    (cx + r + 4, cy - r // 2 - 8 - phase),
                    (cx + r + 2, cy + 4 - phase),
                ])
                pygame.draw.line(surf, (200, 160, 90),
                                 (cx + r + 1, cy - phase),
                                 (cx + r + 5, cy + 6 - phase), 2)
                _eyes(surf, cx, cy, r // 2)
            else:  # Bumblebrook
                for i in range(3):
                    pygame.draw.circle(
                        surf, _shade(self.color, -i * 18),
                        (cx - r // 2 + i * r // 2, cy + (phase if i % 2 else -phase)),
                        max(4, r - i * 3),
                    )
                _eyes(surf, cx + r // 2, cy - r // 3, r // 2)
            if s != "Pebblepuff":
                _draw_pattern(surf, self.rng, self.color,
                              pygame.Rect(cx - r, cy - r, 2 * r, 2 * r))
            _accessory(surf, self.rng, cx, cy, r, self.color)
            frames.append(surf)
        return frames


_cache = {}


def get_creature_sprites(species, color, seed, size=30):
    key = (species, color, seed, size)
    if key not in _cache:
        _cache[key] = CreatureSprite(species, color, seed, size)
    return _cache[key].frames
