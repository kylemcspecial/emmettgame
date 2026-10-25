"""Game constants and tuning values."""
import numpy as np

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TITLE = "Citadel of Friendship & Magic"

WORLD_COLS = 220
WORLD_ROWS = 64
TILE = 32
GRAVITY = 1500.0
MOVE_SPEED = 260.0
JUMP_VELOCITY = -560.0
MAX_FALL = 900.0
REACH = 5          # blocks
BREAK_TIME = 0.35  # seconds per block
WAND_COOLDOWN = 0.4
CHARM_HEARTS = 3   # wand casts to befriend (base, GA-tuned per creature)
REGROWTH_TIME = 25.0
BERRY_FEED_HARMONY = 4.0
SHADOW_SPEED = 26.0
SAVE_PATH = "savegame.json"
MAX_STACK = 99

RNG_SEED = 20261025

PALETTE = {
    "bg_top": (110, 150, 220),
    "bg_bottom": (200, 220, 245),
    "text": (30, 34, 48),
    "panel": (246, 240, 225),
    "panel_edge": (90, 70, 50),
    "accent": (255, 190, 60),
    "wand": (150, 220, 255),
    "harmony": (90, 200, 120),
    "shadow": (30, 22, 40),
    "danger": (220, 90, 90),
}

RNG = np.random.default_rng(RNG_SEED)
