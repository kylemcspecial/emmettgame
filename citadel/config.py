"""Game constants: tuning values shared across modules."""
import numpy as np

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

WORLD_COLS = 64
WORLD_ROWS = 48
TILE = 24
CAMERA_SPEED = 240.0
PLAYER_SPEED = 150.0
PLAYER_DRAW_R = 10

GA_MUTATION_RATE = 0.18
SHADOW_SPEED = 38.0
SHIELD_DECAY = 0.4
HARMONY_DECAY = 0.5
WAND_RANGE = 6
WAND_COOLDOWN = 0.45
CHARM_TIME = 1.2
PYLON_REPAIR_BLOCKS = 4
RNG_SEED = 20261025

PALETTE = {
    "bg": (18, 22, 34),
    "grid": (36, 42, 60),
    "panel": (24, 28, 42),
    "text": (232, 238, 250),
    "accent": (255, 214, 92),
    "wand": (150, 220, 255),
    "harmony": (120, 255, 190),
    "shadow": (40, 32, 50),
    "danger": (255, 120, 120),
}

NUMPY_SEED = np.random.default_rng(RNG_SEED)
