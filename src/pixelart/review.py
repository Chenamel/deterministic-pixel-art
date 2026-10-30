"""Advisory, context-aware review. Never edits artwork or assigns an aesthetic score."""
from __future__ import annotations
import hashlib

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .core import PixelArtError, color, dimensions, integer, pair
from .compat import pixels


from .context import _context, contrast


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
    views=[('native 1:1 / '+_label(ctx['primary_background']),base,1),('checker / nearest',checker,scale)]
    for bg in ctx['backgrounds']:
        piece=_composite(image,bg['color'])
        if bg['name']!=ctx['primary_background']:
            views.append((_label(bg['name'])+' background / native 1:1',piece,1))
        views.append((_label(bg['name'])+' background / nearest',piece,scale))
    views += [('grayscale / context only',ImageOps.grayscale(base).convert('RGBA'),scale)]
    if ctx['asset_type']=='sprite':
        ink=max(((0,0,0,255),(255,255,255,255)),key=lambda c:contrast(c,primary))
        report['facts']['silhouette_color']=list(ink)
        silhouette=Image.new('RGBA',image.size,ink);silhouette.putalpha(image.getchannel('A'))
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
        manifest[i]['sheet_rect']=[x,y+22,im.width*s,im.height*s]
        pen.text((x,y),label[:100],fill='#E9EDF2',font=font)
        sheet.paste(im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST).convert('RGB'),(x,y+22))
    return sheet


def review(image,context=None,comparison=None,*,metadata=None):
    """Return (JSON-serializable report, review sheet, optional diff); no I/O."""
    dimensions(image.size)
    if comparison is not None and comparison.size!=image.size:
        raise PixelArtError('comparison: dimensions must match the source')
    from .metadata import merge_layout
    from .analysis import inspect_image
    merged,provenance=merge_layout(image,context,metadata)
    rgba=image.convert('RGBA');ctx=_context(merged,rgba.size)
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
    report['analysis']=inspect_image(image,context,comparison=comparison,metadata=metadata)
    report['cell_summary']=[{key:cell[key] for key in ('name','visible_pixels','occupancy','bbox','margins','centroid')}
                            for cell in report['analysis']['cells']]
    return report,_sheet(rgba,ctx,report,difference),difference
