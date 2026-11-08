"""Export exact PNG animation sources and optional, explicitly projected GIFs."""

import hashlib
import json
from pathlib import Path
import sys

from _common import entry, parser, PixelArtError
from _animation_project import (
    MAX_DELIVERY_BYTES,
    MAX_JSON_BYTES,
    budget,
    freeze_sources,
    plan,
    read_bounded,
)
from _animation_gif import encode_action
import PIL
from pixelart.cli import check_alias
from pixelart.compat import require_pillow
from pixelart.jsonio import parse_json
from pixelart.output import encoded, publish, resolve_portable_output


def make_files(project, base):
    """Prepare all bytes and verify GIFs before creating an output directory."""
    require_pillow()
    normalized, sequences = plan(project)
    paths, snapshots, decoded, records = freeze_sources(normalized, sequences, base)
    files = {}
    source_records = []
    for i, (frame, path, record) in enumerate(
        zip(normalized['frames'], paths, records)
    ):
        name = f'source-{i:04d}.png'
        files[name] = snapshots[path]
        frame['image'] = name
        source_records.append(
            dict(
                index=i,
                file=name,
                png_sha256=hashlib.sha256(snapshots[path]).hexdigest(),
                **record,
            )
        )
    files['animation.json'] = encoded(normalized)
    actions = []
    images = [decoded[path] for path in paths]
    for i, (action, indices) in enumerate(zip(normalized['actions'], sequences)):
        durations = [normalized['frames'][index]['duration_ms'] for index in indices]
        record = dict(
            name=action['name'],
            direction=action['direction'],
            source_indices=indices,
            durations_ms=durations,
            duration_ms=sum(durations),
        )
        if 'gif' in normalized:
            name = f'action-{i:04d}.gif'
            data, gif_report = encode_action(
                images, indices, durations, normalized['gif']
            )
            files[name] = data
            record['gif'] = dict(file=name, **gif_report)
        actions.append(record)
        budget(
            sum(map(len, files.values())), MAX_DELIVERY_BYTES, 'encoded delivery bytes'
        )
    report = dict(
        version=1,
        kind='png-animation-export',
        manifest=dict(
            file='animation.json',
            sha256=hashlib.sha256(files['animation.json']).hexdigest(),
            frame_count=len(source_records),
            action_count=len(actions),
        ),
        sources=source_records,
        actions=actions,
        runtime=dict(python=sys.version.split()[0], pillow=PIL.__version__),
        delivery=dict(
            files=[*files, 'report.json'],
            sha256={
                name: hashlib.sha256(data).hexdigest() for name, data in files.items()
            },
        ),
        note=(
            'Numbered PNGs retain original bytes, alpha and milliseconds. '
            'GIFs are explicit previews with palette/alpha projection and 10ms timing. '
            'Keep the entire directory and regenerate from animation.json into a new directory. '
            'Verify every listed file and hash; report.json has no self-hash. '
            'Publication is not a crash-safe group transaction.'
        ),
    )
    files['report.json'] = encoded(report)
    budget(sum(map(len, files.values())), MAX_DELIVERY_BYTES, 'encoded delivery bytes')
    return files, paths


def export(project_path, out_dir, *, force=False, portable=None):
    if force:
        raise PixelArtError('animation: --force is unsupported; choose a new directory')
    out_dir = Path(out_dir)
    # Lexical existence also detects a dangling link before resolve() follows it.
    try:
        out_dir.lstat()
    except FileNotFoundError:
        pass
    else:
        raise PixelArtError(
            'animation: output directory already exists; choose a new directory'
        )
    destination = out_dir.resolve()
    if destination.exists():
        raise PixelArtError(
            'animation: resolved output already exists; choose a new directory'
        )
    portable = resolve_portable_output(portable)
    project_path = Path(project_path)
    project = parse_json(
        read_bounded(project_path, MAX_JSON_BYTES, 'project JSON bytes').decode(
            'utf-8-sig'
        )
    )
    files, sources = make_files(project, project_path.resolve().parent)
    check_alias([project_path, *sources], [destination / name for name in files])
    destination.mkdir(parents=True, exist_ok=False)
    try:
        publish(
            {destination / name: data for name, data in files.items()},
            portable=portable,
        )
    except (OSError, ValueError) as error:
        try:
            destination.rmdir()
        except OSError:
            raise PixelArtError(
                f'animation: incomplete directory retained at {destination}; {error}'
            ) from error
        raise
    return files


def main():
    cli = parser(
        __doc__,
        force_help='Unsupported for animation export; use a new output directory.',
    )
    cli.add_argument(
        '--project',
        type=Path,
        required=True,
        help='png-animation v1 JSON with explicit PNG frames/actions.',
    )
    cli.epilog = 'Use a new output directory. GIF projection must be selected in the manifest. Keep the whole delivery to move and regenerate it.'
    args = cli.parse_args()
    files = export(
        args.project, args.out_dir, force=args.force, portable=args.portable_output
    )
    print(json.dumps(dict(out_dir=str(args.out_dir.resolve()), files=list(files))))


if __name__ == '__main__':
    entry(main)
