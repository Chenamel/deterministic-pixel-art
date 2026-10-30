"""SW: timber yard and supplies, left downstream bank and lower bridge."""
from chunk_common import Drawing,entry


def make_spec(agreement):
    d=Drawing('sw',agreement)
    d.r(11,40,65,74,'ground_dark');d.r(10,38,63,73,'ground_light')
    d.paving(86,0,14,128)
    d.r(100,0,8,128,'stone_dark');d.r(100,0,2,128,'stone_light');d.r(106,0,2,128,'outline')
    d.r(108,0,20,128,'water');d.r(108,0,3,128,'water_dark')
    d.r(120,56,8,1,'water_light');d.r(116,88,12,1,'water_light')
    d.l([[113,27],[118,27],[121,29]],'water_light');d.r(115,101,8,1,'water_dark')
    d.paving(0,0,100,16)
    d.deck(100,0,28,12)
    for yy,role in ((12,'outline'),(13,'wood_light'),(14,'wood_dark'),(15,'outline')):d.r(100,yy,28,1,role)
    # Timber rack, separate from the north workshop; horizontal stock reinforces wood grain.
    d.r(19,42,53,29,'shadow');d.r(17,39,53,29,'outline');d.r(19,41,49,25,'wood_dark')
    for yy in (43,50,57):
        d.r(21,yy,43,5,'wood');d.r(21,yy,43,1,'wood_light')
        d.r(24,yy+1,2,3,'wood_dark');d.r(59,yy+1,3,3,'wood_dark')
    d.r(17,39,3,31,'metal');d.r(66,39,3,31,'metal')
    d.r(18,39,1,29,'metal_light');d.r(67,39,1,29,'metal_light')
    d.barrel(18,80);d.barrel(34,78);d.crate(51,80,16,14)
    # Open delivery cart with two distinctly separated wheels.
    d.r(35,24,24,10,'wood_dark');d.r(36,24,22,3,'wood_light');d.r(37,28,20,4,'wood')
    d.r(36,32,5,4,'outline');d.r(53,32,5,4,'outline');d.l([[58,27],[69,25]],'wood_dark')
    d.tufts([(6,22),(72,31),(7,95),(77,94),(42,117),(6,119),(68,116)])
    return d.spec()


if __name__=='__main__':entry('sw',make_spec)
