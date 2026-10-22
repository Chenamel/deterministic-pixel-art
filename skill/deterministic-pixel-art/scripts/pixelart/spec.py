"""Version 1 JSON specifications and the strict legacy drawing DSL."""
from __future__ import annotations

from collections.abc import Mapping
from PIL import Image

from .core import (Canvas, PixelArtError, boolean, color, dimensions, integer,
                   make_preview, pair)
from . import presets


def fields(obj, required, optional=()):
    if not isinstance(obj, Mapping) or any(not isinstance(k, str) for k in obj):
        raise PixelArtError('expected an object with string keys')
    missing = set(required) - set(obj)
    unknown = set(obj) - set(required) - set(optional)
    if missing:
        raise PixelArtError(f'missing fields: {sorted(missing)}')
    if unknown:
        raise PixelArtError(f'unknown fields: {sorted(unknown)}')


def parse_dsl(text):
    operations = []
    size = None
    arity = {'CANVAS': 2, 'BG': 1, 'RECT': 5, 'BEVEL': 7, 'SLOT': 2, 'BTN': 5}
    for line_number, line in enumerate(text.splitlines(), 1):
        p = line.split()
        if not p or p[0].startswith('#'):
            continue
        command, args = p[0], p[1:]
        try:
            if command not in arity:
                raise PixelArtError(f'unknown instruction {command!r}')
            if len(args) != arity[command]:
                raise PixelArtError(f'{command} requires {arity[command]} arguments')
            if command == 'CANVAS':
                if size is not None:
                    raise PixelArtError('CANVAS must appear exactly once')
                size = dimensions(tuple(map(int, args)))
                continue
            if size is None:
                raise PixelArtError('CANVAS must precede drawing instructions')
            if command == 'BG':
                op = dict(op='rect', x=0, y=0, w=size[0], h=size[1], color=color(args[0]))
            elif command == 'RECT':
                x, y, w, h = map(int, args[:4])
                op = dict(op='rect', x=x, y=y, w=w, h=h, color=color(args[4]))
            elif command == 'BEVEL':
                x, y, w, h = map(int, args[:4])
                op = dict(op='bevel', x=x, y=y, w=w, h=h, tl=color(args[4]),
                          br=color(args[5]), thickness=int(args[6]))
            elif command == 'SLOT':
                x, y = map(int, args)
                op = dict(op='slot', x=x, y=y)
            else:
                x, y, w, h = map(int, args[:4])
                if args[4] not in presets.BUTTONS:
                    raise PixelArtError(f'unknown button state {args[4]!r}')
                op = dict(op='button', x=x, y=y, w=w, h=h, state=args[4])
            op['_line'] = line_number
            operations.append(op)
        except (ValueError, TypeError) as exc:
            raise PixelArtError(f'line {line_number}: {exc}') from exc
    if size is None:
        raise PixelArtError('CANVAS is required')
    return dict(version=1, kind='draw', size=list(size), preset='minecraft', operations=operations)


def render(spec):
    """Render a specification mapping or DSL string to a new RGBA PIL image."""
    if isinstance(spec, str):
        spec = parse_dsl(spec)
    return _render(spec, 0)


