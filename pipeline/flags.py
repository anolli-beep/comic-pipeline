"""Simplified flags for comic panels (drawn, no images). Fine detail such as emblems and text is left
out on purpose: at comic scale it would be illegible, and a wrong copy of an emblem is worse than none.
Unknown names fall back to a plain grey flag; "stripes" lets a plan describe any striped flag."""
from __future__ import annotations

import math

from . import kit

FLAGS = ("us", "uk", "eu", "un", "nato", "israel", "palestine", "ukraine", "russia", "iran", "lebanon", "qatar",
         "uae", "france", "germany", "poland", "turkey", "china", "japan", "canada", "italy", "spain", "netherlands",
         "belarus", "georgia", "white")


def _h_stripes(cr, w, h, cols):
    for i, c in enumerate(cols):
        cr.rectangle(0, h * i / len(cols), w, h / len(cols) + 1)
        cr.set_source_rgb(*kit.rgb(c))
        cr.fill()


def _v_stripes(cr, w, h, cols):
    for i, c in enumerate(cols):
        cr.rectangle(w * i / len(cols), 0, w / len(cols) + 1, h)
        cr.set_source_rgb(*kit.rgb(c))
        cr.fill()


def _star(cr, x, y, r, points=5, inner=0.42):
    cr.move_to(x, y - r)
    for j in range(1, points * 2):
        a = -math.pi / 2 + j * math.pi / points
        rr = r if j % 2 == 0 else r * inner
        cr.line_to(x + rr * math.cos(a), y + rr * math.sin(a))
    cr.close_path()


