#!/usr/bin/env python3
"""Deterministically render blocked-cache workspace status icons."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/blocked_cache_status_icons.png"
CELL_SIZE = 16
CELL_COUNT = 3
TRANSPARENT = (0, 0, 0, 0)
DARK = (50, 50, 50, 255)
GRAY = (139, 139, 139, 255)
GRAY_DARK = (74, 74, 74, 255)
YELLOW = (215, 169, 61, 255)
YELLOW_BRIGHT = (244, 208, 106, 255)
YELLOW_DARK = (115, 82, 26, 255)
RED = (200, 91, 98, 255)
RED_BRIGHT = (233, 135, 141, 255)
RED_DARK = (108, 45, 49, 255)


def put(image: Image.Image, cell: int, x: int, y: int, color) -> None:
    image.putpixel((cell * CELL_SIZE + x, y), color)


def rect(image: Image.Image, cell: int, x0: int, y0: int, x1: int, y1: int, color) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(image, cell, x, y, color)


def draw_cache_grid(image: Image.Image) -> None:
    for row in range(3):
        for column in range(3):
            x = 2 + column * 4
            y = 2 + row * 4
            rect(image, 0, x, y, x + 2, y + 2, GRAY_DARK)
            put(image, 0, x + 1, y + 1, GRAY)


def draw_warning(image: Image.Image) -> None:
    widths = ((7, 8), (6, 9), (5, 10), (4, 11), (3, 12), (2, 13))
    for row, (left, right) in enumerate(widths, start=3):
        for x in range(left, right + 1):
            edge = x == left or x == right or row == 8
            put(image, 1, x, row, YELLOW_DARK if edge else YELLOW)
    rect(image, 1, 7, 5, 8, 6, DARK)
    rect(image, 1, 7, 7, 8, 7, YELLOW_BRIGHT)


def draw_stopped(image: Image.Image) -> None:
    for y in range(3, 12):
        for x in range(3, 12):
            if (x, y) in ((3, 3), (11, 3), (3, 11), (11, 11)):
                continue
            edge = x in (3, 11) or y in (3, 11) or x + y in (7, 21) or x - y in (-7, 7)
            put(image, 2, x, y, RED_DARK if edge else RED)
    rect(image, 2, 7, 5, 8, 8, DARK)
    rect(image, 2, 7, 9, 8, 10, RED_BRIGHT)


def render() -> Image.Image:
    image = Image.new("RGBA", (CELL_SIZE * CELL_COUNT, CELL_SIZE), TRANSPARENT)
    draw_cache_grid(image)
    draw_warning(image)
    draw_stopped(image)

    assert image.mode == "RGBA"
    assert image.size == (48, 16)
    assert set(pixel[3] for pixel in image.get_flattened_data()) <= {0, 255}
    for cell in range(CELL_COUNT):
        left = cell * CELL_SIZE
        assert all(image.getpixel((left, y)) == TRANSPARENT for y in range(CELL_SIZE))
        assert all(image.getpixel((left + 15, y)) == TRANSPARENT for y in range(CELL_SIZE))
        assert all(image.getpixel((x, 0)) == TRANSPARENT for x in range(left, left + CELL_SIZE))
        assert all(image.getpixel((x, 15)) == TRANSPARENT for x in range(left, left + CELL_SIZE))
        assert any(image.getpixel((x, y))[3] == 255
                   for x in range(left, left + CELL_SIZE) for y in range(CELL_SIZE))
    return image


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generated = render()
    generated.save(OUTPUT)
    print(f"OK {OUTPUT} {generated.mode} {generated.size[0]}x{generated.size[1]}")
