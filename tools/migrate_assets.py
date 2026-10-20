"""Migrate frozen art to editable specs; semantic recipes for representative assets.

Remaining legacy artwork is losslessly encoded as merged rectangle runs. Those
encodings preserve art, but are NOT claimed as independent algorithm rewrites.
"""
from __future__ import annotations
import ast
from collections import Counter
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from pixelart import render, validate
from pixelart.spec import parse_dsl


def rect(x, y, w, h, fill):
    return dict(op='rect', x=x, y=y, w=w, h=h, color=fill)


def drawing(size, operations, background=None, palette=None):
    return dict(version=1, kind='draw', size=list(size), background=background,
                palette=palette or {}, operations=operations)


def compact_spec(image):
    image = image.convert('RGBA')
    pixels = list(image.get_flattened_data())
    background = Counter(pixels).most_common(1)[0][0]
    operations, previous = [], {}
    for y in range(image.height):
        current = {}
        x = 0
        while x < image.width:
            fill = pixels[y * image.width + x]
            end = x + 1
            while end < image.width and pixels[y * image.width + end] == fill:
                end += 1
            if fill != background:
                key = (x, end - x, fill)
                if key in previous:
                    op = previous[key]
                    op['h'] += 1
                else:
                    op = rect(x, y, end - x, 1, list(fill))
                    operations.append(op)
                current[key] = op
            x = end
        previous = current
    return drawing(image.size, operations, list(background))


def nexus_spec(role):
    palette = dict(outline='25282B', edge='454B50', casing='6E7478', detail='91979A',
        port_outer='2C3135', port_inner='3A4146', copper_dark='75452E', copper='B66E42',
        cyan_dark='256977', cyan='66C7D8', orange_dark='7E441D', orange='DC893E',
        yellow_dark='84691C', yellow='E0BE49')
    ops = []
    def inclusive(x0, y0, x1, y1, fill):
        ops.append(rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1, fill))
    def paint(coords, fill):
        ops.append(dict(op='points', points=[list(p) for p in coords], color=fill))
    inclusive(1, 1, 14, 14, 'edge')
    inclusive(2, 2, 13, 13, 'casing')
    paint([(2, 2), (13, 2), (2, 13), (13, 13)], 'detail')
    paint([(3, 3), (12, 3), (3, 12), (12, 12)], 'edge')
    inclusive(3, 3, 12, 12, 'port_outer')
    inclusive(4, 4, 11, 11, 'edge')
    inclusive(5, 5, 10, 10, 'port_inner')
    paint([(7, 4), (8, 4), (11, 7), (11, 8), (7, 11), (8, 11), (4, 7), (4, 8)], 'copper')
    paint([(8, 4), (11, 8), (7, 11), (4, 7)], 'copper_dark')
    inclusive(7, 7, 8, 8, 'outline')
    regions = {
        'top': ((6, 3, 9, 3), (7, 3, 8, 3), 'cyan'),
        'bottom': ((6, 12, 9, 12), (7, 12, 8, 12), 'cyan'),
        'left': ((3, 6, 3, 9), (3, 7, 3, 8), 'orange'),
        'right': ((12, 6, 12, 9), (12, 7, 12, 8), 'orange'),
        'front': ((6, 3, 9, 3), (7, 3, 8, 3), 'yellow'),
        'back': ((6, 12, 9, 12), (7, 12, 8, 12), 'yellow')}
    dark, bright, hue = regions[role]
    inclusive(*dark, hue + '_dark')
    inclusive(*bright, hue)
    if role == 'front':
        inclusive(7, 4, 8, 4, hue)
    if role == 'back':
        inclusive(7, 11, 8, 11, hue)
    return drawing((16, 16), ops, 'outline', palette)


