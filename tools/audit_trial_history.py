"""Read recorded snapshots to locate replaced/deleted artifacts; never alter a trial."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def checked_snapshot(value):
    if not isinstance(value, dict) or len(value) > 512:
        raise ValueError('Expected a snapshot with at most 512 files')
    for name, digest in value.items():
        if not isinstance(name, str):
            raise ValueError('Snapshot paths must be relative POSIX paths')
        path = PurePosixPath(name)
        if not name or name != path.as_posix() or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Snapshot paths must be relative POSIX paths')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Snapshot digests must be SHA-256 hex strings')
    return value


def analyze_history(records, final_snapshot=None):
    """Report mutations of existing paths; additions are not revisions or failures."""
    if not isinstance(records, list) or len(records) > 5000:
        raise ValueError('Expected at most 5000 recorded commands')
    events = []

    def compare(before, after, phase, record):
        for name, previous in sorted(before.items()):
            current = after.get(name)
            if current != previous:
                events.append(dict(phase=phase, record=record, path=name,
                                   kind='removed' if current is None else 'replaced',
                                   before=previous, after=current))

    previous = None
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise ValueError('Expected a command record object')
        before = checked_snapshot(record.get('outputs_before'))
        after = checked_snapshot(record.get('outputs_after'))
        if previous is not None:
            compare(previous, before, 'between_commands', index)
        compare(before, after, 'within_command', index)
        previous = after
    if final_snapshot is not None:
        final_snapshot = checked_snapshot(final_snapshot)
        if previous is not None:
            compare(previous, final_snapshot, 'after_last_command', len(records))
    return dict(version=1, commands=len(records), mutations=len(events),
                removed_paths=sorted({e['path'] for e in events if e['kind'] == 'removed'}),
                replaced_paths=sorted({e['path'] for e in events if e['kind'] == 'replaced'}),
                by_phase=dict(Counter(e['phase'] for e in events)), events=events,
                scope='Observed path mutations only. Authorized rebuilds may be valid; this cannot recover old bytes, prove preserved versions, or judge visual meaning.')


def audit(run_dir):
    run_dir = Path(run_dir).resolve()
    log = run_dir / 'commands.jsonl'
    if log.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Command log exceeds 8 MiB')
    records = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line.strip()]
    final = {}
    total = 0
    for path in sorted(run_dir.rglob('*')):
        if path.is_symlink():
            raise ValueError('Trial must contain regular files, no symlinks')
        if not path.is_file() or path.name in ('commands.jsonl', 'session.json', 'checks.json'):
            continue
        total += path.stat().st_size
        if len(final) >= 512 or total > 32 * 1024 * 1024:
            raise ValueError('Trial exceeds 512 artifact files or 32 MiB')
        final[path.relative_to(run_dir).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return analyze_history(records, final)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.out is not None and args.out.resolve().is_relative_to(args.run_dir.resolve()):
        raise ValueError('Write audit reports outside the preserved trial directory')
    result = audit(args.run_dir)
    data = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.out is not None:
        with args.out.open('x', encoding='utf-8') as stream:
            stream.write(data)
    print(data, end='')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False))
        raise SystemExit(2)
