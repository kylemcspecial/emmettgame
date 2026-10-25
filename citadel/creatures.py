"""Non-violent mythical creatures, charm sequences, and befriending.

Per spec section 1.3: creatures are never fought. The player charms
them with a wand spell sequence; befriended creatures move near the
castle and act as guardians.
"""
from . import config, world as W


class Creature:
    def __init__(self, name, species, col, row, charm_seq, color, favorite):
        self.name = name
        self.species = species
        self.col = col
        self.row = row
        self.charm_seq = list(charm_seq)
        self.charm_idx = 0
        self.color = color
        self.favorite = favorite
        self.befriended = False
        self.wander_t = 0.0
        self.wander_dir = 1
        self.home_col = None

    def advance_charm(self):
        if self.charm_idx < len(self.charm_seq):
            self.charm_idx += 1
            return self.charm_idx >= len(self.charm_seq)
        return False

    def charm_symbols(self):
        return list(self.charm_seq)

    def update(self, world, dt):
        if self.befriended and self.home_col is not None:
            if self.col < self.home_col:
                self.col += 1
            elif self.col > self.home_col:
                self.col = max(0, self.col - 1)
            self.row = max(0, world.surface_row(self.col) - 1)
            return
        self.wander_t += dt
        if self.wander_t > 1.6:
            self.wander_t = 0.0
            self.wander_dir = -self.wander_dir
        step = 1 if self.wander_dir > 0 else -1
        target = self.col + step
        if world.in_bounds(self.row, target) and world.get(self.row, target) == 0:
            self.col = target
        else:
            self.wander_dir = -self.wander_dir
        self.row = max(0, world.surface_row(self.col) - 1)


SPECIES = [
    ("Glimmermoth", (200, 160, 255)),
    ("Pebblepuff", (255, 170, 120)),
    ("Lumifawn", (170, 230, 180)),
    ("Sparklewisp", (255, 230, 130)),
    ("Mossgale", (140, 210, 230)),
]


class CreatureManager:
    def __init__(self, rng, world, ga):
        self.rng = rng
        self.creatures = []
        for i in range(6):
            col = int(rng.integers(8, config.WORLD_COLS - 8))
            species, color = SPECIES[i % len(SPECIES)]
            seq_len = ga.genes["charm_len"]
            seq = [
                "L" if rng.random() < 0.5 else "R"
                for _ in range(seq_len)
            ]
            name = species + " " + str(i + 1)
            c = Creature(
                name, species, col, max(0, world.surface_row(col) - 1),
                seq, ga.mutate_color(color), "crystal",
            )
            self.creatures.append(c)

    def nearest_unbefriended(self, player, max_dist=config.WAND_RANGE):
        best, best_d = None, 10**9
        for c in self.creatures:
            if c.befriended:
                continue
            d = abs(c.col - player.col) + abs(c.row - player.row)
            if d < best_d:
                best, best_d = c, d
        return best if best_d <= max_dist else None

    def befriend(self, creature, castle_col):
        creature.befriended = True
        creature.home_col = castle_col + self.rng.integers(-3, 4)
        return creature

    def update(self, world, dt):
        for c in self.creatures:
            c.update(world, dt)
