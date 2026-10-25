"""Camera and all rendering: world, entities, HUD, panels, overlays."""
import numpy as np
import pygame

from . import config
from .graphics import Textures  # noqa: F401
from .inventory import ITEMS
from .pylons import RUNE_GLYPHS, RUNE_NAMES

HEART = "\u2665"
from .world import BLOCKS


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self._snap_next = True

    def snap(self, px, py):
        self.x = px - config.SCREEN_W / 2
        self.y = py - config.SCREEN_H / 2

    def follow(self, px, py, dt):
        tx = px - config.SCREEN_W / 2
        ty = py - config.SCREEN_H / 2
        if self._snap_next:
            self.x, self.y = tx, ty
            self._snap_next = False
            return
        self.x += (tx - self.x) * min(1.0, 6.0 * dt)
        self.y += (ty - self.y) * min(1.0, 6.0 * dt)

    def apply(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)

    def world_tile(self, sx, sy):
        return (
            int((sy + self.y) // config.TILE),
            int((sx + self.x) // config.TILE),
        )


class Renderer:
    def __init__(self, screen, font, big_font, small_font, textures):
        self.screen = screen
        self.font = font
        self.big = big_font
        self.small = small_font
        self.textures = textures
        self.cam = Camera()
        self.wizard = self._make_wizard_frames()
        self.sky_day = self._make_sky((255, 250, 200))
        self.sky_night = self._make_sky((230, 230, 255), night=True)
        self.sky_steps = self._make_sky_steps()
        self.hills = self._make_hills()
        self.rune_rects = {}
        self.backpack_rects = {}

    def _make_wizard_frames(self):
        W, H = config.TILE, config.TILE + 10
        frames = []
        for phase in range(3):  # 0 stand, 1 walk-bob, 2 jump
            surf = pygame.Surface((W, H), pygame.SRCALPHA)
            bob = 1 if phase == 1 else 0
            jump = phase == 2
            lift = -2 if jump else 0
            cx = 16
            # cape behind the body (sways with motion)
            cape_pts = [(cx - 4, 16 + bob + lift), (cx - 11, 26 + bob),
                        (cx - 3, 30 + bob)]
            pygame.draw.polygon(surf, (150, 60, 110, 255), cape_pts)
            # robe body with left-lit shading
            robe = (cx - 6, 14 + bob + lift, 12, 18) \
                if jump else (cx - 6, 14 + bob, 12, 20)
            pygame.draw.rect(surf, (70, 80, 170, 255), robe)
            pygame.draw.rect(surf, (100, 112, 205, 255),
                              (robe[0], robe[1], 4, robe[3]))
            # belt
            pygame.draw.rect(surf, (230, 190, 90, 255),
                             (robe[0], robe[1] + 11, 12, 2))
            # head + hat
            hy = 10 + bob + lift
            pygame.draw.circle(surf, (255, 226, 190, 255), (cx, hy), 6)
            pygame.draw.circle(surf, (255, 240, 215, 255), (cx - 2, hy - 1), 3)
            pygame.draw.polygon(surf, (50, 50, 110, 255),
                                [(cx - 9, hy - 3), (cx + 9, hy - 3),
                                 (cx + 3, hy - 22)])
            pygame.draw.rect(surf, (65, 65, 130, 255),
                             (cx - 11, hy - 5, 22, 3))
            # star on the hat
            pygame.draw.circle(surf, (255, 214, 92, 255),
                               (cx + 2, hy - 12), 2)
            # wand (raised when jumping)
            wand_y = hy + 4 if jump else hy + 6 + bob
            pygame.draw.line(surf, (150, 100, 60, 255),
                             (cx + 8, wand_y), (cx + 14, wand_y - 9), 2)
            pygame.draw.circle(surf, (255, 250, 180, 255),
                               (cx + 15, wand_y - 10), 4 if jump else 3)
            if jump:
                halo = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 250, 180, 90), (6, 6), 5)
                surf.blit(halo, (cx + 9, wand_y - 16))
                pygame.draw.polygon(surf, (255, 226, 190, 255),
                                    [(cx - 5, 32), (cx + 1, 28), (cx - 3, 36)])
            # dark outline pass for readability
            mask = pygame.mask.from_surface(surf)
            outline = mask.outline()
            for (ox, oy) in outline:
                surf.set_at((ox, oy), (30, 25, 45, 255))
            frames.append(surf)
        return frames

    def _make_hills(self):
        layers = []
        depth = 0
        for (col_a, col_b), speed in (
            (((120, 150, 180), (150, 175, 205)), 0.15),
            (((95, 135, 160), (125, 160, 185)), 0.3),
        ):
            surf = pygame.Surface((config.SCREEN_W * 2, config.SCREEN_H),
                                   pygame.SRCALPHA)
            for x in range(0, config.SCREEN_W * 2, 8):
                h = int(90 + 40 * np.sin(x * 0.006 + depth * 2)
                        + 25 * np.sin(x * 0.017 + depth))
                col = col_a if (x // 8) % 2 == 0 else col_b
                pygame.draw.rect(surf, (*col, 160),
                                 (x, config.SCREEN_H - h, 8, h))
            layers.append((surf, speed))
            depth += 1
        return layers

    def _make_sky(self, sun_color, night=False):
        sky = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
        top = np.array((25, 30, 60) if night
                       else config.PALETTE["bg_top"], dtype=float)
        bot = np.array((60, 70, 110) if night
                       else config.PALETTE["bg_bottom"], dtype=float)
        for y in range(0, config.SCREEN_H, 2):
            t = y / config.SCREEN_H
            c = (top + (bot - top) * t).astype(int)
            pygame.draw.line(sky, c, (0, y), (config.SCREEN_W, y), 2)
        if night:
            rng = np.random.default_rng(7)
            for _ in range(60):
                x = int(rng.integers(0, config.SCREEN_W))
                y = int(rng.integers(0, config.SCREEN_H // 2))
                s = int(rng.integers(1, 3))
                pygame.draw.circle(sky, (240, 240, 255), (x, y), s)
            pygame.draw.circle(sky, (230, 230, 250),
                               (config.SCREEN_W - 160, 100), 26)
        else:
            pygame.draw.circle(sky, sun_color, (config.SCREEN_W - 160, 100), 34)
            rng = np.random.default_rng(7)
            for _ in range(3):
                cx = int(rng.integers(100, config.SCREEN_W - 100))
                cy = int(rng.integers(60, 200))
                pygame.draw.circle(sky, (255, 255, 255), (cx, cy), 26)
                pygame.draw.circle(sky, (255, 255, 255), (cx + 22, cy + 6), 20)
                pygame.draw.circle(sky, (255, 255, 255), (cx - 20, cy + 8), 18)
        return sky

    def _make_sky_steps(self, levels=6):
        steps = [self.sky_day]
        for i in range(1, levels):
            amt = i / levels
            mixed = self.sky_day.copy()
            night = self.sky_night.copy()
            night.set_alpha(int(255 * amt))
            mixed.blit(night, (0, 0))
            steps.append(mixed)
        steps.append(self.sky_night)
        return steps

    def draw_sky(self, day_t):
        night_amt = max(0.0, np.sin((day_t - 0.25) * 2 * np.pi))
        idx = int(night_amt * (len(self.sky_steps) - 1) + 0.5)
        self.screen.blit(self.sky_steps[idx], (0, 0))

    def draw_parallax(self):
        if config.PERFORMANCE_MODE:
            return
        for surf, speed in self.hills:
            x = -int(self.cam.x * speed) % config.SCREEN_W
            self.screen.blit(surf, (x - config.SCREEN_W, 0))
            self.screen.blit(surf, (x, 0))

    _glow_cache = {}

    def _glow_surface(self, color, radius):
        key = (color, radius)
        surf = self._glow_cache.get(key)
        if surf is None:
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            steps = 4
            for i in range(steps, 0, -1):
                a = int(26 * i / steps)
                pygame.draw.circle(surf, (*color, a),
                                   (radius, radius), int(radius * i / steps))
            self._glow_cache[key] = surf
        return surf

    _vignette = None
    _tint = None

    def draw_time_overlay(self, day_t):
        """Warm tint at dawn/dusk; dark vignette + light pool at night."""
        s = self.screen
        night_amt = max(0.0, np.sin((day_t - 0.25) * 2 * np.pi))
        if 0.15 < night_amt < 0.85:
            # golden-hour tint during transitions: BLEND_RGB_ADD ignores
            # alpha, so pre-scale the color by the intended strength
            strength = 26 / 255
            warm = (int(255 * strength), int(180 * strength), int(90 * strength))
            if self._tint is None:
                self._tint = pygame.Surface(
                    (config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            self._tint.fill(warm)
            s.blit(self._tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        if night_amt > 0.4 and not config.PERFORMANCE_MODE:
            if self._vignette is None:
                ys, xs = np.mgrid[0:config.SCREEN_H, 0:config.SCREEN_W]
                cx, cy = config.SCREEN_W / 2, config.SCREEN_H / 2
                d = np.sqrt(((xs - cx) / (config.SCREEN_W / 2)) ** 2
                            + ((ys - cy) / (config.SCREEN_H / 2)) ** 2)
                alpha = np.clip((d - 0.55) / 0.45, 0, 1) ** 1.6
                arr = np.zeros((config.SCREEN_H, config.SCREEN_W, 4),
                               dtype=np.uint8)
                arr[..., 0] = 10
                arr[..., 1] = 12
                arr[..., 2] = 40
                arr[..., 3] = (alpha * 130).astype(np.uint8)
                self._vignette = pygame.image.frombuffer(
                    arr.tobytes(), (config.SCREEN_W, config.SCREEN_H),
                    "RGBA").convert_alpha()
            s.blit(self._vignette, (0, 0))

    def draw_glow(self, points):
        if config.PERFORMANCE_MODE:
            return
        for wx, wy, color, radius in points:
            x, y = self.cam.apply(wx, wy)
            if not (-100 < x < config.SCREEN_W + 100):
                continue
            surf = self._glow_surface(color, radius)
            self.screen.blit(surf, (x - radius, y - radius),
                             special_flags=pygame.BLEND_RGB_ADD)

    def _rebuild_world_cache(self, world):
        surf = pygame.Surface((world.cols * config.TILE,
                               world.rows * config.TILE))
        for r in range(world.rows):
            for c in range(world.cols):
                b = int(world.grid[r, c])
                if b == 0:
                    continue
                tex = self.textures.blocks.get(b)
                if tex:
                    surf.blit(tex, (c * config.TILE, r * config.TILE))
        self._world_surf = surf
        self._world_dirty = set()

    def mark_dirty(self, row, col):
        if getattr(self, "_world_dirty", None) is not None:
            self._world_dirty.add((row, col))

    def draw_world(self, world, day_t=0.25, glow_points=None):
        self.draw_sky(day_t)
        self.draw_parallax()
        if getattr(self, "_world_surf", None) is None:
            self._rebuild_world_cache(world)
        else:
            for (r, c) in self._world_dirty:
                surf = self._world_surf
                rect = pygame.Rect(c * config.TILE, r * config.TILE,
                                   config.TILE, config.TILE)
                surf.fill((0, 0, 0), rect)
                b = int(world.grid[r, c])
                tex = self.textures.blocks.get(b)
                if tex:
                    surf.blit(tex, rect.topleft)
            self._world_dirty.clear()
        area = pygame.Rect(int(self.cam.x), int(self.cam.y),
                           config.SCREEN_W, config.SCREEN_H)
        area = area.clip(self._world_surf.get_rect())
        self.screen.blit(self._world_surf,
                         (-int(self.cam.x), -int(self.cam.y)), area)
        if glow_points:
            self.draw_glow(glow_points)

    _crack_surf = None

    def draw_break_crack(self, row, col, progress):
        """progress 0..1 -> crack overlay grows."""
        x, y = self.cam.apply(col * config.TILE, row * config.TILE)
        rect = pygame.Rect(x, y, config.TILE, config.TILE)
        if self._crack_surf is None:
            self._crack_surf = pygame.Surface(
                (config.TILE, config.TILE), pygame.SRCALPHA)
        shade = self._crack_surf
        shade.fill((0, 0, 0, int(60 * progress)))
        self.screen.blit(shade, rect.topleft)
        n = int(progress * 4) + 1
        rng = np.random.default_rng((row + 1) * (col + 7))
        for i in range(n):
            x0 = int(rng.integers(2, config.TILE - 2))
            y0 = int(rng.integers(2, config.TILE - 2))
            pygame.draw.line(shade, (255, 255, 255, 140),
                             (x0, y0), (x0 + 6, y0 + 5), 1)
        self.screen.blit(shade, rect.topleft)

    _beam_surf = None

    def draw_wand_beam(self, x0, y0, x1, y1, t):
        """glowing beam for ~t seconds after cast; fade out."""
        if t <= 0:
            return
        if self._beam_surf is None:
            self._beam_surf = pygame.Surface(
                (config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        alpha = max(0, min(255, int(255 * t / 0.25)))
        sx, sy = self.cam.apply(x0, y0)
        ex, ey = self.cam.apply(x1, y1)
        self._beam_surf.fill((0, 0, 0, 0))
        pygame.draw.line(self._beam_surf, (150, 220, 255, alpha),
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(self._beam_surf, (255, 255, 255, alpha),
                         (sx, sy), (ex, ey), 2)
        self.screen.blit(self._beam_surf, (0, 0))

    def highlight_tile(self, row, col, ok=True):
        x, y = self.cam.apply(col * config.TILE, row * config.TILE)
        rect = pygame.Rect(x, y, config.TILE, config.TILE)
        color = (255, 255, 255) if ok else (255, 120, 120)
        pygame.draw.rect(self.screen, color, rect, 2)

    _shadow_ell = None

    def draw_blob_shadow(self, wx, wy, width=20):
        """Soft ellipse shadow on the ground below an entity."""
        if self._shadow_ell is None:
            self._shadow_ell = pygame.Surface((48, 16), pygame.SRCALPHA)
        s = self._shadow_ell
        s.fill((0, 0, 0, 0))
        pygame.draw.ellipse(s, (20, 16, 30, 70),
                            (24 - width // 2, 2, width, 10))
        x, y = self.cam.apply(wx, wy)
        self.screen.blit(s, (x - 24, y - 8))

    def draw_player(self, player):
        x, y = self.cam.apply(player.x, player.y)
        self.draw_blob_shadow(player.x, player.y + 20, width=18)
        if not player.on_ground:
            frame = self.wizard[2]
        else:
            moving = abs(player.vx) > 1
            frame = self.wizard[pygame.time.get_ticks() // 200 % 2] \
                if moving else self.wizard[0]
        if player.facing < 0:
            frame = pygame.transform.flip(frame, True, False)
        self.screen.blit(frame, frame.get_rect(center=(x, y)))

    _weather_surf_day = None
    _weather_surf_night = None

    def draw_weather(self, t, day_t):
        """Drifting pollen by day, fireflies at night."""
        if config.PERFORMANCE_MODE:
            return
        night = np.sin((day_t - 0.25) * 2 * np.pi) > 0
        if night:
            if self._weather_surf_night is None:
                self._weather_surf_night = pygame.Surface((8, 8), pygame.SRCALPHA)
            surf = self._weather_surf_night
        else:
            if self._weather_surf_day is None:
                self._weather_surf_day = pygame.Surface((6, 6), pygame.SRCALPHA)
            surf = self._weather_surf_day
        rng = np.random.default_rng(1234)
        s = self.screen
        for i in range(18):
            speed = 12 + (i % 3) * 6
            x = (rng.integers(0, config.SCREEN_W) - t * speed) \
                % config.SCREEN_W
            y = (rng.integers(60, config.SCREEN_H - 80)
                 + np.sin(t * 0.7 + i) * 12)
            if night:
                tw = 0.5 + 0.5 * np.sin(t * 3 + i * 1.7)
                surf.fill((0, 0, 0, 0))
                a = int(120 * tw)
                pygame.draw.circle(surf, (255, 240, 150, a), (4, 4), 3)
                s.blit(surf, (int(x) - 4, int(y) - 4))
            else:
                surf.fill((0, 0, 0, 0))
                pygame.draw.circle(surf, (255, 255, 210, 90), (3, 3), 2)
                s.blit(surf, (int(x) - 3, int(y) - 3))

    def draw_fountain(self, fountain, world):
        col = fountain.col
        row = world.surface_row(col)
        x, y = self.cam.apply((col + 0.5) * config.TILE,
                              row * config.TILE)
        basin = pygame.Rect(x - 14, y - 10, 28, 10)
        pygame.draw.ellipse(self.screen, (120, 200, 235), basin)
        pygame.draw.ellipse(self.screen, (90, 70, 50), basin, 2)
        pillar = pygame.Rect(x - 4, y - 30, 8, 22)
        pygame.draw.rect(self.screen, (200, 205, 215), pillar)
        t = pygame.time.get_ticks() * 0.004
        for i in range(3):
            yy = y - 30 + (i * 6) + 3 * np.sin(t + i)
            pygame.draw.circle(self.screen, (170, 225, 250),
                               (x + int(4 * np.sin(t * 1.3 + i)), int(yy)), 3)
        label = self.small.render("Blessing Fountain", True, (90, 60, 40))
        bg = label.get_rect(topleft=(x - label.get_width() // 2, y - 52))
        bg.inflate_ip(8, 5)
        pygame.draw.rect(self.screen, (255, 245, 210), bg, border_radius=5)
        pygame.draw.rect(self.screen, (90, 70, 50), bg, 2, border_radius=5)
        self.screen.blit(label, (bg.x + 4, bg.y + 2))

    def draw_castle_banner(self, castle, world):
        col = castle.col
        row = world.surface_row(col)
        x, y = self.cam.apply((col + 0.5) * config.TILE,
                              (row - 2) * config.TILE)
        pole = pygame.Rect(x - 3, y - config.TILE * 2, 6, config.TILE * 2)
        pygame.draw.rect(self.screen, (120, 90, 60), pole)
        wave = 3 * np.sin(pygame.time.get_ticks() * 0.004)
        flag = pygame.Rect(x + 3, y - config.TILE * 2, 44, 26)
        pygame.draw.polygon(self.screen, (255, 120, 110), [
            (flag.x, flag.y + wave),
            (flag.right, flag.y + 6 + wave),
            (flag.right, flag.y + flag.h + wave),
            (flag.x, flag.y + flag.h + wave),
        ])
        pygame.draw.circle(self.screen, (255, 214, 92),
                           (flag.x + 12, flag.y + 13 + wave), 5)
        label = self.small.render("Build your citadel here!", True, (90, 60, 40))
        bg = label.get_rect(
            topleft=(x - label.get_width() // 2 + 20,
                     y - config.TILE * 2 - 24))
        bg.inflate_ip(8, 6)
        pygame.draw.rect(self.screen, (255, 245, 210), bg, border_radius=6)
        pygame.draw.rect(self.screen, (90, 70, 50), bg, 2, border_radius=6)
        self.screen.blit(label, (bg.x + 4, bg.y + 3))

    def draw_creatures(self, creatures):
        tick = pygame.time.get_ticks() // 250
        for c in creatures:
            x, y = self.cam.apply(c.x, c.y + c.bob)
            self.draw_blob_shadow(c.x, c.y + 14, width=16)
            frames = c.sprite_frames()
            frame = frames[int(tick % 2)]
            if c.dir < 0:
                frame = pygame.transform.flip(frame, True, False)
            self.screen.blit(frame, frame.get_rect(center=(x, y)))
            label = c.name if c.name else c.species
            name = self.small.render(label, True, (50, 50, 60))
            self.screen.blit(name, (x - name.get_width() // 2, y - 26))
            if not c.befriended:
                total = c.max_hearts
                left = c.hearts
                for i in range(total):
                    hx = x - total * 7 + i * 14
                    filled = i >= total - left
                    col = (255, 120, 140) if filled else (200, 200, 200)
                    pygame.draw.circle(self.screen, col, (hx, y + 20), 4)
            else:
                heart = self.small.render("\u2665 befriended", True, (230, 90, 110))
                self.screen.blit(heart, (x - heart.get_width() // 2, y + 16))

    def draw_pylons(self, pylons):
        for p in pylons:
            x, y = self.cam.apply(p.x, p.y)
            if p.restored:
                color = (255, 214, 92)
            elif p.awakened:
                color = (110, 95, 150)
            else:
                color = (70, 62, 92)
            pygame.draw.rect(
                self.screen, color,
                (x - config.TILE // 2, y - config.TILE, config.TILE, config.TILE * 2),
            )
            pygame.draw.circle(
                self.screen, (255, 255, 200) if p.restored else (80, 70, 110),
                (x, y - config.TILE), 8,
            )
            if p.restored and p.shield_radius > 2:
                pygame.draw.circle(
                    self.screen, (255, 240, 180),
                    (x, y), int(p.shield_radius), 2,
                )

    _shadow_surf = None

    def draw_shadow(self, shadow):
        if not shadow.active or shadow.banished:
            return
        x, _ = self.cam.apply(shadow.x, 0)
        if self._shadow_surf is None:
            self._shadow_surf = pygame.Surface(
                (70, config.SCREEN_H), pygame.SRCALPHA)
        surf = self._shadow_surf
        surf.fill((0, 0, 0, 0))
        w = 30 + 8 * np.sin(shadow.wobble * 2)
        pygame.draw.ellipse(surf, (20, 12, 30, 170), (35 - w / 2, 0, w, config.SCREEN_H))
        self.screen.blit(surf, (x - 35, 0))

    def draw_drops(self, drops):
        for d in drops:
            x, y = self.cam.apply(d.x, d.y + d.bob)
            name, color = ITEMS[d.item]
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 6)
            pygame.draw.circle(self.screen, (50, 40, 30), (int(x), int(y)), 6, 1)

    def draw_hud(self, game):
        s = self.screen
        pygame.draw.rect(s, (245, 240, 225), (10, 10, 360, 96), border_radius=8)
        pygame.draw.rect(s, (90, 70, 50), (10, 10, 360, 96), 2, border_radius=8)
        pygame.draw.rect(s, (230, 230, 230), (22, 22, 336, 10))
        frac = game.shield.strength(
            len(game.pylons.pylons),
            len(game.pylons.pylons) - len(game.pylons.unrestored()),
        )
        pygame.draw.rect(s, (120, 200, 240), (22, 22, int(336 * frac), 10))
        t1 = self.font.render(
            f"Friendship Shield {int(frac * 100)}%", True, config.PALETTE["text"])
        s.blit(t1, (22, 40))
        friends = sum(1 for c in game.creatures.creatures if c.befriended)
        t2 = self.font.render(
            f"Harmony {game.shield.harmony:.0f}   Friends {friends}"
            f"/{len(game.creatures.creatures)}   GA gen {game.ga.generation}",
            True, config.PALETTE["text"])
        s.blit(t2, (22, 66))

        bar_w = 9 * 58 + 8
        bar = pygame.Rect(10, config.SCREEN_H - 70, bar_w, 60)
        pygame.draw.rect(s, (245, 240, 225), bar, border_radius=8)
        pygame.draw.rect(s, (90, 70, 50), bar, 2, border_radius=8)
        for i, (item, count) in enumerate(game.inventory.hotbar):
            rect = pygame.Rect(16 + i * 58, config.SCREEN_H - 64, 52, 48)
            sel = i == game.inventory.selected
            pygame.draw.rect(s, (255, 220, 120) if sel else (215, 208, 190), rect, 2)
            if item:
                name, color = ITEMS[item]
                if item == "wand":
                    pygame.draw.line(s, (150, 100, 60), rect.center,
                                     (rect.center[0] + 12, rect.center[1] - 14), 3)
                    pygame.draw.circle(s, (255, 250, 180),
                                       (rect.center[0] + 13, rect.center[1] - 15), 4)
                else:
                    pygame.draw.rect(s, color, rect.inflate(-16, -16), border_radius=4)
                if count:
                    ct = self.small.render(str(count), True, (40, 34, 28))
                    s.blit(ct, (rect.right - ct.get_width() - 2, rect.bottom - 16))
            num = self.small.render(str(i + 1), True, (120, 105, 90))
            s.blit(num, (rect.x + 3, rect.y + 2))

    def draw_quests(self, game):
        s = self.screen
        friends = sum(1 for c in game.creatures.creatures if c.befriended)
        total_friends = len(game.creatures.creatures)
        restored = len(game.pylons.pylons) - len(game.pylons.unrestored())
        awake = sum(1 for p in game.pylons.pylons if p.awakened)
        total_pylons = len(game.pylons.pylons)
        harmony = game.shield.harmony
        pyl_label = (f"Restore pylons ({restored}/{awake})"
                     if awake < total_pylons
                     else f"Restore pylons ({restored}/{total_pylons})")
        quests = [
            (f"Befriend creatures ({friends}/{total_friends})", friends >= total_friends),
            (pyl_label, restored >= total_pylons),
            ("Fill Harmony to 100", harmony >= 100),
        ]
        done = all(ok for _, ok in quests)
        x, y = config.SCREEN_W - 300, 14
        panel = pygame.Rect(x, y, 286, 30 + 26 * len(quests))
        pygame.draw.rect(s, (245, 240, 225), panel, border_radius=8)
        pygame.draw.rect(s, (90, 70, 50), panel, 2, border_radius=8)
        title = self.font.render(
            "Your Quests" if not done else "All quests complete!",
            True, config.PALETTE["text"],
        )
        s.blit(title, (x + 12, y + 6))
        for i, (text, ok) in enumerate(quests):
            yy = y + 34 + i * 26
            box = pygame.Rect(x + 12, yy + 2, 14, 14)
            pygame.draw.rect(s, (120, 200, 120) if ok else (230, 230, 230),
                             box, border_radius=3)
            if ok:
                pygame.draw.line(s, (255, 255, 255), (box.x + 3, box.y + 7),
                                 (box.x + 6, box.y + 10), 2)
                pygame.draw.line(s, (255, 255, 255), (box.x + 6, box.y + 10),
                                 (box.x + 11, box.y + 4), 2)
            else:
                pygame.draw.rect(s, (150, 140, 130), box, 2, border_radius=3)
            label = self.small.render(text, True,
                                      (110, 100, 90) if ok else (60, 50, 40))
            s.blit(label, (x + 34, yy))

    def draw_message(self, message):
        if not message:
            return
        surf = self.font.render(message, True, (50, 40, 30))
        pad = 12
        box = surf.get_rect(center=(config.SCREEN_W // 2, 120))
        bg = pygame.Rect(box.x - pad, box.y - 6, box.w + pad * 2, box.h + 12)
        pygame.draw.rect(self.screen, (255, 245, 210), bg, border_radius=8)
        pygame.draw.rect(self.screen, (90, 70, 50), bg, 2, border_radius=8)
        self.screen.blit(surf, box)

    def draw_puzzle(self, pylon):
        s = self.screen
        cols = len(RUNE_NAMES)
        pw = cols * 90 + 40
        panel = pygame.Rect(config.SCREEN_W // 2 - pw // 2, 150, pw, 200)
        pygame.draw.rect(s, (246, 240, 225), panel, border_radius=10)
        pygame.draw.rect(s, (90, 70, 50), panel, 3, border_radius=10)
        title = self.font.render("Align the runes! Click in the lit order.", True,
                                 config.PALETTE["text"])
        s.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))
        hint = ", ".join(pylon.rune_order_hint())
        hint_s = self.small.render(f"Feel the energy: {hint}", True, (110, 90, 70))
        s.blit(hint_s, (panel.centerx - hint_s.get_width() // 2, panel.y + 42))
        self.rune_rects = {}
        for i, rune in enumerate(RUNE_NAMES):
            rx = panel.x + 20 + i * 90
            ry = panel.y + 68
            rect = pygame.Rect(rx, ry, 80, 80)
            self.rune_rects[rune] = rect
            done = rune in pylon.target_seq[: pylon.progress]
            base = (255, 214, 92) if done else (215, 208, 190)
            pygame.draw.rect(s, base, rect, border_radius=8)
            pygame.draw.rect(s, (90, 70, 50), rect, 2, border_radius=8)
            g = self.big.render(RUNE_GLYPH[rune], True, (60, 50, 40))
            s.blit(g, g.get_rect(center=rect.center))
            lbl = self.small.render(rune, True, (110, 90, 70))
            s.blit(lbl, lbl.get_rect(center=(rect.centerx, rect.bottom + 10)))

    def draw_inventory_screen(self, game):
        s = self.screen
        overlay = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((20, 24, 40, 190))
        s.blit(overlay, (0, 0))
        panel = pygame.Rect(200, 80, config.SCREEN_W - 400, config.SCREEN_H - 160)
        pygame.draw.rect(s, (246, 240, 225), panel, border_radius=12)
        pygame.draw.rect(s, (90, 70, 50), panel, 3, border_radius=12)
        title = self.big.render("Friendship Ledger", True, config.PALETTE["text"])
        s.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 16))
        y = panel.y + 66
        friends = ", ".join(
            f"{c.name or c.species} " + (
                HEART if c.befriended else "?")
            for c in game.creatures.creatures
        )
        line1 = self.font.render(f"Citizens of the realm:  {friends}", True, (80, 65, 50))
        s.blit(line1, (panel.x + 24, y)); y += 30
        restored = len(game.pylons.pylons) - len(game.pylons.unrestored())
        line2 = self.font.render(
            f"Pylons restored: {restored}/{len(game.pylons.pylons)}    "
            f"Harmony: {game.shield.harmony:.0f}    GA generation: {game.ga.generation}",
            True, (80, 65, 50))
        s.blit(line2, (panel.x + 24, y)); y += 30
        hint = self._compass_hints(game)
        if hint:
            line2b = self.font.render(hint, True, (60, 90, 60))
            s.blit(line2b, (panel.x + 24, y)); y += 30
        line3 = self.font.render(
            "Castle: place quartz, crystal, starlight, oak, or castle blocks near the "
            "heart of the realm to raise Harmony.", True, (80, 65, 50))
        line3b = self.small.render(
            "Tip: keep some of each material! Creatures love living beside their "
            "favorite blocks - the fountain blesses only your surplus.",
            True, (110, 90, 70))
        s.blit(line3, (panel.x + 24, y)); y += 26
        s.blit(line3b, (panel.x + 24, y)); y += 22
        got = sum(1 for d in game.achievements.DEFS
                  if d[0] in game.achievements.unlocked)
        badge_row = self.font.render(
            "Badges:  " + " ".join(
                "\u2605" if d[0] in game.achievements.unlocked else "\u2606"
                for d in game.achievements.DEFS
            ) + f"   ({got}/{len(game.achievements.DEFS)})",
            True, (200, 150, 60))
        s.blit(badge_row, (panel.x + 24, y)); y += 30
        inv = self.font.render(
            "Backpack (click: to hotbar. Right-click a hotbar slot below: to backpack)",
            True, config.PALETTE["text"])
        s.blit(inv, (panel.x + 24, y)); y += 30
        self.backpack_rects = {}
        for r in range(3):
            for c in range(9):
                x = panel.x + 24 + c * 58
                rect = pygame.Rect(x, y + r * 54, 52, 48)
                self.backpack_rects[(r, c)] = rect
                pygame.draw.rect(s, (215, 208, 190), rect, 2, border_radius=4)
                item, count = game.inventory.backpack[r][c]
                if item:
                    name, color = ITEMS[item]
                    pygame.draw.rect(s, color, rect.inflate(-16, -16), border_radius=4)
                    if count:
                        ct = self.small.render(str(count), True, (40, 34, 28))
                        s.blit(ct, (rect.right - ct.get_width() - 2,
                                    rect.bottom - 16))
        hot_y = y + 3 * 54 + 16
        hot_label = self.small.render("Hotbar (right-click to store):", True,
                                      (110, 90, 70))
        s.blit(hot_label, (panel.x + 24, hot_y - 18))
        for i, (item, count) in enumerate(game.inventory.hotbar):
            x = panel.x + 24 + i * 58
            rect = pygame.Rect(x, hot_y, 52, 48)
            self.backpack_rects[(3, i)] = rect
            pygame.draw.rect(s, (255, 220, 120) if i == game.inventory.selected
                             else (215, 208, 190), rect, 2, border_radius=4)
            if item:
                name, color = ITEMS[item]
                if item == "wand":
                    pygame.draw.line(s, (150, 100, 60), rect.center,
                                     (rect.center[0] + 12, rect.center[1] - 14), 3)
                    pygame.draw.circle(s, (255, 250, 180),
                                       (rect.center[0] + 13, rect.center[1] - 15), 4)
                else:
                    pygame.draw.rect(s, color, rect.inflate(-16, -16), border_radius=4)
                if count:
                    ct = self.small.render(str(count), True, (40, 34, 28))
                    s.blit(ct, (rect.right - ct.get_width() - 2, rect.bottom - 16))
        hint = self.small.render(
            "E or Esc to close  |  Click backpack item: to hotbar  |  "
            "Right-click a hotbar row below: to backpack  |  F5 saves",
            True, (110, 90, 70))
        s.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 34))

    def _compass_hints(self, game):
        px = game.player.x
        parts = []
        best_c = None
        best_d = float("inf")
        for c in game.creatures.creatures:
            if not c.befriended:
                d = abs(c.x - px)
                if d < best_d:
                    best_c, best_d = c, d
        if best_c is not None:
            dist = int(best_d // config.TILE)
            side = "right" if best_c.x >= px else "left"
            parts.append(
                f"A lonely {best_c.species} waits {dist} steps to your {side}"
            )
        best_p = None
        best_d = float("inf")
        for p in game.pylons.pylons:
            if not p.restored:
                d = abs(p.x - px)
                if d < best_d:
                    best_p, best_d = p, d
        if best_p is not None:
            dist = int(best_d // config.TILE)
            side = "right" if best_p.x >= px else "left"
            parts.append(f"a sleeping pylon glows {dist} steps to your {side}")
        if not parts:
            return ""
        return "Where to go: " + "  |  ".join(parts)

    title_button_rect = None

    def draw_title(self, first=True):
        s = self.screen
        overlay = pygame.Surface((config.SCREEN_W, config.SCREEN_H),
                                 pygame.SRCALPHA)
        overlay.fill((20, 24, 50, 140))
        s.blit(overlay, (0, 0))
        title = pygame.transform.scale2x(
            self.big.render("Citadel of Friendship & Magic", True, (255, 245, 210)))
        s.blit(title, title.get_rect(center=(config.SCREEN_W // 2, 160)))
        sub = self.font.render(
            "Build a castle, make friends, and light up the world!",
            True, (230, 230, 240))
        s.blit(sub, sub.get_rect(center=(config.SCREEN_W // 2, 240)))
        btn_w, btn_h = 280, 80
        self.title_button_rect = pygame.Rect(
            config.SCREEN_W // 2 - btn_w // 2, 340, btn_w, btn_h)
        pulse = 3 * int(np.sin(pygame.time.get_ticks() * 0.005))
        pygame.draw.rect(s, (255, 214, 92), self.title_button_rect.inflate(
            pulse * 2, pulse * 2), border_radius=14)
        from .save import has_save
        label_txt = "Continue!" if has_save() else "Play!"
        label = self.big.render(label_txt, True, (60, 40, 20))
        s.blit(label, label.get_rect(center=self.title_button_rect.center))
        hint = self.small.render(
            "or press Enter/Space  -  H for help  -  gamepads work too!",
            True, (200, 200, 215))
        s.blit(hint, hint.get_rect(center=(config.SCREEN_W // 2, 470)))
        ded = self.small.render(
            "made with love for Emmett", True, (255, 214, 92))
        s.blit(ded, (config.SCREEN_W - ded.get_width() - 16,
                     config.SCREEN_H - ded.get_height() - 12))

    def draw_hints(self):
        s = self.screen
        overlay = pygame.Surface((config.SCREEN_W, config.SCREEN_H),
                                 pygame.SRCALPHA)
        overlay.fill((20, 24, 50, 150))
        s.blit(overlay, (0, 0))
        panel = pygame.Rect(240, 80, config.SCREEN_W - 480,
                            config.SCREEN_H - 160)
        pygame.draw.rect(s, (246, 240, 225), panel, border_radius=12)
        pygame.draw.rect(s, (90, 70, 50), panel, 3, border_radius=12)
        title = self.big.render("How to Play", True, config.PALETTE["text"])
        s.blit(title, title.get_rect(center=(panel.centerx, panel.y + 40)))
        hints = [
            ("Move", "A / D or Left / Right arrows (or gamepad stick)"),
            ("Jump", "W, Space, or Up arrow"),
            ("Break blocks", "Hold LEFT click on a block near you"),
            ("Place blocks", "RIGHT click with blocks selected (1-9 / scroll)"),
            ("Make friends", "LEFT click creatures with your Wand to charm "
                "them - or feed them Sunberries (RIGHT click)!"),
            ("Light pylons", "LEFT click a sleeping pylon, then click the "
                "runes in the lit order"),
            ("Keys & Catalysts", "Mine glowing shards and blooms; RIGHT click "
                "a pylon to use a Rune Key"),
            ("Friendship Ledger", "E - see creatures, find where to go, move "
                "items between hotbar and backpack"),
            ("Save", "F5 quick-saves; the game also saves when you quit"),
        ]
        y = panel.y + 80
        for head, body in hints:
            h = self.font.render(head, True, (150, 90, 40))
            s.blit(h, (panel.x + 30, y))
            b = self.font.render(body, True, (60, 50, 40))
            s.blit(b, (panel.x + 210, y))
            y += 34
        foot = self.small.render(
            "Press H or click to go back to the game", True, (110, 90, 70))
        s.blit(foot, foot.get_rect(center=(panel.centerx, panel.bottom - 28)))

    def draw_naming(self, text):
        s = self.screen
        box = pygame.Rect(config.SCREEN_W // 2 - 240, 200, 480, 90)
        pygame.draw.rect(s, (246, 240, 225), box, border_radius=10)
        pygame.draw.rect(s, (90, 70, 50), box, 3, border_radius=10)
        t1 = self.font.render("Name your friend:", True, (60, 50, 40))
        s.blit(t1, (box.x + 20, box.y + 14))
        caret = "|" if pygame.time.get_ticks() // 400 % 2 == 0 else ""
        t2 = self.big.render(text + caret, True, (150, 90, 40))
        s.blit(t2, (box.x + 20, box.y + 40))
        foot = self.small.render("Enter to confirm  -  Esc to cancel",
                                 True, (110, 90, 70))
        s.blit(foot, (box.right - foot.get_width() - 14, box.bottom - 22))

    def draw_victory(self):
        s = self.screen
        overlay = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((255, 245, 210, 210))
        s.blit(overlay, (0, 0))
        t1 = self.big.render("The Unnamed Shadow is banished!", True, (90, 60, 30))
        t1 = pygame.transform.scale2x(t1)
        s.blit(t1, t1.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2 - 60)))
        t2 = self.font.render(
            "Warmth, friendship, and your citadel have filled the realm with light.",
            True, (90, 60, 30))
        s.blit(t2, t2.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2 + 50)))
        t3 = self.font.render(
            "Press R for a brand-new realm, or keep building your dream citadel.",
            True, (90, 60, 30))
        s.blit(t3, t3.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2 + 90)))
