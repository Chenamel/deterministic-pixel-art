"""Measure an actual font and compose labels over named atlas cells, without editing the atlas."""
import hashlib
from pathlib import Path

from _common import emit, entry, parser, PixelArtError
from PIL import Image, ImageDraw, ImageFont
from pixelart.context import _context
from pixelart.core import color, dimensions, integer, pair
from pixelart.jsonio import parse_json
from pixelart.metadata import merge_layout, rgba_digest


def compose_labels(image, context, *, font_path, font_size, labels, font_mode,
                   metadata=None, padding=2, ink='FFFFFF', state_offsets=None, state_colors=None):
    """Return consumer PNGs and a placement report; never write or change inputs.

    Rows follow atlas state order; columns follow labels. One reserved_text
    region is required per cell. Origins share a cell-local base per label,
    plus explicit state offsets. Rectangles are half-open [x,y,width,height].
    """
    merged, provenance = merge_layout(image, context, metadata)
    ctx = _context(merged, image.size)
    cells = ctx['cells']
    if not cells or provenance['unverified_records']:
        raise PixelArtError('labels: require a named atlas with content-bound metadata; regenerate --metadata with the PNG')
    if font_mode not in ('grayscale', 'monochrome'):
        raise PixelArtError('font_mode: choose grayscale or monochrome explicitly')
    integer(font_size, 'font_size', 1)
    if font_size > 512:
        raise PixelArtError('font_size: maximum 512 logical pixels')
    integer(padding, 'padding', 0)
    if (not isinstance(labels, (list, tuple)) or not 1 <= len(labels) <= 16 or
        any(not isinstance(t, str) or not t.strip() or len(t) > 256 or
            any(ord(c) < 32 or ord(c) == 127 for c in t) for t in labels)):
        raise PixelArtError('labels: expected 1..16 nonempty single-line strings of at most 256 characters')
    names = {c['name'] for c in cells}
    offsets = dict(state_offsets or {})
    colors = dict(state_colors or {})
    if (set(offsets) | set(colors)) - names:
        raise PixelArtError('labels: unknown state in offsets or colors')
    offsets = {name: pair(value, 'state_offsets.' + name) for name, value in offsets.items()}
    colors = {name: color(value) for name, value in colors.items()}
    default_ink = color(ink)
    if not default_ink[3] or any(not c[3] for c in colors.values()):
        raise PixelArtError('labels: text colors must have nonzero alpha')

    reservations = {}
    for region in (r for r in ctx['regions'] if r['role'] == 'reserved_text'):
        x, y, w, h = region['rect']
        owners = [c for c in cells if c['rect'][0] <= x and c['rect'][1] <= y and
                  x + w <= c['rect'][0] + c['rect'][2] and y + h <= c['rect'][1] + c['rect'][3]]
        if len(owners) != 1 or owners[0]['name'] in reservations:
            raise PixelArtError('labels: each reserved_text region must belong to one cell, with one region per cell')
        cell = owners[0]
        reservations[cell['name']] = [x - cell['rect'][0], y - cell['rect'][1], w, h]
    if set(reservations) != names:
        raise PixelArtError('labels: require exactly one reserved_text region per named cell; generate buttons with --content')

    font_path = Path(font_path)
    # Loading a missing font must fail; a fallback cannot establish actual fit.
    font = ImageFont.truetype(str(font_path), font_size)
    measure = ImageDraw.Draw(Image.new('L', (1, 1)))
    metrics = []
    bases = []
    for label in labels:
        left, top, right, bottom = measure.textbbox((0, 0), label, font=font)
        gw, gh = right - left, bottom - top
        if gw < 1 or gh < 1:
            raise PixelArtError(f'label {label!r}: font produces no measurable glyph bounds')
        limits = []
        for cell in cells:
            rx, ry, rw, rh = reservations[cell['name']]
            dx, dy = offsets.get(cell['name'], (0, 0))
            limits.append((rx + padding - dx, ry + padding - dy,
                           rx + rw - padding - gw - dx, ry + rh - padding - gh - dy))
        x0, y0 = max(v[0] for v in limits), max(v[1] for v in limits)
        x1, y1 = min(v[2] for v in limits), min(v[3] for v in limits)
        if x0 > x1 or y0 > y1:
            raise PixelArtError(f'label {label!r}: font bbox {gw}x{gh} cannot fit all state reservations '
                                f'with padding {padding} and offsets {offsets}; widen --content/--width or adjust the reservation/offsets')
        rx, ry, rw, rh = reservations[cells[0]['name']]
        bx = min(max(rx + padding + (rw - 2 * padding - gw) // 2, x0), x1)
        by = min(max(ry + padding + (rh - 2 * padding - gh) // 2, y0), y1)
        bases.append((bx - left, by - top))
        metrics.append(dict(label=label, font_bbox=[left, top, right, bottom]))

    cw, ch = cells[0]['rect'][2:]
    size = dimensions((cw * len(labels), ch * len(cells)))
    dimensions((size[0] * 3, size[1] * 3))
    consumer = Image.new('RGBA', size)
    instances = []
    for row, cell in enumerate(cells):
        state = cell['name']
        sx, sy, sw, sh = cell['rect']
        patch = image.convert('RGBA').crop((sx, sy, sx + sw, sy + sh))
        dx, dy = offsets.get(state, (0, 0))
        rgba = colors.get(state, default_ink)
        rx, ry, rw, rh = reservations[state]
        for column, (label, base) in enumerate(zip(labels, bases)):
            x, y = column * cw, row * ch
            origin = [base[0] + dx, base[1] + dy]
            layer = Image.new('RGBA', (cw, ch))
            draw = ImageDraw.Draw(layer)
            draw.fontmode = '1' if font_mode == 'monochrome' else 'L'
            draw.text(origin, label, font=font, fill=rgba)
            bbox = layer.getchannel('A').getbbox()
            if bbox is None or not (rx + padding <= bbox[0] and ry + padding <= bbox[1] and
                                   bbox[2] <= rx + rw - padding and bbox[3] <= ry + rh - padding):
                raise PixelArtError(f'label {label!r}, state {state!r}: rasterized ink does not fit reserved text padding')
            consumer.paste(Image.alpha_composite(patch, layer), (x, y))
            instances.append(dict(state=state, label=label, origin=[x + origin[0], y + origin[1]],
                state_offset=[dx, dy], color=bytes(rgba).hex().upper(),
                reserved_rect=[x + rx, y + ry, rw, rh],
                ink_rect=[x + bbox[0], y + bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]]))
    report = dict(version=1, font=dict(file=font_path.name, sha256=hashlib.sha256(font_path.read_bytes()).hexdigest(),
                  size=font_size, mode=font_mode), padding=padding, labels=metrics,
                  source_rgba_sha256=rgba_digest(image), consumer_size=list(size),
                  states=[c['name'] for c in cells], metadata=provenance, instances=instances,
                  note='Offline font-fit composite. Inspect glyph coverage and optical alignment at native size; application input and font-engine behavior remain consumer checks.')
    return {'consumer.png': consumer,
            'consumer-3x.png': consumer.resize((size[0] * 3, size[1] * 3), Image.Resampling.NEAREST),
            'text-fit.json': report}


def _options(items, convert):
    values = {}
    for name, *value in items:
        if name in values:
            raise PixelArtError(f'state option: duplicate {name!r}')
        values[name] = convert(value)
    return values


def main():
    cli = parser(__doc__)
    cli.add_argument('--image', type=Path, required=True)
    cli.add_argument('--context', type=Path, required=True)
    cli.add_argument('--metadata', type=Path, help='Content-bound layout; omit only if embedded in the PNG.')
    cli.add_argument('--font', type=Path, required=True)
    cli.add_argument('--font-size', type=int, required=True)
    cli.add_argument('--font-mode', choices=('grayscale', 'monochrome'), required=True)
    cli.add_argument('--labels', nargs='+', required=True)
    cli.add_argument('--padding', type=int, default=2)
    cli.add_argument('--color', default='FFFFFF')
    cli.add_argument('--state-offset', action='append', nargs=3, default=[], metavar=('STATE', 'DX', 'DY'))
    cli.add_argument('--state-color', action='append', nargs=2, default=[], metavar=('STATE', 'COLOR'))
    args = cli.parse_args()
    # Never permit --force to replace one of this operation's inputs.
    inputs = [args.image, args.context, args.font] + ([args.metadata] if args.metadata else [])
    outputs = [args.out_dir / name for name in ('consumer.png', 'consumer-3x.png', 'text-fit.json')]
    if {p.resolve() for p in inputs} & {p.resolve() for p in outputs}:
        raise PixelArtError('output aliases an input; choose a separate --out-dir')
    context = parse_json(args.context.read_text(encoding='utf-8-sig'))
    metadata = parse_json(args.metadata.read_text(encoding='utf-8-sig')) if args.metadata else None
    with Image.open(args.image) as image:
        if getattr(image, 'n_frames', 1) != 1:
            raise PixelArtError('labels: expected a single-frame atlas')
        files = compose_labels(image, context, metadata=metadata, font_path=args.font, font_size=args.font_size,
            font_mode=args.font_mode, labels=args.labels, padding=args.padding, ink=args.color,
            state_offsets=_options(args.state_offset, lambda v: [int(n) for n in v]),
            state_colors=_options(args.state_color, lambda v: v[0]))
    emit(args, files)


if __name__ == '__main__':
    entry(main)
