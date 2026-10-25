"""Camera and all rendering: world, entities, HUD, panels, overlays."""
import numpy as np
import pygame

from . import config
from .graphics import make_creature_sprite, make_wizard
from .inventory import ITEMS
from .pylons import RUNE_GLYPHS, RUNE_NAMES
from .world import BLOCKS


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def follow(self, px, py, dt):
        tx = px - config.SCREEN_W / 2
        ty = py - config.SCREEN_H / 2
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
        self.wizard = make_wizard()
        self.sky = self._make_sky()
        self.rune_rects = {}
        self.backpack_rects = {}

    def _make_sky(self):
        sky = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
        top = np.array(config.PALETTE["bg_top"], dtype=float)
        bot = np.array(config.PALETTE["bg_bottom"], dtype=float)
        for y in range(config.SCREEN_H):
            t = y / config.SCREEN_H
            c = top + (bot - top) * t
            pygame.draw.line(sky, c, (0, y), (config.SCREEN_W, y))
        pygame.draw.circle(sky, (255, 250, 200), (config.SCREEN_W - 160, 100), 34)
        rng = np.random.default_rng(7)
        for _ in range(3):
            cx = int(rng.integers(100, config.SCREEN_W - 100))
            cy = int(rng.integers(60, 200))
            pygame.draw.circle(sky, (255, 255, 255), (cx, cy), 26)
            pygame.draw.circle(sky, (255, 255, 255), (cx + 22, cy + 6), 20)
            pygame.draw.circle(sky, (255, 255, 255), (cx - 20, cy + 8), 18)
        return sky

    def draw_world(self, world):
        self.screen.blit(self.sky, (0, 0))
        c0 = max(0, int(self.cam.x // config.TILE) - 1)
        c1 = min(world.cols, int((self.cam.x + config.SCREEN_W) // config.TILE) + 2)
        r0 = max(0, int(self.cam.y // config.TILE) - 1)
        r1 = min(world.rows, int((self.cam.y + config.SCREEN_H) // config.TILE) + 2)
        for r in range(r0, r1):
            for c in range(c0, c1):
                b = world.get(r, c)
                if b == 0:
                    continue
                x, y = self.cam.apply(c * config.TILE, r * config.TILE)
                tex = self.textures.blocks.get(b)
                if tex:
                    self.screen.blit(tex, (x, y))

    def highlight_tile(self, row, col, ok=True):
        x, y = self.cam.apply(col * config.TILE, row * config.TILE)
        rect = pygame.Rect(x, y, config.TILE, config.TILE)
        color = (255, 255, 255) if ok else (255, 120, 120)
        pygame.draw.rect(self.screen, color, rect, 2)

    def draw_player(self, player):
        x, y = self.cam.apply(player.x, player.y)
        rect = self.wizard.get_rect(center=(x, y))
        if player.facing < 0:
            self.screen.blit(pygame.transform.flip(self.wizard, True, False), rect)
        else:
            self.screen.blit(self.wizard, rect)

    def draw_creatures(self, creatures):
        for c in creatures:
            x, y = self.cam.apply(c.x, c.y + c.bob)
            sprite = make_creature_sprite(c.color)
            self.screen.blit(sprite, sprite.get_rect(center=(x, y)))
            name = self.small.render(c.species, True, (50, 50, 60))
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
            color = (255, 214, 92) if p.restored else (110, 95, 150)
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

    def draw_shadow(self, shadow):
        if not shadow.active or shadow.banished:
            return
        x, _ = self.cam.apply(shadow.x, 0)
        surf = pygame.Surface((70, config.SCREEN_H), pygame.SRCALPHA)
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
        total_pylons = len(game.pylons.pylons)
        harmony = game.shield.harmony
        quests = [
            (f"Befriend creatures ({friends}/{total_friends})", friends >= total_friends),
            (f"Restore pylons ({restored}/{total_pylons})", restored >= total_pylons),
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
            f"{c.species} {'\u2665' if c.befriended else '?'}"
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
        line3 = self.font.render(
            "Castle: place quartz, crystal, starlight, oak, or castle blocks near the "
            "heart of the realm to raise Harmony.", True, (80, 65, 50))
        s.blit(line3, (panel.x + 24, y)); y += 40
        inv = self.font.render(
            "Backpack (click an item to move it to your hotbar):", True,
            config.PALETTE["text"])
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
        hint = self.small.render(
            "E or Esc to close   |   F5 quick-saves   |   Feed Sunberries to creatures "
            "with right-click!", True, (110, 90, 70))
        s.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 34))

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
