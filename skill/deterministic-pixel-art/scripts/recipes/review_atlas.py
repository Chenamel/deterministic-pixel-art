"""View every named atlas cell at native size across bounded contact-sheet pages."""
from io import BytesIO
import hashlib
import json
from pathlib import Path

from _common import entry, parser, PixelArtError
from PIL import Image, ImageDraw, ImageFont
from pixelart.cli import check_alias
from pixelart.context import _context
from pixelart.core import dimensions, integer
from pixelart.jsonio import parse_json
from pixelart.metadata import merge_layout, rgba_digest
from pixelart.output import encoded, publish, resolve_portable_output

MAX_CELLS = 4096
MAX_TILES = 4096
MAX_PAGES = 64
TILE_SIDE = 128
MAX_PAGE_PIXELS = 4_194_304
MAX_TOTAL_PIXELS = 67_108_864
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024
MAX_PNG_BYTES = 80 * 1024 * 1024
BACKGROUNDS = (('dark', (23, 32, 51, 255)), ('light', (233, 237, 242, 255)))


def _budget(ok, message):
    if not ok:
        raise PixelArtError('atlas review: ' + message + '; split the atlas into smaller named layouts')


def _plan(image, metadata, blocks_per_page):
    integer(blocks_per_page, 'blocks-per-page', 1)
    if blocks_per_page > 64:
        raise PixelArtError('blocks-per-page: choose 1 to 64 native blocks per page; a large cell may span pages')
    if metadata is not None:
        _budget(len(json.dumps(metadata, ensure_ascii=True).encode('utf-8')) <= MAX_METADATA_BYTES,
                'metadata exceeds 1 MiB')
    merged, provenance = merge_layout(image, metadata=metadata, require_bound_atlas=True)
    atlas = merged.get('atlas')
    if not isinstance(atlas, dict) or not isinstance(atlas.get('cells'), list) or not atlas['cells']:
        raise PixelArtError('atlas review: requires a nonempty named atlas')
    _budget(len(atlas['cells']) <= MAX_CELLS, f'more than {MAX_CELLS} cells')
    first = atlas['cells'][0]
    if not isinstance(first, dict) or not isinstance(first.get('name'), str) or not first['name']:
        raise PixelArtError('atlas review: expected a nonempty first cell name')
    # Existing selected-cell validation checks EVERY layout entry before selection.
    # We consume all entries only after this full validation; default limits stay unchanged.
    _context(merged, image.size, selected_cell=first['name'])
    cells, tiles = [], []
    for ordinal, cell in enumerate(atlas['cells'], 1):
        x, y, w, h = (cell[key] for key in ('x', 'y', 'w', 'h'))
        count = ((w + TILE_SIDE - 1) // TILE_SIDE) * ((h + TILE_SIDE - 1) // TILE_SIDE)
        _budget(len(tiles) + count <= MAX_TILES, f'more than {MAX_TILES} native blocks')
        ids = []
        for dy in range(0, h, TILE_SIDE):
            for dx in range(0, w, TILE_SIDE):
                ids.append(len(tiles) + 1)
                tiles.append(dict(id=len(tiles) + 1, cell=ordinal, part=len(ids),
                                  source_rect=[x + dx, y + dy, min(TILE_SIDE, w - dx), min(TILE_SIDE, h - dy)]))
        cells.append(dict(id=ordinal, name=cell['name'], source_rect=[x, y, w, h], blocks=ids))
    page_count = (len(tiles) + blocks_per_page - 1) // blocks_per_page
    _budget(page_count <= MAX_PAGES, f'more than {MAX_PAGES} pages; increase --blocks-per-page up to 64')
    pages, total_pixels = [], 0
    for start in range(0, len(tiles), blocks_per_page):
        batch = tiles[start:start + blocks_per_page]
        columns = min(8, len(batch))
        card_w = max(192, max(tile['source_rect'][2] for tile in batch) * 2 + 24)
        card_h = max(tile['source_rect'][3] for tile in batch) + 40
        size = [columns * card_w, ((len(batch) + columns - 1) // columns) * card_h + 32]
        _budget(max(size) <= 8192 and size[0] * size[1] <= MAX_PAGE_PIXELS,
                f'page exceeds {MAX_PAGE_PIXELS} pixels')
        total_pixels += size[0] * size[1]
        _budget(total_pixels <= MAX_TOTAL_PIXELS, f'pages exceed {MAX_TOTAL_PIXELS} total pixels')
        number = len(pages) + 1
        for slot, tile in enumerate(batch):
            x, y = slot % columns * card_w + 8, slot // columns * card_h + 64
            w, h = tile['source_rect'][2:]
            tile.update(page=number, views=[dict(background=name, sheet_rect=[x + i * (w + 8), y, w, h], scale=1)
                                           for i, (name, _) in enumerate(BACKGROUNDS)])
        pages.append(dict(number=number, file=f'page-{number:04d}.png', size=size,
                          blocks=[tile['id'] for tile in batch], card_size=[card_w, card_h], columns=columns))
    for cell in cells:
        cell['pages'] = sorted({tiles[i - 1]['page'] for i in cell['blocks']})
    return dict(version=1, kind='atlas-native-pages', input=dict(size=list(image.size), rgba_sha256=rgba_digest(image)),
                provenance=provenance, cells=cells, blocks=tiles, pages=pages, page_count=len(pages),
                backgrounds=[dict(name=name, rgba=list(rgba)) for name, rgba in BACKGROUNDS],
                coverage=dict(scope='declared cells only; unnamed grid positions are excluded',
                              declared_cells=len(cells), native_blocks=len(tiles), omitted_cells=0,
                              omitted_declared_pixels=0, declared_pixels=sum(c['source_rect'][2] * c['source_rect'][3] for c in cells)),
                limits=dict(cells=MAX_CELLS, native_blocks=MAX_TILES, native_block_side=TILE_SIDE,
                            blocks_per_page=blocks_per_page, pages=MAX_PAGES, page_pixels=MAX_PAGE_PIXELS,
                            total_page_pixels=MAX_TOTAL_PIXELS, encoded_bytes=MAX_OUTPUT_BYTES),
                total_page_pixels=total_pixels,
                note='Open every listed page at native size. Each block is shown on dark (left) and light (right). '
                     'Full names are in this index; page captions use cell/block IDs. Large cells span blocks/pages. '
                     'This is coverage visualization, not the review command\'s warnings or a quality judgment. '
                     'A complete index lists the authoritative output set; interruption can leave an incomplete directory.')


def _page(image, index, page):
    sheet = Image.new('RGB', page['size'], '#101827')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=10)
    draw.text((8, 4), f"ATLAS {page['number']}/{index['page_count']} / native 1:1", font=font, fill='#E9EDF2')
    draw.text((8, 16), 'dark | light; names: index.json', font=font, fill='#E9EDF2')
    cw = page['card_size'][0]
    for slot, ident in enumerate(page['blocks']):
        tile = index['blocks'][ident - 1]
        x, y, w, h = tile['source_rect']
        piece = image.crop((x, y, x + w, y + h)).convert('RGBA')
        caption = Image.new('RGB', (cw - 16, 24), '#101827')
        text = ImageDraw.Draw(caption)
        text.text((0, 0), f"cell {tile['cell']} / block {tile['part']}", font=font, fill='#E9EDF2')
        text.text((0, 12), f'[{x},{y},{w},{h}] / 1:1', font=font, fill='#E9EDF2')
        sx, sy = tile['views'][0]['sheet_rect'][:2]
        sheet.paste(caption, (sx, sy - 28))
        for view, (_, rgba) in zip(tile['views'], BACKGROUNDS):
            background = Image.new('RGBA', piece.size, rgba)
            background.alpha_composite(piece)
            sheet.paste(background.convert('RGB'), tuple(view['sheet_rect'][:2]))
        piece.close()
    return sheet


def make_files(png_bytes, metadata=None, blocks_per_page=64):
    """Prepare bounded encoded pages and their complete index without file writes."""
    _budget(len(png_bytes) <= MAX_PNG_BYTES, 'PNG exceeds 80 MiB')
    header = png_bytes[:33]
    if len(header) < 33 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise PixelArtError('atlas review: expected a PNG input')
    if header[24] > 8:
        raise PixelArtError('atlas review: PNG bit depth above 8 is unsupported')
    with Image.open(BytesIO(png_bytes)) as image:
        dimensions(image.size)
        if getattr(image, 'n_frames', 1) != 1:
            raise PixelArtError('atlas review: animation/multiframe PNG is unsupported')
        index = _plan(image, metadata, blocks_per_page)
        index['input']['png_sha256'] = hashlib.sha256(png_bytes).hexdigest()
        files, byte_count = {}, 0
        for page in index['pages']:
            sheet = _page(image, index, page)
            data = encoded(sheet)
            sheet.close()
            byte_count += len(data)
            _budget(byte_count <= MAX_OUTPUT_BYTES, 'encoded pages exceed 32 MiB')
            page.update(sha256=hashlib.sha256(data).hexdigest(), encoded_bytes=len(data))
            files[page['file']] = data
        data = encoded(index)
        _budget(byte_count + len(data) <= MAX_OUTPUT_BYTES, 'encoded delivery exceeds 32 MiB')
        files['index.json'] = data
    return files


def _read(path, maximum, label):
    with path.open('rb') as handle:
        data = handle.read(maximum + 1)
    if len(data) > maximum:
        raise PixelArtError(f'atlas review: {label} exceeds {maximum} bytes; split the input')
    return data


def main():
    cli = parser(__doc__)
    cli.epilog = 'Open index.json, then every listed page at 1:1. Names and global coordinates are in the index. Use a new directory for every revision.'
    cli.add_argument('--image', type=Path, required=True, help='Single-frame PNG with a named atlas.')
    cli.add_argument('--metadata', type=Path, help='Matching render --metadata file; optional with embedded layout.')
    cli.add_argument('--blocks-per-page', type=int, default=64,
                     help='Maximum native blocks per page, 1–64 (default 64); a large cell may span pages.')
    args = cli.parse_args()
    if args.force:
        raise PixelArtError('atlas review: --force is unsupported; use a new directory to avoid obsolete pages')
    destination = args.out_dir.resolve()
    if destination.exists():
        raise PixelArtError('atlas review: output directory already exists; choose a new directory')
    portable = resolve_portable_output(args.portable_output)
    metadata = parse_json(_read(args.metadata, MAX_METADATA_BYTES, 'metadata').decode('utf-8-sig')) if args.metadata else None
    files = make_files(_read(args.image, MAX_PNG_BYTES, 'PNG'), metadata, args.blocks_per_page)
    check_alias([args.image, args.metadata], [destination / name for name in files])
    destination.mkdir(parents=True, exist_ok=False)
    try:
        publish({destination / name: data for name, data in files.items()}, portable=portable)
    except (OSError, ValueError) as error:
        try:
            destination.rmdir()  # Never recursively remove another writer's additions.
        except OSError:
            raise PixelArtError(f'atlas review: incomplete directory retained at {destination}; {error}') from error
        raise
    print(json.dumps(dict(out_dir=str(destination), index='index.json', pages=len(files) - 1,
                          note='Inspect every listed page at native size; coverage is not aesthetic acceptance.')))


if __name__ == '__main__':
    entry(main)
