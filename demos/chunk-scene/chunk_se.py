"""SE: warehouse and canal crane, right downstream bank and lower bridge."""
from chunk_common import Drawing,entry


def make_spec(agreement):
    d=Drawing('se',agreement)
    d.r(47,48,73,65,'ground_dark');d.r(45,46,73,65,'ground_light')
    d.r(0,0,20,128,'water');d.r(17,0,3,128,'water_dark')
    d.r(0,56,9,1,'water_light');d.r(0,88,9,1,'water_light')
    d.l([[6,32],[11,32],[14,29]],'water_light');d.r(6,105,8,1,'water_dark')
    d.r(20,0,8,128,'stone_dark');d.r(20,0,2,128,'outline');d.r(22,0,2,128,'stone_light')
    d.paving(28,0,14,128)
    d.paving(28,0,100,16)
    d.deck(0,0,28,12)
    for yy,role in ((12,'outline'),(13,'wood_light'),(14,'wood_dark'),(15,'outline')):d.r(0,yy,28,1,role)
    d.house(52,62,58,42,roof='roof_dark')
    # Crane boom is over land/quay; it must not block the bridge's walking deck.
    d.r(45,31,11,28,'shadow');d.r(43,29,11,28,'outline');d.r(45,31,7,24,'metal')
    d.r(45,31,2,22,'metal_light');d.r(47,21,3,13,'outline')
    d.p([[15,24],[17,21],[54,21],[57,24],[54,27],[15,27]],'outline')
    d.r(17,22,36,3,'wood');d.r(17,22,36,1,'wood_light')
    d.l([[48,23],[53,35]],'gold');d.l([[17,27],[17,29],[20,32],[23,29]],'outline')
    d.l([[18,28],[18,29],[20,31]],'metal_light')
    d.crate(62,29,16,15);d.crate(83,33,14,12)
    d.r(81,8,4,4,'stone_dark')
    d.tufts([(119,23),(100,46),(43,117),(73,116),(112,118),(46,5)])
    return d.spec()


if __name__=='__main__':entry('se',make_spec)
