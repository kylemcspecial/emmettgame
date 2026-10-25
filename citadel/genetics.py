"""Self-evaluating Genetic Algorithm tuner (spec section 3).

Genes control puzzle difficulty and creature variety; the tuner
evaluates the player's recent completion times and nudges genes toward
the target challenge band.
"""
from . import config


class GeneticTuner:
    def __init__(self, rng):
        self.rng = rng
        self.genes = {
            "pylon_runes": 3,
            "charm_hearts": 3,
            "shadow_pressure": 1.0,
            "harmony_gain": 1.0,
            "creature_palette_jitter": 18,
        }
        self.bounds = {
            "pylon_runes": (2, 5),
            "charm_hearts": (2, 5),
            "shadow_pressure": (0.6, 1.6),
            "harmony_gain": (0.6, 1.6),
            "creature_palette_jitter": (0, 60),
        }
        self.history = []
        self.generation = 1

    def record_event(self, event, duration):
        self.history.append((event, duration))
        if len(self.history) >= 4:
            self._evaluate()

    def _evaluate(self):
        avg = sum(d for _, d in self.history) / len(self.history)
        if avg < 8.0:
            self._step(("pylon_runes", "charm_hearts"), +1)
        elif avg > 20.0:
            self._step(("pylon_runes", "charm_hearts"), -1)
        self.history.clear()
        self.generation += 1

    def _step(self, keys, delta):
        for k in keys:
            lo, hi = self.bounds[k]
            self.genes[k] = max(lo, min(hi, self.genes[k] + delta))

    def mutate_color(self, color):
        j = self.genes["creature_palette_jitter"]
        return tuple(
            max(0, min(255, int(c) + int(self.rng.integers(-j, j + 1))))
            for c in color
        )

    def synergy_bonus(self, item, species):
        """Spec 3.1: castle buffs from pairing block types near creatures."""
        table = {
            ("castle_quartz", "Glimmermoth"): 2,
            ("crystal", "Lumifawn"): 3,
            ("wood", "Mossgale"): 2,
            ("starlight", "Sparklewisp"): 3,
            ("castle_stone", "Pebblepuff"): 1,
            ("stone", "Bumblebrook"): 1,
        }
        return table.get((item, species), 0)

    def to_dict(self):
        return {"generation": self.generation, "genes": dict(self.genes)}

    def load_dict(self, data):
        self.generation = data.get("generation", self.generation)
        for k, v in data.get("genes", {}).items():
            if k in self.genes:
                lo, hi = self.bounds[k]
                self.genes[k] = max(lo, min(hi, v))
