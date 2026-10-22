"""Original native artwork and executable editing/assembly controls (Pillow only)."""
import json
from pathlib import Path
import sys
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
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


def rect(x,y,w,h,color):return dict(op='rect',x=x,y=y,w=w,h=h,color=color)
def poly(points,color):return dict(op='polygon',points=points,color=color)
def line(points,color):return dict(op='line',points=points,color=color)
def spec(size,ops,background=None):return dict(version=1,kind='draw',size=size,background=background,operations=ops)


def points_for(size,ops):
    im=render(spec(size,ops))
    return {(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]}


def clipped(size,op,body):
    return dict(op='points',points=[list(p) for p in sorted(points_for(size,[op])&body)],color=op['color'])


def courier():
    size=[128,128];ink='142B3D'
    shapes=[poly([[21,59],[41,43],[78,40],[101,50],[115,65],[99,79],[63,86],[27,76]],'FFFFFF'),
        poly([[43,50],[32,25],[39,23],[69,46]],'FFFFFF'),
        poly([[52,75],[81,105],[98,104],[82,72]],'FFFFFF')]
    body=points_for(size,shapes)
    ops=[poly([[4,61],[15,57],[17,65],[14,71],[6,69]],'C45E42'),
        poly([[7,63],[15,60],[16,65],[13,68]],'F1B765'),
        rect(37,16,2,19,ink),rect(34,16,8,3,'E8AC62'),
        dict(op='mask',points=[list(p) for p in sorted(body)],color='4B8C9D',outline=ink,thickness=2,neighborhood=8)]
    for op in [
        poly([[32,25],[40,25],[62,46],[43,50]],'79B8BD'),
        poly([[37,29],[41,34],[46,49],[43,49]],'D2D5B6'),
        poly([[50,75],[78,77],[98,103],[82,103]],'31576C'),
        poly([[59,79],[66,81],[87,100],[82,99]],'74A9B1'),
        poly([[24,67],[54,69],[98,62],[113,66],[98,78],[63,84],[28,75]],'31576C'),
        poly([[31,54],[44,45],[76,42],[96,50],[89,53],[51,51]],'86BEC2'),
        poly([[93,52],[111,65],[98,72],[83,72]],'5FA0AB'),
        poly([[42,69],[77,68],[89,72],[73,77],[44,76]],'D38A48'),
        rect(49,69,23,2,'F2C37B'),
        poly([[50,49],[76,45],[94,53],[94,63],[55,62]],ink),
        poly([[55,50],[76,48],[89,54],[88,59],[57,59]],'30698C'),
        poly([[56,50],[74,48],[78,50],[58,53]],'A4DDE0'),
        poly([[80,51],[89,55],[88,58],[81,57]],'67BEC8'),
    ]:ops.append(clipped(size,op,body))
    ops.extend([rect(19,58,7,15,ink),rect(21,60,3,10,'DBA664'),
        line([[97,57],[104,62],[99,66]],'B8D8D0'),
        line([[74,80],[86,94]],ink),line([[78,81],[90,95]],'6392A1'),
        rect(34,60,11,7,ink),rect(35,61,3,5,'89B8B9'),rect(40,61,3,5,'89B8B9'),
        rect(63,79,6,2,'A8CAC4'),rect(72,78,4,2,'A8CAC4'),rect(46,40,2,4,'C45E42'),
        rect(37,19,2,7,'86BEC2')])
    return spec(size,ops)


def terrain():
    ops=[poly([[110,0],[147,0],[156,87],[140,166],[154,255],[106,255],[96,167],[109,86]],'354F51'),
        poly([[116,0],[141,0],[150,86],[134,166],[148,255],[112,255],[102,167],[115,86]],'477D89'),
        poly([[123,0],[137,0],[145,89],[128,163],[141,255],[119,255],[109,167],[121,86]],'5E9C9E'),
        rect(0,154,89,28,'A79570'),rect(171,154,85,28,'A79570'),
        rect(0,157,89,3,'C3B087'),rect(171,157,85,3,'C3B087')]
    for y in (6,19,131,207,232):
        x=120 if y<70 else 117
        ops.extend([rect(x,y,9,1,'93BAB1'),rect(x+3,y+4,12,1,'396675')])
    for x,y in ((14,80),(29,135),(185,132),(235,198),(52,197),(82,230),(165,224),(198,13)):
        ops.extend([rect(x,y,5,2,'6F8958'),rect(x+3,y-3,2,3,'7C955F'),rect(x+7,y+1,3,1,'405C48')])
    for x in (7,32,61,184,212,242):
        ops.extend([rect(x,163,9,2,'897C60'),rect(x+5,173,7,2,'B9A984')])
    return spec([256,256],ops,'596F50')


