"""Validate the bounded PNG-animation manifest and freeze its source files."""

from io import BytesIO
from pathlib import Path
import re
import stat
import struct
import unicodedata

from PIL import Image
from pixelart import PixelArtError
from pixelart.core import dimensions, integer
from pixelart.metadata import rgba_digest

MAX_JSON_BYTES = 1_048_576
MAX_FRAMES = 128
MAX_ACTIONS = 16
MAX_SIDE = 1024
MAX_FRAME_PIXELS = 1_048_576
MAX_PNG_BYTES = 8_388_608
MAX_SOURCE_BYTES = 67_108_864
MAX_SOURCE_PIXELS = 16_777_216
MAX_DURATION_MS = 60_000
MAX_ACTION_ENTRIES = 256
MAX_EXPANDED_ENTRIES = 1024
MAX_ACTION_MS = 120_000
MAX_GIF_PIXELS = 67_108_864
MAX_DELIVERY_BYTES = 134_217_728


def budget(actual, maximum, label):
    if actual > maximum:
        raise PixelArtError(
            f'animation: {label} is {actual}, limit {maximum}; split actions or sources'
        )


def read_bounded(path, maximum, label):
    with path.open('rb') as handle:
        data = handle.read(maximum + 1)
    budget(len(data), maximum, label)
    return data


def fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise PixelArtError(f'{label}: expected an object')
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        raise PixelArtError(
            f'{label}: missing fields {sorted(missing)}, unknown fields {sorted(unknown)}'
        )


def text(value, maximum, label):
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= maximum
        or any(unicodedata.category(c) in ('Cc', 'Cs') for c in value)
    ):
        raise PixelArtError(
            f'{label}: expected 1–{maximum} Unicode characters without controls'
        )
    return value


def resource_path(value):
    value = text(value, 1024, 'frame.image')
    if (
        '\\' in value
        or ':' in value
        or any(part in ('', '.', '..') for part in value.split('/'))
    ):
        raise PixelArtError(
            'frame.image: expected a relative /-separated resource path'
        )
    return value


def positive_integer(value, maximum, label):
    result = integer(value, label, 1)
    budget(result, maximum, label)
    return result


def gif_config(value):
    fields(value, ('mode',), ('background', 'loop'), 'gif')
    if value['mode'] not in ('binary', 'background'):
        raise PixelArtError('gif.mode: expected binary or background')
    loop = integer(value.get('loop', 0), 'gif.loop', 0)
    budget(loop, 65_535, 'gif.loop')
    result = dict(mode=value['mode'], loop=loop)
    if value['mode'] == 'background':
        background = value.get('background')
        if not isinstance(background, str) or not re.fullmatch(
            r'[0-9a-fA-F]{6}', background
        ):
            raise PixelArtError('gif.background: expected six RGB hex digits')
        result['background'] = background.upper()
    elif 'background' in value:
        raise PixelArtError('gif.background: only valid in background mode')
    return result


def expand_action(action, frame_count, label):
    fields(action, ('name', 'range'), ('direction',), label)
    name = text(action['name'], 128, f'{label}.name')
    bounds = action['range']
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise PixelArtError(f'{label}.range: expected [start, end)')
    start, end = (
        integer(value, f'{label}.range[{i}]', 0) for i, value in enumerate(bounds)
    )
    if not start < end <= frame_count:
        raise PixelArtError(f'{label}.range: require 0 <= start < end <= {frame_count}')
    direction = action.get('direction', 'forward')
    if direction not in ('forward', 'reverse', 'pingpong'):
        raise PixelArtError(f'{label}.direction: expected forward, reverse or pingpong')
    indices = list(range(start, end))
    if direction == 'reverse':
        indices.reverse()
    elif direction == 'pingpong':
        indices += indices[-2:0:-1]
    budget(len(indices), MAX_ACTION_ENTRIES, f'{label} expanded entries')
    return dict(name=name, range=[start, end], direction=direction), indices


