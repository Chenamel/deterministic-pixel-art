"""Named placement, bounded feedback and portable delivery through the recipe."""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from pixelart import PixelArtError
from pixelart.assembly import assemble, load_project
from pixelart.metadata import encode_png, layout_record, rgba_digest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import tile_scene


def fixture(count=4, cell_size=(3, 2)):
    w, h = cell_size
    image = Image.new('RGBA', (w * count, h))
    # Nonuniform RGBA, including invisible RGB and partial alpha, in every cell.
    image.putdata([((x * 19) % 256, (y * 77) % 256, (x * 11 + y) % 256,
                    (0, 1, 128, 255)[(x + y) % 4]) for y in range(h) for x in range(w * count)])
    names = ['grass', 'path', '转角', ' '][:count]
    names += [f'cell-{i}' for i in range(len(names), count)]
    image.info['pixelart'] = dict(cell_size=[w, h], columns=count, rows=1,
        cells=[dict(name=name, x=i*w, y=0, w=w, h=h) for i, name in enumerate(names)])
    return image, layout_record(image)


def decode(files, name):
    with Image.open(BytesIO(files[name])) as image:
        return image.convert('RGBA')


def report(files):
    return json.loads(files['report.json'])


class TileSceneTests(unittest.TestCase):
    def run_cli(self, directory, image, metadata, layout, output, *options, env=None):
        task_env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PIXELART_PORTABLE_OUTPUT')}
        task_env.update(env or {})
        arguments = [sys.executable, '-B', str(ROOT/'recipes/tile_scene.py'),
                     '--image', str(image), '--layout', str(layout), '--out-dir', str(output)]
        if metadata:
            arguments += ['--metadata', str(metadata)]
        return subprocess.run([*arguments, *options], cwd=directory, env=task_env,
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def inputs(self, root):
        image, metadata = fixture()
        png, sidecar, layout = (root/name for name in ('input.png', 'input.json', 'map.json'))
        png.write_bytes(encode_png(image))
        sidecar.write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
        layout.write_text(json.dumps(dict(version=1, rows=[['grass', 'path'], ['转角', 'grass']])), encoding='utf-8')
        return png, sidecar, layout

    def test_exact_name_placements_preserve_all_rgba_and_inputs(self):
        image, metadata = fixture()
        layout = dict(version=1, rows=[['转角', 'grass', ' '], ['path', '转角', 'grass']])
        original = encode_png(image)
        before = deepcopy((metadata, layout))
        files = tile_scene.make_files(original, layout, metadata)
        self.assertEqual(set(files), set(tile_scene.OUTPUT_NAMES))
        self.assertTrue(all(isinstance(value, bytes) for value in files.values()))
        self.assertEqual(files['atlas.png'], original)
        scene = decode(files, 'scene.png')
        self.assertEqual(scene.size, (9, 4))
        cells = {c['name']: c for c in metadata['atlas']['cells']}
        for y, row in enumerate(layout['rows']):
            for x, name in enumerate(row):
                c = cells[name]
                expected = image.crop((c['x'], 0, c['x']+3, 2))
                self.assertEqual(scene.crop((x*3, y*2, x*3+3, y*2+2)).tobytes(), expected.tobytes())
        self.assertEqual((metadata, layout), before)
        data = report(files)
        self.assertEqual(data['assembly']['rgba_sha256'], rgba_digest(scene))
        self.assertEqual([p['tile'] for p in data['placements']], sum(layout['rows'], []))
        self.assertEqual(data['adjacency_count'], 7)
        self.assertEqual(data['assembly']['uncovered_pixels'], 0)
        for name, digest in data['delivery']['sha256'].items():
            self.assertEqual(hashlib.sha256(files[name]).hexdigest(), digest)

    def test_replacing_one_tile_updates_every_reference_only(self):
        image, metadata = fixture()
        layout = dict(version=1, rows=[['grass', 'path', 'grass'], ['转角', 'grass', ' ']])
        before = decode(tile_scene.make_files(encode_png(image), layout, metadata), 'scene.png')
        changed = image.copy()
        changed.paste((71, 19, 147, 0), (0, 0, 3, 2))
        fresh = deepcopy(metadata)
        fresh['rgba_sha256'] = rgba_digest(changed)
        after = decode(tile_scene.make_files(encode_png(changed), layout, fresh), 'scene.png')
        for y, row in enumerate(layout['rows']):
            for x, name in enumerate(row):
                box = (x*3, y*2, x*3+3, y*2+2)
                if name == 'grass':
                    self.assertEqual(after.crop(box).tobytes(), changed.crop((0, 0, 3, 2)).tobytes())
                    self.assertNotEqual(after.crop(box).tobytes(), before.crop(box).tobytes())
                else:
                    self.assertEqual(after.crop(box).tobytes(), before.crop(box).tobytes())

    def test_all_supported_png_modes_and_embedded_layout(self):
        source, _ = fixture(count=2)
        for mode in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA'):
            with self.subTest(mode=mode):
                image = source.convert(mode)
                image.info['pixelart'] = deepcopy(source.info['pixelart'])
                if mode == 'P':
                    image.info['transparency'] = 0
                # Bind to the actual stored palette/alpha, after PNG round-trip.
                with Image.open(BytesIO(encode_png(image))) as stored:
                    stored.info['pixelart'] = deepcopy(source.info['pixelart'])
                    metadata = layout_record(stored)
                    data = encode_png(stored, metadata)
                with Image.open(BytesIO(data)) as opened:
                    expected = opened.convert('RGBA')
                files = tile_scene.make_files(data, dict(version=1, rows=[['path', 'grass']]))
                self.assertEqual(files['atlas.png'], data)
                self.assertEqual(decode(files, 'scene.png').crop((0, 0, 3, 2)).tobytes(),
                                 expected.crop((3, 0, 6, 2)).tobytes())

    def test_sparse_positions_and_arbitrary_names_are_data_not_paths(self):
        image, metadata = fixture()
        metadata['atlas']['cells'] = [metadata['atlas']['cells'][3], metadata['atlas']['cells'][1]]
        names = ['../长名字 / '+('字'*200), ' \n ']
        for cell, name in zip(metadata['atlas']['cells'], names):
            cell['name'] = name
        files = tile_scene.make_files(encode_png(image), dict(version=1, rows=[names]), metadata)
        data = report(files)
        self.assertEqual([p['tile'] for p in data['placements']], names)
        self.assertEqual(data['placements'][0]['source_rect'], [9, 0, 3, 2])
        self.assertEqual(set(files), set(tile_scene.OUTPUT_NAMES))
        self.assertEqual([p['name'] for p in json.loads(files['project.json'])['parts']], ['tile-0-0', 'tile-1-0'])

    def test_complete_adjacency_mapping_beyond_seam_cap(self):
        image, metadata = fixture(count=1, cell_size=(1, 1))
        files = tile_scene.make_files(encode_png(image), dict(version=1, rows=[['grass']*16 for _ in range(16)]), metadata, scale=1)
        data = report(files)
        self.assertEqual(data['adjacency_count'], 480)
        self.assertEqual(data['assembly']['omitted_seams'], 224)
        self.assertEqual(len(data['assembly']['seam_views']), 32)
        self.assertEqual(data['omitted_adjacency_views'], 448)
        self.assertEqual(sum(len(a['seam_view_indices']) for a in data['adjacencies']), 32)
        positions = {p['id']: p for p in data['placements']}
        seen = set()
        for a in data['adjacencies']:
            left, right = (positions[p] for p in a['placements'])
            self.assertEqual(sum(abs(i-j) for i,j in zip(left['grid'], right['grid'])), 1)
            seen.add(tuple(a['placements']))
            for i in a['seam_view_indices']:
                view = data['assembly']['seam_views'][i]
                self.assertEqual(view['parts'], a['placements'])
                x,y,w,h = a['source_rect']
                vx,vy,vw,vh = view['source_rect']
                self.assertTrue(x <= vx < vx+vw <= x+w and y <= vy < vy+vh <= y+h)
        self.assertEqual(len(seen), 480)

    def test_segment_omissions_and_single_tile_have_precise_counts(self):
        image, metadata = fixture(count=1, cell_size=(1, 1100))
        files = tile_scene.make_files(encode_png(image), dict(version=1, rows=[['grass']*3]), metadata, scale=1)
        self.assertEqual(report(files)['omitted_adjacency_views'], 4)
        one = tile_scene.make_files(encode_png(image), dict(version=1, rows=[['grass']]), metadata, scale=1)
        self.assertEqual(report(one)['adjacencies'], [])
        self.assertEqual(report(one)['omitted_adjacency_views'], 0)

    def test_preview_nearest_and_background_does_not_modify_scene(self):
        image, metadata = fixture(count=2)
        layout = dict(version=1, rows=[['grass', 'path']])
        black = tile_scene.make_files(encode_png(image), layout, metadata, scale=3, background='000000')
        white = tile_scene.make_files(encode_png(image), layout, metadata, scale=3, background='FFFFFF')
        self.assertEqual(black['scene.png'], white['scene.png'])
        self.assertNotEqual(black['preview.png'], white['preview.png'])
        scene, preview = decode(black, 'scene.png'), decode(black, 'preview.png')
        native = Image.alpha_composite(Image.new('RGBA', scene.size, 'black'), scene)
        self.assertEqual(preview.tobytes(), native.resize(preview.size, Image.Resampling.NEAREST).tobytes())

    def test_full_layout_validation_including_unused_last_cell(self):
        image, metadata = fixture()
        layout = dict(version=1, rows=[['grass']])
        for key, value in [('name', 'grass'), ('x', -1), ('x', 0), ('w', 2), ('h', 3)]:
            with self.subTest(key=key, value=value):
                bad = deepcopy(metadata)
                bad['atlas']['cells'][-1][key] = value
                with self.assertRaises(PixelArtError), patch.object(tile_scene, 'assemble') as assembly:
                    tile_scene.make_files(encode_png(image), layout, bad)
                assembly.assert_not_called()

    def test_binding_missing_stale_legacy_and_conflicting_layouts_fail(self):
        image, metadata = fixture()
        data = encode_png(image)
        layout = dict(version=1, rows=[['grass']])
        stale = deepcopy(metadata); stale['rgba_sha256'] = '0'*64
        legacy = deepcopy(metadata); del legacy['rgba_sha256']
        unbound = deepcopy(metadata); unbound['atlas'] = None
        for bad in (None, stale, legacy, unbound, [], True, 1, 'bad'):
            with self.subTest(bad=bad), self.assertRaises(PixelArtError):
                tile_scene.make_files(data, layout, bad)
        conflict = deepcopy(metadata)
        conflict['atlas']['cells'][-1]['name'] = 'other'
        with self.assertRaisesRegex(PixelArtError, 'conflict'):
            tile_scene.make_files(encode_png(image, metadata), layout, conflict)

    def test_atlas_cell_limit_is_separate_from_placement_limit(self):
        for count in (257, 4096):
            image, metadata = fixture(count=count, cell_size=(1, 1))
            size, placements, _, _ = tile_scene._plan(image, metadata, dict(version=1, rows=[[f'cell-{count-1}']]), 1)
            self.assertEqual(size, (1, 1))
            self.assertEqual(placements[0]['source_rect'], [count-1, 0, 1, 1])
        image, metadata = fixture(count=4097, cell_size=(1, 1))
        with self.assertRaisesRegex(PixelArtError, '4096'):
            tile_scene._plan(image, metadata, dict(version=1, rows=[['grass']]), 1)

    def test_layout_and_scale_errors_precede_assembly(self):
        image, metadata = fixture()
        bad_layouts = [None, [], {}, dict(version=True, rows=[['grass']]), dict(version=2, rows=[['grass']]),
                      dict(version=1, rows=[]), dict(version=1, rows=[[]]), dict(version=1, rows='grass'),
                      dict(version=1, rows=[['grass'], []]), dict(version=1, rows=[['grass'], 'path']),
                      dict(version=1, rows=[['']]), dict(version=1, rows=[[True]]),
                      dict(version=1, rows=[['unknown']]), dict(version=1, rows=[['grass']*257]),
                      dict(version=1, rows=[['grass']], digest='ignored')]
        for layout in bad_layouts:
            with self.subTest(layout=layout), patch.object(tile_scene, 'assemble') as assembly:
                with self.assertRaises(PixelArtError):
                    tile_scene.make_files(encode_png(image), layout, metadata)
                assembly.assert_not_called()
        for scale in (0, -1, True, 1.5):
            with self.assertRaises(PixelArtError):
                tile_scene.make_files(encode_png(image), dict(version=1, rows=[['grass']]), metadata, scale)

    def test_budgets_before_allocation_and_encoding_before_publication(self):
        for cell_size, names, scale, message in [((4096, 1), ['grass']*3, 1, 'scene'),
                ((700, 1), ['grass']*3, 4, '--scale 3'), ((400, 400), ['grass']*8, 4, '--scale 2')]:
            image, metadata = fixture(count=1, cell_size=cell_size)
            with patch.object(tile_scene, 'assemble') as assembly, self.assertRaisesRegex(PixelArtError, message):
                tile_scene.make_files(encode_png(image), dict(version=1, rows=[names]), metadata, scale)
            assembly.assert_not_called()
        image, metadata = fixture()
        for constant in ('MAX_PNG_BYTES', 'MAX_JSON_BYTES', 'MAX_OUTPUT_BYTES'):
            with patch.object(tile_scene, constant, 1), self.assertRaises(PixelArtError):
                tile_scene.make_files(encode_png(image), dict(version=1, rows=[['grass']]), metadata)

    def test_rejects_unsupported_png_inputs(self):
        gif = BytesIO(); Image.new('RGB', (1, 1)).save(gif, format='GIF')
        animated = BytesIO()
        Image.new('RGBA', (2, 2), 'red').save(animated, format='PNG', save_all=True,
            append_images=[Image.new('RGBA', (2, 2), 'blue')], duration=100, loop=0)
        for data in (b'', gif.getvalue(), encode_png(Image.new('I;16', (2, 2))), animated.getvalue(),
                     encode_png(Image.new('RGBA', (8193, 1)))):
            with self.assertRaises(PixelArtError):
                tile_scene.make_files(data, dict(version=1, rows=[['grass']]))

    def test_cli_migration_reassembly_and_name_based_regeneration(self):
        with tempfile.TemporaryDirectory(prefix='命名 地块 ') as directory:
            root = Path(directory)
            png, metadata, layout = self.inputs(root)
            result = self.run_cli(root, png, metadata, layout, root/'v1')
            self.assertEqual(result.returncode, 0, result.stderr)
            moved = root/'移动 空格'/'工程'
            shutil.move(str(root/'v1'), moved)
            for p in (png, metadata, layout): p.unlink()
            project, sources, _ = load_project(moved/'project.json')
            reassembled, _ = assemble(project, sources)
            with Image.open(moved/'scene.png') as expected:
                self.assertEqual(reassembled.tobytes(), expected.tobytes())
            result = self.run_cli(root, moved/'atlas.png', moved/'atlas-layout.json', moved/'layout.json', root/'v2')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root/'v2/scene.png').read_bytes(), (moved/'scene.png').read_bytes())

    def test_cli_refuses_existing_directory_force_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png, metadata, layout = self.inputs(root)
            before = {p: p.read_bytes() for p in (png, metadata, layout)}
            existing = root/'old'; existing.mkdir(); (existing/'keep.txt').write_text('keep')
            for output, options in [(existing, ()), (root/'force', ('--force',)),
                                    (root/'bad-color', ('--background', 'invalid'))]:
                result = self.run_cli(root, png, metadata, layout, output, *options)
                self.assertEqual(result.returncode, 2, result.stderr)
                if output != existing: self.assertFalse(output.exists())
            self.assertEqual((existing/'keep.txt').read_text(), 'keep')
            for content in ('{"version":1,"version":1,"rows":[["grass"]]}',
                            '{"version":1,"rows":[["missing"]]}', ' '* (tile_scene.MAX_JSON_BYTES + 1)):
                layout.write_text(content, encoding='utf-8')
                result = self.run_cli(root, png, metadata, layout, root/'invalid')
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse((root/'invalid').exists())
            self.assertEqual(png.read_bytes(), before[png])
            self.assertEqual(metadata.read_bytes(), before[metadata])

    def test_portable_flags_override_invalid_environment_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png, metadata, layout = self.inputs(root)
            env = dict(PIXELART_PORTABLE_OUTPUT='invalid')
            result = self.run_cli(root, png, metadata, layout, root/'invalid', env=env)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse((root/'invalid').exists())
            for flag in ('--portable-output', '--no-portable-output'):
                result = self.run_cli(root, png, metadata, layout, root/flag[2:], flag, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_publication_failure_does_not_delete_other_writers_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png, metadata, layout = self.inputs(root)
            def fail(files, **kwargs):
                (root/'output/other.txt').write_text('another writer')
                raise OSError('injected publication failure')
            arguments = ['tile_scene.py', '--image', str(png), '--metadata', str(metadata),
                         '--layout', str(layout), '--out-dir', str(root/'output')]
            with patch.object(sys, 'argv', arguments), patch.object(tile_scene, 'publish', side_effect=fail):
                with self.assertRaisesRegex(PixelArtError, 'incomplete directory retained'):
                    tile_scene.main()
            self.assertEqual((root/'output/other.txt').read_text(), 'another writer')
            self.assertTrue(all(p.exists() for p in (png, metadata, layout)))
