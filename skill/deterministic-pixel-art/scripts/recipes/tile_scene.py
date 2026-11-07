"""Arrange named atlas tiles into an explicit scene, with portable source files."""
from io import BytesIO
import hashlib
import json
from math import isqrt
from pathlib import Path

from _common import entry, make_preview, parser, PixelArtError
from PIL import Image
from pixelart.assembly import assemble, seam_sheet
from pixelart.cli import check_alias
from pixelart.context import _context, _fields
from pixelart.core import dimensions, integer, MAX_PIXELS, MAX_SIDE
from pixelart.jsonio import parse_json
from pixelart.metadata import merge_layout, rgba_digest
from pixelart.output import encoded, publish, resolve_portable_output

MAX_CELLS = 4096
MAX_PLACEMENTS = 256
MAX_JSON_BYTES = 1024 * 1024
MAX_PNG_BYTES = 80 * 1024 * 1024
MAX_OUTPUT_BYTES = 128 * 1024 * 1024
OUTPUT_NAMES = ('atlas.png', 'atlas-layout.json', 'layout.json', 'scene.png',
                'preview.png', 'seams.png', 'project.json', 'report.json')


def _budget(ok, message):
    if not ok:
        raise PixelArtError('tile scene: ' + message + '; split the atlas or scene')


