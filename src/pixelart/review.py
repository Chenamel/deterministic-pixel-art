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


def _window(size, point):
    w,h=min(128,size[0]),min(128,size[1])
    return [max(0,min(size[0]-w,point[0]-w//2)),
            max(0,min(size[1]-h,point[1]-h//2)),w,h]


def _intersection(a,b):
    x=max(a[0],b[0]);y=max(a[1],b[1])
    right=min(a[0]+a[2],b[0]+b[2]);bottom=min(a[1]+a[3],b[1]+b[3])
    return [x,y,right-x,bottom-y] if right>x and bottom>y else None


def _covered_area(rect,windows):
    """Exact rectangle-union area, without allocating another full-size mask."""
    boxes=[box for window in windows if (box:=_intersection(rect,window)) is not None]
    edges=sorted({edge for x,y,w,h in boxes for edge in (x,x+w)})
    area=0
    for left,right in zip(edges,edges[1:]):
        intervals=sorted((y,y+h) for x,y,w,h in boxes if x<=left and x+w>=right)
        end=-1;covered=0
        for top,bottom in intervals:
            covered+=max(0,bottom-max(top,end));end=max(end,bottom)
        area+=(right-left)*covered
    return area


def _focus_windows(size,ctx,change_mask):
    """At most eight native windows, with exact coverage and omission facts."""
    w,h=size;limit=8
    changes=[]
    bbox=change_mask.getbbox() if change_mask is not None else None
    if bbox:
        for y in range(bbox[1]//128*128,bbox[3],128):
            for x in range(bbox[0]//128*128,bbox[2],128):
                rect=[x,y,min(128,w-x),min(128,h-y)]
                if _crop(change_mask,rect).getbbox():
                    changes.append(dict(source_rect=rect,reason='visible changes'))

    def spread(items,count):
        if count<=0:return []
        if len(items)<=count:return items
        if count==1:return items[:1]
        return [items[i*(len(items)-1)//(count-1)] for i in range(count)]

    windows=spread(changes,limit)
    def add(items):
        seen={tuple(item['source_rect']) for item in windows};unique=[]
        for item in items:
            key=tuple(item['source_rect'])
            if key not in seen:
                seen.add(key);unique.append(item)
        windows.extend(spread(unique,limit-len(windows)))

    # Center declarations first; large targets also supply boundary samples.
    for anchor in ('center','top-left','top-right','bottom-left','bottom-right'):
        targets=[]
        for region in ctx['regions']:
            x,y,rw,rh=region['rect']
            if anchor=='center':point=(x+rw//2,y+rh//2)
            elif anchor=='top-left':point=(x,y)
            elif anchor=='top-right':point=(x+rw-1,y)
            elif anchor=='bottom-left':point=(x,y+rh-1)
            else:point=(x+rw-1,y+rh-1)
            targets.append(dict(source_rect=_window(size,point),reason='declared region',region=region['name']))
        add(targets)
    add([dict(source_rect=_window(size,point),reason='image boundary/context')
         for point in ((0,0),(w-1,0),(0,h-1),(w-1,h-1),(w//2,h//2))])
    rects=[item['source_rect'] for item in windows]
    changed=omitted=remaining_bbox=None
    if change_mask is not None:
        changed=sum(change_mask.histogram()[1:]);remaining=change_mask.copy()
        for x,y,rw,rh in rects:remaining.paste(0,(x,y,x+rw,y+rh))
        omitted=sum(remaining.histogram()[1:]);bounds=remaining.getbbox()
        if bounds:remaining_bbox=[bounds[0],bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]]
    targets=[]
    for region in ctx['regions']:
        area=_covered_area(region['rect'],rects)
        targets.append(dict(name=region['name'],source_rect=region['rect'],displayed_area=area,
                            omitted_area=region['rect'][2]*region['rect'][3]-area))
    area=_covered_area([0,0,w,h],rects)
    facts=dict(window_limit=limit,native_window_max_size=[128,128],windows=windows,
        changed_tiles=len(changes),changed_visible_pixels=changed,
        displayed_changed_visible_pixels=None if changed is None else changed-omitted,
        omitted_changed_visible_pixels=omitted,omitted_changed_bbox=remaining_bbox,
        target_regions=targets,native_source_pixels_displayed=area,native_source_pixels_omitted=w*h-area,
        note='Coverage describes these focus windows; the full-image overview is downsampled. '
             'Changes take priority, then declared regions and boundary/context samples. '
             'When over budget, deterministic spatial samples leave explicitly counted omissions.')
    return windows,facts


def _sheet(image,ctx,report,difference,*,change_mask=None):
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
    origins=[(0,0)]*len(views)
    # State cells are numbered; names and exact rectangles are also in report.json.
    for i,cell in enumerate(ctx['cells']):
        piece=_crop(base,cell['rect'])
        views.append((f"cell {i+1}: {_label(cell['name'])}",piece,scale))
        origins.append(tuple(cell['rect'][:2]))
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
        # Focus actual changes/declared regions; a thumbnail cannot guarantee
        # visibility of a one-pixel edit. Keep all original diagnostic cards.
        focuses,report['facts']['review_focus']=_focus_windows(image.size,ctx,change_mask)
        overview=base.copy();overview.thumbnail((128,128),Image.Resampling.NEAREST)
        cropped=[('full image / nearest thumbnail',overview,1)]
        manifest.append(dict(label='full image / nearest thumbnail',source_rect=[0,0,w,h],downsampled=True))
        for (label,im,_),(ox,oy) in zip(views,origins):
            source=[ox,oy,*im.size]
            if source==[0,0,w,h]:rect=focuses[0]['source_rect']
            else:
                intersections=[box for focus in focuses
                               if (box:=_intersection(source,focus['source_rect'])) is not None]
                box=intersections[0] if intersections else source
                local=_window(im.size,(box[0]+box[2]//2-ox,box[1]+box[3]//2-oy))
                rect=[ox+local[0],oy+local[1],*local[2:]]
            local=[rect[0]-ox,rect[1]-oy,*rect[2:]]
            cropped.append((label+f' / native crop {rect}',_crop(im,local),1))
            manifest.append(dict(label=label,source_rect=rect,scale=1,cropped=rect!=source))
        for index,focus in enumerate(focuses[1:],2):
            rect=focus['source_rect'];label=f"focus {index}: {focus['reason']} / native {rect}"
            cropped.append((label,_crop(base,rect),1))
            manifest.append(dict(label=label,source_rect=rect,scale=1,cropped=rect!=[0,0,w,h],
                                 focus_kind='source',focus_reason=focus['reason']))
            if difference is not None:
                cropped.append((label+' / difference',_crop(difference,rect),1))
                manifest.append(dict(label=label+' / difference',source_rect=rect,scale=1,
                                     cropped=rect!=[0,0,w,h],focus_kind='difference',focus_reason=focus['reason']))
        views=cropped
        layout=fit(views,8)
    else:
        manifest=[dict(label=label,source_rect=[*origin,*im.size],scale=s,cropped=False)
                  for (label,im,s),origin in zip(views,origins)]
    if layout is None:raise PixelArtError('review: native crop cards exceed the contact-sheet budget')
    card_w,card_h,columns,size=layout
    report['facts']['review_views']=manifest
    sheet=Image.new('RGB',size,'#101827');pen=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=12)
    crop_font=ImageFont.load_default(size=10) if 'review_focus' in report['facts'] else None
    pen.text((8,8),'ADVISORY REVIEW - overlays and diagnostics are separate from source art',fill='#E9EDF2',font=font)
    for i,(label,im,s) in enumerate(views):
        x=i%columns*card_w+8;y=i//columns*card_h+40
        manifest[i]['sheet_rect']=[x,y+22,im.width*s,im.height*s]
        if crop_font is not None:
            # Clip each caption to its card, with coordinates on a separate line.
            caption=Image.new('RGB',(card_w-16,22),'#101827');text=ImageDraw.Draw(caption)
            item=manifest[i];title=item['label'].split(' / native')[0]
            if item.get('focus_kind')=='difference':title='difference / '+title
            text.text((0,0),title,fill='#E9EDF2',font=crop_font)
            detail='overview / not native' if item.get('downsampled') else (
                '['+','.join(map(str,item['source_rect']))+'] / 1:1')
            text.text((0,11),detail,fill='#E9EDF2',font=crop_font)
            sheet.paste(caption,(x,y))
        else:pen.text((x,y),label[:100],fill='#E9EDF2',font=font)
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
    difference=None; comparison_report=None;mask=None
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
    return report,_sheet(rgba,ctx,report,difference,change_mask=mask),difference
