"""The Unnamed Shadow and the Friendship Shield (spec section 2.2).

The shadow cannot be attacked. It is gently repelled by the warmth
of the restored pylons and the castle's Harmony Rating. If it reaches
the player while the shield is too weak, it drains harmony — never
health; the game has no combat.
"""
from . import config


class Shadow:
    def __init__(self, col):
        self.col = float(col)
        self.active = False
        self.pushback = 0.0

    def update(self, dt, shield_strength, player_col, ga):
        if shield_strength <= 0:
            self.active = False
            return 0.0
        self.active = True
        pressure = config.SHADOW_SPEED * ga.genes["shadow_pressure"]
        if shield_strength > 0.5:
            self.col += pressure * dt * 0.5
        else:
            self.col -= pressure * dt
        self.col = max(1.0, min(config.WORLD_COLS - 2.0, self.col))
        if abs(self.col - player_col) < 1.5 and shield_strength < 0.35:
            return config.HARMONY_DECAY * dt * 2
        return 0.0


class FriendshipShield:
    """Aggregates pylon restoration and castle harmony into shield power."""

    def __init__(self):
        self.harmony = 0.0
        self.pylon_count = 0

    def strength(self, pylons_total, pylons_restored):
        pylon_part = pylons_restored / max(1, pylons_total)
        harmony_part = min(1.0, self.harmony / 100.0)
        return 0.5 * pylon_part + 0.5 * harmony_part

    def add_harmony(self, amount, ga):
        self.harmony = min(120.0, self.harmony + amount * ga.genes["harmony_gain"])

    def drain(self, amount):
        self.harmony = max(0.0, self.harmony - amount)
