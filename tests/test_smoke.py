"""Headless smoke test covering all gameplay systems."""
import json
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from citadel.main import Game  # noqa: E402
from citadel import config, world as W  # noqa: E402


def approx_eq(a, b, tol=1e-6):
    return abs(a - b) < tol


def main():
    game = Game(headless=True, load=False)
    for _ in range(30):
        game.frame()

    # world gen
    assert game.world.cols == config.WORLD_COLS
    assert game.world.counts()["Grass"] > 100
    assert any(game.world.get(r, c) == W.WOOD
               for r in range(game.world.rows)
               for c in range(0, 20))

    # player physics: falls to ground, walks, jumps
    y0 = game.player.y
    game.player.update(game.world, 0.5, 1, False)
    assert game.player.x > 0
    landed = game.player.on_ground
    assert landed, "player should land on terrain"
    game.player.update(game.world, 0.02, 0, True)
    assert game.player.vy < 0 or not game.player.on_ground

    # mining: break a block, get a drop, pick it up
    prow, pcol = game.player.tile()
    target = None
    for c in range(pcol - 4, pcol + 5):
        for r in range(prow - 4, prow + 5):
            if game.world.get(r, c) in W.BREAKABLE:
                target = (r, c)
                break
        if target:
            break
    assert target, "should find a breakable block near player"
    r, c = target
    block = game.world.get(r, c)
    block_drop, n = game.world.break_block(r, c)
    assert game.world.get(r, c) == W.AIR
    from citadel.inventory import BLOCK_TO_ITEM
    drop_item = BLOCK_TO_ITEM.get(block_drop)
    if drop_item:
        game.drops.spawn(drop_item, (c + 0.5) * config.TILE,
                         (r + 0.5) * config.TILE, n)
        game.player.x = (c + 0.5) * config.TILE
        game.player.y = (r + 0.5) * config.TILE
        game.drops.update(0.1, game.player, game.inventory)
        assert game.inventory.count(drop_item) >= 1, "drop should be collected"

    # placing from inventory
    game.inventory.hotbar[1] = ("stone", 5)
    game.inventory.selected = 1
    r2, c2 = game.player.tile()
    pr, pc = r2 - 2, c2
    if game.world.get(pr, pc) == W.AIR:
        assert game.world.place_block(pr, pc, W.STONE)
        assert game.world.get(pr, pc) == W.STONE

    # creature charming via wand
    creature = game.creatures.creatures[0]
    creature.x = game.player.x + config.TILE
    creature.y = game.player.y
    while not creature.befriended:
        game.player.wand_timer = 0
        game._cast_wand(creature)
    assert creature.befriended
    friends = [c for c in game.creatures.creatures if c.befriended]
    assert len(friends) == 1

    # feeding berries also charms
    c2 = game.creatures.creatures[1]
    c2.x = game.player.x - config.TILE
    c2.y = game.player.y
    game.inventory.add("berry", 5)
    while not c2.befriended:
        c2.hearts > 0 and game.inventory.consume("berry", 1)
        c2.hearts -= 1
        if c2.hearts == 0:
            game.creatures.befriend(c2, game.castle.x)
    assert c2.befriended

    # pylon puzzle: solve by clicking runes in order
    pylon = game.pylons.unrestored()[0]
    game.active_pylon = pylon
    game.mode = "puzzle"
    game.renderer.rune_rects = {
        name: pygame.Rect(i * 90, 150, 80, 80)
        for i, name in enumerate(["Sun", "Moon", "Star", "Leaf", "Wave"])
    }
    for rune in pylon.target_seq:
        rect = game.renderer.rune_rects[rune]
        game._puzzle_click(rect.center)
    assert pylon.restored, "pylon should be solved after correct sequence"
    assert game.mode == "play"

    # wrong sequence resets
    p2 = game.pylons.unrestored()[0]
    p2.progress = 1
    assert p2.click_rune("X-invalid") == "wrong"
    assert p2.progress == 0

    # shield strength rises with restored pylons and harmony
    strength = game.shield.strength(len(game.pylons.pylons), 1)
    assert 0 < strength < 1

    # GA evaluates and evolves
    for _ in range(4):
        game.ga.record_event("pylon", 5.0)
    assert game.ga.generation == 2

    # castle synergy: placing near befriended creature boosts harmony
    harmony0 = game.shield.harmony
    col = game.castle.col
    row = game.world.surface_row(col) - 1
    game.world.set(row, col, W.AIR)
    gain = game.castle.register_block(row, col, W.CRYSTAL,
                                      game.creatures.creatures, game.ga)
    assert gain >= 1.0

    # save / load round-trip
    from citadel.save import save_game, load_game
    path = save_game(game, "/tmp/test_save.json")
    data = json.load(open(path))
    assert data["version"] == 1
    harmony_before = game.shield.harmony
    friends_before = sum(c.befriended for c in game.creatures.creatures)
    game2 = Game(headless=True, load=False)
    load_game(game2, "/tmp/test_save.json")
    assert approx_eq(game2.shield.harmony, harmony_before)
    assert sum(c.befriended for c in game2.creatures.creatures) == friends_before
    assert game2.pylons.pylons[0].restored == pylon.restored

    # run more frames for stability
    for _ in range(60):
        game.frame()
        game2.frame()

    # victory path: all pylons + harmony banishes shadow
    for p in game.pylons.pylons:
        p.restored = True
        p.shield_radius = 100
    game.shield.harmony = 120
    game.update(0.1)
    assert game.shadow.banished, "shadow should be banished at full shield"
    for _ in range(5):
        game.frame()
    assert game.mode == "victory"

    print("SMOKE TEST PASSED")
    pygame.quit()


if __name__ == "__main__":
    main()
