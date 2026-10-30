"""Four coherent original icons; one palette role and stable named layout."""
from _common import emit,entry,asset_files,parser
from PIL import Image,ImageDraw
from pixelart import image_to_spec


def make_specs(ink='D8E3ED'):
    images=[]
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
    cli=parser(__doc__);cli.add_argument('--ink',default='D8E3ED');args=cli.parse_args()
    before,replacement=make_specs(args.ink)
    files=asset_files(before);files['transfer-replacement.json']=replacement
    emit(args,files)


if __name__=='__main__':entry(main)
