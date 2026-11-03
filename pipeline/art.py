"""The panel art library. Each art kind draws one comic panel from a plan's panel spec.

Every function is draw(cr, w, h, t, a, th): w/h = panel size in pixels, t = seconds since the panel
appeared, a = the panel spec from the plan, th = theme (accent, caption, paper colours).
ART lists every kind with its options; plans/README.md documents them for plan writers.
"""
from __future__ import annotations

import math
import random

import cairo

from . import flags as F
from . import kit, maps
from .kit import INK, WHITE, background, ease, clamp, inked, rgb


def _bg(cr, w, h, t, a, default):
    background(cr, w, h, t, a.get("bg", default), seed=hash(str(a.get("bg"))) % 97)


def _flag_pair(cr, w, h, t, a, y=0.08, size=0.16):
    fl = a.get("flags") or []
    if len(fl) >= 1 and fl[0]:
        F.flag(cr, w * 0.06, h * y, h * size * 1.6, h * size, fl[0], t)
    if len(fl) >= 2 and fl[1]:
        F.flag(cr, w * 0.94 - h * size * 1.6, h * y, h * size * 1.6, h * size, fl[1], t + 1.3)


# ------------------------------------------------------------------ people
def art_portrait(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "blue_burst")
    if a.get("flag"):
        F.flag(cr, w * 0.62, h * 0.12, h * 0.42, h * 0.27, a["flag"], t)
    size = min(w * 0.7, h * 1.0)
    kit.person(cr, w * 0.5, h * 1.02, size, a.get("who", "official"), t, a.get("mood"),
               talking=bool(a.get("talking")))


def art_duo(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "grey")
    _flag_pair(cr, w, h, t, a)
    size = min(w * 0.42, h * 1.0)
    talk = a.get("talking")
    kit.person(cr, w * 0.28, h * 1.02, size, a.get("who", "official"), t, a.get("mood"), look=1,
               talking=talk in ("who", "left", True))
    kit.person(cr, w * 0.72, h * 1.02, size, a.get("other", "diplomat"), t + 0.7, a.get("other_mood"), look=-1,
               talking=talk in ("other", "right"))


def art_group(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "paper")
    people = a.get("people") or ["official", "general", "diplomat"]
    n = max(1, min(6, len(people)))
    size = min(w / n * 1.05, h * 0.95)
    for i, p in enumerate(people[:n]):
        x = w * (i + 0.5) / n
        kit.person(cr, x, h * 1.02 + (i % 2) * h * 0.04, size, p, t + i * 0.6, look=(0.5 - i / max(1, n - 1)) * 2)


def art_crowd(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "day")
    for i, fl in enumerate(a.get("flags") or []):
        x = w * (0.15 + 0.7 * i / max(1, len(a["flags"]) - 1)) if len(a["flags"]) > 1 else w * 0.5
        F.flag(cr, x, h * 0.18 + 6 * math.sin(t * 2 + i), h * 0.22, h * 0.14, fl, t + i)
    kit.crowd_heads(cr, w, h, h * 0.62, int(a.get("count", 9)), t, signs=a.get("signs") or [],
                    sign_size=max(16, h * 0.045))


def art_podium(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "blue")
    fl = a.get("flags") or []
    for i, f in enumerate(fl[:2]):
        F.flag(cr, w * (0.1 if i == 0 else 0.72), h * 0.08, h * 0.32, h * 0.2, f, t + i)
    size = min(w * 0.55, h * 0.9)
    kit.person(cr, w * 0.5, h * 0.82, size, a.get("who", "president"), t, a.get("mood", "speaking"),
               talking=a.get("talking", True))
    cr.move_to(w * 0.3, h * 0.62)
    cr.line_to(w * 0.7, h * 0.62)
    cr.line_to(w * 0.64, h)
    cr.line_to(w * 0.36, h)
    cr.close_path()
    inked(cr, (0.45, 0.3, 0.18), 4)
    for dx in (-0.04, 0.04):
        cr.move_to(w * (0.5 + dx), h * 0.62)
        cr.line_to(w * (0.5 + dx * 0.5), h * 0.5)
        cr.set_source_rgb(*INK)
        cr.set_line_width(4)
        cr.stroke()
        cr.new_sub_path(); cr.arc(w * (0.5 + dx * 0.5), h * 0.49, h * 0.02, 0, 2 * math.pi)
        inked(cr, (0.2, 0.2, 0.22), 2)
    if a.get("sign"):
        kit.font(cr, "caption", h * 0.045)
        e = cr.text_extents(str(a["sign"]).upper())
        cr.move_to(w * 0.5 - e.x_advance / 2, h * 0.78)
        cr.set_source_rgb(0.95, 0.85, 0.5)
        cr.show_text(str(a["sign"]).upper())


def art_table(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "paper")
    if a.get("label"):
        kit.font(cr, "title", h * 0.09)
        e = cr.text_extents(str(a["label"]).upper())
        rrw = e.x_advance + h * 0.08
        cr.rectangle(w / 2 - rrw / 2, h * 0.05, rrw, h * 0.13)
        inked(cr, (0.16, 0.22, 0.4), 3)
        cr.move_to(w / 2 - e.x_advance / 2, h * 0.155)
        cr.set_source_rgb(1, 1, 1)
        cr.show_text(str(a["label"]).upper())
    size = min(w * 0.36, h * 0.85)
    kit.person(cr, w * 0.24, h * 0.86, size, a.get("who", "diplomat"), t, a.get("mood", "serious"), look=1,
               talking=a.get("talking") == "who", nameplate=False)
    kit.person(cr, w * 0.76, h * 0.86, size, a.get("other", "official"), t + 0.8, a.get("other_mood", "listening"),
               look=-1, talking=a.get("talking") == "other", nameplate=False)
    cr.rectangle(w * 0.04, h * 0.74, w * 0.92, h * 0.08)
    inked(cr, (0.42, 0.28, 0.17), 4)
    cr.rectangle(w * 0.06, h * 0.82, w * 0.88, h * 0.2)
    inked(cr, (0.33, 0.21, 0.12), 4)
    fl = a.get("flags") or []
    for i, f in enumerate(fl[:2]):
        x = w * (0.4 if i == 0 else 0.55)
        cr.rectangle(x + w * 0.025, h * 0.6, 3, h * 0.14)
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.fill()
        F.flag(cr, x + w * 0.025, h * 0.6, h * 0.1, h * 0.065, f, t + i, pole=False)
    for i, key in enumerate(("who", "other")):
        who = kit.person_spec(a.get(key, {}))
        if who.get("name"):
            kit.label_tag(cr, w * (0.24 if i == 0 else 0.76), h * 0.84, who["name"], max(12, h * 0.04))


def art_handshake(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "yellow_burst")
    cols = a.get("sleeves") or ["#1f2a44", "#3a3e46"]
    shake = math.sin(t * 6) * h * 0.015
    for side, col in ((-1, cols[0]), (1, cols[-1])):
        cr.save()
        cr.translate(w / 2, h * 0.55 + shake)
        cr.scale(side, 1)
        cr.move_to(w * 0.55, -h * 0.12)
        cr.line_to(w * 0.08, -h * 0.1)
        cr.line_to(w * 0.08, h * 0.1)
        cr.line_to(w * 0.55, h * 0.14)
        cr.close_path()
        inked(cr, rgb(col), 4)
        kit.rrect(cr, -w * 0.06, -h * 0.1, w * 0.16, h * 0.2, h * 0.07)
        inked(cr, kit.SKIN["fair"] if side < 0 else kit.SKIN["medium"], 4)
        cr.restore()
    _flag_pair(cr, w, h, t, a, y=0.06, size=0.18)


