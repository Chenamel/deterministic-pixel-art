"""Deliver one flat pixel asset with an editable source and portable previews."""

from io import BytesIO
import json
from math import isqrt
from pathlib import Path
from struct import unpack_from
import zipfile

from _common import entry, make_preview, parser, resolve_portable_output
from PIL import Image
from pixelart import PixelArtError, image_to_spec, render
from pixelart.cli import check_alias
from pixelart.compat import require_pillow
from pixelart.core import MAX_PIXELS, MAX_SIDE, color, dimensions, integer
from pixelart.jsonio import read_json
from pixelart.metadata import merge_layout, rgba_digest
from pixelart.output import encoded, publish


OUTPUT_NAMES = ('asset.png', 'asset.json', 'native.png', 'nearest.png', 'REBUILD.md')
PNG_NATIVE_OUTPUT_NAMES = (
    'asset.png',
    'manifest.json',
    'native.png',
    'nearest.png',
    'REBUILD.md',
)
REBUILD_GUIDE = """# Rebuild

Keep `asset.json` beside this file. From this directory, run the command below
after replacing `<skill>` with the path to your installed skill directory.

```text
python "<skill>/scripts/pixel_art.py" render --spec asset.json --out rebuilt.png
```

Keep any original drawing layers, object structure or painting scripts alongside
the delivery.
"""
PNG_NATIVE_REBUILD_GUIDE = """# Rebuild (PNG-Native)

This delivery keeps the lossless 8-bit RGBA `asset.png` as pixel truth without
forcing a flat JSON grid conversion (avoiding the 62-color scanline expansion
cliff). Verify integrity against `manifest.json` or use `asset_toolkit.py` for
masked local edits.

```text
python "<skill>/scripts/recipes/asset_toolkit.py" verify --image asset.png
```

Keep any original drawing layers, atlas layout sidecar or painting scripts
alongside the delivery.
"""


def _check_preview_size(size, scale):
    width, height = size
    maximum = min(
        MAX_SIDE // width, MAX_SIDE // height, isqrt(MAX_PIXELS // (width * height))
    )
    if scale > maximum:
        raise PixelArtError(
            f'single asset: {scale}x preview exceeds image limits for {width}x{height}; '
            f'use --scale {maximum} or smaller'
        )


def _read_png(source, metadata, scale):
    with source.open('rb') as handle:
        header = handle.read(33)
        if (
            len(header) < 33
            or header[:8] != b'\x89PNG\r\n\x1a\n'
            or header[8:16] != b'\x00\x00\x00\x0dIHDR'
        ):
            raise PixelArtError('single asset: expected a PNG input')
        if header[24] > 8:
            raise PixelArtError('single asset: PNG bit depth above 8 is not supported')
        size = dimensions(unpack_from('>II', header, 16))
        _check_preview_size(size, scale)
        handle.seek(0)
        with Image.open(handle, formats=('PNG',)) as opened:
            if getattr(opened, 'n_frames', 1) != 1:
                raise PixelArtError(
                    'single asset: animated or multiframe PNG is unsupported'
                )
            metadata_value = read_json(metadata) if metadata is not None else None
            # Pillow reads text chunks after the image data during load().
            opened.load()
            merged, _ = merge_layout(opened, metadata=metadata_value)
            if 'atlas' in merged:
                raise PixelArtError(
                    'single asset: named atlas detected; use import --metadata <layout.json> '
                    '--cell <name>, or continue with the named atlas workflow'
                )
            return opened.convert('RGBA')


