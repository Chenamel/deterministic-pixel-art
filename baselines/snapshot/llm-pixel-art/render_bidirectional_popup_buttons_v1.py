#!/usr/bin/env python3
"""Generate the dedicated MEK-style bidirectional popup button atlases."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus"
TRANSPARENT = (0, 0, 0, 0)


def draw_button(width: int, height: int, state: int, selected: bool = False) -> Image.Image:
    image = Image.new("RGBA", (width, height), TRANSPARENT)
    # Keep a one-pixel transparent boundary so neighboring GUI pixels never bleed.
    dark = (42, 42, 42, 255)
    mid = (112, 112, 112, 255)
    face = (198, 198, 198, 255)
    light = (232, 232, 232, 255)
    if state == 1:  # hover
        face, light = (214, 214, 214, 255), (250, 250, 250, 255)
    elif state == 2 or selected:
        face, light, mid = (174, 196, 204, 255), (224, 244, 248, 255), (78, 100, 108, 255)
    elif state == 3:  # disabled
        dark, mid, face, light = (54, 54, 54, 255), (92, 92, 92, 255), (126, 126, 126, 255), (148, 148, 148, 255)
    for x in range(1, width - 1):
        for y in range(1, height - 1):
            image.putpixel((x, y), face)
    for x in range(1, width - 1):
        image.putpixel((x, 1), light)
        image.putpixel((x, height - 2), dark)
    for y in range(1, height - 1):
        image.putpixel((1, y), light)
        image.putpixel((width - 2, y), dark)
    image.putpixel((2, 2), light)
    image.putpixel((width - 3, height - 3), mid)
    return image


def render_popup_buttons() -> Image.Image:
    image = Image.new("RGBA", (22, 80), TRANSPARENT)
    for state in range(4):
        cell = draw_button(22, 20, state)
        image.paste(cell, (0, state * 20), cell)
    return image


def render_close_button() -> Image.Image:
    image = Image.new("RGBA", (20, 40), TRANSPARENT)
    for state in range(2):
        cell = draw_button(20, 20, state)
        color = (82, 82, 82, 255) if state == 0 else (116, 86, 34, 255)
        for x, y in ((6, 5), (7, 6), (8, 7), (9, 8), (10, 9), (11, 10),
                     (11, 5), (10, 6), (9, 7), (8, 8), (7, 9), (6, 10)):
            cell.putpixel((x, y), color)
        image.paste(cell, (0, state * 20), cell)
    return image


def assert_edges(image: Image.Image, cell_width: int, cell_height: int, cells: int) -> None:
    assert image.mode == "RGBA"
    for cell in range(cells):
        x0, y0 = cell * cell_width, 0
        for y in range(cell_height):
            assert image.getpixel((x0, y0 + y))[3] == 0
            assert image.getpixel((x0 + cell_width - 1, y0 + y))[3] == 0
        for x in range(x0, x0 + cell_width):
            assert image.getpixel((x, y0))[3] == 0
            assert image.getpixel((x, y0 + cell_height - 1))[3] == 0


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    popup = render_popup_buttons()
    close = render_close_button()
    assert popup.size == (22, 80)
    assert close.size == (20, 40)
    assert_edges(popup, 22, 20, 1)
    for state in range(4):
        assert_edges(popup.crop((0, state * 20, 22, state * 20 + 20)), 22, 20, 1)
    for state in range(2):
        assert_edges(close.crop((0, state * 20, 20, state * 20 + 20)), 20, 20, 1)
    popup.save(OUT / "bidirectional_popup_button-v1.png")
    close.save(OUT / "bidirectional_close_button-v1.png")
    print("OK bidirectional_popup_button-v1.png 22x80 RGBA")
    print("OK bidirectional_close_button-v1.png 20x40 RGBA")
