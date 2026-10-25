"""Pygame rendering for the voxel grid, HUD, hotbar, and overlays."""
import pygame

from . import config, world as W
from .world import BLOCK_COLORS


class Renderer:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small = small_font
        self.camera_col = 0.0

    def world_to_screen(self, col, row, player_col, player_row):
        x = col * config.TILE - player_col * config.TILE + config.SCREEN_W // 2
        y = row * config.TILE - player_row * config.TILE + config.SCREEN_H // 2
        return int(x), int(y)

    def draw_world(self, world, player):
        self.screen.fill(config.PALETTE["bg"])
        cols = config.SCREEN_W // config.TILE + 2
        for dc in range(-cols // 2, cols // 2 + 1):
            col = player.col + dc
            if not 0 <= col < world.cols:
                continue
            for row in range(world.rows):
                block = world.get(row, col)
                if block == W.AIR:
                    continue
                x, y = self.world_to_screen(col, row, player.col, player.row)
                if y < -config.TILE or y > config.SCREEN_H:
                    continue
                color = BLOCK_COLORS.get(block, (90, 90, 90))
                rect = pygame.Rect(x, y, config.TILE, config.TILE)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def draw_player(self, player):
        x = config.SCREEN_W // 2
        y = config.SCREEN_H // 2
        pygame.draw.circle(self.screen, (255, 240, 220), (x, y), config.PLAYER_DRAW_R)
        pygame.draw.circle(self.screen, (90, 140, 255), (x, y - 4), 4)

    def draw_creatures(self, creatures, player):
        for c in creatures:
            x, y = self.world_to_screen(c.col, c.row, player.col, player.row)
            pygame.draw.circle(self.screen, c.color, (x + 8, y + 8), 7)
            if c.befriended:
                pygame.draw.circle(self.screen, (255, 255, 255), (x + 8, y + 2), 2)

    def draw_pylons(self, pylons, player):
        for p in pylons:
            x, y = self.world_to_screen(p.col, p.row, player.col, player.row)
            color = (255, 214, 92) if p.restored else (120, 100, 160)
            pygame.draw.rect(self.screen, color, (x, y - 8, config.TILE, config.TILE + 8))
            if p.restored and p.shield_radius > 1:
                r = int(p.shield_radius * config.TILE)
                pygame.draw.circle(
                    self.screen, (140, 200, 255), (x + 12, y + 12), r, 2
                )

    def draw_shadow(self, shadow, player):
        if not shadow.active:
            return
        x, y = self.world_to_screen(int(shadow.col), player.row, player.col, player.row)
        surf = pygame.Surface((config.TILE * 2, config.SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(surf, (20, 10, 30, 160), (0, 0, config.TILE * 2, config.SCREEN_H))
        self.screen.blit(surf, (x - config.TILE, 0))

    def draw_hud(self, hotbar, shield, harmony, ga, message):
        bar = pygame.Rect(20, config.SCREEN_H - 70, 9 * 52, 56)
        pygame.draw.rect(self.screen, config.PALETTE["panel"], bar)
        for i, (kind, value, count) in enumerate(hotbar.slots):
            rect = pygame.Rect(24 + i * 52, config.SCREEN_H - 66, 48, 48)
            color = (255, 214, 92) if i == hotbar.selected else (60, 66, 90)
            pygame.draw.rect(self.screen, color, rect, 2 if i != hotbar.selected else 0)
            if i != hotbar.selected:
                pygame.draw.rect(self.screen, (40, 46, 66), rect)
                pygame.draw.rect(self.screen, color, rect, 2)
            if kind == "wand":
                pygame.draw.line(self.screen, (150, 220, 255), rect.center, (rect.center[0] + 14, rect.center[1] - 14), 3)
            elif kind == "block":
                pygame.draw.rect(self.screen, BLOCK_COLORS.get(value, (120, 120, 120)), rect.inflate(-16, -16))
            label = str(i + 1)
            num = self.small.render(label, True, config.PALETTE["text"])
            self.screen.blit(num, (rect.x + 2, rect.y + 2))
            if kind in ("block", "catalyst") and count:
                cnt = self.small.render(str(count), True, config.PALETTE["text"])
                self.screen.blit(cnt, (rect.right - 16, rect.bottom - 16))
        pygame.draw.rect(
            self.screen,
            config.PALETTE["harmony"],
            (20, 14, min(300, int(300 * shield)), 10),
        )
        text = self.font.render(
            f"Harmony {harmony:.0f} | GA gen {ga.generation}", True, config.PALETTE["text"]
        )
        self.screen.blit(text, (20, 30))
        if message:
            msg = self.font.render(message, True, config.PALETTE["accent"])
            self.screen.blit(msg, (config.SCREEN_W // 2 - 150, 60))

    def draw_puzzle(self, pylon):
        panel = pygame.Rect(
            config.SCREEN_W // 2 - 220, 160, 440, 40 + 52 * len(pylon.rune_set)
        )
        pygame.draw.rect(self.screen, config.PALETTE["panel"], panel)
        title = self.font.render("Align the runes", True, config.PALETTE["text"])
        self.screen.blit(title, (panel.x + 16, panel.y + 10))
        for i, rune in enumerate(pylon.rune_set):
            rect = pygame.Rect(panel.x + 20, panel.y + 46 + i * 52, 400, 44)
            pygame.draw.rect(self.screen, (50, 56, 80), rect)
            label = self.small.render(rune, True, config.PALETTE["text"])
            self.screen.blit(label, (rect.x + 12, rect.y + 12))
            state = ""
            if pylon.progress > i and not pylon.restored:
                state = "lit"
            elif pylon.restored:
                state = "lit"
            if state == "lit":
                pygame.draw.rect(self.screen, (255, 214, 92), rect, 2)
