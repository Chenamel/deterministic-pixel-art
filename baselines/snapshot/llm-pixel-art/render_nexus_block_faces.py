#!/usr/bin/env python3
"""Deterministically render the six opaque Nexus block faces.

The accent colors are tied to RelativeSide, not world Direction:
top/bottom cyan, left/right orange, front/back yellow.
"""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/block"
SIZE = 16
OPAQUE = 255

PALETTE = {
    "outline": (37, 40, 43, OPAQUE),
    "edge": (69, 75, 80, OPAQUE),
    "casing": (110, 116, 120, OPAQUE),
    "detail": (145, 151, 154, OPAQUE),
    "port_outer": (44, 49, 53, OPAQUE),
    "port_inner": (58, 65, 70, OPAQUE),
    "copper_dark": (117, 69, 46, OPAQUE),
    "copper": (182, 110, 66, OPAQUE),
    "cyan_dark": (37, 105, 119, OPAQUE),
    "cyan": (102, 199, 216, OPAQUE),
    "orange_dark": (126, 68, 29, OPAQUE),
    "orange": (220, 137, 62, OPAQUE),
    "yellow_dark": (132, 105, 28, OPAQUE),
    "yellow": (224, 190, 73, OPAQUE),
}


def rect(image: Image.Image, x0: int, y0: int, x1: int, y1: int, color) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            image.putpixel((x, y), color)


def render_base() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), PALETTE["outline"])
    rect(image, 1, 1, 14, 14, PALETTE["edge"])
    rect(image, 2, 2, 13, 13, PALETTE["casing"])
    for point in ((2, 2), (13, 2), (2, 13), (13, 13)):
        image.putpixel(point, PALETTE["detail"])
    for point in ((3, 3), (12, 3), (3, 12), (12, 12)):
        image.putpixel(point, PALETTE["edge"])
    rect(image, 3, 3, 12, 12, PALETTE["port_outer"])
    rect(image, 4, 4, 11, 11, PALETTE["edge"])
    rect(image, 5, 5, 10, 10, PALETTE["port_inner"])
    for point in ((7, 4), (8, 4), (11, 7), (11, 8),
                  (7, 11), (8, 11), (4, 7), (4, 8)):
        image.putpixel(point, PALETTE["copper"])
    for point in ((8, 4), (11, 8), (7, 11), (4, 7)):
        image.putpixel(point, PALETTE["copper_dark"])
    rect(image, 7, 7, 8, 8, PALETTE["outline"])
    return image


def accent(image: Image.Image, role: str) -> None:
    if role == "top":
        dark, bright = PALETTE["cyan_dark"], PALETTE["cyan"]
        rect(image, 6, 3, 9, 3, dark)
        rect(image, 7, 3, 8, 3, bright)
    elif role == "bottom":
        dark, bright = PALETTE["cyan_dark"], PALETTE["cyan"]
        rect(image, 6, 12, 9, 12, dark)
        rect(image, 7, 12, 8, 12, bright)
    elif role == "left":
        dark, bright = PALETTE["orange_dark"], PALETTE["orange"]
        rect(image, 3, 6, 3, 9, dark)
        rect(image, 3, 7, 3, 8, bright)
    elif role == "right":
        dark, bright = PALETTE["orange_dark"], PALETTE["orange"]
        rect(image, 12, 6, 12, 9, dark)
        rect(image, 12, 7, 12, 8, bright)
    elif role == "front":
        dark, bright = PALETTE["yellow_dark"], PALETTE["yellow"]
        rect(image, 6, 3, 9, 3, dark)
        rect(image, 7, 3, 8, 3, bright)
        rect(image, 7, 4, 8, 4, bright)
    elif role == "back":
        dark, bright = PALETTE["yellow_dark"], PALETTE["yellow"]
        rect(image, 6, 12, 9, 12, dark)
        rect(image, 7, 12, 8, 12, bright)
        rect(image, 7, 11, 8, 11, bright)


def render_face(role: str) -> Image.Image:
    image = render_base()
    accent(image, role)
    assert image.mode == "RGBA" and image.size == (SIZE, SIZE)
    pixels = image.get_flattened_data()
    assert all(pixel[3] == OPAQUE for pixel in pixels)
    assert not any(pixel[:3] == (255, 255, 255) for pixel in pixels)
    assert any(pixel != PALETTE["outline"] for pixel in pixels)
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for role in ("front", "back", "left", "right", "top", "bottom"):
        render_face(role).save(OUT / f"nexus_{role}.png")
    faces = {role: render_face(role) for role in ("front", "back", "left", "right", "top", "bottom")}
    assert faces["front"].tobytes() != faces["back"].tobytes()
    assert faces["left"].tobytes() != faces["right"].tobytes()
    assert faces["top"].tobytes() != faces["bottom"].tobytes()
    print("OK six Nexus block faces")


if __name__ == "__main__":
    main()
