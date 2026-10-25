"""Energy-flow shield puzzles at ancient pylons (spec section 2.1).

Each pylon shows a rune sequence the player must click in order. When
solved, the pylon restores and projects an expanding protective shield.
"""
from . import config, world as W


class Pylon:
    def __init__(self, col, row, seq_len, rng):
        self.col = col
        self.row = row
        self.restored = False
        self.rune_set = ["Alpha", "Beta", "Gamma", "Delta", "Omega"]
        self.target_seq = [
            self.rune_set[i] for i in rng.permutation(len(self.rune_set))[:seq_len]
        ]
        self.progress = 0
        self.shield_radius = 0.0
        self.attempt_start = None

    def click_rune(self, rune_name, rng):
        if self.restored:
            return "restored"
        expected = self.target_seq[self.progress]
        if rune_name == expected:
            self.progress += 1
            if self.progress >= len(self.target_seq):
                self.restored = True
                self.shield_radius = 1.0
                return "solved"
            return "correct"
        self.progress = 0
        return "wrong"

    def update(self, dt):
        if self.restored and self.shield_radius < config.WORLD_COLS:
            self.shield_radius += config.SHIELD_DECAY * dt * 10


class PylonManager:
    def __init__(self, rng, world, ga):
        self.rng = rng
        self.pylons = []
        cols = rng.choice(np.arange(6, config.WORLD_COLS - 6), size=4, replace=False)
        for col in cols:
            row = max(0, world.surface_row(int(col)) - 1)
            p = Pylon(int(col), row, ga.genes["pylon_runes_required"], rng)
            self.pylons.append(p)
            world.set(row, int(col), W.RUNE)

    def nearest_unrestored(self, player, max_dist=config.WAND_RANGE):
        best, best_d = None, 10**9
        for p in self.pylons:
            if p.restored:
                continue
            d = abs(p.col - player.col) + abs(p.row - player.row)
            if d < best_d:
                best, best_d = p, d
        return best if best_d <= max_dist else None

    def all_restored(self):
        return all(p.restored for p in self.pylons)

    def update(self, dt):
        for p in self.pylons:
            p.update(dt)


import numpy as np  # noqa: E402  (kept local to avoid import cycle at module load)
