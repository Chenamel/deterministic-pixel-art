"""Six-state buttons with optional reserved text, fixed 18px height and stable names."""
from _common import emit,entry,asset_files,parser,poly,rect,line,spec,render,PixelArtError

STATES=('normal','hover','focus','pressed','selected','disabled')


def make_spec(*,width=32,hover='345D78'):
    if type(width) is not int or not 24<=width<=256:
        raise PixelArtError('width: expected integer 24..256; height stays 18')
    cells=[]
    for state in STATES:
        fill={'hover':hover,'pressed':'192D43','selected':'244F58','disabled':'334151'}.get(state,'263E56')
        border='D9B56C' if state=='focus' else '111E30'
        top='142337' if state=='pressed' else ('586879' if state=='disabled' else '66859B')
        bottom='66859B' if state=='pressed' else '15283D'
        ink='8997A5' if state=='disabled' else 'E5ECEE'
        ops=[rect(0,1,width,16,border),rect(1,0,width-2,18,border),rect(1,2,width-2,14,fill),
             rect(2,1,width-4,1,top),rect(2,16,width-4,1,bottom)]
        if state=='focus':ops += [rect(2,3,width-4,1,'D9B56C'),rect(2,14,width-4,1,'D9B56C')]
        if state=='selected':ops += [rect(2,14,width-4,2,'72CCC6'),line([[4,8],[6,10],[9,6]],'A4E2C8')]
        offset=1 if state=='pressed' else 0
        ops += [poly([[13,5+offset],[20,9+offset],[13,13+offset]],ink)]
        cells.append(dict(name=state,spec=spec([width,18],ops)))
    return dict(version=1,kind='atlas',columns=3,cells=cells)


def make_files(*,width=32,hover='345D78',content=None):
    data=make_spec(width=width,hover=hover);image=render(data)
    context=dict(asset_type='ui',backgrounds=[dict(name='target',color='1D293D')])
    if content is not None:
        if len(content)!=4 or any(type(v) is not int for v in content):
            raise PixelArtError('content: expected x y width height in each cell')
        x,y,w,h=content
        if w<1 or h<1 or x<23 or y<4 or x+w>width-2 or y+h>14:
            raise PixelArtError(f'content: [{x},{y},{w},{h}] must fit x>=23, x+w<={width-2}, '
                                'y>=4, y+h<=14; rectangles use half-open [x,x+w), [y,y+h). Increase --width if needed')
        context['regions']=[dict(name=cell['name']+'-text',rect=[cell['x']+x,cell['y']+y,w,h],role='reserved_text')
            for cell in image.info['pixelart']['cells']]
    return asset_files(data,background='1D293D',context=context)


def main():
    cli=parser(__doc__)
    cli.add_argument('--width',type=int,default=32)
    cli.add_argument('--hover',default='345D78',help='Only hover fill; other state colors remain unchanged.')
    cli.add_argument('--content',type=int,nargs=4,metavar=('X','Y','W','H'),help='Per-cell text rectangle, not rendered text. Use a consumer font to verify fit.')
    args=cli.parse_args();emit(args,make_files(width=args.width,hover=args.hover,content=args.content))


if __name__=='__main__':entry(main)
