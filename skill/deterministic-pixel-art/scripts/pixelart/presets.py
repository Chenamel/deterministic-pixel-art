"""Opt-in Minecraft demo styles, separate from general pixel rendering."""
from .core import PixelArtError

BUTTONS = {
    'NORMAL': dict(border='1B1B1B', fill='8B8B8B', tl='A8A8A8', br='5A5A5A'),
    'HOVER': dict(border='E0E0FF', fill='8FA2E0', tl='B8C4F0', br='5A6BB0'),
    'PRESSED': dict(border='1B1B1B', fill='5F5F5F', tl='3F3F3F', br='8B8B8B'),
    'SELECTED': dict(border='373737', fill='A0A0A0', tl='555555', br='FFFFFF'),
    'DISABLED': dict(border='373737', fill='707070', tl='7A7A7A', br='666666'),
}


def button(canvas, x, y, w, h, state, *, clip=False):
    if state not in BUTTONS:
        raise PixelArtError(f'button.state: expected one of {list(BUTTONS)}')
    if w < 4 or h < 4:
        raise PixelArtError('button: minimum size is 4x4')
    s = BUTTONS[state]
    canvas.rect(x, y, w, h, s['border'], clip=clip)
    canvas.rect(x + 1, y + 1, w - 2, h - 2, s['fill'], clip=clip)
    canvas.bevel(x + 1, y + 1, w - 2, h - 2, s['tl'], s['br'], clip=clip)


def slot(canvas, x, y, *, clip=False):
    canvas.rect(x, y, 18, 18, '8B8B8B', clip=clip)
    canvas.bevel(x, y, 18, 18, '373737', 'FFFFFF', clip=clip)
