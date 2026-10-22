"""Run the portable source-to-skill checks from any working directory."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(name, *arguments):
    subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / name), *arguments],
                   cwd=ROOT, check=True)


if __name__ == '__main__':
    run('build_workflow_examples.py')
    run('migrate_assets.py')
    run('evaluate.py')
    run('evaluate_quality.py')
    run('evaluate_feedback.py')
    run('package_skill.py')
    archive = ROOT / 'deterministic-pixel-art.zip'
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    run('package_skill.py')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != before:
        raise RuntimeError('Packaging identical sources produced different archives')
    run('test_skill.py', '--python', sys.executable)
    print('Portable checks and reproducible package passed')
