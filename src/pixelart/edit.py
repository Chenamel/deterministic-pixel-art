"""Explicit named-cell replacement and raw RGBA edit-boundary verification."""
from copy import deepcopy
from PIL import Image,ImageDraw
from .core import PixelArtError,dimensions
from .context import _box


def replace_cell(spec,name,replacement):
    """Return a new valid atlas spec; no I/O and no change to the original."""
    from .spec import render
    if not isinstance(spec,dict) or spec.get('kind')!='atlas':
        raise PixelArtError('replace-cell: expected an atlas spec')
    render(spec)
    result=deepcopy(spec)
    matches=[cell for cell in result['cells'] if cell['name']==name]
    if len(matches)!=1:raise PixelArtError(f'replace-cell: unknown cell {name!r}')
    if render(matches[0]['spec']).size!=render(replacement).size:
        raise PixelArtError('replace-cell: replacement dimensions must match the existing cell')
    matches[0]['spec']=deepcopy(replacement)
    render(result)
    return result


def verify_edit(image,comparison,*,regions=None,mask=None):
    """Check candidate vs baseline, including RGB hidden under zero alpha.

    Allowed regions and mask combine by union. Masks use alpha (RGBA/LA) or
    nonzero intensity (L/1); RGB masks are rejected to avoid an all-allowed trap.
    All reported rectangles are [x,y,width,height]. No artwork is changed.
    """
    dimensions(image.size)
    if image.size!=comparison.size:raise PixelArtError('verify: comparison dimensions must match')
    if regions is not None and not isinstance(regions,(list,tuple)):
        raise PixelArtError('verify.regions: expected a list of rectangles')
    if not regions and mask is None:raise PixelArtError('verify: declare allowed regions or a mask')
    allowed=Image.new('L',image.size);pen=ImageDraw.Draw(allowed)
    for region in regions or []:
        x,y,w,h=_box(region,image.size,'verify.region')
        pen.rectangle((x,y,x+w-1,y+h-1),fill=255)
    if mask is not None:
        if mask.size!=image.size:raise PixelArtError('verify.mask: dimensions must match')
        if mask.mode in ('RGBA','LA'):channel=mask.getchannel('A')
        elif mask.mode in ('L','1'):channel=mask.convert('L')
        else:raise PixelArtError('verify.mask: use L/1 intensity or RGBA/LA alpha')
        allowed.paste(255,(0,0),channel.point(lambda v:255 if v else 0))
    raw=image.convert('RGBA').tobytes();old=comparison.convert('RGBA').tobytes();permissions=allowed.tobytes()
    changed=outside=0;samples=[];x0=image.width;y0=image.height;x1=y1=0
    for i in range(len(permissions)):
        if raw[i*4:i*4+4]==old[i*4:i*4+4]:continue
        changed+=1
        if permissions[i]:continue
        outside+=1;x=i%image.width;y=i//image.width
        x0=min(x0,x);y0=min(y0,y);x1=max(x1,x+1);y1=max(y1,y+1)
        if len(samples)<64:samples.append([x,y])
    return dict(version=1,valid=outside==0,changed_rgba_pixels=changed,
        changed_inside=changed-outside,changed_outside=outside,allowed_pixels=sum(v>0 for v in permissions),
        outside_bbox=[x0,y0,x1-x0,y1-y0] if outside else None,outside_samples=samples,
        omitted_outside_samples=max(0,outside-len(samples)),
        note='Exact edit boundary only; does not judge appearance, object identity or state meaning.')
