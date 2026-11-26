#!/usr/bin/env python3
"""Direct executable entrypoint and Python API re-export; works from any current directory."""
try:
    from pixelart import (
        Canvas,
        PixelArtError,
        __all__,
        __version__,
        assemble,
        color,
        image_to_spec,
        inspect_image,
        make_preview,
        outline,
        recolor_image,
        render,
        replace_cell,
        validate,
        verify_edit,
    )
    from pixelart.cli import main
except ModuleNotFoundError as exc:
    if exc.name == 'PIL' or (exc.name or '').startswith('PIL.'):
        import json
        import sys
        print(json.dumps({'error': 'Pillow is missing; install requirements.txt (Pillow==12.3.0 baseline)'}), file=sys.stderr)
        raise SystemExit(2) from None
    raise

if __name__ == '__main__':
    raise SystemExit(main())
