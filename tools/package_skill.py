"""Package only the tested portable runtime, examples and skill references."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    metrics = json.loads((ROOT / 'evaluation/metrics.json').read_text(encoding='utf-8'))
    if not metrics['quality_gate_passed'] or not metrics['fixtures_unchanged']:
        raise RuntimeError('Packaging requires a passing quality gate')
    current_runtime = {p.relative_to(ROOT / 'src').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted((ROOT / 'src').rglob('*.py'))}
    if metrics.get('runtime_sha256') != current_runtime:
        raise RuntimeError('Runtime changed since evaluation; rerun evaluate.py before packaging')
    quality = json.loads((ROOT / 'evaluation/quality-results.json').read_text(encoding='utf-8'))
    if not quality.get('agent_review_passed') or quality.get('stable_outputs_unchanged') != 43:
        raise RuntimeError('Packaging requires current compatibility checks and recorded author self-review')
    for item in quality['cases']:
        for key, folder in [('spec_sha256', 'examples/quality'), ('context_sha256', 'examples/quality/contexts')]:
            if hashlib.sha256((ROOT / folder / (item['task'] + '.json')).read_bytes()).hexdigest() != item[key]:
                raise RuntimeError('Quality examples changed since review; inspect and evaluate again')
    skill = ROOT / 'skill/deterministic-pixel-art'
    for sub in ('scripts/pixelart', 'references', 'assets', 'agents'):
        (skill / sub).mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / 'skill-content').rglob('*')):
        if source.is_file():
            target = skill / source.relative_to(ROOT / 'skill-content')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    shutil.copyfile(ROOT / 'requirements.txt', skill / 'requirements.txt')
    shutil.copyfile(ROOT / 'LICENSE', skill / 'LICENSE')
    shutil.copyfile(ROOT / 'src/pixel_art.py', skill / 'scripts/pixel_art.py')
    for path in sorted((ROOT / 'src/pixelart').glob('*.py')):
        shutil.copyfile(path, skill / 'scripts/pixelart' / path.name)
    for path in sorted((ROOT / 'examples').rglob('*')):
        if path.suffix not in ('.json','.png') or not path.is_file():
            continue
        target = skill / 'assets' / path.relative_to(ROOT / 'examples')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for path in sorted((ROOT / 'docs/quality').glob('*.png')):
        target = skill / 'assets/studies' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    manifest = {p.relative_to(skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(skill.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    (ROOT / 'evaluation/package-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = ROOT / 'deterministic-pixel-art.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative in manifest:
            # Fixed timestamps and permissions make identical sources reproducible.
            entry = zipfile.ZipInfo(f'deterministic-pixel-art/{relative}', (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, (skill / relative).read_bytes())
    print(json.dumps({'skill': str(skill), 'files': len(manifest), 'zip_bytes': archive.stat().st_size}))


if __name__ == '__main__':
    main()
