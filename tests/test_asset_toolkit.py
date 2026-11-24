"""Unit and integration tests for the pixel-asset workflow toolkit."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image
from pixelart.core import PixelArtError
from pixelart.toolkit import deliver_asset

ROOT = Path(__file__).resolve().parents[1]
TOOLKIT_CLI = ROOT / 'recipes/asset_toolkit.py'
SINGLE_CLI = ROOT / 'recipes/single_asset.py'


def _run_cli(script, args, *, env_extra=None):
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, '-B', str(script), *map(str, args)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=30,
    )


class AssetToolkitTests(unittest.TestCase):
    def _assert_input_alias_refused(self, source, out_dir, protected_path, **options):
        original = protected_path.read_bytes()
        with patch('pixelart.toolkit.publish') as publish:
            with self.assertRaisesRegex(PixelArtError, 'aliases input path'):
                deliver_asset(
                    source,
                    out_dir,
                    pack_zip=protected_path,
                    force=True,
                    **options,
                )
            publish.assert_not_called()
        self.assertEqual(protected_path.read_bytes(), original)
        self.assertFalse(out_dir.exists())

    def test_route_natural_language_intents(self):
        cases = [
            ('新建一个16x16的小图标', 'grid'),
            ('局部修改已有PNG的提灯玻璃颜色，使用掩码限定区域', 'png-native'),
            ('做一个同轮廓双态按钮，未点亮和点亮切换配色', 'shared-grid-states'),
            ('制作32x32宝箱开合双状态素材，箱盖抬起改变轮廓且支持局部回退', 'state-set'),
            ('保留命名图集格名并替换其中一个单元格', 'atlas'),
            ('保留独立图层组件拼接场景并检查接缝', 'assembly'),
        ]
        for prompt, expected_mode in cases:
            res = _run_cli(TOOLKIT_CLI, ['route', '--prompt', prompt])
            self.assertEqual(res.returncode, 0, res.stderr)
            data = json.loads(res.stdout)
            self.assertEqual(data['recommended_mode'], expected_mode)
            self.assertIn('asset_toolkit.py', data['entrypoint'])

    def test_grid_deliver_rebuild_conflict_and_extra_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / 'brief.txt'
            note.write_text('16x16 gem icon brief\n', encoding='utf-8')
            out_dir = root / 'gem-out'
            zip_path = root / 'gem.zip'

            res = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver',
                    '--source', ROOT / 'examples/gem-16.json',
                    '--out-dir', out_dir,
                    '--scale', '6',
                    '--background', '172033',
                    '--pack-zip', zip_path,
                    '--extra-file', note,
                ],
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            payload = json.loads(res.stdout)
            self.assertEqual(payload['mode'], 'grid')
            self.assertTrue(payload['tiers']['required']['rebuild_verified'])
            self.assertTrue(payload['tiers']['contract']['passed'])
            self.assertTrue(zip_path.is_file())
            with zipfile.ZipFile(zip_path) as zf:
                self.assertIsNone(zf.testzip())
                self.assertIn('extras/brief.txt', zf.namelist())

            # Conflict without --force must fail (rc=2) and keep original bytes untouched
            orig_bytes = (out_dir / 'asset.png').read_bytes()
            conflict = _run_cli(
                TOOLKIT_CLI,
                ['deliver', '--source', ROOT / 'examples/gem-16.json', '--out-dir', out_dir],
            )
            self.assertEqual(conflict.returncode, 2)
            self.assertEqual((out_dir / 'asset.png').read_bytes(), orig_bytes)

            # Independent rebuild from ZIP into a fresh directory
            rebuilt_dir = root / 'rebuilt'
            reb = _run_cli(
                TOOLKIT_CLI,
                ['rebuild', '--input', zip_path, '--out-dir', rebuilt_dir],
            )
            self.assertEqual(reb.returncode, 0, reb.stderr)
            reb_data = json.loads(reb.stdout)
            self.assertTrue(reb_data['verified'])
            self.assertTrue(reb_data['crc_checked'])
            with Image.open(out_dir / 'asset.png') as a, Image.open(rebuilt_dir / 'asset.png') as b:
                self.assertEqual(a.convert('RGBA').tobytes(), b.convert('RGBA').tobytes())

    def test_png_native_63_colors_and_mask_boundary_enforcement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Create a 64x64 PNG with 65 distinct opaque colors (past the 62-color grid cliff)
            img = Image.new('RGBA', (64, 64), (10, 20, 30, 255))
            for i in range(64):
                img.putpixel((i, 0), (i * 3, 100, 200, 255))
            img.putpixel((10, 10), (200, 40, 40, 255))
            src_png = root / 'rich65.png'
            img.save(src_png)

            # single_asset --source-mode png-native also handles >62 colors cleanly
            sa_dir = root / 'single-native'
            sa_res = _run_cli(
                SINGLE_CLI,
                ['--source', src_png, '--source-mode', 'png-native', '--out-dir', sa_dir],
            )
            self.assertEqual(sa_res.returncode, 0, sa_res.stderr)
            self.assertTrue((sa_dir / 'manifest.json').is_file())

            # Masked local recolor via toolkit png-native
            mask = Image.new('L', (64, 64), 0)
            for y in range(8, 14):
                for x in range(8, 14):
                    mask.putpixel((x, y), 255)
            mask_path = root / 'mask.png'
            mask.save(mask_path)

            recolor_map = root / 'map.json'
            recolor_map.write_text(json.dumps({'C82828FF': '36CFC9FF'}), encoding='utf-8')
            out_dir = root / 'png-edited'
            res = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver',
                    '--mode', 'png-native',
                    '--source', src_png,
                    '--mask', mask_path,
                    '--recolor', recolor_map,
                    '--out-dir', out_dir,
                ],
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            data = json.loads(res.stdout)
            self.assertEqual(data['tiers']['contract']['details']['boundary']['changed_outside'], 0)
            self.assertEqual(data['tiers']['contract']['details']['boundary']['changed_inside'], 1)
            self.assertEqual(data['tiers']['contract']['details']['alpha']['alpha_changed_pixels'], 0)

            # Intentional failure: patch writing outside mask must be rejected with rc=1 and zero output
            bad_patch = root / 'bad_patch.json'
            bad_patch.write_text(
                json.dumps({'ops': [{'op': 'pixel', 'x': 2, 'y': 2, 'color': 'FFFFFFFF'}]}),
                encoding='utf-8',
            )
            bad_out = root / 'should-not-exist'
            bad_res = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver',
                    '--mode', 'png-native',
                    '--source', src_png,
                    '--mask', mask_path,
                    '--patch', bad_patch,
                    '--out-dir', bad_out,
                ],
            )
            self.assertEqual(bad_res.returncode, 1)
            self.assertFalse(bad_out.exists())

    def test_shared_grid_states_success_and_preflight_alpha_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good_spec = {
                'version': 1,
                'kind': 'shared-grid-states',
                'rows': ['....', '.OO.', '.OC.', '....'],
                'base_palette': {'.': None, 'O': '202634'},
                'states': {
                    'unlit': {'C': '3A506B'},
                    'lit': {'C': 'F7C948'},
                },
            }
            good_path = root / 'shared.json'
            good_path.write_text(json.dumps(good_spec), encoding='utf-8')
            out_dir = root / 'shared-out'
            zip_path = root / 'shared.zip'

            res = _run_cli(
                TOOLKIT_CLI,
                ['deliver', '--source', good_path, '--out-dir', out_dir, '--pack-zip', zip_path],
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            reb = _run_cli(
                TOOLKIT_CLI,
                ['rebuild', '--input', zip_path, '--out-dir', root / 'shared-rebuilt'],
            )
            self.assertEqual(reb.returncode, 0, reb.stderr)

            # Alpha mismatch must fail preflight with rc=1 and leave no output directory
            bad_spec = json.loads(json.dumps(good_spec))
            bad_spec['states']['lit']['C'] = None
            bad_path = root / 'bad_shared.json'
            bad_path.write_text(json.dumps(bad_spec), encoding='utf-8')
            bad_out = root / 'bad-shared-out'
            bad_res = _run_cli(
                TOOLKIT_CLI,
                ['deliver', '--source', bad_path, '--out-dir', bad_out],
            )
            self.assertEqual(bad_res.returncode, 1)
            self.assertIn('state-set', bad_res.stderr)
            self.assertFalse(bad_out.exists())

    def test_cli_shared_grid_states_rejects_state_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = {
                'kind': 'shared-grid-states',
                'rows': ['.'],
                'base_palette': {'.': None},
                'states': {'../../escape': {}},
            }
            source = root / 'shared.json'
            source_bytes = json.dumps(spec).encode('utf-8')
            source.write_bytes(source_bytes)
            out_dir = root / 'delivery'
            before = {path.relative_to(root).as_posix() for path in root.rglob('*')}

            result = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver', '--mode', 'shared-grid-states',
                    '--source', source, '--out-dir', out_dir,
                ],
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('invalid state filename', result.stderr)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertFalse(out_dir.exists())
            self.assertFalse((root / 'escape.json').exists())
            self.assertFalse((root / 'escape.png').exists())
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in root.rglob('*')},
                before,
            )

    def test_cli_state_set_rejects_state_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = {
                'kind': 'state-set',
                'base': {
                    'version': 1,
                    'kind': 'grid',
                    'rows': ['.'],
                    'palette': {'.': None},
                },
                'states': {'../../escape': {}},
            }
            source = root / 'state-set.json'
            source_bytes = json.dumps(spec).encode('utf-8')
            source.write_bytes(source_bytes)
            out_dir = root / 'delivery'
            before = {path.relative_to(root).as_posix() for path in root.rglob('*')}

            result = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver', '--mode', 'state-set',
                    '--source', source, '--out-dir', out_dir,
                ],
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('invalid state filename', result.stderr)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertFalse(out_dir.exists())
            self.assertFalse((root / 'escape.json').exists())
            self.assertFalse((root / 'escape.png').exists())
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in root.rglob('*')},
                before,
            )

    def test_state_set_alpha_delta_recolor_order_and_local_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_spec = {
                'version': 1,
                'kind': 'state-set',
                'base': {
                    'version': 1,
                    'kind': 'grid',
                    'rows': [
                        '........',
                        '........',
                        '..WWWW..',
                        '..WWWW..',
                        '..BBBB..',
                        '..BBBB..',
                        '........',
                        '........',
                    ],
                    'palette': {'.': None, 'W': '8B5A2B', 'B': '6B4226'},
                },
                'regions': {
                    'lid_zone': [0, 0, 8, 4],
                    'body_zone': [0, 4, 8, 4],
                },
                'states': {
                    'closed': {'patches': [], 'region_recolor': []},
                    'cursed_open': {
                        'allow_alpha_delta': ['lid_zone'],
                        'patches': [
                            {
                                'id': 'raise_lid',
                                'region': 'lid_zone',
                                'ops': [
                                    {'op': 'rect', 'x': 2, 'y': 0, 'w': 4, 'h': 2, 'color': '8B5A2B'},
                                ],
                            },
                            {
                                'id': 'optional_spark',
                                'region': 'lid_zone',
                                'ops': [
                                    {'op': 'pixel', 'x': 0, 'y': 0, 'color': 'FFE066'},
                                ],
                            },
                        ],
                        'region_recolor': [
                            {'regions': ['lid_zone', 'body_zone'], 'map': {'8B5A2BFF': '7A49A5FF'}},
                        ],
                    },
                },
            }
            spec_path = root / 'chest.json'
            spec_path.write_text(json.dumps(state_spec), encoding='utf-8')

            out_full = root / 'chest-full'
            res_full = _run_cli(
                TOOLKIT_CLI,
                ['deliver', '--source', spec_path, '--out-dir', out_full],
            )
            self.assertEqual(res_full.returncode, 0, res_full.stderr)
            with Image.open(out_full / 'states/cursed_open.png') as opened:
                # Raised lid pixel at (2,0) MUST be recolored to purple (patch-before-recolor invariant!)
                self.assertEqual(opened.convert('RGBA').getpixel((2, 0)), (122, 73, 165, 255))
                self.assertEqual(opened.convert('RGBA').getpixel((0, 0)), (255, 224, 102, 255))

            # Local rollback: disable optional_spark while keeping raise_lid and recolor
            out_rb = root / 'chest-rollback'
            res_rb = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver',
                    '--source', spec_path,
                    '--disable-patch', 'optional_spark',
                    '--out-dir', out_rb,
                ],
            )
            self.assertEqual(res_rb.returncode, 0, res_rb.stderr)
            with Image.open(out_rb / 'states/cursed_open.png') as opened:
                self.assertEqual(opened.convert('RGBA').getpixel((2, 0)), (122, 73, 165, 255))
                self.assertEqual(opened.convert('RGBA').getpixel((0, 0)), (0, 0, 0, 0))

            # Intentional failure: alpha change in locked body_zone must fail contract (rc=1)
            bad_spec = json.loads(json.dumps(state_spec))
            bad_spec['states']['cursed_open']['patches'].append(
                {
                    'id': 'erase_body',
                    'region': 'body_zone',
                    'ops': [{'op': 'pixel', 'x': 2, 'y': 4, 'color': None}],
                }
            )
            bad_path = root / 'chest_bad.json'
            bad_path.write_text(json.dumps(bad_spec), encoding='utf-8')
            bad_res = _run_cli(
                TOOLKIT_CLI,
                ['deliver', '--source', bad_path, '--out-dir', root / 'chest-bad-out'],
            )
            self.assertEqual(bad_res.returncode, 1)
            self.assertFalse((root / 'chest-bad-out').exists())

    def test_multistate_rejects_unsafe_and_equivalent_state_names_before_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_template = {
                'kind': 'shared-grid-states',
                'rows': ['.'],
                'base_palette': {'.': None},
            }
            state_set_template = {
                'kind': 'state-set',
                'base': {
                    'version': 1,
                    'kind': 'grid',
                    'rows': ['.'],
                    'palette': {'.': None},
                },
            }
            invalid_names = [
                '../../escape',
                '/absolute',
                r'C:\\escape',
                'folder/name',
                r'folder\\name',
                '.',
                '..',
                'CON',
                'NUL.txt',
                'COM1',
                'bad:name',
                'trailing.',
                'control\x01name',
            ]

            cases = [(shared_template, 'shared-grid-states'), (state_set_template, 'state-set')]
            for template, mode in cases:
                for index, name in enumerate(invalid_names):
                    with self.subTest(mode=mode, state=name):
                        spec = json.loads(json.dumps(template))
                        spec['states'] = {name: {}}
                        spec_path = root / f'{mode}-{index}.json'
                        spec_path.write_text(json.dumps(spec), encoding='utf-8')
                        out_dir = root / f'{mode}-{index}-out'
                        with patch('pixelart.toolkit.publish') as publish:
                            with self.assertRaises(PixelArtError):
                                deliver_asset(spec_path, out_dir, mode=mode)
                            publish.assert_not_called()
                        self.assertFalse(out_dir.exists())

                for index, duplicate_names in enumerate((('Idle', 'idle'), ('é', 'e\u0301'))):
                    with self.subTest(mode=mode, equivalent_names=duplicate_names):
                        spec = json.loads(json.dumps(template))
                        spec['states'] = {name: {} for name in duplicate_names}
                        spec_path = root / f'{mode}-duplicate-{index}.json'
                        spec_path.write_text(json.dumps(spec), encoding='utf-8')
                        out_dir = root / f'{mode}-duplicate-{index}-out'
                        with patch('pixelart.toolkit.publish') as publish:
                            with self.assertRaisesRegex(PixelArtError, 'resolve to the same filename'):
                                deliver_asset(spec_path, out_dir, mode=mode)
                            publish.assert_not_called()
                        self.assertFalse(out_dir.exists())

            self.assertFalse((root / 'escape.json').exists())
            self.assertFalse((root / 'escape.png').exists())

    def test_zip_output_path_conflicts_are_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.json'
            source.write_text((ROOT / 'examples/gem-16.json').read_text(encoding='utf-8'), encoding='utf-8')

            for index, zip_name in enumerate(('asset.png', 'ASSET.PNG')):
                with self.subTest(zip_name=zip_name):
                    out_dir = root / f'out-{index}'
                    with patch('pixelart.toolkit.publish') as publish:
                        with self.assertRaisesRegex(PixelArtError, 'output path conflict'):
                            deliver_asset(
                                source, out_dir, mode='grid', pack_zip=out_dir / zip_name
                            )
                        publish.assert_not_called()
                    self.assertFalse(out_dir.exists())

            existing_out = root / 'existing-out'
            existing_out.mkdir()
            existing_asset = existing_out / 'asset.png'
            existing_asset.write_bytes(b'preserve existing output')
            original = existing_asset.read_bytes()
            with patch('pixelart.toolkit.publish') as publish:
                with self.assertRaisesRegex(PixelArtError, 'output path conflict'):
                    deliver_asset(
                        source, existing_out, mode='grid',
                        pack_zip=existing_out / 'ASSET.PNG', force=True,
                    )
                publish.assert_not_called()
            self.assertEqual(existing_asset.read_bytes(), original)

    def test_zip_output_symlink_alias_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.json'
            source.write_text((ROOT / 'examples/gem-16.json').read_text(encoding='utf-8'), encoding='utf-8')
            out_dir = root / 'delivery'
            out_dir.mkdir()
            asset = out_dir / 'asset.png'
            asset.write_bytes(b'preserve existing output')
            alias_dir = root / 'delivery-alias'
            if os.name == 'nt':
                result = subprocess.run(
                    ['cmd.exe', '/c', 'mklink', '/J', str(alias_dir), str(out_dir)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                )
                if result.returncode:
                    self.skipTest(f'directory junctions are unavailable in this environment: {result.stderr}')
            else:
                try:
                    alias_dir.symlink_to(out_dir, target_is_directory=True)
                except OSError as exc:
                    self.skipTest(f'directory symlinks are unavailable in this environment: {exc}')
            alias = alias_dir / 'asset.png'

            original = asset.read_bytes()
            with patch('pixelart.toolkit.publish') as publish:
                with self.assertRaisesRegex(PixelArtError, 'output path conflict'):
                    deliver_asset(
                        source, out_dir, mode='grid', pack_zip=alias, force=True
                    )
                publish.assert_not_called()
            self.assertEqual(asset.read_bytes(), original)

    def test_cli_force_rejects_input_and_artifact_path_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.json'
            source.write_text((ROOT / 'examples/gem-16.json').read_text(encoding='utf-8'), encoding='utf-8')
            source_bytes = source.read_bytes()
            source_alias_out = root / 'source-alias-out'
            source_alias = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver', '--mode', 'grid', '--source', source,
                    '--out-dir', source_alias_out, '--pack-zip', source, '--force',
                ],
            )
            self.assertEqual(source_alias.returncode, 2, source_alias.stderr)
            self.assertIn('aliases input path', source_alias.stderr)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertFalse(source_alias_out.exists())

            out_dir = root / 'artifact-alias-out'
            out_dir.mkdir()
            asset = out_dir / 'asset.png'
            asset.write_bytes(b'preserve existing output')
            asset_bytes = asset.read_bytes()
            artifact_alias = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver', '--mode', 'grid', '--source', source,
                    '--out-dir', out_dir, '--pack-zip', asset, '--force',
                ],
            )
            self.assertEqual(artifact_alias.returncode, 2, artifact_alias.stderr)
            self.assertIn('output path conflict', artifact_alias.stderr)
            self.assertEqual(asset.read_bytes(), asset_bytes)

    def test_force_rejects_zip_aliases_to_every_read_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            grid_source = root / 'grid.json'
            grid_source.write_text((ROOT / 'examples/gem-16.json').read_text(encoding='utf-8'), encoding='utf-8')

            self._assert_input_alias_refused(
                grid_source, root / 'source-alias-out', grid_source, mode='grid'
            )

            contract = root / 'contract.json'
            contract.write_text('{}', encoding='utf-8')
            self._assert_input_alias_refused(
                grid_source, root / 'contract-alias-out', contract,
                mode='grid', contract_path=contract,
            )

            extra = root / 'brief.txt'
            extra.write_text('preserve input brief', encoding='utf-8')
            self._assert_input_alias_refused(
                grid_source, root / 'extra-alias-out', extra,
                mode='grid', extra_files=[extra],
            )

            source_png = root / 'source.png'
            image = Image.new('RGBA', (3, 1), (10, 20, 30, 255))
            image.putpixel((1, 0), (40, 50, 60, 255))
            image.save(source_png)
            baseline = root / 'baseline.png'
            image.save(baseline)
            mask = root / 'mask.png'
            Image.new('L', image.size, 255).save(mask)
            metadata = root / 'metadata.json'
            metadata.write_text(json.dumps({'version': 1, 'size': [3, 1], 'mode': 'RGBA'}), encoding='utf-8')
            recolor = root / 'recolor.json'
            recolor.write_text(json.dumps({'0A141EFF': '1E283CFF'}), encoding='utf-8')
            patch_spec = root / 'patch.json'
            patch_spec.write_text(json.dumps({'ops': [{'op': 'pixel', 'x': 0, 'y': 0, 'color': '1E283CFF'}]}), encoding='utf-8')

            for option, path in (
                ('--baseline', baseline),
                ('--metadata', metadata),
                ('--mask', mask),
                ('--recolor', recolor),
                ('--patch', patch_spec),
            ):
                with self.subTest(input_option=option):
                    options = {'mode': 'png-native'}
                    if option == '--baseline':
                        options['baseline'] = path
                    elif option == '--metadata':
                        options['metadata'] = path
                    elif option == '--mask':
                        options['mask'] = path
                    elif option == '--recolor':
                        options['recolor_path'] = path
                    else:
                        options['patch_path'] = path
                    if option == '--recolor':
                        options['mask'] = mask
                    if option == '--patch':
                        options['mask'] = mask
                    self._assert_input_alias_refused(
                        source_png, root / f'{option[2:]}-alias-out', path, **options
                    )

            output_source_dir = root / 'source-output'
            output_source_dir.mkdir()
            output_source = output_source_dir / 'asset.png'
            image.save(output_source)
            original_source = output_source.read_bytes()
            with patch('pixelart.toolkit.publish') as publish:
                with self.assertRaisesRegex(PixelArtError, 'aliases input path'):
                    deliver_asset(output_source, output_source_dir, force=True)
                publish.assert_not_called()
            self.assertEqual(output_source.read_bytes(), original_source)

            atlas_source = root / 'atlas-before.png'
            atlas_source.write_bytes((ROOT / 'examples/workflows/atlas-before.png').read_bytes())
            atlas_metadata = root / 'atlas-layout.json'
            atlas_metadata.write_bytes((ROOT / 'examples/workflows/atlas-before-layout.json').read_bytes())
            replacement = root / 'replacement.json'
            replacement.write_bytes((ROOT / 'examples/workflows/atlas-replacement.json').read_bytes())
            self._assert_input_alias_refused(
                atlas_source, root / 'replacement-alias-out', replacement,
                mode='atlas', metadata=atlas_metadata, replace_cell_name='transfer',
                replacement_path=replacement,
            )

            project = json.loads((ROOT / 'examples/workflows/scene-components.json').read_text(encoding='utf-8'))
            project_path = root / 'project.json'
            project_path.write_text(json.dumps(project), encoding='utf-8')
            first_layer = None
            source_layers = ROOT / 'examples/workflows'
            for part in project['parts']:
                layer = root / part['image']
                layer.parent.mkdir(parents=True, exist_ok=True)
                layer.write_bytes((source_layers / part['image']).read_bytes())
                first_layer = first_layer or layer
            self._assert_input_alias_refused(
                project_path, root / 'layer-alias-out', first_layer,
                mode='assembly',
            )

    def test_png_native_rebuild_guides_run_with_unpacked_skill_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / 'unpacked-skill' / 'deterministic-pixel-art'
            for source_root, package_root in (
                (ROOT / 'skill-content', skill_dir),
                (ROOT / 'src/pixelart', skill_dir / 'scripts/pixelart'),
                (ROOT / 'recipes', skill_dir / 'scripts/recipes'),
            ):
                pattern = '*' if source_root.name == 'skill-content' else '*.py'
                for source_file in source_root.rglob(pattern):
                    if not source_file.is_file():
                        continue
                    relative = source_file.relative_to(source_root)
                    target = package_root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target)
            (skill_dir / 'scripts').mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / 'src/pixel_art.py', skill_dir / 'scripts/pixel_art.py')
            shutil.copy2(ROOT / 'LICENSE', skill_dir / 'LICENSE')
            shutil.copy2(ROOT / 'requirements.txt', skill_dir / 'requirements.txt')
            skill_cli = skill_dir / 'scripts/recipes/asset_toolkit.py'

            def verify_from_guide(bundle_dir):
                guide = (bundle_dir / 'REBUILD.md').read_text(encoding='utf-8')
                command_line = next(
                    line.strip()
                    for line in guide.splitlines()
                    if ' verify ' in line and line.strip().startswith('python ')
                )
                arguments = shlex.split(command_line)
                self.assertEqual(arguments[0], 'python')
                arguments[0:2] = [sys.executable, str(skill_cli)]
                return subprocess.run(
                    arguments,
                    cwd=bundle_dir,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=30,
                )

            source = root / 'untouched.png'
            Image.new('RGBA', (2, 1), (10, 20, 30, 255)).save(source)
            contract = {'size': [2, 1], 'binary_alpha': True}
            contract_path = root / 'declared.json'
            contract_path.write_text(json.dumps(contract), encoding='utf-8')
            untouched_zip = root / 'untouched.zip'
            deliver_asset(
                source, root / 'untouched-out', mode='png-native',
                contract_path=contract_path, pack_zip=untouched_zip,
            )
            untouched_bundle = root / 'untouched-bundle'
            untouched_bundle.mkdir()
            with zipfile.ZipFile(untouched_zip) as archive:
                archive.extractall(untouched_bundle)
            untouched_guide = (untouched_bundle / 'REBUILD.md').read_text(encoding='utf-8')
            untouched_command = next(line for line in untouched_guide.splitlines() if ' verify ' in line)
            self.assertIn('--image asset.png', untouched_command)
            self.assertNotIn('--baseline', untouched_command)
            self.assertNotIn('--compare', untouched_command)
            self.assertIn('--contract contract.json', untouched_command)
            self.assertEqual(json.loads((untouched_bundle / 'contract.json').read_bytes()), contract)
            untouched_result = verify_from_guide(untouched_bundle)
            self.assertEqual(untouched_result.returncode, 0, untouched_result.stderr)
            untouched_details = json.loads(untouched_result.stdout)['tiers']['contract']['details']
            self.assertEqual(untouched_details['declared_contract'], {
                'declared': True, 'size': [2, 1], 'non_binary_alpha_pixels': 0,
            })

            baseline = root / 'edited-baseline.png'
            Image.new('RGBA', (2, 1), (10, 20, 30, 255)).save(baseline)
            mask = Image.new('L', (2, 1), 0)
            mask.putpixel((0, 0), 255)
            mask_path = root / 'edited-mask.png'
            mask.save(mask_path)
            patch = root / 'edit.json'
            patch.write_text(
                json.dumps({'ops': [{'op': 'pixel', 'x': 0, 'y': 0, 'color': '1E283C00'}]}),
                encoding='utf-8',
            )
            edit_options = {
                'mode': 'png-native',
                'baseline': baseline,
                'patch_path': patch,
                'mask': mask_path,
                'allow_regions': [[0, 0, 1, 1]],
                'contract_path': contract_path,
            }
            with self.assertRaisesRegex(PixelArtError, 'alpha lock violated'):
                deliver_asset(baseline, root / 'locked-out', **edit_options)

            edited_zip = root / 'edited.zip'
            deliver_asset(
                baseline, root / 'edited-out', allow_alpha_change=True, pack_zip=edited_zip,
                **edit_options,
            )
            edited_bundle = root / 'edited-bundle'
            edited_bundle.mkdir()
            with zipfile.ZipFile(edited_zip) as archive:
                archive.extractall(edited_bundle)
            edited_guide = (edited_bundle / 'REBUILD.md').read_text(encoding='utf-8')
            edited_command = next(line for line in edited_guide.splitlines() if ' verify ' in line)
            self.assertIn('--baseline baseline.png', edited_command)
            self.assertIn('--allow-region 0 0 1 1', edited_command)
            self.assertIn('--mask edit-mask.png', edited_command)
            self.assertIn('--allow-alpha-change', edited_command)
            self.assertIn('--contract contract.json', edited_command)
            self.assertTrue((edited_bundle / 'edit-mask.png').is_file())
            self.assertEqual(json.loads((edited_bundle / 'contract.json').read_bytes()), contract)
            edited_result = verify_from_guide(edited_bundle)
            self.assertEqual(edited_result.returncode, 0, edited_result.stderr)
            edited_details = json.loads(edited_result.stdout)['tiers']['contract']['details']
            self.assertEqual(edited_details['alpha']['alpha_changed_pixels'], 1)
            self.assertTrue(edited_details['boundary']['valid'])
            self.assertEqual(edited_details['declared_contract'], untouched_details['declared_contract'])

    def test_atlas_and_assembly_preserve_names_and_layers_through_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 1. Atlas with single-cell replacement
            atlas_out = root / 'atlas-out'
            atlas_zip = root / 'atlas.zip'
            res_atlas = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver',
                    '--mode', 'atlas',
                    '--source', ROOT / 'examples/workflows/atlas-before.png',
                    '--metadata', ROOT / 'examples/workflows/atlas-before-layout.json',
                    '--replace-cell', 'transfer',
                    '--replacement', ROOT / 'examples/workflows/atlas-replacement.json',
                    '--out-dir', atlas_out,
                    '--pack-zip', atlas_zip,
                ],
            )
            self.assertEqual(res_atlas.returncode, 0, res_atlas.stderr)
            reb_atlas = _run_cli(
                TOOLKIT_CLI,
                ['rebuild', '--input', atlas_zip, '--out-dir', root / 'atlas-rebuilt'],
            )
            self.assertEqual(reb_atlas.returncode, 0, reb_atlas.stderr)
            reb_a_data = json.loads(reb_atlas.stdout)
            self.assertEqual(reb_a_data['preserved_cell_names'], ['add', 'refresh', 'transfer', 'lock'])

            # 2. Assembly preserving layers through ZIP into isolated rebuild
            asm_out = root / 'asm-out'
            asm_zip = root / 'asm.zip'
            res_asm = _run_cli(
                TOOLKIT_CLI,
                [
                    'deliver',
                    '--mode', 'assembly',
                    '--source', ROOT / 'examples/workflows/scene-components.json',
                    '--out-dir', asm_out,
                    '--pack-zip', asm_zip,
                ],
            )
            self.assertEqual(res_asm.returncode, 0, res_asm.stderr)
            reb_asm = _run_cli(
                TOOLKIT_CLI,
                ['rebuild', '--input', asm_zip, '--out-dir', root / 'asm-rebuilt'],
            )
            self.assertEqual(reb_asm.returncode, 0, reb_asm.stderr)
            reb_s_data = json.loads(reb_asm.stdout)
            self.assertTrue(len(reb_s_data['preserved_layer_files']) >= 2)

    def test_three_tier_advisory_does_not_block_multicomponent_ship(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # asymmetric-ship-32.json has 3 valid 8-connected components; must pass without contract
            out_ok = root / 'ship-ok'
            res_ok = _run_cli(
                TOOLKIT_CLI,
                ['deliver', '--source', ROOT / 'examples/asymmetric-ship-32.json', '--out-dir', out_ok],
            )
            self.assertEqual(res_ok.returncode, 0, res_ok.stderr)
            data = json.loads(res_ok.stdout)
            self.assertGreater(data['tiers']['advisory']['components_8conn_count'], 1)

            # With explicit contract max_components=1, verify must fail at contract tier (rc=1)
            strict_contract = root / 'strict.json'
            strict_contract.write_text(json.dumps({'max_components': 1}), encoding='utf-8')
            v_res = _run_cli(
                TOOLKIT_CLI,
                ['verify', '--image', out_ok / 'asset.png', '--contract', strict_contract],
            )
            self.assertEqual(v_res.returncode, 1)
            v_data = json.loads(v_res.stdout)
            self.assertFalse(v_data['tiers']['contract']['passed'])


if __name__ == '__main__':
    unittest.main()
