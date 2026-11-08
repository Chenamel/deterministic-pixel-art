"""Check the explicitly covered Python sources without changing files."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    for arguments in (
        ['check'],
        ['format', '--check'],
    ):
        result = subprocess.run(
            [
                sys.executable,
                '-B',
                '-m',
                'ruff',
                *arguments,
                '--config',
                str(ROOT / '.ruff.toml'),
                '--no-cache',
                str(ROOT),
            ],
            cwd=ROOT,
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
