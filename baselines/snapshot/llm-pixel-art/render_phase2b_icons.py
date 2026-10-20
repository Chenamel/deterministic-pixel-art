#!/usr/bin/env python3
"""Deterministic Phase 2B GUI icons; never touches existing PNG assets."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus"
T = (0, 0, 0, 0)
DARK = (35, 35, 35, 255)
MID = (112, 112, 112, 255)
LIGHT = (224, 224, 224, 255)
BLUE = (102, 140, 208, 255)
BLUE_DARK = (38, 55, 89, 255)
RED = (206, 104, 115, 255)


def put(img, points, color):
    for x, y in points:
        if 0 <= x < 16 and 0 <= y < 16:
            img.putpixel((x, y), color)


def scheduler_icon():
    img = Image.new("RGBA", (16, 16), T)
    # Three staggered ports and a clockwise routing arrow.
    put(img, {(2, 3), (3, 3), (2, 7), (3, 7), (2, 11), (3, 11)}, MID)
    put(img, {(5, 3), (6, 3), (5, 7), (6, 7), (5, 11), (6, 11)}, BLUE)
    put(img, {(9, 3), (10, 3), (9, 7), (10, 7), (9, 11), (10, 11)}, LIGHT)
    put(img, {(4, 2), (5, 2), (6, 2), (7, 2), (8, 2),
              (8, 1), (9, 1), (10, 2), (10, 3), (9, 4), (8, 4)}, DARK)
    put(img, {(4, 2), (5, 2), (6, 2), (7, 2), (8, 2),
              (8, 1), (9, 1), (10, 2), (10, 3), (9, 4), (8, 4)}, BLUE_DARK)
    return img


def expand_icon():
    img = Image.new("RGBA", (16, 16), T)
    put(img, {(7, 4), (8, 4), (6, 5), (7, 5), (8, 5), (9, 5),
              (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6)}, DARK)
    put(img, {(7, 5), (8, 5), (6, 6), (7, 6), (8, 6), (9, 6),
              (6, 7), (7, 7), (8, 7), (9, 7)}, BLUE)
    return img


def clear_icon():
    img = Image.new("RGBA", (16, 16), T)
    put(img, {(3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3),
              (10, 3), (11, 3), (3, 4), (11, 4), (3, 5), (11, 5),
              (3, 6), (11, 6), (3, 7), (11, 7), (3, 8), (11, 8),
              (3, 9), (11, 9), (3, 10), (11, 10), (3, 11), (4, 11),
              (5, 11), (6, 11), (7, 11), (8, 11), (9, 11), (10, 11), (11, 11)}, MID)
    put(img, {(4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4),
              (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5),
              (4, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6),
              (4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7),
              (4, 8), (5, 8), (6, 8), (7, 8), (8, 8), (9, 8), (10, 8),
              (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9),
              (4, 10), (5, 10), (6, 10), (7, 10), (8, 10), (9, 10), (10, 10)}, DARK)
    put(img, {(4, 12), (5, 12), (6, 12), (7, 12), (8, 12), (9, 12), (10, 12),
              (5, 11), (6, 11), (7, 11), (8, 11), (9, 11)}, RED)
    return img


def validate(name, img):
    assert img.mode == "RGBA" and img.size == (16, 16)
    pixels = list(img.getdata())
    assert all(p[3] in (0, 255) for p in pixels)
    assert all(p[:3] != (255, 255, 255) for p in pixels)
    assert img.getpixel((0, 0)) == T and img.getpixel((15, 15)) == T
    assert any(p[3] == 255 for p in pixels)
    img.save(OUT / name)


def face_icons():
    img = Image.new("RGBA", (96, 16), T)
    directions = ((0, -1), (0, 1), (-1, 0), (1, 0), (1, -1), (-1, 1))
    for cell, (dx, dy) in enumerate(directions):
        ox = cell * 16
        cx, cy = ox + 8, 8
        points = {(cx, cy)}
        for step in range(1, 5):
            points.add((cx + dx * step, cy + dy * step))
        tipx, tipy = cx + dx * 5, cy + dy * 5
        if dx == 0:
            points.update(((tipx - 1, tipy - dy), (tipx, tipy), (tipx + 1, tipy - dy)))
        elif dy == 0:
            points.update(((tipx - dx, tipy - 1), (tipx, tipy), (tipx - dx, tipy + 1)))
        else:
            points.update(((tipx - dx, tipy), (tipx, tipy), (tipx, tipy - dy)))
        for x, y in points:
            img.putpixel((x, y), BLUE_DARK)
        inner = {(x, y) for x, y in points
                 if (x - ox, y) not in ((0, 0), (15, 15))}
        for x, y in inner:
            img.putpixel((x, y), LIGHT)
    assert img.mode == "RGBA" and img.size == (96, 16)
    assert all(p[3] in (0, 255) for p in img.getdata())
    assert all(p[:3] != (255, 255, 255) for p in img.getdata())
    for cell in range(6):
        ox = cell * 16
        assert all(img.getpixel((ox, y))[3] == 0 for y in range(16))
        assert all(img.getpixel((ox + 15, y))[3] == 0 for y in range(16))
        assert all(img.getpixel((x, 0))[3] == 0 for x in range(ox, ox + 16))
        assert all(img.getpixel((x, 15))[3] == 0 for x in range(ox, ox + 16))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    validate("active_transfer_scheduler.png", scheduler_icon())
    validate("bidirectional_expand.png", expand_icon())
    validate("clear_side_config.png", clear_icon())
    face = face_icons()
    face.save(OUT / "active_transfer_face_icons.png")
    print("OK phase2b icons")


if __name__ == "__main__":
    main()
