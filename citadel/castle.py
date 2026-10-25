"""Castle building and Harmony Rating (spec section 2.2, 3.1).

Harmony rises from placing castle-worthy blocks near the chosen castle
site, boosted by genetic synergy rules when the right block types sit
near the right befriended creatures.
"""
from . import world as W


class Castle:
    def __init__(self, col):
        self.col = int(col)
        self.blocks = {}
        self.rating = 0.0

    def register_block(self, row, col, block, creatures, ga):
        if block not in (W.CASTLE_STONE, W.QUARTZ, W.CRYSTAL, W.STARLIGHT, W.WOOD):
            return 0.0
        if abs(col - self.col) > 12:
            return 0.0
        self.blocks[(row, col)] = block
        gain = 1.0
        names = {
            W.CASTLE_STONE: "castle_stone",
            W.QUARTZ: "quartz",
            W.CRYSTAL: "crystal",
            W.STARLIGHT: "starlight",
            W.WOOD: "ancient_oak",
        }
        for c in creatures:
            if c.befriended and abs(c.col - col) <= 4:
                gain += ga.synergy_bonus(names[block], c.species) * 0.5
        self.rating += gain
        return gain

    def guardians(self, creatures):
        return [c for c in creatures if c.befriended and abs(c.col - self.col) <= 8]
