"""Package a single Linux portability trial using an explicitly frozen Skill ZIP."""
import argparse
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw
from build_long_term_trials import ROOT, encoded, frozen_files
from prepare_agent_trials import archive_bytes, sha

EXPECTED='5c206399714545f445e9e93fd5c1b227a6f1cab677cc8a45a43b86c19a313768'


def png(image, **kwargs):
    buffer=BytesIO();image.save(buffer,format='PNG',**kwargs)
    return buffer.getvalue()


def inputs():
    rgba=Image.new('RGBA',(16,16),(17,31,47,0))
    pen=ImageDraw.Draw(rgba)
    pen.polygon([(4,3),(12,8),(4,12)],fill=(229,236,238,255))
    pen.rectangle((2,6,3,9),fill=(75,174,190,128))
    rgb=Image.new('RGB',(20,16))
    rgb.putdata([((x*11+y*3)%256,(x*5+y*13)%256,(x*17+y*7)%256) for y in range(16) for x in range(20)])
    indexed=Image.new('P',(12,12))
    indexed.putpalette([19,43,61,229,236,238,75,174,190,114,204,198]+[0]*756)
    indexed.putdata([0 if x in (0,11) or y in (0,11) else 1+(x+y)%3 for y in range(12) for x in range(12)])
    return {'inputs/rgba.png':png(rgba),'inputs/rgb.png':png(rgb),
            'inputs/indexed.png':png(indexed,transparency=bytes([0,255,128,255]))}


def build(skill_zip,out,expected=EXPECTED):
    files=frozen_files(skill_zip,expected)
    count=len(files)
    files.update({'START_HERE.md':(ROOT/'benchmarks/long-term/LT03.md').read_bytes(),
                  'run.py':(ROOT/'benchmarks/long-term/linux_runner.py').read_bytes(),
                  'recorder.py':(ROOT/'benchmarks/long-term/runner.py').read_bytes(),
                  'task.json':encoded(dict(id='LT03',skill_zip_sha256=expected)),
                  'inputs/panel.json':files['deterministic-pixel-art/assets/quality/ui-panel.json'],
                  'inputs/panel-context.json':files['deterministic-pixel-art/assets/quality/contexts/ui-panel.json']})
    files.update(inputs())
    files['checksums.json']=encoded({name:sha(data) for name,data in sorted(files.items())})
    payload=archive_bytes({'LT03/'+name:data for name,data in files.items()})
    out.mkdir(parents=True,exist_ok=False)
    (out/'LT03-Linux.zip').write_bytes(payload)
    record=dict(task='LT03',recommended_environment='Qwen office assistant, Linux, fresh session',
                archive='LT03-Linux.zip',bytes=len(payload),sha256=sha(payload),
                skill_zip_sha256=expected,skill_files=count,packet_files=len(files),external_runs=0)
    coordinator=out/'coordinator';coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(record))
    (coordinator/'SHA256SUMS.txt').write_text(sha(payload)+'  LT03-Linux.zip\n',encoding='ascii')
    return record


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--skill-zip',type=Path,required=True)
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--sha256',default=EXPECTED)
    args=cli.parse_args()
    print(json.dumps(build(args.skill_zip,args.out,args.sha256),indent=2))
