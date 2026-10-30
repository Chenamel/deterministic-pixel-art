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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'docs/images/overview.png')
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build().save(args.out)
    print(args.out)
