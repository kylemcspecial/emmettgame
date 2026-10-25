"""Headless smoke test: runs the game loop and simulates core actions."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from citadel.main import Game  # noqa: E402
from citadel import world as W  # noqa: E402


def main():
    game = Game(headless=True)
    for _ in range(120):
        if not game.frame():
            break
    assert game.world is not None
    assert len(game.pylons.pylons) == 4
    assert len(game.creatures.creatures) == 6

    hotbar = game.hotbar
    hotbar.select(2)
    assert hotbar.current_block() == W.STONE

    row = game.world.surface_row(game.player.col) - 3
    col = game.player.col + 1
    assert game.world.place_block(row, col, W.STONE)
    assert game.world.get(row, col) == W.STONE
    assert game.world.break_block(row, col) == W.STONE

    creature = game.creatures.creatures[0]
    creature.col = game.player.col + 2
    creature.row = game.player.row
    for _ in range(len(creature.charm_seq)):
        creature.advance_charm()
    assert creature.befriended is False
    game.creatures.befriend(creature, game.castle.col)
    assert creature.befriended
    assert "Charm" in game.hotbar.slots[7][1]

    pylon = game.pylons.pylons[0]
    for rune in pylon.target_seq:
        pylon.click_rune(rune, game.rng)
    assert pylon.restored

    strength = game.shield.strength(4, 1)
    assert 0 < strength < 1

    for _ in range(60):
        game.frame()
    print("SMOKE TEST PASSED")
    pygame.quit()


if __name__ == "__main__":
    main()