def _render(spec, depth):
    if depth > 24:
        raise PixelArtError('nested specifications exceed depth 24')
    if not isinstance(spec, Mapping):
        raise PixelArtError('spec: expected an object or a DSL string')
    version = spec.get('version', 1)
    if type(version) is not int or version != 1:
        raise PixelArtError('version: only integer version 1 is supported')
    kind = spec.get('kind')
    if not isinstance(kind, str):
        raise PixelArtError('kind: expected grid, draw, atlas or preview')
    common = ('version',)
    if kind == 'grid':
        fields(spec, ('kind', 'rows', 'palette'), common + ('mirror', 'center_x', 'center_y', 'size'))
        rows, palette = spec['rows'], spec['palette']
        if not isinstance(rows, list) or not rows or any(not isinstance(r, str) or not r for r in rows):
            raise PixelArtError('rows: expected a nonempty list of nonempty strings')
        if any(len(r) != len(rows[0]) for r in rows):
            raise PixelArtError('rows: every row must have the same width')
        if not isinstance(palette, Mapping) or any(not isinstance(k, str) or len(k) != 1 for k in palette):
            raise PixelArtError('palette: grid symbols must be single characters')
        colors = {k: bytes(color(v)) for k, v in palette.items()}
        for y, row in enumerate(rows):
            missing = set(row) - set(colors)
            if missing:
                symbol = sorted(missing)[0]
                raise PixelArtError(f'rows[{y}][{row.index(symbol)}]: unknown symbol {symbol!r}')
        mirror = spec.get('mirror', 'none')
        if mirror not in ('none', 'x', 'y', 'xy'):
            raise PixelArtError('mirror: expected none, x, y or xy')
        cx = boolean(spec.get('center_x', False), 'center_x')
        cy = boolean(spec.get('center_y', False), 'center_y')
        if (cx and 'x' not in mirror) or (cy and 'y' not in mirror):
            raise PixelArtError('center_x/center_y require the corresponding mirror axis')
        width = len(rows[0]) * (2 if 'x' in mirror else 1) - int(cx)
        height = len(rows) * (2 if 'y' in mirror else 1) - int(cy)
        size = dimensions((width, height))
        if 'size' in spec and dimensions(spec['size']) != size:
            raise PixelArtError(f'size: grid computes {size}, different from declared size')
        if 'x' in mirror:
            rows = [r + (r[:-1] if cx else r)[::-1] for r in rows]
        if 'y' in mirror:
            rows = rows + (rows[:-1] if cy else rows)[::-1]
        return Image.frombytes('RGBA', size, b''.join(colors[c] for r in rows for c in r))
    if kind == 'preview':
        fields(spec, ('kind', 'source'), common + ('scale', 'background'))
        return make_preview(_render(spec['source'], depth + 1), spec.get('scale', 8), spec.get('background', 'checker'))
    if kind == 'atlas':
        fields(spec, ('kind', 'cells', 'columns'), common + ('background','rows','assembly','base'))
        cells = spec['cells']
        if not isinstance(cells, list) or not cells:
            raise PixelArtError('cells: expected a nonempty list')
        columns = integer(spec['columns'], 'columns', 1)
        if columns > len(cells) and 'rows' not in spec:
            raise PixelArtError('columns: cannot exceed cell count')
        assembly=spec.get('assembly','over')
        if assembly not in ('over','copy'):
            raise PixelArtError('atlas.assembly: expected over or copy')
        names, images, positions = [], [], []
        for i, cell in enumerate(cells):
            fields(cell, ('name', 'spec'), ('at',))
            if not isinstance(cell['name'], str) or not cell['name'] or cell['name'] in names:
                raise PixelArtError(f'cells[{i}].name: requires a unique nonempty name')
            names.append(cell['name'])
            images.append(_render(cell['spec'], depth + 1))
        size = images[0].size
        if any(im.size != size for im in images):
            raise PixelArtError('cells: all images must have identical dimensions')
        for i,cell in enumerate(cells):
            position=pair(cell.get('at',[i%columns*size[0],i//columns*size[1]]),'atlas.cell.at',0)
            if position[0]%size[0] or position[1]%size[1]:
                raise PixelArtError('atlas.cell.at: must align to cell grid')
            if position in positions:
                raise PixelArtError('atlas.cell.at: duplicate position')
            positions.append(position)
        rows=integer(spec.get('rows',max(y//size[1]+1 for x,y in positions)),'atlas.rows',1)
        cv = Canvas(size[0] * columns, size[1] * rows, spec.get('background'))
        if 'base' in spec:
            base=_render(spec['base'],depth+1)
            if base.size!=cv.image.size:
                raise PixelArtError('atlas.base: dimensions must match the atlas')
            if assembly=='copy':cv.image.paste(base,(0,0))
            else:cv.composite(base,0,0)
        metadata = []
        for i, (name, image) in enumerate(zip(names, images)):
            x,y=positions[i]
            cv._box(x,y,*size,False)
            if assembly=='copy':cv.image.paste(image,(x,y))
            else:cv.composite(image, x, y)
            metadata.append({'name': name, 'x': x, 'y': y, 'w': size[0], 'h': size[1]})
        cv.image.info['pixelart'] = {'cell_size': list(size), 'columns': columns, 'rows': rows, 'cells': metadata}
        return cv.image
    if kind != 'draw':
        raise PixelArtError(f'kind: unknown kind {kind!r}')
    fields(spec, ('kind', 'size', 'operations'), common + ('background', 'palette', 'preset'))
    preset = spec.get('preset')
    if preset not in (None, 'minecraft'):
        raise PixelArtError('preset: only minecraft is available; omit it for general drawing')
    palette = spec.get('palette', {})
    if not isinstance(palette, Mapping) or any(not isinstance(k, str) for k in palette):
        raise PixelArtError('palette: expected an object with string keys')
    resolved = {k: color(v) for k, v in palette.items()}

    def resolve(value):
        return resolved[value] if isinstance(value, str) and value in resolved else color(value)

    cv = Canvas(*dimensions(spec['size']), background=resolve(spec.get('background')))
    operations = spec['operations']
    if not isinstance(operations, list):
        raise PixelArtError('operations: expected a list')
    for index, op in enumerate(operations):
        location = f'operations[{index}]'
        try:
            if not isinstance(op, Mapping):
                raise PixelArtError('expected an operation object')
            if '_line' in op:
                location = f"line {op['_line']}"
            clip = boolean(op.get('clip', False), 'clip')
            name = op.get('op')
            opts = ('clip', '_line')
            if name in ('rect', 'bevel', 'button'):
                required = ('op', 'x', 'y', 'w', 'h')
                if name == 'rect':
                    fields(op, required + ('color',), opts)
                elif name == 'bevel':
                    fields(op, required + ('tl', 'br'), opts + ('thickness',))
                else:
                    fields(op, required + ('state',), opts)
                x, y = pair((op['x'], op['y']), 'position')
                w, h = pair((op['w'], op['h']), 'extent', 1)
                if name == 'rect':
                    cv.rect(x, y, w, h, resolve(op['color']), clip=clip)
                elif name == 'bevel':
                    cv.bevel(x, y, w, h, resolve(op['tl']), resolve(op['br']), op.get('thickness', 1), clip=clip)
                else:
                    if preset != 'minecraft':
                        raise PixelArtError('button requires preset=minecraft')
                    presets.button(cv, x, y, w, h, op['state'], clip=clip)
            elif name in ('points', 'line', 'polygon', 'mask'):
                fields(op, ('op', 'points', 'color'), opts + (('outline', 'neighborhood', 'thickness') if name == 'mask' else ()))
                if name == 'mask':
                    cv.mask(op['points'], resolve(op['color']),
                            resolve(op['outline']) if op.get('outline') is not None else None,
                            neighborhood=op.get('neighborhood', 8), thickness=op.get('thickness', 1), clip=clip)
                else:
                    getattr(cv, 'paint' if name == 'points' else name)(op['points'], resolve(op['color']), clip=clip)
            elif name == 'slot':
                fields(op, ('op', 'x', 'y'), opts)
                if preset != 'minecraft':
                    raise PixelArtError('slot requires preset=minecraft')
                x, y = pair((op['x'], op['y']), 'position')
                presets.slot(cv, x, y, clip=clip)
            elif name == 'blit':
                fields(op, ('op', 'x', 'y', 'source'), opts + ('crop',))
                image = _render(op['source'], depth + 1)
                if 'crop' in op:
                    crop = op['crop']
                    if not isinstance(crop, (tuple, list)) or len(crop) != 4:
                        raise PixelArtError('crop: expected [x, y, width, height]')
                    x, y = pair(crop[:2], 'crop.position', 0)
                    w, h = pair(crop[2:], 'crop.extent', 1)
                    if x + w > image.width or y + h > image.height:
                        raise PixelArtError('crop: exceeds source dimensions')
                    image = image.crop((x, y, x + w, y + h))
                cv.composite(image, op['x'], op['y'], clip=clip)
            else:
                raise PixelArtError(f'unknown operation {name!r}')
        except (ValueError, TypeError, KeyError) as exc:
            message = str(exc)
            if location.startswith('line '):
                message = message.replace('; use clip=true explicitly', '; adjust coordinates or use JSON with clip=true')
            raise PixelArtError(f'{location}: {message}') from exc
    return cv.image
