"""Original native artwork and executable editing/assembly controls (Pillow only)."""
import json
from pathlib import Path
import sys
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'recipes'))
from pixelart import render,image_to_spec,replace_cell,verify_edit,make_preview
from pixelart.metadata import layout_record
from pixelart.review import review
from pixelart.assembly import assemble,seam_sheet

OUT=ROOT/'examples/workflows'
CHECK=ROOT/'evaluation/workflows'
DOC=ROOT/'docs/workflows'


def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


from courier128 import make_spec as courier
from scene256 import terrain,mill,bridge,decorations
from icons import make_specs as icons
from _common import spec


def main():
    OUT.mkdir(parents=True,exist_ok=True);CHECK.mkdir(parents=True,exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
    sprite=courier();save_json(OUT/'sprite-128.json',sprite);sprite_image=render(sprite)
    sprite_image.save(OUT/'sprite-128.png')
    make_preview(sprite_image,3,'243449').save(DOC/'sprite-128-preview.png')
    ctx=dict(asset_type='sprite',backgrounds=[dict(name='target',color='243449')])
    save_json(OUT/'sprite-context.json',ctx)
    report,sheet,_=review(sprite_image,ctx);sheet.save(CHECK/'sprite-review.png');save_json(CHECK/'sprite-review.json',report)
    pieces={'terrain':(terrain(),[0,0]),'mill':(mill(),[104,18]),'bridge':(bridge(),[80,140]),'details':(decorations(),[0,0])}
    parts=[];sources={};control_ops=[]
    for name,(data,at) in pieces.items():
        save_json(OUT/f'scene/{name}.json',data);im=render(data);im.save(OUT/f'scene/{name}.png')
        relative=f'scene/{name}.png';sources[relative]=im
        parts.append(dict(name=name,image=relative,at=at,mode='copy' if name=='terrain' else 'over',allow_overlap=name!='terrain'))
        control_ops.append(dict(op='blit',x=at[0],y=at[1],source=data))
    project=dict(version=1,size=[256,256],require_coverage=True,parts=parts)
    save_json(OUT/'scene-components.json',project)
    scene,assembly=assemble(project,sources);scene.save(OUT/'scene-256.png');save_json(CHECK/'scene-assembly.json',assembly)
    make_preview(scene,2).save(DOC/'scene-256-preview.png')
    control=spec([256,256],control_ops);save_json(OUT/'scene-control.json',control)
    assert render(control).tobytes()==scene.tobytes()
    tiles=[];tile_sources={}
    for name,x,y in [('nw',0,0),('ne',128,0),('sw',0,128),('se',128,128)]:
        im=scene.crop((x,y,x+128,y+128));path=f'tiles/{name}.png'
        save_json(OUT/f'tiles/{name}.json',image_to_spec(im));im.save(OUT/path);tile_sources[path]=im
        tiles.append(dict(name=name,image=path,at=[x,y],mode='copy'))
    tiled=dict(version=1,size=[256,256],require_coverage=True,parts=tiles);save_json(OUT/'scene-tiles.json',tiled)
    rebuilt,tile_report=assemble(tiled,tile_sources);assert rebuilt.tobytes()==scene.tobytes()
    seam_sheet(rebuilt,tile_report).save(CHECK/'scene-seams.png');save_json(CHECK/'scene-tiles-report.json',tile_report)
    review(scene,dict(asset_type='general'))[1].save(CHECK/'scene-review.png')
    before,replacement=icons();save_json(OUT/'atlas-before.json',before);save_json(OUT/'atlas-replacement.json',replacement)
    im=render(before);im.save(OUT/'atlas-before.png');metadata=layout_record(im);save_json(OUT/'atlas-before-layout.json',metadata)
    imported=image_to_spec(im,metadata=metadata);save_json(OUT/'atlas-editable.json',imported)
    edited=replace_cell(imported,'transfer',replacement);save_json(OUT/'atlas-final.json',edited)
    final=render(edited);final.save(OUT/'atlas-final.png');save_json(OUT/'atlas-final-layout.json',layout_record(final))
    pair=Image.new('RGBA',(64,36));pair.paste(im,(0,0));pair.paste(final,(0,20))
    make_preview(pair,6,'172033').save(DOC/'atlas-edit-preview.png')
    edit_report=verify_edit(final,im,regions=[[32,0,16,16]]);assert edit_report['valid']
    save_json(CHECK/'atlas-edit-verification.json',edit_report)
    result=dict(sprite_native_size=list(sprite_image.size),scene_native_size=list(scene.size),
        component_control_exact=True,tile_reassembly_exact=True,tile_seams=tile_report['seam_count'],
        edit_verification=edit_report,review='Author agent visual review; not independent or game/runtime acceptance.')
    save_json(CHECK/'results.json',result)
    print(json.dumps(result))


if __name__=='__main__':main()
