"""Preview a single PNG repeated three times along explicitly chosen axes."""
import hashlib
from io import BytesIO
from math import isqrt
from pathlib import Path

from _common import emit, entry, make_preview, parser, PixelArtError
from PIL import Image
from pixelart.assembly import assemble, seam_sheet
from pixelart.cli import check_alias
from pixelart.core import dimensions, integer, MAX_PIXELS, MAX_SIDE
from pixelart.metadata import rgba_digest


OUTPUT_NAMES = ('source.png', 'repeated.png', 'preview.png', 'seams.png',
                'project.json', 'report.json')


def _size(size, label, hint):
    try:
        return dimensions(size)
    except PixelArtError as exc:
        raise PixelArtError(f'tile preview {label}: {exc}; {hint}') from exc


def make_files(png_bytes, axis, scale=4, background='checker'):
    """Return portable outputs; source bytes and repeated RGBA stay unchanged.

    Preview backgrounds and seam markers are diagnostic only. Assembly validity
    establishes rectangular coverage, never visual continuity.
    """
    if axis not in ('x', 'y', 'xy'):
        raise PixelArtError('tile preview axis: choose x, y or xy explicitly')
    integer(scale, 'scale', 1)
    header = png_bytes[:33]
    if len(header) < 33 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise PixelArtError('tile preview: expected a PNG input')
    if header[24] > 8:
        raise PixelArtError('tile preview: PNG bit depth above 8 is not supported')
    repeats = [3 if 'x' in axis else 1, 3 if 'y' in axis else 1]
    with Image.open(BytesIO(png_bytes)) as opened:
        width, height = _size(opened.size, 'source', 'use a smaller source crop')
        if getattr(opened, 'n_frames', 1) != 1:
            raise PixelArtError('tile preview: expected a single-frame PNG; animation is unsupported')
        size = _size((width * repeats[0], height * repeats[1]), 'repeat',
                     'use a smaller source crop; the source is never resized')
        preview_size = (size[0] * scale, size[1] * scale)
        try:
            dimensions(preview_size)
        except PixelArtError as exc:
            maximum = min(MAX_SIDE // size[0], MAX_SIDE // size[1],
                          isqrt(MAX_PIXELS // (size[0] * size[1])))
            raise PixelArtError(f'tile preview: repeated image {size[0]}x{size[1]}; '
                f'{scale}x preview {preview_size[0]}x{preview_size[1]} exceeds limits '
                f'({MAX_SIDE} per side, {MAX_PIXELS} pixels); '
                f'use --scale {maximum} (maximum integer scale)') from exc
        source = opened.convert('RGBA')

    project = dict(version=1, size=list(size), require_coverage=True, parts=[
        dict(name=f'tile-{column}-{row}', image='source.png',
             at=[column * width, row * height], mode='copy')
        for row in range(repeats[1]) for column in range(repeats[0])])
    repeated, assembly = assemble(project, {'source.png': source})
    seams = seam_sheet(repeated, assembly)
    report = dict(version=1,
        input=dict(file='source.png', sha256=hashlib.sha256(png_bytes).hexdigest(),
                   rgba_sha256=rgba_digest(source), size=[width, height], bit_depth=header[24]),
        axis=axis, repeats=repeats, size=list(size), preview_scale=scale,
        preview_background=background,
        seam_lines=[dict(axis='x', at=column * width, span=[0, size[1]])
                    for column in range(1, repeats[0])] +
                   [dict(axis='y', at=row * height, span=[0, size[0]])
                    for row in range(1, repeats[1])],
        assembly=assembly,
        note='Assembly valid means geometric coverage only. Inspect source.png, repeated.png '
             'and seams.png for continuity along the declared axes. Preview backgrounds and '
             'seam markers do not modify repeated.png. Seam close-ups may be omitted; see '
             'assembly.omitted_seam_views and inspect the full repeated image.')
    return {'source.png': png_bytes, 'repeated.png': repeated,
            'preview.png': make_preview(repeated, scale, background),
            'seams.png': seams, 'project.json': project, 'report.json': report}


def main():
    cli = parser(__doc__)
    cli.epilog = 'Open preview.png for the overall repeat, then seams.png for close-ups. repeated.png is the native-size result.'
    cli.add_argument('--image', type=Path, required=True, help='Single-frame PNG to repeat.')
    cli.add_argument('--axis', choices=('x', 'y', 'xy'), required=True,
                     help='x: left/right (3x1); y: up/down (1x3); xy: both (3x3).')
    cli.add_argument('--scale', type=int, default=4, help='Positive integer preview enlargement (default: 4).')
    cli.add_argument('--background', default='checker', help='Preview background: checker or RRGGBB[AA].')
    args = cli.parse_args()
    check_alias([args.image], [args.out_dir / name for name in OUTPUT_NAMES])
    emit(args, make_files(args.image.read_bytes(), args.axis, args.scale, args.background))


if __name__ == '__main__':
    entry(main)
