"""Player with platformer physics and an aim cursor."""
from . import config


class Player:
    def __init__(self, world, col=8):
        self.x = (col + 0.5) * config.TILE
        self.y = world.surface_row(col) * config.TILE - config.TILE * 0.75 + 0.01
        self.vx = 0.0
        self.vy = 0.0
        self.w = config.TILE * 0.6
        self.h = config.TILE * 1.5
        self.on_ground = False
        self.facing = 1
        self.wand_timer = 0.0
        self.mining = None       # (row, col, progress)
        self.wand_timer = 0.0

    def rect(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)

    def _collides(self, world, x, y):
        r0 = int((y - self.h / 2) / config.TILE)
        r1 = int((y + self.h / 2) / config.TILE)
        c0 = int((x - self.w / 2) / config.TILE)
        c1 = int((x + self.w / 2) / config.TILE)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if world.is_solid(r, c):
                    return True
        return False

    def update(self, world, dt, move_axis, jump):
        self.wand_timer = max(0.0, self.wand_timer - dt)
        self.vx = move_axis * config.MOVE_SPEED
        if move_axis:
            self.facing = move_axis
        self.vy = min(config.MAX_FALL, self.vy + config.GRAVITY * dt)
        if jump and self.on_ground:
            self.vy = config.JUMP_VELOCITY
        steps = max(1, int(max(abs(self.vx), abs(self.vy)) * dt / (config.TILE / 2)) + 1)
        sdt = dt / steps
        for _ in range(steps):
            self._step(world, sdt)

    def _step(self, world, dt):
        dx = self.vx * dt
        if not self._collides(world, self.x + dx, self.y):
            self.x += dx
        dy = self.vy * dt
        if not self._collides(world, self.x, self.y + dy):
            self.y += dy
            if dy > 0:
                self.on_ground = False
        else:
            if self.vy > 0:
                foot_row = int((self.y + dy + self.h / 2) / config.TILE)
                self.y = foot_row * config.TILE - self.h / 2 - 0.01
                self.on_ground = True
            elif self.vy < 0:
                head_row = int((self.y + dy - self.h / 2) / config.TILE)
                self.y = (head_row + 1) * config.TILE + self.h / 2 + 0.01
            self.vy = 0.0
        self.x = max(self.w / 2, min(world.cols * config.TILE - self.w / 2, self.x))

    def tile(self):
        return int(self.y // config.TILE), int(self.x // config.TILE)

    def center(self):
        return self.x, self.y
