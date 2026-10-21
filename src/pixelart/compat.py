"""Small Pillow compatibility boundary; no installation or filesystem effects."""
import re

import PIL


def require_pillow():
    version = tuple(map(int, re.findall(r'\d+', PIL.__version__)[:2]))
    if not (len(version) == 2 and (10, 4) <= version < (13, 0)):
        raise ValueError('Pillow >=10.4,<13 is required; install requirements.txt '
                         '(Pillow==12.3.0 is the reproducibility baseline)')


def pixels(image):
    """Use the renamed API when present; Pillow 10/11 expose getdata instead."""
    method = getattr(image, 'get_flattened_data', None)
    return method() if method else image.getdata()
