"""NE: packet depot, moored boat and upper-right bridge; local coordinates."""
from chunk_common import Drawing,entry,color


def make_spec(agreement,*,flag='E4BB6B'):
    color(flag)
    d=Drawing('ne',agreement)
    d.r(45,16,73,76,'ground_dark');d.r(43,14,73,76,'ground_light')
    d.r(0,0,20,128,'water');d.r(17,0,3,128,'water_dark')
    d.r(0,40,9,1,'water_light');d.r(0,72,9,1,'water_light')
    d.l([[9,18],[14,18],[16,16]],'water_light');d.r(4,54,6,1,'water_dark')
    d.r(20,0,8,128,'stone_dark');d.r(20,0,2,128,'outline');d.r(22,0,2,128,'stone_light')
    d.paving(28,0,14,128)
    d.paving(28,112,100,16)
    d.deck(0,116,28,12)
    for yy,role in ((112,'outline'),(113,'wood_light'),(114,'wood_dark'),(115,'outline')):d.r(0,yy,28,1,role)
    d.house(50,27,58,53)
    # Only this small flag is exposed for the scoped-edit rehearsal.
    d.r(80,9,2,27,'outline');d.r(82,11,16,9,'outline');d.r(83,12,14,7,flag)
    d.r(83,12,14,1,'ivory')
    # Narrow moored boat beside the quay, leaving the central seam unobstructed.
    d.p([[9,56],[14,49],[18,56],[18,83],[14,90],[9,83]],'outline')
    d.p([[11,57],[14,53],[16,57],[16,82],[14,86],[11,82]],'wood_light')
    d.r(11,63,6,13,'wood_dark');d.r(12,64,4,11,'wood')
    d.r(11,78,6,2,'wood_light');d.l([[17,60],[23,55]],'ivory')
    d.r(30,55,3,3,'outline');d.r(30,55,2,1,'metal_light')
    d.crate(48,87,15,12);d.crate(68,88)
    d.tufts([(109,100),(84,98),(116,49),(48,5),(99,5),(51,102)])
    return d.spec()


if __name__=='__main__':entry('ne',make_spec,flag=True)
