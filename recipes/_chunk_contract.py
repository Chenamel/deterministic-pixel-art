"""Small example contract and local material primitives; never draws a full image."""
from _common import rect

CONTRACT = {
    'version': 1, 'size': [64, 32],
    'owners': {'left': [0, 0, 32, 32], 'right': [32, 0, 32, 32]},
    'light': 'upper-left', 'road_y': [14, 22], 'bridge_rails_y': [12, 22],
    'plank_period': 6, 'plank_origin_x': 24,
    'editable_flag_global': [51, 5, 6, 4],
    'note': 'Two local drawings; not a native512 or independent-agent quality study.',
}
PALETTE = dict(ground='66775A', stone='A69B7E', mortar='756F60',
               water='356B80', ripple='72A4AD', wood='9B7950',
               dark='4F4942', light='D2B27C')


def deck(ops, origin_x, x, width):
    """Fill a local deck with a GLOBAL phase; 32 is not divisible by six."""
    ops.append(rect(x, 14, width, 8, PALETTE['wood']))
    for local_x in range(x, x + width):
        phase = (origin_x + local_x - CONTRACT['plank_origin_x']) % CONTRACT['plank_period']
        if phase in (0, 1):
            ops.append(rect(local_x, 14, 1, 8, PALETTE['dark' if phase == 0 else 'light']))
    for y in CONTRACT['bridge_rails_y']:
        ops.extend([rect(x, y, width, 2, PALETTE['dark']),
                    rect(x, y, width, 1, PALETTE['light'])])
