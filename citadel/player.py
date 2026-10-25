"""Player avatar: tile-based movement over the voxel grid."""
from . import config


class Player:
    def __init__(self, world, col=8):
        self.col = int(col)
        self.row = world.surface_row(self.col) - 1
        self.wand_timer = 0.0
        self.charm_target = None
        self.charm_progress = 0.0

    def try_move(self, world, dcol):
        target = self.col + dcol
        if not world.in_bounds(self.row, target):
            return
        feet = world.get(self.row, target)
        head = world.get(self.row - 1, target)
        if feet == 0 and head == 0:
            self.col = target
        elif feet != 0 and head == 0 and world.get(self.row - 2, target) == 0:
            self.col = target
            self.row -= 1
        elif feet == 0 and world.get(self.row + 1, target) == 0:
            self.col = target
            self.row += 1
        self.row = max(0, min(world.rows - 1, self.row))

    def apply_gravity(self, world):
        below = world.get(self.row + 1, self.col)
        if below == 0:
            self.row = min(world.rows - 1, self.row + 1)

    def update(self, world, dt, move_dir):
        self.wand_timer = max(0.0, self.wand_timer - dt)
        if move_dir:
            self.try_move(world, move_dir)
        self.apply_gravity(world)
