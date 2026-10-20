#!/usr/bin/env python3
"""Render the deterministic bidirectional transport control atlas."""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/bidirectional_controls_v2.png"
CELL = 16
COUNT = 6
T = (0, 0, 0, 0)
DARK = (52, 44, 58, 255)
BLUE = (102, 140, 208, 255)
BLUE_DARK = (38, 55, 89, 255)
RED = (206, 104, 115, 255)
RED_DARK = (85, 40, 45, 255)
PURPLE = (165, 123, 190, 255)
GRAY = (139, 139, 139, 255)
GRAY_DARK = (74, 74, 74, 255)


def put(img, cell, points, color):
    for x, y in points:
        img.putpixel((cell * CELL + x, y), color)


def arrow(right=True):
    body = {(x, y) for x in range(4, 11) for y in (7, 8)} if right else {(x, y) for x in range(5, 12) for y in (7, 8)}
    head = ((10, range(5, 11)), (11, range(6, 10)), (12, range(7, 9))) if right else ((5, range(5, 11)), (4, range(6, 10)), (3, range(7, 9)))
    for x, ys in head:
        body.update((x, y) for y in ys)
    return body


def render():
    image = Image.new("RGBA", (CELL * COUNT, CELL), T)
    # Expand affordance: a compact downward triangle.
    put(image, 0, {(7, 6), (8, 6), (6, 7), (7, 7), (8, 7), (9, 7),
                    (5, 8), (6, 8), (7, 8), (8, 8), (9, 8), (10, 8)}, DARK)
    for cell, mask, body, outline in (
        (1, arrow(True), BLUE, BLUE_DARK),
        (2, arrow(True) | arrow(False), PURPLE, DARK),
        (3, arrow(False), RED, RED_DARK),
    ):
        for x, y in mask:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if (x + dx, y + dy) not in mask and 0 <= x + dx < CELL and 0 <= y + dy < CELL:
                    image.putpixel((cell * CELL + x + dx, y + dy), outline)
        put(image, cell, mask, body)
    # Return policy icons: a neutral broken loop and a warning loop.
    loop = {(5, 5), (6, 5), (7, 5), (8, 5), (9, 6), (9, 7), (8, 8), (7, 9), (6, 9), (5, 8), (5, 7)}
    put(image, 4, loop, GRAY)
    put(image, 5, loop, RED)
    put(image, 5, {(4, 10), (5, 11), (6, 12), (9, 4), (10, 5), (11, 6)}, RED_DARK)
    assert image.mode == "RGBA" and image.size == (96, 16)
    for cell in range(COUNT):
        x0 = cell * CELL
        assert all(image.getpixel((x0, y))[3] == 0 for y in range(CELL))
        assert all(image.getpixel((x0 + CELL - 1, y))[3] == 0 for y in range(CELL))
        assert all(image.getpixel((x, 0))[3] == 0 for x in range(x0, x0 + CELL))
        assert all(image.getpixel((x, CELL - 1))[3] == 0 for x in range(x0, x0 + CELL))
    assert all(pixel[3] in (0, 255) for pixel in image.getdata())
    assert not any(pixel[:3] == (255, 255, 255) for pixel in image.getdata())
    return image


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    render().save(OUTPUT)
    print(f"OK {OUTPUT}")
