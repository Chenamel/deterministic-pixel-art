#!/usr/bin/env python3
# 绘制指令 DSL demo：LLM 输出指令列表 -> 确定性渲染 MC 风格 GUI
import os
from PIL import Image

def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

class Canvas:
    def __init__(self, w, h):
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.px = self.img.load()
        self.w, self.h = w, h
    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c
    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)
    def bevel(self, x, y, w, h, tl, br, t=1):
        for i in range(t):
            for xx in range(x, x + w):
                self.put(xx, y + i, tl)
                self.put(xx, y + h - 1 - i, br)
            for yy in range(y, y + h):
                self.put(x + i, yy, tl)
                self.put(x + w - 1 - i, yy, br)

# 按钮三态配色（vanilla 风格）
BTN_STYLE = {
    'NORMAL':  dict(border='1B1B1B', fill='8B8B8B', tl='A8A8A8', br='5A5A5A'),
    'HOVER':   dict(border='E0E0FF', fill='8FA2E0', tl='B8C4F0', br='5A6BB0'),
    'PRESSED': dict(border='1B1B1B', fill='5F5F5F', tl='3F3F3F', br='8B8B8B'),
}

def op_slot(cv, x, y):
    cv.rect(x, y, 18, 18, hx('8B8B8B'))
    cv.bevel(x, y, 18, 18, hx('373737'), hx('FFFFFF'), 1)  # 凹陷

def op_btn(cv, x, y, w, h, state):
    s = {k: hx(v) for k, v in BTN_STYLE[state].items()}
    cv.rect(x, y, w, h, s['border'])
    cv.rect(x + 1, y + 1, w - 2, h - 2, s['fill'])
    cv.bevel(x + 1, y + 1, w - 2, h - 2, s['tl'], s['br'], 1)

def render(spec):
    cv = None
    for line in spec.strip().splitlines():
        p = line.split()
        if not p:
            continue
        op = p[0]
        if op == 'CANVAS':
            cv = Canvas(int(p[1]), int(p[2]))
        elif op == 'BG':
            cv.rect(0, 0, cv.w, cv.h, hx(p[1]))
        elif op == 'BEVEL':
            cv.bevel(*map(int, p[1:5]), hx(p[5]), hx(p[6]), int(p[7]))
        elif op == 'SLOT':
            op_slot(cv, int(p[1]), int(p[2]))
        elif op == 'BTN':
            op_btn(cv, *map(int, p[1:5]), p[5])
    return cv.img

# ---------- 以下就是全部的"LLM 输出" ----------
SPEC_PANEL = """
CANVAS 128 48
BG C6C6C6
BEVEL 0 0 128 48 FFFFFF 555555 1
BEVEL 1 1 126 46 DBDBDB 8B8B8B 1
SLOT 8 8
SLOT 30 8
SLOT 52 8
BTN 74 15 46 18 NORMAL
"""

SPEC_BUTTONS = """
CANVAS 44 46
BG C6C6C6
BTN 2 1 40 14 NORMAL
BTN 2 16 40 14 HOVER
BTN 2 31 40 14 PRESSED
"""
# ----------------------------------------------

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(out, exist_ok=True)

panel = render(SPEC_PANEL)
panel.save(os.path.join(out, 'gui_panel_128x48.png'))
panel.resize((panel.width * 3, panel.height * 3), Image.NEAREST).save(
    os.path.join(out, 'gui_panel_preview.png'))

btns = render(SPEC_BUTTONS)
btns.save(os.path.join(out, 'btn_states_44x46.png'))
btns.resize((btns.width * 4, btns.height * 4), Image.NEAREST).save(
    os.path.join(out, 'btn_states_preview.png'))

print('OK panel', panel.size, 'buttons', btns.size)
