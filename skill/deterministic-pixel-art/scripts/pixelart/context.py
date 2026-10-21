"""Shared strict context parsing and declared contrast calculations."""
from collections.abc import Mapping
import math
from PIL import Image
from .core import PixelArtError, color, dimensions, integer, pair


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
                            'contrast_pairs','allowed_specks','analysis'))
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
    analysis=value.get('analysis',{})
    _fields(analysis,optional=('exclude_colors',),where='analysis')
    excluded=[color(c) for c in _items(analysis.get('exclude_colors',[]),'analysis.exclude_colors',256)]
    return dict(asset_type=kind,backgrounds=backgrounds,primary_background=primary,cells=cells,regions=regions,
                allowed_specks=allowed,contrast_pairs=pairs,exclude_colors=excluded)
