"""Staged multi-output publication with cooperating-writer locks and rollback.

Each file is published atomically. This is not a crash-safe group transaction.
"""
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile

from .core import PixelArtError


def encoded(artifact):
    if isinstance(artifact, bytes):
        return artifact
    if isinstance(artifact, dict):
        return json.dumps(artifact, ensure_ascii=False, indent=2).encode('utf-8')
    buffer = BytesIO()
    artifact.save(buffer, format='PNG')
    return buffer.getvalue()


def publish(artifacts, *, force=False):
    """Publish path->artifact, rejecting existing targets unless force is set.

    Encoding and predictable path errors precede publication. No-force uses an
    exclusive hard link, so another writer cannot be overwritten by a late race.
    Filesystems without hard-link support fail explicitly rather than clobber.
    """
    prepared = [(Path(p).resolve(), encoded(value)) for p, value in artifacts.items()]
    if len({p for p, _ in prepared}) != len(prepared):
        raise PixelArtError('output paths must be distinct')
    for path, _ in prepared:
        if path.exists() and (not path.is_file() or not force):
            raise PixelArtError(f'output already exists or is not a file: {path}; use --force only for files')
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise PixelArtError(f'output parent is not a directory: {parent}')
    locks, staged, backups, committed = [], {}, {}, []
    rollback_errors = []
    try:
        for path, _ in sorted(prepared):
            path.parent.mkdir(parents=True, exist_ok=True)
            lock = path.with_name('.' + path.name + '.pixelart.lock')
            try:
                fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError as exc:
                raise PixelArtError(f'output reserved by another writer: {path}') from exc
            os.close(fd)
            locks.append(lock)
        # Recheck after acquiring every reservation, before staging or replacing.
        for path, data in prepared:
            if path.exists() and (not force or not path.is_file()):
                raise PixelArtError(f'output already exists or is not a file: {path}')
            with tempfile.NamedTemporaryFile(prefix='.' + path.name + '.', suffix='.tmp',
                                             dir=path.parent, delete=False) as handle:
                staged[path] = Path(handle.name)
                handle.write(data)
            if path.exists():
                with tempfile.NamedTemporaryFile(prefix='.' + path.name + '.', suffix='.bak',
                                                 dir=path.parent, delete=False) as handle:
                    backups[path] = Path(handle.name)
                    handle.write(path.read_bytes())
        for path, _ in prepared:
            if force:
                os.replace(staged[path], path)
            else:
                os.link(staged[path], path)
            committed.append(path)
    except (OSError, PixelArtError) as exc:
        for path in reversed(committed):
            try:
                expected = next(data for p, data in prepared if p == path)
                if not path.is_file() or path.read_bytes() != expected:
                    raise OSError('target changed after publication; left untouched')
                if path in backups:
                    os.replace(backups[path], path)
                else:
                    path.unlink()
            except OSError as rollback:
                rollback_errors.append({'path': str(path), 'error': str(rollback)})
        detail = {'cause': str(exc), 'committed_before_error': list(map(str, committed)),
                  'rollback_errors': rollback_errors,
                  'remaining_outputs': [str(p) for p in committed if p.exists()]}
        raise PixelArtError('output publication failed: ' + json.dumps(detail, ensure_ascii=False)) from exc
    finally:
        for path in [*staged.values(), *backups.values(), *locks]:
            if path.exists():
                path.unlink()
