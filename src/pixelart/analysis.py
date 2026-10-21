"""Bounded textual facts about pixels, with no aesthetic pass/fail."""
from collections import Counter
import hashlib
import string
import struct
import sys

from .core import PixelArtError, dimensions
from .context import _box, _context
from .metadata import merge_layout, rgba_digest

SYMBOLS = string.digits + string.ascii_uppercase + string.ascii_lowercase


def _rgba(value):
    return list(value.to_bytes(4, 'big'))


def _rect(bounds, origin):
    x0,y0,x1,y1=bounds
    return [x0+origin[0],y0+origin[1],x1-x0,y1-y0]


def _components(mask,w,h,neighbors,origin):
    count=sum(mask)
    if not count:
        return dict(count=0,largest=[],omitted=0)
    if count==w*h:
        return dict(count=1,largest=[dict(pixels=count,bbox=[*origin,w,h])],omitted=0)
    pending=bytearray(mask)
    total=0;largest=[]
    offsets=((-1,0),(1,0),(0,-1),(0,1))
    if neighbors==8:
        offsets+=((-1,-1),(-1,1),(1,-1),(1,1))
    for seed in range(w*h):
        if not pending[seed]:continue
        total+=1;pending[seed]=0;stack=[seed]
        size=0;x0=w;y0=h;x1=y1=0
        while stack:
            point=stack.pop();x=point%w;y=point//w
            size+=1;x0=min(x0,x);y0=min(y0,y);x1=max(x1,x+1);y1=max(y1,y+1)
            for dx,dy in offsets:
                nx,ny=x+dx,y+dy
                if 0<=nx<w and 0<=ny<h:
                    index=ny*w+nx
                    if pending[index]:pending[index]=0;stack.append(index)
        largest.append(dict(pixels=size,bbox=_rect((x0,y0,x1,y1),origin)))
        largest.sort(key=lambda c:(-c['pixels'],c['bbox']))
        if len(largest)>16:largest.pop()
    return dict(count=total,largest=largest,omitted=max(0,total-16))


