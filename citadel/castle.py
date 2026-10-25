"""Castle building: Harmony Rating with GA synergy bonuses (spec 2.2, 3.1)."""
from . import config
from .inventory import BLOCK_TO_ITEM


class Castle:
    def __init__(self, col):
        self.col = int(col)
        self.x = (col + 0.5) * config.TILE
        self.blocks = {}
        self.rating = 0.0

    def within_site(self, col):
        return abs(col - self.col) <= 14

    def register_block(self, row, col, block, creatures, ga):
        item = BLOCK_TO_ITEM.get(block)
        if item is None or not self.within_site(col):
            return 0.0
        self.blocks[(row, col)] = block
        gain = 1.0
        for c in creatures:
            if abs(c.x - (col + 0.5) * config.TILE) <= config.TILE * 4:
                gain += ga.synergy_bonus(item, c.species) * 0.5
        self.rating += gain
        return gain

    def guardians(self, creatures):
        return [
            c for c in creatures
            if c.befriended and abs(c.x - self.x) <= config.TILE * 10
        ]
