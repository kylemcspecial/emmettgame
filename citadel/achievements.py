"""Achievements: gentle milestone badges with toast notifications.

Checked each frame against game state; unlocked badges persist in the
save file and are shown in the Friendship Ledger.
"""
import pygame

from . import config


class Achievements:
    DEFS = [
        ("first_friend", "First Friend!",
         "Befriend your very first creature"),
        ("three_friends", "Circle of Friends",
         "Befriend three creatures"),
        ("all_friends", "Everyone Belongs",
         "Befriend every creature in the realm"),
        ("first_pylon", "Lightbringer",
         "Restore your first pylon"),
        ("half_pylons", "Beacon Keeper",
         "Restore half of the awakened pylons"),
        ("all_pylons", "Guardian of Light",
         "Restore every pylon"),
        ("builder", "Castle Builder",
         "Place 25 blocks at your citadel"),
        ("architect", "Master Architect",
         "Place 100 blocks at your citadel"),
        ("harmony_50", "Warm Heart",
         "Reach 50 Harmony"),
        ("harmony_100", "Radiant Realm",
         "Reach 100 Harmony"),
        ("shadow_banished", "Shadow Banished",
         "Fill the realm with light"),
        ("green_thumb", "Green Thumb",
         "Harvest 10 Sunberries"),
        ("namer", "The Namer",
         "Give a friend their name"),
    ]

    def __init__(self, game):
        self.game = game
        self.unlocked = set()
        self.toasts = []           # (text, sub, t)
        self.berries = 0
        self.named = False

    def unlock(self, key):
        if key not in self.unlocked:
            self.unlocked.add(key)
            name, sub = next(
                (d[1], d[2]) for d in self.DEFS if d[0] == key)
            self.toasts.append([name, sub, 4.0])
            self.game.sounds.play("friend")

    def event_berry_harvest(self):
        self.berries += 1
        if self.berries >= 10:
            self.unlock("green_thumb")

    def event_named(self):
        self.named = True
        self.unlock("namer")

    def check(self):
        g = self.game
        friends = sum(1 for c in g.creatures.creatures if c.befriended)
        total = len(g.creatures.creatures)
        restored = len(g.pylons.pylons) - len(g.pylons.unrestored())
        awake = sum(1 for p in g.pylons.pylons if p.awakened)
        placed = len(g.castle.blocks)
        if friends >= 1:
            self.unlock("first_friend")
        if friends >= 3:
            self.unlock("three_friends")
        if friends >= total:
            self.unlock("all_friends")
        if restored >= 1:
            self.unlock("first_pylon")
        if awake and restored >= (awake + 1) // 2 and restored >= 1:
            self.unlock("half_pylons")
        if restored >= len(g.pylons.pylons):
            self.unlock("all_pylons")
        if placed >= 25:
            self.unlock("builder")
        if placed >= 100:
            self.unlock("architect")
        if g.shield.harmony >= 50:
            self.unlock("harmony_50")
        if g.shield.harmony >= 100:
            self.unlock("harmony_100")
        if g.shadow.banished:
            self.unlock("shadow_banished")

    def update(self, dt):
        self.check()
        for t in self.toasts:
            t[2] -= dt
        self.toasts = [t for t in self.toasts if t[2] > 0]

    def draw(self, screen, font, small):
        for i, (name, sub, t) in enumerate(self.toasts):
            alpha = min(1.0, t / 1.0)
            surf = pygame.Surface((340, 64), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255, 245, 210, int(235 * alpha)),
                            surf.get_rect(), border_radius=10)
            pygame.draw.rect(surf, (255, 214, 92, int(255 * alpha)),
                            surf.get_rect(), 3, border_radius=10)
            n = font.render(name, True, (150, 90, 40))
            s = small.render(sub, True, (90, 70, 50))
            star = font.render("\u2605", True, (255, 214, 92))
            surf.blit(star, (10, 8))
            surf.blit(n, (40, 8))
            surf.blit(s, (40, 34))
            y = 150 + i * 70
            screen.blit(surf, (config.SCREEN_W - 360, y))

    def to_dict(self):
        return {"unlocked": sorted(self.unlocked),
                "berries": self.berries, "named": self.named}

    def load_dict(self, data):
        self.unlocked = set(data.get("unlocked", []))
        self.berries = int(data.get("berries", 0))
        self.named = bool(data.get("named", False))
