from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / 'contract.json').read_text(encoding='utf-8'))
P = C['palette']


def rect(s, x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(128, x + w)
    y1 = min(128, y + h)
    if x1 > x0 and y1 > y0:
        s['operations'].append(
            dict(op='rect', x=x0, y=y0, w=x1 - x0, h=y1 - y0, color=c)
        )


def water(s, ox, oy):
    rect(s, 104 - ox, -oy, 48, 256, P['water'])
    for y in range(0, 256, 10):
        rect(s, 104 - ox, y - oy, 48, 1, P['wave'])


def walkway(s, ox, oy):
    rect(s, -ox, 112 - oy, 256, 24, P['rail'])
    rect(s, -ox, 113 - oy, 256, 22, P['plank'])
    for x in range(0, 256, 6):
        rect(s, x - ox, 113 - oy, 1, 22, P['joint'])


def create(name):
    owner = next(o for o in C['owners'] if o['name'] == name)
    ox, oy = owner['rect'][:2]
    s = dict(
        version=1, kind='draw', size=[128, 128], background='567F55', operations=[]
    )
    for y in range(7, 128, 19):
        for x in range(6, 128, 23):
            rect(s, x, y, 3, 1, '6F945F')
    water(s, ox, oy)
    walkway(s, ox, oy)
    return s
