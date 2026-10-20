#!/usr/bin/env python3
# GUI 资产确定性渲染：face_selector_button.png (22x110) + view_control_icons.png (48x16)
# 规则：GUI 1x 逻辑像素、RGBA、最近邻、无抗锯齿
import math
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)

def hx(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

# ================= 图1：face_selector_button.png 22x110 =================
BORDER = hx('000000')
STATES = [
    # (fill, bevel左上, bevel右下) —— 凸起态: 左上亮右下暗；按下/选中态: 反转(凹陷)
    dict(fill='8B8B8B', tl='A8A8A8', br='5A5A5A'),  # Y=0   普通
    dict(fill='8FA2E0', tl='C0CBF0', br='5A6BB0'),  # Y=22  悬停(原版高亮蓝调)
    dict(fill='5F5F5F', tl='3F3F3F', br='8B8B8B'),  # Y=44  瞬间按下(凹陷,深灰)
    dict(fill='4F5D9E', tl='2F3866', br='7E8AC0'),  # Y=66  持续选中(凹陷,深蓝,区别于按下)
    dict(fill='707070', tl='7A7A7A', br='666666'),  # Y=88  禁用(发灰发死,几乎无凹凸)
]

btn = Image.new('RGBA', (22, 110), (0, 0, 0, 0))
px = btn.load()

def rect(img_px, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            img_px[xx, yy] = c

for i, st in enumerate(STATES):
    oy = i * 22
    fill, tl, br = hx(st['fill']), hx(st['tl']), hx(st['br'])
    rect(px, 0, oy, 22, 22, BORDER)          # 1px 外边框
    rect(px, 1, oy + 1, 20, 20, fill)        # 按钮面
    rect(px, 1, oy + 1, 20, 1, tl)           # 上
    rect(px, 1, oy + 1, 1, 20, tl)           # 左
    rect(px, 1, oy + 20, 20, 1, br)          # 下
    rect(px, 20, oy + 1, 1, 20, br)          # 右
    # (3,3) 起的 16x16 动态内容区保持纯 fill，图标由代码叠加

btn.save(os.path.join(OUT, 'face_selector_button.png'))

# ================= 图2：view_control_icons.png 48x16 =================
DARK  = hx('1B1B1B')
LIGHT = hx('E8E8E8')
MID   = hx('A8A8A8')
SHADE = hx('707070')

icons = Image.new('RGBA', (48, 16), (0, 0, 0, 0))
ipx = icons.load()

# --- 图标1 (X=0)：2D 六面展开图（十字形，纯矩形，像素完美） ---
# 深色十字轮廓（含 1px 外描边与 1px 面间缝线）
rect(ipx, 6, 0, 5, 16, DARK)    # 竖条 x=6..10, y=0..15
rect(ipx, 2, 4, 13, 5, DARK)    # 横条 x=2..14, y=4..8
# 六个 3x3 亮面（间距 1px 缝线）
faces = [(7, 1), (3, 5), (7, 5), (11, 5), (7, 9), (7, 13)]
for fx, fy in faces:
    rect(ipx, fx, fy, 3, 3, LIGHT)

# --- 图标2 (X=16)：3D 立方体（等距，多边形填充 + 1px 描边） ---
d2 = ImageDraw.Draw(icons)
OX = 16
sil = [(OX+8,1),(OX+14,4),(OX+14,10),(OX+8,13),(OX+2,10),(OX+2,4)]
d2.polygon([(OX+8,1),(OX+14,4),(OX+8,7),(OX+2,4)], fill=LIGHT)          # 顶面
d2.polygon([(OX+2,4),(OX+8,7),(OX+8,13),(OX+2,10)], fill=MID)           # 左面
d2.polygon([(OX+8,7),(OX+14,4),(OX+14,10),(OX+8,13)], fill=SHADE)       # 右面
for a, b in zip(sil, sil[1:] + sil[:1]):
    d2.line([a, b], fill=DARK, width=1)                                  # 外轮廓
for a, b in [((OX+2,4),(OX+8,7)), ((OX+8,7),(OX+14,4)), ((OX+8,7),(OX+8,13))]:
    d2.line([a, b], fill=DARK, width=1)                                  # 内棱

# --- 图标3 (X=32)：重置视角（顺时针环形箭头，距离带 + 三角箭头） ---
CX, CY = 8.0, 8.0
for y in range(16):
    for x in range(32, 48):
        dx, dy = x - CX - 32, y - CY
        dist = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx))      # 0=右，顺时针增大(屏幕坐标)
        a2 = (ang + 45) % 360                       # -45° 归零
        if a2 <= 270:                               # 270° 弧，缺口在上方
            if 3.7 <= dist <= 6.5:
                ipx[x, y] = DARK
            if 4.5 <= dist <= 5.7:
                ipx[x, y] = LIGHT
# 箭头（位于弧起点 θ=-45°，指向顺时针方向）
u = (math.cos(math.radians(-45)), math.sin(math.radians(-45)))
t = (-u[1], u[0])                                    # 顺时针切向
n = (-t[1], t[0])
E = (CX + 32 + 5.1 * u[0], CY + 5.1 * u[1])
def V(base, k, v):  return (base[0] + k * v[0], base[1] + k * v[1])
tip, b1, b2 = V(E, 2.6, t), V(V(E, -0.8, t), 2.4, n), V(V(E, -0.8, t), -2.4, n)
d2.polygon([tip, b1, b2], fill=DARK)
tip2, c1, c2 = V(E, 1.2, t), V(V(E, -0.5, t), 1.1, n), V(V(E, -0.5, t), -1.1, n)
d2.polygon([tip2, c1, c2], fill=LIGHT)

icons.save(os.path.join(OUT, 'view_control_icons.png'))

# ================= 预览图（最近邻放大，GUI 灰底 #C6C6C6） =================
def preview(img, scale, path):
    bg = Image.new('RGBA', (img.width * scale, img.height * scale), hx('C6C6C6'))
    bg.alpha_composite(img.resize((img.width * scale, img.height * scale), Image.NEAREST))
    bg.save(path)

preview(btn, 6, os.path.join(OUT, 'face_selector_button_preview.png'))
preview(icons, 10, os.path.join(OUT, 'view_control_icons_preview.png'))
print('OK', btn.size, icons.size)
