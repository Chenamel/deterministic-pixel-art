#!/usr/bin/env python3
"""Generate the compact three-state bidirectional settings footer."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/bidirectional_settings_footer-v4.png"
WIDTH, CELL_HEIGHT, STATES = 22, 5, 3


def render_cell(state: int) -> Image.Image:
    image = Image.new("RGBA", (WIDTH, CELL_HEIGHT), (0, 0, 0, 255))
    face = [(144, 144, 144, 255), (160, 160, 160, 255), (112, 112, 112, 255)][state]
    edge = [(74, 74, 74, 255), (55, 55, 55, 255), (176, 176, 176, 255)][state]
    triangle = [(80, 80, 80, 255), (196, 148, 54, 255), (58, 58, 58, 255)][state]

    for x in range(1, WIDTH - 1):
        for y in range(1, CELL_HEIGHT - 1):
            image.putpixel((x, y), face)
    for x in range(WIDTH):
        image.putpixel((x, 0), edge)
        image.putpixel((x, CELL_HEIGHT - 1), edge)
    for y in range(CELL_HEIGHT):
        image.putpixel((0, y), edge)
        image.putpixel((WIDTH - 1, y), edge)

    # The legacy code-drawn silhouette: 8, 4, and 2 pixels on successive rows.
    for x in range(7, 15):
        image.putpixel((x, 1), triangle)
    for x in range(9, 13):
        image.putpixel((x, 2), triangle)
    for x in range(10, 12):
        image.putpixel((x, 3), triangle)
    return image


def main() -> None:
    image = Image.new("RGBA", (WIDTH, CELL_HEIGHT * STATES), (0, 0, 0, 0))
    for state in range(STATES):
        image.paste(render_cell(state), (0, state * CELL_HEIGHT))
    assert image.size == (22, 15) and image.mode == "RGBA"
    for state in range(STATES):
        cell = image.crop((0, state * CELL_HEIGHT, WIDTH, (state + 1) * CELL_HEIGHT))
        assert all(cell.getpixel((x, y))[3] == 255
                   for x in range(WIDTH) for y in range(CELL_HEIGHT))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(f"OK {OUT} 22x15 RGBA")


if __name__ == "__main__":
    main()
