"""Exact decoded 8-bit RGBA to existing JSON v1 specifications."""
import json

from .analysis import SYMBOLS
from .context import _box
from .core import PixelArtError, dimensions

MAX_SPEC_BYTES=4*1024*1024


def spec_bytes(spec):
    result=json.dumps(spec,ensure_ascii=False,indent=2).encode('utf-8')
    if len(result)>MAX_SPEC_BYTES:
        raise PixelArtError('import: specification exceeds 4 MiB; crop the target asset with --region')
    return result


def image_to_spec(image,*,region=None):
    """Flatten an 8-bit Pillow image without quantizing or reconstructing layers."""
    dimensions(image.size)
    if getattr(image,'n_frames',1)!=1:raise PixelArtError('import: animated/multiframe PNG is not supported')
    if image.mode not in ('1','L','LA','P','RGB','RGBA'):
        raise PixelArtError('import: only decoded 8-bit grayscale, palette, RGB and RGBA images are supported')
    if region is not None:
        x,y,w,h=_box(region,image.size,'region');image=image.crop((x,y,x+w,y+h))
    rgba=image.convert('RGBA');w,h=rgba.size;raw=rgba.tobytes()
    colors=set()
    for i in range(0,len(raw),4):
        colors.add(raw[i:i+4])
        if len(colors)>62:break
    if len(colors)<=62:
        if w*h+h*6>MAX_SPEC_BYTES:
            raise PixelArtError('import: grid exceeds 4 MiB; crop the target asset with --region')
        symbols={c:SYMBOLS[i] for i,c in enumerate(sorted(colors))}
        spec=dict(version=1,kind='grid',size=[w,h],palette={v:k.hex().upper() for k,v in symbols.items()},
                  rows=[''.join(symbols[raw[(y*w+x)*4:(y*w+x+1)*4]] for x in range(w)) for y in range(h)])
    else:
        operations=[];estimated=0
        for y in range(h):
            x=0
            while x<w:
                c=raw[(y*w+x)*4:(y*w+x+1)*4];end=x+1
                while end<w and raw[(y*w+end)*4:(y*w+end+1)*4]==c:end+=1
                if c!=b'\0\0\0\0':
                    op=dict(op='rect',x=x,y=y,w=end-x,h=1,color=c.hex().upper())
                    estimated+=len(json.dumps(op,indent=2).encode())+32
                    if estimated>MAX_SPEC_BYTES:
                        raise PixelArtError('import: run specification exceeds 4 MiB; crop the target asset with --region')
                    operations.append(op)
                x=end
        spec=dict(version=1,kind='draw',size=[w,h],operations=operations)
    spec_bytes(spec)
    return spec