def _symmetry(mask,values,w,h):
    result={}
    for axis in ('x','y'):
        pairs=(w//2)*h if axis=='x' else (h//2)*w
        shape=colors=0
        for y in range(h if axis=='x' else h//2):
            for x in range(w//2 if axis=='x' else w):
                a=y*w+x;b=y*w+(w-1-x) if axis=='x' else (h-1-y)*w+x
                if bool(mask[a])!=bool(mask[b]):shape+=1
                av=values[a] if mask[a] else 0;bv=values[b] if mask[b] else 0
                if av!=bv:colors+=1
        result[axis]=dict(compared_pairs=pairs,silhouette_mismatched_pairs=shape,
                          color_mismatched_pairs=colors,
                          silhouette_mismatch_ratio=shape/pairs if pairs else 0,
                          color_mismatch_ratio=colors/pairs if pairs else 0)
    return result


def _facts(image,origin,excluded):
    rgba=image.convert('RGBA');w,h=rgba.size
    raw=rgba.tobytes();values=memoryview(raw).cast('I')
    # Values use native byte order only for equality; RGBA decoding uses >I.
    exclude={int.from_bytes(bytes(c),byteorder=sys.byteorder) for c in excluded}
    mask=bytearray(w*h);hist=Counter();alpha=Counter();partial=[];partial_count=0
    visible=0;sx=sy=0;x0=w;y0=h;x1=y1=0
    visual=bytearray(raw)
    for i,value in enumerate(values):
        a=raw[i*4+3];alpha[a]+=1
        x,y=i%w,i//w
        if 0<a<255:
            partial_count+=1
            if len(partial)<64:partial.append([x+origin[0],y+origin[1]])
        if a and value not in exclude:
            mask[i]=1;visible+=1;sx+=x+.5;sy+=y+.5
            x0=min(x0,x);y0=min(y0,y);x1=max(x1,x+1);y1=max(y1,y+1)
            hist[struct.unpack_from('>I',raw,i*4)[0]]+=1
        else:
            visual[i*4:i*4+4]=b'\0\0\0\0'
    top=sorted(hist.items(),key=lambda item:(-item[1],item[0]))[:32]
    box=_rect((x0,y0,x1,y1),origin) if visible else None
    return dict(rect=[*origin,w,h],visible_pixels=visible,occupancy=visible/(w*h),bbox=box,
        margins=dict(left=x0,right=w-x1,top=y0,bottom=h-y1) if visible else None,
        centroid=[sx/visible+origin[0],sy/visible+origin[1]] if visible else None,
        foreground=dict(rule='alpha>0, excluding exact declared RGBA colors',exclude_colors=[list(c) for c in excluded]),
        colors=dict(count=len(hist),top=[dict(rgba=_rgba(c),pixels=n) for c,n in top],omitted=max(0,len(hist)-32)),
        alpha=dict(histogram=[dict(value=a,pixels=n) for a,n in sorted(alpha.items())],
                   partial_pixels=partial_count,partial_coordinates=partial,omitted_coordinates=max(0,partial_count-64)),
        symmetry=_symmetry(mask,values,w,h),
        components={str(n):_components(mask,w,h,n,origin) for n in (4,8)},
        rgba_sha256=rgba_digest(rgba),visible_sha256=hashlib.sha256(visual).hexdigest())


def _grid(image,origin):
    w,h=image.size
    if w>64 or h>64:
        raise PixelArtError('grid: limited to 64x64; select --region or --cell')
    raw=image.convert('RGBA').tobytes()
    colors=sorted({raw[i:i+4] for i in range(0,len(raw),4)})
    if len(colors)>62:
        raise PixelArtError('grid: limited to 62 exact colors; select a smaller region (no quantization is applied)')
    symbols={c:SYMBOLS[i] for i,c in enumerate(colors)}
    return dict(origin=list(origin),palette={symbols[c]:c.hex().upper() for c in colors},
                rows=[''.join(symbols[raw[(y*w+x)*4:(y*w+x+1)*4]] for x in range(w)) for y in range(h)])


def _comparison(image,other,origin):
    if image.size!=other.size:raise PixelArtError('comparison: dimensions must match the source')
    a=image.convert('RGBA').tobytes();b=other.convert('RGBA').tobytes();w,h=image.size
    changed=raw_changed=0;x0=w;y0=h;x1=y1=0
    for i in range(w*h):
        av=a[i*4:i*4+4];bv=b[i*4:i*4+4]
        if av!=bv:raw_changed+=1
        if (av if av[3] else b'\0'*4)!=(bv if bv[3] else b'\0'*4):
            changed+=1;x=i%w;y=i//w;x0=min(x0,x);y0=min(y0,y);x1=max(x1,x+1);y1=max(y1,y+1)
    return dict(changed_visible_pixels=changed,changed_rgba_pixels=raw_changed,
                bbox=_rect((x0,y0,x1,y1),origin) if changed else None,
                note='Changed pixels do not establish better artwork.')


def inspect_image(image,context=None,*,region=None,cell=None,grid=False,comparison=None,metadata=None):
    """Return bounded JSON facts. All rectangles are global [x,y,width,height].

    Centroids use visible pixel centers (x+.5,y+.5), not optical-weight estimates.
    Empty foreground has null bbox, margins and centroid. No files are written.
    """
    dimensions(image.size)
    if region is not None and cell is not None:raise PixelArtError('choose region or cell, not both')
    merged,provenance=merge_layout(image,context,metadata);ctx=_context(merged,image.size)
    selected=[0,0,*image.size]
    if region is not None:selected=_box(region,image.size,'region')
    if cell is not None:
        found=next((c for c in ctx['cells'] if c['name']==cell),None)
        if found is None:raise PixelArtError(f'cell: unknown name {cell!r}')
        selected=found['rect']
    x,y,w,h=selected;crop=image.crop((x,y,x+w,y+h))
    result=dict(version=1,advisory=True,source_size=list(image.size),mode=image.mode,
        metadata=provenance,facts=_facts(crop,(x,y),ctx['exclude_colors']),cells=[],comparison=None,
        limitations=['Geometry and hashes do not identify objects or judge beauty.',
                     'Foreground uses alpha and explicit exclusions, never inferred background.',
                     'Centroid and symmetry are measurements, not requirements.'])
    if region is None and cell is None:
        for item in ctx['cells']:
            cx,cy,cw,ch=item['rect']
            result['cells'].append(dict(name=item['name'],**_facts(image.crop((cx,cy,cx+cw,cy+ch)),(cx,cy),ctx['exclude_colors'])))
    if grid:result['grid']=_grid(crop,(x,y))
    if comparison is not None:
        if comparison.size!=image.size:raise PixelArtError('comparison: dimensions must match the source')
        result['comparison']=_comparison(crop,comparison.crop((x,y,x+w,y+h)),(x,y))
    return result