def art_phone_call(cr, w, h, t, a, th):
    cr.set_source_rgb(*INK)
    cr.paint()
    for side, key, bg in ((0, "who", a.get("bg", "blue")), (1, "other", a.get("other_bg", "red"))):
        cr.save()
        cr.rectangle(side * w / 2 + (6 if side else 0), 0, w / 2 - 6, h)
        cr.clip()
        cr.translate(side * w / 2, 0)
        background(cr, w / 2, h, t, bg)
        size = min(w * 0.4, h * 0.95)
        kit.person(cr, w * 0.25, h * 1.02, size, a.get(key, "official"), t + side, a.get("mood"),
                   look=1 if side == 0 else -1, talking=(int(t * 0.5) % 2) == side)
        hx = w * 0.25 + (-1 if side == 0 else 1) * size * 0.27
        cr.save()
        cr.translate(hx, h * 1.02 - size * 0.6)
        cr.rotate(0.35 if side == 0 else -0.35)
        kit.rrect(cr, -size * 0.05, -size * 0.14, size * 0.1, size * 0.3, size * 0.03)
        inked(cr, (0.12, 0.12, 0.14), 3)
        cr.restore()
        cr.restore()
    for i in range(3):
        p = ((t * 1.5 + i / 3) % 1)
        cr.new_sub_path(); cr.arc(w / 2, h * 0.4, h * 0.05 + p * h * 0.15, -0.6, 0.6)
        cr.set_source_rgba(1, 1, 1, 1 - p)
        cr.set_line_width(4)
        cr.stroke()
        cr.arc_negative(w / 2, h * 0.4, h * 0.05 + p * h * 0.15, math.pi + 0.6, math.pi - 0.6)
        cr.stroke()


# ------------------------------------------------------------------ places
def _building(cr, x, base, s, kind, lit, t, accent):
    """One building, centred at x, standing on `base`, scale s (s = its height in px)."""
    wall = (0.92, 0.9, 0.84)
    win = (1, 0.86, 0.45) if lit else (0.18, 0.2, 0.28)
    r = random.Random(hash(kind) % 1000)
    if kind in ("dome", "capitol"):
        cr.rectangle(x - s * 0.9, base - s * 0.45, s * 1.8, s * 0.45)
        inked(cr, wall, 4)
        for i in range(9):
            cr.rectangle(x - s * 0.8 + i * s * 0.2, base - s * 0.42, s * 0.06, s * 0.38)
            inked(cr, (0.98, 0.97, 0.94), 2)
        cr.rectangle(x - s * 0.3, base - s * 0.62, s * 0.6, s * 0.17)
        inked(cr, wall, 4)
        cr.save()
        cr.translate(x, base - s * 0.62)
        cr.scale(1, 1.1)
        cr.new_sub_path(); cr.arc(0, 0, s * 0.28, math.pi, 2 * math.pi)
        cr.restore()
        inked(cr, wall, 4)
        cr.rectangle(x - s * 0.04, base - s * 1.02, s * 0.08, s * 0.1)
        inked(cr, wall, 3)
    elif kind == "columns":
        cr.move_to(x - s * 0.95, base - s * 0.62)
        cr.line_to(x, base - s * 0.9)
        cr.line_to(x + s * 0.95, base - s * 0.62)
        cr.close_path()
        inked(cr, wall, 4)
        cr.rectangle(x - s * 0.9, base - s * 0.62, s * 1.8, s * 0.62)
        inked(cr, wall, 4)
        for i in range(6):
            cr.rectangle(x - s * 0.75 + i * s * 0.3, base - s * 0.58, s * 0.1, s * 0.52)
            inked(cr, (0.98, 0.97, 0.94), 2)
    elif kind == "white_house":
        cr.rectangle(x - s * 1.1, base - s * 0.5, s * 2.2, s * 0.5)
        inked(cr, (0.97, 0.97, 0.95), 4)
        cr.move_to(x - s * 0.35, base - s * 0.5)
        cr.line_to(x, base - s * 0.68)
        cr.line_to(x + s * 0.35, base - s * 0.5)
        cr.close_path()
        inked(cr, (0.97, 0.97, 0.95), 4)
        for i in range(10):
            if abs(i - 4.5) > 1.5:
                cr.rectangle(x - s * 1.0 + i * s * 0.21, base - s * 0.4, s * 0.09, s * 0.12)
                inked(cr, win, 1.5)
        for i in range(4):
            cr.rectangle(x - s * 0.28 + i * s * 0.17, base - s * 0.48, s * 0.05, s * 0.48)
            inked(cr, (1, 1, 1), 1.5)
    elif kind == "towers":
        cr.rectangle(x - s * 1.2, base - s * 0.35, s * 2.4, s * 0.35)
        inked(cr, (0.66, 0.16, 0.13), 4)
        for i in range(-2, 3):
            tx = x + i * s * 0.5
            th_ = s * (0.75 if i == 0 else 0.55)
            cr.rectangle(tx - s * 0.1, base - th_, s * 0.2, th_)
            inked(cr, (0.66, 0.16, 0.13), 3)
            cr.move_to(tx - s * 0.13, base - th_)
            cr.line_to(tx, base - th_ - s * 0.25)
            cr.line_to(tx + s * 0.13, base - th_)
            cr.close_path()
            inked(cr, (0.2, 0.42, 0.3), 3)
        for i in range(14):
            cr.rectangle(x - s * 1.2 + i * s * 0.18, base - s * 0.4, s * 0.09, s * 0.06)
            inked(cr, (0.66, 0.16, 0.13), 1.5)
    elif kind in ("office", "embassy", "hospital", "apartments"):
        bw = s * (0.7 if kind == "office" else 1.1)
        bh = s * (1.0 if kind == "office" else 0.7)
        cr.rectangle(x - bw / 2, base - bh, bw, bh)
        inked(cr, (0.75, 0.78, 0.82) if kind == "office" else wall, 4)
        rows, cols = (8, 5) if kind == "office" else (4, 7)
        for i in range(rows):
            for j in range(cols):
                on = lit and r.random() < 0.75
                cr.rectangle(x - bw / 2 + bw * (j + 0.2) / cols, base - bh + bh * (i + 0.2) / rows,
                             bw / cols * 0.6, bh / rows * 0.55)
                cr.set_source_rgb(*((1, 0.86, 0.45) if on else (0.2, 0.24, 0.32)))
                cr.fill()
        if kind == "hospital":
            cr.rectangle(x - s * 0.06, base - bh - s * 0.25, s * 0.12, s * 0.22)
            cr.rectangle(x - s * 0.13, base - bh - s * 0.17, s * 0.26, s * 0.08)
            cr.set_source_rgb(0.85, 0.1, 0.1)
            cr.fill()
    elif kind in ("refinery", "power_plant", "nuclear_site"):
        for i in range(3):
            tx = x - s * 0.6 + i * s * 0.6
            if kind == "refinery":
                cr.rectangle(tx - s * 0.12, base - s * 0.7, s * 0.24, s * 0.7)
                inked(cr, (0.7, 0.7, 0.68), 3)
                cr.rectangle(tx - s * 0.12, base - s * 0.55, s * 0.24, s * 0.05)
                cr.set_source_rgb(*accent)
                cr.fill()
            else:
                cr.move_to(tx - s * 0.25, base)
                cr.curve_to(tx - s * 0.12, base - s * 0.4, tx - s * 0.18, base - s * 0.7, tx - s * 0.16, base - s * 0.8)
                cr.line_to(tx + s * 0.16, base - s * 0.8)
                cr.curve_to(tx + s * 0.18, base - s * 0.7, tx + s * 0.12, base - s * 0.4, tx + s * 0.25, base)
                cr.close_path()
                inked(cr, (0.82, 0.82, 0.8), 3)
            for k in range(3):
                p = ((t * 0.4 + k / 3 + i * 0.2) % 1)
                cr.new_sub_path(); cr.arc(tx + p * s * 0.2, base - s * 0.85 - p * s * 0.5, s * (0.08 + p * 0.12), 0, 2 * math.pi)
                cr.set_source_rgba(0.9, 0.9, 0.9, 0.7 * (1 - p))
                cr.fill()
        if kind == "nuclear_site":
            cr.save()
            cr.translate(x + s * 0.95, base - s * 0.25)
            cr.new_sub_path(); cr.arc(0, 0, s * 0.2, math.pi, 2 * math.pi)
            cr.close_path()
            inked(cr, (0.85, 0.85, 0.82), 3)
            cr.restore()
    elif kind == "parliament":
        cr.rectangle(x - s * 1.2, base - s * 0.45, s * 2.4, s * 0.45)
        inked(cr, (0.85, 0.8, 0.68), 4)
        cr.rectangle(x - s * 0.15, base - s * 0.95, s * 0.3, s * 0.95)
        inked(cr, (0.85, 0.8, 0.68), 4)
        cr.new_sub_path(); cr.arc(x, base - s * 0.8, s * 0.09, 0, 2 * math.pi)
        inked(cr, (0.98, 0.95, 0.85), 2)
        for i in range(12):
            cr.rectangle(x - s * 1.1 + i * s * 0.19, base - s * 0.35, s * 0.07, s * 0.2)
            inked(cr, win, 1.5)


