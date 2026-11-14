"""Verify the actual npm archive, real DSH services and relocatable PNG tools."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

from PIL import Image

try:
    from . import package_dsh, package_skill
except ImportError:
    import package_dsh
    import package_skill

ROOT = Path(__file__).resolve().parents[1]
HOST_PACKAGES = (
    'dsh-skill',
    'dsh-skill-filesystem',
    'dsh-llm',
    'dsh-scope',
    'dsh-fs',
    'dsh-home-paths',
)


def verify_host_versions(package, expected_version):
    for name in HOST_PACKAGES:
        manifest = package / 'node_modules' / '@deepseek-ai' / name / 'package.json'
        installed_version = json.loads(manifest.read_text(encoding='utf-8'))['version']
        if installed_version != expected_version:
            raise RuntimeError(
                f'Expected @deepseek-ai/{name} {expected_version}, '
                f'got {installed_version}'
            )


def verify(output, skill_version=None):
    output.mkdir(parents=True, exist_ok=False)
    records = []

    def run(arguments, cwd=output, env=None, display=True):
        result = subprocess.run(
            [str(arg) for arg in arguments],
            cwd=cwd,
            env=env or dict(os.environ, PYTHONIOENCODING='utf-8'),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        records.append(
            dict(
                argv=[str(arg) for arg in arguments],
                cwd=str(cwd),
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        if display:
            print(result.stdout, end='')
            print(result.stderr, end='', file=sys.stderr)
        result.check_returncode()
        return result.stdout

    try:
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        node = shutil.which('node')
        if not npm or not node:
            raise RuntimeError('DSH package checks require Node >=24.9.0 and npm')
        run([node, '--version'])
        run([npm, '--version'])
        stage = output / 'staged-package'
        package_dsh.build(stage)
        run([node, '--check', stage / 'index.js'])
        packed = json.loads(
            run([npm, 'pack', stage, '--ignore-scripts', '--json'], display=False)
        )[0]
        archive = output / packed['filename']
        inputs = package_skill._sources(ROOT)
        expected = {
            'package/' + name for name in (*package_dsh.TEMPLATE_FILES, 'LICENSE')
        } | {'package/generated/skill.json', 'package/skill-manifest.json'}
        expected |= {
            'package/skills/deterministic-pixel-art/' + name for name in inputs
        }
        unpacked = output / 'unpacked'
        with tarfile.open(archive) as bundle:
            members = bundle.getmembers()
            if any(not member.isfile() for member in members):
                raise RuntimeError('npm archive contains a nonregular member')
            names = [member.name for member in members]
            if len(names) != len(set(names)) or set(names) != expected:
                raise RuntimeError(
                    'npm archive file set differs from the package contract'
                )
            hashes = {}
            for member in members:
                data = bundle.extractfile(member).read()
                hashes[member.name] = hashlib.sha256(data).hexdigest()
                target = unpacked / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            for name, source in inputs.items():
                member = 'package/skills/deterministic-pixel-art/' + name
                if hashes[member] != package_skill._digest(source):
                    raise RuntimeError(f'Packed Skill differs from its source: {name}')
        (output / 'members.sha256.json').write_text(
            json.dumps(hashes, indent=2) + '\n', encoding='utf-8'
        )
        package = unpacked / 'package'
        # Install only real peer services into this disposable unpacked package.
        install = [npm, 'install', '--ignore-scripts', '--no-package-lock']
        if skill_version:
            install.extend(['--no-save'])
            install.extend(
                f'@deepseek-ai/{name}@{skill_version}' for name in HOST_PACKAGES
            )
        run(install, cwd=package)
        if skill_version:
            verify_host_versions(package, skill_version)
        moved = output / '搬移后的包 with spaces'
        package.rename(moved)
        unrelated = output / '无关 工作目录'
        unrelated.mkdir()
        environment = dict(os.environ, DSH_ADAPTER_PACKAGE=str(moved))
        run(
            [node, '--test', ROOT / 'integrations/dsh/test/provider.test.js'],
            cwd=unrelated,
            env=environment,
        )
        spec = unrelated / 'editable.json'
        spec.write_text(
            json.dumps(
                {
                    'version': 1,
                    'kind': 'grid',
                    'rows': ['...', '.X.', '...'],
                    'palette': {'.': None, 'X': '62D8E8'},
                }
            ),
            encoding='utf-8',
        )
        before = package_skill._digest(spec)
        png = unrelated / 'candidate.png'
        run(
            [
                sys.executable,
                '-B',
                moved / 'skills/deterministic-pixel-art/scripts/pixel_art.py',
                'render',
                '--spec',
                spec,
                '--out',
                png,
            ],
            cwd=unrelated,
        )
        with Image.open(png) as image:
            image.load()
            if image.format != 'PNG' or image.size != (3, 3):
                raise RuntimeError('Packaged renderer did not create the expected PNG')
            rgba = image.convert('RGBA')
            pixels = [rgba.getpixel((x, y)) for y in range(3) for x in range(3)]
            if pixels[4] != (98, 216, 232, 255) or any(
                pixel[3] != 0 for i, pixel in enumerate(pixels) if i != 4
            ):
                raise RuntimeError('Packaged render has unexpected decoded pixels')
        if package_skill._digest(spec) != before:
            raise RuntimeError('Packaged renderer modified its editable input')
        print(f'DSH archive and real-service checks passed ({len(inputs)} Skill files)')
    finally:
        (output / 'commands.json').write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='new evidence directory to retain')
    parser.add_argument(
        '--skill-version',
        choices=('0.2.2-rc.1', '0.2.2-rc.2', '0.2.2-rc.3'),
        help='install matching DSH Skill services for the adapter check',
    )
    args = parser.parse_args()
    if args.out:
        verify(args.out.absolute(), args.skill_version)
    else:
        with tempfile.TemporaryDirectory(prefix='dsh-check-') as directory:
            verify(Path(directory) / 'evidence', args.skill_version)


if __name__ == '__main__':
    main()
