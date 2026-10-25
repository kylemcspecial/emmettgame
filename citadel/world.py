"""Voxel grid world: generation, block queries, drops and regrowth.

Side-view 2D voxel grid. Layers: sky above terrain; grass/dirt/stone
below; scattered resources (ancient oak, crystal, starlight, berry
bushes, dark thorns) on the surface; a cave pocket underground.
"""
import numpy as np

from . import config

AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
QUARTZ = 5
CRYSTAL = 6
STARLIGHT = 7
THORNS = 8
BERRY_BUSH = 9
CASTLE_STONE = 10
CASTLE_QUARTZ = 11
RUNE_KEY_BLOCK = 12
CATALYST_BLOOM = 13

BLOCKS = {
    AIR: ("Air", None),
    GRASS: ("Grass", (100, 170, 80)),
    DIRT: ("Dirt", (128, 92, 60)),
    STONE: ("Stone", (135, 135, 145)),
    WOOD: ("Ancient Oak", (150, 108, 62)),
    QUARTZ: ("Quartz", (235, 235, 240)),
    CRYSTAL: ("Crystal", (120, 220, 255)),
    STARLIGHT: ("Starlight Stone", (255, 240, 160)),
    THORNS: ("Dark Thorns", (70, 46, 66)),
    BERRY_BUSH: ("Berry Bush", (60, 140, 70)),
    CASTLE_STONE: ("Castle Stone", (185, 190, 205)),
    CASTLE_QUARTZ: ("Castle Quartz", (250, 245, 255)),
    RUNE_KEY_BLOCK: ("Rune Key Shard", (200, 140, 255)),
    CATALYST_BLOOM: ("Catalyst Bloom", (170, 130, 255)),
}

BREAKABLE = {GRASS, DIRT, STONE, WOOD, QUARTZ, CRYSTAL, STARLIGHT, THORNS,
             BERRY_BUSH, CASTLE_STONE, CASTLE_QUARTZ, RUNE_KEY_BLOCK,
             CATALYST_BLOOM}
DROPS = {
    GRASS: DIRT,
    DIRT: DIRT,
    STONE: STONE,
    WOOD: WOOD,
    QUARTZ: QUARTZ,
    CRYSTAL: CRYSTAL,
    STARLIGHT: STARLIGHT,
    THORNS: None,
    BERRY_BUSH: None,
    CASTLE_STONE: CASTLE_STONE,
    CASTLE_QUARTZ: CASTLE_QUARTZ,
    RUNE_KEY_BLOCK: None,
}
PLACEABLE = {DIRT, STONE, WOOD, QUARTZ, CRYSTAL, STARLIGHT, CASTLE_STONE, CASTLE_QUARTZ}
SOLID = {b for b in BLOCKS if b != AIR}


