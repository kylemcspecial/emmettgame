"""Persistent player settings (volume, performance mode, fullscreen)."""
import json
import os

from . import config

SETTINGS_PATH = "settings.json"
KEYS = ("performance_mode", "show_fps", "volume", "fullscreen")


def load_settings(path=None):
    path = path or SETTINGS_PATH
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            data = {}
    config.PERFORMANCE_MODE = bool(data.get("performance_mode", False))
    config.SHOW_FPS = bool(data.get("show_fps", False))
    config.FULLSCREEN = bool(data.get("fullscreen", False))
    config.VOLUME = max(0.0, min(1.0, float(data.get("volume", 0.8))))


def save_settings(path=None):
    path = path or SETTINGS_PATH
    data = {
        "performance_mode": bool(config.PERFORMANCE_MODE),
        "show_fps": bool(config.SHOW_FPS),
        "volume": float(config.VOLUME),
        "fullscreen": bool(config.FULLSCREEN),
    }
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass
