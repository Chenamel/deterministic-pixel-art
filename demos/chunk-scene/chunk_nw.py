"""NW: clockwork workshop, left canal and upper-left bridge; local coordinates."""
from chunk_common import Drawing,entry


def make_spec(agreement):
    d=Drawing('nw',agreement)
    d.r(12,12,67,77,'ground_dark');d.r(10,10,67,77,'ground_light')
    d.paving(86,0,14,128)
    d.r(100,0,8,128,'stone_dark');d.r(100,0,2,128,'stone_light');d.r(106,0,2,128,'outline')
    d.r(108,0,20,128,'water');d.r(108,0,3,128,'water_dark')
    d.l([[113,9],[118,9],[121,12]],'water_light');d.r(114,24,7,1,'water_dark')
    d.r(120,40,8,1,'water_light');d.r(116,72,12,1,'water_light')
    d.l([[112,88],[116,88],[119,86]],'water_dark')
    d.paving(0,112,100,16)
    d.deck(100,116,28,12)
    for yy,role in ((112,'outline'),(113,'wood_light'),(114,'wood_dark'),(115,'outline')):d.r(100,yy,28,1,role)
    d.house(17,22,58,53)
    # Clock tower and north-facing light, separate from the roof's tile texture.
    d.r(54,8,13,22,'outline');d.r(56,10,9,17,'wall');d.r(54,7,13,3,'roof_dark')
    d.p([[57,12],[62,12],[64,14],[64,19],[62,21],[57,21],[55,19],[55,14]],'gold')
    d.l([[60,14],[60,17],[62,18]],'outline')
    # Pump and connecting pipe stop before the shared clear-water checkpoint y=96.
    d.r(80,56,14,33,'shadow');d.r(78,54,14,30,'outline');d.r(80,56,10,25,'metal')
    d.r(81,57,3,21,'metal_light');d.r(84,50,4,9,'outline');d.r(85,51,2,7,'gold')
    d.l([[90,63],[101,63],[104,66],[104,75]],'outline')
    d.l([[91,64],[100,64],[103,67],[103,73]],'metal_light')
    d.crate(23,85);d.crate(43,88,16,11)
    d.tufts([(3,22),(4,61),(63,92),(71,103),(14,101),(41,5)])
    return d.spec()


if __name__=='__main__':entry('nw',make_spec)
