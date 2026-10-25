"""Self-evaluating Genetic Algorithm (GA) tuning system (spec section 3).

Genes adapt to the player's measured performance (completion speed of
puzzles, creatures charmed) to hold difficulty at a good level for a
10-year-old player. Implemented as a simple fitness-driven mutation
loop evaluated on recent history.
"""
from . import config


class GeneticTuner:
    """Evolves puzzle and creature genes toward a target challenge."""

    def __init__(self, rng):
        self.rng = rng
        self.genes = {
            "pylon_path_len": 3,
            "pylon_runes_required": 3,
            "charm_len": 3,
            "shadow_pressure": 1.0,
            "harmony_gain": 1.0,
            "creature_palette_jitter": 20,
        }
        self.gene_bounds = {
            "pylon_path_len": (2, 6),
            "pylon_runes_required": (2, 5),
            "charm_len": (2, 5),
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
        durations = [d for _, d in self.history]
        avg = sum(durations) / len(durations)
        if avg < 6.0:
            direction = 1
        elif avg > 14.0:
            direction = -1
        else:
            direction = 0
        for key in ("pylon_path_len", "pylon_runes_required", "charm_len"):
            lo, hi = self.gene_bounds[key]
            if direction:
                delta = 1 if direction > 0 else -1
                self.genes[key] = max(lo, min(hi, self.genes[key] + delta))
        self.history.clear()
        self.generation += 1

    def mutate_color(self, color):
        jitter = self.genes["creature_palette_jitter"]
        return tuple(
            max(0, min(255, int(c) + self.rng.integers(-jitter, jitter + 1)))
            for c in color
        )

    def synergy_bonus(self, block_type, species):
        """Spec 3.1: castle buff synergies between block types and creatures."""
        table = {
            ("quartz", "Glimmermoth"): 2,
            ("crystal", "Lumifawn"): 3,
            ("ancient_oak", "Mossgale"): 2,
            ("starlight", "Sparklewisp"): 3,
            ("castle_stone", "Pebblepuff"): 1,
        }
        return table.get((block_type, species), 0)


class GeneSerializer:
    @staticmethod
    def to_dict(ga):
        return {"generation": ga.generation, "genes": dict(ga.genes)}

    @staticmethod
    def from_dict(ga, data):
        ga.generation = data.get("generation", ga.generation)
        for k, v in data.get("genes", {}).items():
            if k in ga.genes:
                ga.genes[k] = v
