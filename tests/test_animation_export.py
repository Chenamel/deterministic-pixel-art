"""Animation contracts exercised through real PNG/GIF bytes and the recipe CLI."""

from copy import deepcopy
import errno
import hashlib
from io import BytesIO
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import animation_export as animation
import _animation_gif as gif
import _animation_project as project_rules
from pixelart import PixelArtError
from pixelart.metadata import encode_png


def manifest(paths, durations=None, actions=None, config=None):
    data = dict(
        version=1,
        kind='png-animation',
        frames=[
            dict(image=path, duration_ms=duration)
            for path, duration in zip(paths, durations or [40] * len(paths))
        ],
        actions=actions or [dict(name='idle', range=[0, len(paths)])],
    )
    if config is not None:
        data['gif'] = config
    return data


def gif_frames(data):
    frames, durations = [], []
    with Image.open(BytesIO(data)) as image:
        loop = image.info['loop']
        for index in range(image.n_frames):
            image.seek(index)
            frames.append(image.convert('RGBA'))
            durations.append(image.info['duration'])
    return frames, durations, loop


class AnimationExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='动画 contract ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inputs = self.root / '原图 inputs'
        self.inputs.mkdir()
        self.cwd = self.root / '无关 cwd'
        self.cwd.mkdir()
        self.output = self.root / 'new export'
        self.project = self.inputs / 'animation.json'
        self.data = manifest(['a.png', 'b.png', 'c.png', 'd.png'], [45, 75, 115, 155])
        self.images = []
        for i, name in enumerate(('a.png', 'b.png', 'c.png', 'd.png')):
            image = Image.new('RGBA', (3, 2))
            image.putdata(
                [
                    (80 + i * 30, 20 + x * 20, 70 + x, a)
                    for x, a in enumerate((0, 1, 127, 128, 254, 255))
                ]
            )
            image.save(self.inputs / name)
            self.images.append(image)
        self.write()

    def write(self, data=None):
        self.project.write_text(
            json.dumps(self.data if data is None else data), encoding='utf-8'
        )

    def files(self, data=None):
        return animation.make_files(self.data if data is None else data, self.inputs)[0]

    def cli(self, *options, output=None, env=None):
        process_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ('PYTHONPATH', 'PYTHONHOME', 'PIXELART_PORTABLE_OUTPUT')
        }
        process_env.update(env or {})
        return subprocess.run(
            [
                sys.executable,
                '-B',
                str(ROOT / 'recipes/animation_export.py'),
                '--project',
                str(self.project),
                '--out-dir',
                str(output or self.output),
                *options,
            ],
            cwd=self.cwd,
            env=process_env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30,
        )

    def reject(self, data, message=None):
        with self.assertRaisesRegex(PixelArtError, message or '.'):
            self.files(data)
        self.assertFalse(self.output.exists())

    def test_exact_png_bytes_hidden_rgb_and_delivery_hashes(self):
        original = deepcopy(self.data)
        source_bytes = [
            (self.inputs / frame['image']).read_bytes() for frame in self.data['frames']
        ]
        files = self.files()
        report = json.loads(files['report.json'])
        normalized = json.loads(files['animation.json'])
        self.assertEqual(self.data, original)
        self.assertEqual(set(files), set(report['delivery']['files']))
        self.assertNotIn('report.json', report['delivery']['sha256'])
        for i, data in enumerate(source_bytes):
            self.assertEqual(files[f'source-{i:04d}.png'], data)
            with Image.open(BytesIO(files[f'source-{i:04d}.png'])) as image:
                self.assertEqual(image.size, (3, 2))
                self.assertEqual(
                    image.convert('RGBA').tobytes(), self.images[i].tobytes()
                )
                self.assertEqual(
                    image.convert('RGBA').getpixel((0, 0)), (80 + i * 30, 20, 70, 0)
                )
            self.assertEqual(
                normalized['frames'][i]['duration_ms'], (45, 75, 115, 155)[i]
            )
        self.assertEqual(normalized['actions'][0]['direction'], 'forward')
        for name, digest in report['delivery']['sha256'].items():
            self.assertEqual(hashlib.sha256(files[name]).hexdigest(), digest)
        self.assertNotIn(str(self.inputs), files['report.json'].decode())

    def test_png_modes_palette_transparency_and_low_bit_depth(self):
        for mode in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA'):
            with self.subTest(mode=mode):
                image = self.images[0].convert(mode)
                if mode == 'P':
                    image.info['transparency'] = bytes([0, 1, 127, 128, 254, 255])
                source = encode_png(image)
                (self.inputs / 'mode.png').write_bytes(source)
                files = self.files(manifest(['mode.png']))
                self.assertEqual(files['source-0000.png'], source)
                with (
                    Image.open(BytesIO(source)) as before,
                    Image.open(BytesIO(files['source-0000.png'])) as after,
                ):
                    self.assertEqual(
                        before.convert('RGBA').tobytes(),
                        after.convert('RGBA').tobytes(),
                    )

    def test_directions_keep_each_source_duration_and_allow_overlapping_actions(self):
        self.data['actions'] = [
            dict(name='CON / 转身', range=[0, 4], direction='reverse'),
            dict(name='walk', range=[1, 4], direction='pingpong'),
            dict(name='single', range=[2, 3], direction='pingpong'),
            dict(name='pair', range=[0, 2], direction='pingpong'),
        ]
        actions = json.loads(self.files()['report.json'])['actions']
        for record, indices, durations in zip(
            actions,
            ([3, 2, 1, 0], [1, 2, 3, 2], [2], [0, 1]),
            ([155, 115, 75, 45], [75, 115, 155, 115], [115], [45, 75]),
        ):
            self.assertEqual(record['source_indices'], indices)
            self.assertEqual(record['durations_ms'], durations)
        self.assertEqual(
            [a['name'] for a in actions], ['CON / 转身', 'walk', 'single', 'pair']
        )

    def test_duplicate_paths_read_once_and_preserve_entries(self):
        repeated = manifest(['a.png', 'a.png', 'b.png'], [40, 50, 60])
        actual_read = project_rules.read_bounded
        calls = []

        def counted(path, *args):
            calls.append(path)
            return actual_read(path, *args)

        with patch.object(project_rules, 'read_bounded', side_effect=counted):
            files = self.files(repeated)
        self.assertEqual(len(calls), 2)
        self.assertEqual(files['source-0000.png'], files['source-0001.png'])
        self.assertEqual(
            json.loads(files['report.json'])['actions'][0]['durations_ms'], [40, 50, 60]
        )

    def test_binary_threshold_same_rgb_transparency_and_rounding(self):
        data = deepcopy(self.data)
        data['frames'] = data['frames'][:3]
        data['actions'] = [dict(name='idle', range=[0, 3])]
        data['gif'] = dict(mode='binary', loop=2)
        files = self.files(data)
        frames, durations, loop = gif_frames(files['action-0000.gif'])
        self.assertEqual(durations, [40, 70, 110])
        self.assertEqual(loop, 2)
        for i, frame in enumerate(frames):
            self.assertEqual(
                list(frame.getchannel('A').tobytes()), [0, 0, 0, 255, 255, 255]
            )
            self.assertEqual(frame.getpixel((0, 1)), (80 + i * 30, 80, 73, 255))
        record = json.loads(files['report.json'])['actions'][0]['gif']
        self.assertEqual(record['lost_duration_ms'], 15)
        self.assertEqual(
            [e['duration_ms'] for e in record['logical_entries']], [45, 75, 115]
        )
        self.assertEqual(record['palette']['quantizer'], 'exact')
        image = Image.new('RGBA', (2, 1))
        image.putdata([(12, 34, 56, 0), (12, 34, 56, 255)])
        image.save(self.inputs / 'twins.png')
        result = self.files(manifest(['twins.png'], config=dict(mode='binary')))
        frame = gif_frames(result['action-0000.gif'])[0][0]
        self.assertEqual(frame.getpixel((1, 0)), (12, 34, 56, 255))
        self.assertEqual(frame.getpixel((0, 0))[3], 0)
        maximum_loop = self.files(
            manifest(['twins.png'], config=dict(mode='binary', loop=65_535))
        )
        self.assertEqual(gif_frames(maximum_loop['action-0000.gif'])[2], 65_535)

    def test_background_source_over_is_explicit_and_opaque(self):
        image = Image.new('RGBA', (3, 1))
        image.putdata([(200, 100, 50, 0), (200, 100, 50, 128), (200, 100, 50, 255)])
        image.save(self.inputs / 'edge.png')
        files = self.files(
            manifest(['edge.png'], config=dict(mode='background', background='14283c'))
        )
        frame = gif_frames(files['action-0000.gif'])[0][0]
        self.assertEqual(
            frame.tobytes(),
            bytes((20, 40, 60, 255, 110, 70, 55, 255, 200, 100, 50, 255)),
        )
        self.assertEqual(
            json.loads(files['animation.json'])['gif'],
            dict(mode='background', background='14283C', loop=0),
        )

    def test_all_transparent_and_clear_after_opaque(self):
        Image.new('RGBA', (3, 2), (1, 2, 3, 0)).save(self.inputs / 'clear.png')
        Image.new('RGBA', (3, 2), 'red').save(self.inputs / 'red.png')
        data = manifest(
            ['red.png', 'clear.png', 'red.png'],
            [10, 20, 30],
            config=dict(mode='binary'),
        )
        frames, durations, _ = gif_frames(self.files(data)['action-0000.gif'])
        self.assertEqual(durations, [10, 20, 30])
        self.assertEqual(set(frames[0].getchannel('A').tobytes()), {255})
        self.assertEqual(set(frames[1].getchannel('A').tobytes()), {0})
        self.assertEqual(frames[0].tobytes(), frames[2].tobytes())
        transparent = self.files(
            manifest(['clear.png', 'clear.png'], [45, 75], config=dict(mode='binary'))
        )
        frames, durations, _ = gif_frames(transparent['action-0000.gif'])
        self.assertEqual(durations, [110])
        self.assertEqual(set(frames[0].getchannel('A').tobytes()), {0})
        self.assertEqual(
            json.loads(transparent['report.json'])['actions'][0]['gif']['palette'][
                'opaque_colors'
            ],
            0,
        )

    def test_adjacent_equal_pixels_different_pngs_merge_after_rounding(self):
        self.images[0].save(self.inputs / 'same.png', compress_level=0)
        self.assertNotEqual(
            (self.inputs / 'a.png').read_bytes(),
            (self.inputs / 'same.png').read_bytes(),
        )
        data = manifest(
            ['a.png', 'same.png', 'b.png', 'a.png'],
            [45, 75, 115, 10],
            config=dict(mode='binary'),
        )
        files = self.files(data)
        frames, durations, _ = gif_frames(files['action-0000.gif'])
        self.assertEqual(durations, [110, 110, 10])
        self.assertEqual(frames[0].tobytes(), frames[2].tobytes())
        record = json.loads(files['report.json'])['actions'][0]['gif']
        self.assertEqual(record['segments'][0]['logical_entries'], [0, 1])
        self.assertEqual(
            [e['segment'] for e in record['logical_entries']], [0, 0, 1, 2]
        )

    def test_palette_capacity_exact_and_mediancut_without_dither(self):
        for count, mode, quantized in (
            (255, 'binary', False),
            (256, 'background', False),
            (256, 'binary', True),
            (257, 'background', True),
        ):
            with self.subTest(count=count, mode=mode):
                image = Image.new('RGBA', (count, 1))
                image.putdata(
                    [(i % 256, i // 256, (i * 29) % 256, 255) for i in range(count)]
                )
                image.save(self.inputs / 'colors.png')
                config = dict(mode=mode)
                if mode == 'background':
                    config['background'] = '14283C'
                files = self.files(manifest(['colors.png'], config=config))
                frame = gif_frames(files['action-0000.gif'])[0][0]
                record = json.loads(files['report.json'])['actions'][0]['gif'][
                    'palette'
                ]
                self.assertEqual(record['quantized'], quantized)
                self.assertEqual(record['dither'], 'NONE')
                self.assertLessEqual(
                    len(frame.getcolors()), 255 if mode == 'binary' else 256
                )
                if not quantized:
                    self.assertEqual(frame.tobytes(), image.tobytes())
                else:
                    self.assertNotEqual(frame.tobytes(), image.tobytes())

    def test_quantized_identical_frames_are_one_visible_run(self):
        image = Image.new('RGBA', (257, 1))
        image.putdata([(i % 256, i // 256, (i * 17) % 256, 255) for i in range(257)])
        image.save(self.inputs / 'colors.png')
        files = self.files(
            manifest(['colors.png', 'colors.png'], [45, 75], config=dict(mode='binary'))
        )
        self.assertEqual(gif_frames(files['action-0000.gif'])[1], [110])
        record = json.loads(files['report.json'])['actions'][0]['gif']
        self.assertTrue(record['palette']['quantized'])
        self.assertEqual(record['segments'][0]['logical_entries'], [0, 1])

    def test_sub_10ms_allowed_only_without_selected_gif(self):
        data = manifest(['a.png', 'b.png'], [1, 9])
        self.assertEqual(
            json.loads(self.files(data)['animation.json'])['frames'][1]['duration_ms'],
            9,
        )
        data['gif'] = dict(mode='binary')
        self.reject(data, 'at least 10ms')
        data['frames'].append(dict(image='c.png', duration_ms=10))
        data['actions'] = [dict(name='ten', range=[2, 3])]
        self.assertEqual(gif_frames(self.files(data)['action-0000.gif'])[1], [10])

    def test_strict_types_unknown_fields_and_ranges(self):
        mutations = [
            ('version', True),
            ('kind', 'draw'),
            ('frames', []),
            ('actions', []),
            ('extra', 1),
            ('gif', False),
            ('gif', True),
            ('gif', None),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                data = deepcopy(self.data)
                data[key] = value
                self.reject(data)
        for value in (True, 40.0, '40', 0, -1, 60_001):
            with self.subTest(duration=value):
                data = deepcopy(self.data)
                data['frames'][0]['duration_ms'] = value
                self.reject(data)
        for bounds in (
            [True, 2],
            [0, False],
            [0.0, 2],
            [-1, 2],
            [2, 2],
            [0, 5],
            [3, 1],
            [0],
            None,
        ):
            with self.subTest(bounds=bounds):
                data = deepcopy(self.data)
                data['actions'][0]['range'] = bounds
                self.reject(data)
        for config in (
            dict(mode='binary', loop=True),
            dict(mode='binary', loop=-1),
            dict(mode='binary', loop=65_536),
            dict(mode='binary', background='000000'),
            dict(mode='background'),
            dict(mode='background', background='00000000'),
            dict(mode='binary', extra=0),
            dict(mode='other'),
        ):
            with self.subTest(config=config):
                data = deepcopy(self.data)
                data['gif'] = config
                self.reject(data)
        for collection in ('frames', 'actions'):
            data = deepcopy(self.data)
            data[collection][0]['extra'] = True
            self.reject(data)
        for value in ('', 'x' * 129, 'bad\nname', '\ud800'):
            data = deepcopy(self.data)
            data['actions'][0]['name'] = value
            self.reject(data)
        data = deepcopy(self.data)
        data['actions'].append(deepcopy(data['actions'][0]))
        self.reject(data, 'duplicate')
        data = deepcopy(self.data)
        data['actions'][0]['direction'] = 'backwards'
        self.reject(data)

    def test_resource_paths_and_nonordinary_files(self):
        for value in (
            '/a.png',
            'C:/a.png',
            '//host/share.png',
            'dir\\a.png',
            '../a.png',
            'dir/../a.png',
            './a.png',
            'dir//a.png',
            'a.png/',
            'a\n.png',
            '\ud800',
            '',
            'x' * 1025,
            True,
        ):
            with self.subTest(path=value):
                data = manifest([value])
                self.reject(data)
        for value in ('missing.png', 'directory'):
            (self.inputs / 'directory').mkdir(exist_ok=True)
            with self.assertRaises((OSError, ValueError)):
                self.files(manifest([value]))
        nested = self.inputs / '子目录 space'
        nested.mkdir()
        shutil.copyfile(self.inputs / 'a.png', nested / 'frame.png')
        self.assertEqual(
            self.files(manifest(['子目录 space/frame.png']))['source-0000.png'],
            (nested / 'frame.png').read_bytes(),
        )

    def test_external_symlink_is_rejected_and_internal_link_copies_bytes(self):
        outside = self.root / 'outside.png'
        shutil.copyfile(self.inputs / 'a.png', outside)
        try:
            (self.inputs / 'external.png').symlink_to(outside)
            (self.inputs / 'internal.png').symlink_to(self.inputs / 'a.png')
        except OSError as error:
            self.skipTest(f'host cannot create symlinks: {error}')
        self.reject(manifest(['external.png']), 'inside project')
        self.assertEqual(
            self.files(manifest(['internal.png']))['source-0000.png'],
            outside.read_bytes(),
        )

    def test_png_rejects_bad_formats_multiframe_and_wrong_size(self):
        (self.inputs / 'bad.png').write_bytes(b'not a PNG')
        self.images[0].convert('RGB').save(self.inputs / 'jpeg.png', format='JPEG')
        Image.new('I;16', (3, 2)).save(self.inputs / 'sixteen.png')
        Image.new('RGBA', (2, 2)).save(self.inputs / 'small.png')
        self.images[0].save(
            self.inputs / 'animated.png',
            save_all=True,
            append_images=[self.images[1]],
            duration=40,
        )
        (self.inputs / 'truncated.png').write_bytes(
            (self.inputs / 'a.png').read_bytes()[:-12]
        )
        for name in (
            'bad.png',
            'jpeg.png',
            'sixteen.png',
            'animated.png',
            'truncated.png',
        ):
            with self.subTest(name=name), self.assertRaises((OSError, ValueError)):
                self.files(manifest([name]))
        self.reject(manifest(['a.png', 'small.png']), 'native size')

    @unittest.skipUnless(os.name == 'nt', 'Windows junction contract')
    def test_windows_junction_containment_and_dangling_output(self):
        outside = self.root / 'outside directory'
        outside.mkdir()
        shutil.copyfile(self.inputs / 'a.png', outside / 'a.png')
        link = self.inputs / 'outside junction'
        dangling = self.root / 'dangling junction'
        for source, target in ((link, outside), (dangling, self.root / 'absent')):
            result = subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(source), str(target)],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.addCleanup(source.rmdir)
        self.reject(manifest(['outside junction/a.png']), 'inside project')
        result = self.cli(output=dangling)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('already exists', json.loads(result.stderr)['error'])
        self.assertFalse((self.root / 'absent').exists())

    def test_structural_limits_and_temporal_limits(self):
        valid = manifest(['a.png'] * 128, [1] * 128)
        self.assertEqual(len(project_rules.plan(valid)[0]['frames']), 128)
        self.reject(manifest(['a.png'] * 129, [1] * 129), '129, limit 128')
        valid['actions'] = [dict(name=str(i), range=[0, 1]) for i in range(16)]
        self.assertEqual(len(project_rules.plan(valid)[0]['actions']), 16)
        valid['actions'].append(dict(name='extra', range=[0, 1]))
        self.reject(valid, '17, limit 16')
        valid = manifest(['a.png', 'b.png'], [60_000, 60_000])
        self.assertEqual(
            json.loads(self.files(valid)['report.json'])['actions'][0]['duration_ms'],
            120_000,
        )
        self.reject(manifest(['a.png'] * 3, [60_000, 60_000, 1]), '120001')
        expanded = manifest(['a.png'] * 128, [1] * 128)
        expanded['actions'] = [dict(name=str(i), range=[0, 128]) for i in range(8)]
        self.assertEqual(sum(map(len, project_rules.plan(expanded)[1])), 1024)
        expanded['actions'].append(dict(name='over', range=[0, 1]))
        self.reject(expanded, '1025')
        with patch.object(project_rules, 'MAX_ACTION_ENTRIES', 3):
            self.reject(self.data, 'expanded entries')
        with patch.object(project_rules, 'MAX_ACTION_ENTRIES', 4):
            self.assertEqual(len(project_rules.plan(self.data)[1][0]), 4)

    def test_source_and_gif_budgets_count_repeated_entries_before_decode(self):
        source = (self.inputs / 'a.png').read_bytes()
        data = manifest(['a.png', 'a.png'])
        checks = (
            ('MAX_PNG_BYTES', len(source), len(source) - 1),
            ('MAX_SOURCE_BYTES', len(source) * 2, len(source) * 2 - 1),
            ('MAX_SOURCE_PIXELS', 12, 11),
        )
        for constant, boundary, exceeded in checks:
            with self.subTest(constant=constant):
                with patch.object(project_rules, constant, boundary):
                    self.assertIn('source-0001.png', self.files(data))
                with (
                    patch.object(project_rules, constant, exceeded),
                    patch.object(
                        project_rules.Image,
                        'open',
                        side_effect=AssertionError('must reject before decode'),
                    ),
                ):
                    self.reject(data, 'limit')
        data['gif'] = dict(mode='binary')
        with patch.object(project_rules, 'MAX_GIF_PIXELS', 12):
            self.assertIn('action-0000.gif', self.files(data))
        with (
            patch.object(project_rules, 'MAX_GIF_PIXELS', 11),
            patch.object(
                project_rules.Image,
                'open',
                side_effect=AssertionError('must reject before decode'),
            ),
        ):
            self.reject(data, 'GIF pixels')
        files = self.files()
        total = sum(map(len, files.values()))
        with patch.object(animation, 'MAX_DELIVERY_BYTES', total):
            self.assertEqual(self.files(), files)
        with patch.object(animation, 'MAX_DELIVERY_BYTES', total - 1):
            self.reject(self.data, 'delivery bytes')

    def test_native_png_side_and_pixel_header_limits(self):
        image = Image.new('1', (1024, 1024))
        image.save(self.inputs / 'edge.png')
        self.assertEqual(
            json.loads(self.files(manifest(['edge.png']))['report.json'])['sources'][0][
                'size'
            ],
            [1024, 1024],
        )
        Image.new('1', (1025, 1)).save(self.inputs / 'over.png')
        self.reject(manifest(['over.png']), 'side')
        with (
            patch.object(project_rules, 'MAX_FRAME_PIXELS', 5),
            patch.object(
                project_rules.Image,
                'open',
                side_effect=AssertionError('must reject before decode'),
            ),
        ):
            self.reject(manifest(['a.png']), 'pixels')

    def test_json_bom_duplicates_and_one_mib_read_limit(self):
        self.project.write_text(json.dumps(self.data), encoding='utf-8-sig')
        self.assertEqual(self.cli().returncode, 0)
        raw = json.dumps(self.data).encode()
        self.project.write_bytes(raw + b' ' * (project_rules.MAX_JSON_BYTES - len(raw)))
        result = self.cli(output=self.root / 'boundary')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.project.write_bytes(self.project.read_bytes() + b' ')
        result = self.cli(output=self.root / 'oversize')
        self.assertEqual(result.returncode, 2)
        self.assertIn('project JSON bytes', json.loads(result.stderr)['error'])
        self.assertFalse((self.root / 'oversize').exists())
        self.project.write_text('{"version":1,"version":1}', encoding='utf-8')
        result = self.cli(output=self.root / 'duplicate')
        self.assertEqual(result.returncode, 2)
        self.assertIn('duplicate JSON key', json.loads(result.stderr)['error'])
        self.assertFalse((self.root / 'duplicate').exists())

    def test_cli_errors_are_json_and_leave_no_directory(self):
        for duration in (True, 40.0, 0, 60_001):
            data = deepcopy(self.data)
            data['frames'][0]['duration_ms'] = duration
            self.write(data)
            result = self.cli()
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('error', json.loads(result.stderr))
            self.assertFalse(self.output.exists())

    def test_output_conflicts_force_and_dangling_link(self):
        self.output.mkdir()
        self.assertEqual(self.cli().returncode, 2)
        marker = self.output / 'keep'
        marker.write_bytes(b'old')
        self.assertEqual(self.cli('--force').returncode, 2)
        self.assertEqual(marker.read_bytes(), b'old')
        self.assertEqual(sorted(p.name for p in self.output.iterdir()), ['keep'])
        link = self.root / 'dangling'
        try:
            link.symlink_to(self.root / 'absent', target_is_directory=True)
        except OSError as error:
            self.skipTest(f'host cannot create symlinks: {error}')
        self.assertEqual(self.cli(output=link).returncode, 2)
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.root / 'absent').exists())

    def test_two_cli_writers_only_one_gets_directory(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ('PYTHONPATH', 'PYTHONHOME', 'PIXELART_PORTABLE_OUTPUT')
        }
        command = [
            sys.executable,
            '-B',
            str(ROOT / 'recipes/animation_export.py'),
            '--project',
            str(self.project),
            '--out-dir',
            str(self.output),
        ]
        processes = [
            subprocess.Popen(
                command,
                cwd=self.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for _ in range(2)
        ]
        outcomes = [(p.communicate(timeout=30), p.returncode) for p in processes]
        self.assertEqual(sorted(code for _, code in outcomes), [0, 2])
        self.assertEqual(set(p.name for p in self.output.iterdir()), set(self.files()))

    def test_portable_environment_and_explicit_override(self):
        result = self.cli(env={'PIXELART_PORTABLE_OUTPUT': 'invalid'})
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.output.exists())
        self.assertEqual(
            self.cli(
                '--portable-output', env={'PIXELART_PORTABLE_OUTPUT': 'invalid'}
            ).returncode,
            0,
        )
        self.assertEqual(
            self.cli(
                '--no-portable-output',
                output=self.root / 'hard',
                env={'PIXELART_PORTABLE_OUTPUT': '1'},
            ).returncode,
            0,
        )

    def test_hard_link_failure_and_mid_publish_rollback(self):
        before = (self.inputs / 'a.png').read_bytes()
        with patch(
            'pixelart.output.os.link',
            side_effect=OSError(errno.EPERM, 'injected hard-link refusal'),
        ):
            with self.assertRaisesRegex(PixelArtError, 'portable-output'):
                animation.export(self.project, self.output)
        self.assertFalse(self.output.exists())
        real_link = os.link
        calls = 0

        def fail_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected publication failure')
            return real_link(source, target)

        with patch('pixelart.output.os.link', side_effect=fail_second):
            with self.assertRaisesRegex(PixelArtError, 'publication failure'):
                animation.export(self.project, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual((self.inputs / 'a.png').read_bytes(), before)

    def test_rollback_failure_retains_owned_file_and_external_additions(self):
        real_link, real_unlink = os.link, Path.unlink
        calls = 0

        def fail_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected publication failure')
            return real_link(source, target)

        def fail_owned_unlink(path, *args, **kwargs):
            if path == self.output / 'source-0000.png':
                raise OSError('injected rollback refusal')
            return real_unlink(path, *args, **kwargs)

        with (
            patch('pixelart.output.os.link', side_effect=fail_second),
            patch.object(Path, 'unlink', fail_owned_unlink),
        ):
            with self.assertRaisesRegex(
                PixelArtError, 'incomplete directory retained'
            ) as caught:
                animation.export(self.project, self.output)
        self.assertIn('rollback refusal', str(caught.exception))
        self.assertEqual(
            (self.output / 'source-0000.png').read_bytes(),
            (self.inputs / 'a.png').read_bytes(),
        )
        fresh = self.root / 'external writer'

        def external_write(*args, **kwargs):
            (fresh / 'other.txt').write_bytes(b'external')
            raise OSError('injected ordinary failure')

        with patch.object(animation, 'publish', side_effect=external_write):
            with self.assertRaisesRegex(PixelArtError, 'incomplete directory retained'):
                animation.export(self.project, fresh)
        self.assertEqual((fresh / 'other.txt').read_bytes(), b'external')
        empty = self.root / 'cleanup refused'
        real_rmdir = Path.rmdir

        def refuse_cleanup(path, *args, **kwargs):
            if path == empty:
                raise OSError('injected directory cleanup refusal')
            return real_rmdir(path, *args, **kwargs)

        with (
            patch.object(animation, 'publish', side_effect=OSError('write failed')),
            patch.object(Path, 'rmdir', refuse_cleanup),
        ):
            with self.assertRaisesRegex(PixelArtError, 'incomplete directory retained'):
                animation.export(self.project, empty)
        self.assertTrue(empty.is_dir())
        self.assertEqual(list(empty.iterdir()), [])

    def test_directory_race_loser_never_cleans_winner(self):
        real_mkdir = Path.mkdir

        def raced(path, *args, **kwargs):
            if path == self.output:
                real_mkdir(path, *args, **kwargs)
                (path / 'winner.txt').write_bytes(b'winner')
                raise FileExistsError('injected directory race')
            return real_mkdir(path, *args, **kwargs)

        with patch.object(Path, 'mkdir', raced):
            with self.assertRaises(FileExistsError):
                animation.export(self.project, self.output)
        self.assertEqual((self.output / 'winner.txt').read_bytes(), b'winner')

    def test_gif_encode_or_readback_failure_precedes_mkdir(self):
        self.data['gif'] = dict(mode='binary')
        self.write()
        with patch.object(
            gif, 'readback', side_effect=PixelArtError('injected readback failure')
        ):
            with self.assertRaisesRegex(PixelArtError, 'readback failure'):
                animation.export(self.project, self.output)
        self.assertFalse(self.output.exists())
        with patch.object(gif, 'readback', return_value=([], [], [])):
            with self.assertRaisesRegex(PixelArtError, 'visible timeline differs'):
                animation.export(self.project, self.output)
        self.assertFalse(self.output.exists())
        with patch.object(
            Image.Image, 'save', side_effect=OSError('injected GIF encoding failure')
        ):
            with self.assertRaisesRegex(PixelArtError, 'GIF encoding failed'):
                animation.export(self.project, self.output)
        self.assertFalse(self.output.exists())

    def test_actual_move_regeneration_has_identical_all_files(self):
        self.data['gif'] = dict(mode='binary', loop=2)
        self.data['actions'].append(
            dict(name='turn', range=[1, 4], direction='pingpong')
        )
        self.write()
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {p.name: p.read_bytes() for p in self.output.iterdir()}
        moved = self.root / '移动后 package'
        shutil.move(str(self.output), moved)
        shutil.rmtree(self.inputs)
        self.project = moved / 'animation.json'
        result = self.cli(output=self.root / 'regenerated')
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = {p.name: p.read_bytes() for p in (self.root / 'regenerated').iterdir()}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
