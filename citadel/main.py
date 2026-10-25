"""Main game loop: Citadel of Friendship & Magic."""
import os
import sys

import numpy as np
import pygame

from . import config
from .castle import Castle
from .creatures import CreatureManager
from .genetics import GeneticTuner
from .inventory import Hotbar
from .player import Player
from .pylons import PylonManager
from .renderer import Renderer
from .shadow import FriendshipShield, Shadow
from . import world as W


class Game:
    def __init__(self, headless=False):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy" if headless else "x11")
        pygame.init()
        self.headless = headless
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption("Citadel of Friendship & Magic")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 22)
        self.rng = np.random.default_rng(config.RNG_SEED)
        self.world = W.World(self.rng)
        self.ga = GeneticTuner(self.rng)
        self.hotbar = Hotbar()
        self.player = Player(self.world, col=8)
        self.creatures = CreatureManager(self.rng, self.world, self.ga)
        self.pylons = PylonManager(self.rng, self.world, self.ga)
        self.castle = Castle(col=config.WORLD_COLS // 2)
        self.shadow = Shadow(col=2.0)
        self.shield = FriendshipShield()
        self.renderer = Renderer(self.screen, self.font, self.small)
        self.active_pylon = None
        self.message = ""
        self.message_t = 0.0
        self.pylon_timer = 0.0
        self.running = True

    def notify(self, text, duration=3.0):
        self.message = text
        self.message_t = duration

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                self.hotbar.select(event.key - pygame.K_0)
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.player.try_move(self.world, -1)
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.player.try_move(self.world, 1)
            elif event.key == pygame.K_e:
                self.notify("Friendship Ledger: " + ", ".join(
                    c.name for c in self.creatures.creatures if c.befriended
                ) or "No friends yet - go charm a creature!")
        elif event.type == pygame.MOUSEWHEEL:
            self.hotbar.cycle(1 if event.y > 0 else -1)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.active_pylon and not self.active_pylon.restored:
                return
            if event.button == 1:
                self.cast_wand()
            elif event.button == 3:
                self.use_block()

    def screen_to_world(self, pos):
        x, y = pos
        col = (x - config.SCREEN_W // 2) // config.TILE + self.player.col
        row = (y - config.SCREEN_H // 2) // config.TILE + self.player.row
        return int(row), int(col)

    def cast_wand(self):
        if self.player.wand_timer > 0:
            return
        self.player.wand_timer = config.WAND_COOLDOWN
        if self.hotbar.current_block() is not None and self.hotbar.kind_of(self.hotbar.selected) == "wand":
            return
        creature = self.creatures.nearest_unbefriended(self.player)
        if creature is not None:
            result = creature.advance_charm()
            self.notify(f"{creature.name}: charm {creature.charm_idx}/{len(creature.charm_seq)}")
            if result:
                self.creatures.befriend(creature, self.castle.col)
                self.hotbar.set_charm(creature.species)
                self.shield.add_harmony(12, self.ga)
                self.ga.record_event("charm", config.CHARM_TIME)
                self.notify(f"{creature.name} befriended! A guardian joins your citadel.")
            return
        pylon = self.pylons.nearest_unrestored(self.player)
        if pylon is not None:
            self.active_pylon = pylon
            self.notify("Puzzle: click the runes in the lit order!")
            return
        row, col = self.screen_to_world(pygame.mouse.get_pos())
        if 0 <= abs(col - self.player.col) <= config.WAND_RANGE:
            block = self.world.get(row, col)
            if block == W.THORNS:
                self.world.set(row, col, W.AIR)
                self.notify("Dark thorns cleared by wand light.")
                self.shield.add_harmony(2, self.ga)

    def use_block(self):
        row, col = self.screen_to_world(pygame.mouse.get_pos())
        if abs(col - self.player.col) > config.WAND_RANGE:
            return
        kind = self.hotbar.kind_of(self.hotbar.selected)
        if kind == "block":
            block = self.hotbar.consume_current()
            if block is not None and self.world.place_block(row, col, block):
                gain = self.castle.register_block(row, col, block, self.creatures.creatures, self.ga)
                if gain:
                    self.shield.add_harmony(gain, self.ga)
                    self.notify(f"Castle harmony +{gain:.1f}")
        elif kind == "catalyst":
            if self.hotbar.use_catalyst():
                self.shield.add_harmony(10, self.ga)
                self.notify("Shield catalyst released warmth into the land.")

    def update(self, dt):
        self.player.update(self.world, dt, 0)
        self.creatures.update(self.world, dt)
        self.pylons.update(dt)
        strength = self.shield.strength(len(self.pylons.pylons), sum(
            1 for p in self.pylons.pylons if p.restored))
        drain = self.shadow.update(dt, strength, self.player.col, self.ga)
        if drain:
            self.shield.drain(drain)
        if self.message_t > 0:
            self.message_t -= dt
            if self.message_t <= 0:
                self.message = ""

    def draw(self):
        self.renderer.draw_world(self.world, self.player)
        self.renderer.draw_pylons(self.pylons.pylons, self.player)
        self.renderer.draw_creatures(self.creatures.creatures, self.player)
        self.renderer.draw_shadow(self.shadow, self.player)
        self.renderer.draw_player(self.player)
        self.renderer.draw_hud(
            self.hotbar,
            self.shield.strength(len(self.pylons.pylons), sum(
                1 for p in self.pylons.pylons if p.restored)),
            self.shield.harmony,
            self.ga,
            self.message if self.message_t > 0 else "",
        )
        if self.active_pylon and not self.active_pylon.restored:
            self.renderer.draw_puzzle(self.active_pylon)
        pygame.display.flip()

    def frame(self):
        dt = self.clock.tick(config.FPS) / 1000.0
        for event in pygame.event.get():
            self.handle_event(event)
        self.update(dt)
        self.draw()
        return self.running

    def run(self, max_frames=None):
        frames = 0
        while self.running:
            self.frame()
            frames += 1
            if max_frames and frames >= max_frames:
                break
        pygame.quit()


def main():
    headless = "--headless" in sys.argv or not os.environ.get("DISPLAY")
    game = Game(headless=headless)
    game.run()


if __name__ == "__main__":
    main()
