"""Advisory, context-aware review. Never edits artwork or assigns an aesthetic score."""
from __future__ import annotations
from collections.abc import Mapping
import hashlib
import math

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .core import PixelArtError, color, dimensions, integer, pair
from .compat import pixels


def _fields(value, required=(), optional=(), where='context'):
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        raise PixelArtError(f'{where}: expected an object with string keys')
    missing, unknown = set(required)-set(value), set(value)-set(required)-set(optional)
    if missing or unknown:
        raise PixelArtError(f'{where}: missing {sorted(missing)}, unknown {sorted(unknown)}')


def _name(value, where):
    if not isinstance(value, str) or not value.strip() or len(value)>160:
        raise PixelArtError(f'{where}: expected a nonempty name of at most 160 characters')
    return value


def _items(value, where, maximum=256):
    if not isinstance(value, list) or len(value)>maximum:
        raise PixelArtError(f'{where}: expected a list of at most {maximum} items')
    return value


def _box(value, size, where):
    if not isinstance(value, (list,tuple)) or len(value)!=4:
        raise PixelArtError(f'{where}: expected [x,y,w,h]')
    x,y=pair(value[:2],where,0); w,h=pair(value[2:],where,1)
    if x+w>size[0] or y+h>size[1]: raise PixelArtError(f'{where}: outside image')
    return [x,y,w,h]


def _opaque(value, where):
    rgba=color(value)
    if rgba[3]!=255: raise PixelArtError(f'{where}: requires an opaque background')
    return rgba


def _over(fg,bg):
    return Image.alpha_composite(Image.new('RGBA',(1,1),bg),Image.new('RGBA',(1,1),fg)).getpixel((0,0))


def _luminance(c):
    def linear(v):
        v=v/255
        return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    return sum(w*linear(v) for w,v in zip((0.2126,0.7152,0.0722),c[:3]))


def contrast(fg,bg):
    """sRGB relative-luminance ratio after compositing foreground onto opaque bg."""
    a,b=sorted((_luminance(_over(fg,bg)),_luminance(bg)))
    return (b+0.05)/(a+0.05)


def _context(value,size):
    value={} if value is None else value
    _fields(value,optional=('version','asset_type','backgrounds','primary_background','atlas','regions',
                            'contrast_pairs','allowed_specks'))
    if type(value.get('version',1)) is not int or value.get('version',1)!=1:
        raise PixelArtError('context.version: only integer 1 is supported')
    kind=value.get('asset_type','general')
    if kind not in ('general','sprite','ui'): raise PixelArtError('context.asset_type: expected general, sprite or ui')
    backgrounds=[dict(name='dark',color=(23,32,51,255)),dict(name='light',color=(233,237,242,255))]
    names={'dark','light'}
    for item in _items(value.get('backgrounds',[]),'backgrounds',8):
        _fields(item,('name','color'),where='background')
        name=_name(item['name'],'background.name')
        if name in names: raise PixelArtError('background.name: names must be unique, including dark/light')
        names.add(name); backgrounds.append(dict(name=name,color=_opaque(item['color'],'background.color')))
    primary=value.get('primary_background', backgrounds[2]['name'] if len(backgrounds)>2 else 'dark')
    if not isinstance(primary,str) or primary not in names:
        raise PixelArtError('primary_background: expected a declared background name')
    cells=[]
    if 'atlas' in value:
        layout=value['atlas']; _fields(layout,('cell_size','columns','rows','cells'),where='atlas')
        cw,ch=dimensions(layout['cell_size'])
        cols=integer(layout['columns'],'atlas.columns',1); rows=integer(layout['rows'],'atlas.rows',1)
        if (cw*cols,ch*rows)!=size: raise PixelArtError('atlas: grid does not match image dimensions')
        occupied=set(); names=set()
        for item in _items(layout['cells'],'atlas.cells'):
            _fields(item,('name','x','y','w','h'),where='atlas.cell')
            name=_name(item['name'],'atlas.cell.name')
            box=_box([item[k] for k in ('x','y','w','h')],size,'atlas.cell')
            x,y,w,h=box
            if name in names or (x,y) in occupied: raise PixelArtError('atlas: duplicate cell name or position')
            if (w,h)!=(cw,ch) or x%cw or y%ch: raise PixelArtError('atlas: cells must align to declared grid')
            names.add(name);occupied.add((x,y));cells.append(dict(name=name,rect=box))
        if not cells: raise PixelArtError('atlas.cells: cannot be empty')
    regions=[]
    names=set()
    for item in _items(value.get('regions',[]),'regions'):
        _fields(item,('name','rect','role'),where='region')
        name=_name(item['name'],'region.name')
        if name in names: raise PixelArtError('regions: duplicate name')
        names.add(name)
        if item['role'] not in ('content','control','reserved_text','decoration'):
            raise PixelArtError('region.role: expected content, control, reserved_text or decoration')
        regions.append(dict(name=name,rect=_box(item['rect'],size,'region.rect'),role=item['role']))
    allowed=set()
    for item in _items(value.get('allowed_specks',[]),'allowed_specks',4096):
        x,y=pair(item,'allowed_specks',0)
        if x>=size[0] or y>=size[1]: raise PixelArtError('allowed_specks: outside image')
        allowed.add((x,y))
    pairs=[];names=set()
    for item in _items(value.get('contrast_pairs',[]),'contrast_pairs'):
        _fields(item,('name','foreground','background'),('min_ratio','rect'),where='contrast_pair')
        name=_name(item['name'],'contrast_pair.name')
        if name in names: raise PixelArtError('contrast_pairs: duplicate name')
        names.add(name)
        minimum=item.get('min_ratio',3)
        if type(minimum) not in (int,float) or not math.isfinite(minimum) or not 1<=minimum<=21:
            raise PixelArtError('contrast_pair.min_ratio: expected a finite number from 1 to 21')
        fg=color(item['foreground']); bg=_opaque(item['background'],'contrast_pair.background')
        pairs.append(dict(name=name,foreground=list(fg),background=list(bg),min_ratio=minimum,
                          ratio=contrast(fg,bg),rect=_box(item['rect'],size,'contrast_pair.rect') if 'rect' in item else None))
    return dict(asset_type=kind,backgrounds=backgrounds,primary_background=primary,cells=cells,regions=regions,
                allowed_specks=allowed,contrast_pairs=pairs)


