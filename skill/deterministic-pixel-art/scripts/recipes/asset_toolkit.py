"""Unified pixel-asset workflow toolkit CLI (route, deliver, patch-draw, verify, rebuild)."""

import sys

if __name__ == '__main__':
    # CLI runs leave read-only Skill script trees free of __pycache__ files.
    sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path

from _common import resolve_portable_output
from pixelart.compat import require_pillow
from pixelart.core import PixelArtError
from pixelart.output import add_output_options
from pixelart.toolkit import (
    ContractViolationError,
    SUPPORTED_MODES,
    analyze_advisory,
    check_declared_contract,
    deliver_asset,
    inspect_draw_ops,
    patch_draw,
    rebuild_and_verify,
    route_intent,
    _alpha_diff_stats,
    _read_static_png,
)
from pixelart.edit import verify_edit
from pixelart.jsonio import read_json


def _add_deliver_parser(subparsers):
    cmd = subparsers.add_parser(
        'deliver',
        help='Build, verify (3-tier), preview, independently rebuild, and optionally ZIP-pack an asset.',
    )
    cmd.add_argument('--source', type=Path, required=True, help='Input .json spec/project or .png image.')
    cmd.add_argument('--out-dir', type=Path, required=True, help='Fresh output directory (no silent overwrite).')
    cmd.add_argument(
        '--mode',
        choices=SUPPORTED_MODES,
        default='auto',
        help='Source mode or auto-detect (default: auto). grid accepts JSON v1 kind grid and kind draw.',
    )
    cmd.add_argument('--metadata', type=Path, help='Optional layout.json sidecar for PNG inputs.')
    cmd.add_argument('--baseline', type=Path, help='Original PNG baseline for png-native diff/boundary verification.')
    cmd.add_argument(
        '--allow-region',
        type=int,
        nargs=4,
        action='append',
        metavar=('X', 'Y', 'W', 'H'),
        help='Allowed edit rectangle [x y w h]; repeatable.',
    )
    cmd.add_argument('--mask', type=Path, help='Optional PNG mask (L/1 intensity or RGBA/LA alpha).')
    cmd.add_argument('--recolor', type=Path, help='Optional color-mapping JSON for png-native scoped recolor.')
    cmd.add_argument('--patch', type=Path, help='Optional explicit pixel/rect patch JSON for png-native edit.')
    cmd.add_argument(
        '--allow-alpha-change',
        action='store_true',
        help='Explicitly allow alpha channel changes during png-native local edits.',
    )
    cmd.add_argument('--replace-cell', help='Named atlas cell to replace (atlas mode).')
    cmd.add_argument('--replacement', type=Path, help='Replacement JSON v1 spec for --replace-cell.')
    cmd.add_argument(
        '--disable-patch',
        action='append',
        default=[],
        help='Patch ID to disable for clean local rollback (state-set mode); repeatable.',
    )
    cmd.add_argument('--contract', type=Path, help='Optional declared structural contract JSON.')
    cmd.add_argument('--scale', type=int, default=4, help='Integer nearest-neighbor preview scale (default: 4).')
    cmd.add_argument('--background', default='checker', help='Preview background: checker or RRGGBB[AA].')
    cmd.add_argument('--pack-zip', type=Path, help='Optional deterministic ZIP archive output path.')
    cmd.add_argument(
        '--extra-file',
        type=Path,
        action='append',
        default=[],
        help='Optional extra file (e.g. brief/notes) to include under extras/ and in the ZIP.',
    )
    cmd.add_argument('--force', action='store_true', help='Explicitly allow replacing existing output files.')
    add_output_options(cmd)


def _add_patch_draw_parser(subparsers):
    cmd = subparsers.add_parser(
        'patch-draw',
        help='Inspect draw operation indices or apply one scoped operation slice to a draw spec.',
    )
    cmd.add_argument('--source', type=Path, required=True, help='Editable JSON v1 draw source.')
    cmd.add_argument(
        '--inspect-ops',
        action='store_true',
        help='Read-only mode (accepts only --source, --offset, --limit): print file_sha256 and operation summaries.',
    )
    cmd.add_argument('--offset', type=int, help='First zero-based index to inspect (default: 0).')
    cmd.add_argument('--limit', type=int, help='Operations per inspection page (default: 50, max: 200).')
    cmd.add_argument('--patch', type=Path, help='JSON v1 draw operation slice.')
    cmd.add_argument('--out', type=Path, help='Output editable JSON v1 draw file.')
    cmd.add_argument(
        '--allow-region',
        type=int,
        nargs=4,
        action='append',
        metavar=('X', 'Y', 'W', 'H'),
        help='Allowed edit rectangle [x y w h]; repeatable.',
    )
    cmd.add_argument('--mask', type=Path, help='Optional PNG mask (L/1 intensity or RGBA/LA alpha).')
    cmd.add_argument('--allow-alpha-change', action='store_true', help='Allow alpha changes inside the edit scope.')
    cmd.add_argument('--force', action='store_true', help='Explicitly allow replacing an existing output file.')
    add_output_options(cmd)


