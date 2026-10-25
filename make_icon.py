#!/usr/bin/env python3
"""Generate the game's desktop icon (no image assets needed in the repo).

Only uses pygame's draw primitives so it works before any game code runs.
Usage: python3 make_icon.py [output.png]
"""
import sys

import pygame

SIZE = 256


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "citadel-icon.png"
    pygame.init()
    surf = pygame.Surface((SIZE, SIZE))
    cx = SIZE // 2

    # Rounded sky background
    surf.fill((110, 150, 220))
    pygame.draw.circle(surf, (255, 250, 200), (SIZE - 60, 56), 30)  # sun

    # Grass base
    pygame.draw.rect(surf, (100, 175, 85), (0, SIZE - 46, SIZE, 46))

    # Castle towers
    for tx, tw in ((44, 44), (168, 44)):
        pygame.draw.rect(surf, (232, 232, 238), (tx, 92, tw, SIZE - 92))
        pygame.draw.polygon(surf, (255, 120, 110), [
            (tx - 6, 92), (tx + tw + 6, 92), (tx + tw // 2, 44),
        ])
        pygame.draw.rect(surf, (90, 70, 120), (tx + tw // 2 - 6, 120, 12, 22))
    # Castle wall + gate
    pygame.draw.rect(surf, (210, 205, 195), (88, 140, 80, SIZE - 140))
    pygame.draw.arc(surf, (120, 80, 60), (110, SIZE - 76, 36, 40), 3.14, 0, 0)
    pygame.draw.rect(surf, (120, 80, 60), (110, SIZE - 70, 36, 30))

    # Magic wand spark
    pygame.draw.line(surf, (150, 100, 60), (56, 210), (96, 158), 7)
    for i, r in enumerate((16, 11, 7)):
        pygame.draw.circle(
            surf, (255, 220, 90) if i % 2 == 0 else (255, 250, 180),
            (100, 152), r,
        )

    # Friendly creature peeking by the gate
    pygame.draw.circle(surf, (255, 170, 120), (150, SIZE - 52), 16)
    pygame.draw.circle(surf, (255, 255, 255), (145, SIZE - 56), 3)
    pygame.draw.circle(surf, (255, 255, 255), (156, SIZE - 56), 3)
    pygame.draw.circle(surf, (40, 40, 60), (145, SIZE - 56), 1)
    pygame.draw.circle(surf, (40, 40, 60), (156, SIZE - 56), 1)

    pygame.image.save(surf, out)
    print(f"Icon written to {out}")


if __name__ == "__main__":
    main()
