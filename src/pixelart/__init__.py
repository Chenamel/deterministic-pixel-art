"""Deterministic pixel assets. No files are created by importing this package."""
from .core import Canvas, PixelArtError, color, make_preview, outline, validate
from .spec import render

__all__ = ['Canvas', 'PixelArtError', 'color', 'make_preview', 'outline', 'render', 'validate',
           'inspect_image', 'image_to_spec']
__version__ = '1.2.0-rc.1'


def inspect_image(image, context=None, *, region=None, cell=None, grid=False, comparison=None, metadata=None):
    from .analysis import inspect_image as inspect
    return inspect(image,context,region=region,cell=cell,grid=grid,comparison=comparison,metadata=metadata)


def image_to_spec(image, *, region=None):
    from .ingest import image_to_spec as convert
    return convert(image,region=region)
