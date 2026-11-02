"""Build a separate SkillHub ZIP from the complete generated Skill."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skill/deterministic-pixel-art'
HOMEPAGE = 'https://github.com/Chenamel/deterministic-pixel-art'
SEMVER = re.compile(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z')


def current_commit():
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD'], cwd=ROOT).returncode:
        raise ValueError('Commit tracked changes before binding a package to HEAD.')
    prefix = SKILL.relative_to(ROOT).as_posix() + '/'
    snapshot = subprocess.check_output(['git', 'archive', '--format=zip', 'HEAD', '--', prefix], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(snapshot)) as archive:
        committed = {name.removeprefix(prefix): archive.read(name) for name in archive.namelist()
                     if not name.endswith('/')}
    actual = {path.relative_to(SKILL).as_posix(): path.read_bytes() for path in SKILL.rglob('*')
              if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.pyo')}
    if actual != committed:
        raise ValueError('Generated Skill files must match HEAD, including untracked or ignored files.')
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def package_bytes(skill, source_commit):
    if not re.fullmatch(r'[0-9a-f]{40}', source_commit):
        raise ValueError('Source commit must be a full lowercase Git SHA-1.')
    required = ('SKILL.md', 'LICENSE', 'requirements.txt', 'scripts/pixel_art.py',
                'scripts/pixelart/__init__.py')
    if not all((skill / name).is_file() for name in required):
        raise ValueError('Use the complete generated Skill, not skill-content/.')
    paths = sorted(skill.rglob('*'))
    if any(path.is_symlink() for path in paths):
        raise ValueError('Portable Skill packages must contain regular files, not symlinks.')
    files = {path.relative_to(skill).as_posix(): path.read_bytes() for path in paths
             if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.pyo')}
    text = files['SKILL.md'].decode('utf-8')
    front = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not front or not all(re.search(r'^' + key + r':\s*\S', front[1], re.M)
                            for key in ('name', 'description')):
        raise ValueError('The generic Skill needs name and description frontmatter.')
    if re.search(r'^(slug|version|displayName|summary|tags|homepage):', front[1], re.M) or 'DISTRIBUTION.json' in files:
        raise ValueError('The source is already adapted; start from the generic Skill.')
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", files['scripts/pixelart/__init__.py'].decode('utf-8'), re.M)
    if not match or not SEMVER.fullmatch(match[1]):
        raise ValueError('The packaged runtime must declare a SemVer version.')
    version = match[1]
    metadata = dict(slug='deterministic-pixel-art', displayName='Deterministic Pixel Art',
                    version=version, summary='用可编辑网格和整数绘图命令制作、检查与精确修改像素 PNG。',
                    homepage=HOMEPAGE)
    fields = [key + ': ' + json.dumps(value, ensure_ascii=False) for key, value in metadata.items()]
    fields.append('tags: [pixel-art, image-editing, python, deterministic]')
    start = text.index('\n') + 1
    files['SKILL.md'] = (text[:start] + '\n'.join(fields) + '\n' + text[start:]).encode('utf-8')
    files['DISTRIBUTION.json'] = (json.dumps(dict(format='skillhub', version=version,
        runtime_version=version, repository=HOMEPAGE, source_commit=source_commit), indent=2) + '\n').encode('utf-8')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    return buffer.getvalue(), manifest, version


def package(skill, out, source_commit):
    if out.exists():
        raise FileExistsError('Use a new output directory; previous packages are preserved.')
    data, manifest, version = package_bytes(skill, source_commit)
    name = f'deterministic-pixel-art-skillhub-v{version}.zip'
    manifest_data = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    digest = hashlib.sha256(data).hexdigest()
    out.mkdir(parents=True, exist_ok=False)
    (out / name).write_bytes(data)
    (out / 'skillhub-manifest.json').write_bytes(manifest_data)
    (out / 'SHA256SUMS.txt').write_text(
        digest + '  ' + name + '\n' + hashlib.sha256(manifest_data).hexdigest() + '  skillhub-manifest.json\n',
        encoding='ascii', newline='\n')
    return dict(archive=str(out / name), version=version, source_commit=source_commit,
                files=len(manifest), bytes=len(data), sha256=digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--source-commit', help='Full source SHA; otherwise use clean repository HEAD.')
    args = parser.parse_args()
    try:
        result = package(SKILL, args.out, args.source_commit or current_commit())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f'SkillHub packaging failed: {error}\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
