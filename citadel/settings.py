"""Persistent player settings (volume, performance mode, fullscreen)."""
import json
import os

from . import config

SETTINGS_PATH = "settings.json"


def _bool(data, key, default):
    v = data.get(key, default)
    return bool(v) if isinstance(v, (bool, int)) else default


def _volume(data):
    v = data.get("volume", 0.8)
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.8


def load_settings(path=None):
    path = path or SETTINGS_PATH
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
    config.PERFORMANCE_MODE = _bool(data, "performance_mode", False)
    config.SHOW_FPS = _bool(data, "show_fps", False)
    config.FULLSCREEN = _bool(data, "fullscreen", False)
    config.VOLUME = _volume(data)


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
