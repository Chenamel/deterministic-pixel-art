"""Original asymmetric 128px courier. Edit semantic colors, not expanded point lists."""
from _common import clipped,emit,entry,asset_files,parser,points_for,poly,rect,line,spec


def make_spec(*,hull='4B8C9D',stripe='D38A48',stripe_light='F2C37B'):
    size=[128,128];ink='142B3D'
    shapes=[poly([[21,59],[41,43],[78,40],[101,50],[115,65],[99,79],[63,86],[27,76]],'FFFFFF'),
        poly([[43,50],[32,25],[39,23],[69,46]],'FFFFFF'),
        poly([[52,75],[81,105],[98,104],[82,72]],'FFFFFF')]
    body=points_for(size,shapes)
    ops=[poly([[4,61],[15,57],[17,65],[14,71],[6,69]],'C45E42'),
        poly([[7,63],[15,60],[16,65],[13,68]],'F1B765'),
        rect(37,16,2,19,ink),rect(34,16,8,3,'E8AC62'),
        dict(op='mask',points=[list(p) for p in sorted(body)],color=hull,outline=ink,thickness=2,neighborhood=8)]
    for op in [
        poly([[32,25],[40,25],[62,46],[43,50]],'79B8BD'),
        poly([[37,29],[41,34],[46,49],[43,49]],'D2D5B6'),
        poly([[50,75],[78,77],[98,103],[82,103]],'31576C'),
        poly([[59,79],[66,81],[87,100],[82,99]],'74A9B1'),
        poly([[24,67],[54,69],[98,62],[113,66],[98,78],[63,84],[28,75]],'31576C'),
        poly([[31,54],[44,45],[76,42],[96,50],[89,53],[51,51]],'86BEC2'),
        poly([[93,52],[111,65],[98,72],[83,72]],'5FA0AB'),
        poly([[42,69],[77,68],[89,72],[73,77],[44,76]],stripe),
        rect(49,69,23,2,stripe_light),
        poly([[50,49],[76,45],[94,53],[94,63],[55,62]],ink),
        poly([[55,50],[76,48],[89,54],[88,59],[57,59]],'30698C'),
        poly([[56,50],[74,48],[78,50],[58,53]],'A4DDE0'),
        poly([[80,51],[89,55],[88,58],[81,57]],'67BEC8'),
    ]:ops.append(clipped(size,op,body))
    ops.extend([rect(19,58,7,15,ink),rect(21,60,3,10,'DBA664'),
        line([[97,57],[104,62],[99,66]],'B8D8D0'),
        line([[74,80],[86,94]],ink),line([[78,81],[90,95]],'6392A1'),
        rect(34,60,11,7,ink),rect(35,61,3,5,'89B8B9'),rect(40,61,3,5,'89B8B9'),
        rect(63,79,6,2,'A8CAC4'),rect(72,78,4,2,'A8CAC4'),rect(46,40,2,4,'C45E42'),
        rect(37,19,2,7,'86BEC2')])
    return spec(size,ops)


def main():
    cli=parser(__doc__)
    cli.add_argument('--hull',default='4B8C9D')
    cli.add_argument('--stripe',default='D38A48')
    cli.add_argument('--stripe-light',default='F2C37B')
    args=cli.parse_args()
    emit(args,asset_files(make_spec(hull=args.hull,stripe=args.stripe,stripe_light=args.stripe_light),
        context=dict(asset_type='sprite',backgrounds=[dict(name='target',color='243449')])))


if __name__=='__main__':entry(main)