def art_building(cr, w, h, t, a, th):
    night = a.get("night", False)
    _bg(cr, w, h, t, a, "night" if night else "day")
    lights_out = a.get("lights_out_at")
    lit = night and not (lights_out is not None and t > float(lights_out))
    base = h * 0.85
    kit.ground(cr, w, h, base, (0.32, 0.38, 0.3) if not night else (0.12, 0.14, 0.16))
    _building(cr, w / 2, base, min(h * 0.62, w * 0.36), a.get("kind", "columns"), lit or not night, t, th["accent"])
    if a.get("flag"):
        F.flag(cr, w * 0.78, h * 0.12, h * 0.24, h * 0.15, a["flag"], t)
    if a.get("label"):
        kit.label_tag(cr, w / 2, h * 0.88, a["label"], max(14, h * 0.045))


def art_city(cr, w, h, t, a, th):
    night = a.get("night", True)
    _bg(cr, w, h, t, a, "night" if night else "dusk")
    out = a.get("lights_out_at")
    r = random.Random(4)
    x = 0
    base = h * 0.92
    while x < w:
        bw = r.uniform(w * 0.05, w * 0.11)
        bh = r.uniform(h * 0.25, h * 0.7)
        cr.rectangle(x, base - bh, bw, bh)
        inked(cr, (0.1, 0.12, 0.18) if night else (0.25, 0.25, 0.32), 3)
        for i in range(int(bh / (h * 0.06))):
            for j in range(int(bw / (w * 0.025))):
                dark = out is not None and t > float(out) + (x / w) * 0.8
                if r.random() < 0.6 and not dark:
                    cr.rectangle(x + j * w * 0.025 + 5, base - bh + i * h * 0.06 + 8, w * 0.012, h * 0.025)
                    cr.set_source_rgb(1, 0.86, 0.45)
                    cr.fill()
        x += bw + r.uniform(2, 10)
    kit.ground(cr, w, h, base, (0.08, 0.08, 0.1))


