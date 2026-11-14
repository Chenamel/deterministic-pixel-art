"""Optional deterministic PNG layout records; never infer object semantics."""
from collections.abc import Mapping
import hashlib
from io import BytesIO
import json
import struct

from PIL.PngImagePlugin import PngInfo

from .core import PixelArtError
from .jsonio import parse_json

PNG_KEY = 'pixelart:layout'
MAX_LAYOUT_BYTES = 256 * 1024


def _check_record_size(text, source):
    if len(text.encode('utf-8')) > MAX_LAYOUT_BYTES:
        raise PixelArtError(f'{source} metadata exceeds 256 KiB')


def rgba_digest(image):
    digest = hashlib.sha256(b'pixelart-rgba-v1\0' + struct.pack('>II', *image.size))
    digest.update(image.convert('RGBA').tobytes())
    return digest.hexdigest()


def layout_record(image):
    return dict(version=1, size=list(image.size), mode=image.mode,
                atlas=image.info.get('pixelart'), rgba_sha256=rgba_digest(image))


def encode_png(image, metadata=None):
    buffer = BytesIO()
    options = {}
    if metadata is not None:
        serialized = json.dumps(
            metadata, ensure_ascii=True, sort_keys=True, separators=(',', ':')
        )
        _check_record_size(serialized, 'embedded')
        info = PngInfo()
        info.add_text(PNG_KEY, serialized)
        options['pnginfo'] = info
    image.save(buffer, format='PNG', **options)
    return buffer.getvalue()


def merge_layout(image, context=None, metadata=None, *, require_bound_atlas=False):
    """Merge declarations; mismatch is an error, never precedence.

    Strict consumers can require a digest-checked record supplying the atlas.
    Context alone, or a pixel digest with no atlas, cannot bind a layout.
    """
    if context is not None and not isinstance(context, Mapping):
        raise PixelArtError('context: expected an object')
    context = dict(context or {})
    sources, unchecked, bound_atlases = [], [], []
    atlas = context.get('atlas')
    if atlas is not None:
        sources.append('context')
    records = [('memory',layout_record(image) if image.info.get('pixelart') is not None else None),
               ('embedded', image.info.get(PNG_KEY)), ('sidecar', metadata)]
    digest = None
    for source, record in records:
        if record is None:
            continue
        if isinstance(record, str):
            _check_record_size(record, source)
            record = parse_json(record)
        if not isinstance(record, Mapping) or set(record)-{'version','size','mode','atlas','rgba_sha256'}:
            raise PixelArtError(f'{source} metadata: unknown fields or not an object')
        if type(record.get('version',1)) is not int or record.get('version',1)!=1:
            raise PixelArtError(f'{source} metadata.version: only 1 is supported')
        size=record.get('size')
        if not isinstance(size,(list,tuple)) or any(type(v) is not int for v in size) or list(size)!=list(image.size):
            raise PixelArtError(f'{source} metadata.size does not match image {image.size}')
        if not isinstance(record.get('mode'),str):
            raise PixelArtError(f'{source} metadata.mode: expected a string')
        if record['mode'] != image.mode:
            raise PixelArtError(f'{source} metadata.mode does not match image mode {image.mode}')
        if 'rgba_sha256' in record:
            digest = digest or rgba_digest(image)
            if record['rgba_sha256'] != digest:
                raise PixelArtError(f'{source} metadata pixel digest does not match image')
        else:
            unchecked.append(source)
        candidate = record.get('atlas')
        if candidate is not None:
            if atlas is not None and atlas != candidate:
                raise PixelArtError(f'{source} metadata conflicts with declared atlas')
            atlas = candidate
            if 'rgba_sha256' in record:
                bound_atlases.append(source)
        sources.append(source)
    if atlas is not None:
        context['atlas'] = atlas
    provenance = dict(sources=sources, unverified_records=unchecked,
                      note='Hashes verify pixels, not state-name meaning; legacy records have no pixel digest.')
    if require_bound_atlas:
        if not bound_atlases or unchecked:
            raise PixelArtError('atlas: require content-bound metadata supplying the named layout; '
                                'regenerate --metadata with the PNG')
        provenance['content_bound_atlas_sources'] = bound_atlases
    return context, provenance