def draw_face(cr, w, h, name, stripes=None):
    """Draw the flag's face into the rectangle (0, 0, w, h)."""
    n = (name or "").lower()
    if n == "stripes" or (not n and stripes):
        (_v_stripes if (stripes or {}).get("vertical") else _h_stripes)(cr, w, h, (stripes or {}).get("colours", ["#888"]))
    elif n == "us":
        for i in range(13):
            cr.rectangle(0, h * i / 13, w, h / 13 + 1)
            cr.set_source_rgb(*((0.75, 0.13, 0.2) if i % 2 == 0 else (1, 1, 1)))
            cr.fill()
        cr.rectangle(0, 0, w * 0.4, h * 7 / 13)
        cr.set_source_rgb(0.16, 0.2, 0.42)
        cr.fill()
        for r in range(5):
            for c in range(6):
                cr.arc(w * 0.035 + c * w * 0.066, h * 0.06 + r * h * 0.1, max(1, h * 0.018), 0, 2 * math.pi)
                cr.set_source_rgb(1, 1, 1)
                cr.fill()
    elif n == "uk":
        cr.set_source_rgb(0.0, 0.14, 0.49)
        cr.paint()
        for lw, col in ((h * 0.2, (1, 1, 1)), (h * 0.07, (0.78, 0.06, 0.18))):
            cr.set_line_width(lw)
            cr.set_source_rgb(*col)
            cr.move_to(0, 0); cr.line_to(w, h); cr.move_to(w, 0); cr.line_to(0, h); cr.stroke()
        for lw, col in ((h * 0.33, (1, 1, 1)), (h * 0.2, (0.78, 0.06, 0.18))):
            cr.set_line_width(lw)
            cr.set_source_rgb(*col)
            cr.move_to(w / 2, 0); cr.line_to(w / 2, h); cr.move_to(0, h / 2); cr.line_to(w, h / 2); cr.stroke()
    elif n == "eu":
        cr.set_source_rgb(0.0, 0.2, 0.6)
        cr.paint()
        for i in range(12):
            a = i * math.pi / 6
            _star(cr, w / 2 + h * 0.33 * math.cos(a), h / 2 + h * 0.33 * math.sin(a), h * 0.055)
            cr.set_source_rgb(1, 0.8, 0)
            cr.fill()
    elif n == "un":
        cr.set_source_rgb(0.29, 0.57, 0.86)
        cr.paint()
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(max(1.5, h * 0.025))
        for rr in (0.12, 0.2, 0.28):
            cr.arc(w / 2, h / 2, h * rr, 0, 2 * math.pi)
            cr.stroke()
        cr.move_to(w / 2 - h * 0.28, h / 2); cr.line_to(w / 2 + h * 0.28, h / 2)
        cr.move_to(w / 2, h / 2 - h * 0.28); cr.line_to(w / 2, h / 2 + h * 0.28)
        cr.stroke()
    elif n == "nato":
        cr.set_source_rgb(0.0, 0.16, 0.36)
        cr.paint()
        _star(cr, w / 2, h / 2, h * 0.3, 4, 0.25)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
    elif n == "israel":
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        for y in (0.1, 0.78):
            cr.rectangle(0, h * y, w, h * 0.12)
            cr.set_source_rgb(0.0, 0.22, 0.72)
            cr.fill()
        r = h * 0.2
        cr.set_line_width(max(1.5, h * 0.035))
        cr.set_source_rgb(0.0, 0.22, 0.72)
        for rot in (0, math.pi):
            cr.move_to(w / 2 + r * math.cos(-math.pi / 2 + rot), h / 2 + r * math.sin(-math.pi / 2 + rot))
            for j in (1, 2):
                a = -math.pi / 2 + rot + j * 2 * math.pi / 3
                cr.line_to(w / 2 + r * math.cos(a), h / 2 + r * math.sin(a))
            cr.close_path()
            cr.stroke()
    elif n == "palestine":
        _h_stripes(cr, w, h, ["#000000", "#ffffff", "#007a3d"])
        cr.move_to(0, 0); cr.line_to(w * 0.4, h / 2); cr.line_to(0, h); cr.close_path()
        cr.set_source_rgb(0.81, 0.07, 0.15)
        cr.fill()
    elif n == "ukraine":
        _h_stripes(cr, w, h, ["#0057b7", "#ffd700"])
    elif n == "russia":
        _h_stripes(cr, w, h, ["#ffffff", "#0039a6", "#d52b1e"])
    elif n == "iran":
        _h_stripes(cr, w, h, ["#239f40", "#ffffff", "#da0000"])
    elif n == "lebanon":
        _h_stripes(cr, w, h, ["#ed1c24", "#ffffff", "#ffffff", "#ed1c24"])
        cr.move_to(w / 2, h * 0.3); cr.line_to(w / 2 + h * 0.2, h * 0.68); cr.line_to(w / 2 - h * 0.2, h * 0.68)
        cr.close_path()
        cr.set_source_rgb(0, 0.65, 0.32)
        cr.fill()
    elif n == "qatar":
        cr.set_source_rgb(0.54, 0.08, 0.24)
        cr.paint()
        cr.move_to(0, 0)
        cr.line_to(w * 0.3, 0)
        for i in range(9):
            y0 = h * i / 9
            cr.line_to(w * 0.38, y0 + h / 18)
            cr.line_to(w * 0.3, y0 + h / 9)
        cr.line_to(0, h)
        cr.close_path()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
    elif n == "uae":
        _h_stripes(cr, w, h, ["#00732f", "#ffffff", "#000000"])
        cr.rectangle(0, 0, w * 0.26, h)
        cr.set_source_rgb(1, 0, 0)
        cr.fill()
    elif n == "france":
        _v_stripes(cr, w, h, ["#002395", "#ffffff", "#ed2939"])
    elif n == "italy":
        _v_stripes(cr, w, h, ["#009246", "#ffffff", "#ce2b37"])
    elif n == "germany":
        _h_stripes(cr, w, h, ["#000000", "#dd0000", "#ffce00"])
    elif n == "netherlands":
        _h_stripes(cr, w, h, ["#ae1c28", "#ffffff", "#21468b"])
    elif n == "spain":
        _h_stripes(cr, w, h, ["#aa151b", "#f1bf00", "#f1bf00", "#aa151b"])
    elif n == "poland":
        _h_stripes(cr, w, h, ["#ffffff", "#dc143c"])
    elif n == "belarus":
        _h_stripes(cr, w, h, ["#c8313e", "#c8313e", "#4aa657"])
    elif n == "georgia":
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        cr.rectangle(w * 0.43, 0, w * 0.14, h); cr.rectangle(0, h * 0.4, w, h * 0.2)
        cr.set_source_rgb(1, 0, 0)
        cr.fill()
    elif n == "turkey":
        cr.set_source_rgb(0.89, 0.04, 0.09)
        cr.paint()
        cr.arc(w * 0.38, h / 2, h * 0.25, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        cr.arc(w * 0.42, h / 2, h * 0.2, 0, 2 * math.pi)
        cr.set_source_rgb(0.89, 0.04, 0.09)
        cr.fill()
        _star(cr, w * 0.58, h / 2, h * 0.12)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
    elif n == "china":
        cr.set_source_rgb(0.87, 0.16, 0.06)
        cr.paint()
        _star(cr, w * 0.17, h * 0.27, h * 0.15)
        for x, y in ((0.33, 0.1), (0.4, 0.2), (0.4, 0.35), (0.33, 0.45)):
            _star(cr, w * x, h * y, h * 0.05)
        cr.set_source_rgb(1, 0.87, 0)
        cr.fill()
    elif n == "japan":
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        cr.arc(w / 2, h / 2, h * 0.3, 0, 2 * math.pi)
        cr.set_source_rgb(0.74, 0.0, 0.18)
        cr.fill()
    elif n == "canada":
        _v_stripes(cr, w, h, ["#ff0000", "#ffffff", "#ffffff", "#ff0000"])
        _star(cr, w / 2, h / 2, h * 0.25, 7, 0.5)
        cr.set_source_rgb(1, 0, 0)
        cr.fill()
    elif n == "white":
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
    else:
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.paint()


def flag(cr, x, y, w, h, name, t=0.0, wave=True, stripes=None, pole=True):
    """A waving flag whose top-left corner is at (x, y)."""
    import cairo
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, int(w)), max(1, int(h)))
    c = cairo.Context(surf)
    draw_face(c, int(w), int(h), name, stripes)
    if pole:
        cr.rectangle(x - w * 0.04, y - h * 0.08, w * 0.04, h * 2.2)
        kit.inked(cr, (0.55, 0.45, 0.35), 2)
    cols = 24
    for i in range(cols):
        u = i / cols
        dy = (math.sin(t * 3 - u * 6) * h * 0.06 * u) if wave else 0
        cr.save()
        cr.rectangle(x + u * w, y + dy, w / cols + 1, h)
        cr.clip()
        cr.set_source_surface(surf, x, y + dy)
        cr.paint()
        cr.restore()
        shade = 0.12 * math.sin(t * 3 - u * 6) if wave else 0
        if shade > 0:
            cr.rectangle(x + u * w, y + dy, w / cols + 1, h)
            cr.set_source_rgba(0, 0, 0, shade)
            cr.fill()
    cr.rectangle(x, y, w, h)
    cr.set_source_rgb(*kit.INK)
    cr.set_line_width(2.5)
    cr.stroke()
