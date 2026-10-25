"""Ancient pylons: rune-sequence energy-flow puzzles and shields (spec 2.1).

A pylon activates when the player stands near it and casts the wand.
The puzzle panel shows runes; click them in the lit sequence order.
Solving restores the pylon, which projects an expanding warm shield
that pushes the Unnamed Shadow back.
"""
import numpy as np

from . import config

RUNE_NAMES = ["Sun", "Moon", "Star", "Leaf", "Wave"]
RUNE_GLYPHS = {"Sun": "\u2600", "Moon": "\u263D", "Star": "\u2605", "Leaf": "\u2618", "Wave": "\u224B"}


class Pylon:
    def __init__(self, pid, col, row, seq_len, rng):
        self.pid = pid
        self.col = int(col)
        self.row = int(row)
        self.x = (col + 0.5) * config.TILE
        self.y = (row + 0.5) * config.TILE
        self.restored = False
        self.target_seq = [RUNE_NAMES[i] for i in rng.permutation(len(RUNE_NAMES))[:seq_len]]
        self.progress = 0
        self.shield_radius = 0.0
        self.last_feedback = None
        self.feedback_t = 0.0
        self.awakened = pid == 0   # first pylon starts awake; others wake in order

    def rune_order_hint(self):
        return list(self.target_seq)

    def click_rune(self, rune):
        if self.restored:
            return "restored"
        expected = self.target_seq[self.progress]
        if rune == expected:
            self.progress += 1
            if self.progress >= len(self.target_seq):
                self.restored = True
                self.shield_radius = 1.0
                return "solved"
            return "correct"
        self.progress = 0
        return "wrong"

    def update(self, dt):
        if self.feedback_t > 0:
            self.feedback_t -= dt
        if self.restored:
            max_r = config.WORLD_COLS * config.TILE
            self.shield_radius = min(max_r, self.shield_radius + 40.0 * dt)


class PylonManager:
    def __init__(self, rng, world, ga):
        self.rng = rng
        self.pylons = []
        cols = rng.choice(np.arange(12, config.WORLD_COLS - 12), size=5, replace=False)
        cols = np.sort(cols)
        for i, col in enumerate(cols):
            col = int(col)
            row = world.surface_row(col) - 1
            p = Pylon(i, col, row, ga.genes["pylon_runes"], rng)
            self.pylons.append(p)

    def awakened(self):
        return [p for p in self.pylons if p.awakened]

    def unrestored(self):
        return [p for p in self.pylons if p.awakened and not p.restored]

    def on_restored(self, pylon):
        """Wake the next pylon in order so progression stays gentle."""
        for p in self.pylons:
            if not p.awakened:
                p.awakened = True
                return p
        return None

    def near(self, x, y, dist=config.TILE * 4):
        for p in self.pylons:
            if not p.awakened:
                continue
            if ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5 <= dist:
                return p
        return None

    def all_restored(self):
        return all(p.restored for p in self.pylons)

    def update(self, dt):
        for p in self.pylons:
            p.update(dt)


class Shadow:
    """The Unnamed Shadow. Never fought; repelled by warmth/shield only."""

    def __init__(self, col):
        self.x = (col + 0.5) * config.TILE
        self.active = False
        self.banished = False
        self.wobble = 0.0

    def update(self, dt, shield_strength, player_x, ga, harmony):
        self.wobble += dt
        if self.banished:
            return 0.0
        if shield_strength <= 0.05:
            self.active = False
            return 0.0
        self.active = True
        speed = config.SHADOW_SPEED * ga.genes["shadow_pressure"]
        direction = 1 if shield_strength >= 0.5 else -1
        self.x -= direction * speed * dt
        self.x = max(config.TILE, min((config.WORLD_COLS - 1) * config.TILE, self.x))
        if shield_strength >= 0.99 and harmony >= 100:
            self.banished = True
            self.active = False
            return 0.0
        if abs(self.x - player_x) < config.TILE * 1.2 and shield_strength < 0.4:
            return 3.0 * dt
        return 0.0


class FriendshipShield:
    def __init__(self):
        self.harmony = 0.0

    def strength(self, pylons_total, pylons_restored):
        pylon_part = pylons_restored / max(1, pylons_total)
        harmony_part = min(1.0, self.harmony / 100.0)
        return 0.5 * pylon_part + 0.5 * harmony_part

    def add_harmony(self, amount, ga):
        self.harmony = min(150.0, self.harmony + amount * ga.genes["harmony_gain"])

    def drain(self, amount):
        self.harmony = max(0.0, self.harmony - amount)
