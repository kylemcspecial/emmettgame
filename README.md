# Citadel of Friendship & Magic

A family-friendly, non-violent voxel sandbox / puzzle RPG for Raspberry Pi 4/5, built from `Raspberry Pi Game Specification.md`.

## Super Easy Install (for kids!)

1. Clone this repo (or download and unzip it)
2. Open the folder and **double-click `install.sh`** (choose *Execute in Terminal*)
   - If double-click doesn't work: open a Terminal in the folder and run `bash install.sh`
3. When it finishes, a **Citadel of Friendship & Magic** icon appears on your **Desktop**
4. **Double-click the icon and play!**

*(The first time only, Raspberry Pi OS may ask you to right-click the icon and pick "Allow Launching".)*

## Run directly

```bash
pip3 install pygame numpy
python3 run_game.py            # on Pi desktop
python3 run_game.py --headless  # no display (smoke test)
```

## Controls

- `A` / `D` or Left/Right arrows — move; `W` / `Space` — jump
- **Left click** (hold) — break blocks, or cast the wand at creatures, thorns, and pylons
- **Right click** — place the selected block, or feed a Sunberry to a creature
- `1`–`9` or scroll — hotbar selection (slot 1 is the fixed Magic Wand)
- `E` — Friendship Ledger (creatures, pylons, backpack)
- `F5` — quick-save (auto-loads next time)
- `Esc` — close panels / quit

## Gameplay

- Explore: mine ancient oak, crystal, starlight, and stone; berry bushes regrow (farming!).
- Befriend every creature you meet — charm them with your wand or feed them Sunberries. They'll move next to your castle as guardians.
- Solve the rune puzzles at the ancient pylons to light up the Friendship Shield.
- Build your dream citadel at the heart of the realm — the right blocks near the right creatures give extra Harmony.
- The Unnamed Shadow can't be fought — it's gently pushed away by warmth and friendship. Restore all pylons and raise your Harmony to fill the realm with light and win!
- A genetic algorithm quietly tunes puzzles and creatures so the game stays fun and never too hard.

## Layout

- `install.sh` — one-click installer (deps + desktop icon)
- `make_icon.py` — generates the desktop icon
- `run_game.py` — launcher
- `citadel/main.py` — game loop
- `citadel/world.py` — voxel grid, blocks, drops, regrowth
- `citadel/player.py` — physics
- `citadel/inventory.py` — hotbar, backpack, item drops
- `citadel/creatures.py` — befriending and charm hearts
- `citadel/pylons.py` — rune puzzles, shield, the Shadow
- `citadel/genetics.py` — self-evaluating genetic tuner
- `citadel/castle.py` — Harmony Rating and creature/block synergies
- `citadel/save.py` — save/load
- `citadel/graphics.py` / `renderer.py` — procedural art and drawing
- `tests/test_smoke.py` — headless test of all systems
