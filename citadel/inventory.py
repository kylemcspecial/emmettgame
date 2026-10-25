"""9-slot hotbar. Slot 1 is fixed to the Magic Wand; slots 2-9 dynamic."""
from . import world as W


class Hotbar:
    def __init__(self):
        self.slots = [
            ("wand", "Magic Wand", None),
            ("block", W.STONE, 32),
            ("block", W.WOOD, 32),
            ("block", W.QUARTZ, 16),
            ("block", W.CASTLE_STONE, 12),
            ("block", W.CRYSTAL, 8),
            ("block", W.STARLIGHT, 6),
            ("charm", "Empty Charm", None),
            ("catalyst", "Shield Catalyst", 3),
        ]
        self.selected = 0

    def select(self, idx):
        if 1 <= idx <= len(self.slots):
            self.selected = idx - 1

    def cycle(self, delta):
        self.selected = (self.selected + delta) % len(self.slots)

    def kind_of(self, idx):
        return self.slots[idx][0]

    def current(self):
        return self.slots[self.selected]

    def current_block(self):
        kind, value, count = self.slots[self.selected]
        if kind == "block" and count and count > 0:
            return value
        return None

    def consume_current(self):
        kind, value, count = self.slots[self.selected]
        if kind == "block" and count and count > 0:
            self.slots[self.selected] = (kind, value, count - 1)
            return value
        return None

    def add_block(self, block, amount=1):
        for i, (kind, value, count) in enumerate(self.slots):
            if kind == "block" and value == block:
                self.slots[i] = (kind, value, count + amount)
                return True
        for i, (kind, value, count) in enumerate(self.slots):
            if kind == "block" and (not count or count <= 0):
                self.slots[i] = ("block", block, amount)
                return True
        return False

    def set_charm(self, creature_name):
        self.slots[7] = ("charm", f"{creature_name} Charm", 1)

    def use_catalyst(self):
        kind, value, count = self.slots[8]
        if kind == "catalyst" and count and count > 0:
            self.slots[8] = (kind, value, count - 1)
            return True
        return False
