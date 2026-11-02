"""Original 32px travel items and a static UI composition, using JSON v1.

Run from any directory with Python 3.10+ and the repository Pillow requirement.
All artwork is hand-authored integer geometry; no external images are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from pixelart import render, replace_cell, validate, verify_edit
from pixelart.metadata import encode_png, layout_record
from pixelart.output import encoded, publish

PALETTE = dict(
    ink='17212B', deep='25323C', brass_shadow='725342', brass='B38656',
    gold='D6B775', gleam='F4DEAB', leather_dark='583F3D', leather='98634F',
    leather_light='C18D64', rose='B96D69', paper_shadow='AA936D', paper='D9C79B',
    ivory='F0E1B9', sea_dark='325A60', sea='438B87', mint='74B7A4',
    glass='BDD9BD', violet_dark='484968', violet='7475A3', lavender='A3A4D0',
    ice='D1D9E5', panel='253B3D', slot='1B2B31', panel_light='476164',
)
NAMES = ('tonic', 'journal', 'lantern', 'map', 'satchel', 'crystal')
LABELS = ('TONIC', 'JOURNAL', 'LANTERN', 'MAP', 'SATCHEL', 'CRYSTAL')


class Drawing:
    def __init__(self, size=(32, 32)):
        self.spec = dict(version=1, kind='draw', size=list(size), palette=dict(PALETTE), operations=[])

    def op(self, kind, **values):
        self.spec['operations'].append(dict(op=kind, **values))

    def rect(self, x, y, width, height, color):
        self.op('rect', x=x, y=y, w=width, h=height, color=color)

    def poly(self, points, color):
        self.op('polygon', points=[list(point) for point in points], color=color)

    def line(self, points, color):
        self.op('line', points=[list(point) for point in points], color=color)

    def dots(self, points, color):
        self.op('points', points=[list(point) for point in points], color=color)


def tonic():
    art = Drawing()
    art.poly([(12, 3), (20, 3), (20, 10), (24, 14), (26, 19), (25, 25),
              (22, 28), (10, 28), (7, 25), (6, 19), (8, 14), (12, 10)], 'ink')
    art.poly([(13, 9), (19, 9), (19, 11), (23, 15), (25, 19), (24, 24),
              (21, 27), (11, 27), (8, 24), (7, 19), (9, 15), (13, 11)], 'sea_dark')
    art.poly([(12, 13), (19, 12), (22, 16), (22, 21), (18, 25), (11, 25),
              (9, 22), (9, 17)], 'sea')
    art.poly([(9, 19), (13, 17), (18, 18), (23, 17), (24, 20), (23, 24),
              (20, 26), (11, 26), (8, 23)], 'mint')
    art.poly([(10, 21), (15, 22), (20, 21), (23, 21), (22, 25), (19, 26), (12, 26)], 'sea')
    art.line([(9, 18), (10, 15), (12, 13)], 'glass')
    art.line([(9, 20), (9, 22), (10, 23)], 'ivory')
    art.dots([(12, 24), (19, 19), (20, 24)], 'glass')
    art.rect(13, 8, 6, 3, 'mint')
    art.rect(14, 9, 2, 2, 'glass')
    art.rect(11, 6, 10, 3, 'ink')
    art.rect(12, 6, 8, 2, 'brass')
    art.rect(12, 6, 7, 1, 'gleam')
    art.rect(13, 3, 6, 3, 'leather')
    art.rect(13, 3, 5, 1, 'leather_light')
    art.dots([(15, 4), (18, 5)], 'brass_shadow')
    return art.spec


def journal():
    art = Drawing()
    art.poly([(7, 6), (22, 3), (27, 7), (25, 25), (10, 29), (5, 25), (5, 10)], 'ink')
    art.poly([(8, 22), (24, 19), (24, 24), (10, 27), (7, 25)], 'paper_shadow')
    art.poly([(8, 23), (23, 20), (23, 22), (10, 25)], 'ivory')
    art.line([(11, 26), (22, 23)], 'paper')
    art.poly([(7, 7), (21, 4), (25, 7), (23, 22), (9, 26), (6, 23), (6, 10)], 'leather_dark')
    art.poly([(10, 7), (21, 5), (24, 7), (22, 21), (10, 24), (9, 22)], 'leather')
    art.poly([(11, 8), (21, 6), (22, 8), (20, 19), (12, 21), (10, 21)], 'rose')
    art.line([(7, 10), (7, 21), (9, 24)], 'leather_light')
    art.line([(11, 7), (20, 5)], 'leather_light')
    art.poly([(16, 10), (20, 13), (16, 18), (12, 15)], 'brass_shadow')
    art.poly([(16, 10), (19, 13), (16, 16), (13, 14)], 'gold')
    art.poly([(16, 12), (17, 13), (16, 15), (15, 14)], 'gleam')
    art.line([(12, 9), (14, 8)], 'gold')
    art.line([(18, 20), (21, 19), (21, 17)], 'gold')
    art.poly([(17, 25), (20, 24), (20, 29), (18, 28), (17, 30)], 'leather_dark')
    art.rect(18, 25, 1, 3, 'rose')
    return art.spec


def lantern(amber=False):
    art = Drawing()
    # Palette roles isolate the glass change; metal, shape and position stay fixed.
    art.spec['palette'].update(
        pane_shadow='9B5540' if amber else '325A60',
        pane='D58E49' if amber else '438B87',
        pane_light='F3C76E' if amber else '74B7A4',
        pane_glint='FFF0BF' if amber else 'BDD9BD')
    art.poly([(11, 8), (11, 5), (14, 2), (18, 2), (21, 5), (21, 8),
              (18, 8), (18, 6), (17, 5), (15, 5), (14, 6), (14, 8)], 'ink')
    art.line([(12, 7), (12, 5), (14, 3), (18, 3), (20, 5), (20, 7)], 'brass')
    art.line([(13, 5), (15, 3), (17, 3)], 'gleam')
    art.poly([(11, 8), (20, 8), (24, 11), (24, 13), (8, 13), (8, 11)], 'ink')
    art.poly([(12, 9), (20, 9), (22, 11), (10, 11)], 'brass')
    art.line([(12, 9), (18, 9)], 'gold')
    art.rect(9, 12, 14, 15, 'ink')
    art.rect(11, 14, 10, 11, 'pane_shadow')
    art.poly([(12, 14), (19, 14), (20, 16), (19, 23), (12, 23)], 'pane')
    art.poly([(13, 15), (17, 15), (18, 17), (17, 22), (13, 22)], 'pane_light')
    art.line([(12, 16), (12, 20)], 'pane_glint')
    art.dots([(13, 15), (16, 23)], 'pane_glint')
    art.rect(9, 13, 2, 13, 'brass_shadow')
    art.rect(10, 13, 1, 11, 'gold')
    art.rect(21, 13, 2, 13, 'brass_shadow')
    art.rect(21, 13, 1, 11, 'brass')
    art.rect(8, 25, 16, 4, 'ink')
    art.rect(9, 26, 14, 2, 'brass')
    art.rect(10, 26, 11, 1, 'gold')
    art.rect(8, 12, 16, 1, 'gold')
    art.rect(10, 11, 11, 1, 'gleam')
    art.rect(14, 24, 4, 1, 'brass_shadow')
    return art.spec


def map_scroll():
    art = Drawing()
    art.poly([(8, 7), (24, 4), (28, 7), (27, 12), (25, 12), (25, 24),
              (22, 26), (8, 29), (4, 26), (4, 11)], 'ink')
    art.poly([(8, 8), (24, 5), (26, 7), (24, 24), (8, 27)], 'paper_shadow')
    art.poly([(9, 8), (23, 6), (23, 23), (9, 26)], 'paper')
    art.poly([(10, 9), (21, 7), (22, 14), (10, 17)], 'ivory')
    art.line([(11, 17), (16, 16), (21, 17)], 'paper_shadow')
    art.poly([(23, 5), (26, 6), (27, 8), (26, 10), (23, 10)], 'paper')
    art.line([(24, 6), (26, 7), (26, 8)], 'ivory')
    art.rect(24, 9, 2, 1, 'brass_shadow')
    art.poly([(6, 11), (8, 10), (10, 12), (9, 26), (7, 27), (5, 25), (5, 13)], 'paper')
    art.line([(6, 13), (6, 23), (7, 25)], 'ivory')
    art.line([(9, 13), (8, 24)], 'paper_shadow')
    art.line([(12, 14), (15, 10), (18, 13), (20, 10), (22, 12)], 'sea_dark')
    art.line([(20, 14), (18, 16), (19, 19), (16, 23)], 'sea')
    art.dots([(12, 20), (14, 20), (14, 18), (15, 17)], 'leather')
    art.poly([(12, 22), (14, 20), (17, 22), (15, 25), (12, 24)], 'leather_dark')
    art.poly([(13, 22), (14, 21), (16, 22), (15, 24), (13, 23)], 'rose')
    return art.spec


def satchel():
    art = Drawing()
    art.poly([(12, 8), (12, 4), (14, 2), (19, 2), (21, 4), (21, 8), (18, 8),
              (18, 5), (15, 5), (15, 8)], 'ink')
    art.line([(13, 7), (13, 4), (15, 3), (18, 3), (20, 5)], 'leather_light')
    art.poly([(6, 12), (9, 11), (11, 24), (8, 28), (5, 25)], 'ink')
    art.rect(6, 14, 2, 10, 'leather_dark')
    art.poly([(23, 12), (26, 14), (27, 25), (24, 28), (22, 25)], 'ink')
    art.rect(24, 16, 2, 8, 'leather')
    art.poly([(10, 7), (21, 7), (25, 12), (25, 26), (22, 29), (9, 29),
              (6, 26), (7, 13)], 'ink')
    art.poly([(10, 9), (20, 8), (23, 12), (23, 26), (21, 27), (10, 27), (8, 25), (8, 14)], 'leather')
    art.poly([(19, 14), (23, 14), (23, 26), (20, 27), (19, 23)], 'leather_dark')
    art.poly([(9, 9), (20, 8), (23, 11), (23, 15), (20, 18), (10, 18), (8, 15)], 'brass_shadow')
    art.poly([(10, 9), (20, 9), (22, 11), (21, 15), (19, 16), (11, 16), (9, 14)], 'leather_light')
    art.line([(11, 9), (19, 9), (21, 10)], 'paper_shadow')
    art.rect(11, 16, 3, 6, 'ink')
    art.rect(12, 16, 1, 5, 'brass')
    art.rect(18, 16, 3, 6, 'ink')
    art.rect(19, 16, 1, 5, 'brass')
    art.rect(11, 18, 3, 3, 'gold')
    art.rect(12, 19, 1, 1, 'leather_dark')
    art.rect(18, 18, 3, 3, 'gold')
    art.rect(19, 19, 1, 1, 'leather_dark')
    art.rect(11, 23, 9, 4, 'leather_dark')
    art.rect(12, 23, 7, 3, 'leather_light')
    art.line([(12, 23), (18, 23)], 'paper_shadow')
    return art.spec


def crystal():
    art = Drawing()
    art.poly([(5, 14), (9, 11), (14, 21), (10, 28), (5, 24), (3, 18)], 'ink')
    art.poly([(5, 15), (8, 13), (11, 21), (9, 25), (5, 23), (4, 18)], 'violet')
    art.poly([(5, 15), (6, 14), (8, 21), (7, 23), (5, 21)], 'lavender')
    art.poly([(22, 15), (27, 11), (30, 16), (27, 25), (22, 29), (18, 25)], 'ink')
    art.poly([(23, 16), (26, 13), (28, 17), (26, 24), (22, 27), (20, 24)], 'violet_dark')
    art.poly([(24, 16), (26, 14), (27, 17), (24, 24), (22, 25)], 'lavender')
    art.poly([(14, 2), (21, 7), (23, 21), (18, 29), (11, 27), (8, 21), (10, 9)], 'ink')
    art.poly([(14, 4), (20, 8), (21, 20), (17, 27), (12, 25), (10, 20), (11, 10)], 'violet')
    art.poly([(14, 4), (15, 12), (13, 23), (11, 20), (12, 10)], 'ice')
    art.poly([(14, 5), (19, 8), (16, 12), (15, 12)], 'lavender')
    art.poly([(17, 12), (20, 9), (21, 20), (17, 26), (15, 23)], 'violet_dark')
    art.line([(12, 11), (12, 17)], 'gleam')
    art.line([(14, 24), (16, 26)], 'lavender')
    return art.spec


def text_mask(art, label, x, y, font, color):
    mask = Image.new('1', tuple(art.spec['size']))
    draw = ImageDraw.Draw(mask)
    bounds = draw.textbbox((0, 0), label, font=font)
    if x < 0 or y < 0 or x + bounds[2] - bounds[0] > mask.width or y + bounds[3] - bounds[1] > mask.height:
        raise ValueError('Native label exceeds canvas: ' + label)
    draw.text((x - bounds[0], y - bounds[1]), label, font=font, fill=1)
    art.dots([(px, py) for py in range(mask.height) for px in range(mask.width) if mask.getpixel((px, py))], color)


def interface(items, font):
    frame = Drawing((192, 160))
    frame.poly([(4, 1), (187, 1), (190, 4), (190, 155), (187, 158), (4, 158), (1, 155), (1, 4)], 'ink')
    frame.poly([(5, 2), (186, 2), (189, 5), (189, 154), (186, 157), (5, 157), (2, 154), (2, 5)], 'brass_shadow')
    frame.poly([(6, 4), (185, 4), (187, 6), (187, 153), (185, 155), (6, 155), (4, 153), (4, 6)], 'panel')
    frame.line([(7, 5), (184, 5)], 'panel_light')
    frame.rect(7, 8, 178, 26, 'deep')
    frame.rect(10, 35, 172, 1, 'ink')
    for index in range(6):
        x, y = 14 + index % 3 * 60, 44 + index // 3 * 44
        frame.rect(x, y, 44, 40, 'ink')
        frame.rect(x + 1, y + 1, 42, 38, 'panel_light' if index == 2 else 'brass_shadow')
        frame.rect(x + 2, y + 2, 40, 36, 'slot')
        frame.line([(x + 3, y + 36), (x + 40, y + 36)], 'deep')
        if index == 2:
            frame.line([(x, y + 5), (x, y), (x + 5, y)], 'gold')
            frame.line([(x + 38, y + 39), (x + 43, y + 39), (x + 43, y + 34)], 'gold')
            frame.poly([(x + 4, y + 3), (x + 6, y + 5), (x + 4, y + 7), (x + 2, y + 5)], 'gold')
    frame.rect(11, 133, 170, 1, 'ink')
    frame.rect(138, 138, 40, 13, 'ink')
    frame.rect(139, 138, 38, 12, 'brass_shadow')
    frame.rect(140, 139, 36, 9, 'gold')
    frame.rect(141, 139, 34, 1, 'gleam')
    composed = Drawing((192, 160))
    composed.op('blit', x=0, y=0, source=frame.spec)
    for index, item in enumerate(items):
        composed.op('blit', x=20 + index % 3 * 60, y=48 + index // 3 * 44, source=item)
    text_mask(composed, "WAYFARER'S KIT", 14, 15, font, 'ivory')
    text_mask(composed, '06', 165, 15, font, 'mint')
    text_mask(composed, 'LANTERN', 14, 141, font, 'ivory')
    text_mask(composed, 'USE', 151, 140, font, 'ink')
    return frame.spec, composed.spec


def font(size):
    return ImageFont.load_default(size=size)


def card(draw, box):
    draw.rounded_rectangle(box, radius=12, fill='#1C2A32', outline='#35454D', width=1)


def gallery(images, ui):
    sheet = Image.new('RGB', (1120, 720), '#111B23')
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 19), 'ORIGINAL PIXEL ASSETS', font=font(13), fill='#8CB6AC')
    draw.text((24, 40), "Wayfarer's kit", font=font(34), fill='#F0E1B9')
    draw.text((26, 89), 'Six 32px items, a composed interface, and editable JSON sources.', font=font(16), fill='#A5B4B6')
    card(draw, (24, 130, 644, 686))
    draw.text((46, 146), 'STATIC INVENTORY COMPOSITION', font=font(13), fill='#B8C6C6')
    sheet.paste(ui.resize((576, 480), Image.Resampling.NEAREST), (46, 176), ui.resize((576, 480), Image.Resampling.NEAREST))
    draw.text((46, 663), '192 x 160 native pixels  /  3x view', font=font(13), fill='#91A7AA')
    card(draw, (660, 130, 1096, 500))
    draw.text((682, 146), 'SIX NAMED 32 x 32 SPRITES', font=font(13), fill='#B8C6C6')
    for index, image in enumerate(images):
        x, y = 684 + index % 3 * 134, 187 + index // 3 * 145
        enlarged = image.resize((96, 96), Image.Resampling.NEAREST)
        sheet.paste(enlarged, (x + 8, y), enlarged)
        label = LABELS[index]
        draw.text((x + (112 - draw.textlength(label, font=font(12))) // 2, y + 106), label, font=font(12), fill='#CAD2CD')
    card(draw, (660, 516, 1096, 686))
    draw.text((682, 533), 'PALETTE / MATERIALS', font=font(13), fill='#B8C6C6')
    for index, color in enumerate(('ink', 'leather_dark', 'leather', 'rose', 'brass', 'gold', 'ivory', 'sea_dark', 'sea', 'mint', 'violet', 'ice')):
        draw.rectangle((683 + index * 32, 562, 706 + index * 32, 576), fill='#' + PALETTE[color])
    draw.text((682, 595), 'NATIVE 1x', font=font(12), fill='#91A7AA')
    for index, image in enumerate(images):
        sheet.paste(image, (684 + index * 63, 625), image)
    return sheet


def edit_gallery(before, after, changed):
    sheet = Image.new('RGB', (1120, 400), '#111B23')
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 16), 'Replace one item. Keep the set.', font=font(27), fill='#F0E1B9')
    draw.text((26, 55), 'Moss glass to amber glass  /  named lantern cell', font=font(15), fill='#A5B4B6')
    delta = Image.new('RGBA', before.size)
    for y in range(before.height):
        for x in range(before.width):
            if before.getpixel((x, y))[3]:
                delta.putpixel((x, y), (71, 90, 96, 255))
            if before.getpixel((x, y)) != after.getpixel((x, y)):
                delta.putpixel((x, y), (244, 209, 134, 255))
    for index, (label, image) in enumerate(zip(('Before', 'After / lantern replaced', 'Exact RGBA changes'), (before, after, delta))):
        left = 24 + index * 364
        card(draw, (left, 92, left + 344, 338))
        draw.text((left + 17, 105), label, font=font(16), fill='#DDE0D2')
        enlarged = image.resize((288, 192), Image.Resampling.NEAREST)
        sheet.paste(enlarged, (left + 28, 136), enlarged)
        draw.rectangle((left + 220, 135, left + 316, 231), outline='#9E895C')
    draw.text((26, 360), f'{changed} changed RGBA pixels  /  0 outside lantern  /  96 x 64 atlas, 32 x 32 cells', font=font(15), fill='#BFCBC7')
    return sheet


def build():
    native_font = ImageFont.truetype(str(ROOT / 'demos/pixel-ui/fonts/Silkscreen-Regular.ttf'), 8)
    items = [tonic(), journal(), lantern(), map_scroll(), satchel(), crystal()]
    before_spec = dict(version=1, kind='atlas', columns=3,
                       cells=[dict(name=name, spec=spec) for name, spec in zip(NAMES, items)])
    after_spec = replace_cell(before_spec, 'lantern', lantern(amber=True))
    before, after = render(before_spec), render(after_spec)
    final_items = [cell['spec'] for cell in after_spec['cells']]
    images = [render(spec) for spec in final_items]
    for image in images:
        result = validate(image, dict(size=[32, 32], mode='RGBA', alpha=[0, 255], nonempty=True, transparent_margin=1))
        if not result['valid']:
            raise ValueError(result)
    report = verify_edit(after, before, regions=[[64, 0, 32, 32]])
    if not report['valid'] or not report['changed_rgba_pixels']:
        raise ValueError(report)
    frame, ui_spec = interface(final_items, native_font)
    ui = render(ui_spec)
    artifacts = {
        'before.json': before_spec, 'before.png': encode_png(before, layout_record(before)),
        'before-layout.json': layout_record(before), 'after.json': after_spec,
        'after.png': encode_png(after, layout_record(after)), 'after-layout.json': layout_record(after),
        'lantern-amber.json': lantern(amber=True), 'panel.json': frame, 'ui.json': ui_spec,
        'ui.png': ui, 'verification.json': report, 'overview.png': gallery(images, ui),
        'scoped-edit.png': edit_gallery(before, after, report['changed_rgba_pixels']),
    }
    for name, image in zip(NAMES, images):
        artifacts[name + '.png'] = image
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=Path(__file__).resolve().parent / 'assets')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    artifacts = build()
    payloads = {name: encoded(artifact) for name, artifact in artifacts.items()}
    hashes = {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()}
    payloads['manifest.json'] = encoded(dict(version=1, items=list(NAMES),
        native_item_size=[32, 32], native_ui_size=[192, 160], source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        font_sha256=hashlib.sha256((ROOT / 'demos/pixel-ui/fonts/Silkscreen-Regular.ttf').read_bytes()).hexdigest(),
        files=hashes))
    publish({args.out_dir / name: payload for name, payload in payloads.items()}, force=args.force)
    print(json.dumps(dict(out_dir=str(args.out_dir.resolve()), files=len(artifacts) + 1,
        changed_pixels=artifacts['verification.json']['changed_rgba_pixels'], changed_outside=0)))


if __name__ == '__main__':
    main()