def mode_spec(decal=False):
    gate = {(x, y) for x in (7, 8) for y in range(3, 13)}
    inp = {(x, y) for x in range(2, 7) for y in (7, 8)}
    inp |= {(5, y) for y in range(5, 11)} | {(6, y) for y in range(6, 10)}
    out = {(x, y) for x in range(9, 14) for y in (7, 8)}
    out |= {(11, y) for y in range(5, 11)} | {(12, y) for y in range(6, 10)} | {(13, y) for y in (7, 8)}
    off = {(x, y) for x in range(5, 11) for y in (5, 10)}
    off |= {(x, y) for y in range(6, 10) for x in (5, 10)} | {(x, y) for x in (7, 8) for y in (7, 8)}
    cache = {(x, y) for x in range(2, 7) for y in (5, 10)} | {(2, y) for y in range(6, 10)}
    cache |= {(x, y) for x in range(6, 11) for y in (7, 8)}
    cache |= {(10, y) for y in range(5, 11)} | {(11, y) for y in range(6, 10)} | {(12, y) for y in (7, 8)}
    cells = [('disabled', off, '8B8B8B', '4A4A4A'), ('input', gate | inp, '668CD0', '263759'),
             ('output', gate | out, 'CE6873', '55282D')]
    if not decal:
        cells.append(('bidirectional', gate | inp | out, 'A57BBE', '453052'))
    cells.append(('cache_release', cache, '78B585', '2E4D36'))
    return dict(version=1, kind='atlas', columns=len(cells), cells=[
        dict(name=name, spec=drawing((16, 16), [dict(op='mask', points=sorted([list(p) for p in mask]),
            color=body, outline=edge, neighborhood=8)])) for name, mask, body, edge in cells])


def redstone_spec():
    p = dict(groove='4E4E4E', dark='373737', light='A0A0A0', spark='C6C6C6',
             off='5A5A5A', red='E36B6B', red_dark='A84848', red_end='6E3232', mid='6E6E6E')
    ops = []
    for ox, knob, top_on, bottom_on, red in [(0, 3, True, False, True),
                                             (16, 11, False, True, True), (32, 7, False, False, False)]:
        def r(x, y, w, h, fill):
            ops.append(rect(ox + x, y, w, h, fill))
        r(5, 3, 6, 10, 'groove'); r(5, 3, 1, 10, 'dark'); r(10, 3, 1, 10, 'light')
        r(10, 3, 1, 1, 'spark')
        r(4, 2, 8, 1, 'red' if top_on else 'off')
        r(4, 13, 8, 1, 'red' if bottom_on else 'off')
        if not red:
            r(6, 5, 4, 1, 'off'); r(6, 10, 4, 1, 'off')
        r(4, knob, 8, 1, 'red' if red else 'spark')
        r(4, knob + 1, 8, 1, 'red_dark' if red else 'mid')
        for dx in (0, 7):
            r(4 + dx, knob, 1, 2, 'red_end' if red else 'dark')
    return drawing((48, 16), ops, palette=p)


def redstone_composition():
    ops = []
    for i in range(3):
        x = i * 23
        ops += [rect(x, 0, 22, 20, '373737'), rect(x + 1, 1, 20, 18, '8B8B8B'),
                dict(op='bevel', x=x + 1, y=1, w=20, h=18, tl='A8A8A8', br='5A5A5A'),
                dict(op='blit', x=x + 3, y=2, source=redstone_spec(), crop=[i * 16, 0, 16, 16])]
    return drawing((68, 20), ops)


def constants(script):
    result = {}
    for node in ast.parse(script.read_text(encoding='utf-8-sig')).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith('SPEC'):
                    result[target.id] = ast.literal_eval(node.value)
    return result


def examples():
    gem = {'version': 1, 'kind': 'grid', 'palette': {'.': None, 'e': '#16223D',
           'a': '#36CFC9', 'b': '#F7B955', 'h': '#DCFFF4'}, 'mirror': 'x', 'rows': [
           '........', '........', '.....eee', '....ehha', '...ehhaa', '..ehaaaa',
           '..eaaabb', '..eabbbb', '..eabbbb', '...eabbb', '....eabb', '.....eab',
           '......ea', '.......e', '........', '........']}
    ship = drawing((32, 32), [
        dict(op='polygon', points=[[5, 18], [22, 5], [25, 21], [13, 26]], color='16223D'),
        dict(op='polygon', points=[[8, 18], [21, 8], [22, 20], [14, 23]], color='36CFC9'),
        rect(17, 12, 3, 4, 'DCFFF4'), rect(8, 23, 4, 3, 'F7B955'),
        rect(4, 27, 3, 2, 'F07852'), rect(25, 9, 2, 2, 'F7B955'),
        dict(op='line', points=[[10, 19], [16, 15]], color='218390')])
    panel = drawing((96, 40), [rect(1, 1, 94, 38, '16223D'),
        dict(op='bevel', x=1, y=1, w=94, h=38, tl='36CFC9', br='071026'),
        rect(7, 8, 20, 24, '253655'), rect(33, 8, 20, 24, '253655'),
        rect(60, 13, 28, 15, '36CFC9'), rect(63, 16, 22, 2, 'DCFFF4'),
        dict(op='polygon', points=[[69, 20], [77, 20], [73, 25]], color='16223D')])
    states = dict(version=1, kind='atlas', columns=1, cells=[dict(name=state.lower(), spec={
        'kind': 'draw', 'size': [22, 20], 'preset': 'minecraft', 'operations': [
            dict(op='button', x=0, y=0, w=22, h=20, state=state)]})
        for state in ('NORMAL', 'HOVER', 'PRESSED', 'SELECTED', 'DISABLED')])
    return {'gem-16': gem, 'asymmetric-ship-32': ship, 'generic-panel-96x40': panel,
            'minecraft-button-states': states}


