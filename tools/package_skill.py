"""Package only the tested portable runtime, examples and skill references."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked(path, root):
    """Keep generated directories, moves and temporary cleanup inside this root."""
    if not path.resolve().is_relative_to(root):
        raise RuntimeError(f'Package path is outside the workspace: {path}')
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise RuntimeError(f'Package paths must not use symlinks: {parent}')
    return path


def _private(relative):
    return (any(part.startswith('.') or part == '__pycache__' or part.casefold() == 'agents.md'
                for part in relative.parts) or relative.suffix.lower() in ('.pyc', '.pyo'))


def _sources(root):
    """Map every package file to one authoritative input, never generated output."""
    result = {}

    def add(relative, source):
        _checked(source, root)
        if relative in result:
            raise RuntimeError(f'Package inputs collide at {relative}')
        result[relative] = source

    for folder, pattern, prefix in (
        ('skill-content', '**/*', ''),
        ('src/pixelart', '*.py', 'scripts/pixelart/'),
        ('recipes', '*.py', 'scripts/recipes/'),
        ('examples', '**/*', 'assets/'),
        ('docs/quality', '*.png', 'assets/studies/')):
        base = _checked(root / folder, root)
        for source in sorted(base.glob(pattern)):
            relative = source.relative_to(base)
            if _private(relative):
                continue
            if source.is_symlink():
                raise RuntimeError(f'Package inputs must be regular files: {source}')
            if not source.is_file() or (folder == 'examples' and source.suffix not in ('.json', '.png')):
                continue
            add(prefix + relative.as_posix(), source)
    for relative, name in (
        ('requirements.txt', 'requirements.txt'), ('LICENSE', 'LICENSE'),
        ('scripts/pixel_art.py', 'src/pixel_art.py')):
        add(relative, root / name)
    required = {'SKILL.md', 'LICENSE', 'requirements.txt', 'agents/openai.yaml',
                'scripts/pixel_art.py', 'scripts/pixelart/__init__.py'}
    if not required <= result.keys():
        raise RuntimeError(f'Missing required package inputs: {sorted(required - result.keys())}')
    return dict(sorted(result.items()))


def _snapshot(path):
    if path.is_symlink():
        raise RuntimeError(f'Package output must not be a symlink: {path}')
    if not path.exists():
        return None
    if path.is_file():
        return ('file', _digest(path))
    if not path.is_dir():
        raise RuntimeError(f'Package output must be a regular file or directory: {path}')
    entries = {}
    for child in sorted(path.rglob('*')):
        if child.is_symlink() or not (child.is_file() or child.is_dir()):
            raise RuntimeError(f'Generated Skill contains a nonregular entry: {child}')
        name = child.relative_to(path).as_posix()
        entries[name + '/' if child.is_dir() else name] = None if child.is_dir() else _digest(child)
    return ('directory', entries)


def _publish(root, outputs):
    """Preserve replaced outputs; recover ordinary failures without touching sources."""
    originals = {}
    desired = {}
    changes = []
    for target, staged in outputs:
        _checked(target, root)
        _checked(staged, root)
        originals[target], desired[target] = _snapshot(target), _snapshot(staged)
        if originals[target] is not None and originals[target][0] != desired[target][0]:
            raise RuntimeError(f'Package output has the wrong type: {target}')
        if originals[target] != desired[target]:
            changes.append((target, staged))
    previous = {}
    if any(originals[target] is not None for target, _ in changes):
        backup_root = _checked(Path(tempfile.mkdtemp(prefix='package-backup-', dir=root / 'evaluation')), root)
        for index, (target, _) in enumerate(changes):
            if originals[target] is not None:
                backup = backup_root / str(index) / target.name
                backup.parent.mkdir()
                previous[target] = _checked(backup, root)
        (backup_root / 'recovery.json').write_text(json.dumps({
            'note': 'Planned previous-output locations; inspect which paths exist after interruption.',
            'previous_outputs': [{'path': str(path), 'backup': str(backup)}
                                 for path, backup in previous.items()]}, indent=2), encoding='utf-8')
    moved, committed = {}, []
    try:
        for target, _ in changes:
            target.parent.mkdir(parents=True, exist_ok=True)
            if _snapshot(target) != originals[target]:
                raise RuntimeError(f'Package output changed during the build: {target}')
            if target in previous:
                os.replace(target, previous[target])
                moved[target] = previous[target]
        for target, staged in changes:
            if target.exists() or target.is_symlink():
                raise RuntimeError(f'Package output appeared during publication: {target}')
            os.replace(staged, target)
            committed.append((target, staged))
    except (OSError, RuntimeError) as error:
        rollback_errors = []
        for target, staged in reversed(committed):
            try:
                if _snapshot(target) != desired[target]:
                    raise RuntimeError('Published output changed; left untouched')
                os.replace(target, staged)
            except (OSError, RuntimeError) as rollback:
                rollback_errors.append({'path': str(target), 'error': str(rollback)})
        remaining = dict(moved)
        for target, backup in reversed(list(moved.items())):
            try:
                if target.exists() or target.is_symlink():
                    raise RuntimeError('Output exists; previous output left in backup')
                os.replace(backup, target)
                del remaining[target]
            except (OSError, RuntimeError) as rollback:
                rollback_errors.append({'path': str(target), 'error': str(rollback)})
        detail = dict(cause=str(error), rollback_errors=rollback_errors,
                      recovery_backups=[{'path': str(path), 'backup': str(backup)}
                                        for path, backup in remaining.items()])
        raise RuntimeError('Package publication failed: ' + json.dumps(detail)) from error
    return [{'path': str(path), 'backup': str(backup)} for path, backup in moved.items()]


def _quality_gate(root):
    metrics = json.loads((root / 'evaluation/metrics.json').read_text(encoding='utf-8'))
    if not metrics['quality_gate_passed'] or not metrics['fixtures_unchanged']:
        raise RuntimeError('Packaging requires a passing quality gate')
    current_runtime = {p.relative_to(root / 'src').as_posix(): _digest(p)
                       for p in sorted((root / 'src').rglob('*.py'))}
    if metrics.get('runtime_sha256') != current_runtime:
        raise RuntimeError('Runtime changed since evaluation; rerun evaluate.py before packaging')
    quality = json.loads((root / 'evaluation/quality-results.json').read_text(encoding='utf-8'))
    if not quality.get('agent_review_passed') or quality.get('stable_outputs_unchanged') != 43:
        raise RuntimeError('Packaging requires current compatibility checks and recorded author self-review')
    for item in quality['cases']:
        for key, folder in [('spec_sha256', 'examples/quality'), ('context_sha256', 'examples/quality/contexts')]:
            if _digest(root / folder / (item['task'] + '.json')) != item[key]:
                raise RuntimeError('Quality examples changed since review; inspect and evaluate again')


def main():
    root = ROOT.resolve()
    evaluation = _checked(root / 'evaluation', root)
    lock = evaluation / '.package_skill.lock'
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise RuntimeError(f'Another packager holds {lock}; check its owner before removing a stale lock') from error
    os.close(descriptor)
    try:
        _quality_gate(root)
        inputs = _sources(root)
        with tempfile.TemporaryDirectory(prefix='package-stage-', dir=evaluation) as directory:
            stage = _checked(Path(directory), root)
            skill = stage / 'skill'
            for sub in ('scripts/pixelart', 'references', 'assets', 'agents'):
                (skill / sub).mkdir(parents=True, exist_ok=True)
            manifest = {}
            for relative, source in inputs.items():
                digest = _digest(source)
                target = skill / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if _digest(target) != digest:
                    raise RuntimeError(f'Package input changed while copying: {source}')
                manifest[relative] = digest
            actual = {name: value for name, value in _snapshot(skill)[1].items() if not name.endswith('/')}
            if actual != manifest:
                raise RuntimeError('Staged Skill differs from its authoritative input manifest')
            manifest_path = stage / 'package-manifest.json'
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            archive = stage / 'package.zip'
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
                for relative in manifest:
                    entry = zipfile.ZipInfo(f'deterministic-pixel-art/{relative}', (1980, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    bundle.writestr(entry, (skill / relative).read_bytes())
            with zipfile.ZipFile(archive) as bundle:
                expected = ['deterministic-pixel-art/' + name for name in manifest]
                if bundle.namelist() != expected or bundle.testzip() is not None:
                    raise RuntimeError('Staged ZIP file set or CRC differs from its manifest')
                if any(hashlib.sha256(bundle.read('deterministic-pixel-art/' + name)).hexdigest() != digest
                       for name, digest in manifest.items()):
                    raise RuntimeError('Staged ZIP bytes differ from authoritative inputs')
            if _sources(root) != inputs or any(_digest(source) != manifest[name] for name, source in inputs.items()):
                raise RuntimeError('Package inputs changed during the build; retry with one source writer')
            _quality_gate(root)
            destination = root / 'skill/deterministic-pixel-art'
            target_archive = root / 'deterministic-pixel-art.zip'
            previous = _publish(root, [(destination, skill),
                (evaluation / 'package-manifest.json', manifest_path), (target_archive, archive)])
        print(json.dumps({'skill': str(destination), 'files': len(manifest),
                          'zip_bytes': target_archive.stat().st_size, 'previous_outputs': previous}))
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
