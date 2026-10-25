"""Friendly creatures: wander, approach when fed, charm sequences."""
import numpy as np

from . import config

SPECIES = [
    ("Glimmermoth", (190, 150, 255)),
    ("Pebblepuff", (255, 170, 120)),
    ("Lumifawn", (170, 230, 180)),
    ("Sparklewisp", (255, 230, 130)),
    ("Mossgale", (140, 210, 230)),
    ("Bumblebrook", (200, 240, 150)),
]


class Creature:
    def __init__(self, cid, species, color, col, row, hearts, favorite, seed):
        self.cid = cid
        self.species = species
        self.color = color
        self.col = float(col)
        self.row = int(row)
        self.x = (col + 0.5) * config.TILE
        self.y = (row + 0.5) * config.TILE
        self.hearts = hearts            # wand casts needed to befriend
        self.max_hearts = hearts
        self.favorite = favorite        # item id it loves to be fed
        self.befriended = False
        self.fed_this_round = False
        self.wander_t = 0.0
        self.dir = 1
        self.hop_t = float(np.random.uniform(0, 3))
        self.bob = 0.0
        self.bob_t = float(np.random.uniform(0, 6.28))
        self.seed = seed
        self.name = None               # kid-assigned name (Friendship Album)
        self.home_x = None             # set on befriending; castle-side home

    def advance_charm(self):
        if self.hearts > 0:
            self.hearts -= 1
        return self.hearts <= 0

    def charm_display(self):
        return self.hearts, self.max_hearts

    def update(self, world, dt, player_x):
        self.bob_t += dt * 2.5
        self.bob = np.sin(self.bob_t) * 3
        if self.befriended:
            target_x = self.home_x if self.home_x is not None else self.x
            diff = target_x - self.x
            if abs(diff) > 4:
                self.x += np.sign(diff) * config.MOVE_SPEED * 0.6 * dt
                self.dir = 1 if diff > 0 else -1
            self.col = self.x / config.TILE
            self.y = (world.surface_row(int(self.col)) - 0.5) * config.TILE
            return
        self.wander_t -= dt
        if self.wander_t <= 0:
            self.wander_t = float(np.random.uniform(2.0, 5.0))
            to_player = player_x - self.x
            if abs(to_player) < config.TILE * 10 and np.random.random() < 0.4:
                self.dir = 1 if to_player > 0 else -1
            else:
                self.dir = int(np.random.choice([-1, 1]))
        step = self.dir * config.MOVE_SPEED * 0.35 * dt
        nx = self.x + step
        col = int(nx / config.TILE)
        row = world.surface_row(col)
        if world.in_bounds(row, col) and not world.is_solid(row - 1, col):
            self.x = nx
            self.col = col
        else:
            self.dir = -self.dir
        self.row = world.surface_row(int(self.x / config.TILE))
        self.y = (self.row - 0.5) * config.TILE

    def sprite_frames(self, size=30):
        from .sprites import get_creature_sprites
        return get_creature_sprites(self.species, self.color, self.seed, size)


class CreatureManager:
    def __init__(self, rng, world, ga):
        self.rng = rng
        self.creatures = []
        names = set()
        n = 8
        for i in range(n):
            species, base = SPECIES[i % len(SPECIES)]
            col = int(rng.integers(10, config.WORLD_COLS - 10))
            row = world.surface_row(col) - 1
            hearts = ga.genes["charm_hearts"]
            jitter = ga.genes["creature_palette_jitter"]
            color = tuple(
                max(40, min(255, c + int(rng.integers(-jitter, jitter + 1))))
                for c in base
            )
            name = f"{species} {i + 1}"
            k = 1
            while name in names:
                k += 1
                name = f"{species} {k}"
            names.add(name)
            c = Creature(i, species, color, col, row, hearts, "berry",
                         seed=int(rng.integers(0, 2**31)))
            c.x = (col + 0.5) * config.TILE
            c.y = (row + 0.5) * config.TILE
            self.creatures.append(c)

    def nearest(self, x, y, max_dist=config.TILE * 5):
        best, best_d = None, float("inf")
        for c in self.creatures:
            d = ((c.x - x) ** 2 + (c.y - y) ** 2) ** 0.5
            if d < best_d:
                best, best_d = c, d
        return best if best_d <= max_dist else None

    def befriend(self, creature, castle_x):
        creature.befriended = True
        creature.home_x = castle_x + self.rng.integers(-5, 6) * config.TILE
        return creature

    def update(self, world, dt, player_x):
        for c in self.creatures:
            c.update(world, dt, player_x)
