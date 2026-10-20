#!/usr/bin/env python3
"""Render the small modal close icon and revised return-policy glyphs."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TEXTURE_DIR = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus"
CONTROLS_SOURCE = TEXTURE_DIR / "bidirectional_controls_v2.png"
CONTROLS_OUTPUT = TEXTURE_DIR / "bidirectional_controls_v3.png"
CLOSE_OUTPUT = TEXTURE_DIR / "bidirectional_close-v2.png"
CELL = 16
TRANSPARENT = (0, 0, 0, 0)
GRAY = (139, 139, 139, 255)
GRAY_DARK = (74, 74, 74, 255)
HOVER = (224, 190, 73, 255)
HOVER_DARK = (91, 72, 24, 255)
RED = (206, 104, 115, 255)
RED_DARK = (85, 40, 45, 255)


def put(image, cell, points, color):
    for x, y in points:
        image.putpixel((cell * CELL + x, y), color)


def loop_arrow():
    """A compact clockwise loop with two clear arrowheads."""
    return {
        (5, 5), (6, 4), (7, 4), (8, 5), (9, 6), (9, 7),
        (8, 8), (7, 9), (6, 9), (5, 8), (5, 7), (6, 6),
        (4, 5), (5, 5), (4, 6),
        (9, 9), (10, 9), (10, 8),
    }


def outline(mask, color):
    result = set()
    for x, y in mask:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (x + dx, y + dy)
            if point not in mask and 0 < point[0] < CELL - 1 and 0 < point[1] < CELL - 1:
                result.add(point)
    return result, color


def render_controls():
    source = Image.open(CONTROLS_SOURCE).convert("RGBA")
    assert source.size == (96, 16)
    image = source.copy()
    for cell in (4, 5):
        for x in range(CELL):
            for y in range(CELL):
                image.putpixel((cell * CELL + x, y), TRANSPARENT)
    loop = loop_arrow()
    loop_outline, _ = outline(loop, GRAY_DARK)
    put(image, 4, loop_outline, GRAY_DARK)
    put(image, 4, loop, GRAY)
    put(image, 5, loop_outline, RED_DARK)
    put(image, 5, loop, RED)
    slash = {(3, 11), (4, 10), (5, 9), (6, 8), (7, 7), (8, 6), (9, 5), (10, 4), (11, 3)}
    put(image, 5, slash, RED_DARK)
    assert image.size == (96, 16) and image.mode == "RGBA"
    return image


def render_close():
    image = Image.new("RGBA", (CELL, CELL * 2), TRANSPARENT)
    normal = {(5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9),
              (10, 4), (9, 5), (8, 6), (7, 7), (6, 8), (5, 9)}
    hover = {(5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9),
             (10, 4), (9, 5), (8, 6), (7, 7), (6, 8), (5, 9)}
    for x, y in normal:
        image.putpixel((x, y), GRAY_DARK)
    for x, y in hover:
        image.putpixel((x, CELL + y), HOVER_DARK)
    for x, y in {(6, 4), (7, 5), (8, 6), (9, 7), (9, 4), (8, 5), (7, 6), (6, 7)}:
        image.putpixel((x, y), GRAY)
    for x, y in {(6, 4), (7, 5), (8, 6), (9, 7), (9, 4), (8, 5), (7, 6), (6, 7)}:
        image.putpixel((x, CELL + y), HOVER)
    assert image.size == (16, 32) and image.mode == "RGBA"
    return image


def assert_transparent_edges(image, cell_count, cell_height=16):
    for cell in range(cell_count):
        x0 = cell * CELL
        for y in range(cell_height):
            assert image.getpixel((x0, y))[3] == 0
            assert image.getpixel((x0 + CELL - 1, y))[3] == 0
        for x in range(x0, x0 + CELL):
            assert image.getpixel((x, 0))[3] == 0
            assert image.getpixel((x, cell_height - 1))[3] == 0


if __name__ == "__main__":
    CONTROLS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    controls = render_controls()
    close = render_close()
    assert_transparent_edges(controls, 6)
    assert_transparent_edges(close, 1, 16)
    assert_transparent_edges(close.crop((0, 16, 16, 32)), 1, 16)
    controls.save(CONTROLS_OUTPUT)
    close.save(CLOSE_OUTPUT)
    print(f"OK {CONTROLS_OUTPUT}")
    print(f"OK {CLOSE_OUTPUT}")
