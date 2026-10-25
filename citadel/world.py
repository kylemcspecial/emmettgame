"""Block types, hotbar inventory items, and the voxel world grid.

The world is a 2D side-on projection of the voxel grid (a common
approach for lightweight voxel games on Raspberry Pi): the vertical
axis stacks blocks, the horizontal axis is the world grid. Breaking
and placing operate on the same grid Minecraft-style.
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
RUNE = 9
PYLON_CORE = 10
CASTLE_STONE = 11

BLOCK_COLORS = {
    AIR: (0, 0, 0),
    GRASS: (86, 158, 74),
    DIRT: (122, 87, 51),
    STONE: (128, 128, 140),
    WOOD: (150, 108, 62),
    QUARTZ: (232, 232, 238),
    CRYSTAL: (120, 220, 255),
    STARLIGHT: (255, 240, 160),
    THORNS: (70, 46, 66),
    RUNE: (190, 130, 255),
    PYLON_CORE: (255, 214, 92),
    CASTLE_STONE: (180, 190, 210),
}

BLOCK_NAMES = {
    AIR: "Air",
    GRASS: "Grass",
    DIRT: "Dirt",
    STONE: "Stone",
    WOOD: "Ancient Oak",
    QUARTZ: "Quartz",
    CRYSTAL: "Crystal",
    STARLIGHT: "Starlight Stone",
    THORNS: "Dark Thorns",
    RUNE: "Rune",
    PYLON_CORE: "Pylon Core",
    CASTLE_STONE: "Castle Stone",
}

BREAKABLE = {GRASS, DIRT, STONE, WOOD, QUARTZ, CRYSTAL, STARLIGHT, THORNS}
PLACEABLE = {STONE, WOOD, QUARTZ, CRYSTAL, STARLIGHT, CASTLE_STONE}


class World:
    """Voxel grid plus helper queries for building and breaking."""

    def __init__(self, rng):
        self.rng = rng
        self.cols = config.WORLD_COLS
        self.rows = config.WORLD_ROWS
        self.grid = np.zeros((self.rows, self.cols), dtype=np.int16)
        self._generate()

    def _generate(self):
        ground = self.rows - 6
        heights = ground + np.clip(
            np.sin(np.arange(self.cols) * 0.35) * 2
            + self.rng.normal(0, 1.0, self.cols),
            -3, 3,
        ).astype(int)
        for c in range(self.cols):
            h = int(heights[c])
            self.grid[h, c] = GRASS
            self.grid[h + 1 :, c] = DIRT
            self.grid[self.rows - 2 :, c] = STONE
        for _ in range(26):
            c = self.rng.integers(2, self.cols - 2)
            h = int(heights[c]) - 1
            if self.grid[h, c] == AIR:
                self.grid[h, c] = self.rng.choice([WOOD, CRYSTAL, STARLIGHT])
        for _ in range(10):
            c = self.rng.integers(4, self.cols - 4)
            h = int(heights[c]) - 1
            if self.grid[h, c] == AIR:
                self.grid[h, c] = THORNS
        self._carve_cave_pocket()
        self.ground_heights = heights

    def _carve_cave_pocket(self):
        c0 = self.rng.integers(10, self.cols - 10)
        r0 = self.rows - 10
        for dr in range(3):
            for dc in range(6):
                self.grid[r0 + dr, c0 + dc] = AIR
        self.grid[r0 + 3, c0 + 2] = CRYSTAL

    def in_bounds(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get(self, row, col):
        if not self.in_bounds(row, col):
            return AIR
        return int(self.grid[row, col])

    def set(self, row, col, block):
        if self.in_bounds(row, col):
            self.grid[row, col] = block
            return True
        return False

    def surface_row(self, col):
        for r in range(self.rows):
            if self.grid[r, col] != AIR:
                return r
        return self.rows - 1

    def break_block(self, row, col):
        block = self.get(row, col)
        if block in BREAKABLE:
            self.grid[row, col] = AIR
            return block
        return None

    def place_block(self, row, col, block):
        if block in PLACEABLE and self.get(row, col) == AIR:
            self.grid[row, col] = block
            return True
        return False
