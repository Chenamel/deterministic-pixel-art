"""Portable CLI; invalid specs/rules fail before output creation. Errors are JSON."""
import argparse
import json
from pathlib import Path
import sys

from PIL import Image, UnidentifiedImageError
from . import PixelArtError, make_preview, render, validate


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PixelArtError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Deterministic pixel asset renderer (JSON v1 / DSL).')
    commands = parser.add_subparsers(dest='command', required=True)
    draw = commands.add_parser('render')
    draw.add_argument('--spec', type=Path, required=True)
    draw.add_argument('--out', type=Path, required=True)
    draw.add_argument('--preview', type=Path)
    draw.add_argument('--metadata', type=Path)
    draw.add_argument('--scale', type=int, default=8)
    draw.add_argument('--rules', type=Path)
    draw.add_argument('--force', action='store_true')
    preview = commands.add_parser('preview')
    preview.add_argument('--image', type=Path, required=True)
    preview.add_argument('--out', type=Path, required=True)
    preview.add_argument('--scale', type=int, default=8)
    preview.add_argument('--background', default='checker')
    preview.add_argument('--force', action='store_true')
    check = commands.add_parser('validate')
    check.add_argument('--image', type=Path, required=True)
    check.add_argument('--rules', type=Path)
    args = parser.parse_args(argv)
    try:
        outputs = [p.resolve() for p in (getattr(args, 'out', None),
                   getattr(args, 'preview', None), getattr(args, 'metadata', None)) if p]
        inputs = [p.resolve() for p in (getattr(args, 'spec', None),
                  getattr(args, 'image', None), getattr(args, 'rules', None)) if p]
        if len(set(outputs)) != len(outputs) or set(outputs) & set(inputs):
            raise PixelArtError('output paths must be distinct and must not replace inputs')
        if not getattr(args, 'force', False) and any(p.exists() for p in outputs):
            raise PixelArtError('output already exists; choose another path or use --force')
        if args.command == 'render':
            spec = (args.spec.read_text(encoding='utf-8-sig') if args.spec.suffix.lower() == '.dsl'
                    else read_json(args.spec))
            image = render(spec)
            report = validate(image, read_json(args.rules) if args.rules else None)
            if not report['valid']:
                print(json.dumps(report, ensure_ascii=False))
                return 1
            enlarged = make_preview(image, args.scale) if args.preview else None
            metadata = {'size': list(image.size), 'mode': image.mode,
                        'atlas': image.info.get('pixelart')}
            # All rendering/validation and path checks complete before any file write.
            for path in outputs:
                path.parent.mkdir(parents=True, exist_ok=True)
            image.save(args.out, format='PNG')
            if enlarged:
                enlarged.save(args.preview, format='PNG')
            if args.metadata:
                args.metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({'output': str(args.out.resolve()), **metadata}, ensure_ascii=False))
        else:
            with Image.open(args.image) as opened:
                image = opened.copy()
            if args.command == 'validate':
                report = validate(image, read_json(args.rules) if args.rules else None)
                print(json.dumps(report, ensure_ascii=False))
                return 0 if report['valid'] else 1
            image = make_preview(image, args.scale, None if args.background == 'transparent' else args.background)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            image.save(args.out, format='PNG')
            print(json.dumps({'output': str(args.out.resolve()), 'size': list(image.size)}, ensure_ascii=False))
        return 0
    except (PixelArtError, OSError, ValueError, UnidentifiedImageError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
