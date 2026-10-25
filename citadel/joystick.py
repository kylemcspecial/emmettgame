"""Gamepad support: young kids often do better with a controller.

Maps a standard pad to the game's actions. Axes drive movement and
jump; face buttons cast the wand and place blocks; shoulders cycle
the hotbar; start opens the ledger; select quick-saves.
"""
import pygame

from . import config

DEADZONE = 0.25


class Gamepad:
    def __init__(self):
        self.js = None
        self.hat_jump = False
        self.enabled = False

    def connect(self):
        if pygame.joystick.get_init() and pygame.joystick.get_count() > 0:
            self.js = pygame.joystick.Joystick(0)
            self.js.init()
            self.enabled = True
            return True
        return False

    def poll(self):
        """Return (move_axis, jump, actions) or None when no pad."""
        if not self.enabled or not self.js:
            return None
        axis = 0.0
        if self.js.get_numaxes() >= 1:
            raw = self.js.get_axis(0)
            if abs(raw) > DEADZONE:
                axis = 1 if raw > 0 else -1
        jump = False
        if self.js.get_numaxes() >= 2 and self.js.get_axis(1) < -DEADZONE:
            jump = True
        return axis, jump

    def button(self, i):
        return self.enabled and self.js and self.js.get_button(i)


class PadRouter:
    """Translates pad state into the same calls the keyboard uses."""

    def __init__(self, game):
        self.game = game
        self.pad = Gamepad()
        self.pad.connect()
        self.prev = {}

    def _edge(self, idx, action):
        now = bool(self.pad.button(idx))
        if now and not self.prev.get(idx, False):
            action()
        self.prev[idx] = now

    def update(self):
        g = self.game
        if not self.pad.enabled:
            return 0, False
        axis, jump = self.pad.poll() or (0, False)
        if g.mode == "play":
            self._edge(0, lambda: g._left_action(pygame.mouse.get_pos()))
            self._edge(1, lambda: g._right_action(pygame.mouse.get_pos()))
            self._edge(4, lambda: g.inventory.cycle(-1))
            self._edge(5, lambda: g.inventory.cycle(1))
        self._edge(9, lambda: setattr(g, "mode",
                     "play" if g.mode == "inventory" else "inventory"))
        self._edge(8, lambda: g.notify("Gamepad connected: use it to play!",
                                       3) if False else None)
        return axis, jump
