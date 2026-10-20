#!/usr/bin/env python3
"""Deterministically render the colored 2D Nexus side-mode button atlas."""

from pathlib import Path

from PIL import Image


CELL_SIZE = 22
COLUMNS = 5
ROWS = 3
OUTER_BORDER = (0, 0, 0, 255)
OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/face_selector_mode_buttons-v2.png"
)

MODES = (
    ("disabled", "707070", "8B8B8B", "4A4A4A"),
    ("input", "405D92", "668CD0", "263759"),
    ("output", "8E424B", "CE6873", "55282D"),
    ("bidirectional", "74538E", "A57BBE", "442F54"),
    ("cache_release", "4F805B", "78B585", "2E4D36"),
)


def rgb(value: str) -> tuple[int, int, int, int]:
    return tuple(int(value[index:index + 2], 16) for index in range(0, 6, 2)) + (255,)


def blend_toward(source: tuple[int, int, int, int], target: tuple[int, int, int, int], amount: float) -> tuple[int, int, int, int]:
    return tuple(round(channel + (target[index] - channel) * amount) for index, channel in enumerate(source[:3])) + (255,)


def darken(color: tuple[int, int, int, int], amount: float) -> tuple[int, int, int, int]:
    return tuple(round(channel * (1.0 - amount)) for channel in color[:3]) + (255,)


def fill_rect(pixels, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            pixels[x, y] = color


def draw_cell(image: Image.Image, column: int, row: int, fill, top_left, bottom_right) -> None:
    pixels = image.load()
    x0 = column * CELL_SIZE
    y0 = row * CELL_SIZE

    fill_rect(pixels, x0, y0, x0 + CELL_SIZE - 1, y0 + CELL_SIZE - 1, OUTER_BORDER)
    fill_rect(pixels, x0 + 1, y0 + 1, x0 + 20, y0 + 20, fill)
    fill_rect(pixels, x0 + 1, y0 + 1, x0 + 20, y0 + 1, top_left)
    fill_rect(pixels, x0 + 1, y0 + 1, x0 + 1, y0 + 20, top_left)
    fill_rect(pixels, x0 + 1, y0 + 20, x0 + 20, y0 + 20, bottom_right)
    fill_rect(pixels, x0 + 20, y0 + 1, x0 + 20, y0 + 20, bottom_right)
    fill_rect(pixels, x0 + 3, y0 + 3, x0 + 18, y0 + 18, fill)


def assert_cell(image: Image.Image, column: int, row: int, fill, top_left, bottom_right) -> None:
    pixels = image.load()
    x0 = column * CELL_SIZE
    y0 = row * CELL_SIZE

    for offset in range(CELL_SIZE):
        assert pixels[x0 + offset, y0] == OUTER_BORDER
        assert pixels[x0 + offset, y0 + CELL_SIZE - 1] == OUTER_BORDER
        assert pixels[x0, y0 + offset] == OUTER_BORDER
        assert pixels[x0 + CELL_SIZE - 1, y0 + offset] == OUTER_BORDER
    assert pixels[x0 + 1, y0 + 1] == top_left
    assert pixels[x0 + 20, y0 + 20] == bottom_right
    for y in range(y0 + 3, y0 + 19):
        for x in range(x0 + 3, x0 + 19):
            assert pixels[x, y] == fill


def main() -> None:
    image = Image.new("RGBA", (COLUMNS * CELL_SIZE, ROWS * CELL_SIZE), OUTER_BORDER)
    for column, (_, fill_hex, top_left_hex, bottom_right_hex) in enumerate(MODES):
        fill = rgb(fill_hex)
        top_left = rgb(top_left_hex)
        bottom_right = rgb(bottom_right_hex)
        draw_cell(image, column, 0, fill, top_left, bottom_right)
        draw_cell(image, column, 1, blend_toward(fill, top_left, 0.25), top_left, bottom_right)
        draw_cell(image, column, 2, darken(fill, 0.30), bottom_right, top_left)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT)

    with Image.open(OUTPUT) as generated:
        assert generated.mode == "RGBA"
        assert generated.size == (110, 66)
        assert all(alpha == 255 for *_, alpha in generated.get_flattened_data())
        for column, (_, fill_hex, top_left_hex, bottom_right_hex) in enumerate(MODES):
            fill = rgb(fill_hex)
            top_left = rgb(top_left_hex)
            bottom_right = rgb(bottom_right_hex)
            assert_cell(generated, column, 0, fill, top_left, bottom_right)
            assert_cell(generated, column, 1, blend_toward(fill, top_left, 0.25), top_left, bottom_right)
            assert_cell(generated, column, 2, darken(fill, 0.30), bottom_right, top_left)

    print(f"OK {OUTPUT} {image.mode} {image.size[0]}x{image.size[1]}")


if __name__ == "__main__":
    main()
