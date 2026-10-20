#!/usr/bin/env python3
"""Generate the compact close button and MC-style footer states deterministically."""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus"
TRANSPARENT = (0, 0, 0, 0)


def button(width: int, height: int, state: int) -> Image.Image:
    image = Image.new("RGBA", (width, height), TRANSPARENT)
    face = [(198, 198, 198, 255), (214, 214, 214, 255), (174, 174, 174, 255)][state]
    light = [(232, 232, 232, 255), (250, 250, 250, 255), (126, 126, 126, 255)][state]
    dark = [(70, 70, 70, 255), (78, 78, 78, 255), (48, 48, 48, 255)][state]
    for x in range(1, width - 1):
        for y in range(1, height - 1):
            image.putpixel((x, y), face)
    for x in range(1, width - 1):
        image.putpixel((x, 1), light)
        image.putpixel((x, height - 2), dark)
    for y in range(1, height - 1):
        image.putpixel((1, y), light)
        image.putpixel((width - 2, y), dark)
    color = (82, 82, 82, 255) if state != 1 else (116, 86, 34, 255)
    for px, py in ((4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9), (11, 10),
                   (11, 3), (10, 4), (9, 5), (8, 6), (7, 7), (6, 8), (5, 9), (4, 10)):
        if px < width - 1 and py < height - 1:
            image.putpixel((px, py), color)
    return image


def footer(state: int) -> Image.Image:
    image = Image.new("RGBA", (22, 5), TRANSPARENT)
    face = [(139, 139, 139, 255), (160, 160, 160, 255), (112, 112, 112, 255)][state]
    top = [(184, 184, 184, 255), (220, 220, 220, 255), (82, 82, 82, 255)][state]
    bottom = [(58, 58, 58, 255), (76, 76, 76, 255), (176, 176, 176, 255)][state]
    for x in range(1, 21):
        image.putpixel((x, 1), top)
        image.putpixel((x, 2), face)
        image.putpixel((x, 3), bottom)
    triangle = [(92, 92, 92, 255), (196, 148, 54, 255), (58, 58, 58, 255)][state]
    for x in range(7, 15):
        image.putpixel((x, 1), triangle)
    for x in range(9, 13):
        image.putpixel((x, 2), triangle)
    for x in range(10, 12):
        image.putpixel((x, 3), triangle)
    return image


def assert_cell_edges(image: Image.Image, width: int, height: int, count: int) -> None:
    assert image.mode == "RGBA"
    for state in range(count):
        cell = image.crop((0, state * height, width, (state + 1) * height))
        assert all(cell.getpixel((x, y))[3] == 0 for x in range(width) for y in (0, height - 1))
        assert all(cell.getpixel((x, y))[3] == 0 for x in (0, width - 1) for y in range(height))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    close = Image.new("RGBA", (16, 32), TRANSPARENT)
    for state in range(2):
        close.paste(button(16, 16, state), (0, state * 16))
    footer_image = Image.new("RGBA", (22, 15), TRANSPARENT)
    for state in range(3):
        footer_image.paste(footer(state), (0, state * 5))
    assert close.size == (16, 32) and footer_image.size == (22, 15)
    assert_cell_edges(close, 16, 16, 2)
    assert_cell_edges(footer_image, 22, 5, 3)
    close.save(OUT / "bidirectional_close_button-v2.png")
    footer_image.save(OUT / "bidirectional_settings_footer-v2.png")
    print("OK bidirectional_close_button-v2.png 16x32 RGBA")
    print("OK bidirectional_settings_footer-v2.png 22x15 RGBA")


if __name__ == "__main__":
    main()
