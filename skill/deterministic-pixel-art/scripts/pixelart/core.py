"""Integer-pixel RGBA drawing. Rectangle arguments are x, y, width, height."""
from __future__ import annotations

from collections.abc import Mapping
import re

from PIL import Image, ImageDraw


class PixelArtError(ValueError):
    """Invalid drawing specification or validation rule."""


MAX_PIXELS = 16_777_216
MAX_SIDE = 8192
TRANSPARENT = (0, 0, 0, 0)


def integer(value, name, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        suffix = f' >= {minimum}' if minimum is not None else ''
        raise PixelArtError(f'{name}: expected an integer{suffix}, got {value!r}')
    return value


def pair(value, name, minimum=None):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise PixelArtError(f'{name}: expected two integers')
    return tuple(integer(v, f'{name}[{i}]', minimum) for i, v in enumerate(value))


def color(value):
    if value is None:
        return TRANSPARENT
    if isinstance(value, str) and re.fullmatch(r'#?(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})', value):
        s = value.removeprefix('#')
        channels = tuple(int(s[i:i + 2], 16) for i in range(0, len(s), 2))
        return channels + (255,) if len(channels) == 3 else channels
    if isinstance(value, (list, tuple)) and len(value) in (3, 4):
        if all(type(c) is int and 0 <= c <= 255 for c in value):
            return tuple(value) + ((255,) if len(value) == 3 else ())
    raise PixelArtError(f'color: expected RRGGBB, RRGGBBAA, 3/4 byte channels or null, got {value!r}')


def dimensions(size):
    w, h = pair(size, 'size', 1)
    if max(w, h) > MAX_SIDE or w * h > MAX_PIXELS:
        raise PixelArtError(f'size: limit is {MAX_SIDE} per side and {MAX_PIXELS} pixels')
    return w, h


def points(value):
    if not isinstance(value, (list, tuple, set, frozenset)):
        raise PixelArtError('points: expected a collection of [x, y] coordinates')
    result = []
    for i, p in enumerate(value):
        # Avoid constructing diagnostic strings and validating each component twice
        # on the common valid path. The slow path retains the precise error location.
        if isinstance(p, (list, tuple)) and len(p) == 2 and type(p[0]) is int and type(p[1]) is int:
            result.append((p[0], p[1]))
        else:
            result.append(pair(p, f'points[{i}]'))
    return result


def boolean(value, name):
    if type(value) is not bool:
        raise PixelArtError(f'{name}: expected true or false')
    return value


class Canvas:
    def __init__(self, width, height, background=None):
        self.image = Image.new('RGBA', dimensions((width, height)), color(background))
        self.draw = ImageDraw.Draw(self.image)

    def _box(self, x, y, w, h, clip):
        x, y = pair((x, y), 'position')
        w, h = pair((w, h), 'extent', 1)
        boolean(clip, 'clip')
        if not clip and (x < 0 or y < 0 or x + w > self.image.width or y + h > self.image.height):
            raise PixelArtError(f'bounds: rectangle {(x, y, w, h)} exceeds canvas {self.image.size}; use clip=true explicitly')
        return x, y, x + w - 1, y + h - 1

    def rect(self, x, y, w, h, fill, *, clip=False):
        self.draw.rectangle(self._box(x, y, w, h, clip), fill=color(fill))

    def paint(self, coordinates, fill, *, clip=False):
        boolean(clip, 'clip')
        pts = points(coordinates)
        if not clip and any(not (0 <= x < self.image.width and 0 <= y < self.image.height) for x, y in pts):
            raise PixelArtError('bounds: point exceeds canvas; use clip=true explicitly')
        if pts:
            self.draw.point(pts, fill=color(fill))

    def line(self, coordinates, fill, *, clip=False):
        pts = points(coordinates)
        if len(pts) < 2:
            raise PixelArtError('line: requires at least two points')
        self._check_points(pts, clip)
        self.draw.line(pts, fill=color(fill), width=1)

    def polygon(self, coordinates, fill, *, clip=False):
        pts = points(coordinates)
        if len(pts) < 3:
            raise PixelArtError('polygon: requires at least three points')
        self._check_points(pts, clip)
        self.draw.polygon(pts, fill=color(fill))

    def _check_points(self, pts, clip):
        boolean(clip, 'clip')
        if not clip and any(not (0 <= x < self.image.width and 0 <= y < self.image.height) for x, y in pts):
            raise PixelArtError('bounds: geometry exceeds canvas; use clip=true explicitly')

    def bevel(self, x, y, w, h, top_left, bottom_right, thickness=1, *, clip=False):
        self._box(x, y, w, h, clip)
        integer(thickness, 'thickness', 1)
        if thickness * 2 > min(w, h):
            raise PixelArtError('thickness: bevel would overlap itself')
        # Preserve the original row-then-column corner overwrite order per layer.
        for i in range(thickness):
            self.rect(x, y + i, w, 1, top_left, clip=clip)
            self.rect(x, y + h - 1 - i, w, 1, bottom_right, clip=clip)
            self.rect(x + i, y, 1, h, top_left, clip=clip)
            self.rect(x + w - 1 - i, y, 1, h, bottom_right, clip=clip)

    def mask(self, coordinates, fill, outline_color=None, *, neighborhood=8, thickness=1, clip=False):
        body = set(points(coordinates))
        self._check_points(body, clip)
        if outline_color is not None:
            edge = _outline_validated(body, neighborhood, thickness)
            self._check_points(edge, clip)
            if edge:
                self.draw.point(list(edge), fill=color(outline_color))
        if body:
            self.draw.point(list(body), fill=color(fill))

    def composite(self, image, x, y, *, clip=False):
        self._box(x, y, image.width, image.height, clip)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        self.image.alpha_composite(image, (x, y))


def outline(coordinates, *, neighborhood=8, thickness=1):
    return _outline_validated(set(points(coordinates)), neighborhood, thickness)


def _outline_validated(body, neighborhood, thickness):
    if type(neighborhood) is not int or neighborhood not in (4, 8):
        raise PixelArtError('neighborhood: expected 4 or 8')
    integer(thickness, 'thickness', 1)
    if thickness > 64:
        raise PixelArtError('thickness: maximum outline radius is 64')
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)] if neighborhood == 4 else [
        (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
    expanded = body.copy()
    frontier = body
    for _ in range(thickness):
        frontier = {(x + dx, y + dy) for x, y in frontier for dx, dy in offsets} - expanded
        expanded.update(frontier)
    return expanded - body


def make_preview(image, scale=8, background='checker'):
    integer(scale, 'scale', 1)
    size = dimensions((image.width * scale, image.height * scale))
    if background == 'checker':
        base = Image.new('RGBA', size, (44, 44, 44, 255))
        draw = ImageDraw.Draw(base)
        for y in range(0, size[1], 8):
            for x in range(0, size[0], 8):
                if (x // 8 + y // 8) % 2 == 0:
                    draw.rectangle((x, y, x + 7, y + 7), fill=(62, 62, 62, 255))
    else:
        base = Image.new('RGBA', size, color(background))
    return Image.alpha_composite(base, image.convert('RGBA').resize(size, Image.Resampling.NEAREST))


def validate(image, rules=None):
    rules = {} if rules is None else rules
    if not isinstance(rules, Mapping):
        raise PixelArtError('rules: expected an object')
    unknown = set(rules) - {'size', 'mode', 'alpha', 'palette', 'max_colors', 'nonempty',
                             'cell_size', 'transparent_margin', 'expected_pixels'}
    if unknown:
        raise PixelArtError(f'rules: unknown fields {sorted(unknown)}')
    rgba = image.convert('RGBA')
    colors = set(rgba.get_flattened_data())
    alpha = sorted({c[3] for c in colors})
    errors = []

    def check(condition, rule, message):
        if not condition:
            errors.append({'rule': rule, 'message': message})

    if 'size' in rules:
        check(image.size == dimensions(rules['size']), 'size', f'Actual size is {image.size}')
    if 'mode' in rules:
        if not isinstance(rules['mode'], str):
            raise PixelArtError('rules.mode: expected a string')
        check(image.mode == rules['mode'], 'mode', f'Actual mode is {image.mode}')
    if 'alpha' in rules:
        if not isinstance(rules['alpha'], list) or not rules['alpha']:
            raise PixelArtError('rules.alpha: expected a nonempty list of byte values')
        allowed = set()
        for v in rules['alpha']:
            integer(v, 'rules.alpha', 0)
            if v > 255:
                raise PixelArtError('rules.alpha: values must be <= 255')
            allowed.add(v)
        check(set(alpha) <= allowed, 'alpha', f'Actual alpha values are {alpha}')
    if 'palette' in rules:
        if not isinstance(rules['palette'], list):
            raise PixelArtError('rules.palette: expected a list of colors')
        check(colors <= {color(c) for c in rules['palette']}, 'palette', 'Image contains colors outside the allowed palette')
    if 'max_colors' in rules:
        check(len(colors) <= integer(rules['max_colors'], 'max_colors', 1), 'max_colors', f'Actual color count is {len(colors)}')
    if 'nonempty' in rules and boolean(rules['nonempty'], 'nonempty'):
        check(any(c[3] for c in colors), 'nonempty', 'Image is entirely transparent')
    cw, ch = dimensions(rules.get('cell_size', image.size))
    divides = image.width % cw == 0 and image.height % ch == 0
    if 'cell_size' in rules:
        check(divides, 'cell_size', 'Canvas is not divisible by the requested cell size')
    if 'transparent_margin' in rules:
        margin = integer(rules['transparent_margin'], 'transparent_margin', 0)
        if margin * 2 > min(cw, ch):
            raise PixelArtError('transparent_margin: exceeds half the cell size')
        if divides and margin:
            for y0 in range(0, image.height, ch):
                for x0 in range(0, image.width, cw):
                    a = rgba.crop((x0, y0, x0 + cw, y0 + ch)).getchannel('A')
                    edges = ((0, 0, cw, margin), (0, ch - margin, cw, ch),
                             (0, 0, margin, ch), (cw - margin, 0, cw, ch))
                    check(all(a.crop(box).getextrema()[1] == 0 for box in edges),
                          'transparent_margin', f'Opaque pixel in margin of cell at {(x0, y0)}')
    if 'expected_pixels' in rules:
        if not isinstance(rules['expected_pixels'], list):
            raise PixelArtError('expected_pixels: expected a list')
        for item in rules['expected_pixels']:
            if not isinstance(item, Mapping) or set(item) != {'at', 'color'}:
                raise PixelArtError('expected_pixels: each item requires only at and color')
            x, y = pair(item['at'], 'expected_pixels.at', 0)
            if x >= image.width or y >= image.height:
                raise PixelArtError('expected_pixels: coordinate outside canvas')
            check(rgba.getpixel((x, y)) == color(item['color']), 'expected_pixels', f'Unexpected pixel at {(x, y)}')
    return {'valid': not errors, 'errors': errors,
            'facts': {'size': list(image.size), 'mode': image.mode,
                      'colors': len(colors), 'alpha': alpha}}
