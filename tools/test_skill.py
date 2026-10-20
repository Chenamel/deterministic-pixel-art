"""Test the actual zip in a separate, installed runtime and unrelated Unicode cwd.

This is artifact-level forward execution, not an independent LLM/agent evaluation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main(python, validator):
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
    env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    results = []
    with tempfile.TemporaryDirectory(prefix='独立 skill space ') as directory:
        folder = Path(directory)
        with zipfile.ZipFile(ROOT / 'deterministic-pixel-art.zip') as bundle:
            for name in bundle.namelist():
                candidate = (folder / name).resolve()
                if not candidate.is_relative_to(folder.resolve()):
                    raise RuntimeError('Archive path escapes extraction directory')
            bundle.extractall(folder)
        skill = folder / 'deterministic-pixel-art'
        cli = skill / 'scripts/pixel_art.py'
        manifest = json.loads((ROOT / 'evaluation/package-manifest.json').read_text(encoding='utf-8'))
        if not all(hashlib.sha256((skill / name).read_bytes()).hexdigest() == h for name, h in manifest.items()):
            raise RuntimeError('ZIP contents differ from packaged checksums')
        if (skill / 'LICENSE').read_bytes() != (ROOT / 'LICENSE').read_bytes():
            raise RuntimeError('Standalone skill must retain the project license')
        for relative in manifest:
            if re.search(r'[A-Za-z]:[\\/]|/Users/|/home/', (skill / relative).read_text(encoding='utf-8')):
                raise RuntimeError(f'Nonportable host path in skill file {relative}')
        for target in re.findall(r'\]\(([^)]+)\)', (skill / 'SKILL.md').read_text(encoding='utf-8')):
            if not (skill / target).is_file():
                raise RuntimeError(f'Broken skill reference {target}')

        def run(label, arguments, expected=0):
            result = subprocess.run([str(python), '-B', *map(str, arguments)], cwd=folder,
                env=env, capture_output=True, text=True, encoding='utf-8', timeout=30)
            record = dict(case=label, passed=result.returncode == expected,
                          exit_code=result.returncode, stdout=result.stdout.strip(), stderr=result.stderr.strip())
            results.append(record)
            if not record['passed']:
                raise RuntimeError(f'{label} failed: {result.stderr}\n{result.stdout}')
            return result

        run('external-skill-validator' if validator else 'portable-skill-validator',
            [validator or ROOT / 'tools/validate_skill.py', skill])
        run('codex-ui-metadata-contract', ['-c',
            'import sys, yaml; from pathlib import Path; '
            'data=yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")); '
            'ui=data["interface"]; assert 25 <= len(ui["short_description"]) <= 64; '
            'assert "$deterministic-pixel-art" in ui["default_prompt"]; '
            'assert data["policy"]["allow_implicit_invocation"] is True; print("UI metadata valid")',
            skill / 'agents/openai.yaml'])
        run('isolated-import-origin', ['-c',
            'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); '
            'import pixelart; assert Path(pixelart.__file__).is_relative_to(Path(sys.argv[1])); '
            'print(pixelart.__version__)', skill / 'scripts'])
        for name in ('gem-16', 'asymmetric-ship-32', 'generic-panel-96x40', 'minecraft-button-states'):
            output = folder / '输出 results' / f'{name}.png'
            metadata = output.with_suffix('.json')
            run(f'packaged-example-{name}', [cli, 'render', '--spec', skill / f'assets/{name}.json',
                '--out', output, '--preview', output.with_name(name + '-preview.png'), '--metadata', metadata])
            run(f'validate-example-{name}', [cli, 'validate', '--image', output])
        atlas_meta = json.loads((folder / '输出 results/minecraft-button-states.json').read_text(encoding='utf-8'))
        assert [c['name'] for c in atlas_meta['atlas']['cells']] == ['normal', 'hover', 'pressed', 'selected', 'disabled']

        # Held-out task: four named directional icons with safe margins, no MC palette.
        directions = {'right': [[3, 7], [9, 7], [9, 4], [12, 8], [9, 11], [9, 9], [3, 9]]}
        points = directions['right']
        directions['left'] = [[15 - x, y] for x, y in points]
        directions['down'] = [[y, x] for x, y in points]
        directions['up'] = [[y, 15 - x] for x, y in points]
        arrow_spec = dict(kind='atlas', columns=4, cells=[dict(name=name,
            spec=dict(kind='draw', size=[16, 16], operations=[dict(op='polygon', points=points, color='36CFC9')]))
            for name, points in directions.items()])
        source, output, metadata = folder / '四方向.json', folder / '四方向.png', folder / '四方向-layout.json'
        source.write_text(json.dumps(arrow_spec), encoding='utf-8')
        rules = folder / '透明边距.json'
        rules.write_text(json.dumps(dict(size=[64, 16], mode='RGBA', alpha=[0, 255], cell_size=[16, 16],
                                         transparent_margin=1, nonempty=True)), encoding='utf-8')
        run('held-out-directional-atlas-render', [cli, 'render', '--spec', source, '--out', output,
                                                  '--metadata', metadata, '--rules', rules])
        run('held-out-directional-atlas-contract', [cli, 'validate', '--image', output, '--rules', rules])
        atlas_meta = json.loads(metadata.read_text(encoding='utf-8'))
        assert [c['name'] for c in atlas_meta['atlas']['cells']] == ['right', 'left', 'down', 'up']

        # Held-out task: an opaque custom toolbar, not subject to transparent icon margins.
        toolbar = dict(kind='draw', size=[50, 18], background='16223D', operations=[
            dict(op='rect', x=3, y=3, w=20, h=12, color='36CFC9'),
            dict(op='rect', x=27, y=3, w=20, h=12, color='F7B955')])
        source = folder / '工具栏.json'
        source.write_text(json.dumps(toolbar), encoding='utf-8')
        rules.write_text(json.dumps(dict(size=[50, 18], alpha=[255], mode='RGBA')), encoding='utf-8')
        run('held-out-opaque-toolbar', [cli, 'render', '--spec', source, '--out', folder / '工具栏.png', '--rules', rules])

        # Held-out task: 5x3 odd-centered mirror and partial alpha.
        source.write_text(json.dumps(dict(kind='grid', rows=['abc', 'bca'], palette={
            'a': '12345680', 'b': '36CFC9', 'c': None}, mirror='xy', center_x=True, center_y=True)), encoding='utf-8')
        rules.write_text(json.dumps(dict(size=[5, 3], alpha=[0, 128, 255])), encoding='utf-8')
        run('held-out-odd-mirror-semialpha', [cli, 'render', '--spec', source, '--out', folder / '镜像.png', '--rules', rules])

        source = folder / '面板.dsl'
        source.write_text('CANVAS 40 24\nBG C6C6C6\nRECT 2 2 8 8 123456\nBTN 12 3 24 18 NORMAL\n', encoding='utf-8')
        run('portable-dsl-render', [cli, 'render', '--spec', source, '--out', folder / '面板.png'])
        run('portable-preview', [cli, 'preview', '--image', folder / '面板.png', '--out', folder / '面板放大.png', '--background', 'C6C6C6'])
        source.write_text('CANVAS 2 2\nTYPO 1', encoding='utf-8')
        run('invalid-input-no-output', [cli, 'render', '--spec', source, '--out', folder / '错误.png'], expected=2)
        assert not (folder / '错误.png').exists()
        # Preserve held-out artifacts for inspection, but never the extracted runtime/venv.
        evidence = ROOT / 'evaluation/held-out'
        evidence.mkdir(exist_ok=True)
        for path in folder.glob('*.png'):
            (evidence / path.name).write_bytes(path.read_bytes())
        versions = run('fresh-runtime-versions', ['-c', 'import sys, PIL; print(sys.version); print(PIL.__version__)'])
        result = dict(passed=True, cases=results, case_count=len(results),
            testing='artifact-level CLI/API execution; no independent LLM or automatic discovery test',
            versions=versions.stdout.strip(),
            pythonpath_cleared=True, archive_files=len(manifest), no_host_paths=True,
            unicode_space_working_directory=True)
        (ROOT / 'evaluation/skill-tests.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'passed': True, 'cases': len(results), 'zip_files': len(manifest)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--validator', type=Path, help='Optional external skill-creator validator')
    args = parser.parse_args()
    main(args.python.resolve(), args.validator.resolve() if args.validator else None)
