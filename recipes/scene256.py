"""Original component scene. Re-render every component before assembly."""
from _common import clipped,emit,entry,asset_files,parser,points_for,poly,rect,line,spec,render,make_preview
from pixelart.assembly import assemble,seam_sheet


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


def mill(*,roof_color='81594E',roof_light='B78363'):
    ink='303B3E'
    roof=points_for([144,116],[poly([[9,44],[34,7],[106,7],[136,44]],'FFFFFF')])
    ops=[rect(16,45,119,64,ink),rect(18,47,115,58,'C8B68D'),rect(96,47,37,58,'AD9873'),
        rect(16,105,119,8,'5C6662'),rect(18,106,115,2,'9DA28D'),rect(19,110,111,2,'3E4C4D'),
        dict(op='mask',points=[list(p) for p in sorted(roof)],color=roof_color,outline=ink,neighborhood=8,thickness=2)]
    for y in (15,24,33,42):
        ops.append(clipped([144,116],rect(12,y,121,2,roof_light),roof))
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


def make_files(*,roof='81594E',roof_light='B78363'):
    pieces={'terrain':(terrain(),[0,0]),'mill':(mill(roof_color=roof,roof_light=roof_light),[104,18]),
        'bridge':(bridge(),[80,140]),'details':(decorations(),[0,0])}
    files={};sources={};parts=[];control_ops=[]
    for name,(data,at) in pieces.items():
        image=render(data);path=f'scene/{name}.png'
        files[f'scene/{name}.json']=data;files[path]=image;sources[path]=image
        parts.append(dict(name=name,image=path,at=at,mode='copy' if name=='terrain' else 'over',allow_overlap=name!='terrain'))
        control_ops.append(dict(op='blit',x=at[0],y=at[1],source=data))
    project=dict(version=1,size=[256,256],require_coverage=True,parts=parts)
    scene,report=assemble(project,sources)
    files.update({'project.json':project,'assembly.json':report,'seams.png':seam_sheet(scene,report)})
    files.update(asset_files(spec([256,256],control_ops)))
    return files


def main():
    cli=parser(__doc__)
    cli.add_argument('--roof',default='81594E')
    cli.add_argument('--roof-light',default='B78363')
    args=cli.parse_args();emit(args,make_files(roof=args.roof,roof_light=args.roof_light))


if __name__=='__main__':entry(main)
