"""Strict JSON decoding shared by files and embedded metadata."""
import json
from pathlib import Path
from .core import PixelArtError


def parse_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PixelArtError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    try:
        return json.loads(text, object_pairs_hook=unique)
    except RecursionError as exc:
        raise PixelArtError('JSON nesting exceeds the decoder limit; simplify the input') from exc


def read_json(path):
    return parse_json(Path(path).read_text(encoding='utf-8-sig'))
