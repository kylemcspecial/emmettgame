# Citadel of Friendship & Magic — Engineering Notes

This is a kid's game running on **Raspberry Pi OS, Python 3.9–3.11, pygame-ce**.
The dev environment may be newer than the target. The rules below exist because
each one was a real bug found the hard way. Read them before changing code.

## Target platform rules

- **Python 3.9 compatibility is mandatory.** Never use backslashes inside
  f-string expressions, `match` statements, or other 3.10+ syntax. The Pi runs
  3.11; the dev sandbox may run 3.12, which silently accepts more.
  `tests/test_smoke.py` runs a repo-wide AST scan that fails the build on any
  backslash-in-f-string-expression. Keep it.
- **Do not install anything system-wide.** The game runs from a `.venv`
  created by `install.sh` (pygame-ce + numpy from `requirements.txt`).
  The launcher `start-citadel` execs the venv interpreter.
- **The Pi renders with SDL2 on KMS, often without GPU accel for this code
  path.** Treat per-frame allocations as crash risk (a leak/GC churn on the Pi
  was the suspected force-quit contributor). Reuse surfaces via cached
  instance attributes (see `_shadow_surf`, `_beam_surf`, `_weather_surf_*`,
  `_vignette`, `_tint` in `citadel/renderer.py`).

## pygame semantics that bit us (verify, don't assume)

- **`BLEND_RGB_ADD` and friends ignore source alpha.** A color like
  `(255, 180, 90, 26)` does NOT mean 10% strength — it means full-strength
  additive glare. Pre-scale the RGB by the intended strength instead. Any new
  blend-flag blit must be verified with a pixel-measurement probe, not eyeballed.
- **`pygame.display.set_mode()` returns a NEW surface.** Anything that
  reassigns `Game.screen` (e.g. the F11 fullscreen toggle) must also update
  `self.renderer.screen`, or every subsequent draw goes to a dead surface.
- **Full-screen-size alpha surfaces are expensive in software rendering.**
  Precompute once (e.g. the vignette distance-field in `draw_time_overlay`),
  or use quantized steps (e.g. `sky_steps`) — never per-frame full-screen copies.
- **Sounds/music must no-op safely.** The Pi may have no audio device; the
  dev sandbox may lack the mixer's shared library. `Sounds` catches
  everything; keep new audio code inside that pattern.

## Game-architecture rules

- **World/grid coordinate math must clamp.** `World.surface_row` clamps its
  column; creatures clamp to world bounds. Any new code that computes a
  column/row from a float position must do the same — an out-of-bounds
  NumPy index is an instant crash, invisible to the kid (launcher hides the
  terminal).
- **Never repurpose a legacy field for a new feature.** (A hop animation once
  reused `hop_t`, a stale random-initialized field — every creature spawned
  floating 60px in the air.) New behavior gets a new, explicitly-initialized
  field.
- **The world is pre-rendered once into `_world_surf` with dirty-rect
  updates.** Any block mutation goes through `World.set`/`break_block`
  (which fire `on_change`) or must call `renderer.mark_dirty` itself.
  Replacing the grid wholesale (load/reset) must set `renderer._world_surf = None`.
- **Kid-visible failures get kid-friendly fallbacks, never crashes or dead
  ends.** Corrupt `settings.json` or an old save falls back to defaults/a
  fresh realm with a friendly notice (see `citadel/settings.py`,
  `Game.__init__` load path).
- **Any crash must be diagnosable.** `run_game.py` installs a crash logger
  (`crash.log` in the game folder) and emergency-saves before dying; the run
  loop autosaves every 30 s. Don't add code paths outside this harness.

## Testing rules (how bugs hid from us)

- **Test through the real event path, not internal methods.** The dead
  left-click bug (wand interactions unreachable via MOUSEBUTTONDOWN) was
  invisible to tests that called `_left_action()` directly. New input
  features need a simulated `pygame.event.Event(...)` test.
- **Soak-test anything that moves.** The world-edge crash (creature walking
  home indexed out of bounds) reproduced only in a soak with a befriended
  creature forced toward the boundary. Run a 60s+ soak when touching
  creature/AI/position code.
- **Measure pixels for graphics changes.** The inverted vignette and the
  additive glare both *looked fine* in code review but failed numeric probes
  (sample corner vs center brightness on an isolated gray screen). Graphics
  PRs should include or pass a quantitative check like that.
- **Headless can't catch everything.** Fullscreen toggles, real audio, and
  display-surface identity only fail on real hardware. When touching those,
  say so explicitly in the PR and keep `F6` performance mode working.
- **The smoke test is the merge gate.** `python3 tests/test_smoke.py` covers
  physics, mining, befriending, puzzles, GA, save/load, achievements,
  fountains, edge bounds, py39 f-strings, and graphics builds. Every bug fix
  adds a regression check. Run it before every push; `bash -n install.sh`
  when touching the installer.

## Process

- Run `python3 tests/test_smoke.py` before every commit. It is fast (<30 s).
- One focused change per PR; describe verification in the PR body
  (what was probed, what was measured).
- Line-clear, kid-facing copy: short sentences, no jargon, friendly failure
  messages ("The fountain needs 4 Stone for a blessing").
- Never break save compatibility silently — bump `version` in
  `citadel/save.py` and let the load path fall back to a fresh realm with
  a notice for old files.
