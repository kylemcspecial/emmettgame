import os
import sys
import time
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame

from citadel.main import Game

g = Game(headless=True, load=False)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

t0 = time.time()
frames = 0
try:
    while time.time() - t0 < 150:
        g.frame()
        frames += 1
except Exception:
    traceback.print_exc()
    print(f"CRASH at {time.time()-t0:.1f}s after {frames} frames")
    sys.exit(1)
print(f"survived {time.time()-t0:.1f}s, {frames} frames, still running={g.running}")
