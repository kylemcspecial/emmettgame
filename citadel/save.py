"""Save/load game state as JSON next to the game (spec: save state)."""
import json
import os

from . import config


def save_game(game, path=None):
    path = path or config.SAVE_PATH
    data = {
        "version": 1,
        "player": {
            "x": game.player.x, "y": game.player.y,
            "facing": game.player.facing,
        },
        "world": {
            "cols": game.world.cols, "rows": game.world.rows,
            "grid": game.world.grid.tolist(),
            "regrow": game.world.regrow,
        },
        "inventory": {
            "hotbar": game.inventory.hotbar,
            "backpack": game.inventory.backpack,
            "selected": game.inventory.selected,
        },
        "creatures": [
            {
                "cid": c.cid, "species": c.species, "color": list(c.color),
                "x": c.x, "hearts": c.hearts, "max_hearts": c.max_hearts,
                "befriended": c.befriended, "home_x": getattr(c, "home_x", None),
            }
            for c in game.creatures.creatures
        ],
        "pylons": [
            {
                "pid": p.pid, "col": p.col, "row": p.row,
                "restored": p.restored, "progress": p.progress,
                "target_seq": p.target_seq, "shield_radius": p.shield_radius,
            }
            for p in game.pylons.pylons
        ],
        "castle": {
            "col": game.castle.col,
            "blocks": [[r, c, b] for (r, c), b in game.castle.blocks.items()],
            "rating": game.castle.rating,
        },
        "shield": {"harmony": game.shield.harmony},
        "shadow": {
            "x": game.shadow.x, "banished": game.shadow.banished,
        },
        "ga": game.ga.to_dict(),
        "drops": [
            {"item": d.item, "x": d.x, "y": d.y} for d in game.drops.drops
        ],
    }
    with open(path, "w") as f:
        json.dump(data, f)
    return path


def has_save(path=None):
    return os.path.exists(path or config.SAVE_PATH)


def load_game(game, path=None):
    path = path or config.SAVE_PATH
    if not os.path.exists(path):
        return False
    with open(path) as f:
        data = json.load(f)
    import numpy as np

    w = data["world"]
    game.world.grid = np.array(w["grid"], dtype=np.int16)
    game.world.regrow = [list(r) for r in w.get("regrow", [])]
    p = data["player"]
    game.player.x, game.player.y = p["x"], p["y"]
    game.player.facing = p.get("facing", 1)
    inv = data["inventory"]
    game.inventory.hotbar = [tuple(x) for x in inv["hotbar"]]
    game.inventory.backpack = [[tuple(x) for x in row] for row in inv["backpack"]]
    game.inventory.selected = inv.get("selected", 0)
    for saved, live in zip(data["creatures"], game.creatures.creatures):
        live.x = saved["x"]
        live.color = tuple(saved["color"])
        live.hearts = saved["hearts"]
        live.befriended = saved["befriended"]
        if saved.get("home_x"):
            live.home_x = saved["home_x"]
    for saved, live in zip(data["pylons"], game.pylons.pylons):
        live.restored = saved["restored"]
        live.progress = saved["progress"]
        live.target_seq = saved["target_seq"]
        live.shield_radius = saved["shield_radius"]
    cast = data["castle"]
    game.castle.blocks = {(r, c): b for r, c, b in cast["blocks"]}
    game.castle.rating = cast["rating"]
    game.shield.harmony = data["shield"]["harmony"]
    game.shadow.x = data["shadow"]["x"]
    game.shadow.banished = data["shadow"]["banished"]
    game.ga.load_dict(data["ga"])
    from .inventory import DropManager, Drop
    game.drops = DropManager(game.rng)
    for d in data.get("drops", []):
        game.drops.drops.append(Drop(d["item"], d["x"], d["y"], game.rng))
    return True
