"""Local drawing primitives/materials only; never creates or cuts a full scene."""
import argparse
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pixelart import render,PixelArtError
from pixelart.core import color
from pixelart.metadata import layout_record
from pixelart.output import publish


def contract():return json.loads((HERE/'contract.json').read_text(encoding='utf-8'))


class Drawing:
    def __init__(self,name,agreement):
        self.name=name;self.palette=agreement['palette'];self.origin=agreement['chunks'][name][:2];self.ops=[]

    def ink(self,role):return self.palette.get(role,role)
    def r(self,x,y,w,h,role):self.ops.append(dict(op='rect',x=x,y=y,w=w,h=h,color=self.ink(role)))
    def p(self,points,role):self.ops.append(dict(op='polygon',points=points,color=self.ink(role)))
    def l(self,points,role):self.ops.append(dict(op='line',points=points,color=self.ink(role)))
    def spec(self):return dict(version=1,kind='draw',size=[128,128],background=self.palette['ground'],operations=self.ops)

    def paving(self,x,y,w,h):
        """Small repeating material with global phase, bounded to this local rectangle."""
        self.r(x,y,w,h,'stone')
        ox,oy=self.origin
        for yy in range(y,y+h):
            gy=oy+yy
            if gy%8==0:self.r(x,yy,w,1,'mortar')
            elif gy%8==1:self.r(x,yy,w,1,'stone_light')
        for yy in range(y,y+h):
            offset=(8 if ((oy+yy)//8)%2 else 0)
            for xx in range(x,x+w):
                if (ox+xx-offset)%16==0:self.r(xx,yy,1,1,'mortar')

    def deck(self,x,y,w,h):
        self.r(x,y,w,h,'wood')
        ox,oy=self.origin
        for xx in range(x,x+w):
            if (ox+xx-100)%8==0:self.r(xx,y,1,h,'wood_dark')
            elif (ox+xx-100)%8==1:self.r(xx,y,1,h,'wood_light')
        for yy in range(y,y+h):
            if (oy+yy-118)%8==0:
                for xx in range(x,x+w):
                    if (ox+xx-100)%8 in (3,4,5):self.r(xx,yy,1,1,'wood_light')

    def house(self,x,y,w,h,roof='roof'):
        """Reusable prop, six visible wall pixels; caller owns placement."""
        rh=h-6
        self.r(x+4,y+8,w,h-4,'shadow')
        self.r(x+3,y+rh,w-6,6,'outline');self.r(x+4,y+rh,w-8,5,'wall')
        self.r(x+w-8,y+rh,4,5,'wall_dark')
        self.r(x+w//2-3,y+rh,6,6,'wood_dark')
        for xx in (x+9,x+w-14):
            self.r(xx,y+rh+1,5,3,'outline');self.r(xx+1,y+rh+1,3,2,'water_light')
        self.p([[x+6,y],[x+w-7,y],[x+w-1,y+10],[x+w-1,y+rh-1],[x,y+rh-1],[x,y+10]],'outline')
        self.p([[x+7,y+1],[x+w-8,y+1],[x+w-3,y+rh//2],[x+w-2,y+rh-3],[x+2,y+rh-3],[x+2,y+rh//2]],roof)
        self.p([[x+7,y+1],[x+w-8,y+1],[x+w-4,y+rh//2-1],[x+3,y+rh//2-1]],'roof_light')
        self.r(x+4,y+rh//2,w-8,2,'roof_dark')
        for yy in range(y+5,y+rh-3,7):
            self.l([[x+8,yy],[x+w-9,yy]],'roof_dark')
        self.r(x+w//2-5,y+h,10,2,'stone_light')

    def crate(self,x,y,w=14,h=12):
        self.r(x+2,y+2,w,h,'shadow');self.r(x,y,w,h,'outline')
        self.r(x+1,y+1,w-2,h-2,'wood');self.r(x+2,y+1,w-4,2,'wood_light')
        self.l([[x+2,y+3],[x+w-3,y+h-3]],'wood_dark')
        self.l([[x+w-3,y+3],[x+2,y+h-3]],'wood_dark')

    def barrel(self,x,y):
        self.p([[x+2,y],[x+9,y],[x+11,y+3],[x+11,y+13],[x+9,y+16],[x+2,y+16],[x,y+13],[x,y+3]],'outline')
        self.r(x+2,y+2,8,13,'wood');self.r(x+2,y+2,2,12,'wood_light')
        self.r(x+1,y+4,10,2,'metal');self.r(x+1,y+11,10,2,'metal')
        self.r(x+4,y+1,4,2,'wood_dark')

    def tufts(self,positions):
        for x,y in positions:
            self.l([[x,y+2],[x+2,y+3],[x+4,y+1]],'ground_dark')
            self.r(x+2,y,2,1,'ground_light')


def entry(name,make_spec,*,flag=False):
    cli=argparse.ArgumentParser(description=f'Independently render the {name} 128px chunk; no assembled image is read.')
    cli.add_argument('--out-dir',type=Path,required=True);cli.add_argument('--force',action='store_true')
    cli.add_argument('--portable-output',action='store_true')
    if flag:cli.add_argument('--flag',default='E4BB6B',help='NE depot flag color only.')
    args=cli.parse_args()
    try:
        data=make_spec(contract(),**({'flag':args.flag} if flag else {}));image=render(data)
        publish({args.out_dir/f'{name}.json':data,args.out_dir/f'{name}.png':image,
            args.out_dir/f'{name}-layout.json':layout_record(image)},force=args.force,portable=args.portable_output)
        print(json.dumps(dict(chunk=name,size=list(image.size),out_dir=str(args.out_dir))))
    except (OSError,ValueError) as exc:
        print(json.dumps(dict(error=str(exc))),file=sys.stderr);raise SystemExit(2)