def make_files(
    source,
    metadata=None,
    *,
    scale=4,
    background='checker',
    source_mode='json-v1',
):
    """Build a flat single-asset delivery from a JSON v1 spec or PNG file."""
    source = Path(source)
    integer(scale, 'scale', 1)
    if background != 'checker':
        color(background)
    if source_mode not in ('json-v1', 'png-native'):
        raise PixelArtError(
            'single asset: --source-mode must be json-v1 or png-native'
        )

    if source.suffix.lower() == '.json':
        if source_mode == 'png-native':
            raise PixelArtError(
                'single asset: --source-mode png-native only applies to PNG inputs'
            )
        if metadata is not None:
            raise PixelArtError('single asset: --metadata only applies to PNG inputs')
        spec = read_json(source)
        if not isinstance(spec, dict):
            raise PixelArtError(
                'single asset: expected a JSON object for the pixel source'
            )
        if spec.get('kind') == 'atlas':
            raise PixelArtError(
                'single asset: named atlas source retains cell names; use the named atlas workflow'
            )
        if spec.get('kind') == 'preview':
            raise PixelArtError(
                'single asset: use the underlying source of the preview; '
                'use the named atlas workflow for an atlas'
            )
        image = render(spec)
        _check_preview_size(image.size, scale)
    elif source.suffix.lower() == '.png':
        image = _read_png(source, metadata, scale)
        if source_mode == 'png-native':
            native = make_preview(image, 1, background)
            nearest = make_preview(image, scale, background)
            manifest = {
                'version': 1,
                'source_mode': 'png-native',
                'size': list(image.size),
                'rgba_sha256': rgba_digest(image),
                'note': 'Lossless 8-bit PNG preserved without forced JSON grid flattening.',
            }
            return {
                'asset.png': encoded(image),
                'manifest.json': encoded(manifest),
                'native.png': encoded(native),
                'nearest.png': encoded(nearest),
                'REBUILD.md': PNG_NATIVE_REBUILD_GUIDE.encode('utf-8'),
            }
        spec = image_to_spec(image)
        if render(spec).tobytes() != image.tobytes():
            raise PixelArtError(
                'single asset: imported source failed exact RGBA reconstruction'
            )
    else:
        raise PixelArtError('single asset: expected a .png image or .json pixel source')

    native = make_preview(image, 1, background)
    nearest = make_preview(image, scale, background)
    return {
        'asset.png': encoded(image),
        'asset.json': encoded(spec),
        'native.png': encoded(native),
        'nearest.png': encoded(nearest),
        'REBUILD.md': REBUILD_GUIDE.encode('utf-8'),
    }


def main():
    cli = parser(__doc__)
    cli.epilog = (
        'Keep the original painting source or layers separately when they are needed.'
    )
    cli.add_argument(
        '--source',
        type=Path,
        required=True,
        help='One PNG image or JSON v1 pixel source.',
    )
    cli.add_argument(
        '--metadata',
        type=Path,
        help='Optional PNG layout sidecar used to detect a named atlas.',
    )
    cli.add_argument(
        '--source-mode',
        choices=('json-v1', 'png-native'),
        default='json-v1',
        help='Default json-v1 keeps full backward compatibility; png-native keeps lossless PNG without forced JSON grid flattening.',
    )
    cli.add_argument(
        '--scale',
        type=int,
        default=4,
        help='Nearest-neighbor preview scale (default: 4).',
    )
    cli.add_argument(
        '--background',
        default='checker',
        help='Preview background: checker or an RGBA color.',
    )
    cli.add_argument(
        '--pack-zip',
        type=Path,
        help='Optional ZIP path containing the five delivery files.',
    )
    args = cli.parse_args()

    require_pillow()
    output_names = (
        PNG_NATIVE_OUTPUT_NAMES
        if args.source_mode == 'png-native'
        else OUTPUT_NAMES
    )
    outputs = [args.out_dir / name for name in output_names]
    if args.pack_zip:
        outputs.append(args.pack_zip)
    check_alias([args.source, args.metadata], outputs)
    files = make_files(
        args.source,
        args.metadata,
        scale=args.scale,
        background=args.background,
        source_mode=args.source_mode,
    )
    artifacts = {args.out_dir / name: data for name, data in files.items()}
    if args.pack_zip:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            for name in output_names:
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED)
        artifacts[args.pack_zip] = buffer.getvalue()
    publish(
        artifacts,
        force=args.force,
        portable=resolve_portable_output(args.portable_output),
    )
    print(
        json.dumps(
            {
                'out_dir': str(args.out_dir.resolve()),
                'files': sorted(output_names),
                'zip': str(args.pack_zip.resolve()) if args.pack_zip else None,
            }
        )
    )


if __name__ == '__main__':
    entry(main)
