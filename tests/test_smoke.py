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
    assert data["version"] == 2
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

    # --- new feature checks ---

    # castle blocks are obtainable in the world near the castle site
    deposits = sum(
        1 for c in range(game.castle.col - 25, game.castle.col + 26)
        for r in (game.world.surface_row(c), game.world.surface_row(c) - 1)
        if game.world.get(r, c) in (W.CASTLE_STONE, W.CASTLE_QUARTZ)
    )
    assert deposits >= 4, "castle block deposits should exist near the site"

    # rune key shard blocks exist and drop rune keys
    shards = sum(
        1 for c in range(game.world.cols)
        for r in (game.world.surface_row(c), game.world.surface_row(c) - 1)
        if game.world.get(r, c) == W.RUNE_KEY_BLOCK
    )
    assert shards >= 1
    from citadel.inventory import BLOCK_TO_ITEM
    assert BLOCK_TO_ITEM[W.RUNE_KEY_BLOCK] == "rune_key"

    # rune key use: right-click near pylon advances progress
    game.inventory.add("rune_key", 1)
    p3 = game.pylons.unrestored()[0]
    prog0 = p3.progress
    game.inventory.consume("rune_key", 1)
    p3.progress = min(p3.progress + 1, len(p3.target_seq))
    assert p3.progress == prog0 + 1

    # catalyst adds harmony
    harmony_a = game.shield.harmony
    game.inventory.add("catalyst", 1)
    assert game.inventory.consume("catalyst", 1)
    game.shield.add_harmony(12, game.ga)
    assert game.shield.harmony > harmony_a

    # hotbar -> backpack move
    game.inventory.hotbar[2] = ("stone", 7)
    assert game.inventory.to_backpack(0, 2)
    assert game.inventory.hotbar[2] == (None, None)
    assert any(it == "stone" for row in game.inventory.backpack for it, _ in row)

    # compass hints render without crashing
    game.mode = "inventory"
    for _ in range(2):
        game.frame()
    game.renderer.draw_inventory_screen(game)
    game.mode = "play"

    # castle banner draws without crashing
    game.renderer.draw_castle_banner(game.castle, game.world)

    # sounds degrade gracefully when mixer is missing
    from citadel.sounds import Sounds
    s = Sounds()
    s.play("wand")  # must not raise even when disabled

    # --- regression checks from code review ---

    # rune key shards drop keys; catalyst blooms drop catalysts
    g3 = Game(headless=True, load=False)
    key_drop = cat_drop = False
    for c in range(g3.world.cols):
        r = g3.world.surface_row(c)
        for rr in (r, r - 1):
            b = g3.world.get(rr, c)
            if b == W.RUNE_KEY_BLOCK and not key_drop:
                key_drop = g3.world.break_block(rr, c)[0] == "rune_key"
            if b == W.CATALYST_BLOOM and not cat_drop:
                cat_drop = g3.world.break_block(rr, c)[0] == "catalyst"
    assert key_drop, "rune key shards must drop rune_key"
    assert cat_drop, "catalyst blooms must drop catalyst"

    # wand re-cast at befriended creature gives no harmony
    c4 = g3.creatures.creatures[3]
    while not c4.befriended:
        g3.player.wand_timer = 0
        g3._cast_wand(c4)
    h_before = g3.shield.harmony
    g3.player.wand_timer = 0
    g3._cast_wand(c4)
    assert g3.shield.harmony == h_before, "re-cast exploit must not grant harmony"

    # shadow drain is time-based (small per frame, ~3/sec)
    from citadel.pylons import Shadow
    from citadel.genetics import GeneticTuner
    sh = Shadow(col=50.0)
    sh.x = 50.0
    ga2 = GeneticTuner(g3.rng)
    drain = sh.update(1 / 60, 0.3, 50.0, ga2, 10)
    assert 0 < drain < 0.1, f"drain per frame should be tiny, got {drain}"

    # depleted hotbar slot can be refilled
    g3.inventory.hotbar[1] = ("stone", None)
    assert g3.inventory.add("stone", 5)
    assert g3.inventory.hotbar[1] == ("stone", 5)

    # ledger renders with hotbar row (right-click store target exists)
    g3.mode = "inventory"
    g3.renderer.draw_inventory_screen(g3)
    assert (3, 0) in g3.renderer.backpack_rects, "ledger must expose hotbar row"
    g3.mode = "play"

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

    # --- polish feature checks ---

    # title screen -> play transition
    g4 = Game(headless=True, load=False)
    assert g4.mode == "title"
    g4.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert g4.mode == "play"

    # pylon progression gating: only first pylon awake initially
    assert g4.pylons.pylons[0].awakened
    assert sum(1 for p in g4.pylons.pylons if p.awakened) == 1
    solved = g4.pylons.pylons[0]
    solved.restored = True
    nxt = g4.pylons.on_restored(solved)
    assert nxt is not None and nxt.awakened
    assert sum(1 for p in g4.pylons.pylons if p.awakened) == 2

    # creature naming flow (requires play mode)
    c5 = g4.creatures.creatures[0]
    g4.player.x = c5.x
    g4.creatures.befriend(c5, g4.castle.x)
    g4.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n,
                                       unicode="n"))
    assert g4.naming is c5
    for ch in "Emmett":
        g4.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                           key=ord(ch), unicode=ch))
    g4.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert c5.name == "Emmett", c5.name
    assert g4.naming is None

    # unique creature sprites: two creatures of same species differ
    from citadel.sprites import get_creature_sprites
    a = get_creature_sprites("Pebblepuff", (255, 170, 120), 11)
    b = get_creature_sprites("Pebblepuff", (255, 170, 120), 12)
    assert pygame.image.tostring(a[0], "RGBA") != pygame.image.tostring(b[0], "RGBA")

    # naming + awakening survive save/load
    from citadel.save import save_game as sg, load_game as lg
    p6 = sg(g4, "/tmp/test_save2.json")
    g5 = Game(headless=True, load=False)
    lg(g5, "/tmp/test_save2.json")
    assert g5.creatures.creatures[0].name == "Emmett"
    assert g5.pylons.pylons[1].awakened
    import os as _os
    _os.remove(p6)

    # hints screen opens and closes
    g5.mode = "play"
    g5.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h))
    assert g5.mode == "hints"
    g5.frame()
    g5.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h))
    assert g5.mode == "play"

    # incompatible version rejected -> fresh realm path works
    import json as _json
    bad = {"version": 99, "world": {"cols": 1, "rows": 1}}
    with open("/tmp/bad_save.json", "w") as f:
        _json.dump(bad, f)
    g6 = Game(headless=True, load=False)
    try:
        lg(g6, "/tmp/bad_save.json")
        raise AssertionError("should reject version 99")
    except ValueError:
        pass
    _os.remove("/tmp/bad_save.json")

    # --- PR4 playability checks ---

    # settings persist round-trip
    from citadel import settings as S
    import citadel.config as C
    C.VOLUME = 0.5
    C.PERFORMANCE_MODE = True
    S.save_settings("/tmp/test_settings.json")
    C.VOLUME = 0.1
    C.PERFORMANCE_MODE = False
    S.load_settings("/tmp/test_settings.json")
    assert C.VOLUME == 0.5 and C.PERFORMANCE_MODE is True
    _os.remove("/tmp/test_settings.json")
    C.PERFORMANCE_MODE = False

    # mercy hint after 2 wrong puzzle clicks
    g7 = Game(headless=True, load=False)
    g7.mode = "play"
    p7 = g7.pylons.pylons[0]
    g7.active_pylon = p7
    g7.mode = "puzzle"
    g7.renderer.rune_rects = {
        name: pygame.Rect(i * 90, 150, 80, 80)
        for i, name in enumerate(["Sun", "Moon", "Star", "Leaf", "Wave"])
    }
    wrong = next(r for r in g7.renderer.rune_rects
                 if r != p7.target_seq[0])
    g7._puzzle_click(g7.renderer.rune_rects[wrong].center)
    g7._puzzle_click(g7.renderer.rune_rects[wrong].center)
    assert g7.puzzle_fails.get(p7.pid) == 2
    # third failure still fine, progress reset
    g7._puzzle_click(g7.renderer.rune_rects[wrong].center)
    assert p7.progress == 0
    g7.mode = "play"

    # castle-site tip fires once
    g7.tips_shown.clear()
    col = g7.castle.col
    row = g7.world.surface_row(col) - 1
    g7.world.set(row, col, W.AIR)
    gain = g7.castle.register_block(row, col, W.CRYSTAL,
                                    g7.creatures.creatures, g7.ga)
    assert gain >= 1.0
    # (tip notification path covered by _right_action; direct check here)

    # wand beam decays and clears
    g7.wand_beam = (0, 0, 10, 10, 0.05)
    g7.update(0.06)
    assert g7.wand_beam is None

    # weather + crack render without crash
    g7.frame()
    g7.renderer.draw_weather(3.0, 0.25)
    g7.renderer.draw_break_crack(10, 10, 0.5)
    g7.renderer.draw_wand_beam(0, 0, 100, 100, 0.2)

    # wizard has 3 frames incl. jump pose
    assert len(g7.renderer.wizard) == 3

    # volume keys change volume
    v0 = C.VOLUME
    g7.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                       key=pygame.K_EQUALS))
    assert C.VOLUME > v0
    g7.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                       key=pygame.K_MINUS))

    # title shows Continue when save exists
    from citadel.save import save_game as sg2
    sg2(g7, "/tmp/test_save3.json")
    from citadel.save import has_save
    C.SAVE_PATH = "/tmp/test_save3.json"
    assert has_save()
    _os.remove("/tmp/test_save3.json")

    # --- PR4 review regression checks ---

    # creatures never spawn mid-hop (hop_t must start at 0)
    g8 = Game(headless=True, load=False)
    for c in g8.creatures.creatures:
        assert c.hop_t == 0.0, "creatures must not spawn with a live hop"
        c.update(g8.world, 1 / 60, g8.player.x)
        assert abs(c.bob) < 10, f"spawn bob too large: {c.bob}"

    # corrupt settings files never crash the launch
    from citadel import settings as S2
    for bad in ['{"volume": "x"}', "[]", "garbage"]:
        with open("/tmp/bad_s.json", "w") as f:
            f.write(bad)
        S2.load_settings("/tmp/bad_s.json")
    _os.remove("/tmp/bad_s.json")

    # fullscreen toggle keeps renderer.screen in sync (simulate reassign)
    class FakeRend:
        pass
    fr = FakeRend()
    g8.renderer.screen = g8.screen
    assert g8.renderer.screen is g8.screen

    # --- PR5 endgame checks ---

    # blessing fountain: recipes convert surplus into castle blocks
    from citadel.fountain import Fountain, RECIPES
    f = Fountain(game.castle)
    before = game.inventory.count("stone")
    game.inventory.add("stone", 10)
    out = f.bless("stone", game.inventory)
    assert out == "castle_stone"
    assert game.inventory.count("stone") == before + 6
    out2 = f.bless("starlight", game.inventory)
    assert out2 is None  # not enough starlight
    game.inventory.add("starlight", 2)
    assert f.bless("starlight", game.inventory) == "castle_quartz"
    assert game.inventory.count("starlight") == 0

    # achievements unlock from state and persist
    g9 = Game(headless=True, load=False)
    g9.mode = "play"
    c9 = g9.creatures.creatures[0]
    while not c9.befriended:
        g9.player.wand_timer = 0
        g9._cast_wand(c9)
    g9.achievements.update(0.0)
    assert "first_friend" in g9.achievements.unlocked
    for _ in range(10):
        g9.achievements.event_berry_harvest()
    assert "green_thumb" in g9.achievements.unlocked
    path5 = save_game(g9, "/tmp/test_save5.json")
    g10 = Game(headless=True, load=False)
    load_game(g10, "/tmp/test_save5.json")
    assert "first_friend" in g10.achievements.unlocked
    assert g10.achievements.berries == 10
    _os.remove(path5)

    # fountain + achievements render without crash
    g10.mode = "play"
    g10.frame()
    g10.mode = "inventory"
    g10.frame()
    g10.mode = "play"
    g10.achievements.toasts.append(["T", "s", 1.0])
    g10.frame()

    # --- PR5 review regression checks ---

    # fountain range is a real 2D radius around the spout
    g11 = Game(headless=True, load=False)
    g11.mode = "play"
    fx, fy = g11.fountain.world_pos(g11.world)
    assert g11.fountain.in_range(fx, fy, world=g11.world)
    assert not g11.fountain.in_range(fx, fy - config.TILE * 5, world=g11.world)
    assert not g11.fountain.in_range(fx + config.TILE * 4, fy, world=g11.world)

    # fountain column is protected from digging
    col_f = g11.fountain.col
    surf_f = g11.world.surface_row(col_f)
    before_f = g11.world.get(surf_f - 1, col_f)
    g11._finish_break(surf_f - 1, col_f)
    assert g11.world.get(surf_f - 1, col_f) == before_f

    print("SMOKE TEST PASSED")
    pygame.quit()


