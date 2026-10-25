# Game Specification: Citadel of Friendship & Magic

## Executive Summary
- **Target Platform:** Raspberry Pi 4 / 5 (Raspberry Pi OS 64-bit)
- **Target Audience:** Age 10+ (Family-friendly, encouraging friendship, kindness, and non-violent cooperation)
- **Primary Style/Genre:** Minecraft-style Voxel Sandbox / Puzzle RPG
- **Development Method:** Single-shot genetic coding architecture
- **Core Theme:** Friendship, magic wand wizardry, castle architecture, non-violent creature interaction, and environmental shield defense.
- **Tone:** Inspiring, whimsical, and reasonably challenging without battle or combat mechanics.

---

## 1. Core Gameplay & World Mechanics

### 1.1 Voxel World & Block Manipulation
- **Minecraft-style Grid World:** Fully destructible and constructible 3D voxel grid environment.
- **Block Interaction:** Players can break blocks (gathering natural elements like crystal, starlight stone, ancient oak) and place blocks to construct castles, forts, and safe sanctuaries.

### 1.2 Inventory & Interface
- **9-Slot Hotbar Inventory:** A 9-item quickbar on the bottom of the screen.
  - **Slot 1 (Fixed):** Magic Wand.
  - **Slots 2–9:** Dynamic slots for building blocks (stone, wood, quartz), puzzle tools, befriended creature charms, and shield catalysts.

### 1.3 Magic Wand & Spellcrafting (Non-Violent)
- **Charm & Enchantment Spells:** The Magic Wand fires gentle magical beams, light pulses, or gesture-based charm spells.
- **Befriending Creatures:** Wild mythical creatures in the realm are not fought. Instead, players use the wand to enchant, feed, and charm them. Once befriended, creatures move to the player's castle and act as guardians.
- **Utility Magic:** Spells assist with quick block placement, puzzle activation, and clearing dark thorns/corruption.

---

## 2. Puzzles, Shields & Castle Defense

### 2.1 Energy Flow Shield Puzzles
- **Broken Shield Nodes:** Ancient pylons are scattered across the land, needing repair.
- **Interactive Puzzles:** Solving circuit-style energy-flow puzzles and rune alignments restores power to the pylon.
- **Protective Forcefield:** Restored nodes create an expanding protective shield around the land.

### 2.2 Castle Building & The Unnamed Shadow
- **Architectural Defense:** Players construct their ultimate protective castle. Strategic block placement and creature placement boost the overall "Harmony Rating" of the castle.
- **Repelling the Unnamed Evil:** An unnamed dark shadow entity wanders the outskirts of the map. It cannot be attacked or harmed. Instead, it is gently repelled and banished exclusively by the warmth, friendship, and collective power of the Friendship Shield radiating from the completed castle and befriended creatures.

---

## 3. Genetic Coding & Procedural Generation

### 3.1 Single-Shot Genetic Architecture
The entire game engine leverages a self-evaluating Genetic Algorithm (GA) system generated in a single script run:

- **Puzzle Genes:** Dynamically adjusts node complexity, path lengths, and required spell patterns based on player completion speed to maintain an optimal 10-year-old challenge level.
- **Creature Genes:** Mutates sprite patterns, color palettes, favorite items, and charm sequence inputs for infinite variation of friendly creatures.
- **Castle Buff Synergies:** Genetic rules assign higher shield defense bonuses when specific block types are paired near specific friendly creature habitats.

---

## 4. Technical Requirements & Controls (Raspberry Pi)

- **Operating System:** Raspberry Pi OS 64-bit
- **Language/Libraries:** Python 3.9+, Pygame, NumPy
- **Target Performance:** 1280x720 at 60 FPS
- **Control Scheme:**
  - `WASD` / Arrow Keys: Player Movement
  - `Left Click` / Primary Button: Break block / Cast Wand Spell
  - `Right Click` / Secondary Button: Place block / Interact
  - `1–9` Keys / Scroll: Inventory Selection (9 Slots)
  - `E`: Open Extended Inventory / Friendship Ledger