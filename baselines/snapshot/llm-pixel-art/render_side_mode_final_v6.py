#!/usr/bin/env python3
"""Generate the final horizontal Phase 1 plane and world decal atlases."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TEXTURE_DIR = ROOT / "src/main/resources/assets/chenamels_nexus/textures/gui/nexus"
PLANE_OUTPUT = TEXTURE_DIR / "side_mode_plane_horizontal-v4.png"
DECAL_OUTPUT = TEXTURE_DIR / "side_mode_decal_final-v6.png"
CELL_SIZE = 16
TRANSPARENT = (0, 0, 0, 0)
DISABLED_BODY, DISABLED_OUTLINE = (139, 139, 139, 255), (74, 74, 74, 255)
INPUT_BODY, INPUT_OUTLINE = (102, 140, 208, 255), (38, 55, 89, 255)
OUTPUT_BODY, OUTPUT_OUTLINE = (206, 104, 115, 255), (85, 40, 45, 255)
BIDIRECTIONAL_BODY, BIDIRECTIONAL_OUTLINE = (165, 123, 190, 255), (69, 48, 82, 255)
CACHE_BODY, CACHE_OUTLINE = (120, 181, 133, 255), (46, 77, 54, 255)
Mask = set[tuple[int, int]]


def gate() -> Mask:
    return {(x, y) for x in (7, 8) for y in range(3, 13)}


def input_arrow() -> Mask:
    pixels = {(x, y) for x in range(2, 7) for y in (7, 8)}
    pixels.update((5, y) for y in range(5, 11))
    pixels.update((6, y) for y in range(6, 10))
    return pixels


def output_arrow() -> Mask:
    pixels = {(x, y) for x in range(9, 14) for y in (7, 8)}
    pixels.update((11, y) for y in range(5, 11))
    pixels.update((12, y) for y in range(6, 10))
    pixels.update((13, y) for y in (7, 8))
    return pixels


def disabled() -> Mask:
    pixels = {(x, y) for x in range(5, 11) for y in (5, 10)}
    pixels.update((x, y) for y in range(6, 10) for x in (5, 10))
    pixels.update((x, y) for x in range(7, 9) for y in (7, 8))
    return pixels


def cache_release() -> Mask:
    pixels = {(x, y) for x in range(2, 7) for y in (5, 10)}
    pixels.update((2, y) for y in range(6, 10))
    pixels.update((x, y) for x in range(6, 11) for y in (7, 8))
    pixels.update((10, y) for y in range(5, 11))
    pixels.update((11, y) for y in range(6, 10))
    pixels.update((12, y) for y in (7, 8))
    return pixels


def outline(mask: Mask) -> Mask:
    return {(x + dx, y + dy) for x, y in mask for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if (x + dx, y + dy) not in mask and 0 <= x + dx < CELL_SIZE and 0 <= y + dy < CELL_SIZE}


def paint(image: Image.Image, cell: int, mask: Mask, body: tuple[int, int, int, int], edge: tuple[int, int, int, int]) -> None:
    left = cell * CELL_SIZE
    for x, y in outline(mask):
        image.putpixel((left + x, y), edge)
    for x, y in mask:
        image.putpixel((left + x, y), body)


def assert_edges(image: Image.Image, cells: int) -> None:
    assert image.mode == "RGBA"
    for cell in range(cells):
        left = cell * CELL_SIZE
        assert all(image.getpixel((left, y))[3] == 0 and image.getpixel((left + 15, y))[3] == 0 for y in range(16))
        assert all(image.getpixel((x, 0))[3] == 0 and image.getpixel((x, 15))[3] == 0 for x in range(left, left + 16))


def assert_flow() -> None:
    g, i, o = gate(), input_arrow(), output_arrow()
    assert {x for x, _ in g} == {7, 8}
    assert max(x for x, _ in i - g) == 6
    assert min(x for x, _ in o - g) == 9


def render_plane() -> Image.Image:
    image = Image.new("RGBA", (80, 16), TRANSPARENT)
    g, i, o = gate(), input_arrow(), output_arrow()
    paint(image, 0, disabled(), DISABLED_BODY, DISABLED_OUTLINE)
    paint(image, 1, g | i, INPUT_BODY, INPUT_OUTLINE)
    paint(image, 2, g | o, OUTPUT_BODY, OUTPUT_OUTLINE)
    paint(image, 3, g | i | o, BIDIRECTIONAL_BODY, BIDIRECTIONAL_OUTLINE)
    paint(image, 4, cache_release(), CACHE_BODY, CACHE_OUTLINE)
    assert image.size == (80, 16)
    assert_edges(image, 5)
    return image


def render_decal() -> Image.Image:
    image = Image.new("RGBA", (64, 16), TRANSPARENT)
    g, i, o = gate(), input_arrow(), output_arrow()
    paint(image, 0, disabled(), DISABLED_BODY, DISABLED_OUTLINE)
    paint(image, 1, g | i, INPUT_BODY, INPUT_OUTLINE)
    paint(image, 2, g | o, OUTPUT_BODY, OUTPUT_OUTLINE)
    paint(image, 3, cache_release(), CACHE_BODY, CACHE_OUTLINE)
    assert image.size == (64, 16)
    assert_edges(image, 4)
    return image


def save_verified(image: Image.Image, path: Path) -> None:
    image.save(path)
    with Image.open(path) as saved:
        assert saved.mode == "RGBA" and saved.size == image.size


if __name__ == "__main__":
    assert_flow()
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    save_verified(render_plane(), PLANE_OUTPUT)
    save_verified(render_decal(), DECAL_OUTPUT)
    print(f"OK {PLANE_OUTPUT} RGBA 80x16")
    print(f"OK {DECAL_OUTPUT} RGBA 64x16")
