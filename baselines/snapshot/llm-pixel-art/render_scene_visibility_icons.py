#!/usr/bin/env python3
"""Deterministically render the Nexus scene-visibility toggle icons."""

from pathlib import Path

from PIL import Image


CELL_SIZE = 16
CELL_COUNT = 4
OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/scene_visibility_icons.png"
)

TRANSPARENT = (0, 0, 0, 0)
DARK = (27, 27, 27, 255)
MID = (128, 128, 128, 255)
LIGHT = (232, 232, 232, 255)
BLUE = (102, 140, 208, 255)
BLUE_DARK = (38, 55, 89, 255)
RED = (206, 104, 115, 255)
RED_DARK = (85, 40, 45, 255)
LEGACY_RED = (227, 107, 107, 255)
GREEN = (109, 187, 120, 255)
OFF = (112, 112, 112, 255)


def rect(pixels, x0: int, y0: int, x1: int, y1: int, color) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            pixels[x, y] = color


def line(pixels, points, color) -> None:
    for x, y in points:
        pixels[x, y] = color


def square(pixels, x: int, y: int, size: int, fill) -> None:
    rect(pixels, x, y, x + size - 1, y + size - 1, DARK)
    if size > 2:
        rect(pixels, x + 1, y + 1, x + size - 2, y + size - 2, fill)


def slash(pixels, offset: int, outline_color, center_color) -> None:
    dark_points = []
    red_points = []
    for step in range(12):
        x = offset + 2 + step
        y = 13 - step
        dark_points.extend(((x, y - 1), (x, y), (x, y + 1)))
        red_points.append((x, y))
    line(pixels, dark_points, outline_color)
    line(pixels, red_points, center_color)


def draw_decal_icon(pixels, offset: int, enabled: bool) -> None:
    square(pixels, offset + 2, 2, 12, MID if enabled else OFF)
    rect(pixels, offset + 3, 3, offset + 12, 3, LIGHT if enabled else MID)
    rect(pixels, offset + 3, 3, offset + 3, 12, LIGHT if enabled else MID)
    if enabled:
        line(pixels, ((offset + 4, 7), (offset + 5, 7), (offset + 6, 7),
                      (offset + 6, 6), (offset + 6, 10), (offset + 6, 9),
                      (offset + 5, 9), (offset + 4, 9)), BLUE_DARK)
        line(pixels, ((offset + 8, 8), (offset + 6, 7), (offset + 6, 9)), BLUE)
        line(pixels, ((offset + 11, 6), (offset + 10, 6), (offset + 9, 6),
                      (offset + 9, 5), (offset + 9, 9), (offset + 9, 8),
                      (offset + 10, 8), (offset + 11, 8)), RED_DARK)
        line(pixels, ((offset + 7, 7), (offset + 9, 6), (offset + 9, 8)), RED)
    else:
        slash(pixels, offset, RED_DARK, RED)


def draw_neighbors_icon(pixels, offset: int, enabled: bool) -> None:
    satellite = GREEN if enabled else OFF
    center = LIGHT if enabled else MID
    square(pixels, offset + 6, 6, 4, center)
    for x, y in ((7, 0), (7, 14), (0, 7), (14, 7), (2, 2), (12, 12)):
        square(pixels, offset + x, y, 2, satellite)
    line(pixels, ((offset + 7, 4), (offset + 7, 5), (offset + 7, 10), (offset + 7, 11),
                  (offset + 4, 7), (offset + 5, 7), (offset + 10, 7), (offset + 11, 7),
                  (offset + 4, 4), (offset + 5, 5), (offset + 10, 10), (offset + 11, 11)),
         satellite)
    if not enabled:
        slash(pixels, offset, DARK, LEGACY_RED)


def main() -> None:
    image = Image.new("RGBA", (CELL_SIZE * CELL_COUNT, CELL_SIZE), TRANSPARENT)
    pixels = image.load()
    draw_decal_icon(pixels, 0, True)
    draw_decal_icon(pixels, CELL_SIZE, False)
    draw_neighbors_icon(pixels, CELL_SIZE * 2, True)
    draw_neighbors_icon(pixels, CELL_SIZE * 3, False)
    image.save(OUTPUT)

    with Image.open(OUTPUT) as generated:
        assert generated.mode == "RGBA"
        assert generated.size == (64, 16)
        assert set(pixel[3] for pixel in generated.get_flattened_data()) <= {0, 255}
        assert (224, 224, 255, 255) not in set(generated.get_flattened_data())
        for cell in range(CELL_COUNT):
            x0 = cell * CELL_SIZE
            assert generated.getpixel((x0, 0)) == TRANSPARENT
            assert generated.getpixel((x0 + 15, 15)) == TRANSPARENT
            assert any(generated.getpixel((x, y))[3] == 255
                       for x in range(x0, x0 + CELL_SIZE) for y in range(CELL_SIZE))

    print(f"OK {OUTPUT} {image.mode} {image.size[0]}x{image.size[1]}")


if __name__ == "__main__":
    main()