def _run_patch_draw(args):
    if args.inspect_ops:
        if (args.patch is not None or args.out is not None or args.allow_region
                or args.mask is not None or args.allow_alpha_change or args.force
                or args.portable_output is not None):
            raise PixelArtError('patch-draw: --inspect-ops accepts only --source, --offset and --limit')
        return inspect_draw_ops(
            args.source,
            offset=0 if args.offset is None else args.offset,
            limit=50 if args.limit is None else args.limit,
        )
    if args.offset is not None or args.limit is not None:
        raise PixelArtError('patch-draw: --offset and --limit require --inspect-ops')
    if args.patch is None or args.out is None:
        raise PixelArtError('patch-draw: editing requires --patch and --out')
    return patch_draw(
        args.source,
        args.patch,
        args.out,
        regions=args.allow_region,
        mask=args.mask,
        allow_alpha_change=args.allow_alpha_change,
        force=args.force,
        portable=resolve_portable_output(args.portable_output),
    )


def _add_verify_parser(subparsers):
    cmd = subparsers.add_parser(
        'verify',
        help='Run 3-tier verification (required / contract / advisory) on a PNG without modifying files.',
    )
    cmd.add_argument('--image', type=Path, required=True, help='Candidate PNG to inspect and verify.')
    cmd.add_argument('--baseline', type=Path, help='Optional baseline PNG for edit-boundary and alpha checks.')
    cmd.add_argument(
        '--allow-region',
        type=int,
        nargs=4,
        action='append',
        metavar=('X', 'Y', 'W', 'H'),
        help='Allowed edit rectangle [x y w h]; repeatable.',
    )
    cmd.add_argument('--mask', type=Path, help='Optional PNG mask (L/1 or RGBA/LA).')
    cmd.add_argument('--allow-alpha-change', action='store_true', help='Allow alpha differences vs baseline.')
    cmd.add_argument('--contract', type=Path, help='Optional declared structural contract JSON.')


def _add_rebuild_parser(subparsers):
    cmd = subparsers.add_parser(
        'rebuild',
        help='Verify ZIP CRC / SHA-256 manifest and independently rebuild PNGs into a fresh directory.',
    )
    cmd.add_argument('--input', type=Path, required=True, help='Delivery directory or .zip bundle.')
    cmd.add_argument('--out-dir', type=Path, required=True, help='Fresh output directory for rebuilt PNGs.')
    cmd.add_argument('--force', action='store_true', help='Explicitly allow replacing existing files.')
    add_output_options(cmd)


def _add_route_parser(subparsers):
    cmd = subparsers.add_parser(
        'route',
        help='Recommend source mode, CLI entrypoint, and fallback path for a natural-language request.',
    )
    cmd.add_argument('--prompt', required=True, help='Natural-language description of the pixel asset task.')


def _run_verify(args):
    require_pillow()
    img = _read_static_png(args.image).convert('RGBA')
    failures = []
    details = {}

    if args.baseline is not None:
        base = _read_static_png(args.baseline).convert('RGBA')
        mask_img = _read_static_png(args.mask) if args.mask is not None else None
        if args.allow_region or mask_img is not None:
            vrep = verify_edit(img, base, regions=args.allow_region, mask=mask_img)
            details['boundary'] = vrep
            if not vrep['valid']:
                failures.append(
                    f'edit boundary violated: {vrep["changed_outside"]} RGBA pixel(s) outside allowed scope'
                )
        alpha_stats = _alpha_diff_stats(base, img)
        details['alpha'] = alpha_stats
        if not args.allow_alpha_change and alpha_stats['alpha_changed_pixels'] > 0:
            failures.append(
                f'alpha lock violated: {alpha_stats["alpha_changed_pixels"]} pixel(s) changed alpha'
            )

    contract = read_json(args.contract) if args.contract is not None else None
    c_ok, c_fail, c_det = check_declared_contract(img, contract)
    failures.extend(c_fail)
    details['declared_contract'] = c_det

    report = {
        'version': 1,
        'image': str(args.image.resolve()),
        'tiers': {
            'required': {'pillow_compatible': True, 'rgba_8bit': True},
            'contract': {'passed': len(failures) == 0, 'failures': failures, 'details': details},
            'advisory': analyze_advisory(img),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Pixel-asset workflow toolkit: route, deliver, patch-draw, verify, and rebuild.'
    )
    sub = parser.add_subparsers(dest='command', required=True)
    _add_route_parser(sub)
    _add_deliver_parser(sub)
    _add_patch_draw_parser(sub)
    _add_verify_parser(sub)
    _add_rebuild_parser(sub)
    args = parser.parse_args(argv)

    try:
        if args.command == 'route':
            result = route_intent(args.prompt)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == 'patch-draw':
            result = _run_patch_draw(args)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == 'verify':
            _run_verify(args)
            return 0
        if args.command == 'deliver':
            result = deliver_asset(
                args.source,
                args.out_dir,
                mode=args.mode,
                metadata=args.metadata,
                baseline=args.baseline,
                allow_regions=args.allow_region,
                mask=args.mask,
                recolor_path=args.recolor,
                patch_path=args.patch,
                allow_alpha_change=args.allow_alpha_change,
                replace_cell_name=args.replace_cell,
                replacement_path=args.replacement,
                disabled_patches=args.disable_patch,
                contract_path=args.contract,
                scale=args.scale,
                background=args.background,
                pack_zip=args.pack_zip,
                extra_files=args.extra_file,
                force=args.force,
                portable=resolve_portable_output(args.portable_output),
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == 'rebuild':
            result = rebuild_and_verify(
                args.input,
                args.out_dir,
                force=args.force,
                portable=resolve_portable_output(args.portable_output),
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
    except ContractViolationError as exc:
        payload = {'error': str(exc), 'tier': 'contract'}
        if exc.report is not None:
            payload['details'] = exc.report
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    except (PixelArtError, OSError, ValueError) as exc:
        print(
            json.dumps({'error': str(exc), 'tier': 'required'}, ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
