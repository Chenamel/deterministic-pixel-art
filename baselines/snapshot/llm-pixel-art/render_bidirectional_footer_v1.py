#!/usr/bin/env python3
"""Generate the compact normal/hover bidirectional settings footer atlas."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus/bidirectional_settings_footer-v1.png"
WIDTH, HEIGHT = 22, 5
TRANSPARENT = (0, 0, 0, 0)


def render_cell(hovered: bool) -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), TRANSPARENT)
    top = (214, 214, 214, 255) if hovered else (168, 168, 168, 255)
    face = (160, 160, 160, 255) if hovered else (139, 139, 139, 255)
    bottom = (55, 55, 55, 255)
    arrow = (224, 224, 224, 255) if hovered else (90, 90, 90, 255)
    for x in range(1, WIDTH - 1):
        image.putpixel((x, 1), top)
        image.putpixel((x, 2), face)
        image.putpixel((x, 3), bottom)
    # Centered downward chevron, matching the main button's integer-pixel style.
    for x in range(7, 15):
        image.putpixel((x, 1), arrow)
    for x in range(9, 13):
        image.putpixel((x, 2), arrow)
    for x in range(10, 12):
        image.putpixel((x, 3), arrow)
    return image


def main() -> None:
    image = Image.new("RGBA", (WIDTH, HEIGHT * 2), TRANSPARENT)
    image.paste(render_cell(False), (0, 0))
    image.paste(render_cell(True), (0, HEIGHT))
    assert image.size == (22, 10) and image.mode == "RGBA"
    for state in range(2):
        cell = image.crop((0, state * HEIGHT, WIDTH, (state + 1) * HEIGHT))
        assert all(cell.getpixel((x, y))[3] == 0 for x in (0, WIDTH - 1) for y in range(HEIGHT))
        assert all(cell.getpixel((x, y))[3] == 0 for x in range(WIDTH) for y in (0, HEIGHT - 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(f"OK {OUT} 22x10 RGBA")


if __name__ == "__main__":
    main()