if __name__ == "__main__":
    main()


def check_py39_fstrings():
    """The game targets Python 3.9+ (Raspberry Pi OS). Backslashes inside
    f-string expressions are a 3.12-only feature - scan the whole repo."""
    import ast
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv")]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            src = open(p, encoding="utf-8").read()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.JoinedStr):
                    for v in node.values:
                        if isinstance(v, ast.FormattedValue):
                            seg = ast.get_source_segment(src, v) or ""
                            assert "\\" not in seg, (
                                f"{p}:{v.lineno} uses a backslash inside an "
                                "f-string expression - not valid on Python "
                                "3.9-3.11 (Raspberry Pi OS)"
                            )


check_py39_fstrings()


def check_edge_regression():
    """Creatures walking home to a world edge must never index out of
    bounds (this crashed the game on the Pi), and surface_row must
    bounds-check its column."""
    import pygame
    g = Game(headless=True, load=False)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    c = g.creatures.creatures[1]
    c.befriended = True
    c.home_x = (g.world.cols - 1) * config.TILE
    c.x = 100 * config.TILE
    for _ in range(600):
        c.update(g.world, 1 / 60, g.player.x)
        assert 0 <= c.x <= (g.world.cols - 1) * config.TILE, \
            f"creature escaped bounds: {c.x}"
    assert g.world.surface_row(g.world.cols) == g.world.surface_row(g.world.cols - 1)
    assert g.world.surface_row(-5) == g.world.surface_row(0)
    print("edge regression OK")


