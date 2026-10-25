#!/usr/bin/env python3
"""Launcher for Citadel of Friendship & Magic.

Installs a crash logger before the game starts: if anything goes wrong,
the full traceback is written to crash.log next to the game (and we try
to save the realm first so progress is never lost).
"""
import faulthandler
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CRASH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")


def main():
    faulthandler.enable()
    from citadel.main import Game

    game = None
    try:
        from citadel import config
        headless = "--headless" in sys.argv or not os.environ.get("DISPLAY")
        game = Game(headless=headless)
        game.run()
    except Exception:
        try:
            if game is not None and not game.headless:
                from citadel.save import save_game
                save_game(game)
        except Exception:
            pass
        with open(CRASH_LOG, "w") as f:
            f.write("The game hit an error and had to stop.\n")
            f.write("Please share this file with an adult :)\n\n")
            traceback.print_exc(file=f)
        raise


if __name__ == "__main__":
    main()
