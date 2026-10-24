"""Deterministic pixel assets. No files are created by importing this package."""
from .core import Canvas, PixelArtError, color, make_preview, outline, validate
from .spec import render

__all__ = ['Canvas', 'PixelArtError', 'color', 'make_preview', 'outline', 'render', 'validate',
           'inspect_image', 'image_to_spec','replace_cell','verify_edit','assemble']
__version__ = '1.2.0-rc.5'


def inspect_image(image, context=None, *, region=None, cell=None, grid=False, comparison=None, metadata=None):
    from .analysis import inspect_image as inspect
    return inspect(image,context,region=region,cell=cell,grid=grid,comparison=comparison,metadata=metadata)


def image_to_spec(image, *, region=None,metadata=None,cell=None):
    from .ingest import image_to_spec as convert
    return convert(image,region=region,metadata=metadata,cell=cell)


def replace_cell(spec,name,replacement):
    from .edit import replace_cell as replace
    return replace(spec,name,replacement)


def verify_edit(image,comparison,*,regions=None,mask=None):
    from .edit import verify_edit as verify
    return verify(image,comparison,regions=regions,mask=mask)


def assemble(project,sources):
    from .assembly import assemble as compose
    return compose(project,sources)
