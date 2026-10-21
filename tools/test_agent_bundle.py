"""Execute shipped evaluation bundles in isolation; never simulate agent evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def unpack(archive, target):
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            if not (target / name).resolve().is_relative_to(target.resolve()):
                raise RuntimeError('archive path escapes target')
        bundle.extractall(target)
    checks = json.loads((target / 'checksums.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
    if actual != set(checks) | {'checksums.json'}:
        raise RuntimeError('unexpected or missing bundle files')
    for name, expected in checks.items():
        if hashlib.sha256((target / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'checksum mismatch: {name}')


def main():
    source = ROOT / 'evaluation/agent-eval'
    key = json.loads((source / 'version-key.json').read_text(encoding='utf-8'))
    cases = []
    env = {k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
    env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    with tempfile.TemporaryDirectory(prefix='外部测评包 中文 space ') as directory:
        folder = Path(directory)
        agent, judge = folder / 'agent', folder / 'evaluator'
        for name, target in [('agent-evaluation',agent),('agent-evaluator',judge)]:
            unpack(source / f'{name}-v1.2.0-rc.1.zip', target)
            cases.append(name + '-checksums')
        names = {p.relative_to(agent).as_posix() for p in agent.rglob('*') if p.is_file()}
        if any('expected' in name or 'version-key' in name or 'manifest.json' == name for name in names):
            raise RuntimeError('grading answers leaked into agent bundle')
        if len(list((agent / 'tasks').glob('*/request.md'))) != 8:
            raise RuntimeError('eight task requests required')
        cases.append('agent-fixture-boundary')
        for path in (ROOT / 'src').rglob('*.py'):
            if path.read_bytes() != (judge / 'runtime' / path.relative_to(ROOT / 'src')).read_bytes():
                raise RuntimeError('evaluator runtime differs from source')
        cases.append('evaluator-runtime-exact')

        def run(label, *arguments, expected=0):
            result = subprocess.run([sys.executable, '-B', *map(str, arguments)],
                cwd=folder, env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
            if result.returncode != expected:
                raise RuntimeError(f'{label}: {result.stdout}\n{result.stderr}')
            cases.append(label)
            return result

        for label in ('A','B'):
            runtime = folder / ('runtime-' + label)
            with zipfile.ZipFile(agent / 'packages' / f'{label}.zip') as bundle:
                bundle.extractall(runtime)
            skill = runtime / 'deterministic-pixel-art'
            cli = skill / 'scripts/pixel_art.py'
            out = folder / ('smoke-' + label)
            runner = agent / 'runner.py'
            run(label+'-start', runner, 'start', '--out', out, '--task', 'packaging-smoke',
                '--package', label, '--package-zip', agent / 'packages' / f'{label}.zip',
                '--environment', 'PACKAGING-SMOKE', '--mode', 'text_only', '--model', 'NO-AGENT-EXECUTED')
            # The temporary log tests the recorder, not an external task or model.
            run(label+'-render', runner, 'run', '--out', out, '--', sys.executable, '-B', cli,
                'render', '--spec', skill / 'assets/gem-16.json', '--out', out / 'final.png',
                '--metadata', out / 'layout.json')
            run(label+'-validate', runner, 'run', '--out', out, '--', sys.executable, '-B', cli,
                'validate', '--image', out / 'final.png')
            if label == key['candidate_label']:
                run(label+'-inspect', runner, 'run', '--out', out, '--', sys.executable, '-B', cli,
                    'inspect', '--image', out / 'final.png', '--metadata', out / 'layout.json', '--grid')
                run(label+'-import', runner, 'run', '--out', out, '--', sys.executable, '-B', cli,
                    'import', '--image', out / 'final.png', '--out', out / 'editable.json')
            run(label+'-finish', runner, 'finish', '--out', out, '--candidates', '1', '--revisions', '0',
                '--failure-stage', 'repair')
        pending = folder / 'pending.json'
        run('empty-results-reject-stable', judge / 'evaluate_agent_results.py',
            '--manifest', judge / 'manifest.json', '--runs', folder / 'no-external-runs',
            '--out', pending, expected=1)
        result = json.loads(pending.read_text(encoding='utf-8'))
        if result['stable_release_gate_passed'] or result['external_runs'] != 0:
            raise RuntimeError('missing external evidence must not pass')
        (ROOT / 'docs/measurements/feedback-external-gate.json').write_bytes(pending.read_bytes())
    record = dict(cases=cases, passed=len(cases), external_agent_runs=0,
        note='Isolated package and recorder smoke tests only; temporary smoke logs were deleted.')
    (ROOT / 'evaluation/agent-bundle-checks.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
