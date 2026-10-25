"""Procedural sound effects - no audio assets needed.

Generates short synth chimes with NumPy and plays them via pygame's
mixer. Degrades gracefully to silence when no audio device exists
(e.g. headless testing on the Pi without a sound card).
"""
import os

import numpy as np
import pygame

from . import config

SAMPLE_RATE = 22050


def _tone(freqs, dur, volume=0.35, decay=6.0, shape="sine"):
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n) / SAMPLE_RATE
    wave = np.zeros(n)
    for f in freqs:
        if shape == "sine":
            wave += np.sin(2 * np.pi * f * t)
        elif shape == "square":
            wave += np.sign(np.sin(2 * np.pi * f * t)) * 0.4
    envelope = np.exp(-decay * t)
    arr = (wave * envelope * volume * 32767 * 0.5).astype(np.int16)
    stereo = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _melody(notes, note_dur, volume=0.16, shape="sine"):
    """notes: list of frequencies; rendered as one gentle loopable tune."""
    n = int(SAMPLE_RATE * note_dur * len(notes))
    t = np.arange(n) / SAMPLE_RATE
    wave = np.zeros(n)
    seg = n // len(notes)
    for i, f in enumerate(notes):
        ts = t[i * seg:(i + 1) * seg]
        if shape == "sine":
            wave[i * seg:(i + 1) * seg] = np.sin(2 * np.pi * f * ts)
        else:
            wave[i * seg:(i + 1) * seg] = np.sign(
                np.sin(2 * np.pi * f * ts)) * 0.4
    env = np.ones(n)
    for i in range(len(notes)):
        s, e = i * seg, min(n, (i + 1) * seg)
        env[s:e] *= np.exp(-2.5 * (np.arange(e - s) / SAMPLE_RATE) / note_dur)
    arr = (wave * env * volume * 32767 * 0.5).astype(np.int16)
    return pygame.sndarray.make_sound(
        np.ascontiguousarray(np.column_stack([arr, arr])))


C4, D4, E4, G4, A4, C5, E5, G5 = 262, 294, 330, 392, 440, 523, 659, 784


class Sounds:
    """Lazily built sound bank; no-ops safely without an audio device."""

    def __init__(self):
        self.enabled = False
        self.bank = {}
        self.music_on = False
        try:
            os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
            self._build()
            self.enabled = True
        except Exception:
            self.enabled = False

    def start_music(self):
        if not self.enabled or self.music_on:
            return
        try:
            tune = _melody(
                [C4, E4, G4, A4, C5, A4, G4, E4,
                 D4, G4, C5, E5, G5, E5, C5, G4],
                0.55, volume=0.13,
            )
            tune.play(loops=-1)
            self.music_on = True
        except Exception:
            pass

    def _build(self):
        self.bank["break"] = _tone([180, 240], 0.12, 0.3, 22, "square")
        self.bank["place"] = _tone([320, 480], 0.08, 0.3, 28)
        self.bank["pickup"] = _tone([660, 990], 0.09, 0.25, 24)
        self.bank["wand"] = _tone([880, 1320], 0.15, 0.22, 14)
        self.bank["feed"] = _tone([520, 780], 0.12, 0.3, 16)
        self.bank["friend"] = _tone([523, 659, 784], 0.5, 0.4, 5)
        self.bank["key"] = _tone([700, 1050], 0.2, 0.35, 10)
        self.bank["catalyst"] = _tone([440, 550, 660], 0.4, 0.4, 6)
        self.bank["pylon"] = _tone([392, 494, 587, 784], 0.7, 0.45, 4)
        self.bank["puzzle_ok"] = _tone([600], 0.1, 0.3, 20)
        self.bank["puzzle_bad"] = _tone([200], 0.2, 0.3, 10, "square")
        self.bank["jump"] = _tone([330, 440], 0.09, 0.18, 20)
        self.bank["victory"] = _tone([523, 659, 784, 1047], 1.2, 0.5, 2.5)

    def play(self, name):
        if self.enabled and name in self.bank:
            try:
                self.bank[name].play()
            except Exception:
                pass
