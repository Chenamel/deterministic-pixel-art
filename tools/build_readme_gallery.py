"""Compose the README gallery from existing original assets; never repaint them."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PANELS = (
    ('Icons / named atlas', 'demos/pixel-ui/assets/icons.png', 5),
    ('Editable UI states', 'demos/pixel-ui/assets/revised/buttons.png', 2),
    ('Native 128 x 128 sprite', 'examples/workflows/sprite-128.png', 2),
    ('256 x 256 / four source chunks', 'demos/chunk-scene/assets/scene.png', 1),
)


def build():
    sheet = Image.new('RGB', (880, 720), '#111A28')
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.load_default(size=17)
    detail_font = ImageFont.load_default(size=12)
    for index, (title, filename, scale) in enumerate(PANELS):
        x, y = 16 + (index % 2) * 432, 16 + (index // 2) * 352
        draw.rounded_rectangle((x, y, x + 415, y + 335), radius=8,
                               fill='#182637', outline='#33445A', width=1)
        draw.text((x + 16, y + 13), title, font=title_font, fill='#E9EDF2')
        with Image.open(ROOT / filename) as source:
            image = source.convert('RGBA')
        native_size = image.size
        detail = f'{native_size[0]} x {native_size[1]} px'
        if filename.endswith('/buttons.png'):
            layout = json.loads((ROOT / filename).with_name('layout.json').read_text(encoding='utf-8'))
            cells = layout['atlas']['cells']
            image_grid = Image.new('RGBA', (192, 54))
            for cell_index, cell in enumerate(cells):
                tile = image.crop((cell['x'], cell['y'], cell['x'] + cell['w'], cell['y'] + cell['h']))
                image_grid.paste(tile, ((cell_index % 2) * 96, (cell_index // 2) * 18))
            image = image_grid
            detail = '6 states / 96 x 18 px each'
        image = image.resize((image.width * scale, image.height * scale),
                             Image.Resampling.NEAREST)
        if image.width > 384 or image.height > 256:
            raise ValueError(f'Gallery panel does not fit without resampling: {filename}')
        origin = (x + (416 - image.width) // 2, y + 48 + (256 - image.height) // 2)
        sheet.paste(image, origin, image)
        draw.text((x + 16, y + 317),
                  f'{detail}  |  {scale}x nearest-neighbor',
                  font=detail_font, fill='#9AAFC5')
    return sheet


def build_scoped_edit():
    """Show the existing atlas edit and its exact RGBA difference at 4x."""
    images = []
    for name in ('atlas-before.png', 'atlas-final.png'):
        with Image.open(ROOT / 'examples/workflows' / name) as source:
            images.append(source.convert('RGBA'))
    before, after = images
    layout = json.loads((ROOT / 'examples/workflows/atlas-before-layout.json').read_text(encoding='utf-8'))
    labels = [cell['name'] for cell in layout['atlas']['cells']]
    if before.size != (64, 16) or after.size != before.size:
        raise ValueError('Expected matching four-cell 16px atlases')
    mask = Image.new('RGB', before.size, '#33445A')
    changed = []
    for y in range(before.height):
        for x in range(before.width):
            if before.getpixel((x, y)) != after.getpixel((x, y)):
                changed.append((x, y))
                mask.putpixel((x, y), (255, 186, 86))
    if not changed or any(not (32 <= x < 48 and 0 <= y < 16) for x, y in changed):
        raise ValueError('Expected a nonempty change confined to the transfer cell')
    sheet = Image.new('RGB', (880, 200), '#111A28')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    small = ImageFont.load_default(size=11)
    for index, (title, image) in enumerate(zip(
            ('Before', 'After / transfer replaced', 'Changed RGBA pixels'),
            (before, after, mask))):
        x = 16 + index * 288
        draw.rounded_rectangle((x, 12, x + 271, 157), radius=6,
                               fill='#182637', outline='#33445A')
        draw.text((x + 8, 22), title, font=font, fill='#E9EDF2')
        for cell, label in enumerate(labels):
            draw.text((x + 10 + cell * 64, 48), label, font=small, fill='#9AAFC5')
        enlarged = image.resize((256, 64), Image.Resampling.NEAREST)
        if image.mode == 'RGBA':
            sheet.paste(enlarged, (x + 8, 72), enlarged)
        else:
            sheet.paste(enlarged, (x + 8, 72))
        draw.rectangle((x + 135, 70, x + 200, 137), outline='#FFBA56')
    draw.text((24, 174), f'4x nearest-neighbor | {len(changed)} changed pixels inside transfer | 0 outside',
              font=font, fill='#E9EDF2')
    return sheet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--view', choices=('overview', 'scoped-edit'), default='overview')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.out is None:
        args.out = ROOT / 'docs/images' / f'{args.view}.png'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    (build() if args.view == 'overview' else build_scoped_edit()).save(args.out)
    print(args.out)
