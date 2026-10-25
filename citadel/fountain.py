"""Blessing Fountain at the castle site: turn surplus resources into
castle building blocks. Gives mined stone/quartz/crystal a purpose and
teaches gentle resource planning without a crafting-grid UI.

Right-click the fountain while holding any tradeable item; the fountain
'blesses' it into castle stone or castle quartz (better rate for
starlight/crystal).
"""
from . import config

RECIPES = {
    "stone":        ("castle_stone", 4),   # 4 stone -> 1 castle stone
    "dirt":         ("castle_stone", 6),
    "wood":         ("castle_quartz", 6),
    "quartz":       ("castle_quartz", 4),
    "crystal":      ("castle_quartz", 3),
    "starlight":    ("castle_quartz", 2),
}


class Fountain:
    def __init__(self, castle):
        self.col = castle.col - 2
        self.x = (self.col + 0.5) * config.TILE

    def world_pos(self, world):
        """Current world position: follows the terrain under it."""
        row = world.surface_row(self.col)
        self.y = (row - 1) * config.TILE + config.TILE / 2
        return self.x, self.y

    def in_range(self, x, y, world=None, dist=None):
        """True only when the click is near the fountain's spout."""
        if y is None:
            return False
        if world is not None:
            fx, fy = self.world_pos(world)
        else:
            fy = getattr(self, "y", None)
            if fy is None:
                return False
            fx = self.x
        dist = dist or config.TILE * 2
        return (((fx - x) ** 2 + (fy - y) ** 2) ** 0.5 <= dist)

    def recipe_for(self, item):
        return RECIPES.get(item)

    def amount_needed(self, item):
        r = RECIPES.get(item)
        return r[1] if r else None

    def bless(self, item, inventory):
        """Consume amount_needed(item); return the blessed item or None."""
        r = RECIPES.get(item)
        if not r:
            return None
        out, need = r
        if inventory.count(item) >= need and inventory.consume(item, need):
            return out
        return None
