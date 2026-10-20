#!/usr/bin/env python3
# editor_redstone_icons.png v2 —— 按 Codex 反馈返修（A 版机械结构保留，配色重做）
# 变更：导轨纯白→浅灰层级；红色降饱和靠 E36B6B；滑块改红（高/低档）；
#       旁路简化为中央 2x2 机械桥墩；主体灰阶 373737/4E4E4E/5A5A5A/6E6E6E
import os
import shutil
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)

def hx(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

# ---- 配色（全部取自 Codex 指定灰阶 + 降饱和红） ----
GROOVE  = hx('4E4E4E')   # 导轨凹槽内芯
GVDARK  = hx('373737')   # 导轨左缘（暗）
GVLITE  = hx('A0A0A0')   # 导轨右缘（浅灰，替代纯白）
GVSPARK = hx('C6C6C6')   # 少量浅色高光（右缘顶点 1px）
PAD_OFF = hx('5A5A5A')   # 触点（未激活）
PAD_ON  = hx('E36B6B')   # 触点（激活，与输出模式同红）
RS_TOP  = hx('E36B6B')   # 红色滑块 上表面
RS_BOT  = hx('A84848')   # 红色滑块 下表面（更暗红阴影，不发光）
RS_END  = hx('6E3232')   # 红色滑块 端面
NS_TOP  = hx('C6C6C6')   # 中档中性滑块 上表面
NS_BOT  = hx('6E6E6E')   # 中档中性滑块 下表面
NS_END  = hx('373737')   # 中档中性滑块 端面
BYPASS  = hx('5A5A5A')   # 中央机械桥墩

def rect(px, ox, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= ox + xx < 48 and 0 <= yy < 16:
                px[ox + xx, yy] = c

def draw_switch(px, ox, knob_y, top_on, bot_on, red_knob, bypass):
    # 导轨（三格完全一致）：x=5..10, y=3..12
    rect(px, ox, 5, 3, 6, 10, GROOVE)
    rect(px, ox, 5, 3, 1, 10, GVDARK)
    rect(px, ox, 10, 3, 1, 10, GVLITE)
    px[ox + 10, 3] = GVSPARK                 # 少量浅色高光
    # 上下触点条 x=4..11
    rect(px, ox, 4, 2, 8, 1, PAD_ON if top_on else PAD_OFF)
    rect(px, ox, 4, 13, 8, 1, PAD_ON if bot_on else PAD_OFF)
    # 中档旁路：水平止位线（仅内芯宽度 x=6..9，不切断导轨缘，三格导轨保持完全一致）
    if bypass:
        rect(px, ox, 6, 5, 4, 1, BYPASS)
        rect(px, ox, 6, 10, 4, 1, BYPASS)
    # 滑块 8x2（外形三格一致，仅位置/颜色随状态）
    top = RS_TOP if red_knob else NS_TOP
    bot = RS_BOT if red_knob else NS_BOT
    end = RS_END if red_knob else NS_END
    rect(px, ox, 4, knob_y, 8, 1, top)
    rect(px, ox, 4, knob_y + 1, 8, 1, bot)
    for dx in (0, 7):
        px[ox + 4 + dx, knob_y] = end
        px[ox + 4 + dx, knob_y + 1] = end

# ---- 备份 v1 后重做正式文件 ----
src = os.path.join(OUT, 'editor_redstone_icons.png')
bak = os.path.join(OUT, 'editor_redstone_icons_v1_backup.png')
if os.path.exists(src) and not os.path.exists(bak):
    shutil.copy(src, bak)

img = Image.new('RGBA', (48, 16), (0, 0, 0, 0))
px = img.load()
draw_switch(px, 0, 3, True, False, True, False)    # HIGH_LEVEL：上档红滑块
draw_switch(px, 16, 11, False, True, True, False)  # LOW_LEVEL：下档红滑块
draw_switch(px, 32, 7, False, False, False, True)  # IGNORE：中档 + 旁路桥
img.save(src)

# ---- 常规放大预览（按钮灰底 10x） ----
bg = Image.new('RGBA', (480, 160), hx('C6C6C6'))
bg.alpha_composite(img.resize((480, 160), Image.NEAREST))
bg.save(os.path.join(OUT, 'editor_redstone_icons_preview.png'))

# ---- 1:1 游戏内合成校验：三枚 22x20 普通态按钮 + 图标叠在 (3,2) ----
BTN_BORDER, BTN_FILL, BTN_TL, BTN_BR = hx('373737'), hx('8B8B8B'), hx('A8A8A8'), hx('5A5A5A')
comp = Image.new('RGBA', (68, 20), (0, 0, 0, 0))
cp = comp.load()
for i in range(3):
    bx = i * 23
    rect(cp, 0, bx, 0, 22, 20, BTN_BORDER)
    rect(cp, 0, bx, 1, 20, 18, BTN_FILL)
    rect(cp, 0, bx, 1, 20, 1, BTN_TL)
    rect(cp, 0, bx, 1, 1, 18, BTN_TL)
    rect(cp, 0, bx, 18, 20, 1, BTN_BR)
    rect(cp, 0, bx, 18, 1, 18, BTN_BR)
    comp.alpha_composite(img.crop((i * 16, 0, i * 16 + 16, 16)), (bx + 3, 2))
comp.save(os.path.join(OUT, 'redstone_on_buttons_1to1.png'))
big = Image.new('RGBA', (68 * 8, 20 * 8), hx('C6C6C6'))
big.alpha_composite(comp.resize((68 * 8, 20 * 8), Image.NEAREST))
big.save(os.path.join(OUT, 'redstone_on_buttons_preview.png'))
print('OK v2')
