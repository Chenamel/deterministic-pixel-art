"""Bounded PNG component projects, separate from embedded JSON v1 rendering."""
from pathlib import Path
from collections.abc import Mapping
from PIL import Image,ImageDraw,ImageFont
from .core import PixelArtError,color,dimensions,pair,boolean,MAX_PIXELS
from .context import _fields,_box,_name,_items
from .metadata import rgba_digest


def _project(project):
    _fields(project,('size','parts'),('version','background','require_coverage'),where='project')
    if type(project.get('version',1)) is not int or project.get('version',1)!=1:
        raise PixelArtError('project.version: expected integer 1')
    size=dimensions(project['size']);parts=_items(project['parts'],'project.parts')
    if not parts:raise PixelArtError('project.parts: cannot be empty')
    names=set()
    for i,part in enumerate(parts):
        where=f'parts[{i}]'
        _fields(part,('name','image','at','mode'),('crop','allow_overlap'),where=where)
        name=_name(part['name'],where+'.name')
        if name in names:raise PixelArtError(where+': duplicate name')
        names.add(name)
        if not isinstance(part['image'],str) or not part['image']:
            raise PixelArtError(where+'.image: expected a relative PNG path')
        if part['mode'] not in ('copy','over'):raise PixelArtError(where+'.mode: expected copy or over')
        pair(part['at'],where+'.at',0);boolean(part.get('allow_overlap',False),where+'.allow_overlap')
    boolean(project.get('require_coverage',False),'project.require_coverage')
    color(project.get('background'))
    return size,parts


def load_project(path):
    """Read local PNGs contained within the manifest directory. No writes."""
    from .jsonio import read_json
    path=Path(path).resolve();project=read_json(path);_,parts=_project(project)
    sources={};paths=[];total=0
    for part in parts:
        name=part['image'];relative=Path(name)
        source=(path.parent/relative).resolve()
        if relative.is_absolute() or not source.is_relative_to(path.parent):
            raise PixelArtError(f'project image escapes project directory: {name}')
        if name in sources:continue
        with source.open('rb') as handle:header=handle.read(33)
        if len(header)<33 or header[:8]!=b'\x89PNG\r\n\x1a\n' or header[12:16]!=b'IHDR' or header[24]>8:
            raise PixelArtError(f'project image: expected an at-most-8-bit PNG: {name}')
        with Image.open(source) as image:
            dimensions(image.size)
            if getattr(image,'n_frames',1)!=1:raise PixelArtError(f'project image: animation is unsupported: {name}')
            total+=image.width*image.height
            if total>4*MAX_PIXELS:raise PixelArtError('project: decoded source budget exceeds 67,108,864 pixels')
            sources[name]=image.convert('RGBA')
        paths.append(source)
    return project,sources,paths


