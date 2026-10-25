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
- **Right click** — place the selected block, feed a Sunberry, use a Rune Key or Catalyst
- `1`–`9` or scroll — hotbar selection (slot 1 is the fixed Magic Wand)
- `E` — Friendship Ledger (creatures, compass hints, backpack & hotbar)
- `H` — How-to-Play book
- `N` — name a befriended creature (they'll remember it forever!)
- `F5` — quick-save (auto-loads next time; also auto-saves on quit)
- `F6` — performance mode (fancy effects off/on)
- `F7` — FPS display
- `F11` — fullscreen
- `F12` — save a photo of your castle!
- `+` / `-` — volume up / down
- `Esc` — close panels / quit

Settings (volume, performance mode, fullscreen) are remembered between sessions.

**Gamepad:** left stick moves, A jumps, B casts the wand, X places, shoulder buttons cycle the hotbar, Start opens the ledger.

## Gameplay

- Explore: mine ancient oak, crystal, starlight, castle stone, and more; berry bushes regrow (farming!). Glowing shards hold Rune Keys, and Catalyst Blooms hold Shield Catalysts.
- **Blessing Fountain**: right-click the fountain at your castle site while holding stone, wood, quartz, crystal, or starlight - it blesses them into Castle Stone or Castle Quartz!
- **13 badges to earn**: First Friend, Lightbringer, Castle Builder, Green Thumb, and more - watch for star toasts, and see them all in the Friendship Ledger (`E`).
- Befriend every creature you meet — charm them with your wand or feed them Sunberries. **Every creature looks different** — six species, each with its own size, pattern, and little accessories. Name your friends with `N`!
- Pylons awaken one at a time — solve a rune puzzle to restore one, and the next ancient pylon stirs somewhere in the realm.
- Build your dream citadel at the banner in the heart of the realm — the right blocks near the right creatures give extra Harmony.
- The Unnamed Shadow can't be fought — it's gently pushed away by warmth and friendship. Restore all pylons and raise your Harmony to fill the realm with light and win!
- Days pass, stars come out, and a gentle melody plays. A genetic algorithm quietly tunes puzzles and creatures so the game stays fun and never too hard.

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
