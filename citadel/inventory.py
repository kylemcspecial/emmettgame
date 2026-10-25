"""Inventory: hotbar, backpack grid, and item drops on the ground."""
import numpy as np

from . import config
from .world import (AIR, BERRY_BUSH, CASTLE_QUARTZ, CASTLE_STONE, CRYSTAL,
                    DIRT, QUARTZ, RUNE_KEY_BLOCK, STARLIGHT, STONE, THORNS, WOOD)

ITEMS = {
    "wand": ("Magic Wand", (150, 220, 255)),
    "stone": ("Stone", (135, 135, 145)),
    "wood": ("Ancient Oak", (150, 108, 62)),
    "quartz": ("Quartz", (235, 235, 240)),
    "crystal": ("Crystal", (120, 220, 255)),
    "starlight": ("Starlight Stone", (255, 240, 160)),
    "dirt": ("Dirt", (128, 92, 60)),
    "berry": ("Sunberry", (255, 90, 120)),
    "castle_stone": ("Castle Stone", (185, 190, 205)),
    "castle_quartz": ("Castle Quartz", (250, 245, 255)),
    "catalyst": ("Shield Catalyst", (170, 130, 255)),
    "rune_key": ("Rune Key", (200, 140, 255)),
}

BLOCK_TO_ITEM = {
    DIRT: "dirt", STONE: "stone", WOOD: "wood", QUARTZ: "quartz",
    CRYSTAL: "crystal", STARLIGHT: "starlight",
    CASTLE_STONE: "castle_stone", CASTLE_QUARTZ: "castle_quartz",
    RUNE_KEY_BLOCK: "rune_key",
}
ITEM_TO_BLOCK = {v: k for k, v in BLOCK_TO_ITEM.items()}


class Inventory:
    def __init__(self):
        self.hotbar = [
            ("wand", None), ("stone", 20), ("wood", 10),
            ("dirt", 20), (None, None), (None, None), (None, None),
            (None, None), (None, None),
        ]
        self.backpack = [[(None, None) for _ in range(9)] for _ in range(3)]
        self.selected = 0

    def select(self, idx):
        if 1 <= idx <= 9:
            self.selected = idx - 1

    def cycle(self, delta):
        self.selected = (self.selected + delta) % 9

    def current_item(self):
        return self.hotbar[self.selected]

    def current_placeable_block(self):
        item, count = self.hotbar[self.selected]
        if item and count and item in ITEM_TO_BLOCK:
            return ITEM_TO_BLOCK[item]
        return None

    def add(self, item, amount=1):
        if item is None:
            return False
        for i, (it, ct) in enumerate(self.hotbar):
            if it == item and (ct is None or ct < config.MAX_STACK):
                self.hotbar[i] = (it, (ct or 0) + amount)
                return True
        for i, (it, ct) in enumerate(self.hotbar):
            if it is None:
                self.hotbar[i] = (item, amount)
                return True
        for r in range(3):
            for c in range(9):
                it, ct = self.backpack[r][c]
                if it == item and (ct is None or ct < config.MAX_STACK):
                    self.backpack[r][c] = (it, (ct or 0) + amount)
                    return True
        for r in range(3):
            for c in range(9):
                if self.backpack[r][c][0] is None:
                    self.backpack[r][c] = (item, amount)
                    return True
        return False

    def consume_selected(self):
        item, count = self.hotbar[self.selected]
        if item and count and count > 0:
            count -= 1
            self.hotbar[self.selected] = (item, count if count else None)
            return item
        return None

    def to_backpack(self, r, c):
        """Move a hotbar item into a free backpack slot."""
        if r != 0 or not (0 <= c < 9):
            return False
        item, count = self.hotbar[c]
        if not item:
            return False
        for rr in range(3):
            for cc in range(9):
                if self.backpack[rr][cc][0] is None:
                    self.backpack[rr][cc] = (item, count)
                    self.hotbar[c] = (None, None)
                    return True
        return False

    def consume(self, item, amount=1):
        for i, (it, ct) in enumerate(self.hotbar):
            if it == item and ct and ct >= amount:
                ct -= amount
                self.hotbar[i] = (it, ct if ct else None)
                return True
        for r in range(3):
            for c in range(9):
                it, ct = self.backpack[r][c]
                if it == item and ct and ct >= amount:
                    ct -= amount
                    self.backpack[r][c] = (it, ct if ct else None)
                    return True
        return False

    def count(self, item):
        total = 0
        for it, ct in self.hotbar:
            if it == item and ct:
                total += ct
        for row in self.backpack:
            for it, ct in row:
                if it == item and ct:
                    total += ct
        return total


class Drop:
    """A collectible item sitting in the world, bobbing gently."""

    def __init__(self, item, x, y, rng):
        self.item = item
        self.x = x
        self.y = y
        self.t = float(rng.uniform(0, 6.28))
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.t += dt * 3.0

    @property
    def bob(self):
        return np.sin(self.t) * 4


class DropManager:
    def __init__(self, rng, sounds=None):
        self.rng = rng
        self.drops = []
        self.sounds = sounds

    def spawn(self, item, x, y, count=1):
        for _ in range(count):
            jx = x + self.rng.uniform(-8, 8)
            self.drops.append(Drop(item, jx, y, self.rng))

    def update(self, dt, player, inventory, magnet=config.TILE * 2.2):
        picked = []
        px, py = player.center()
        attract = magnet * 2.2
        for d in self.drops:
            d.update(dt)
            dx, dy = px - d.x, py - d.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < attract and dist > 1:
                # drift toward the player so loot feels like it's collected
                pull = min(1.0, 260.0 * dt / max(dist, 1))
                d.x += dx * pull
                d.y += dy * pull
            if dist < magnet:
                if inventory.add(d.item, 1):
                    picked.append(d)
                    if self.sounds is not None:
                        self.sounds.play("pickup")
        self.drops = [d for d in self.drops if d not in picked and d.age < 120]
