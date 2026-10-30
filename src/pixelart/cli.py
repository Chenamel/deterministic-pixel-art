"""Portable CLI; invalid specs/rules fail before output creation. Errors are JSON."""
import argparse
import json
from pathlib import Path
import sys

from PIL import Image, UnidentifiedImageError
from . import PixelArtError, make_preview, render, validate
from .compat import require_pillow
from .output import add_output_options, publish, resolve_portable_output
from .jsonio import read_json


def check_alias(inputs, outputs):
    inputs={Path(p).resolve() for p in inputs if p is not None}
    outputs=[Path(p).resolve() for p in outputs if p is not None]
    if len(set(outputs))!=len(outputs) or inputs & set(outputs):
        raise PixelArtError('output paths must be distinct and must not replace inputs')


def read_image(path):
    from .core import dimensions
    with Image.open(path) as opened:
        dimensions(opened.size)
        return opened.copy()


def main(argv=None):
    # JSON and Unicode paths have a stable wire encoding even on legacy Windows locales.
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Deterministic pixel asset renderer (JSON v1 / DSL).')
    commands = parser.add_subparsers(dest='command', required=True)
    draw = commands.add_parser('render')
    draw.add_argument('--spec', type=Path, required=True)
    draw.add_argument('--out', type=Path, required=True)
    draw.add_argument('--preview', type=Path)
    draw.add_argument('--preview-background',default='checker',help='Background for --preview: checker, transparent or RRGGBB.')
    draw.add_argument('--metadata', type=Path)
    draw.add_argument('--embed-metadata', action='store_true')
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
    review_cmd = commands.add_parser('review', help='Advisory contact sheet and contextual warnings; never edits the input.')
    review_cmd.add_argument('--image', type=Path, required=True)
    review_cmd.add_argument('--out-dir', type=Path, required=True)
    review_cmd.add_argument('--context', type=Path)
    review_cmd.add_argument('--compare', type=Path)
    review_cmd.add_argument('--metadata', type=Path)
    review_cmd.add_argument('--force', action='store_true')
    inspect_cmd=commands.add_parser('inspect',help='Bounded pixel facts and optional exact symbol grid.')
    inspect_cmd.add_argument('--image',type=Path,required=True)
    inspect_cmd.add_argument('--context',type=Path)
    inspect_cmd.add_argument('--metadata',type=Path)
    inspect_cmd.add_argument('--compare',type=Path)
    scope=inspect_cmd.add_mutually_exclusive_group()
    scope.add_argument('--region',type=int,nargs=4,metavar=('X','Y','W','H'))
    scope.add_argument('--cell')
    inspect_cmd.add_argument('--grid',action='store_true')
    inspect_cmd.add_argument('--out',type=Path)
    inspect_cmd.add_argument('--force',action='store_true')
    ingest_cmd=commands.add_parser('import',help='Lossless decoded 8-bit PNG to an editable JSON v1 spec.')
    ingest_cmd.add_argument('--image',type=Path,required=True)
    ingest_cmd.add_argument('--out',type=Path,required=True)
    ingest_scope=ingest_cmd.add_mutually_exclusive_group()
    ingest_scope.add_argument('--region',type=int,nargs=4,metavar=('X','Y','W','H'))
    ingest_scope.add_argument('--cell',help='Import one named cell using verified sidecar, embedded or in-memory layout.')
    ingest_cmd.add_argument('--metadata',type=Path,help='Verified layout: import editable named cells with exact RGBA copy assembly.')
    ingest_cmd.add_argument('--force',action='store_true')
    replace_cmd=commands.add_parser('replace-cell',help='Replace one named atlas cell; optionally render PNG and fresh metadata.')
    replace_cmd.add_argument('--spec',type=Path,required=True)
    replace_cmd.add_argument('--cell',required=True)
    replace_cmd.add_argument('--replacement',type=Path,required=True)
    replace_cmd.add_argument('--out',type=Path,required=True,help='Editable candidate JSON.')
    replace_cmd.add_argument('--image-out',type=Path)
    replace_cmd.add_argument('--metadata',type=Path,help='Output layout for --image-out.')
    replace_cmd.add_argument('--force',action='store_true')
    verify_cmd=commands.add_parser('verify',help='Check that RGBA edits stay within declared regions or mask; not an aesthetic test.')
    verify_cmd.add_argument('--image',type=Path,required=True)
    verify_cmd.add_argument('--compare',type=Path,required=True)
    verify_cmd.add_argument('--allow-region',type=int,nargs=4,action='append',metavar=('X','Y','W','H'))
    verify_cmd.add_argument('--allow-mask',type=Path)
    verify_cmd.add_argument('--out',type=Path)
    verify_cmd.add_argument('--force',action='store_true')
    assemble_cmd=commands.add_parser('assemble',help='Assemble bounded PNG components with explicit copy/over, overlap and coverage contracts.')
    assemble_cmd.add_argument('--project',type=Path,required=True)
    assemble_cmd.add_argument('--out',type=Path,required=True)
    assemble_cmd.add_argument('--report',type=Path)
    assemble_cmd.add_argument('--seams',type=Path)
    assemble_cmd.add_argument('--preview',type=Path)
    assemble_cmd.add_argument('--scale',type=int,default=2)
    assemble_cmd.add_argument('--preview-background',default='checker')
    assemble_cmd.add_argument('--force',action='store_true')
    for writer in (draw,preview,review_cmd,inspect_cmd,ingest_cmd,replace_cmd,verify_cmd,assemble_cmd):
        add_output_options(writer)
    args = parser.parse_args(argv)
    try:
        require_pillow()
        # Read-only commands do not depend on an output environment setting.
        if args.command != 'validate' and (args.command not in ('inspect', 'verify') or args.out):
            args.portable_output = resolve_portable_output(args.portable_output)
        if args.command=='assemble':
            from .assembly import load_project,assemble,seam_sheet
            project,sources,paths=load_project(args.project)
            check_alias([args.project,*paths],[args.out,args.report,args.seams,args.preview])
            image,report=assemble(project,sources);artifacts={args.out:image}
            if args.seams:artifacts[args.seams]=seam_sheet(image,report)
            if args.preview:
                artifacts[args.preview]=make_preview(image,args.scale,
                    None if args.preview_background=='transparent' else args.preview_background)
            if args.report:artifacts[args.report]=report
            publish(artifacts,force=args.force,portable=args.portable_output)
            print(json.dumps(dict(output=str(args.out.resolve()),parts=len(report['parts']),
                uncovered_pixels=report['uncovered_pixels'],rgba_sha256=report['rgba_sha256'])))
            return 0
        if args.command=='verify':
            from .edit import verify_edit
            check_alias([args.image,args.compare,args.allow_mask],[args.out])
            report=verify_edit(read_image(args.image),read_image(args.compare),regions=args.allow_region,
                mask=read_image(args.allow_mask) if args.allow_mask else None)
            if args.out:publish({args.out:report},force=args.force,portable=args.portable_output)
            print(json.dumps(report,ensure_ascii=False,indent=2))
            return 0 if report['valid'] else 1
        if args.command=='replace-cell':
            from .edit import replace_cell
            from .ingest import spec_bytes
            from .metadata import layout_record
            check_alias([args.spec,args.replacement],[args.out,args.image_out,args.metadata])
            if args.metadata and not args.image_out:raise PixelArtError('replace-cell: --metadata requires --image-out')
            spec=replace_cell(read_json(args.spec),args.cell,read_json(args.replacement))
            artifacts={args.out:spec_bytes(spec)}
            if args.image_out:
                image=render(spec);artifacts[args.image_out]=image
                if args.metadata:artifacts[args.metadata]=layout_record(image)
            publish(artifacts,force=args.force,portable=args.portable_output)
            print(json.dumps(dict(output=str(args.out.resolve()),cell=args.cell),ensure_ascii=False))
            return 0
        if args.command=='inspect':
            from .analysis import inspect_image
            check_alias([args.image,args.context,args.metadata,args.compare],[args.out])
            report=inspect_image(read_image(args.image),read_json(args.context) if args.context else None,
                region=args.region,cell=args.cell,grid=args.grid,
                comparison=read_image(args.compare) if args.compare else None,
                metadata=read_json(args.metadata) if args.metadata else None)
            if args.out:
                publish({args.out:report},force=args.force,portable=args.portable_output)
                print(json.dumps(dict(output=str(args.out.resolve()),advisory=True)))
            else:print(json.dumps(report,ensure_ascii=False,indent=2))
            return 0
        if args.command=='import':
            from .ingest import image_to_spec,spec_bytes
            check_alias([args.image,args.metadata],[args.out])
            with args.image.open('rb') as handle:header=handle.read(33)
            if len(header)<33 or header[:8]!=b'\x89PNG\r\n\x1a\n' or header[12:16]!=b'IHDR':
                raise PixelArtError('import: expected a PNG input')
            if header[24]>8:raise PixelArtError('import: PNG bit depth above 8 is not supported')
            with Image.open(args.image) as opened:
                spec=image_to_spec(opened,region=args.region,metadata=read_json(args.metadata) if args.metadata else None,cell=args.cell)
                imported_size=spec.get('size',list(opened.size))
            publish({args.out:spec_bytes(spec)},force=args.force,portable=args.portable_output)
            print(json.dumps(dict(output=str(args.out.resolve()),kind=spec['kind'],size=imported_size,lossless_rgba=True)))
            return 0
        if args.command == 'review':
            # Keep the optional review module out of existing render/validate startup.
            from .review import review
            source = read_image(args.image)
            comparison = None
            if args.compare:
                comparison = read_image(args.compare)
            report, sheet, difference = review(source,
                read_json(args.context) if args.context else None, comparison,
                metadata=read_json(args.metadata) if args.metadata else None)
            artifacts = {'report.json': report, 'review.png': sheet}
            if difference is not None:
                artifacts['difference.png'] = difference
            inputs = {p.resolve() for p in (args.image, args.context, args.compare,args.metadata) if p}
            destinations = {name: (args.out_dir / name).resolve() for name in artifacts}
            if inputs & set(destinations.values()):
                raise PixelArtError('review outputs must not replace inputs')
            if not args.force and any(p.exists() for p in destinations.values()):
                raise PixelArtError('review output already exists; choose another directory or use --force')
            publish({destinations[name]: artifact for name, artifact in artifacts.items()}, force=args.force,portable=args.portable_output)
            print(json.dumps({'advisory': True, 'warnings': len(report['warnings']),
                              'outputs': {k: str(v) for k,v in destinations.items()}}, ensure_ascii=False))
            return 0
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
            enlarged = make_preview(image, args.scale,
                None if args.preview_background=='transparent' else args.preview_background) if args.preview else None
            from .metadata import layout_record,encode_png
            metadata = layout_record(image)
            artifacts = {args.out: encode_png(image,metadata) if args.embed_metadata else image}
            if enlarged:
                artifacts[args.preview] = enlarged
            if args.metadata:
                artifacts[args.metadata] = metadata
            publish(artifacts, force=args.force,portable=args.portable_output)
            print(json.dumps({'output': str(args.out.resolve()), **metadata}, ensure_ascii=False))
        else:
            with Image.open(args.image) as opened:
                image = opened.copy()
            if args.command == 'validate':
                report = validate(image, read_json(args.rules) if args.rules else None)
                print(json.dumps(report, ensure_ascii=False))
                return 0 if report['valid'] else 1
            image = make_preview(image, args.scale, None if args.background == 'transparent' else args.background)
            publish({args.out: image}, force=args.force,portable=args.portable_output)
            print(json.dumps({'output': str(args.out.resolve()), 'size': list(image.size)}, ensure_ascii=False))
        return 0
    except (PixelArtError, OSError, ValueError, UnidentifiedImageError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
