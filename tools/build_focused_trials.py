"""Build three small platform follow-ups from a frozen Skill ZIP; never run agents."""
import argparse
from io import BytesIO
import json
from pathlib import Path,PurePosixPath
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from PIL import Image,ImageDraw
from pixelart import render
from pixelart.metadata import layout_record
from prepare_agent_trials import archive_bytes,sha


def json_bytes(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def png(image):
    buffer=BytesIO();image.save(buffer,format='PNG');return buffer.getvalue()


def hover_inputs():
    names=['normal','hover','focus','pressed','selected','disabled']
    image=Image.new('RGBA',(96,36));draw=ImageDraw.Draw(image);cells=[]
    for i,name in enumerate(names):
        x=i%3*32;y=i//3*18
        draw.rectangle((x+1,y+1,x+30,y+16),fill='#395168')
        draw.rectangle((x+2,y+2,x+29,y+2),fill='#7895A9')
        draw.rectangle((x+2,y+15,x+29,y+15),fill='#1D3044')
        cells.append(dict(name=name,x=x,y=y,w=32,h=18))
    image.info['pixelart']=dict(cell_size=[32,18],columns=3,rows=2,cells=cells)
    mask=Image.new('L',image.size);pen=ImageDraw.Draw(mask);pen.rectangle((32,0,63,17),outline=255,width=1)
    return {'inputs/hover.png':png(image),'inputs/hover-layout.json':json_bytes(layout_record(image)),
            'inputs/allowed-ring.png':png(mask)}


def build(skill_zip,expected,out):
    payload=skill_zip.read_bytes()
    if sha(payload)!=expected.lower():raise ValueError('Skill ZIP SHA-256 mismatch')
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        infos=[item for item in archive.infolist() if not item.is_dir()]
        if sum(item.file_size for item in infos)>16*1024*1024:raise ValueError('Skill ZIP exceeds size budget')
        names=[item.filename for item in infos]
        if len(set(names))!=len(names):raise ValueError('Duplicate ZIP entries')
        for name in names:
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe Skill ZIP path')
            if path.parts[0]!='deterministic-pixel-art':raise ValueError('Unexpected Skill ZIP root')
        frozen={name:archive.read(name) for name in names}
    prefix='deterministic-pixel-art/'
    required=[prefix+'scripts/pixelart/edit.py',prefix+'assets/workflows/atlas-before.png',
        prefix+'assets/workflows/atlas-before-layout.json',prefix+'assets/quality/materials-32.json']
    if not all(name in frozen for name in required):raise ValueError('Expected named-editing candidate Skill resources')
    if out.exists():raise ValueError('Output directory exists; choose a new distribution directory')
    out.mkdir(parents=True)
    material=render(json.loads(frozen[prefix+'assets/quality/materials-32.json']))
    metal=next(cell for cell in material.info['pixelart']['cells'] if cell['name']=='metal')
    common={'run.py':(ROOT/'benchmarks/focused/runner.py').read_bytes(),**frozen}
    summary=[]
    for task_id,label in [('P1-W','DeepSeek'),('P1-C','Qwen'),('P1-V','Gemini')]:
        config=dict(id=task_id,platform=label,skill_zip_sha256=expected.lower(),
            type='focused regression and open feedback; not controlled A/B or independent aesthetic proof')
        files=dict(common)
        if task_id=='P1-W':
            files.update({'inputs/atlas.png':frozen[prefix+'assets/workflows/atlas-before.png'],
                'inputs/layout.json':frozen[prefix+'assets/workflows/atlas-before-layout.json'],**hover_inputs()})
        elif task_id=='P1-C':
            files['inputs/panel.json']=frozen[prefix+'assets/generic-panel-96x40.json']
        else:
            files.update({'inputs/materials.png':png(material),'inputs/layout.json':json_bytes(layout_record(material)),
                'inputs/context.json':json_bytes(dict(asset_type='sprite',primary_background='light',
                    backgrounds=[dict(name='light',color='E9EDF2'),dict(name='target',color='FFFFFF')]))})
            config['allowed_region']=[metal[k] for k in ('x','y','w','h')]
        files['task.json']=json_bytes(config)
        files['START_HERE.md']=(ROOT/'benchmarks/focused'/f'{task_id}.md').read_bytes()
        files['checksums.json']=json_bytes({name:sha(data) for name,data in sorted(files.items())})
        contents={task_id+'/'+name:data for name,data in files.items()}
        name=f'{task_id}-{label}.zip';data=archive_bytes(contents);(out/name).write_bytes(data)
        summary.append(dict(task=task_id,platform=label,archive=name,sha256=sha(data),bytes=len(data),
            external_agent_executed=False))
    (out/'manifest.json').write_bytes(json_bytes(dict(skill_zip_sha256=expected.lower(),trials=summary)))
    (out/'SHA256SUMS.txt').write_text(''.join(f"{item['sha256']}  {item['archive']}\n" for item in summary),encoding='ascii')
    print(json.dumps(dict(prepared=3,external_runs=0,out=str(out),trials=summary),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-zip',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    try:build(args.skill_zip,args.sha256,args.out)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        print(json.dumps(dict(error=str(exc))),file=sys.stderr);raise SystemExit(2)