def plan(project):
    """Check structure and temporal budgets before reading or decoding any PNG."""
    fields(project, ('version', 'kind', 'frames', 'actions'), ('gif',), 'animation')
    if type(project['version']) is not int or project['version'] != 1:
        raise PixelArtError('animation.version: expected integer 1')
    if project['kind'] != 'png-animation':
        raise PixelArtError('animation.kind: expected png-animation')
    frames, actions = project['frames'], project['actions']
    for values, maximum, label in (
        (frames, MAX_FRAMES, 'frames'),
        (actions, MAX_ACTIONS, 'actions'),
    ):
        if not isinstance(values, list) or not values:
            raise PixelArtError(f'animation.{label}: expected a nonempty array')
        budget(len(values), maximum, label)
    normalized_frames = []
    for i, frame in enumerate(frames):
        label = f'frames[{i}]'
        fields(frame, ('image', 'duration_ms'), (), label)
        normalized_frames.append(
            dict(
                image=resource_path(frame['image']),
                duration_ms=positive_integer(
                    frame['duration_ms'], MAX_DURATION_MS, f'{label}.duration_ms'
                ),
            )
        )
    normalized_actions, sequences, names = [], [], set()
    expanded_count = 0
    for i, action in enumerate(actions):
        label = f'actions[{i}]'
        normalized, indices = expand_action(action, len(frames), label)
        if normalized['name'] in names:
            raise PixelArtError(f'{label}.name: duplicate action name')
        names.add(normalized['name'])
        expanded_count += len(indices)
        budget(expanded_count, MAX_EXPANDED_ENTRIES, 'total expanded entries')
        duration = sum(normalized_frames[index]['duration_ms'] for index in indices)
        budget(duration, MAX_ACTION_MS, f'{label} duration_ms')
        normalized_actions.append(normalized)
        sequences.append(indices)
    normalized = dict(
        version=1,
        kind='png-animation',
        frames=normalized_frames,
        actions=normalized_actions,
    )
    if 'gif' in project:
        normalized['gif'] = gif_config(project['gif'])
        for action, indices in zip(normalized_actions, sequences):
            for index in indices:
                if normalized_frames[index]['duration_ms'] < 10:
                    raise PixelArtError(
                        f'animation: action {action["name"]!r}, frame {index}: '
                        'GIF requires at least 10ms; omit gif to retain exact PNG timing'
                    )
    return normalized, sequences


def png_size(data, label):
    if (
        len(data) < 33
        or data[:8] != b'\x89PNG\r\n\x1a\n'
        or data[8:16] != b'\x00\x00\x00\rIHDR'
    ):
        raise PixelArtError(f'{label}: expected a PNG input')
    if data[24] > 8:
        raise PixelArtError(f'{label}: PNG bit depth above 8 is unsupported')
    size = dimensions(struct.unpack('>II', data[16:24]))
    budget(max(size), MAX_SIDE, f'{label} side')
    budget(size[0] * size[1], MAX_FRAME_PIXELS, f'{label} pixels')
    position = 8
    while position + 12 <= len(data):
        length = int.from_bytes(data[position : position + 4], 'big')
        if data[position + 4 : position + 8] == b'acTL':
            raise PixelArtError(f'{label}: APNG animation is unsupported')
        position += length + 12
    return size


def freeze_sources(project, sequences, base):
    """Read each resolved source once, budget all entries, then fully decode."""
    base = Path(base).resolve(strict=True)
    snapshots, paths, sizes = {}, [], []
    total_bytes = total_pixels = 0
    first_size = None
    for i, frame in enumerate(project['frames']):
        label = f'frames[{i}]'
        try:
            path = (base / frame['image']).resolve(strict=True)
        except RuntimeError as error:
            # Python 3.10–3.12 report symlink loops as RuntimeError.
            raise PixelArtError(
                f'{label}.image: cannot resolve resource: {error}'
            ) from error
        if not path.is_relative_to(base) or not stat.S_ISREG(path.stat().st_mode):
            raise PixelArtError(
                f'{label}.image: resource must be a regular file inside project directory'
            )
        if path not in snapshots:
            snapshots[path] = read_bounded(path, MAX_PNG_BYTES, f'{label} PNG bytes')
        data = snapshots[path]
        size = png_size(data, label)
        if first_size is not None and size != first_size:
            raise PixelArtError(
                f'{label}: expected native size {first_size}, got {size}'
            )
        first_size = size
        total_bytes += len(data)
        total_pixels += size[0] * size[1]
        budget(total_bytes, MAX_SOURCE_BYTES, f'{label} accumulated PNG bytes')
        budget(total_pixels, MAX_SOURCE_PIXELS, f'{label} accumulated pixels')
        paths.append(path)
        sizes.append(size)
    if 'gif' in project:
        expanded_pixels = (
            sum(len(indices) for indices in sequences) * sizes[0][0] * sizes[0][1]
        )
        budget(expanded_pixels, MAX_GIF_PIXELS, 'total expanded GIF pixels')
    decoded, records = {}, []
    for i, (path, size) in enumerate(zip(paths, sizes)):
        if path not in decoded:
            try:
                with Image.open(BytesIO(snapshots[path])) as image:
                    image.verify()
                with Image.open(BytesIO(snapshots[path])) as image:
                    if image.format != 'PNG' or getattr(image, 'n_frames', 1) != 1:
                        raise PixelArtError(f'frames[{i}]: expected a single-frame PNG')
                    image.load()
                    decoded[path] = image.convert('RGBA')
            except (OSError, SyntaxError) as error:
                raise PixelArtError(
                    f'frames[{i}]: PNG decode failed: {error}'
                ) from error
        records.append(dict(size=list(size), rgba_sha256=rgba_digest(decoded[path])))
    return paths, snapshots, decoded, records
