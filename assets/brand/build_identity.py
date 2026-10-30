"""Build selected A identity with the released Skill; font is a build-only input.

Editable point specifications retain every glyph, so the resulting headers can
be rendered without installing a font. Only PNG icons enter the standalone Skill.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
ZH_TEXT='面向 AI 的像素绘图与精确编辑'


def english_header(theme):
    """Use the selected, editable geometry rather than private draft scripts."""
    base=ROOT/'assets/brand/identity'
    spec=json.loads((base/f'header-en-{theme}.json').read_text(encoding='utf-8'))
    layouts=json.loads((base/'text-layout.json').read_text(encoding='utf-8'))
    text=next(item['text'] for item in layouts
              if item['language']=='en' and item['theme']==theme)
    return spec,text


def mapped_glyphs(path, text):
    """Read sfnt Unicode cmap directly; refuse .notdef before rasterizing."""
    raw=path.read_bytes()
    u16=lambda n:struct.unpack_from('>H',raw,n)[0]
    u32=lambda n:struct.unpack_from('>I',raw,n)[0]
    tables={raw[12+i*16:16+i*16]:u32(20+i*16) for i in range(u16(4))}
    base=tables[b'cmap']
    subtables=[base+u32(base+4+i*8+4) for i in range(u16(base+2))
               if u16(base+4+i*8) in (0,3)]
    result={}
    for char in sorted(set(text)):
        code=ord(char);glyph=0
        for offset in subtables:
            fmt=u16(offset)
            if fmt==12:
                for group in range(u32(offset+12)):
                    start,end,first=struct.unpack_from('>III',raw,offset+16+group*12)
                    if start<=code<=end:
                        glyph=first+code-start;break
            elif fmt==4 and code<=65535:
                count=u16(offset+6)//2
                ends=offset+14;starts=ends+count*2+2
                deltas=starts+count*2;ranges=deltas+count*2
                for index in range(count):
                    start,end=u16(starts+index*2),u16(ends+index*2)
                    if start<=code<=end:
                        delta=u16(deltas+index*2);distance=u16(ranges+index*2)
                        if distance==0: glyph=(code+delta)%65536
                        else:
                            address=ranges+index*2+distance+(code-start)*2
                            glyph=u16(address)
                            if glyph:glyph=(glyph+delta)%65536
                        break
            if glyph:break
        if not glyph:raise ValueError(f'Font has no mapped glyph for U+{code:04X} {char!r}')
        result[char]=glyph
    return result


def chinese_label(path, text, x,y,color):
    font=ImageFont.truetype(str(path),12)
    bb=font.getbbox(text)
    mask=Image.new('1',(bb[2]-bb[0],bb[3]-bb[1]))
    ImageDraw.Draw(mask).text((-bb[0],-bb[1]),text,font=font,fill=1)
    ink=mask.getbbox();assert ink
    points=[[x+xx,y+yy] for yy in range(mask.height) for xx in range(mask.width) if mask.getpixel((xx,yy))]
    return dict(op='points',points=points,color=color),dict(
        text=text,ink=[x+ink[0],y+ink[1],ink[2]-ink[0],ink[3]-ink[1]],
        mask_origin=[x,y],font_size=12,font='Fusion Pixel Font / zh_hans',
        font_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill',required=True,type=Path)
    parser.add_argument('--font',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--evidence',required=True,type=Path)
    args=parser.parse_args()
    if args.out.exists():parser.error('Use a fresh output directory; preserve reviewed art.')
    mappings=mapped_glyphs(args.font,ZH_TEXT)
    log=args.evidence/'identity-commands.jsonl'
    if log.exists():parser.error('This build has an existing command log.')
    args.evidence.mkdir(parents=True,exist_ok=True)
    args.out.mkdir(parents=True)
    layouts=[]
    def call(*arguments):
        command=[sys.executable,'-X','utf8','-B',str(args.skill/'scripts/pixel_art.py'),*map(str,arguments)]
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
        with log.open('a',encoding='utf-8') as out:
            out.write(json.dumps(dict(command=command,returncode=result.returncode,
                stdout=result.stdout,stderr=result.stderr),ensure_ascii=False)+'\n')
        if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    for language in ('en','zh-CN'):
        for theme in ('dark','light'):
            spec,boxes=english_header(theme)
            if language=='zh-CN':
                text_ops=[i for i,o in enumerate(spec['operations']) if o['op']=='points']
                color=spec['operations'][text_ops[-1]]['color']
                operation,description=chinese_label(args.font,ZH_TEXT,112,79,color)
                spec['operations'][text_ops[-1]]=operation
                boxes[-1]=description
            stem=f'header-{language}-{theme}'
            spec_path=args.out/(stem+'.json')
            spec_path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            png=args.out/(stem+'-native.png')
            call('render','--spec',spec_path,'--out',png)
            call('preview','--image',png,'--out',args.out/(stem+'.png'),'--scale',3,
                 '--background',spec['background'])
            layouts.append(dict(language=language,theme=theme,native_size=[384,112],
                                exported_size=[1152,336],text=boxes))
    for size in (32,128):
        name=f'icon-{size}.json'
        spec=ROOT/'assets/brand/identity'/name
        (args.out/name).write_bytes(spec.read_bytes())
        call('render','--spec',spec,'--out',args.out/f'icon-{size}.png')
    (args.out/'text-layout.json').write_text(json.dumps(layouts,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.evidence/'glyph-mappings.json').write_text(json.dumps(mappings,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.evidence/'identity-build-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(headers=4,icons=2,calls=10,characters=len(mappings),output=str(args.out)),ensure_ascii=False))


if __name__=='__main__':main()