def main():
    baseline = ROOT / 'baselines'
    manifest = json.loads((baseline / 'manifest.json').read_text(encoding='utf-8'))
    snapshot = baseline / 'snapshot/llm-pixel-art'
    demo = constants(snapshot / 'render_demo.py')['SPEC']
    heart = dict(version=1, kind='grid', rows=demo.strip().splitlines(), mirror='x',
        palette={'.': None, '0': [26, 8, 8, 255], 'h': [255, 158, 158, 255],
                 'r': [229, 57, 53, 255], 'R': [139, 26, 26, 255]})
    dsl = constants(snapshot / 'render_dsl_demo.py')
    migrated = []
    for entry in manifest['entries']:
        relative = entry['output']
        name = Path(relative).name
        with Image.open(baseline / 'rendered' / relative) as im:
            spec = compact_spec(im)
        method, change = 'lossless-rectangle-encoding', None
        if name == 'heart_16x16.png':
            spec, method = heart, 'semantic-grid'
        elif name in ('gui_panel_128x48.png', 'btn_states_44x46.png'):
            spec = parse_dsl(dsl['SPEC_PANEL' if name.startswith('gui_') else 'SPEC_BUTTONS'])
            method = 'semantic-dsl'
        elif entry['script'] == 'render_nexus_block_faces.py':
            spec, method = nexus_spec(name.removeprefix('nexus_').removesuffix('.png')), 'semantic-geometry'
        elif name in ('side_mode_plane_horizontal-v4.png', 'side_mode_decal_final-v6.png'):
            spec, method = mode_spec('decal' in name), 'semantic-mask-atlas'
        elif name == 'editor_redstone_icons.png':
            spec, method = redstone_spec(), 'semantic-geometry'
        elif name in ('redstone_on_buttons_1to1.png', 'redstone_on_buttons_preview.png'):
            spec = redstone_composition()
            if name.endswith('_preview.png'):
                spec = dict(version=1, kind='preview', source=spec, scale=8, background='C6C6C6')
            method, change = 'semantic-composition', 'corrected-button-preview'
        elif name == 'bidirectional_settings_footer-v4.png':
            with Image.open(baseline / 'snapshot' / relative) as im:
                spec = compact_spec(im)
            change = 'align-with-current-runtime-pixels; normalize RGB to RGBA'
        image = render(spec)
        check = validate(image, {'size': entry['size'], 'mode': 'RGBA', 'alpha': [0, 255]})
        if not check['valid']:
            raise ValueError(f'{relative}: {check}')
        spec_path = ROOT / 'specs/legacy' / Path(relative).with_suffix('.json')
        image_path = ROOT / 'output/legacy' / relative
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, separators=(',', ':')), encoding='utf-8', newline='\n')
        image.save(image_path, format='PNG')
        migrated.append(dict(output=relative, spec=spec_path.relative_to(ROOT).as_posix(),
                             method=method, intended_change=change))
    for name, spec in examples().items():
        p = ROOT / 'examples' / f'{name}.json'
        p.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
        image = render(spec)
        out = ROOT / 'output/examples'
        out.mkdir(parents=True, exist_ok=True)
        image.save(out / f'{name}.png')
    (ROOT / 'specs/manifest.json').write_text(json.dumps(migrated, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps({'migrated': len(migrated), 'examples': len(examples())}))


if __name__ == '__main__':
    main()