def _crop(image,rect):
    x,y,w,h=rect
    return image.crop((x,y,x+w,y+h))


def _visual_bytes(image):
    # RGB under alpha=0 has no visible meaning. Preserve all partially visible RGB.
    return bytes(v for rgba in pixels(image) for v in ((0,0,0,0) if rgba[3]==0 else rgba))


def _specks(image,scopes,allowed):
    result=[]; count=0
    for scope in scopes:
        x0,y0,w,h=scope['rect']; alpha=_crop(image,scope['rect']).getchannel('A').tobytes()
        for y in range(h):
            for x in range(w):
                if not alpha[y*w+x] or (x+x0,y+y0) in allowed: continue
                neighbors=(alpha[ny*w+nx] for ny in range(max(0,y-1),min(h,y+2))
                           for nx in range(max(0,x-1),min(w,x+2)) if (nx,ny)!=(x,y))
                if any(neighbors): continue
                count+=1
                if len(result)<256:
                    result.append(dict(rule='isolated_pixel',at=[x+x0,y+y0],cell=scope['name'],
                        message='No visible 8-neighbor within this cell; may be an intentional highlight or particle.'))
    return result,count


def _composite(image,bg):
    return Image.alpha_composite(Image.new('RGBA',image.size,bg),image)


def _label(name):
    # The bundled Pillow font is not a CJK font. Full original names remain in JSON.
    return name if name.isascii() else '[Unicode name: see report.json]'