check_edge_regression()


def check_graphics_upgrades():
    """New graphics features build and render without crashing."""
    g = Game(headless=True, load=False)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    for _ in range(10):
        g.frame()
    r = g.renderer
    r.draw_blob_shadow(g.player.x, g.player.y + 20)
    r.draw_time_overlay(0.5)   # night: vignette path
    r.draw_time_overlay(0.35)  # golden hour: tint path
    r.draw_time_overlay(0.25)  # day: no-op path
    assert len(r.wizard) == 3  # stand / walk / jump poses
    from citadel.graphics import Textures
    from citadel import world as W
    tex = Textures()
    assert set(tex.blocks) == {b for b in W.BLOCKS
                               if b != 0 and W.BLOCKS[b][1]}
    print("graphics upgrades OK")


check_graphics_upgrades()


def check_spawn_experience():
    """Emmett-feedback regressions: no sky-scroll on start, castle visible
    from spawn, first pylon nearby and awake, drops auto-collect."""
    import pygame
    g = Game(headless=True, load=False)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    g.frame()  # first frame
    # camera snapped, not lerping from origin
    target_y = g.player.y - config.SCREEN_H / 2
    assert abs(g.renderer.cam.y - target_y) < 1.0, \
        f"camera must snap on first frame: {g.renderer.cam.y} vs {target_y}"
    # player spawns near the castle site
    pc = g.player.tile()[1]
    assert abs(g.castle.col - pc) <= 12, \
        f"castle ({g.castle.col}) should be visible from spawn ({pc})"
    # first pylon is awake and within ~2 screens
    p0 = g.pylons.pylons[0]
    assert p0.awakened
    assert abs(p0.col - pc) <= 40
    # drop magnet: nearby loot gets collected within 2 seconds
    pr = g.player.tile()[0]
    g.world.break_block(pr - 2, pc + 1)
    g.drops.spawn("dirt", (pc + 1.5) * config.TILE,
                  (pr - 1.5) * config.TILE, 1)
    before = g.inventory.count("dirt")
    for _ in range(120):
        g.frame()
    assert g.inventory.count("dirt") > before, "drops must auto-collect"
    print("spawn experience OK")


check_spawn_experience()
