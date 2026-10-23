"""Build four separately authored local chunks, then assemble; no full-scene input."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'demos/chunk-scene'
sys.path[:0]=[str(ROOT/'src'),str(DEMO)]
from PIL import Image,ImageDraw,ImageOps
from pixelart import render,make_preview,PixelArtError
from pixelart.core import color
from pixelart.metadata import rgba_digest,layout_record
from pixelart.assembly import assemble,seam_sheet
from pixelart.output import encoded,publish
import chunk_nw,chunk_ne,chunk_sw,chunk_se

AUTHORS={'nw':chunk_nw,'ne':chunk_ne,'sw':chunk_sw,'se':chunk_se}


def check_edges(images,agreement):
    """Check predeclared material/phase contracts, not aesthetic correctness."""
    palette=agreement['palette'];issues=[];checked=0
    def sample(x,y):return images[('n' if y<128 else 's')+('w' if x<128 else 'e')].getpixel((x%128,y%128))
    def expect(x,y,roles):
        nonlocal checked
        checked+=1;allowed={color(palette[role]) for role in roles}
        if sample(x,y) not in allowed:issues.append(dict(at=[x,y],expected=roles,actual=list(sample(x,y))))
    for y in (*range(112),*range(144,256)):
        for x in (127,128):expect(x,y,['water','water_dark','water_light'])
    for y in (127,128):
        for x in (*range(100),*range(156,256)):expect(x,y,['stone','stone_light','stone_dark','mortar'])
        for x in range(100,156):expect(x,y,['wood','wood_light','wood_dark'])
    for y in agreement['validation']['clear_canal_rows']:
        for x in range(108,148):expect(x,y,['water_dark'] if x<111 or x>=145 else ['water','water_dark','water_light'])
        for x,role in [(100,'stone_light'),(105,'stone_dark'),(106,'outline'),(107,'outline'),
                       (148,'outline'),(149,'outline'),(150,'stone_light'),(155,'stone_dark')]:expect(x,y,[role])
    # Independent anchor expectations, declared before authoring; no pattern-generator call.
    for y,role in ((112,'outline'),(113,'wood_light'),(114,'wood_dark'),(115,'outline'),
                   (140,'outline'),(141,'wood_light'),(142,'wood_dark'),(143,'outline'),
                   (40,'water_light'),(72,'water_light'),(184,'water_light'),(216,'water_light')):
        for x in (127,128):expect(x,y,[role])
    for x in (32,192):
        expect(x,127,['stone']);expect(x,128,['mortar'])
    for y in (127,128):
        expect(124,y,['wood_dark']);expect(125,y,['wood_light']);expect(127,y,['wood']);expect(128,y,['wood'])
    return dict(valid=not issues,checked_pixels=checked,issues=issues,
        note='Frozen material/phase anchors only; does not judge art, light, routes or object identity.')


def sketch(agreement):
    image=Image.new('RGB',(256,256),'#66775A');pen=ImageDraw.Draw(image)
    for name,rect in agreement['structure'].items():
        x,y,w,h=rect
        ink='#356B80' if name=='canal' else '#9B7950' if name.startswith('bridge') else '#A69B7E'
        pen.rectangle((x,y,x+w-1,y+h-1),fill=ink)
    for rect in ((17,22,58,53),(178,27,58,53),(17,167,53,29),(180,190,58,42)):
        x,y,w,h=rect;pen.rectangle((x,y,x+w-1,y+h-1),outline='#E4BB6B',width=1)
    pen.line((128,0,128,255),fill='#F4E3B1');pen.line((0,128,255,128),fill='#F4E3B1')
    return image


def build_files(agreement,*,flag='E4BB6B'):
    files={};images={};source_records={}
    # Each source returns only its own 128px spec. None receives any finished PNG.
    for name,module in AUTHORS.items():
        data=module.make_spec(agreement,**({'flag':flag} if name=='ne' else {}));image=render(data)
        if image.size!=(128,128):raise PixelArtError(f'{name}: expected 128x128 owner')
        images[name]=image
        files[f'chunks/{name}.json']=data;files[f'chunks/{name}.png']=image
        files[f'chunks/{name}-layout.json']=layout_record(image)
        source_records[name]=dict(source=f'chunk_{name}.py',source_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
            rgba_sha256=rgba_digest(image),size=list(image.size),reads_full_scene=False)
    edges=check_edges(images,agreement)
    if not edges['valid']:raise PixelArtError('chunk edge contract failed: '+json.dumps(edges))
    project=dict(version=1,size=[256,256],require_coverage=True,parts=[dict(name=name,image=f'chunks/{name}.png',
        at=agreement['chunks'][name][:2],mode='copy') for name in AUTHORS])
    scene,report=assemble(project,{f'chunks/{name}.png':image for name,image in images.items()})
    files.update({'project.json':project,'scene.png':scene,'layout.json':layout_record(scene),
        'preview.png':make_preview(scene,2),'seams.png':seam_sheet(scene,report),
        'grayscale.png':ImageOps.grayscale(scene).convert('RGB').resize((512,512),Image.Resampling.NEAREST),
        'center.png':scene.crop((116,104,140,152)).resize((192,384),Image.Resampling.NEAREST),
        'assembly.json':report,'edges.json':edges,'layout-sketch.png':sketch(agreement)})
    payloads={name:encoded(value) for name,value in files.items()}
    payloads['manifest.json']=encoded(dict(version=1,scope='One author, four separate local drawings; not multi-agent/blind aesthetic evidence',
        contract_sha256=hashlib.sha256((DEMO/'contract.json').read_bytes()).hexdigest(),
        parameters=dict(depot_flag=flag),
        shared_helpers_sha256=hashlib.sha256((DEMO/'chunk_common.py').read_bytes()).hexdigest(),
        chunks=source_records,scene_rgba_sha256=rgba_digest(scene),
        assets={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in sorted(payloads.items())}))
    return payloads


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out-dir',type=Path,default=DEMO/'assets');cli.add_argument('--force',action='store_true')
    cli.add_argument('--check-chunks',type=Path,help='Read four existing name.png files, check frozen edges, write nothing.')
    cli.add_argument('--flag',default='E4BB6B',help='NE depot flag color; full build refreshes every output together.')
    cli.add_argument('--portable-output',action='store_true');args=cli.parse_args()
    agreement=json.loads((DEMO/'contract.json').read_text(encoding='utf-8'))
    if args.check_chunks:
        images={}
        for name in AUTHORS:
            with Image.open(args.check_chunks/f'{name}.png') as source:
                if source.size!=(128,128) or getattr(source,'n_frames',1)!=1:
                    raise PixelArtError(f'{name}: expected a static 128x128 chunk')
                images[name]=source.convert('RGBA')
        report=check_edges(images,agreement)
        print(json.dumps(report))
        return 0 if report['valid'] else 2
    files=build_files(agreement,flag=args.flag)
    publish({args.out_dir/name:value for name,value in files.items()},force=args.force,portable=args.portable_output)
    print(json.dumps(dict(out_dir=str(args.out_dir),files=len(files),chunks=4,size=[256,256])))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError) as exc:
        print(json.dumps(dict(error=str(exc))),file=sys.stderr);raise SystemExit(2)
