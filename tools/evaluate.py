"""Reproducible compatibility, correctness and timing evidence; no original writes."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from pixelart import PixelArtError, render, validate
from tools.migrate_assets import constants, mode_spec, nexus_spec
from tools.baseline import verify_fixtures


def load_legacy(name):
    path = ROOT / 'baselines/snapshot/llm-pixel-art' / name
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node,
        (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef)) or (
            isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
                (t.id.isupper() or t.id == 'Mask') for target in node.targets for t in ast.walk(target)))]
    namespace = {'__file__': str(path), '__name__': '__evaluation__'}
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace, tree


def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def timing(function, count=400):
    for _ in range(20):
        function()
    samples = []
    for _ in range(count):
        start = time.perf_counter_ns()
        function()
        samples.append((time.perf_counter_ns() - start) / 1e6)
    tracemalloc.start()
    for _ in range(10):
        function()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return dict(median_ms=statistics.median(samples), p95_ms=percentile(samples, .95),
                samples=count, python_peak_bytes=peak)


def compare_outputs(entries):
    result = []
    for entry in entries:
        relative = entry['output']
        new = render(json.loads((ROOT / entry['spec']).read_text(encoding='utf-8')))
        with Image.open(ROOT / 'baselines/rendered' / relative) as image:
            old = image.convert('RGBA')
            diff = sum(a != b for a, b in zip(old.get_flattened_data(), new.get_flattened_data()))
            old_mode = image.mode
        same = new.size == old.size and diff == 0
        current = ROOT / 'baselines/snapshot' / relative
        runtime_equal = None
        if current.exists():
            with Image.open(current) as image:
                runtime_equal = new.size == image.size and new.tobytes() == image.convert('RGBA').tobytes()
        result.append(dict(output=relative, same_rgba=same, original_mode=old_mode,
            new_mode=new.mode, changed_pixels=diff, intended_change=entry['intended_change'],
            runtime_rgba_equal=runtime_equal, migration_method=entry['method'],
            valid=validate(new, {'size': list(old.size), 'mode': 'RGBA', 'alpha': [0, 255]})['valid']))
    return result


def comparison_sheet():
    sheet = Image.new('RGB', (920, 790), '#ECEEF2')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=17)
    small = ImageFont.load_default(size=13)
    draw.text((20, 14), 'DETERMINISTIC PIXEL ART - VERIFIED COMPARISONS', fill='#17233D', font=font)
    def panel(path, dest, scale):
        with Image.open(path) as source:
            image = source.convert('RGBA')
        bg = Image.new('RGBA', image.size, '#C6C6C6')
        bg.alpha_composite(image)
        sheet.paste(bg.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST).convert('RGB'), dest)
    legacy = Path('llm-pixel-art/out')
    draw.text((20, 50), 'Original composition: clipped / incomplete button frames', fill='#17233D', font=small)
    panel(ROOT / 'baselines/rendered' / legacy / 'redstone_on_buttons_1to1.png', (20, 74), 6)
    draw.text((470, 50), 'Corrected composition: 3 complete buttons + 2 transparent gaps', fill='#17233D', font=small)
    panel(ROOT / 'output/legacy' / legacy / 'redstone_on_buttons_1to1.png', (470, 74), 6)
    runtime = Path('src/main/resources/assets/chenamels_nexus/textures/gui/nexus/bidirectional_settings_footer-v4.png')
    draw.text((20, 220), 'Old generator (left) / Current resource + new spec (right)', fill='#17233D', font=small)
    panel(ROOT / 'baselines/rendered' / runtime, (20, 245), 7)
    panel(ROOT / 'output/legacy' / runtime, (210, 245), 7)
    draw.text((420, 260), '60 pixels differ from old generator.', fill='#17233D', font=small)
    draw.text((420, 285), 'New output matches current resource after RGBA conversion.', fill='#17233D', font=small)
    draw.text((20, 375), 'Generic examples (non-Minecraft palette; nearest-neighbor only)', fill='#17233D', font=font)
    panel(ROOT / 'output/examples/gem-16.png', (20, 415), 8)
    panel(ROOT / 'output/examples/asymmetric-ship-32.png', (185, 415), 5)
    panel(ROOT / 'output/examples/generic-panel-96x40.png', (385, 415), 5)
    draw.text((20, 635), 'Native sizes: 16x16 / 32x32 / 96x40', fill='#17233D', font=small)
    for name, x in [('gem-16', 20), ('asymmetric-ship-32', 70), ('generic-panel-96x40', 140)]:
        panel(ROOT / f'output/examples/{name}.png', (x, 665), 1)
    draw.text((20, 735), 'Artwork preservation is pixel-tested. Semantic/readability inspection is separately recorded.',
              fill='#17233D', font=small)
    sheet.save(ROOT / 'evaluation/comparison.png')


def main():
    out = ROOT / 'evaluation'
    out.mkdir(exist_ok=True)
    baseline = json.loads((ROOT / 'baselines/manifest.json').read_text(encoding='utf-8'))
    entries = json.loads((ROOT / 'specs/manifest.json').read_text(encoding='utf-8'))
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join([str(ROOT / 'src'), str(ROOT)]),
           'PYTHONIOENCODING': 'utf-8'}
    env.pop('PIXELART_PORTABLE_OUTPUT', None)  # Default-mode checks set task overrides explicitly.
    suite = subprocess.run([sys.executable, '-B', '-W', 'error', '-m', 'unittest', 'discover',
                            '-s', str(ROOT / 'tests'), '-v'], cwd=ROOT, env=env,
                           capture_output=True, text=True, encoding='utf-8', timeout=180)
    (out / 'tests.log').write_text(suite.stdout + suite.stderr, encoding='utf-8')
    if suite.returncode:
        raise RuntimeError('Tests failed; see evaluation/tests.log')
    dsl, dsl_tree = load_legacy('render_dsl_demo.py')
    nexus, _ = load_legacy('render_nexus_block_faces.py')
    modes, _ = load_legacy('render_side_mode_final_v6.py')
    panel_spec = json.loads(next(ROOT.glob('specs/legacy/**/gui_panel_128x48.json')).read_text(encoding='utf-8'))
    cases = [('panel_128x48', lambda: dsl['render'](dsl['SPEC_PANEL']), lambda: render(panel_spec)),
             ('block_front_16x16', lambda: nexus['render_face']('front'), lambda: render(nexus_spec('front'))),
             ('mode_atlas_80x16', modes['render_plane'], lambda: render(mode_spec()))]
    # Do not include recipe construction in only one side of a render benchmark.
    cached_nexus, cached_modes = nexus_spec('front'), mode_spec()
    cases[1] = (cases[1][0], cases[1][1], lambda: render(cached_nexus))
    cases[2] = (cases[2][0], cases[2][1], lambda: render(cached_modes))
    benchmarks = []
    for name, old, new in cases:
        if old().tobytes() != new().tobytes():
            raise RuntimeError(f'Benchmark output mismatch: {name}')
        a, b = timing(old), timing(new)
        benchmarks.append(dict(case=name, old=a, new=b, speedup=a['median_ms'] / b['median_ms'],
                               includes_io=False, includes_process_start=False))
    probes = []
    for name, spec in [('unknown_instruction', 'CANVAS 2 2\nMISTYPED 1'),
                       ('invalid_color_suffix', 'CANVAS 2 2\nBG FF0000XYZ'),
                       ('repeated_canvas', 'CANVAS 2 2\nCANVAS 3 3'),
                       ('implicit_clipping', 'CANVAS 2 2\nSLOT 0 0')]:
        try:
            dsl['render'](spec)
            old_rejects = False
        except Exception:
            old_rejects = True
        try:
            render(spec)
            new_rejects, message = False, ''
        except PixelArtError as exc:
            new_rejects, message = True, str(exc)
        probes.append(dict(case=name, old_rejects=old_rejects, new_rejects=new_rejects, message=message))
    # The original demo's actual grid loop, with its SPEC replaced by an unknown glyph.
    path = ROOT / 'baselines/snapshot/llm-pixel-art/render_demo.py'
    grid_tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    grid_tree.body = [n for n in grid_tree.body if n.lineno < 47]
    for node in grid_tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SPEC' for t in node.targets):
            node.value = ast.Constant('?')
    ast.fix_missing_locations(grid_tree)
    exec(compile(grid_tree, str(path), 'exec'), {'__file__': str(path), '__name__': '__evaluation__'})
    try:
        render(dict(kind='grid', rows=['?'], palette={'.': None}))
        rejected = False
    except PixelArtError:
        rejected = True
    probes.append(dict(case='unknown_grid_symbol', old_rejects=False, new_rejects=rejected))
    positive = 'CANVAS 2 2\nRECT 0 0 2 2 FF0000'
    rect_pixels = lambda image: sum(p[3] > 0 for p in image.get_flattened_data())
    rect_probe = dict(old_drawn=rect_pixels(dsl['render'](positive)), new_drawn=rect_pixels(render(positive)), expected=4)
    # Fair cold CLI comparison: same panel + 3x preview, two PNGs each, isolated disk writes.
    with tempfile.TemporaryDirectory(prefix='pixel-benchmark ') as folder:
        folder = Path(folder)
        driver = ast.unparse(dsl_tree) + '''\nfrom pathlib import Path\nimport sys\nout = Path(sys.argv[1])\nimage = render(SPEC_PANEL)\nimage.save(out)\nimage.resize((384,144), Image.Resampling.NEAREST).save(out.with_name('old-preview.png'))\n'''
        script = folder / 'old_panel.py'
        script.write_text(driver, encoding='utf-8')
        specfile = folder / 'panel.json'
        specfile.write_text(json.dumps(panel_spec), encoding='utf-8')
        old_cmd = [sys.executable, '-B', str(script), str(folder / 'old.png')]
        new_cmd = [sys.executable, '-B', str(ROOT / 'src/pixel_art.py'), 'render', '--spec', str(specfile),
                   '--out', str(folder / 'new.png'), '--preview', str(folder / 'new-preview.png'), '--scale', '3', '--force']
        cold = {'old': [], 'new': []}
        for iteration in range(12):
            for label, command in ([('old', old_cmd), ('new', new_cmd)] if iteration % 2 == 0 else [('new', new_cmd), ('old', old_cmd)]):
                start = time.perf_counter_ns()
                subprocess.run(command, cwd=folder, env=env, check=True, capture_output=True, timeout=30)
                cold[label].append((time.perf_counter_ns() - start) / 1e6)
        for a, b in [('old.png', 'new.png'), ('old-preview.png', 'new-preview.png')]:
            with Image.open(folder / a) as x, Image.open(folder / b) as y:
                if x.tobytes() != y.tobytes():
                    raise RuntimeError('Cold CLI outputs differ')
        cold_result = {k: dict(median_ms=statistics.median(v), p95_ms=percentile(v, .95), samples=len(v)) for k, v in cold.items()}
    comparisons = compare_outputs(entries)
    ordinary = [c for c in comparisons if not c['intended_change']]
    passed = (verify_fixtures(ROOT / 'baselines') and all(c['valid'] for c in comparisons)
        and len(ordinary) == 40 and all(c['same_rgba'] for c in ordinary)
        and all(p['new_rejects'] for p in probes) and rect_probe['new_drawn'] == 4
        and next(c for c in comparisons if 'footer-v4.png' in c['output'])['runtime_rgba_equal'])
    result = dict(quality_gate_passed=passed, python=sys.version, pillow=Image.__version__,
        runtime_sha256={p.relative_to(ROOT / 'src').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted((ROOT / 'src').rglob('*.py'))},
        fixture_files=len(baseline['fixture_files']), fixtures_unchanged=verify_fixtures(ROOT / 'baselines'),
        tests_passed=True, comparisons=comparisons, benchmarks=benchmarks,
        cold_cli=cold_result, error_probes=probes, rect_probe=rect_probe,
        spec_lengths=dict(old_panel_dsl_characters=len(dsl['SPEC_PANEL']),
                          new_panel_json_characters=len(json.dumps(panel_spec, separators=(',', ':')))),
        measurement_limits=['Python peak excludes native Pillow image buffers',
            'No token counts or LLM correction-round improvements were measured',
            'Cold CLI is same asset + preview, not the complete original four-output demo',
            'Lossless migrated encodings are not independent legacy algorithm rewrites'])
    (out / 'metrics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    comparison_sheet()
    if not passed:
        raise RuntimeError('Quality gate failed; do not package the skill')
    print(json.dumps({'quality_gate_passed': passed, 'identical': len(ordinary), 'intentional_changes': 3,
        'benchmarks': [{'case': b['case'], 'speedup': round(b['speedup'], 2)} for b in benchmarks], 'cold_cli': cold_result}))


if __name__ == '__main__':
    main()