def mill():
    ink='303B3E'
    roof=points_for([144,116],[poly([[9,44],[34,7],[106,7],[136,44]],'FFFFFF')])
    ops=[rect(16,45,119,64,ink),rect(18,47,115,58,'C8B68D'),rect(96,47,37,58,'AD9873'),
        rect(16,105,119,8,'5C6662'),rect(18,106,115,2,'9DA28D'),rect(19,110,111,2,'3E4C4D'),
        dict(op='mask',points=[list(p) for p in sorted(roof)],color='81594E',outline=ink,neighborhood=8,thickness=2)]
    for y in (15,24,33,42):
        ops.append(clipped([144,116],rect(12,y,121,2,'B78363'),roof))
        for x in range(25+(y%2)*4,129,16):ops.append(clipped([144,116],rect(x,y,1,8,'5B4845'),roof))
    ops.extend([rect(29,58,26,22,ink),rect(31,60,22,18,'52818B'),rect(31,60,22,3,'A2BCB1'),
        rect(41,60,2,18,'8D795D'),rect(31,68,22,2,'8D795D'),
        rect(94,58,26,22,ink),rect(96,60,22,18,'52818B'),rect(96,60,22,3,'A2BCB1'),
        rect(106,60,2,18,'8D795D'),rect(96,68,22,2,'8D795D'),
        rect(66,69,23,36,ink),rect(68,71,19,34,'705A49'),rect(70,73,2,30,'967556'),rect(82,73,2,30,'514B42'),
        rect(82,86,2,3,'D9B76C'),rect(61,105,33,3,'A3A18B'),
        rect(101,0,11,18,ink),rect(103,2,7,14,'A29A7D'),rect(100,0,13,3,'C4B595'),
        poly([[2,72],[12,62],[27,62],[38,73],[38,91],[27,103],[12,103],[2,91]],ink),
        poly([[5,74],[14,65],[25,65],[35,75],[35,90],[25,100],[14,100],[5,90]],'8C694A'),
        line([[7,77],[32,88]],'C29B69'),line([[7,88],[31,74]],'C29B69'),line([[19,66],[19,99]],'C29B69'),
        rect(15,79,9,9,'414A47'),rect(17,81,5,5,'A4A18A'),rect(1,103,38,3,'405451')])
    return spec([144,116],ops)


def bridge():
    ops=[rect(7,8,82,45,'3D4945'),rect(9,10,78,39,'A98A5E')]
    for x in range(10,87,8):ops.extend([rect(x,12,6,34,'C4A374'),rect(x,46,7,2,'7D684C')])
    ops.extend([rect(2,3,92,5,'4E4E40'),rect(2,3,92,2,'C1B58A'),rect(2,51,92,5,'4E4E40'),rect(2,51,92,2,'C1B58A')])
    for x in (3,24,46,68,89):ops.extend([rect(x,1,3,11,'6A6248'),rect(x,49,3,10,'6A6248')])
    return spec([96,60],ops)


def decorations():
    ops=[]
    for x,y in ((9,12),(55,28),(14,94),(14,204),(203,211)):
        ops.extend([rect(x+10,y+22,5,11,'394B3D'),rect(x+11,y+23,2,8,'887454'),
            poly([[x,y+13],[x+5,y+3],[x+15,y],[x+25,y+6],[x+27,y+17],[x+20,y+26],[x+8,y+25]],'304C40'),
            poly([[x+2,y+12],[x+7,y+5],[x+15,y+2],[x+23,y+8],[x+20,y+17],[x+10,y+19]],'729061'),
            poly([[x+6,y+8],[x+11,y+4],[x+18,y+5],[x+16,y+9]],'9EA66A')])
    for x,y in ((179,195),(199,191),(179,214)):
        ops.extend([rect(x,y,17,15,'434B40'),rect(x+1,y+1,15,13,'9E7C51'),rect(x+2,y+2,13,2,'CEAD73'),
            line([[x+2,y+4],[x+13,y+11]],'675C43'),line([[x+13,y+4],[x+2,y+11]],'675C43')])
    for x,y in ((74,133),(174,132)):
        ops.extend([rect(x,y,2,15,'394B43'),rect(x-2,y-4,6,6,'3C4840'),rect(x-1,y-3,4,4,'E5BC70')])
    return spec([256,256],ops)


def icons():
    ink='D8E3ED';images=[]
    for name in ('add','refresh','transfer','lock'):
        im=Image.new('RGBA',(16,16));pen=ImageDraw.Draw(im)
        if name=='add':pen.rectangle((7,3,8,12),fill='#'+ink);pen.rectangle((3,7,12,8),fill='#'+ink)
        elif name=='refresh':
            pen.line([(10,3),(6,3),(3,6),(3,10),(6,13),(10,13),(13,10)],fill='#'+ink,width=2)
            pen.polygon([(9,1),(13,4),(9,7)],fill='#'+ink)
        elif name=='transfer':
            pen.rectangle((3,7,10,8),fill='#'+ink);pen.polygon([(10,4),(13,7),(10,11)],fill='#'+ink)
        else:
            pen.rectangle((5,3,10,8),fill='#'+ink);pen.rectangle((7,5,8,8),fill=(0,0,0,0))
            pen.rectangle((4,8,11,13),fill='#'+ink);pen.rectangle((7,10,8,11),fill=(0,0,0,0))
        images.append(dict(name=name,spec=image_to_spec(im)))
    before=dict(version=1,kind='atlas',columns=4,cells=images)
    im=Image.new('RGBA',(16,16));pen=ImageDraw.Draw(im)
    pen.rectangle((3,4,10,5),fill='#'+ink);pen.polygon([(10,2),(13,5),(10,7)],fill='#'+ink)
    pen.rectangle((5,10,12,11),fill='#'+ink);pen.polygon([(5,8),(2,11),(5,13)],fill='#'+ink)
    return before,image_to_spec(im)


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
