"""Explicit pixel edits and raw RGBA edit-boundary verification."""
from copy import deepcopy
from collections.abc import Mapping
from PIL import Image,ImageDraw
from .core import PixelArtError,color,dimensions
from .context import _box


def _check_edit_image(image, where):
    dimensions(image.size)
    if getattr(image, 'n_frames', 1) != 1:
        raise PixelArtError(f'{where}: animated/multiframe images are not supported')
    if image.mode not in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA'):
        raise PixelArtError(
            f'{where}: requires decoded 8-bit grayscale, palette, RGB or RGBA pixels'
        )


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


def _allowed_mask(size,regions,mask,where):
    """The shared explicit union contract; never infer an object's selection."""
    if regions is not None and not isinstance(regions,(list,tuple)):
        raise PixelArtError(f'{where}.regions: expected a list of rectangles')
    if not regions and mask is None:raise PixelArtError(f'{where}: declare allowed regions or a mask')
    allowed=Image.new('L',size);pen=ImageDraw.Draw(allowed)
    for region in regions or []:
        x,y,w,h=_box(region,size,where+'.region')
        pen.rectangle((x,y,x+w-1,y+h-1),fill=255)
    if mask is not None:
        if getattr(mask, 'n_frames', 1) != 1:
            raise PixelArtError(f'{where}.mask: animated/multiframe masks are not supported')
        if mask.size!=size:raise PixelArtError(f'{where}.mask: dimensions must match')
        if mask.mode in ('RGBA','LA'):channel=mask.getchannel('A')
        elif mask.mode in ('L','1'):channel=mask.convert('L')
        else:raise PixelArtError(f'{where}.mask: use L/1 intensity or RGBA/LA alpha')
        allowed.paste(255,(0,0),channel.point(lambda v:255 if v else 0))
    return allowed


def recolor_image(image,mapping,*,regions=None,mask=None):
    """Return fresh RGBA pixels and a report, with no writes or input mutation.

    Mapping is a dict or a nonempty list of (source, target) color pairs. Each
    unique decoded source RGBA is matched against the original pixels, only
    inside the declared region/mask union. No chained replacement or inferred
    object selection takes place. Returned pixels do not inherit PNG metadata;
    callers must validate source layout and publish a fresh output record.
    """
    _check_edit_image(image, 'recolor')
    pairs=list(mapping.items()) if isinstance(mapping,Mapping) else mapping
    if not isinstance(pairs,(list,tuple)) or not pairs:
        raise PixelArtError('recolor.mapping: expected a nonempty mapping or list of color pairs')
    lookup={};records=[]
    for index,pair in enumerate(pairs):
        if not isinstance(pair,(list,tuple)) or len(pair)!=2:
            raise PixelArtError(f'recolor.mapping[{index}]: expected source and target colors')
        source=bytes(color(pair[0]));target=bytes(color(pair[1]))
        if source in lookup:
            raise PixelArtError(f'recolor.mapping[{index}]: duplicate source RGBA {source.hex().upper()}')
        lookup[source]=(target,index)
        records.append(dict(source=source.hex().upper(),target=target.hex().upper(),
                            matched_pixels=0,changed_rgba_pixels=0))
    allowed=_allowed_mask(image.size,regions,mask,'recolor')
    permissions=allowed.tobytes();raw=image.convert('RGBA').tobytes();result=bytearray(raw)
    changed=0
    for index,permission in enumerate(permissions):
        if not permission:continue
        offset=index*4;source=raw[offset:offset+4];replacement=lookup.get(source)
        if replacement is None:continue
        target,record_index=replacement;record=records[record_index]
        record['matched_pixels']+=1
        if source!=target:
            result[offset:offset+4]=target
            record['changed_rgba_pixels']+=1;changed+=1
    candidate=Image.frombytes('RGBA',image.size,bytes(result))
    report=dict(version=1,operation='recolor',size=list(image.size),
        allowed_pixels=sum(v>0 for v in permissions),mappings=records,
        matched_pixels=sum(record['matched_pixels'] for record in records),
        changed_rgba_pixels=changed,no_op=changed==0,
        unmatched_sources=[record['source'] for record in records if not record['matched_pixels']],
        note='Exact scoped RGBA replacement; no object identification or aesthetic acceptance. '
             'Changed RGBA includes invisible RGB changes under zero alpha.')
    return candidate,report


def verify_edit(image,comparison,*,regions=None,mask=None):
    """Check candidate vs baseline, including RGB hidden under zero alpha.

    Allowed regions and mask combine by union. Masks use alpha (RGBA/LA) or
    nonzero intensity (L/1); RGB masks are rejected to avoid an all-allowed trap.
    All reported rectangles are [x,y,width,height]. No artwork is changed.
    """
    _check_edit_image(image, 'verify.image')
    _check_edit_image(comparison, 'verify.compare')
    if image.size!=comparison.size:raise PixelArtError('verify: comparison dimensions must match')
    allowed=_allowed_mask(image.size,regions,mask,'verify')
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