class World:
    def __init__(self, rng, cols=None, rows=None, castle_col=None):
        self.on_change = None      # renderer hook: (row, col)
        self.rng = rng
        self.cols = cols or config.WORLD_COLS
        self.rows = rows or config.WORLD_ROWS
        self.grid = np.zeros((self.rows, self.cols), dtype=np.int16)
        self.regrow = []  # (time_left, row, col, block)
        self.generate(castle_col=castle_col)

    def generate(self, castle_col=None):
        self.castle_col = castle_col
        ground = self.rows - 12
        heights = ground + np.clip(
            np.sin(np.arange(self.cols) * 0.18) * 2
            + self.rng.normal(0, 0.9, self.cols).cumsum() * 0.08,
            -4, 4,
        ).astype(int)
        for c in range(self.cols):
            h = int(heights[c])
            self.grid[h, c] = GRASS
            self.grid[h + 1:, c] = DIRT
            self.grid[self.rows - 4:, c] = STONE
        self.heights = heights
        self._scatter(WOOD, 30)
        self._scatter(CRYSTAL, 16)
        self._scatter(STARLIGHT, 10)
        self._scatter(THORNS, 14)
        self._scatter(BERRY_BUSH, 12)
        self._castle_deposits()
        self._rune_key_shards()
        self._caves()

    def _castle_deposits(self):
        center = self.castle_col or self.cols // 2
        placed = 0
        attempts = 0
        while placed < 8 and attempts < 400:
            attempts += 1
            c = int(self.rng.integers(center - 25, center + 26))
            c = max(2, min(self.cols - 3, c))
            r = self.surface_row(c) - 1
            if r >= 0 and self.grid[r, c] == AIR:
                block = CASTLE_STONE if placed % 2 == 0 else CASTLE_QUARTZ
                self.grid[r, c] = block
                placed += 1

    def _rune_key_shards(self):
        placed = 0
        attempts = 0
        while placed < 3 and attempts < 400:
            attempts += 1
            c = int(self.rng.integers(4, self.cols - 4))
            r = self.surface_row(c) - 1
            if r >= 0 and self.grid[r, c] == AIR:
                self.grid[r, c] = RUNE_KEY_BLOCK
                placed += 1
        placed = 0
        attempts = 0
        while placed < 3 and attempts < 400:
            attempts += 1
            c = int(self.rng.integers(4, self.cols - 4))
            r = self.surface_row(c) - 1
            if r >= 0 and self.grid[r, c] == AIR:
                self.grid[r, c] = CATALYST_BLOOM
                placed += 1

    def _scatter(self, block, n):
        placed = 0
        attempts = 0
        while placed < n and attempts < n * 40:
            attempts += 1
            c = int(self.rng.integers(3, self.cols - 3))
            h = int(self.heights[c])
            r = h - 1
            if 0 <= r and self.grid[r, c] == AIR:
                self.grid[r, c] = block
                placed += 1

    def _caves(self):
        for _ in range(5):
            c0 = int(self.rng.integers(8, self.cols - 16))
            r0 = int(self.rng.integers(self.rows - 14, self.rows - 6))
            for dr in range(3):
                for dc in range(int(5 + self.rng.integers(0, 3))):
                    rr, cc = r0 + dr, c0 + dc
                    if self.in_bounds(rr, cc):
                        self.grid[rr, cc] = AIR
            rr = min(self.rows - 1, r0 + 3)
            cc = c0 + 2
            if self.in_bounds(rr, cc) and self.grid[rr, cc] == AIR:
                self.grid[rr, cc] = CRYSTAL

    def in_bounds(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get(self, row, col):
        if self.in_bounds(row, col):
            return int(self.grid[row, col])
        return AIR

    def set(self, row, col, block):
        if self.in_bounds(row, col):
            self.grid[row, col] = block
            if self.on_change is not None:
                self.on_change(row, col)
            return True
        return False

    def is_solid(self, row, col):
        return self.get(row, col) in SOLID

    def surface_row(self, col):
        for r in range(self.rows):
            if self.grid[r, col] != AIR:
                return r
        return self.rows - 1

    def break_block(self, row, col):
        block = self.get(row, col)
        if block in BREAKABLE:
            self.grid[row, col] = AIR
            if self.on_change is not None:
                self.on_change(row, col)
            if block == BERRY_BUSH:
                return "berry", 2
            if block == THORNS:
                return None, 0
            if block == RUNE_KEY_BLOCK:
                return "rune_key", 1
            if block == CATALYST_BLOOM:
                return "catalyst", 1
            drop = DROPS.get(block)
            return drop, 1
        return None, 0

    def place_block(self, row, col, block):
        if block in PLACEABLE and self.get(row, col) == AIR:
            self.grid[row, col] = block
            return True
        return False

    def schedule_regrowth(self, row, col, block, delay=None):
        delay = delay if delay is not None else config.REGROWTH_TIME
        self.regrow.append([delay, row, col, block])

    def update(self, dt):
        still = []
        for entry in self.regrow:
            entry[0] -= dt
            if entry[0] <= 0:
                _, r, c, b = entry
                if self.get(r, c) == AIR:
                    self.grid[r, c] = b
                    if self.on_change is not None:
                        self.on_change(r, c)
            else:
                still.append(entry)
        self.regrow = still

    def counts(self):
        return {name: int((self.grid == b).sum()) for b, (name, _) in BLOCKS.items() if b}
