# Citadel of Friendship & Magic

A family-friendly, non-violent voxel sandbox / puzzle RPG for Raspberry Pi 4/5, built from `Raspberry Pi Game Specification.md`.

## Run

```bash
pip3 install pygame numpy
python3 run_game.py          # on Pi desktop
python3 run_game.py --headless  # no display (smoke test)
```

## Controls

- `A` / `D` or Left/Right arrows — move
- Left click — cast wand (charm creatures, clear dark thorns, open pylon puzzles)
- Right click — place selected block / use item
- `1`–`9` or scroll — hotbar selection (slot 1 is the fixed Magic Wand)
- `E` — Friendship Ledger

## Gameplay

- Break and place blocks to build your castle near the shimmering pylon at map center.
- Charm wild creatures with wand spells; befriended ones become castle guardians.
- Solve energy-flow rune puzzles at ancient pylons to raise the Friendship Shield.
- The Unnamed Shadow is never fought — it is repelled only by warmth, friendship, and your castle's Harmony Rating.
- A genetic algorithm tunes puzzle complexity, charm sequences, and creature palettes to keep the challenge right for a 10-year-old wizard.

## Layout

- `citadel/main.py` — game loop
- `citadel/world.py` — voxel grid and block types
- `citadel/creatures.py` — befriending and charm sequences
- `citadel/pylons.py` — energy-flow shield puzzles
- `citadel/genetics.py` — self-evaluating genetic tuner
- `citadel/shadow.py` — the Unnamed Shadow and Friendship Shield
- `citadel/castle.py` — Harmony Rating and creature/block synergies
