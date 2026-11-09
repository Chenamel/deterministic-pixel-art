"""Build the optional DSH npm package from authoritative portable Skill inputs."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

import yaml

try:
    from . import package_skill
except ImportError:
    import package_skill

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILES = (
    'package.json',
    'index.js',
    'cordis.patch.yml',
    'README.md',
    'README.zh-CN.md',
    'NOTICE.md',
)


def skill_metadata(path):
    """Parse YAML frontmatter, including folded or multiline descriptions."""
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        raise ValueError(f'Missing YAML frontmatter: {path}')
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        raise ValueError(f'Unclosed YAML frontmatter: {path}')
    metadata = yaml.safe_load(''.join(lines[1:end]))
    if not isinstance(metadata, dict):
        raise ValueError(f'Skill metadata must be a mapping: {path}')
    for key in ('name', 'description'):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f'Skill metadata needs a nonempty {key}: {path}')
    if metadata['name'] != 'deterministic-pixel-art':
        raise ValueError(f'Unexpected Skill name: {metadata["name"]}')
    return {key: metadata[key] for key in ('name', 'description')}


def build(destination, root=ROOT):
    """Create a new package directory; existing paths are never replaced."""
    destination = Path(destination).absolute()
    for path in (destination, *destination.parents):
        if path.is_symlink():
            raise ValueError(f'Package output must not use symlinks: {path}')
    if destination.exists():
        raise FileExistsError(f'Package output already exists: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    inputs = package_skill._sources(root)
    manifest = {name: package_skill._digest(source) for name, source in inputs.items()}
    metadata = skill_metadata(inputs['SKILL.md'])
    with tempfile.TemporaryDirectory(
        prefix='dsh-package-', dir=destination.parent
    ) as temp:
        stage = Path(temp)
        template = root / 'integrations/dsh'
        for name in TEMPLATE_FILES:
            source = template / name
            if source.is_symlink() or not source.is_file():
                raise ValueError(f'Expected a regular DSH template file: {source}')
            shutil.copyfile(source, stage / name)
        shutil.copyfile(root / 'LICENSE', stage / 'LICENSE')
        skill = stage / 'skills/deterministic-pixel-art'
        for name, source in inputs.items():
            target = skill / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if package_skill._digest(target) != manifest[name]:
                raise RuntimeError(f'Skill input changed while copying: {source}')
        (stage / 'generated').mkdir()
        (stage / 'generated/skill.json').write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
        (stage / 'skill-manifest.json').write_text(
            json.dumps(manifest, indent=2) + '\n', encoding='utf-8'
        )
        if package_skill._sources(root) != inputs or any(
            package_skill._digest(source) != manifest[name]
            for name, source in inputs.items()
        ):
            raise RuntimeError('Skill inputs changed during the build; retry')
        # copytree claims a new directory before copying and refuses existing outputs.
        shutil.copytree(stage, destination)
    return {'package': str(destination), 'skill_files': len(manifest)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='new package directory')
    args = parser.parse_args()
    print(json.dumps(build(args.out)))


if __name__ == '__main__':
    main()
