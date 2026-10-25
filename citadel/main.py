"""Main game loop for Citadel of Friendship & Magic."""
import os
import sys

import numpy as np
import pygame

from . import config
from .castle import Castle
from .creatures import CreatureManager
from .genetics import GeneticTuner
from .graphics import Particles, Textures
from .inventory import BLOCK_TO_ITEM, DropManager, ITEMS
from .joystick import Gamepad
from .player import Player
from .pylons import FriendshipShield, PylonManager, Shadow
from .renderer import Renderer
from .save import load_game, save_game
from .settings import load_settings, save_settings
from .sounds import Sounds
from . import world as W


class Game:
    def __init__(self, headless=False, load=True):
        os.environ.setdefault(
            "SDL_VIDEODRIVER", "dummy" if headless else "x11"
        )
        pygame.init()
        self.headless = headless
        load_settings()
        if not headless and config.FULLSCREEN:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_W, config.SCREEN_H), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.big = pygame.font.Font(None, 44)
        self.small = pygame.font.Font(None, 22)
        self.rng = np.random.default_rng(config.RNG_SEED)
        self.sounds = Sounds()
        self._fresh_state()
        self.renderer = Renderer(
            self.screen, self.font, self.big, self.small, Textures()
        )
        self.world.on_change = self.renderer.mark_dirty
        self.particles = Particles()
        self.gamepad = Gamepad()
        self.gamepad.connect()
        self.mode = "title"         # title | play | puzzle | inventory | victory | hints
        self.message = ""
        self.message_t = 0.0
        self.active_pylon = None
        self.mouse_held = {"left": False, "right": False}
        self.breaking = None        # (row, col, progress)
        self._break_sound_tile = None
        self.day_t = 0.25
        self._title_button_rect = None
        self.naming = None            # creature being named
        self.naming_text = ""
        self.tips_shown = set()        # one-time contextual tips
        self.puzzle_fails = {}         # pylon id -> consecutive wrong clicks
        self.wand_beam = None          # (x0,y0,x1,y1,t)
        self.weather_t = 0.0
        self.running = True
        if load and not headless:
            from .save import has_save
            if has_save():
                try:
                    load_game(self)
                    self.notify("Welcome back! Your realm was restored.", 4)
                except Exception:
                    self._fresh_state()
                    self.notify(
                        "Your old realm could not be opened, so a brand-new "
                        "one was made just for you!", 5,
                    )
        else:
            self.notify(
                "Welcome, wizard! A/D to walk, W to jump. Cast your wand "
                "(left click) at creatures to make friends!", 6,
            )

    def shutdown(self):
        try:
            if not self.headless:
                save_game(self)
                save_settings()
        except Exception:
            pass
        self.running = False

    def _fresh_state(self):
        self.castle = Castle(col=config.WORLD_COLS // 2)
        self.world = W.World(self.rng, castle_col=self.castle.col)
        self.ga = GeneticTuner(self.rng)
        self.player = Player(self.world, col=8)
        self.inventory = self._make_inventory()
        self.creatures = CreatureManager(self.rng, self.world, self.ga)
        self.pylons = PylonManager(self.rng, self.world, self.ga)
        self.shadow = Shadow(col=3)
        self.shield = FriendshipShield()
        self.drops = DropManager(self.rng, self.sounds)

    def _make_inventory(self):
        from .inventory import Inventory
        inv = Inventory()
        return inv

    def notify(self, text, t=3.0):
        self.message = text
        self.message_t = t

    # ---------------- input ----------------

    def _start_play(self):
        self.mode = "play"
        self.sounds.start_music()
        if "intro" not in self.tips_shown:
            self.tips_shown.add("intro")
            self.notify(
                "Welcome, wizard! A/D to walk, W to jump. Cast your wand "
                "(left click) at creatures to make friends!", 7,
            )
            if not self.shadow.banished:
                self.tips_shown.add("shadow_intro")
                self.notify(
                    "Something dark watches from afar... only warmth and "
                    "friendship will push it away.", 8,
                )
        else:
            self.notify("Welcome back to your realm!", 4)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.shutdown()
            return
        if event.type == pygame.KEYDOWN:
            if self.naming is not None:
                if event.key == pygame.K_RETURN:
                    if self.naming_text.strip():
                        self.naming.name = self.naming_text.strip()[:14]
                        self.sounds.play("friend")
                        self.notify(f"{self.naming.name} loves their new name!")
                    self.naming = None
                    self.naming_text = ""
                elif event.key == pygame.K_ESCAPE:
                    self.naming = None
                    self.naming_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.naming_text = self.naming_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self.naming_text = (self.naming_text + event.unicode)[:14]
                return
            if event.key == pygame.K_ESCAPE:
                if self.mode in ("puzzle", "inventory"):
                    self.mode = "play"
                else:
                    self.shutdown()
                return
            if event.key == pygame.K_e:
                if self.mode == "play":
                    self.mode = "inventory"
                elif self.mode == "inventory":
                    self.mode = "play"
                return
            if event.key == pygame.K_h and self.mode in ("play", "hints"):
                self.mode = "play" if self.mode == "hints" else "hints"
                return
            if self.mode == "title":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                 pygame.K_KP_ENTER):
                    self._start_play()
                elif event.key == pygame.K_ESCAPE:
                    self.shutdown()
                return
            if self.mode == "hints":
                if event.key in (pygame.K_h, pygame.K_ESCAPE,
                                pygame.K_RETURN):
                    self.mode = "play"
                return
            if event.key == pygame.K_n and self.mode == "play":
                c = self.creatures.nearest(self.player.x, self.player.y,
                                           max_dist=config.TILE * 4)
                if c is not None and c.befriended:
                    self.naming = c
                    self.naming_text = c.name or ""
                    self.notify(f"Type a name for your {c.species} friend, "
                                "then press Enter!", 4)
                return
            if self.mode != "play":
                if event.key == pygame.K_r and self.mode == "victory":
                    self.reset()
                return
            if pygame.K_1 <= event.key <= pygame.K_9:
                self.inventory.select(event.key - pygame.K_0)
            elif event.key == pygame.K_F5:
                path = save_game(self)
                self.notify(f"Realm saved to {os.path.basename(path)}")
            elif event.key == pygame.K_F6:
                config.PERFORMANCE_MODE = not config.PERFORMANCE_MODE
                self.notify(
                    "Performance mode ON - fancy effects off." if
                    config.PERFORMANCE_MODE else
                    "Performance mode OFF - fancy effects back on!")
            elif event.key == pygame.K_F7:
                config.SHOW_FPS = not config.SHOW_FPS
            elif event.key == pygame.K_F11:
                config.FULLSCREEN = not config.FULLSCREEN
                if not self.headless:
                    flags = pygame.FULLSCREEN if config.FULLSCREEN else 0
                    self.screen = pygame.display.set_mode(
                        (config.SCREEN_W, config.SCREEN_H), flags)
                    self.renderer.screen = self.screen
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                self.sounds.set_volume(config.VOLUME + 0.1)
                self.notify(f"Volume {int(config.VOLUME * 100)}%")
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                self.sounds.set_volume(config.VOLUME - 0.1)
                self.notify(f"Volume {int(config.VOLUME * 100)}%")
            elif event.key == pygame.K_F12:
                path = f"citadel-photo-{int(pygame.time.get_ticks() / 1000)}.png"
                try:
                    pygame.image.save(self.screen, path)
                    self.notify(f"Photo saved: {path}!")
                except Exception:
                    self.notify("Could not save the photo, sorry!")
        elif event.type == pygame.MOUSEWHEEL:
            if self.mode == "play":
                self.inventory.cycle(1 if event.y > 0 else -1)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.mode == "title" and event.button == 1:
                if self._title_button_rect and \
                        self._title_button_rect.collidepoint(event.pos):
                    self._start_play()
                return
            if self.mode == "hints" and event.button == 1:
                self.mode = "play"
                return
            if self.mode == "puzzle" and event.button == 1:
                self._puzzle_click(event.pos)
            elif self.mode == "inventory" and event.button in (1, 3):
                self._backpack_click(event.pos, event.button)
            elif self.mode == "play":
                if event.button == 1:
                    self.mouse_held["left"] = True
                elif event.button == 3:
                    self.mouse_held["right"] = True
                    self._right_action(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_held["left"] = False
                self.breaking = None
                self._break_sound_tile = None
            elif event.button == 3:
                self.mouse_held["right"] = False
        elif event.type == pygame.JOYBUTTONDOWN:
            self._joypad_button(event.button)
        elif event.type == pygame.JOYDEVICEADDED:
            if not self.gamepad.enabled and self.gamepad.connect():
                self.notify("Gamepad connected! Left stick to move, "
                             "A to jump, B to cast your wand.", 4)

    def _joypad_button(self, button):
        if self.mode == "inventory":
            if button in (9, 1):
                self.mode = "play"
            return
        if self.mode == "puzzle":
            return
        if self.mode == "victory":
            if button == 0:
                self.reset()
            return
        if button == 0:
            self.player.update(self.world, 0, 0, True)
        elif button == 1:
            self._left_action(pygame.mouse.get_pos())
        elif button == 2:
            self._right_action(pygame.mouse.get_pos())
        elif button in (4, 5):
            self.inventory.cycle(1 if button == 5 else -1)
        elif button == 9:
            self.mode = "inventory"

    def _puzzle_click(self, pos):
        if not self.active_pylon:
            return
        for rune, rect in self.renderer.rune_rects.items():
            if rect.collidepoint(pos):
                result = self.active_pylon.click_rune(rune)
                if result == "solved":
                    self.sounds.play("pylon")
                    self.notify("The pylon hums with warm light!")
                    self.mode = "play"
                    solved = self.active_pylon
                    self.active_pylon = None
                    self.shield.add_harmony(15, self.ga)
                    self.ga.record_event("pylon", 10.0)
                    nxt = self.pylons.on_restored(solved)
                    if nxt is not None:
                        side = "right" if nxt.x >= self.player.x else "left"
                        dist = int(abs(nxt.x - self.player.x) // config.TILE)
                        self.notify(
                            f"A new pylon has awakened {dist} steps to your "
                            f"{side}!", 5,
                        )
                elif result == "correct":
                    self.notify("The energy flows... keep going!")
                    self.sounds.play("puzzle_ok")
                else:
                    self.notify("The runes dim. Feel the energy and try again.")
                    self.sounds.play("puzzle_bad")
                    pid = self.active_pylon.pid
                    self.puzzle_fails[pid] = self.puzzle_fails.get(pid, 0) + 1
                    if self.puzzle_fails[pid] == 2:
                        first = self.active_pylon.target_seq[0]
                        self.notify(
                            f"The runes whisper... try {first} first...", 5,
                        )
                return

    def _backpack_click(self, pos, button=1):
        if button == 3:
            for (r, c), rect in self.renderer.backpack_rects.items():
                if rect.collidepoint(pos):
                    if r == 3:
                        item, count = self.inventory.hotbar[c]
                        if item and self.inventory.to_backpack(0, c):
                            self.notify(f"Moved {ITEMS[item][0]} to backpack.")
                    return
        for (r, c), rect in self.renderer.backpack_rects.items():
            if rect.collidepoint(pos):
                item, count = self.inventory.backpack[r][c]
                if item:
                    if self.inventory.add(item, count):
                        self.inventory.backpack[r][c] = (None, None)
                        self.notify(f"Moved {ITEMS[item][0]} to hotbar.")
                return

    def _aim_tile(self, pos):
        return self.renderer.cam.world_tile(*pos)

    def _in_reach(self, row, col):
        prow, pcol = self.player.tile()
        return abs(row - prow) <= config.REACH and abs(col - pcol) <= config.REACH

    def _left_action(self, pos):
        row, col = self._aim_tile(pos)
        if not self._in_reach(row, col):
            return
        held_item, _ = self.inventory.current_item()
        if held_item == "wand":
            creature = self.creatures.nearest(
                col * config.TILE + config.TILE / 2,
                row * config.TILE + config.TILE / 2,
            )
            if creature is not None:
                self._cast_wand(creature)
                return
            pylon = self.pylons.near(
                self.player.x, self.player.y, dist=config.TILE * 6
            )
            if pylon is not None and not pylon.restored:
                self.active_pylon = pylon
                self.mode = "puzzle"
                self.notify("Ancient pylon awakened! Align the runes.")
                return
            if self.world.get(row, col) == W.THORNS:
                self.world.set(row, col, W.AIR)
                self.particles.emit(
                    (col + 0.5) * config.TILE, (row + 0.5) * config.TILE,
                    (150, 90, 180), 14,
                )
                self.shield.add_harmony(1.5, self.ga)
                self.notify("Dark thorns cleared by wand light!")
                return
        block = self.world.get(row, col)
        if block in W.BREAKABLE:
            if self._break_sound_tile != (row, col):
                self.sounds.play("break")
                self._break_sound_tile = (row, col)
            self.breaking = [row, col, 0.0]

    def _cast_wand(self, creature):
        if self.player.wand_timer > 0 or creature.befriended:
            return
        self.player.wand_timer = config.WAND_COOLDOWN
        self.particles.emit(creature.x, creature.y, creature.color, 16)
        self.wand_beam = (self.player.x, self.player.y - 8,
                          creature.x, creature.y, 0.25)
        self.sounds.play("wand")
        done = creature.advance_charm()
        if done:
            self.creatures.befriend(creature, self.castle.x)
            self.shield.add_harmony(10, self.ga)
            self.ga.record_event("charm", 8.0)
            self.notify(f"{creature.species} befriended! It will guard your citadel.")
        else:
            self.notify(
                f"Charming {creature.species}... "
                f"{creature.max_hearts - creature.hearts + 1}"
                f"/{creature.max_hearts}"
            )

    def _right_action(self, pos):
        row, col = self._aim_tile(pos)
        held_item, _ = self.inventory.current_item()
        creature = self.creatures.nearest(
            pos[0] + self.renderer.cam.x, pos[1] + self.renderer.cam.y,
            max_dist=config.TILE * 3,
        )
        if creature is not None and not creature.befriended:
            if self.inventory.count("berry") > 0:
                if self.inventory.consume("berry", 1):
                    self.particles.emit(creature.x, creature.y, (255, 120, 140), 10)
                    creature.hearts = max(0, creature.hearts - 1)
                    self.shield.add_harmony(config.BERRY_FEED_HARMONY * 0.5, self.ga)
                    self.notify(f"{creature.species} loves Sunberries!")
                    self.sounds.play("feed")
                    if creature.hearts == 0:
                        self.creatures.befriend(creature, self.castle.x)
                        self.shield.add_harmony(6, self.ga)
                        self.notify(f"{creature.species} befriended!")
                        self.sounds.play("friend")
                    return
        if held_item == "rune_key":
            pylon = self.pylons.near(
                pos[0] + self.renderer.cam.x,
                pos[1] + self.renderer.cam.y,
                dist=config.TILE * 5,
            )
            if pylon is not None and not pylon.restored:
                if self.inventory.consume("rune_key", 1):
                    pylon.progress = min(pylon.progress + 1,
                                          len(pylon.target_seq))
                    self.particles.emit(pylon.x, pylon.y, (200, 140, 255), 16)
                    self.notify("The Rune Key lights a rune for you!")
                    self.sounds.play("key")
                    if pylon.progress >= len(pylon.target_seq):
                        pylon.restored = True
                        pylon.shield_radius = 1.0
                        self.shield.add_harmony(15, self.ga)
                        self.notify("The pylon hums with warm light!")
                        self.sounds.play("pylon")
                        nxt = self.pylons.on_restored(pylon)
                        if nxt is not None:
                            self.notify("A new pylon has awakened somewhere "
                                        "in the realm!", 5)
                return
        if held_item == "catalyst":
            if self.inventory.consume("catalyst", 1):
                self.shield.add_harmony(12, self.ga)
                self.particles.emit(self.player.x, self.player.y,
                                    (170, 130, 255), 24, speed=90)
                self.notify("The catalyst bursts into warm light! Harmony +12")
                self.sounds.play("catalyst")
            return
        if not self._in_reach(row, col):
            return
        block = self.inventory.current_placeable_block()
        if block is not None and self.world.place_block(row, col, block):
            self.inventory.consume_selected()
            self.sounds.play("place")
            gain = self.castle.register_block(
                row, col, block, self.creatures.creatures, self.ga
            )
            if gain:
                self.shield.add_harmony(gain, self.ga)
                if "castle_site" not in self.tips_shown:
                    self.tips_shown.add("castle_site")
                    self.notify(
                        "This is your citadel! Every block you place here "
                        "adds warmth - and warmth keeps the Shadow away.", 6,
                    )
            self.particles.emit(
                (col + 0.5) * config.TILE, (row + 0.5) * config.TILE,
                (220, 220, 210), 6, speed=30,
            )

    def reset(self):
        self.rng = np.random.default_rng(config.RNG_SEED + int(self.rng.integers(0, 99999)))
        self._fresh_state()
        self.world.on_change = self.renderer.mark_dirty
        self.renderer._world_surf = None
        self.mode = "play"
        self.active_pylon = None
        self.notify("A brand-new realm shimmers into being...", 4)

    # ---------------- update ----------------

    def update(self, dt):
        self.day_t = (self.day_t + dt / config.DAY_LENGTH) % 1.0
        if self.wand_beam is not None:
            x0, y0, x1, y1, t = self.wand_beam
            t -= dt
            self.wand_beam = (x0, y0, x1, y1, t) if t > 0 else None
        self.weather_t += dt
        if self.message_t > 0:
            self.message_t -= dt
            if self.message_t <= 0:
                self.message = ""
        if self.mode == "victory":
            return
        keys = pygame.key.get_pressed()
        axis = 0
        if self.mode in ("title", "hints"):
            return
        if self.naming is not None:
            return
        if self.mode == "play":
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                axis -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                axis += 1
        jump = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        pad_axis, pad_jump = self.gamepad.poll() or (0, False)
        if pad_axis:
            axis = pad_axis
        jump = jump or pad_jump
        if jump and self.player.on_ground and self.mode == "play":
            self.sounds.play("jump")
        self.player.update(self.world, dt, axis, jump)
        self.creatures.update(self.world, dt, self.player.x)
        self.pylons.update(dt)
        self.world.update(dt)
        self.drops.update(dt, self.player, self.inventory)
        self.particles.update(dt)
        restored = len(self.pylons.pylons) - len(self.pylons.unrestored())
        strength = self.shield.strength(len(self.pylons.pylons), restored)
        drain = self.shadow.update(dt, strength, self.player.x, self.ga,
                                   self.shield.harmony)
        if drain:
            self.shield.drain(drain)
            if int(self.clock.get_time()) % 120 == 0:
                self.notify("The Shadow saps warmth... restore pylons and build harmony!", 2)
        if self.shadow.banished and self.mode != "victory":
            self.mode = "victory"
            self.sounds.play("victory")
        if self.mouse_held["left"] and self.mode == "play":
            pos = pygame.mouse.get_pos()
            row, col = self._aim_tile(pos)
            if self.breaking and self.breaking[0] == row and self.breaking[1] == col:
                self.breaking[2] += dt
                if self.breaking[2] >= config.BREAK_TIME:
                    self._finish_break(row, col)
            else:
                self.breaking = None
                held_item, _ = self.inventory.current_item()
                if held_item != "wand":
                    self._left_action(pos)

    def _finish_break(self, row, col):
        self.breaking = None
        block = self.world.get(row, col)
        block_col = W.BLOCKS.get(block, ("", (200, 200, 190)))[1]
        drop, n = self.world.break_block(row, col)
        if drop:
            if drop in BLOCK_TO_ITEM:
                drop = BLOCK_TO_ITEM[drop]
            self.drops.spawn(
                drop, (col + 0.5) * config.TILE, (row + 0.5) * config.TILE, n
            )
            self.particles.emit(
                (col + 0.5) * config.TILE, (row + 0.5) * config.TILE,
                block_col, 10, speed=50,
            )
            if drop == "berry":
                self.world.schedule_regrowth(row, col, W.BERRY_BUSH)
            self.shield.add_harmony(0.2, self.ga)

    # ---------------- draw ----------------

    def draw(self):
        r = self.renderer
        r.cam.follow(self.player.x, self.player.y, 1 / config.FPS)
        if self.mode == "title":
            r.draw_world(self.world, self.day_t)
            r.draw_creatures(self.creatures.creatures)
            r.draw_castle_banner(self.castle, self.world)
            r.draw_title(self._title_button_rect is None)
            self._title_button_rect = r.title_button_rect
            pygame.display.flip()
            return
        if self.mode == "hints":
            r.draw_world(self.world, self.day_t)
            r.draw_hints()
            pygame.display.flip()
            return
        glow = []
        night = np.sin((self.day_t - 0.25) * 2 * np.pi) > 0
        for p in self.pylons.pylons:
            if p.restored:
                glow.append((p.x, p.y, (255, 214, 92),
                              3 * config.TILE))
        if not config.PERFORMANCE_MODE:
            cam0 = int(self.renderer.cam.x // config.TILE) - 1
            cam1 = cam0 + config.SCREEN_W // config.TILE + 3
            row0 = int(self.renderer.cam.y // config.TILE) - 1
            row1 = row0 + config.SCREEN_H // config.TILE + 3
            row0 = max(0, row0)
            row1 = min(self.world.rows, row1)
            for cc in range(cam0, cam1):
                for rr in range(row0, row1):
                    b = self.world.get(rr, cc)
                    if b in (W.CRYSTAL, W.STARLIGHT, W.RUNE_KEY_BLOCK,
                             W.CATALYST_BLOOM):
                        col = ((120, 220, 255) if b == W.CRYSTAL else
                               (255, 240, 160) if b == W.STARLIGHT else
                               (200, 140, 255) if b == W.RUNE_KEY_BLOCK else
                               (170, 130, 255))
                        glow.append(((cc + 0.5) * config.TILE,
                                     (rr + 0.5) * config.TILE, col,
                                     int(config.TILE * 1.5)))
        r.draw_world(self.world, self.day_t, glow)
        r.draw_castle_banner(self.castle, self.world)
        r.draw_pylons(self.pylons.pylons)
        r.draw_drops(self.drops.drops)
        r.draw_creatures(self.creatures.creatures)
        r.draw_shadow(self.shadow)
        r.draw_player(self.player)
        r.draw_weather(self.weather_t, self.day_t)
        self.particles.draw(self.screen, r.cam)
        if self.mode == "play":
            pos = pygame.mouse.get_pos()
            row, col = self._aim_tile(pos)
            r.highlight_tile(row, col, self._in_reach(row, col))
            if self.breaking:
                r.draw_break_crack(self.breaking[0], self.breaking[1],
                                    self.breaking[2] / config.BREAK_TIME)
        if self.wand_beam is not None:
            r.draw_wand_beam(*self.wand_beam)
        if self.mode in ("play", "puzzle", "inventory"):
            r.draw_hud(self)
            r.draw_quests(self)
            if config.SHOW_FPS:
                fps = self.font.render(
                    f"{self.clock.get_fps():.0f} FPS", True,
                    (255, 255, 255))
                self.screen.blit(fps, (config.SCREEN_W - 80,
                                       config.SCREEN_H - 90))
        r.draw_message(self.message if self.message_t > 0 else "")
        if self.naming is not None:
            r.draw_naming(self.naming_text)
        if self.mode == "puzzle" and self.active_pylon:
            r.draw_puzzle(self.active_pylon)
        elif self.mode == "inventory":
            r.draw_inventory_screen(self)
        elif self.mode == "victory":
            r.draw_victory()
        pygame.display.flip()

    def frame(self):
        dt = self.clock.tick(config.FPS) / 1000.0
        for event in pygame.event.get():
            self.handle_event(event)
        self.update(dt)
        self.draw()
        return self.running

    def run(self, max_frames=None):
        frames = 0
        while self.running:
            self.frame()
            frames += 1
            if max_frames and frames >= max_frames:
                break
        pygame.quit()


def main():
    headless = "--headless" in sys.argv or not os.environ.get("DISPLAY")
    game = Game(headless=headless)
    game.run()


if __name__ == "__main__":
    main()
