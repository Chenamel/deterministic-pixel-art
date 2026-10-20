#!/usr/bin/env python3
# 红石图标传统风格候选：
#   候选A 红石火把亮灭组（传统物流/科技模组语言）candidate_torch.png
#   候选B 原版信号强度豆组（无火把约束内最原版）candidate_signal.png
# 均 48x16，三格 16x16：高电平 / 低电平 / 忽略
import os
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)

def hx(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

def px_put(px, x, y, c):
    if 0 <= x < 48 and 0 <= y < 16:
        px[x, y] = c

def rect(px, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px_put(px, xx, yy, c)

# ================= 候选A：红石火把亮灭组 =================
HEAD_LIT_RING  = hx('A02020')   # 亮火炬头部外圈
HEAD_LIT_CORE  = hx('FF6A5A')   # 亮火炬头部热核
HEAD_OFF_RING  = hx('5E2020')   # 熄灭火炬头部外圈
HEAD_OFF_CORE  = hx('7E3030')   # 熄灭火炬头部暗核
HEAD_GRAY_RING = hx('555555')   # 灰化火炬头部外圈
HEAD_GRAY_CORE = hx('6E6E6E')   # 灰化火炬头部内芯
SHAFT_L = hx('7A5A3E')          # 木杆受光面
SHAFT_D = hx('4E3A28')          # 木杆背光面
SHAFT_TIP = hx('3E2E20')        # 木杆底端
SPARK = hx('FF7A6A')            # 点亮火花
SLASH = hx('4A4A4A')            # 忽略态斜杠

def draw_torch(px, ox, ring, core, shaft_l, shaft_d, lit=False):
    # 头部 4x4：x=ox+6..ox+9, y=2..5
    rect(px, ox + 6, 2, 4, 4, ring)
    rect(px, ox + 7, 3, 2, 2, core)
    # 木杆 2x7：x=ox+7..ox+8, y=6..12
    rect(px, ox + 7, 6, 1, 7, shaft_d)
    rect(px, ox + 8, 6, 1, 7, shaft_l)
    px_put(px, ox + 7, 12, SHAFT_TIP)
    px_put(px, ox + 8, 12, SHAFT_TIP)
    if lit:  # 点亮火花（原版粒子感）
        px_put(px, ox + 4, 3, SPARK)
        px_put(px, ox + 11, 2, SPARK)
        px_put(px, ox + 10, 6, SPARK)

imgA = Image.new('RGBA', (48, 16), (0, 0, 0, 0))
pa = imgA.load()
draw_torch(pa, 0, HEAD_LIT_RING, HEAD_LIT_CORE, SHAFT_L, SHAFT_D, lit=True)      # 高电平：点亮
draw_torch(pa, 16, HEAD_OFF_RING, HEAD_OFF_CORE, SHAFT_L, SHAFT_D, lit=False)    # 低电平：熄灭
draw_torch(pa, 32, HEAD_GRAY_RING, HEAD_GRAY_CORE, hx('6E6E6E'), hx('555555'))   # 忽略：灰化
for x in range(3, 13):  # 忽略态叠加斜杠（左下到右上）
    px_put(pa, 32 + x, 15 - x, SLASH)
imgA.save(os.path.join(OUT, 'candidate_torch.png'))

# ================= 候选B：原版信号强度豆组 =================
PIP_TL = hx('FF5A5A')   # 亮豆高光
PIP_M  = hx('E03E3E')   # 亮豆主色
PIP_BR = hx('A82828')   # 亮豆暗角
OFF_TL = hx('5A5A5A')   # 灭豆
OFF_BR = hx('3E3E3E')
DASH   = hx('6E6E6E')   # 忽略态虚线（旁路）

def draw_pip(px, ox, pipx, tl, m, br):
    px_put(px, ox + pipx, 7, tl)
    px_put(px, ox + pipx + 1, 7, m)
    px_put(px, ox + pipx, 8, m)
    px_put(px, ox + pipx + 1, 8, br)

imgB = Image.new('RGBA', (48, 16), (0, 0, 0, 0))
pb = imgB.load()
for i in range(4):                       # 高电平：四豆全亮
    draw_pip(pb, 0, 3 + i * 3, PIP_TL, PIP_M, PIP_BR)
draw_pip(pb, 16, 3, PIP_TL, PIP_M, PIP_BR)   # 低电平：仅首豆亮
for i in range(1, 4):
    draw_pip(pb, 16, 3 + i * 3, OFF_TL, OFF_TL, OFF_BR)
for dx0 in (3, 7, 11):                 # 忽略：灰色虚线直通（三段 2x2）
    rect(pb, 32 + dx0, 7, 2, 2, DASH)
imgB.save(os.path.join(OUT, 'candidate_signal.png'))

# ================= 预览（按钮灰底 10x） =================
def preview(im, name):
    bg = Image.new('RGBA', (im.width * 10, im.height * 10), hx('C6C6C6'))
    bg.alpha_composite(im.resize((im.width * 10, im.height * 10), Image.NEAREST))
    bg.save(os.path.join(OUT, name))

preview(imgA, 'candidate_torch_preview.png')
preview(imgB, 'candidate_signal_preview.png')
print('OK')
