#!/usr/bin/env python3
# 像素参数渲染器 demo：模拟 LLM 输出"半幅网格 + 镜像"规格 -> 确定性渲染 16x16 PNG
import os
from PIL import Image

# ---------- 以下就是全部的"LLM 输出"：128 个字符 + 4 色调色板 ----------
SPEC = """
........
........
..0000..
.0hrrr0.
.0rrrrrr
.0rrrrrr
.0rrrrrr
.0rrrrrr
..0rrrrr
...0Rrrr
....0Rrr
.....0Rr
......0R
.......0
........
........
"""
PALETTE = {
    '.': None,                 # 透明
    '0': (26, 8, 8, 255),      # 描边
    'h': (255, 158, 158, 255), # 高光
    'r': (229, 57, 53, 255),   # 主红
    'R': (139, 26, 26, 255),   # 暗部
}
# -------------------------------------------------------------------

rows = [r for r in SPEC.strip('\n').split('\n')]
full_rows = [r + r[::-1] for r in rows]   # 半幅镜像 -> 完整 16x16
W, H = len(full_rows[0]), len(full_rows)

img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
px = img.load()
for y, row in enumerate(full_rows):
    assert len(row) == W, f'row {y} width mismatch'
    for x, ch in enumerate(row):
        c = PALETTE.get(ch)
        if c:
            px[x, y] = c

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(out, exist_ok=True)
img.save(os.path.join(out, 'heart_16x16.png'))  # 真正进模组的资产

# 最近邻放大预览 + 棋盘格背景展示透明通道
preview = img.resize((256, 256), Image.NEAREST)
bg = Image.new('RGBA', (256, 256))
for by in range(16):
    for bx in range(16):
        col = (62, 62, 62, 255) if (bx + by) % 2 == 0 else (44, 44, 44, 255)
        for yy in range(16):
            for xx in range(16):
                bg.putpixel((bx * 16 + xx, by * 16 + yy), col)
Image.alpha_composite(bg, preview).save(os.path.join(out, 'heart_preview.png'))
print('OK', W, 'x', H)
