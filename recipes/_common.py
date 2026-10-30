"""Shared mechanics for editable recipes; no output writes at import time."""
import argparse
import json
from pathlib import Path
import sys

RUNTIME=Path(__file__).resolve().parents[1]
if not (RUNTIME/'pixelart').is_dir():RUNTIME=RUNTIME/'src'
sys.path.insert(0,str(RUNTIME))
try:
    from pixelart import PixelArtError,render,make_preview
    from pixelart.core import color
    from pixelart.metadata import layout_record
    from pixelart.output import add_output_options, publish, resolve_portable_output
except ImportError as exc:
    raise SystemExit('Recipes need Python 3.10+ and Pillow>=10.4,<13. Install the Skill requirements.txt in your task environment.') from exc


def rect(x,y,w,h,color):return dict(op='rect',x=x,y=y,w=w,h=h,color=color)
def poly(points,color):return dict(op='polygon',points=points,color=color)
def line(points,color):return dict(op='line',points=points,color=color)
def spec(size,ops,background=None):return dict(version=1,kind='draw',size=size,background=background,operations=ops)


def points_for(size,ops):
    image=render(spec(size,ops))
    return {(x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y))[3]}


def clipped(size,op,body):
    return dict(op='points',points=[list(p) for p in sorted(points_for(size,[op])&body)],color=op['color'])


def parser(description):
    result=argparse.ArgumentParser(description=description)
    result.add_argument('--out-dir',type=Path,required=True)
    result.add_argument('--force',action='store_true',help='Explicitly replace this recipe\'s existing outputs.')
    add_output_options(result)
    return result


def asset_files(data,*,background='243449',context=None):
    image=render(data)
    files={'asset.json':data,'asset.png':image,'layout.json':layout_record(image),
        'preview.png':make_preview(image,3,background)}
    if context is not None:files['context.json']=context
    return files


def emit(args,files):
    publish({args.out_dir/name:value for name,value in files.items()},force=args.force,
            portable=resolve_portable_output(args.portable_output))
    print(json.dumps(dict(out_dir=str(args.out_dir),files=sorted(files),
        note='Editable recipe output; inspect at native size. No automatic aesthetic acceptance.')))


def entry(main):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    try:main()
    except (OSError,ValueError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
