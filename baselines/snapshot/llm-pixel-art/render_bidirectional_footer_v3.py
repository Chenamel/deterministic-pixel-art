#!/usr/bin/env python3
"""Generate the attached 22x10 three-state bidirectional settings footer."""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/bidirectional_settings_footer-v3.png"
WIDTH, CELL_HEIGHT, STATES = 22, 10, 3
TRANSPARENT = (0, 0, 0, 0)


def render_cell(state: int) -> Image.Image:
    image = Image.new("RGBA", (WIDTH, CELL_HEIGHT), TRANSPARENT)
    face = [(139, 139, 139, 255), (160, 160, 160, 255), (112, 112, 112, 255)][state]
    top = [(214, 214, 214, 255), (244, 244, 244, 255), (78, 78, 78, 255)][state]
    bottom = [(55, 55, 55, 255), (64, 64, 64, 255), (196, 196, 196, 255)][state]
    left = [(184, 184, 184, 255), (224, 224, 224, 255), (84, 84, 84, 255)][state]
    right = [(72, 72, 72, 255), (82, 82, 82, 255), (168, 168, 168, 255)][state]
    for x in range(1, WIDTH - 1):
        for y in range(1, CELL_HEIGHT - 1):
            image.putpixel((x, y), face)
    for x in range(WIDTH):
        image.putpixel((x, 0), top)
        image.putpixel((x, CELL_HEIGHT - 1), bottom)
    for y in range(CELL_HEIGHT):
        image.putpixel((0, y), left)
        image.putpixel((WIDTH - 1, y), right)
    triangle = [(92, 92, 92, 255), (194, 148, 50, 255), (58, 58, 58, 255)][state]
    for x in range(6, 16):
        for y in (3, 4):
            image.putpixel((x, y), triangle)
    for x in range(8, 14):
        for y in (5, 6):
            image.putpixel((x, y), triangle)
    for x in range(10, 12):
        for y in (7, 8):
            image.putpixel((x, y), triangle)
    return image


def main() -> None:
    image = Image.new("RGBA", (WIDTH, CELL_HEIGHT * STATES), TRANSPARENT)
    for state in range(STATES):
        image.paste(render_cell(state), (0, state * CELL_HEIGHT))
    assert image.size == (22, 30) and image.mode == "RGBA"
    for state in range(STATES):
        cell = image.crop((0, state * CELL_HEIGHT, WIDTH, (state + 1) * CELL_HEIGHT))
        assert all(cell.getpixel((x, y))[3] == 255 for x in range(WIDTH) for y in range(CELL_HEIGHT))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(f"OK {OUT} 22x30 RGBA")


if __name__ == "__main__":
    main()