def assemble(project,sources):
    """Return (RGBA image, geometric report), with no I/O or aesthetic verdict.

    Copy preserves all RGBA bytes. Over is source-over once. Coverage means
    destination rectangles, not nontransparent ink or semantic continuity.
    """
    size,parts=_project(project);canvas=Image.new('RGBA',size,color(project.get('background')))
    if not isinstance(sources,Mapping):raise PixelArtError('project sources: expected a name-to-image mapping')
    coverage=Image.new('1',size);pen=ImageDraw.Draw(coverage);placements=[];overlaps=[]
    total=0
    for key,image in sources.items():
        if image.mode not in ('1','L','LA','P','RGB','RGBA'):
            raise PixelArtError(f'project source {key!r}: requires decoded 8-bit pixels')
        dimensions(image.size);total+=image.width*image.height
        if total>4*MAX_PIXELS:raise PixelArtError('project: decoded source budget exceeds 67,108,864 pixels')
    for i,part in enumerate(parts):
        name=part['name'];source=sources.get(part['image'])
        if source is None:raise PixelArtError(f'parts[{i}]: missing PNG source {part["image"]!r}')
        if getattr(source,'n_frames',1)!=1:raise PixelArtError(f'parts[{i}]: animated sources are unsupported')
        crop=_box(part.get('crop',[0,0,*source.size]),source.size,f'parts[{i}].crop')
        x,y=pair(part['at'],f'parts[{i}].at',0);sx,sy,w,h=crop
        _box([x,y,w,h],size,f'parts[{i}].destination')
        for previous in placements:
            px,py,pw,ph=previous['rect'];ix=max(x,px);iy=max(y,py)
            iw=min(x+w,px+pw)-ix;ih=min(y+h,py+ph)-iy
            if iw>0 and ih>0:
                if not part.get('allow_overlap',False):
                    raise PixelArtError(f'parts[{i}] {name!r}: overlap with {previous["name"]!r} at {[ix,iy,iw,ih]}; declare allow_overlap only if intended')
                overlaps.append(dict(parts=[previous['name'],name],rect=[ix,iy,iw,ih]))
        piece=source.crop((sx,sy,sx+w,sy+h)).convert('RGBA')
        if part['mode']=='copy':canvas.paste(piece,(x,y))
        else:canvas.alpha_composite(piece,(x,y))
        pen.rectangle((x,y,x+w-1,y+h-1),fill=1)
        placements.append(dict(name=name,image=part['image'],source_rect=crop,rect=[x,y,w,h],mode=part['mode']))
    covered=sum(coverage.histogram()[1:])
    missing=size[0]*size[1]-covered
    if project.get('require_coverage',False) and missing:
        bbox=coverage.point(lambda v:0 if v else 1).getbbox()
        raise PixelArtError(f'project: {missing} pixels lack a component rectangle; uncovered bbox {bbox}')
    seams=[];seam_count=0
    for i,a in enumerate(placements):
        ax,ay,aw,ah=a['rect']
        for b in placements[i+1:]:
            bx,by,bw,bh=b['rect'];rect=None
            if (ax+aw==bx or bx+bw==ax) and max(ay,by)<min(ay+ah,by+bh):
                edge=bx if ax+aw==bx else ax;y0=max(ay,by);y1=min(ay+ah,by+bh)
                x0=max(0,edge-4);rect=[x0,y0,min(size[0],edge+4)-x0,y1-y0]
            elif (ay+ah==by or by+bh==ay) and max(ax,bx)<min(ax+aw,bx+bw):
                edge=by if ay+ah==by else ay;x0=max(ax,bx);x1=min(ax+aw,bx+bw)
                y0=max(0,edge-4);rect=[x0,y0,x1-x0,min(size[1],edge+4)-y0]
            if rect:
                seam_count+=1
                if len(seams)<256:seams.append(dict(parts=[a['name'],b['name']],rect=rect))
    report=dict(version=1,valid=True,size=list(size),covered_pixels=covered,uncovered_pixels=missing,
        parts=placements,intended_overlaps=overlaps,seams=seams,seam_count=seam_count,
        omitted_seams=max(0,seam_count-len(seams)),rgba_sha256=rgba_digest(canvas),
        limitations=['Coverage is geometric; transparent pixels still count.',
            'Seam crops support visual inspection, not automatic color/shape continuity acceptance.',
            'Copy replaces RGBA; over composites in manifest order. No artwork is silently resized.'])
    return canvas,report


def seam_sheet(image,report):
    """Show labeled native-coordinate seam segments with bounded nearest zoom."""
    cards=[];count=0
    for seam in report['seams']:
        x,y,w,h=seam['rect']
        for yy in range(y,y+h,64):
            for xx in range(x,x+w,64):
                count+=1
                if len(cards)<32:
                    rect=[xx,yy,min(64,x+w-xx),min(64,y+h-yy)]
                    cards.append((seam['parts'],rect))
    report['seam_views']=[]
    report['omitted_seam_views']=max(0,count-len(cards))
    columns=2;rows=max(1,(len(cards)+1)//2)
    sheet=Image.new('RGB',(560,rows*304+40),'#101827');draw=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=12)
    draw.text((8,8),'SEAM INSPECTION - global [x,y,w,h], nearest 4x; not an aesthetic verdict',fill='white',font=font)
    if not cards:draw.text((8,42),'No adjacent component rectangles.',fill='white',font=font)
    for i,(names,rect) in enumerate(cards):
        x,y,w,h=rect;piece=image.crop((x,y,x+w,y+h))
        bg=Image.new('RGBA',piece.size,'#172033');bg.alpha_composite(piece)
        dx=i%columns*280+8;dy=i//columns*304+40
        label=' / '.join(names);label=label if label.isascii() else '[Unicode names in report]'
        draw.text((dx,dy),label[:36],fill='white',font=font)
        draw.text((dx,dy+16),str(rect),fill='white',font=font)
        sheet.paste(bg.resize((w*4,h*4),Image.Resampling.NEAREST).convert('RGB'),(dx,dy+34))
        report['seam_views'].append(dict(parts=names,source_rect=rect,scale=4))
    return sheet