def _plan(image, metadata, layout, scale):
    integer(scale, 'scale', 1)
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise PixelArtError('tile scene metadata: expected an object')
        _budget(len(encoded(metadata)) <= MAX_JSON_BYTES, 'metadata exceeds 1 MiB')
    _fields(layout, ('version', 'rows'), where='tile scene layout')
    if type(layout['version']) is not int or layout['version'] != 1:
        raise PixelArtError('tile scene layout.version: expected integer 1')
    _budget(len(encoded(layout)) <= MAX_JSON_BYTES, 'layout exceeds 1 MiB')
    rows = layout['rows']
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], list) or not rows[0]:
        raise PixelArtError('tile scene layout.rows: expected nonempty rectangular rows of tile names')
    columns = len(rows[0])
    _budget(columns * len(rows) <= MAX_PLACEMENTS, 'more than 256 placements')
    for y, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != columns:
            raise PixelArtError(f'tile scene layout.rows[{y}]: expected {columns} names')
        if any(not isinstance(name, str) or not name for name in row):
            raise PixelArtError(f'tile scene layout.rows[{y}]: every tile name must be a nonempty string')

    merged, provenance = merge_layout(image, metadata=metadata, require_bound_atlas=True)
    atlas = merged.get('atlas')
    if not isinstance(atlas, dict) or not isinstance(atlas.get('cells'), list) or not atlas['cells']:
        raise PixelArtError('tile scene: requires a nonempty named atlas')
    _budget(len(atlas['cells']) <= MAX_CELLS, 'more than 4096 declared cells')
    first = atlas['cells'][0]
    if not isinstance(first, dict) or not isinstance(first.get('name'), str) or not first['name']:
        raise PixelArtError('tile scene: expected a nonempty first cell name')
    # Selection bounds the old consumer, but still validates EVERY layout entry.
    _context(merged, image.size, selected_cell=first['name'])
    cells = {cell['name']: [cell[k] for k in ('x', 'y', 'w', 'h')] for cell in atlas['cells']}
    for y, row in enumerate(rows):
        for x, name in enumerate(row):
            if name not in cells:
                raise PixelArtError(f'tile scene layout.rows[{y}][{x}]: unknown tile {name!r}')
    width, height = atlas['cell_size']
    try:
        size = dimensions((width * columns, height * len(rows)))
    except PixelArtError as exc:
        raise PixelArtError(f'tile scene: scene exceeds canvas limits; use fewer placements: {exc}') from exc
    try:
        dimensions((size[0] * scale, size[1] * scale))
    except PixelArtError as exc:
        maximum = min(MAX_SIDE // size[0], MAX_SIDE // size[1],
                      isqrt(MAX_PIXELS // (size[0] * size[1])))
        raise PixelArtError(f'tile scene: {scale}x preview of {size[0]}x{size[1]} exceeds limits; '
                            f'use --scale {maximum} (maximum integer scale)') from exc
    placements = [dict(id=f'tile-{x}-{y}', tile=name, grid=[x, y],
                       source_rect=cells[name], rect=[x * width, y * height, width, height])
                  for y, row in enumerate(rows) for x, name in enumerate(row)]
    return size, placements, atlas, provenance


def _adjacencies(rows, size, placements, assembly):
    """Complete name/position mapping, including seams omitted by assembly views."""
    columns = len(rows[0])
    views = {}
    for i, view in enumerate(assembly['seam_views']):
        views.setdefault(tuple(view['parts']), []).append(i)
    result = []
    for y, row in enumerate(rows):
        for x, _ in enumerate(row):
            a = placements[y * columns + x]
            ax, ay, w, h = a['rect']
            neighbors = []
            if x + 1 < columns:
                edge = ax + w
                neighbors.append((placements[y * columns + x + 1], 'x', edge, [ay, ay + h],
                                  [max(0, edge - 4), ay, min(size[0], edge + 4) - max(0, edge - 4), h]))
            if y + 1 < len(rows):
                edge = ay + h
                neighbors.append((placements[(y + 1) * columns + x], 'y', edge, [ax, ax + w],
                                  [ax, max(0, edge - 4), w, min(size[1], edge + 4) - max(0, edge - 4)]))
            for b, axis, edge, span, rect in neighbors:
                indices = views.get((a['id'], b['id']), [])
                segments = ((rect[2] + 63) // 64) * ((rect[3] + 63) // 64)
                result.append(dict(placements=[a['id'], b['id']], tiles=[a['tile'], b['tile']],
                                   axis=axis, at=edge, span=span, source_rect=rect,
                                   seam_view_indices=indices, omitted_views=segments - len(indices)))
    return result


def make_files(png_bytes, layout, metadata=None, scale=4, background='checker'):
    """Return bounded encoded outputs, without writing or modifying the inputs."""
    _budget(len(png_bytes) <= MAX_PNG_BYTES, 'PNG exceeds 80 MiB')
    header = png_bytes[:33]
    if len(header) < 33 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise PixelArtError('tile scene: expected a PNG input')
    if header[24] > 8:
        raise PixelArtError('tile scene: PNG bit depth above 8 is unsupported')
    with Image.open(BytesIO(png_bytes)) as image:
        dimensions(image.size)
        if getattr(image, 'n_frames', 1) != 1:
            raise PixelArtError('tile scene: animation/multiframe PNG is unsupported')
        size, placements, atlas, provenance = _plan(image, metadata, layout, scale)
        project = dict(version=1, size=list(size), require_coverage=True, parts=[
            dict(name=p['id'], image='atlas.png', at=p['rect'][:2], crop=p['source_rect'], mode='copy')
            for p in placements])
        scene, assembly = assemble(project, {'atlas.png': image.convert('RGBA')})
        seams = seam_sheet(scene, assembly)
        adjacencies = _adjacencies(layout['rows'], size, placements, assembly)
        record = dict(version=1, size=list(image.size), mode=image.mode, atlas=atlas,
                      rgba_sha256=rgba_digest(image))
        artifacts = {'atlas.png': png_bytes, 'atlas-layout.json': record, 'layout.json': layout,
                     'scene.png': scene, 'preview.png': make_preview(scene, scale, background),
                     'seams.png': seams, 'project.json': project}
        files, byte_count = {}, 0
        for name, artifact in artifacts.items():
            data = encoded(artifact)
            byte_count += len(data)
            _budget(byte_count <= MAX_OUTPUT_BYTES, 'encoded delivery exceeds 128 MiB')
            files[name] = data
        report = dict(version=1, kind='named-tile-scene',
            input=dict(file='atlas.png', png_sha256=hashlib.sha256(png_bytes).hexdigest(),
                       rgba_sha256=record['rgba_sha256'], size=list(image.size), provenance=provenance),
            layout=dict(file='layout.json', sha256=hashlib.sha256(files['layout.json']).hexdigest(),
                        columns=len(layout['rows'][0]), rows=len(layout['rows']), tile_size=atlas['cell_size']),
            size=list(size), preview_scale=scale, preview_background=background,
            placements=placements, adjacencies=adjacencies,
            adjacency_count=len(adjacencies), omitted_adjacency_views=sum(a['omitted_views'] for a in adjacencies),
            assembly=assembly, delivery=dict(files=list(OUTPUT_NAMES),
                sha256={name: hashlib.sha256(data).hexdigest() for name, data in files.items()}),
            note='Open preview.png for context, scene.png at native size and seams.png for close-ups. '
                 'Adjacency seam_view_indices are zero-based indices into assembly.seam_views; omitted_views '
                 'counts undisplayed 64px segments, including adjacencies beyond assembly\'s seam cap. '
                 'Coverage and matching edges do not certify visual continuity or tile meaning. '
                 'Keep the entire directory; use a new directory for each revision. Check all listed files '
                 'and hashes (report.json has no self-hash); interruption can leave an incomplete directory.')
        data = encoded(report)
        _budget(byte_count + len(data) <= MAX_OUTPUT_BYTES, 'encoded delivery exceeds 128 MiB')
        files['report.json'] = data
    return files


def _read(path, maximum, label):
    with path.open('rb') as handle:
        data = handle.read(maximum + 1)
    _budget(len(data) <= maximum, f'{label} exceeds {maximum} bytes')
    return data


def main():
    cli = parser(__doc__)
    cli.epilog = 'Open preview.png, scene.png at 1:1, then seams.png; report.json maps tile names and omitted views. Use a new directory for each revision.'
    cli.add_argument('--image', type=Path, required=True, help='Single-frame PNG with a named atlas.')
    cli.add_argument('--metadata', type=Path, help='Matching render --metadata file; optional with embedded layout.')
    cli.add_argument('--layout', type=Path, required=True, help='JSON: {"version":1,"rows":[["grass","path"]]}; names are exact.')
    cli.add_argument('--scale', type=int, default=4, help='Positive integer preview enlargement (default: 4).')
    cli.add_argument('--background', default='checker', help='Preview background: checker or RRGGBB[AA].')
    args = cli.parse_args()
    if args.force:
        raise PixelArtError('tile scene: --force is unsupported; use a new directory for each revision')
    destination = args.out_dir.resolve()
    if destination.exists():
        raise PixelArtError('tile scene: output directory already exists; choose a new directory')
    portable = resolve_portable_output(args.portable_output)
    layout = parse_json(_read(args.layout, MAX_JSON_BYTES, 'layout').decode('utf-8-sig'))
    metadata = parse_json(_read(args.metadata, MAX_JSON_BYTES, 'metadata').decode('utf-8-sig')) if args.metadata else None
    files = make_files(_read(args.image, MAX_PNG_BYTES, 'PNG'), layout, metadata, args.scale, args.background)
    check_alias([args.image, args.metadata, args.layout], [destination / name for name in files])
    destination.mkdir(parents=True, exist_ok=False)
    try:
        publish({destination / name: data for name, data in files.items()}, portable=portable)
    except (OSError, ValueError) as error:
        try:
            destination.rmdir()  # Never remove another writer's additions recursively.
        except OSError:
            raise PixelArtError(f'tile scene: incomplete directory retained at {destination}; {error}') from error
        raise
    print(json.dumps(dict(out_dir=str(destination), files=list(OUTPUT_NAMES),
                          note='Inspect preview.png, native scene.png and seams.png; geometric coverage is not visual acceptance.')))


if __name__ == '__main__':
    entry(main)
