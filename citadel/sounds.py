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


def _noise(dur, volume=0.12, lowpass=True):
    """Soft wind: filtered noise with slow amplitude swell."""
    n = int(SAMPLE_RATE * dur)
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 1, n)
    if lowpass:
        kernel = np.ones(220) / 220.0
        noise = np.convolve(noise, kernel, mode="same")
    t = np.arange(n) / SAMPLE_RATE
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / dur)
    arr = (noise * swell * volume * 32767 * 0.5).astype(np.int16)
    return pygame.sndarray.make_sound(
        np.ascontiguousarray(np.column_stack([arr, arr])))


def _birds(dur=6.0, volume=0.05):
    """Sparse bird chirps over silence."""
    n = int(SAMPLE_RATE * dur)
    wave = np.zeros(n)
    rng = np.random.default_rng(11)
    for _ in range(6):
        start = int(rng.uniform(0.05, 0.9) * n)
        chirp_len = int(0.12 * SAMPLE_RATE)
        if start + chirp_len >= n:
            continue
        base = float(rng.uniform(1800, 3200))
        tt = np.arange(chirp_len) / SAMPLE_RATE
        chirp = np.sin(2 * np.pi * (base + 600 * tt / 0.12) * tt)
        env = np.exp(-18 * tt)
        wave[start:start + chirp_len] += chirp * env
    arr = (wave * volume * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(
        np.ascontiguousarray(np.column_stack([arr, arr])))


class Sounds:
    """Lazily built sound bank; no-ops safely without an audio device."""

    def __init__(self):
        self.enabled = False
        self.bank = {}
        self.music_on = False
        self._volume = float(getattr(config, "VOLUME", 0.8))
        try:
            os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
            self._build()
            self.enabled = True
            self.apply_volume()
        except Exception:
            self.enabled = False

    def apply_volume(self):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.set_volume(self._volume * 0.5)
        except Exception:
            pass

    def set_volume(self, v):
        self._volume = max(0.0, min(1.0, float(v)))
        config.VOLUME = self._volume
        self.apply_volume()

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

    def start_ambient(self, night=False):
        """Looping wind; birds by day. Safe no-op without audio."""
        if not self.enabled or getattr(self, "_ambient_on", False):
            return
        try:
            _noise(8.0, volume=0.05).play(loops=-1)
            if not night:
                _birds().play(loops=-1, fade_ms=500)
            self._ambient_on = True
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
                snd = self.bank[name]
                snd.set_volume(self._volume)
                snd.play()
            except Exception:
                pass
