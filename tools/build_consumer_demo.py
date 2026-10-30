"""Build repository-only browser demo assets from the maintained recipes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'recipes')]
from pixelart import PixelArtError,render
from pixelart.metadata import layout_record
from pixelart.output import encoded,publish
import buttons,courier128,icons

DEMO=ROOT/'demos/pixel-ui'


def build(config):
    if not isinstance(config,dict) or set(config)!={'baseline_width','button_width','hover','labels'}:
        raise PixelArtError('demo config: expected baseline_width, button_width, hover, labels')
    labels=config['labels']
    if not isinstance(labels,dict) or set(labels)!={'run','loop','export'} or any(
        not isinstance(value,str) or not value or len(value)>32 or any(ord(c)<32 or ord(c)>126 for c in value)
        for value in labels.values()):
        raise PixelArtError('labels: expected run/loop/export with 1..32 printable ASCII characters; bundled font coverage is Latin')
    files={}
    for variant,key in [('baseline','baseline_width'),('revised','button_width')]:
        width=config[key]
        if type(width) is not int or not 38<=width<=256:raise PixelArtError(key+': expected integer 38..256')
        generated=buttons.make_files(width=width,hover=config['hover'],content=[28,4,width-34,10])
        for source,target in [('asset.png','buttons.png'),('asset.json','buttons.json'),
                              ('layout.json','layout.json'),('context.json','context.json')]:
            files[variant+'/'+target]=generated[source]
    courier=render(courier128.make_spec(stripe='E17B57',stripe_light='F9D5A0'))
    icon_spec=icons.make_specs('F5C26B')[0];icon_image=render(icon_spec)
    files.update({'courier.png':courier,'icons.png':icon_image,'icons.json':icon_spec,'icons-layout.json':layout_record(icon_image)})
    payloads={name:encoded(value) for name,value in files.items()}
    font_source=json.loads((DEMO/'fonts/source.json').read_text(encoding='utf-8'))
    for record in font_source['files']:
        if hashlib.sha256((DEMO/'fonts'/record['file']).read_bytes()).hexdigest()!=record['sha256']:
            raise PixelArtError('Bundled font/license differs from recorded provenance')
    manifest=dict(version=1,labels=labels,font=dict(family='Silkscreen',size=8,license='SIL Open Font License 1.1',
        sha256=font_source['files'][0]['sha256']),
        variants={name:dict(width=config[key],height=18,columns=3,states=list(buttons.STATES))
                  for name,key in [('baseline','baseline_width'),('revised','button_width')]},
        source_recipes={name:hashlib.sha256((ROOT/'recipes'/name).read_bytes()).hexdigest()
                        for name in ('buttons.py','courier128.py','icons.py','_common.py')},
        parameters=dict(buttons=config,courier=dict(stripe='E17B57',stripe_light='F9D5A0'),icons=dict(ink='F5C26B')),
        assets={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in sorted(payloads.items())},
        scope='Browser consumer demonstration; no Minecraft font or in-game acceptance.')
    payloads['manifest.json']=encoded(manifest)
    return payloads


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--config',type=Path,default=DEMO/'demo.json')
    cli.add_argument('--out-dir',type=Path,default=DEMO/'assets')
    cli.add_argument('--force',action='store_true')
    cli.add_argument('--portable-output',action='store_true')
    args=cli.parse_args()
    files=build(json.loads(args.config.read_text(encoding='utf-8')))
    publish({args.out_dir/name:value for name,value in files.items()},force=args.force,portable=args.portable_output)
    print(json.dumps(dict(out_dir=str(args.out_dir),files=len(files),variants=['baseline','revised'])))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError) as exc:
        print(json.dumps(dict(error=str(exc))),file=sys.stderr);raise SystemExit(2)