def art_document(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dark")
    pw, ph = min(w * 0.55, h * 0.62), min(h * 0.9, w * 0.8)
    x0, y0 = w / 2 - pw / 2, h / 2 - ph / 2 + h * 0.04
    cr.save()
    cr.translate(w / 2, h / 2)
    cr.rotate(-0.03)
    cr.translate(-w / 2, -h / 2)
    cr.rectangle(x0 + 8, y0 + 8, pw, ph)
    cr.set_source_rgba(0, 0, 0, 0.4)
    cr.fill()
    cr.rectangle(x0, y0, pw, ph)
    inked(cr, (0.98, 0.96, 0.9), 4)
    kit.font(cr, "caption", ph * 0.055)
    lines = kit.wrap(cr, str(a.get("title", "AGREEMENT")).upper(), pw * 0.8)
    for i, ln in enumerate(lines[:2]):
        e = cr.text_extents(ln)
        cr.move_to(w / 2 - e.x_advance / 2, y0 + ph * 0.12 + i * ph * 0.07)
        cr.set_source_rgb(*INK)
        cr.show_text(ln)
    shown = clamp(t / 1.5)
    n = int(a.get("lines", 9))
    for i in range(n):
        if i / n > shown:
            break
        lw_ = pw * (0.75 if i % 4 != 3 else 0.5)
        cr.rectangle(x0 + pw * 0.1, y0 + ph * 0.28 + i * ph * 0.055, lw_, ph * 0.012)
        cr.set_source_rgb(0.45, 0.45, 0.48)
        cr.fill()
    if a.get("signature", True) and t > 1.5:
        k = clamp((t - 1.5) / 0.8)
        cr.move_to(x0 + pw * 0.55, y0 + ph * 0.86)
        for j in range(int(20 * k)):
            cr.line_to(x0 + pw * (0.55 + j * 0.017), y0 + ph * (0.86 - 0.025 * math.sin(j * 1.3)))
        cr.set_source_rgb(0.1, 0.15, 0.5)
        cr.set_line_width(3)
        cr.stroke()
    cr.restore()
    if a.get("stamp") and t > 1.0:
        k = kit.back((t - 1.0) / 0.25)
        cr.save()
        cr.translate(w / 2 + pw * 0.15, h / 2 + ph * 0.12)
        cr.rotate(-0.2)
        cr.scale(k, k)
        kit.font(cr, "title", ph * 0.11)
        e = cr.text_extents(str(a["stamp"]).upper())
        kit.rrect(cr, -e.x_advance / 2 - 14, -ph * 0.09, e.x_advance + 28, ph * 0.13, 8)
        cr.set_source_rgb(*th["accent"])
        cr.set_line_width(6)
        cr.stroke()
        cr.move_to(-e.x_advance / 2, ph * 0.02)
        cr.show_text(str(a["stamp"]).upper())
        cr.restore()


def art_newspaper(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dark_burst" if False else "red_burst")
    spin = 1 - ease(t / 0.8)
    cr.save()
    cr.translate(w / 2, h / 2)
    cr.rotate(spin * 6 - 0.04)
    s = 0.3 + 0.7 * ease(t / 0.8)
    cr.scale(s, s)
    pw, ph = w * 0.7, h * 0.85
    cr.rectangle(-pw / 2, -ph / 2, pw, ph)
    inked(cr, (0.96, 0.95, 0.9), 4)
    kit.font(cr, "body", ph * 0.07)
    mast = str(a.get("masthead", "THE DAILY CHRONICLE")).upper()
    e = cr.text_extents(mast)
    cr.move_to(-e.x_advance / 2, -ph / 2 + ph * 0.1)
    cr.set_source_rgb(*INK)
    cr.show_text(mast)
    cr.rectangle(-pw * 0.45, -ph / 2 + ph * 0.13, pw * 0.9, 3)
    cr.fill()
    kit.font(cr, "title", ph * 0.14)
    lines = kit.wrap(cr, str(a.get("headline", "")).upper(), pw * 0.88)
    for i, ln in enumerate(lines[:3]):
        e = cr.text_extents(ln)
        cr.move_to(-e.x_advance / 2, -ph / 2 + ph * 0.3 + i * ph * 0.15)
        cr.show_text(ln)
    for i in range(6):
        for col in range(3):
            cr.rectangle(-pw * 0.44 + col * pw * 0.3, ph * 0.12 + i * ph * 0.05, pw * 0.26, ph * 0.015)
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.fill()
    cr.restore()


def art_tv(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dark")
    sw, sh = w * 0.84, h * 0.78
    x0, y0 = (w - sw) / 2, h * 0.06
    kit.rrect(cr, x0 - 14, y0 - 14, sw + 28, sh + 28, 18)
    inked(cr, (0.15, 0.15, 0.17), 4)
    cr.save()
    cr.rectangle(x0, y0, sw, sh)
    cr.clip()
    cr.translate(x0, y0)
    inner = a.get("inner") or {"art": "map", "region": "world"}
    draw_art(cr, sw, sh, t, inner, th)
    cr.restore()
    cr.rectangle(x0, y0 + sh * 0.74, sw, sh * 0.16)
    cr.set_source_rgb(*th["accent"])
    cr.fill()
    kit.font(cr, "title", sh * 0.1)
    cr.move_to(x0 + sw * 0.03, y0 + sh * 0.86)
    cr.set_source_rgb(1, 1, 1)
    cr.show_text(str(a.get("headline", "BREAKING")).upper())
    cr.rectangle(x0, y0 + sh * 0.9, sw, sh * 0.1)
    cr.set_source_rgb(0.08, 0.08, 0.1)
    cr.fill()
    kit.font(cr, "caption", sh * 0.055)
    ticker = ("   •   ".join(a.get("ticker") or [])).upper() or " "
    e = cr.text_extents(ticker + "   •   ")
    off = (t * sw * 0.12) % max(1, e.x_advance)
    cr.save()
    cr.rectangle(x0, y0 + sh * 0.9, sw, sh * 0.1)
    cr.clip()
    for k in range(3):
        cr.move_to(x0 + sw * 0.02 - off + k * e.x_advance, y0 + sh * 0.97)
        cr.set_source_rgb(1, 1, 1)
        cr.show_text(ticker + "   •   ")
    cr.restore()
    cr.rectangle(w * 0.46, y0 + sh + 14, w * 0.08, h * 0.08)
    inked(cr, (0.15, 0.15, 0.17), 3)


def art_calendar(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "yellow_burst")
    cw, ch = min(w * 0.45, h * 0.7), min(h * 0.75, w * 0.55)
    x0, y0 = w / 2 - cw / 2, h / 2 - ch / 2
    flip = ease(t / 0.6)
    cr.rectangle(x0, y0, cw, ch)
    inked(cr, WHITE, 5)
    cr.rectangle(x0, y0, cw, ch * 0.28)
    inked(cr, th["accent"], 5)
    date = str(a.get("date", "1 JAN")).upper().split()
    kit.font(cr, "title", ch * 0.18)
    top = date[1] if len(date) > 1 else ""
    e = cr.text_extents(top)
    cr.move_to(w / 2 - e.x_advance / 2, y0 + ch * 0.21)
    cr.set_source_rgb(1, 1, 1)
    cr.show_text(top)
    kit.font(cr, "title", ch * 0.5 * flip + 1)
    e = cr.text_extents(date[0])
    cr.move_to(w / 2 - e.x_advance / 2, y0 + ch * 0.8)
    cr.set_source_rgb(*INK)
    cr.show_text(date[0])
    if a.get("year"):
        kit.font(cr, "caption", ch * 0.08)
        e = cr.text_extents(str(a["year"]))
        cr.move_to(w / 2 - e.x_advance / 2, y0 + ch * 0.94)
        cr.show_text(str(a["year"]))
    for i in range(2):
        cr.new_sub_path(); cr.arc(x0 + cw * (0.3 + 0.4 * i), y0, ch * 0.04, 0, 2 * math.pi)
        inked(cr, (0.7, 0.7, 0.7), 3)


def art_flag(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "day")
    fw = min(w * 0.7, h * 1.1)
    F.flag(cr, w / 2 - fw / 2 + w * 0.03, h * 0.18, fw, fw * 0.6, a.get("flag", "white"), t,
           stripes=a.get("stripes"))


# ------------------------------------------------------------------ numbers and text
def art_title(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "red_burst")
    kit.sfx(cr, w / 2, h * 0.45, str(a.get("text", "")).upper(), t, 0.0, size=min(h * 0.3, w * 0.11),
            rot=-0.05, fill=(0.98, 0.95, 0.85))
    if a.get("sub"):
        kit.caption_box(cr, w * 0.2, h * 0.68, w * 0.6, a["sub"], t, 0.5, max(16, h * 0.05), th["caption"])


def art_question(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "purple_burst")
    k = kit.back(t / 0.4)
    cr.save()
    cr.translate(w * 0.5, h * 0.42)
    cr.scale(k, k)
    cr.rotate(0.08 * math.sin(t * 2))
    kit.sfx(cr, 0, 0, "?", 1, 0, size=h * 0.62, rot=0, fill=(1, 0.85, 0.2))
    cr.restore()
    if a.get("text"):
        kit.caption_box(cr, w * 0.12, h * 0.74, w * 0.76, a["text"], t, 0.4, max(18, h * 0.055), th["caption"])


def art_stat(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "yellow_burst")
    cr.save()
    cr.translate(w / 2, h * 0.45)
    n = 22
    k = kit.back(t / 0.35)
    cr.scale(k, k)
    rr = min(w, h) * 0.42
    cr.move_to(rr, 0)
    for i in range(1, n * 2 + 1):
        ang = math.pi * i / n
        r2 = rr if i % 2 == 0 else rr * 0.78
        cr.line_to(r2 * math.cos(ang) * (w / h if w > h else 1) * 0.8, r2 * math.sin(ang))
    cr.close_path()
    inked(cr, WHITE, 5)
    cr.restore()
    value = str(a.get("value", ""))
    size = min(h * 0.28, w * 0.9 / max(2, len(value)) * 1.6)
    kit.sfx(cr, w / 2, h * 0.42, value, t, 0.1, size=size, rot=-0.04, fill=th["accent"])
    if a.get("label"):
        kit.caption_box(cr, w * 0.15, h * 0.7, w * 0.7, a["label"], t, 0.4, max(16, h * 0.05), th["caption"], typing=0.6)
    if a.get("note"):
        kit.font(cr, "body", max(12, h * 0.032))
        e = cr.text_extents(a["note"])
        cr.move_to(w / 2 - e.x_advance / 2, h * 0.96)
        cr.set_source_rgb(*INK)
        cr.show_text(a["note"])


def art_chart(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "paper")
    labels, values = a.get("labels", []), [float(v) for v in a.get("values", [])]
    if not values:
        return
    title = str(a.get("title", "")).upper()
    kit.font(cr, "title", h * 0.08)
    cr.move_to(w * 0.05, h * 0.12)
    cr.set_source_rgb(*INK)
    cr.show_text(title)
    x0, x1, y0, y1 = w * 0.08, w * 0.95, h * 0.2, h * 0.8
    vmax = max(values) * 1.15 or 1
    vmin = min(0, min(values))
    n = len(values)
    k = ease(t / 1.5)
    hl = a.get("highlight")
    pre, suf = a.get("prefix", ""), a.get("suffix", "")
    cr.move_to(x0, y1)
    cr.line_to(x1, y1)
    cr.set_source_rgb(*INK)
    cr.set_line_width(4)
    cr.stroke()
    if a.get("type", "bar") == "line":
        pts = [(x0 + (x1 - x0) * (i + 0.5) / n, y1 - (y1 - y0) * (v - vmin) / (vmax - vmin)) for i, v in enumerate(values)]
        m = max(1, int(round(k * (n - 1))) + 1)
        cr.move_to(*pts[0])
        for p in pts[1:m]:
            cr.line_to(*p)
        cr.set_source_rgb(*th["accent"])
        cr.set_line_width(max(5, h * 0.015))
        cr.stroke()
        for i, p in enumerate(pts[:m]):
            cr.new_sub_path(); cr.arc(p[0], p[1], max(6, h * 0.016), 0, 2 * math.pi)
            inked(cr, WHITE, 3)
    else:
        bw = (x1 - x0) / n * 0.62
        for i, v in enumerate(values):
            cx = x0 + (x1 - x0) * (i + 0.5) / n
            bh = (y1 - y0) * (v - vmin) / (vmax - vmin) * k
            cr.rectangle(cx - bw / 2, y1 - bh, bw, bh)
            colour = th["accent"] if (hl is None or hl == i) else (0.55, 0.6, 0.68)
            inked(cr, colour, 4)
            if k >= 1:
                kit.font(cr, "title", min(h * 0.07, bw * 0.45))
                txt = f"{pre}{v:,.0f}{suf}" if float(v).is_integer() else f"{pre}{v:,}{suf}"
                e = cr.text_extents(txt)
                cr.move_to(cx - e.x_advance / 2, y1 - bh - h * 0.02)
                cr.set_source_rgb(*INK)
                cr.show_text(txt)
    kit.font(cr, "caption", max(12, min(h * 0.04, (x1 - x0) / n / 6)))
    for i, lab in enumerate(labels[:n]):
        cx = x0 + (x1 - x0) * (i + 0.5) / n
        lines = kit.wrap(cr, str(lab).upper(), (x1 - x0) / n * 0.95)
        for j, ln in enumerate(lines[:2]):
            e = cr.text_extents(ln)
            cr.move_to(cx - e.x_advance / 2, y1 + h * 0.06 + j * h * 0.045)
            cr.set_source_rgb(*INK)
            cr.show_text(ln)
    if a.get("source"):
        kit.font(cr, "body", max(11, h * 0.03))
        cr.move_to(w * 0.05, h * 0.97)
        cr.show_text("Source: " + str(a["source"]))


def art_versus(cr, w, h, t, a, th):
    cr.set_source_rgb(*INK)
    cr.paint()
    for side in (0, 1):
        cr.save()
        if side == 0:
            cr.move_to(0, 0); cr.line_to(w * 0.54, 0); cr.line_to(w * 0.46, h); cr.line_to(0, h)
        else:
            cr.move_to(w * 0.56, 0); cr.line_to(w, 0); cr.line_to(w, h); cr.line_to(w * 0.48, h)
        cr.close_path()
        cr.clip()
        background(cr, w, h, t, a.get("left_bg" if side == 0 else "right_bg", "blue" if side == 0 else "red"))
        key = "left" if side == 0 else "right"
        cx = w * (0.25 if side == 0 else 0.75)
        if a.get(key + "_flag"):
            F.flag(cr, cx - h * 0.2, h * 0.08, h * 0.4, h * 0.25, a[key + "_flag"], t + side)
        title = a.get(key + "_title", "")
        kit.font(cr, "title", h * 0.09)
        e = cr.text_extents(str(title).upper())
        cr.move_to(cx - e.x_advance / 2, h * 0.47)
        cr.text_path(str(title).upper())
        cr.set_source_rgb(1, 1, 1)
        cr.fill_preserve()
        cr.set_source_rgb(*INK)
        cr.set_line_width(3)
        cr.stroke()
        kit.font(cr, "caption", max(14, h * 0.045))
        for i, item in enumerate((a.get(key + "_items") or [])[:4]):
            if t < 0.6 + i * 0.5 + side * 0.25:
                continue
            lines = kit.wrap(cr, "• " + str(item), w * 0.38)
            for j, ln in enumerate(lines[:2]):
                cr.move_to(cx - w * 0.19, h * 0.58 + i * h * 0.1 + j * h * 0.05)
                cr.set_source_rgb(1, 1, 1)
                cr.show_text(ln)
        cr.restore()
    kit.sfx(cr, w * 0.51, h * 0.47, "VS", t, 0.2, size=h * 0.2, rot=-0.1, fill=(1, 0.85, 0.2))


def art_list(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "paper")
    kit.font(cr, "title", h * 0.1)
    cr.move_to(w * 0.07, h * 0.16)
    cr.set_source_rgb(*th["accent"])
    cr.show_text(str(a.get("title", "")).upper())
    kit.font(cr, "caption", max(16, h * 0.06))
    for i, item in enumerate((a.get("items") or [])[:5]):
        if t < 0.4 + i * 0.5:
            continue
        y = h * 0.3 + i * h * 0.13
        cr.new_sub_path(); cr.arc(w * 0.1, y - h * 0.02, h * 0.03, 0, 2 * math.pi)
        inked(cr, th["accent"], 3)
        cr.move_to(w * 0.15, y)
        cr.set_source_rgb(*INK)
        cr.show_text(str(item))


def art_quote(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dark")
    kit.font(cr, "caption", h * 0.5)
    cr.move_to(w * 0.04, h * 0.45)
    cr.set_source_rgb(*th["accent"])
    cr.show_text("“")
    kit.font(cr, "caption", max(18, h * 0.065))
    lines = kit.wrap(cr, a.get("text", ""), w * 0.76)
    shown = int(sum(len(l) for l in lines) * clamp(t / 1.6))
    used = 0
    for i, ln in enumerate(lines[:6]):
        part = ln[:max(0, shown - used)]
        used += len(ln)
        cr.move_to(w * 0.14, h * 0.3 + i * h * 0.1)
        cr.set_source_rgb(1, 1, 1)
        cr.show_text(part)
    if a.get("by") and t > 1.6:
        kit.font(cr, "body", max(14, h * 0.045))
        cr.move_to(w * 0.14, h * 0.3 + len(lines[:6]) * h * 0.1 + h * 0.05)
        cr.set_source_rgb(*th["caption"])
        cr.show_text("— " + a["by"])


def art_scales(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "grey")
    tilt = float(a.get("tilt", 0)) * ease(t / 1.2) * 0.3 + 0.03 * math.sin(t * 2)
    cx, cy = w / 2, h * 0.3
    cr.rectangle(cx - h * 0.02, cy, h * 0.04, h * 0.6)
    inked(cr, (0.8, 0.65, 0.3), 3)
    cr.rectangle(cx - h * 0.18, h * 0.88, h * 0.36, h * 0.06)
    inked(cr, (0.8, 0.65, 0.3), 3)
    arm = min(w * 0.35, h * 0.6)
    lx, ly = cx - arm * math.cos(tilt), cy - arm * math.sin(tilt)
    rx, ry = cx + arm * math.cos(tilt), cy + arm * math.sin(tilt)
    cr.move_to(lx, ly)
    cr.line_to(rx, ry)
    cr.set_source_rgb(*INK)
    cr.set_line_width(8)
    cr.stroke()
    for i, (px, py) in enumerate(((lx, ly), (rx, ry))):
        cr.move_to(px, py); cr.line_to(px - h * 0.12, py + h * 0.25)
        cr.move_to(px, py); cr.line_to(px + h * 0.12, py + h * 0.25)
        cr.set_line_width(3)
        cr.stroke()
        cr.new_sub_path(); cr.arc(px, py + h * 0.25, h * 0.14, 0, math.pi)
        cr.close_path()
        inked(cr, (0.85, 0.7, 0.35), 3)
        labs = a.get("labels") or []
        if i < len(labs):
            kit.label_tag(cr, px, py + h * 0.4, labs[i], max(13, h * 0.04))


def art_money(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "green_burst")
    sym = a.get("symbol", "$")
    r = random.Random(2)
    for i in range(14):
        p = ((t * 0.5 + i / 14) % 1)
        x = r.uniform(0.05, 0.95) * w
        y = -h * 0.1 + p * h * 1.2
        cr.save()
        cr.translate(x, y)
        cr.rotate(math.sin(t * 2 + i) * 0.6)
        cr.rectangle(-h * 0.08, -h * 0.04, h * 0.16, h * 0.08)
        inked(cr, (0.6, 0.8, 0.55), 2)
        cr.restore()
    kit.sfx(cr, w / 2, h * 0.45, sym, t, 0.0, size=h * 0.45, rot=-0.05, fill=(0.4, 0.75, 0.35))
    if a.get("label"):
        kit.caption_box(cr, w * 0.18, h * 0.74, w * 0.64, a["label"], t, 0.4, max(16, h * 0.05), th["caption"])


# ------------------------------------------------------------------ hardware and events
def _jet(cr, x, y, s, ang=0.0, col=(0.55, 0.58, 0.62)):
    cr.save()
    cr.translate(x, y)
    cr.rotate(ang)
    cr.move_to(s, 0)
    cr.line_to(s * 0.2, -s * 0.12)
    cr.line_to(-s * 0.1, -s * 0.6)
    cr.line_to(-s * 0.3, -s * 0.6)
    cr.line_to(-s * 0.2, -s * 0.12)
    cr.line_to(-s * 0.8, -s * 0.1)
    cr.line_to(-s * 0.95, -s * 0.35)
    cr.line_to(-s * 1.05, -s * 0.35)
    cr.line_to(-s * 1.0, 0)
    cr.line_to(-s * 1.05, s * 0.35)
    cr.line_to(-s * 0.95, s * 0.35)
    cr.line_to(-s * 0.8, s * 0.1)
    cr.line_to(-s * 0.2, s * 0.12)
    cr.line_to(-s * 0.3, s * 0.6)
    cr.line_to(-s * 0.1, s * 0.6)
    cr.line_to(s * 0.2, s * 0.12)
    cr.close_path()
    inked(cr, col, max(2, s * 0.05))
    cr.restore()


def art_jets(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "night" if a.get("night") else "day_burst")
    n = int(a.get("count", 3))
    for i in range(n):
        x = (t * w * 0.25 + i * w * 0.35) % (w * 1.4) - w * 0.2
        y = h * (0.3 + 0.2 * (i % 3)) + 6 * math.sin(t * 3 + i)
        cr.move_to(x - w * 0.5, y)
        cr.line_to(x - h * 0.12, y)
        cr.set_source_rgba(1, 1, 1, 0.5)
        cr.set_line_width(4)
        cr.stroke()
        _jet(cr, x, y, h * 0.12, 0.0)


def art_missiles(cr, w, h, t, a, th):
    """Streaks across a night sky; optional interceptor flashes. Shows no damage or casualties."""
    _bg(cr, w, h, t, a, "night")
    n = int(a.get("count", 6))
    r = random.Random(11)
    for i in range(n):
        delay = i * 0.35
        p = clamp((t - delay) / 2.2)
        if p <= 0:
            continue
        x0, y0 = r.uniform(-0.1, 0.3) * w, h * r.uniform(0.75, 0.95)
        x1, y1 = r.uniform(0.6, 1.1) * w, h * r.uniform(0.05, 0.35)
        x, y = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p - math.sin(p * math.pi) * h * 0.2
        g = cairo.LinearGradient(x0, y0, x, y)
        g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0)
        g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0.9)
        cr.move_to(x0, y0)
        cr.curve_to(x0 + (x - x0) * 0.4, y0 + (y - y0) * 0.4 - h * 0.12 * p, x - (x - x0) * 0.2, y, x, y)
        cr.set_source(g)
        cr.set_line_width(5)
        cr.stroke()
        cr.new_sub_path(); cr.arc(x, y, 7, 0, 2 * math.pi)
        cr.set_source_rgb(1, 0.95, 0.8)
        cr.fill()
        if a.get("intercept", True) and 0.55 < p < 0.75 and i % 2 == 0:
            f = (p - 0.55) / 0.2
            for k in range(12):
                ang = k * math.pi / 6
                cr.move_to(x, y)
                cr.line_to(x + math.cos(ang) * h * 0.08 * f, y + math.sin(ang) * h * 0.08 * f)
            cr.set_source_rgba(1, 1, 0.8, 1 - f)
            cr.set_line_width(3)
            cr.stroke()
    kit.ground(cr, w, h, h * 0.94, (0.08, 0.08, 0.1))


def art_drones(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "night")
    n = int(a.get("count", 7))
    r = random.Random(5)
    for i in range(n):
        x = (r.uniform(0, 1) * w + t * w * 0.08 * (1 + i % 3)) % (w * 1.2) - w * 0.1
        y = h * r.uniform(0.15, 0.6) + 5 * math.sin(t * 4 + i)
        s = h * r.uniform(0.04, 0.07)
        cr.move_to(x + s, y)
        cr.line_to(x - s, y - s * 0.9)
        cr.line_to(x - s * 0.6, y)
        cr.line_to(x - s, y + s * 0.9)
        cr.close_path()
        inked(cr, (0.25, 0.27, 0.3), 2)
        cr.new_sub_path(); cr.arc(x - s * 0.8, y, s * 0.15, 0, 2 * math.pi)
        cr.set_source_rgba(1, 0.6, 0.2, 0.6 + 0.4 * math.sin(t * 20 + i))
        cr.fill()


def _ship(cr, x, y, s, kind="destroyer", col=(0.5, 0.53, 0.58)):
    if kind == "carrier":
        cr.move_to(x - s * 1.4, y - s * 0.22)
        cr.line_to(x + s * 1.5, y - s * 0.22)
        cr.line_to(x + s * 1.2, y)
        cr.line_to(x - s * 1.2, y)
        cr.close_path()
        inked(cr, col, 3)
        cr.rectangle(x + s * 0.5, y - s * 0.55, s * 0.25, s * 0.33)
        inked(cr, col, 3)
        for i in range(4):
            _jet(cr, x - s * 1.0 + i * s * 0.4, y - s * 0.3, s * 0.12, 0, (0.4, 0.43, 0.47))
    elif kind == "tanker":
        cr.move_to(x - s * 1.4, y - s * 0.3)
        cr.line_to(x + s * 1.3, y - s * 0.3)
        cr.line_to(x + s * 1.1, y)
        cr.line_to(x - s * 1.3, y)
        cr.close_path()
        inked(cr, (0.7, 0.18, 0.15), 3)
        cr.rectangle(x - s * 1.3, y - s * 0.75, s * 0.4, s * 0.45)
        inked(cr, (0.95, 0.95, 0.92), 3)
        for i in range(5):
            cr.new_sub_path(); cr.arc(x - s * 0.6 + i * s * 0.38, y - s * 0.3, s * 0.15, math.pi, 2 * math.pi)
            inked(cr, (0.85, 0.85, 0.82), 2)
    else:
        cr.move_to(x - s * 1.2, y - s * 0.25)
        cr.line_to(x + s * 1.3, y - s * 0.25)
        cr.line_to(x + s * 1.0, y)
        cr.line_to(x - s * 1.1, y)
        cr.close_path()
        inked(cr, col, 3)
        cr.move_to(x - s * 0.5, y - s * 0.25)
        cr.line_to(x - s * 0.4, y - s * 0.6)
        cr.line_to(x + s * 0.2, y - s * 0.6)
        cr.line_to(x + s * 0.35, y - s * 0.25)
        cr.close_path()
        inked(cr, col, 3)
        cr.rectangle(x - s * 0.15, y - s * 0.9, s * 0.08, s * 0.3)
        inked(cr, col, 2)
        cr.move_to(x + s * 0.7, y - s * 0.3)
        cr.line_to(x + s * 1.05, y - s * 0.38)
        cr.set_source_rgb(*INK)
        cr.set_line_width(4)
        cr.stroke()


def art_warship(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "night" if a.get("night") else "day")
    kit.sea(cr, w, h, h * 0.62, t)
    n = int(a.get("count", 2))
    for i in range(n):
        s = h * (0.22 if i == 0 else 0.13)
        x = w * (0.45 + 0.3 * i) + t * w * 0.01
        _ship(cr, x, h * (0.7 + 0.04 * i), s, a.get("kind", "destroyer") if i == 0 else "destroyer")
    if a.get("flag"):
        F.flag(cr, w * 0.06, h * 0.08, h * 0.26, h * 0.16, a["flag"], t)


def art_tanker(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dusk")
    kit.sea(cr, w, h, h * 0.6, t)
    cr.move_to(0, h * 0.6)
    cr.line_to(w * 0.25, h * 0.45)
    cr.line_to(w * 0.35, h * 0.6)
    cr.close_path()
    inked(cr, (0.55, 0.45, 0.32), 3)
    cr.move_to(w, h * 0.6)
    cr.line_to(w * 0.78, h * 0.42)
    cr.line_to(w * 0.62, h * 0.6)
    cr.close_path()
    inked(cr, (0.55, 0.45, 0.32), 3)
    blocked = a.get("blocked", False)
    x = w * 0.5 + (0 if blocked else (t * w * 0.03 - w * 0.06))
    _ship(cr, x, h * 0.72, h * 0.18, "tanker")
    if blocked:
        k = kit.back((t - 0.6) / 0.3)
        if t > 0.6:
            cr.save()
            cr.translate(x, h * 0.55)
            cr.scale(k, k)
            for ang in (0.8, -0.8):
                cr.save()
                cr.rotate(ang)
                kit.rrect(cr, -h * 0.25, -h * 0.03, h * 0.5, h * 0.06, h * 0.02)
                inked(cr, th["accent"], 3)
                cr.restore()
            cr.restore()
    if a.get("label"):
        kit.label_tag(cr, w / 2, h * 0.86, a["label"], max(14, h * 0.045))


def art_fuel_pump(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "red_burst")
    pw, ph = min(w * 0.38, h * 0.55), h * 0.82
    x0, y0 = w * 0.32 - pw / 2, h * 0.12
    kit.rrect(cr, x0, y0, pw, ph, pw * 0.08)
    inked(cr, (0.85, 0.85, 0.82), 5)
    cr.rectangle(x0 + pw * 0.12, y0 + ph * 0.1, pw * 0.76, ph * 0.3)
    inked(cr, (0.1, 0.12, 0.1), 4)
    try:
        a0, a1 = float(a.get("from", 3.0)), float(a.get("to", 4.5))
    except ValueError:
        a0, a1 = 3.0, 4.5
    v = a0 + (a1 - a0) * ease(t / 2.5)
    kit.font(cr, "title", ph * 0.13)
    txt = f"{a.get('unit', '$')}{v:.2f}"
    e = cr.text_extents(txt)
    cr.move_to(x0 + pw / 2 - e.x_advance / 2, y0 + ph * 0.32)
    cr.set_source_rgb(1, 0.4, 0.2)
    cr.show_text(txt)
    cr.move_to(x0 + pw, y0 + ph * 0.5)
    cr.curve_to(x0 + pw * 1.6, y0 + ph * 0.5, x0 + pw * 1.6, y0 + ph * 0.9, x0 + pw * 1.25, y0 + ph * 0.72)
    cr.set_source_rgb(*INK)
    cr.set_line_width(10)
    cr.stroke()
    if t > 2.0:
        kit.sfx(cr, w * 0.75, h * 0.3, "UP!", t, 2.0, size=h * 0.2, rot=-0.15)


def art_power_grid(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "night")
    out = float(a.get("lights_out_at", 1.5))
    dark = t > out
    for i in range(4):
        x = w * (0.12 + i * 0.26)
        s = h * 0.7
        cr.move_to(x - s * 0.18, h * 0.95)
        cr.line_to(x - s * 0.05, h * 0.95 - s)
        cr.line_to(x + s * 0.05, h * 0.95 - s)
        cr.line_to(x + s * 0.18, h * 0.95)
        cr.set_source_rgb(*INK)
        cr.set_line_width(5)
        cr.stroke()
        for k in range(3):
            cr.move_to(x - s * 0.2, h * 0.95 - s * (0.75 - k * 0.12))
            cr.line_to(x + s * 0.2, h * 0.95 - s * (0.75 - k * 0.12))
        cr.stroke()
    for k in range(3):
        cr.move_to(0, h * (0.3 + k * 0.08))
        for i in range(5):
            x = w * (0.12 + i * 0.26)
            cr.line_to(x, h * (0.3 + k * 0.08))
        cr.set_source_rgba(0.6, 0.6, 0.6, 0.8)
        cr.set_line_width(2)
        cr.stroke()
    if not dark and int(t * 8) % 2:
        for i in range(4):
            cr.new_sub_path(); cr.arc(w * (0.12 + i * 0.26), h * 0.3, 8, 0, 2 * math.pi)
            cr.set_source_rgb(1, 0.95, 0.5)
            cr.fill()
    r = random.Random(1)
    for i in range(18):
        x = r.uniform(0.02, 0.95) * w
        bw_, bh_ = w * 0.05, h * r.uniform(0.1, 0.22)
        cr.rectangle(x, h * 0.95 - bh_, bw_, bh_)
        inked(cr, (0.12, 0.13, 0.17), 2)
        if not (dark and x / w < (t - out) * 1.5):
            cr.rectangle(x + bw_ * 0.25, h * 0.95 - bh_ * 0.75, bw_ * 0.5, bh_ * 0.3)
            cr.set_source_rgb(1, 0.86, 0.45)
            cr.fill()
    if dark:
        kit.sfx(cr, w * 0.5, h * 0.18, "BLACKOUT", t, out, size=h * 0.14, rot=-0.06, fill=(0.85, 0.85, 0.9))


def art_tanks(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dawn")
    kit.ground(cr, w, h, h * 0.75, (0.45, 0.42, 0.3))
    n = int(a.get("count", 3))
    for i in range(n):
        s = h * (0.16 - i * 0.025)
        x = w * (0.75 - i * 0.28) + t * w * 0.015 * (1 if a.get("direction", "right") == "right" else -1)
        y = h * (0.82 - i * 0.04)
        col = rgb(a.get("colour"), (0.38, 0.42, 0.3))
        kit.rrect(cr, x - s * 1.1, y - s * 0.3, s * 2.2, s * 0.32, s * 0.15)
        inked(cr, shade_(col, 0.7), 3)
        cr.move_to(x - s * 0.9, y - s * 0.3)
        cr.line_to(x + s * 0.9, y - s * 0.3)
        cr.line_to(x + s * 0.7, y - s * 0.6)
        cr.line_to(x - s * 0.7, y - s * 0.6)
        cr.close_path()
        inked(cr, col, 3)
        kit.rrect(cr, x - s * 0.4, y - s * 0.9, s * 0.8, s * 0.32, s * 0.1)
        inked(cr, col, 3)
        cr.rectangle(x + s * 0.4, y - s * 0.8, s * 0.9, s * 0.1)
        inked(cr, col, 3)
        for k in range(5):
            cr.new_sub_path(); cr.arc(x - s * 0.8 + k * s * 0.4, y - s * 0.14, s * 0.1, 0, 2 * math.pi)
            inked(cr, (0.2, 0.2, 0.2), 2)


def shade_(c, k):
    return kit.shade(c, k)


def art_soldiers(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dusk")
    kit.ground(cr, w, h, h * 0.85, (0.25, 0.22, 0.18))
    n = int(a.get("count", 7))
    for i in range(n):
        x = w * (i + 0.5) / n + (t * w * 0.02) % (w / n)
        s = h * 0.5
        bob = abs(math.sin(t * 4 + i)) * s * 0.03
        y = h * 0.85 - bob
        cr.new_sub_path(); cr.arc(x, y - s * 0.85, s * 0.08, 0, 2 * math.pi)
        cr.set_source_rgb(*INK)
        cr.fill()
        cr.new_sub_path(); cr.arc(x, y - s * 0.88, s * 0.1, math.pi, 2 * math.pi)
        cr.fill()
        cr.rectangle(x - s * 0.08, y - s * 0.77, s * 0.16, s * 0.4)
        cr.fill()
        ph = math.sin(t * 4 + i) * 0.4
        for leg in (-1, 1):
            cr.save()
            cr.translate(x, y - s * 0.37)
            cr.rotate(ph * leg)
            cr.rectangle(-s * 0.035, 0, s * 0.07, s * 0.37)
            cr.fill()
            cr.restore()
        cr.move_to(x + s * 0.06, y - s * 0.7)
        cr.line_to(x + s * 0.2, y - s * 0.95)
        cr.set_line_width(s * 0.03)
        cr.stroke()


def art_ballot(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "blue_burst")
    bw, bh = min(w * 0.4, h * 0.55), min(h * 0.45, w * 0.35)
    x0, y0 = w / 2 - bw / 2, h * 0.5
    cr.rectangle(x0, y0, bw, bh)
    inked(cr, (0.94, 0.94, 0.96), 5)
    cr.rectangle(w / 2 - bw * 0.3, y0 - 4, bw * 0.6, 10)
    cr.set_source_rgb(*INK)
    cr.fill()
    if a.get("label"):
        kit.font(cr, "title", bh * 0.2)
        e = cr.text_extents(str(a["label"]).upper())
        cr.move_to(w / 2 - e.x_advance / 2, y0 + bh * 0.62)
        cr.set_source_rgb(*th["accent"])
        cr.show_text(str(a["label"]).upper())
    p = (t % 1.6) / 1.6
    py = h * 0.05 + (y0 - h * 0.05) * ease(p)
    cr.save()
    cr.translate(w / 2, py)
    cr.rotate(0.15 * (1 - p))
    cr.rectangle(-bw * 0.18, -bh * 0.3, bw * 0.36, bh * 0.36)
    inked(cr, WHITE, 3)
    cr.move_to(-bw * 0.08, -bh * 0.12)
    cr.line_to(-bw * 0.02, -bh * 0.05)
    cr.line_to(bw * 0.1, -bh * 0.22)
    cr.set_source_rgb(*th["accent"])
    cr.set_line_width(5)
    cr.stroke()
    cr.restore()


def art_plane(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "day")
    r = random.Random(3)
    for i in range(5):
        cx = (r.uniform(0, 1) * w - t * w * 0.05) % (w * 1.3) - w * 0.15
        cy = r.uniform(0.15, 0.85) * h
        for k in range(4):
            cr.new_sub_path(); cr.arc(cx + k * h * 0.05, cy + (k % 2) * h * 0.02, h * 0.05, 0, 2 * math.pi)
        cr.set_source_rgba(1, 1, 1, 0.85)
        cr.fill()
    x, y, s = w * 0.5, h * 0.48 + 6 * math.sin(t * 2), h * 0.28
    cr.save()
    cr.translate(x, y)
    cr.rotate(-0.08)
    kit.rrect(cr, -s * 1.2, -s * 0.13, s * 2.4, s * 0.26, s * 0.13)
    inked(cr, (0.95, 0.95, 0.97), 4)
    cr.move_to(-s * 0.2, 0)
    cr.line_to(-s * 0.6, s * 0.7)
    cr.line_to(-s * 0.35, s * 0.7)
    cr.line_to(s * 0.3, 0)
    cr.close_path()
    inked(cr, (0.85, 0.86, 0.9), 4)
    cr.move_to(-s * 1.0, -s * 0.1)
    cr.line_to(-s * 1.2, -s * 0.55)
    cr.line_to(-s * 1.05, -s * 0.55)
    cr.line_to(-s * 0.75, -s * 0.1)
    cr.close_path()
    inked(cr, th["accent"], 4)
    for i in range(9):
        cr.new_sub_path(); cr.arc(-s * 0.7 + i * s * 0.17, -s * 0.03, s * 0.035, 0, 2 * math.pi)
        cr.set_source_rgb(0.3, 0.45, 0.65)
        cr.fill()
    cr.restore()
    if a.get("label"):
        kit.label_tag(cr, w / 2, h * 0.84, a["label"], max(14, h * 0.045))


def art_aid(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "dawn")
    kit.ground(cr, w, h, h * 0.78, (0.72, 0.62, 0.45))
    n = int(a.get("count", 3))
    for i in range(n):
        s = h * 0.17
        x = w * (0.2 + i * 0.3) + t * w * 0.02
        y = h * 0.8
        cr.rectangle(x - s * 1.1, y - s * 0.75, s * 1.5, s * 0.65)
        inked(cr, (0.95, 0.95, 0.95), 3)
        cr.rectangle(x + s * 0.4, y - s * 0.55, s * 0.55, s * 0.45)
        inked(cr, (0.85, 0.85, 0.85), 3)
        cr.rectangle(x - s * 0.5, y - s * 0.6, s * 0.3, s * 0.1)
        cr.rectangle(x - s * 0.4, y - s * 0.7, s * 0.1, s * 0.3)
        cr.set_source_rgb(0.2, 0.45, 0.8) if a.get("symbol") != "red_cross" else cr.set_source_rgb(0.85, 0.1, 0.1)
        cr.fill()
        for k in (-0.8, 0.6):
            cr.new_sub_path(); cr.arc(x + s * k, y - s * 0.08, s * 0.12, 0, 2 * math.pi)
            inked(cr, (0.15, 0.15, 0.15), 2)
    if a.get("label"):
        kit.label_tag(cr, w / 2, h * 0.88, a["label"], max(14, h * 0.045))


def art_ship(cr, w, h, t, a, th):
    _bg(cr, w, h, t, a, "night" if a.get("night", True) else "day")
    kit.sea(cr, w, h, h * 0.68, t)
    _ship(cr, w * 0.45 + t * w * 0.01, h * 0.72, h * 0.22, a.get("kind", "destroyer"))


def art_map(cr, w, h, t, a, th):
    maps.draw(cr, w, h, t, a, th)
    if a.get("title"):
        kit.label_tag(cr, w * 0.04, h * 0.04, a["title"], max(14, h * 0.05), centre=False)


ART = {
    "title": (art_title, "text, sub, bg"),
    "question": (art_question, "text, bg"),
    "portrait": (art_portrait, "who, mood, talking, flag, bg"),
    "duo": (art_duo, "who, other, mood, other_mood, talking (who|other), flags [left, right], bg"),
    "group": (art_group, "people [who, ...] (2-6), bg"),
    "crowd": (art_crowd, "signs [text], flags [names], count, bg"),
    "podium": (art_podium, "who, mood, talking, sign, flags [up to 2], bg"),
    "table": (art_table, "who, other, flags [left, right], label, talking (who|other), bg"),
    "handshake": (art_handshake, "sleeves [colour, colour], flags [left, right], bg"),
    "phone_call": (art_phone_call, "who, other, bg, other_bg"),
    "map": (art_map, "region | bbox, highlight {country: colour}, occupied [names], labels [names], markers, arrows, title"),
    "building": (art_building, "kind (dome|columns|white_house|towers|parliament|office|embassy|hospital|apartments|refinery|power_plant|nuclear_site), night, lights_out_at, flag, label"),
    "city": (art_city, "night, lights_out_at"),
    "document": (art_document, "title, lines, stamp, signature"),
    "newspaper": (art_newspaper, "headline, masthead (keep it fictional)"),
    "tv": (art_tv, "headline, ticker [text], inner (another panel spec shown on the screen)"),
    "calendar": (art_calendar, "date ('3 NOV'), year"),
    "flag": (art_flag, "flag | stripes {colours, vertical}, bg"),
    "stat": (art_stat, "value, label, note"),
    "chart": (art_chart, "type (bar|line), labels, values, title, source, prefix, suffix, highlight"),
    "versus": (art_versus, "left_title, right_title, left_items, right_items, left_flag, right_flag, left_bg, right_bg"),
    "list": (art_list, "title, items (max 5)"),
    "quote": (art_quote, "text (real quote only), by"),
    "scales": (art_scales, "tilt (-1 to 1), labels [left, right]"),
    "money": (art_money, "symbol, label"),
    "jets": (art_jets, "count, night"),
    "missiles": (art_missiles, "count, intercept"),
    "drones": (art_drones, "count"),
    "warship": (art_warship, "kind (destroyer|carrier), count, flag, night"),
    "ship": (art_ship, "kind (destroyer|carrier|tanker), night"),
    "tanker": (art_tanker, "blocked, label"),
    "fuel_pump": (art_fuel_pump, "from, to, unit"),
    "power_grid": (art_power_grid, "lights_out_at"),
    "tanks": (art_tanks, "count, direction, colour"),
    "soldiers": (art_soldiers, "count"),
    "ballot": (art_ballot, "label"),
    "plane": (art_plane, "label"),
    "aid": (art_aid, "count, label, symbol (red_cross|un)"),
}


def draw_art(cr, w, h, t, a, th):
    kind = a.get("art", "title")
    fn = ART.get(kind, (art_title, ""))[0]
    if kind not in ART:
        a = dict(a, text=a.get("text") or kind.replace("_", " "))
    cr.save()
    fn(cr, w, h, t, a, th)
    cr.restore()