def _sheet(image,ctx,report,difference):
    w,h=image.size
    scale=max(1,min(8,512//max(w,h)))
    primary=next(bg['color'] for bg in ctx['backgrounds'] if bg['name']==ctx['primary_background'])
    base=_composite(image,primary)
    checker=Image.new('RGBA',image.size,'#2C2C2C'); pen=ImageDraw.Draw(checker)
    for y in range(0,h,4):
        for x in range(0,w,4):
            if (x//4+y//4)%2==0:pen.rectangle((x,y,x+3,y+3),fill='#484848')
    checker.alpha_composite(image)
    views=[('native 1:1',base,1),('checker / nearest',checker,scale)]
    views += [(_label(bg['name'])+' background',_composite(image,bg['color']),scale) for bg in ctx['backgrounds']]
    views += [('grayscale / context only',ImageOps.grayscale(base).convert('RGBA'),scale)]
    if ctx['asset_type']=='sprite':
        silhouette=Image.new('RGBA',image.size,'#E9EDF2');silhouette.putalpha(image.getchannel('A'))
        views.append(('alpha silhouette',_composite(silhouette,primary),scale))
    annotated=base.copy();pen=ImageDraw.Draw(annotated)
    for cell in ctx['cells']:
        x,y,cw,ch=cell['rect'];pen.rectangle((x,y,x+cw-1,y+ch-1),outline='#F5C26B')
    for region in ctx['regions']:
        x,y,rw,rh=region['rect'];pen.rectangle((x,y,x+rw-1,y+rh-1),outline='#F5C26B')
    for warning in report['warnings']:
        if 'at' in warning:pen.point(tuple(warning['at']),fill='#FF6885')
    views.append(('annotated / not source art',annotated,scale))
    if difference is not None: views.append(('changed visible pixels',difference,scale))
    # State cells are numbered; names and exact rectangles are also in report.json.
    for i,cell in enumerate(ctx['cells']):
        piece=_crop(base,cell['rect'])
        views.append((f"cell {i+1}: {_label(cell['name'])}",piece,scale))
    def fit(items, maximum_columns):
        cw=max(240,max(im.width*s for _,im,s in items))+16
        ch=max(im.height*s for _,im,s in items)+44
        for cols in range(min(maximum_columns,len(items)),0,-1):
            size=(cw*cols,ch*((len(items)+cols-1)//cols)+32)
            if max(size)<=8192 and size[0]*size[1]<=16_777_216:
                return cw,ch,cols,size
        return None
    layout=fit(views,3)
    manifest=[]
    if layout is None:
        # Keep bounded native crops plus a labeled overview, never an implicit
        # resize of a card claiming to be native 1:1.
        overview=base.copy();overview.thumbnail((128,128),Image.Resampling.NEAREST)
        cropped=[('full image / nearest thumbnail',overview,1)]
        manifest.append(dict(label='full image / nearest thumbnail',source_rect=[0,0,w,h],downsampled=True))
        for label,im,_ in views:
            cw,ch=min(128,im.width),min(128,im.height)
            cropped.append((label+f' / native crop [0,0,{cw},{ch}]',im.crop((0,0,cw,ch)),1))
            manifest.append(dict(label=label,source_rect=[0,0,cw,ch],scale=1,
                                 cropped=(cw,ch)!=im.size))
        views=cropped
        layout=fit(views,8)
    else:
        manifest=[dict(label=label,source_rect=[0,0,*im.size],scale=s,cropped=False) for label,im,s in views]
    card_w,card_h,columns,size=layout
    report['facts']['review_views']=manifest
    sheet=Image.new('RGB',size,'#101827');pen=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=12)
    pen.text((8,8),'ADVISORY REVIEW - overlays and diagnostics are separate from source art',fill='#E9EDF2',font=font)
    for i,(label,im,s) in enumerate(views):
        x=i%columns*card_w+8;y=i//columns*card_h+40
        pen.text((x,y),label[:100],fill='#E9EDF2',font=font)
        sheet.paste(im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST).convert('RGB'),(x,y+22))
    return sheet


def review(image,context=None,comparison=None):
    """Return (JSON-serializable report, review sheet, optional diff); no I/O."""
    dimensions(image.size)
    if comparison is not None and comparison.size!=image.size:
        raise PixelArtError('comparison: dimensions must match the source')
    rgba=image.convert('RGBA');ctx=_context(context,rgba.size)
    scopes=ctx['cells'] or [dict(name='image',rect=[0,0,*rgba.size])]
    warnings,speck_count=_specks(rgba,scopes,ctx['allowed_specks'])
    hashes={}
    for cell in ctx['cells']:
        digest=hashlib.sha256(_visual_bytes(_crop(rgba,cell['rect']))).hexdigest()
        if digest in hashes:
            warnings.append(dict(rule='duplicate_state',cells=[hashes[digest],cell['name']],
                rect=cell['rect'],message='Cells are visually identical; sharing artwork may be intentional.'))
        else:hashes[digest]=cell['name']
    for item in ctx['contrast_pairs']:
        if item['ratio']<item['min_ratio']:
            warnings.append(dict(rule='declared_contrast',name=item['name'],rect=item['rect'],
                ratio=item['ratio'],minimum=item['min_ratio'],
                message='Declared functional color pair is below its requested contrast ratio.'))
    difference=None; comparison_report=None
    if comparison is not None:
        other=comparison.convert('RGBA')
        a,b=_visual_bytes(rgba),_visual_bytes(other)
        mask=Image.frombytes('L',rgba.size,bytes(255 if a[i:i+4]!=b[i:i+4] else 0 for i in range(0,len(a),4)))
        difference=Image.new('RGBA',rgba.size,'#172033');highlight=Image.new('RGBA',rgba.size,'#FF6885')
        difference.paste(highlight,(0,0),mask)
        comparison_report=dict(changed_visible_pixels=sum(mask.histogram()[1:]),bbox=mask.getbbox(),
                               note='Pixel changes do not establish better artwork.')
    facts=dict(size=list(image.size),mode=image.mode,asset_type=ctx['asset_type'],
        backgrounds=ctx['backgrounds'],primary_background=ctx['primary_background'],isolated_pixels=speck_count,
        omitted_isolated_warnings=max(0,speck_count-256),cells=ctx['cells'],regions=ctx['regions'],
        contrast_pairs=ctx['contrast_pairs'],allowed_specks=[list(p) for p in sorted(ctx['allowed_specks'])])
    report=dict(version=1,advisory=True,facts=facts,warnings=warnings,comparison=comparison_report,
        checklist=['Read at native size on the intended background.',
                   'Check direction, silhouette, material and named state meaning.',
                   'Inspect reserved text regions using the consumer font and real content.',
                   'Review warnings against intent; no automatic aesthetic pass/fail.'],
        limitations=['No independent visual judgement, font-layout or in-game verification.',
                     'Only explicitly declared functional color pairs have contrast thresholds.',
                     'Isolated pixels are tested per cell with visible alpha and 8-neighbor connectivity.'])
    return report,_sheet(rgba,ctx,report,difference),difference
