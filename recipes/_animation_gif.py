"""Explicit GIF projection using public Pillow APIs and decoded timeline checks."""

import hashlib
from io import BytesIO

from PIL import Image
from pixelart import PixelArtError
from pixelart.core import color
from pixelart.metadata import rgba_digest


def visible_rgba(image):
    """Canonicalize invisible RGB only for comparisons of GIF display pixels."""
    # Pillow may install alpha into a P image's palette during convert().
    # Keep the indexed images awaiting GIF encoding isolated from that mutation.
    rgba = image.copy().convert('RGBA')
    rgba.paste(
        (0, 0, 0, 0), mask=rgba.getchannel('A').point(lambda a: 255 if a == 0 else 0)
    )
    return rgba


def project_frame(image, config):
    if config['mode'] == 'background':
        background = Image.new('RGBA', image.size, color(config['background']))
        return Image.alpha_composite(background, image)
    result = image.copy()
    result.putalpha(result.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
    return visible_rgba(result)


def opaque_rgb(image):
    """Compact visible RGB bytes so hidden colors never train the palette."""
    data = image.tobytes()
    result = bytearray()
    for position in range(0, len(data), 4):
        if data[position + 3]:
            result.extend(data[position : position + 3])
    return result


def palette_frames(projected, indices, capacity):
    """Use exact colors when possible; otherwise train one MEDIANCUT palette."""
    colors = set()
    quantized = False
    for image in projected.values():
        counted = image.getcolors(capacity + 1)
        if counted is None:
            quantized = True
            break
        colors.update(rgba[:3] for _, rgba in counted if rgba[3])
        if len(colors) > capacity:
            quantized = True
            break

    if quantized:
        rgb_by_frame = {index: opaque_rgb(image) for index, image in projected.items()}
        training_bytes = bytearray()
        for index in indices:
            training_bytes.extend(rgb_by_frame[index])
        training = Image.frombytes(
            'RGB', (len(training_bytes) // 3, 1), bytes(training_bytes)
        )
        trained = training.quantize(
            colors=capacity,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )
        palette = trained.getpalette()
        used_colors = len(trained.getcolors())
        mapped = iter(trained.tobytes())
        color_indices = None
    else:
        ordered = sorted(colors)
        palette = [channel for rgb in ordered for channel in rgb]
        used_colors = len(ordered)
        color_indices = {rgb: i for i, rgb in enumerate(ordered)}
        mapped = None
    palette += [0] * (768 - len(palette))

    frames = []
    for index in indices:
        image = projected[index]
        rgba = image.tobytes()
        pixels = bytearray()
        for position in range(0, len(rgba), 4):
            if not rgba[position + 3]:
                pixels.append(255)
            elif mapped is not None:
                pixels.append(next(mapped))
            else:
                pixels.append(color_indices[tuple(rgba[position : position + 3])])
        frame = Image.frombytes('P', image.size, bytes(pixels))
        frame.putpalette(palette)
        if capacity == 255:
            frame.info['transparency'] = 255
        frames.append(frame)
    return frames, dict(
        capacity=capacity,
        opaque_colors=used_colors,
        quantized=quantized,
        quantizer='MEDIANCUT' if quantized else 'exact',
        dither='NONE',
    )


def timeline(frames, durations):
    """Group adjacent identical visible frames, retaining their logical indices."""
    segments = []
    for logical_index, (image, duration) in enumerate(zip(frames, durations)):
        rgba = visible_rgba(image)
        digest = rgba_digest(rgba)
        if segments and segments[-1]['rgba_sha256'] == digest:
            segments[-1]['duration_ms'] += duration
            segments[-1]['logical_entries'].append(logical_index)
        else:
            segments.append(
                dict(
                    rgba_sha256=digest,
                    duration_ms=duration,
                    logical_entries=[logical_index],
                )
            )
    return segments


def readback(data, size, loop):
    """Read actual composited display frames, including disposal effects."""
    frames, durations = [], []
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != 'GIF' or image.size != size:
                raise PixelArtError('animation: GIF readback has wrong format or size')
            if image.info.get('loop') != loop:
                raise PixelArtError('animation: GIF readback loop differs')
            for index in range(image.n_frames):
                image.seek(index)
                duration = image.info.get('duration', 0)
                if type(duration) is not int or duration <= 0 or duration % 10:
                    raise PixelArtError('animation: GIF readback has invalid duration')
                frames.append(image.convert('RGBA'))
                durations.append(duration)
    except (OSError, EOFError) as error:
        raise PixelArtError(f'animation: GIF readback failed: {error}') from error
    return frames, durations, timeline(frames, durations)


def encode_action(images, indices, original_durations, config):
    projected = {
        index: project_frame(images[index], config) for index in dict.fromkeys(indices)
    }
    capacity = 255 if config['mode'] == 'binary' else 256
    frames, palette = palette_frames(projected, indices, capacity)
    durations = [duration // 10 * 10 for duration in original_durations]
    expected = timeline(frames, durations)
    # Merge before saving so the report maps each logical entry to its visible run.
    encoded_frames = [frames[segment['logical_entries'][0]] for segment in expected]
    options = dict(
        format='GIF',
        save_all=True,
        append_images=encoded_frames[1:],
        duration=[segment['duration_ms'] for segment in expected],
        loop=config['loop'],
        disposal=2,
        optimize=False,
    )
    if config['mode'] == 'binary':
        options.update(transparency=255, background=255)
    buffer = BytesIO()
    try:
        encoded_frames[0].save(buffer, **options)
    except (OSError, ValueError) as error:
        raise PixelArtError(f'animation: GIF encoding failed: {error}') from error
    data = buffer.getvalue()
    actual_frames, actual_durations, actual_timeline = readback(
        data, frames[0].size, config['loop']
    )
    expected_visible = [(s['rgba_sha256'], s['duration_ms']) for s in expected]
    actual_visible = [(s['rgba_sha256'], s['duration_ms']) for s in actual_timeline]
    if expected_visible != actual_visible:
        raise PixelArtError(
            'animation: GIF readback visible timeline differs; no outputs published'
        )
    logical = []
    for index, original, duration in zip(indices, original_durations, durations):
        logical.append(
            dict(source_index=index, duration_ms=original, encoded_ms=duration)
        )
    for segment_index, segment in enumerate(expected):
        for logical_index in segment['logical_entries']:
            logical[logical_index]['segment'] = segment_index
    report = dict(
        mode=config['mode'],
        loop=config['loop'],
        palette=palette,
        alpha_threshold=128 if config['mode'] == 'binary' else None,
        background=config.get('background'),
        logical_entries=logical,
        segments=expected,
        original_duration_ms=sum(original_durations),
        encoded_duration_ms=sum(durations),
        lost_duration_ms=sum(original_durations) - sum(durations),
        readback=dict(
            verified=True,
            size=list(frames[0].size),
            loop=config['loop'],
            frame_count=len(actual_frames),
            durations_ms=actual_durations,
            visible_timeline=[
                dict(rgba_sha256=s['rgba_sha256'], duration_ms=s['duration_ms'])
                for s in actual_timeline
            ],
            gif_sha256=hashlib.sha256(data).hexdigest(),
        ),
    )
    return data, report
