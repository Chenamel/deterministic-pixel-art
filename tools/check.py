"""Run the portable source-to-skill checks from any working directory."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = {
    '.github',
    'assets',
    'baselines',
    'benchmarks',
    'demos',
    'docs',
    'examples',
    'integrations',
    'quality',
    'recipes',
    'skill',
    'skill-content',
    'specs',
    'src',
    'tests',
    'tools',
}
SOURCE_FILES = {
    '.gitattributes',
    '.gitignore',
    '.ruff.toml',
    'CHANGELOG.md',
    'CONTRIBUTING.md',
    'INSTALL.md',
    'LICENSE',
    'README.md',
    'README.zh-CN.md',
    'WORK_STATE.md',
    'requirements-dev.txt',
    'requirements.txt',
}
PRIVATE_NAMES = {'agents.md', '__pycache__', 'node_modules'}
GIT_ENV = {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'}


def source_path(relative):
    first, *children = relative.parts
    if not children:
        return first in SOURCE_DIRECTORIES or first in SOURCE_FILES
    return (
        first in SOURCE_DIRECTORIES
        and not any(
            name.startswith('.') or name.casefold() in PRIVATE_NAMES
            for name in children
        )
        and relative.suffix not in ('.pyc', '.pyo')
    )


def export_paths():
    for name in sorted(SOURCE_FILES):
        yield Path(name)
    for directory in sorted(SOURCE_DIRECTORIES):
        for current, directories, files in os.walk(ROOT / directory):
            relative = Path(current).relative_to(ROOT)
            directories[:] = [
                name for name in directories if source_path(relative / name)
            ]
            yield from (relative / name for name in files)


def copy_source(destination, env):
    if (ROOT / '.git').exists():
        listed = subprocess.check_output(
            [
                'git',
                '-C',
                str(ROOT),
                'ls-files',
                '--cached',
                '--others',
                '--exclude-standard',
                '-z',
            ],
            env=env,
        )
        paths = (Path(os.fsdecode(name)) for name in listed.split(b'\0') if name)
    else:
        paths = export_paths()

    for relative in paths:
        if not source_path(relative):
            continue
        source = ROOT / relative
        if not source.is_file():
            continue
        if source.resolve() != source:
            raise ValueError(
                f'Check source must be a regular file inside the project: {relative}'
            )
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def run(root, env, log, name, *arguments):
    if log is not None:
        print(f'Running {name}', file=log, flush=True)
    subprocess.run(
        [sys.executable, '-B', str(root / 'tools' / name), *arguments],
        cwd=root,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT if log is not None else None,
        check=True,
    )


def check(root, env=None, log=None):
    for name, arguments in (
        ('check_format.py', ()),
        ('build_workflow_examples.py', ()),
        ('build_consumer_demo.py', ('--force',)),
        ('build_chunk_scene.py', ('--force',)),
        ('migrate_assets.py', ()),
        ('evaluate.py', ()),
        ('evaluate_quality.py', ()),
        ('evaluate_feedback.py', ()),
        ('package_skill.py', ()),
    ):
        run(root, env, log, name, *arguments)
    archive = root / 'deterministic-pixel-art.zip'
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    run(root, env, log, 'package_skill.py')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != before:
        raise RuntimeError('Packaging identical sources produced different archives')
    run(root, env, log, 'test_skill.py', '--python', sys.executable)
    print('Portable checks and reproducible package passed', file=log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--isolated',
        metavar='DIRECTORY',
        type=Path,
        help='Run in a new directory outside the project and keep the check artifacts there.',
    )
    arguments = parser.parse_args()
    if arguments.isolated is None:
        check(ROOT)
        return 0

    destination = arguments.isolated.resolve()
    if destination.is_relative_to(ROOT):
        parser.error('--isolated requires a new directory outside the project')
    try:
        destination.mkdir(parents=True)
    except OSError as error:
        parser.error(str(error))
    log_path = destination / 'check.log'
    root = destination / 'project'
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_ENV and not key.startswith('GIT_CONFIG_')
    }
    env.pop('PYTHONPATH', None)
    env['PYTHONIOENCODING'] = 'utf-8'
    with log_path.open('w', encoding='utf-8') as log:
        message = f'Check log: {log_path}'
        print(message, file=log, flush=True)
        sys.stdout.reconfigure(errors='backslashreplace')
        print(message, flush=True)
        try:
            copy_source(root, env)
            check(root, env, log)
        except subprocess.CalledProcessError as error:
            print(
                f'Check command failed with exit {error.returncode}: {error.cmd}',
                file=log,
            )
            return error.returncode
        except (OSError, ValueError, RuntimeError) as error:
            print(str(error), file=log)
            return 1
    print('Portable checks and reproducible package passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
