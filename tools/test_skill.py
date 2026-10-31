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


def invocation_path(path):
    """Absolute invocation path, deliberately preserving a venv symlink."""
    return Path(os.path.abspath(path))


def nonportable_host_path(text):
    # Citations are URLs, not machine paths; avoid matching the s:/ in https://.
    without_urls = re.sub(r'https?://\S+', '', text)
    return re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/', without_urls) is not None


def validate_local_references(skill):
    """Check entry and reference files; fragments identify sections, not files."""
    for doc in [skill / 'SKILL.md', *sorted((skill / 'references').glob('*.md'))]:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            filename = target.partition('#')[0]
            if filename and '://' not in target and not (doc.parent / filename).is_file():
                raise RuntimeError(f'Broken skill reference {doc.name} -> {target}')


def main(python, validator):
    env = {k: v for k, v in os.environ.items()
           if k not in ('PYTHONPATH', 'PYTHONHOME', 'PIXELART_PORTABLE_OUTPUT')}
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
            if relative.endswith('.png'):
                continue
            if nonportable_host_path((skill / relative).read_text(encoding='utf-8')):
                raise RuntimeError(f'Nonportable host path in skill file {relative}')
        validate_local_references(skill)

        def run(label, arguments, expected=0, extra_env=None):
            result = subprocess.run([str(python), '-B', *map(str, arguments)], cwd=folder,
                env={**env, **(extra_env or {})}, capture_output=True, text=True, encoding='utf-8', timeout=30)
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

        for source in sorted((skill / 'assets/quality').glob('*.json')):
            name = source.stem
            output = folder / 'quality 输出' / f'{name}.png'
            run(f'quality-render-{name}', [cli, 'render', '--spec', source, '--out', output])
            run(f'quality-review-{name}', [cli, 'review', '--image', output,
                '--context', skill / 'assets/quality/contexts' / source.name,
                '--compare', output, '--out-dir', folder / 'reviews' / name])
            report = json.loads((folder / 'reviews' / name / 'report.json').read_text(encoding='utf-8'))
            assert report['advisory'] and report['comparison']['changed_visible_pixels'] == 0
        from PIL import Image
        warning_image = folder / 'intentional particle.png'
        with Image.new('RGBA', (3, 3)) as particle:
            particle.putpixel((1, 1), (255, 200, 100, 128))
            particle.save(warning_image)
        run('packaged-advisory-warning-exit-zero', [cli, 'review', '--image', warning_image,
            '--out-dir', folder / 'warning-review'])
        inspection=folder/'pixel-facts.json'
        run('packaged-inspect-grid', [cli,'inspect','--image',warning_image,'--grid','--out',inspection])
        assert json.loads(inspection.read_text(encoding='utf-8'))['facts']['bbox']==[1,1,1,1]
        imported=folder/'imported.json';roundtrip=folder/'roundtrip.png'
        run('packaged-lossless-import',[cli,'import','--image',warning_image,'--out',imported])
        run('packaged-import-render',[cli,'render','--spec',imported,'--out',roundtrip])
        with Image.open(warning_image) as a,Image.open(roundtrip) as b:
            assert a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
        run('packaged-import-no-clobber',[cli,'import','--image',warning_image,'--out',imported],expected=2)
        run('packaged-inspect-input-alias',[cli,'inspect','--image',warning_image,'--out',warning_image,'--force'],expected=2)
        embedded=folder/'embedded-atlas.png'
        run('packaged-embed-layout',[cli,'render','--spec',skill/'assets/minecraft-button-states.json',
            '--out',embedded,'--embed-metadata'])
        run('packaged-auto-layout-cell',[cli,'inspect','--image',embedded,'--cell','selected','--grid'])
        run('packaged-sidecar-layout-review',[cli,'review','--image',folder/'输出 results/minecraft-button-states.png',
            '--metadata',folder/'输出 results/minecraft-button-states.json','--out-dir',folder/'sidecar-review'])

        # Exercise the distributed workflow assets, not the source checkout.
        workflows=skill/'assets/workflows';work=folder/'新工作流 outputs';work.mkdir()
        run('packaged-preview-target-background',[cli,'render','--spec',skill/'assets/transparent-grid.json',
            '--out',work/'transparent.png','--preview',work/'target.png','--preview-background','E9EDF2','--scale','3'])
        with Image.open(work/'target.png') as preview:
            assert preview.size==(12,12) and preview.convert('RGB').getpixel((0,0))==(233,237,242)
        imported=work/'named-editable.json';candidate=work/'named-candidate.png';layout=work/'named-layout.json'
        run('packaged-named-import',[cli,'import','--image',workflows/'atlas-before.png',
            '--metadata',workflows/'atlas-before-layout.json','--out',imported])
        data=json.loads(imported.read_text(encoding='utf-8'))
        assert data['assembly']=='copy' and [cell['name'] for cell in data['cells']]==['add','refresh','transfer','lock']
        run('packaged-replace-named-cell',[cli,'replace-cell','--spec',imported,'--cell','transfer',
            '--replacement',workflows/'atlas-replacement.json','--out',work/'named-candidate.json',
            '--image-out',candidate,'--metadata',layout])
        run('packaged-verify-cell-boundary',[cli,'verify','--image',candidate,'--compare',workflows/'atlas-before.png',
            '--allow-region','32','0','16','16','--out',work/'verification.json'])
        verified=json.loads((work/'verification.json').read_text(encoding='utf-8'))
        assert verified['changed_rgba_pixels']==66 and verified['changed_outside']==0
        run('packaged-named-cell-import',[cli,'import','--image',workflows/'atlas-before.png',
            '--metadata',workflows/'atlas-before-layout.json','--cell','transfer','--out',work/'transfer-only.json'])
        selected=json.loads((work/'transfer-only.json').read_text(encoding='utf-8'))
        assert selected['kind']=='grid' and selected['size']==[16,16]
        run('packaged-named-cell-render',[cli,'render','--spec',work/'transfer-only.json','--out',work/'transfer-only.png'])
        with Image.open(workflows/'atlas-before.png') as atlas,Image.open(work/'transfer-only.png') as cell:
            assert cell.convert('RGBA').tobytes()==atlas.convert('RGBA').crop((32,0,48,16)).tobytes()
        run('packaged-named-cell-unknown',[cli,'import','--image',workflows/'atlas-before.png',
            '--metadata',workflows/'atlas-before-layout.json','--cell','missing','--out',work/'missing-cell.json'],expected=2)
        assert not (work/'missing-cell.json').exists()
        run('packaged-named-cell-stale-layout',[cli,'import','--image',candidate,
            '--metadata',workflows/'atlas-before-layout.json','--cell','transfer','--out',work/'stale-cell.json'],expected=2)
        assert not (work/'stale-cell.json').exists()
        run('packaged-named-cell-embedded',[cli,'import','--image',embedded,'--cell','selected',
            '--out',work/'embedded-cell.json'])
        run('packaged-verify-reject-wrong-region',[cli,'verify','--image',candidate,'--compare',workflows/'atlas-before.png',
            '--allow-region','0','0','16','16'],expected=1)
        run('packaged-named-candidate-inspect',[cli,'inspect','--image',candidate,'--metadata',layout,'--cell','transfer','--grid'])
        run('packaged-named-stale-layout',[cli,'inspect','--image',candidate,
            '--metadata',workflows/'atlas-before-layout.json','--cell','transfer'],expected=2)
        run('packaged-replace-input-alias',[cli,'replace-cell','--spec',imported,'--cell','transfer',
            '--replacement',workflows/'atlas-replacement.json','--out',imported,'--force'],expected=2)
        run('packaged-native-128-render',[cli,'render','--spec',workflows/'sprite-128.json','--out',work/'sprite.png'])
        light=work/'light-context.json';light.write_text(json.dumps(dict(asset_type='sprite',
            backgrounds=[dict(name='light',color='E9EDF2')],primary_background='light')),encoding='utf-8')
        run('packaged-light-silhouette',[cli,'review','--image',work/'sprite.png','--context',light,'--out-dir',work/'review'])
        report=json.loads((work/'review/report.json').read_text(encoding='utf-8'))
        assert report['facts']['silhouette_color']==[0,0,0,255]
        silhouette=next(v for v in report['facts']['review_views'] if v['label']=='alpha silhouette')
        x,y,w,h=silhouette['sheet_rect']
        with Image.open(work/'review/review.png') as sheet:
            assert len(sheet.crop((x,y,x+w,y+h)).getcolors(w*h))>1
        run('packaged-component-assembly',[cli,'assemble','--project',workflows/'scene-components.json',
            '--out',work/'components.png','--report',work/'components.json'])
        run('packaged-tile-assembly',[cli,'assemble','--project',workflows/'scene-tiles.json',
            '--out',work/'tiles.png','--report',work/'tiles.json','--seams',work/'seams.png',
            '--preview',work/'scene-preview.png','--scale','2'])
        run('packaged-whole-scene-control',[cli,'render','--spec',workflows/'scene-control.json','--out',work/'control.png'])
        with Image.open(work/'control.png') as control:
            for name in ('components.png','tiles.png'):
                with Image.open(work/name) as assembled:
                    assert assembled.size==(256,256) and assembled.convert('RGBA').tobytes()==control.convert('RGBA').tobytes()
        tiles=json.loads((work/'tiles.json').read_text(encoding='utf-8'))
        assert tiles['uncovered_pixels']==0 and tiles['seam_count']==4 and len(tiles['seam_views'])==8
        run('packaged-assembly-input-alias',[cli,'assemble','--project',workflows/'scene-tiles.json',
            '--out',workflows/'tiles/nw.png','--force'],expected=2)
        run('packaged-portable-output',[cli,'render','--spec',skill/'assets/transparent-grid.json',
            '--out',work/'portable.png','--portable-output'])
        original=(work/'portable.png').read_bytes()
        run('packaged-portable-no-clobber',[cli,'render','--spec',skill/'assets/gem-16.json',
            '--out',work/'portable.png','--portable-output'],expected=2)
        assert (work/'portable.png').read_bytes()==original

        inherited={'PIXELART_PORTABLE_OUTPUT':'1'}
        invalid={'PIXELART_PORTABLE_OUTPUT':'invalid'}
        run('packaged-task-portable-render',[cli,'render','--spec',skill/'assets/transparent-grid.json',
            '--out',work/'task-portable.png'],extra_env=inherited)
        run('packaged-task-portable-import',[cli,'import','--image',work/'task-portable.png',
            '--out',work/'task-editable.json'],extra_env=inherited)
        run('packaged-task-portable-recipe',[skill/'scripts/recipes/icons.py',
            '--out-dir',work/'task-icons'],extra_env=inherited)
        run('packaged-task-portable-no-clobber',[cli,'render','--spec',skill/'assets/gem-16.json',
            '--out',work/'task-portable.png'],expected=2,extra_env=inherited)
        assert (work/'task-portable.png').read_bytes()==original
        run('packaged-task-invalid-output-setting',[cli,'render','--spec',skill/'assets/transparent-grid.json',
            '--out',work/'invalid-setting.png'],expected=2,extra_env=invalid)
        assert not (work/'invalid-setting.png').exists()
        run('packaged-task-cli-override',[cli,'render','--spec',skill/'assets/transparent-grid.json',
            '--out',work/'override.png','--portable-output'],extra_env=invalid)
        run('packaged-task-recipe-override',[skill/'scripts/recipes/icons.py',
            '--out-dir',work/'override-icons','--no-portable-output'],extra_env=invalid)
        run('packaged-task-readonly-independent',[cli,'inspect','--image',work/'task-portable.png'],extra_env=invalid)
        run('packaged-task-zero-keeps-default',[cli,'render','--spec',skill/'assets/transparent-grid.json',
            '--out',work/'default-setting.png'],extra_env={'PIXELART_PORTABLE_OUTPUT':'0'})

        # Authoring recipes must work from the ZIP with PYTHONPATH cleared.
        recipes=skill/'scripts/recipes';recipe_work=folder/'可读 recipes'
        for name in ('icons','buttons','courier128','scene256'):
            run('packaged-recipe-default-'+name,[recipes/(name+'.py'),'--out-dir',recipe_work/name])
        for name,reference in [('icons',workflows/'atlas-before.png'),('courier128',workflows/'sprite-128.png'),
                               ('scene256',workflows/'scene-256.png')]:
            with Image.open(recipe_work/name/'asset.png') as produced,Image.open(reference) as frozen:
                assert produced.size==frozen.size and produced.convert('RGBA').tobytes()==frozen.convert('RGBA').tobytes()
        with Image.open(recipe_work/'buttons/asset.png') as produced,Image.open(folder/'quality 输出/ui-states.png') as frozen:
            assert produced.convert('RGBA').tobytes()==frozen.convert('RGBA').tobytes()
        run('packaged-recipe-icons-edit',[recipes/'icons.py','--out-dir',recipe_work/'icons-edited','--ink','F5C26B'])
        run('packaged-recipe-ui-edit',[recipes/'buttons.py','--out-dir',recipe_work/'buttons-edited',
            '--width','64','--content','28','4','30','10','--hover','426B83'])
        run('packaged-recipe-sprite-edit',[recipes/'courier128.py','--out-dir',recipe_work/'courier-edited',
            '--stripe','E17B57','--stripe-light','F9D5A0'])
        run('packaged-recipe-sprite-scope',[cli,'verify','--image',recipe_work/'courier-edited/asset.png',
            '--compare',recipe_work/'courier128/asset.png','--allow-region','42','68','48','10'])
        for name in ('icons-edited','buttons-edited','courier-edited'):
            rebuilt=recipe_work/(name+'-rebuilt.png')
            run('packaged-recipe-rerender-'+name,[cli,'render','--spec',recipe_work/name/'asset.json','--out',rebuilt])
            with Image.open(rebuilt) as image,Image.open(recipe_work/name/'asset.png') as expected:
                assert image.convert('RGBA').tobytes()==expected.convert('RGBA').tobytes()
        run('packaged-recipe-context-review',[cli,'review','--image',recipe_work/'buttons-edited/asset.png',
            '--metadata',recipe_work/'buttons-edited/layout.json','--context',recipe_work/'buttons-edited/context.json',
            '--out-dir',recipe_work/'button-review'])

        # A real font is a caller-provided input, never an installed host fallback.
        font = folder/'字体 input.ttf'
        font.write_bytes((ROOT/'demos/pixel-ui/fonts/Silkscreen-Regular.ttf').read_bytes())
        run('packaged-label-buttons', [recipes/'buttons.py', '--out-dir', recipe_work/'label-buttons',
            '--width', '88', '--content', '23', '4', '63', '10'])
        label_args = [recipes/'label_atlas.py', '--image', recipe_work/'label-buttons/asset.png',
            '--metadata', recipe_work/'label-buttons/layout.json', '--context', recipe_work/'label-buttons/context.json',
            '--font', font, '--font-size', '8', '--labels', 'START', 'LOOP', 'EXPORT MAP',
            '--state-offset', 'pressed', '0', '1']
        for mode in ('monochrome', 'grayscale'):
            run('packaged-font-'+mode, [*label_args, '--font-mode', mode, '--out-dir', recipe_work/mode])
        fit=json.loads((recipe_work/'monochrome/text-fit.json').read_text(encoding='utf-8'))
        assert len(fit['instances'])==18 and fit['font']['mode']=='monochrome'
        assert fit['instances'][9]['origin'][1]-54==fit['instances'][0]['origin'][1]+1
        with Image.open(recipe_work/'monochrome/consumer.png') as mono, Image.open(recipe_work/'grayscale/consumer.png') as gray:
            assert mono.size==(264,108) and mono.tobytes()!=gray.tobytes()
        run('packaged-label-no-clobber', [*label_args, '--font-mode', 'monochrome', '--out-dir', recipe_work/'monochrome'], expected=2)
        run('packaged-label-bad-fit', [*label_args, '--font-mode', 'monochrome', '--padding', '3',
            '--out-dir', recipe_work/'label-bad'], expected=2)
        assert not (recipe_work/'label-bad').exists()
        result=run('packaged-grid-wide-cell', [cli,'inspect','--image',recipe_work/'label-buttons/asset.png',
            '--metadata',recipe_work/'label-buttons/layout.json','--cell','normal','--grid'], expected=2)
        assert 'selected 88x18 at (0,0)' in result.stderr and 'replace --cell' in result.stderr
        before=(recipe_work/'icons-edited/asset.png').read_bytes()
        run('packaged-recipe-no-clobber',[recipes/'icons.py','--out-dir',recipe_work/'icons-edited'],expected=2)
        assert (recipe_work/'icons-edited/asset.png').read_bytes()==before
        run('packaged-recipe-bad-content-no-output',[recipes/'buttons.py','--out-dir',recipe_work/'bad',
            '--content','0','0','30','18'],expected=2)
        assert not (recipe_work/'bad').exists()
        run('packaged-recipe-scene-edit',[recipes/'scene256.py','--out-dir',recipe_work/'scene-edited',
            '--roof','684C6A','--roof-light','A07A89'])
        run('packaged-recipe-rebuilt-component-assembly',[cli,'assemble','--project',recipe_work/'scene-edited/project.json',
            '--out',recipe_work/'scene-reassembled.png'])
        with Image.open(recipe_work/'scene-reassembled.png') as image,Image.open(recipe_work/'scene-edited/asset.png') as expected:
            assert image.convert('RGBA').tobytes()==expected.convert('RGBA').tobytes()

        # The minimal independently drawn owners must be usable from the ZIP alone.
        pair = recipe_work / 'chunk-pair'
        edited_pair = recipe_work / 'chunk-pair-edited'
        run('packaged-chunk-pair', [recipes/'chunk_pair.py', '--out-dir', pair])
        run('packaged-chunk-pair-edit', [recipes/'chunk_pair.py', '--out-dir', edited_pair, '--flag', '73A5AA'])
        run('packaged-chunk-pair-scope', [cli, 'verify', '--image', edited_pair/'asset.png',
            '--compare', pair/'asset.png', '--allow-region', '51', '5', '6', '4', '--out', edited_pair/'verified.json'])
        assert json.loads((edited_pair/'verified.json').read_text(encoding='utf-8'))['changed_rgba_pixels']==24
        assert (pair/'left/asset.png').read_bytes()==(edited_pair/'left/asset.png').read_bytes()
        previous = (edited_pair/'asset.png').read_bytes()
        run('packaged-one-owner-rebuild', [recipes/'chunk_right.py', '--out-dir', edited_pair/'right',
            '--flag', 'C47763', '--force'])
        run('packaged-owner-reassembly', [cli, 'assemble', '--project', edited_pair/'project.json',
            '--out', edited_pair/'reassembled.png', '--report', edited_pair/'reassembled-report.json',
            '--seams', edited_pair/'reassembled-seams.png'])
        run('packaged-owner-reassembly-scope', [cli, 'verify', '--image', edited_pair/'reassembled.png',
            '--compare', pair/'asset.png', '--allow-region', '51', '5', '6', '4'])
        assert (edited_pair/'asset.png').read_bytes()==previous
        with Image.open(edited_pair/'reassembled.png') as image:
            assert image.convert('RGBA').getpixel((51,5))==(196,119,99,255)
        run('packaged-owner-stale-merge-layout', [cli, 'inspect', '--image', edited_pair/'reassembled.png',
            '--metadata', edited_pair/'layout.json'], expected=2)
        run('packaged-chunk-no-clobber', [recipes/'chunk_pair.py', '--out-dir', pair], expected=2)
        run('packaged-chunk-invalid-flag', [recipes/'chunk_pair.py', '--out-dir', recipe_work/'bad-chunks',
            '--flag', 'invalid'], expected=2)
        assert not (recipe_work/'bad-chunks').exists()

        bad_context = folder / 'bad-context.json'
        bad_context.write_text('{"atlas":{}}', encoding='utf-8')
        run('packaged-bad-context-no-output', [cli, 'review', '--image', warning_image,
            '--context', bad_context, '--out-dir', folder / 'bad-review'], expected=2)
        assert not (folder / 'bad-review').exists()
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
    # POSIX venv interpreters are symlinks: keep the invocation path, not its target.
    main(invocation_path(args.python), args.validator.resolve() if args.validator else None)
