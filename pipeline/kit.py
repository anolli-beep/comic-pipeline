"""Comic drawing kit: ink, paper, halftone, skies, lettering, speech bubbles, sound effects and people.

Everything is drawn with pycairo. Sizes are in pixels of the surface being drawn on.
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

import cairo

from .common import comic_font, hex_rgb

INK = (0.06, 0.06, 0.09)
WHITE = (1, 1, 1)
CAPTION = (0.97, 0.88, 0.48)
RED = (0.84, 0.15, 0.17)


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def back(x: float) -> float:
    """Ease with a little overshoot (pops)."""
    x = clamp(x)
    c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def rgb(c, default=(0.5, 0.5, 0.5)):
    if c is None:
        return default
    if isinstance(c, (tuple, list)):
        return tuple(float(v) for v in c[:3])
    try:
        return hex_rgb(c)
    except (ValueError, TypeError):
        return default


def shade(c, k: float):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


# ------------------------------------------------------------------ fonts
_FACES: dict[str, cairo.FontFace] = {}
_FAMILIES = {"title": ("Bangers", False), "caption": ("Comic Neue", True), "body": ("Comic Neue", False)}
_installed = False


def ensure_fonts() -> None:
    """Make the comic fonts in assets/fonts visible to cairo (copies them to the user font folder once)."""
    global _installed
    if _installed:
        return
    import shutil
    import subprocess
    from pathlib import Path
    dest = Path.home() / ".local" / "share" / "fonts"
    dest.mkdir(parents=True, exist_ok=True)
    changed = False
    for kind in ("title", "caption", "body"):
        src = Path(comic_font(kind))
        if src.exists() and not (dest / src.name).exists():
            shutil.copy(src, dest / src.name)
            changed = True
    if changed:
        subprocess.run(["fc-cache", "-f", str(dest)], capture_output=True)
    _installed = True


def face(kind: str) -> cairo.FontFace:
    if kind not in _FACES:
        ensure_fonts()
        family, bold = _FAMILIES[kind]
        _FACES[kind] = cairo.ToyFontFace(family, cairo.FONT_SLANT_NORMAL,
                                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    return _FACES[kind]


def font(cr: cairo.Context, kind: str, size: float) -> None:
    cr.set_font_face(face(kind))
    cr.set_font_size(size)


def wrap(cr: cairo.Context, text: str, maxw: float) -> list[str]:
    words, lines, cur = str(text).split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if cr.text_extents(trial).x_advance > maxw and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


# ------------------------------------------------------------------ textures
@lru_cache(maxsize=8)
def halftone(w: int, h: int, step: int = 11, alpha: float = 0.14) -> cairo.ImageSurface:
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(s)
    for row, y in enumerate(range(0, h + step, step)):
        for x in range(0, w + step, step):
            r = 0.5 + 2.8 * (y / max(h, 1))
            c.arc(x + (step / 2 if row % 2 else 0), y, r, 0, 2 * math.pi)
            c.new_sub_path()
    c.set_source_rgba(0, 0, 0, alpha)
    c.fill()
    return s


@lru_cache(maxsize=4)
def paper(w: int, h: int, colour: tuple) -> cairo.ImageSurface:
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    c = cairo.Context(s)
    c.set_source_rgb(*colour)
    c.paint()
    r = random.Random(5)
    for _ in range(int(w * h / 90)):
        c.rectangle(r.uniform(0, w), r.uniform(0, h), 1.6, 1.6)
        c.set_source_rgba(0.4, 0.3, 0.1, r.uniform(0, 0.07))
        c.fill()
    return s


# ------------------------------------------------------------------ backgrounds
BG = {
    "night": ((0.05, 0.07, 0.17), (0.12, 0.17, 0.33)),
    "dusk": ((0.2, 0.12, 0.3), (0.85, 0.45, 0.3)),
    "dawn": ((0.45, 0.55, 0.78), (0.96, 0.76, 0.55)),
    "day": ((0.42, 0.68, 0.92), (0.78, 0.9, 0.98)),
    "dark": ((0.1, 0.1, 0.12), (0.2, 0.2, 0.24)),
    "grey": ((0.62, 0.64, 0.66), (0.8, 0.81, 0.82)),
    "paper": ((0.95, 0.92, 0.84), (0.95, 0.92, 0.84)),
    "red": ((0.75, 0.12, 0.13), (0.88, 0.25, 0.2)),
    "yellow": ((0.96, 0.78, 0.25), (0.98, 0.88, 0.45)),
    "blue": ((0.18, 0.45, 0.72), (0.35, 0.62, 0.85)),
    "green": ((0.2, 0.48, 0.35), (0.42, 0.66, 0.48)),
    "purple": ((0.3, 0.2, 0.45), (0.5, 0.35, 0.65)),
}


def background(cr, w, h, t, name="day", seed=1):
    name = name or "day"
    burst = name.endswith("_burst") or name in ("speed", "burst")
    base = name.replace("_burst", "")
    if base in ("speed", "burst"):
        base = "yellow"
    top, bottom = BG.get(base, BG["day"])
    g = cairo.LinearGradient(0, 0, 0, h)
    g.add_color_stop_rgb(0, *top)
    g.add_color_stop_rgb(1, *bottom)
    cr.set_source(g)
    cr.paint()
    if base == "night":
        stars(cr, w, h * 0.7, t, 70, seed)
    if burst:
        speed_lines(cr, w, h, w / 2, h / 2, t)


def stars(cr, w, h, t, n=60, seed=1):
    r = random.Random(seed)
    for _ in range(n):
        x, y = r.uniform(0, w), r.uniform(0, h)
        a = 0.45 + 0.45 * math.sin(t * 2.5 + x * 0.05)
        cr.arc(x, y, r.uniform(1, 2.4), 0, 2 * math.pi)
        cr.set_source_rgba(1, 1, 0.92, a)
        cr.fill()


def speed_lines(cr, w, h, cx, cy, t, col=(1, 1, 1), a=0.35, n=44):
    r = random.Random(7)
    for i in range(n):
        ang = r.uniform(0, 2 * math.pi)
        r0 = r.uniform(0.3, 0.5) * max(w, h)
        r1 = r0 + r.uniform(0.3, 0.8) * max(w, h)
        wob = 0.02 * math.sin(t * 6 + i)
        cr.move_to(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang))
        cr.line_to(cx + r1 * math.cos(ang + 0.013 + wob), cy + r1 * math.sin(ang + 0.013 + wob))
        cr.line_to(cx + r1 * math.cos(ang - 0.013 + wob), cy + r1 * math.sin(ang - 0.013 + wob))
        cr.close_path()
    cr.set_source_rgba(*col, a)
    cr.fill()


def sea(cr, w, h, y0, t, col=(0.05, 0.12, 0.24)):
    cr.rectangle(0, y0, w, h - y0)
    cr.set_source_rgb(*col)
    cr.fill()
    cr.set_line_width(max(2, h / 300))
    r = random.Random(3)
    rows = max(3, int((h - y0) / (h / 40)))
    for i in range(rows):
        y = y0 + (i + 0.6) * (h - y0) / rows
        off = (t * 18 * (1 + i * 0.15)) % (w / 9)
        for x in range(-int(w / 9), int(w) + int(w / 9), int(w / 9)):
            xx = x + off + r.uniform(-10, 10)
            cr.move_to(xx, y)
            cr.line_to(xx + w / 30 + i * 3, y)
    cr.set_source_rgba(0.55, 0.7, 0.9, 0.28)
    cr.stroke()


def ground(cr, w, h, y0, col=(0.36, 0.42, 0.3)):
    cr.rectangle(0, y0, w, h - y0)
    cr.set_source_rgb(*col)
    cr.fill()
    cr.move_to(0, y0)
    cr.line_to(w, y0)
    cr.set_source_rgb(*INK)
    cr.set_line_width(max(3, h / 200))
    cr.stroke()


def inked(cr, fill, lw=4.0):
    """Fill the current path, then stroke it in ink."""
    cr.set_source_rgb(*fill)
    cr.fill_preserve()
    cr.set_source_rgb(*INK)
    cr.set_line_width(lw)
    cr.stroke()


def rrect(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


# ------------------------------------------------------------------ lettering
def caption_box(cr, x, y, w, text, t, start, size, colour=CAPTION, typing=1.1, max_h=None):
    """Yellow narration box. Text types on over `typing` seconds. Returns the box height."""
    if t < start:
        return 0
    k = ease((t - start) / 0.3)
    font(cr, "caption", size)
    lines = wrap(cr, str(text).upper(), w - size * 1.3)
    lh = size * 1.18
    h = size * 0.9 + len(lines) * lh
    if max_h and h > max_h:
        return caption_box(cr, x, y, w, text, t, start, size * 0.88, colour, typing, max_h)
    cr.save()
    cr.translate(0, (1 - k) * -size * 0.6)
    cr.rectangle(x + size * 0.22, y + size * 0.22, w, h)
    cr.set_source_rgba(0, 0, 0, 0.35 * k)
    cr.fill()
    cr.rectangle(x, y, w, h)
    cr.set_source_rgba(*colour, k)
    cr.fill_preserve()
    cr.set_source_rgba(*INK, k)
    cr.set_line_width(max(2.5, size * 0.13))
    cr.stroke()
    total = sum(len(s) + 1 for s in lines)
    shown = total if typing <= 0 else int(total * clamp((t - start) / typing))
    used = 0
    for i, ln in enumerate(lines):
        part = ln[:max(0, shown - used)]
        used += len(ln) + 1
        cr.move_to(x + size * 0.6, y + size * 0.42 + size * 0.86 + i * lh)
        cr.set_source_rgba(*INK, k)
        cr.show_text(part)
    cr.restore()
    return h


def bubble(cr, x, y, w, text, t, start, tail=(0.0, 0.0), size=30, shout=False, source=None):
    """Speech bubble centred at (x, y); tail points to (x + tail[0], y + tail[1])."""
    if t < start:
        return
    k = back((t - start) / 0.3)
    cr.save()
    cr.translate(x, y)
    cr.scale(k, k)
    font(cr, "caption", size)
    lines = wrap(cr, str(text).upper(), w * 0.8)
    lh = size * 1.15
    h = size * 1.4 + len(lines) * lh
    tx, ty = tail
    cr.move_to(-w * 0.1, h * 0.3)
    cr.line_to(tx, ty)
    cr.line_to(w * 0.08, h * 0.32)
    cr.close_path()
    inked(cr, WHITE, max(3, size * 0.12))
    if shout:
        n = 20
        cr.move_to(w * 0.62, 0)
        for i in range(1, n * 2 + 1):
            a = math.pi * i / n
            rr = 1.0 if i % 2 == 0 else 1.16
            cr.line_to(w * 0.62 * rr * math.cos(a), h * 0.8 * rr * math.sin(a))
        cr.close_path()
    else:
        cr.save()
        cr.scale(w * 0.6, h * 0.78)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
    inked(cr, WHITE, max(3, size * 0.12))
    cr.set_source_rgb(*INK)
    font(cr, "caption", size)
    for i, ln in enumerate(lines):
        e = cr.text_extents(ln)
        cr.move_to(-e.x_advance / 2, -h / 2 + size * 0.7 + size * 0.86 + i * lh - size * 0.2)
        cr.show_text(ln)
    cr.restore()
    if source:
        font(cr, "caption", size * 0.62)
        e = cr.text_extents(source)
        cr.move_to(x - e.x_advance / 2, y + h * 0.78 * k + size * 0.75)
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.text_path(source)
        cr.set_line_width(3)
        cr.set_source_rgb(*INK)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()


def sfx(cr, x, y, text, t, start, size, rot=-0.1, fill=(1, 0.85, 0.2), outline=INK, shake=0.0):
    if t < start:
        return
    k = back((t - start) / 0.25)
    cr.save()
    cr.translate(x + (math.sin(t * 50) * shake if shake else 0), y)
    cr.rotate(rot)
    cr.scale(k, k)
    font(cr, "title", size)
    e = cr.text_extents(text)
    ox, oy = -e.x_advance / 2, e.height / 2
    cr.move_to(ox + size * 0.05, oy + size * 0.05)
    cr.text_path(text)
    cr.set_source_rgb(*outline)
    cr.fill()
    cr.move_to(ox, oy)
    cr.text_path(text)
    cr.set_source_rgb(*fill)
    cr.fill_preserve()
    cr.set_source_rgb(*outline)
    cr.set_line_width(size * 0.06)
    cr.stroke()
    cr.restore()


def label_tag(cr, x, y, text, size, fill=CAPTION, centre=True):
    """Small name plate (yellow strip with ink border)."""
    font(cr, "caption", size)
    e = cr.text_extents(str(text).upper())
    w, h = e.x_advance + size * 1.0, size * 1.45
    x0 = x - w / 2 if centre else x
    cr.rectangle(x0, y, w, h)
    inked(cr, fill, max(2, size * 0.12))
    cr.move_to(x0 + size * 0.5, y + size * 1.05)
    cr.set_source_rgb(*INK)
    cr.show_text(str(text).upper())


# ------------------------------------------------------------------ people
SKIN = {"light": (0.98, 0.84, 0.72), "fair": (0.96, 0.8, 0.66), "medium": (0.88, 0.68, 0.52),
        "tan": (0.76, 0.56, 0.4), "brown": (0.58, 0.4, 0.28), "dark": (0.4, 0.27, 0.19)}
HAIR = {"black": (0.1, 0.09, 0.08), "brown": (0.36, 0.24, 0.14), "grey": (0.66, 0.66, 0.66),
        "white": (0.94, 0.94, 0.94), "blond": (0.92, 0.78, 0.42), "red": (0.7, 0.3, 0.15),
        "silver": (0.8, 0.8, 0.82)}

PEOPLE = {
    # outfit, outfit colour, tie, cap, hair, extras
    "official":   dict(outfit="suit", colour="#20283c", tie="#8a1c1c", hair="short", hair_colour="grey"),
    "president":  dict(outfit="suit", colour="#1b2338", tie="#b0202a", hair="swept", hair_colour="grey", pin=True),
    "diplomat":   dict(outfit="suit", colour="#2b2f38", tie="#2a4f7a", hair="short", hair_colour="brown", glasses=True),
    "analyst":    dict(outfit="suit", colour="#3a3e46", tie="#5a5a5a", hair="short", hair_colour="black", glasses=True),
    "general":    dict(outfit="uniform", colour="#3f4a33", cap="officer", hair="short", hair_colour="grey", medals=True),
    "officer":    dict(outfit="uniform", colour="#1f2a44", cap="officer", hair="short", hair_colour="brown"),
    "soldier":    dict(outfit="fatigues", colour="#4b5638", cap="helmet", hair="short", hair_colour="brown"),
    "pilot":      dict(outfit="flightsuit", colour="#5a6248", cap="pilot", hair="short", hair_colour="brown"),
    "sailor":     dict(outfit="uniform", colour="#f2f2f2", cap="sailor", hair="short", hair_colour="brown"),
    "reporter":   dict(outfit="casual", colour="#6d4c3a", hair="long", hair_colour="brown", mic=True),
    "protester":  dict(outfit="casual", colour="#7a3a2a", hair="curly", hair_colour="black"),
    "worker":     dict(outfit="workwear", colour="#d27a1e", cap="hardhat", hair="short", hair_colour="brown"),
    "voter":      dict(outfit="casual", colour="#3e6a8a", hair="short", hair_colour="brown"),
    "citizen":    dict(outfit="coat", colour="#5a4a3c", hair="short", hair_colour="black"),
    "scientist":  dict(outfit="labcoat", colour="#f4f4f4", hair="short", hair_colour="grey", glasses=True),
    "judge":      dict(outfit="robe", colour="#151515", hair="short", hair_colour="grey", glasses=True),
    "monarch":    dict(outfit="suit", colour="#2a2140", tie="#c9a227", hair="short", hair_colour="white"),
    "aid_worker": dict(outfit="vest", colour="#e8e8e8", cap="none", hair="short", hair_colour="brown"),
}
MOODS = ("neutral", "serious", "concerned", "speaking", "determined", "surprised", "smiling", "listening")


def person_spec(who) -> dict:
    """Preset name or dict with 'preset' plus overrides -> full spec."""
    if isinstance(who, str):
        who = {"preset": who}
    who = dict(who or {})
    spec = dict(PEOPLE.get(who.get("preset", "citizen"), PEOPLE["citizen"]))
    spec.update({k: v for k, v in who.items() if k != "preset"})
    return spec


def person(cr, cx, base, size, who, t=0.0, mood=None, look=0.0, talking=False, nameplate=True):
    """A comic-style bust standing on `base` (bottom of the shoulders), head radius = size*0.3.

    who: preset name or dict (preset, skin, hair, hair_colour, facial, glasses, outfit, colour, tie,
    cap, name, mood).
    """
    s = person_spec(who)
    mood = mood or s.get("mood", "neutral")
    skin = SKIN.get(s.get("skin", "fair"), SKIN["fair"])
    hc = s.get("hair_colour", "brown")
    hair_col = HAIR[hc] if hc in HAIR else rgb(hc, HAIR["brown"])
    col = rgb(s.get("colour"), (0.3, 0.3, 0.35))
    r = size * 0.3
    lw = max(2.5, size * 0.022)
    hy = base - size * 0.62          # head centre
    cr.save()
    # --- body (shoulders)
    sh_w = size * 0.95
    top = base - size * 0.34
    cr.move_to(cx - sh_w / 2, base)
    cr.curve_to(cx - sh_w / 2, top + size * 0.05, cx - sh_w * 0.32, top, cx, top)
    cr.curve_to(cx + sh_w * 0.32, top, cx + sh_w / 2, top + size * 0.05, cx + sh_w / 2, base)
    cr.close_path()
    inked(cr, col, lw)
    # cel shadow on the right side of the body
    cr.move_to(cx + sh_w * 0.18, top + size * 0.02)
    cr.curve_to(cx + sh_w * 0.4, top + size * 0.04, cx + sh_w / 2, top + size * 0.1, cx + sh_w / 2, base)
    cr.line_to(cx + sh_w * 0.25, base)
    cr.close_path()
    cr.set_source_rgba(0, 0, 0, 0.18)
    cr.fill()
    outfit = s.get("outfit", "suit")
    neck_w = r * 0.55
    if outfit in ("suit", "monarch"):
        cr.move_to(cx - neck_w, top + 2)
        cr.line_to(cx, top + size * 0.2)
        cr.line_to(cx + neck_w, top + 2)
        cr.close_path()
        inked(cr, (0.97, 0.97, 0.97), lw * 0.7)
        if s.get("tie"):
            tie = rgb(s.get("tie"))
            cr.move_to(cx - r * 0.12, top + size * 0.03)
            cr.line_to(cx + r * 0.12, top + size * 0.03)
            cr.line_to(cx + r * 0.16, top + size * 0.26)
            cr.line_to(cx, top + size * 0.32)
            cr.line_to(cx - r * 0.16, top + size * 0.26)
            cr.close_path()
            inked(cr, tie, lw * 0.6)
        for sx in (-1, 1):   # lapels
            cr.move_to(cx + sx * neck_w, top + 2)
            cr.line_to(cx + sx * r * 0.25, top + size * 0.28)
            cr.set_source_rgb(*INK)
            cr.set_line_width(lw * 0.8)
            cr.stroke()
        if s.get("pin"):
            cr.rectangle(cx - sh_w * 0.3, top + size * 0.12, r * 0.22, r * 0.14)
            inked(cr, (0.85, 0.15, 0.2), 1.5)
    elif outfit in ("uniform", "flightsuit", "fatigues"):
        cr.move_to(cx - neck_w * 0.8, top + 2)
        cr.line_to(cx, top + size * 0.12)
        cr.line_to(cx + neck_w * 0.8, top + 2)
        cr.set_source_rgb(*INK)
        cr.set_line_width(lw * 0.8)
        cr.stroke()
        for i in range(3):
            cr.arc(cx, top + size * 0.16 + i * size * 0.07, r * 0.06, 0, 2 * math.pi)
            cr.set_source_rgb(0.92, 0.78, 0.3)
            cr.fill()
        if s.get("medals"):
            for i, c in enumerate(((0.8, 0.2, 0.2), (0.2, 0.4, 0.8), (0.9, 0.75, 0.2))):
                cr.rectangle(cx - sh_w * 0.34 + i * r * 0.2, top + size * 0.12, r * 0.17, r * 0.12)
                inked(cr, c, 1.2)
        if outfit == "fatigues":
            rr = random.Random(9)
            for _ in range(10):
                cr.arc(cx + rr.uniform(-sh_w * 0.4, sh_w * 0.4), base - rr.uniform(0, size * 0.25), r * rr.uniform(0.1, 0.2), 0, 2 * math.pi)
                cr.set_source_rgba(0.2, 0.25, 0.12, 0.5)
                cr.fill()
    elif outfit == "labcoat":
        cr.move_to(cx, top + size * 0.05)
        cr.line_to(cx, base)
        cr.set_source_rgb(*INK)
        cr.set_line_width(lw * 0.7)
        cr.stroke()
    elif outfit == "robe":
        cr.rectangle(cx - neck_w * 0.6, top, neck_w * 1.2, size * 0.1)
        inked(cr, (0.96, 0.96, 0.96), lw * 0.6)
    elif outfit == "vest":
        cr.rectangle(cx - sh_w * 0.32, top + size * 0.1, sh_w * 0.64, size * 0.2)
        inked(cr, (0.25, 0.45, 0.75), lw * 0.6)
    elif outfit == "workwear":
        cr.rectangle(cx - sh_w * 0.35, top + size * 0.16, sh_w * 0.7, size * 0.04)
        cr.set_source_rgb(0.95, 0.95, 0.4)
        cr.fill()
    # --- neck and head
    cr.rectangle(cx - r * 0.28, hy + r * 0.7, r * 0.56, top - hy - r * 0.6)
    inked(cr, skin, lw * 0.8)
    hair = s.get("hair", "short")
    if hair == "long":
        cr.move_to(cx - r * 1.05, hy)
        cr.curve_to(cx - r * 1.15, hy + r * 1.6, cx + r * 1.15, hy + r * 1.6, cx + r * 1.05, hy)
        cr.close_path()
        inked(cr, hair_col, lw)
    cr.save()
    cr.translate(cx, hy)
    cr.scale(0.92, 1.0)
    cr.arc(0, 0, r, 0, 2 * math.pi)
    cr.restore()
    inked(cr, skin, lw)
    # cel shadow on the face
    cr.save()
    cr.translate(cx, hy)
    cr.scale(0.92, 1.0)
    cr.arc(0, 0, r, -0.9, 1.6)
    cr.arc_negative(r * 0.25, 0, r * 0.95, 1.4, -0.75)
    cr.restore()
    cr.set_source_rgba(0.55, 0.25, 0.1, 0.16)
    cr.fill()
    # ears
    for sx in (-1, 1):
        cr.arc(cx + sx * r * 0.93, hy + r * 0.1, r * 0.16, 0, 2 * math.pi)
        inked(cr, skin, lw * 0.7)
    # hair
    if hair in ("short", "swept", "curly", "long"):
        cr.move_to(cx - r * 0.95, hy - r * 0.05)
        if hair == "swept":
            cr.curve_to(cx - r * 1.05, hy - r * 1.3, cx + r * 0.6, hy - r * 1.35, cx + r * 1.0, hy - r * 0.55)
            cr.curve_to(cx + r * 0.6, hy - r * 0.75, cx - r * 0.2, hy - r * 0.6, cx - r * 0.95, hy - r * 0.05)
        elif hair == "curly":
            for i in range(9):
                a = math.pi + i * math.pi / 8
                cr.arc(cx + r * 0.85 * math.cos(a), hy - r * 0.25 + r * 0.8 * math.sin(a), r * 0.28, 0, 2 * math.pi)
                cr.new_sub_path()
        else:
            cr.curve_to(cx - r * 1.0, hy - r * 1.2, cx + r * 1.0, hy - r * 1.2, cx + r * 0.95, hy - r * 0.05)
            cr.curve_to(cx + r * 0.7, hy - r * 0.55, cx - r * 0.7, hy - r * 0.55, cx - r * 0.95, hy - r * 0.05)
        cr.close_path()
        inked(cr, hair_col, lw)
    elif hair == "receding":
        for sx in (-1, 1):
            cr.move_to(cx + sx * r * 0.95, hy + r * 0.1)
            cr.curve_to(cx + sx * r * 1.0, hy - r * 0.6, cx + sx * r * 0.7, hy - r * 0.8, cx + sx * r * 0.45, hy - r * 0.85)
            cr.line_to(cx + sx * r * 0.6, hy - r * 0.4)
            cr.close_path()
            inked(cr, hair_col, lw * 0.8)
    # facial hair
    facial = s.get("facial")
    if facial == "beard":
        cr.move_to(cx - r * 0.85, hy + r * 0.05)
        cr.curve_to(cx - r * 0.75, hy + r * 1.3, cx + r * 0.75, hy + r * 1.3, cx + r * 0.85, hy + r * 0.05)
        cr.line_to(cx + r * 0.5, hy + r * 0.35)
        cr.line_to(cx - r * 0.5, hy + r * 0.35)
        cr.close_path()
        inked(cr, hair_col, lw * 0.8)
    elif facial == "stubble":
        cr.move_to(cx - r * 0.8, hy + r * 0.2)
        cr.curve_to(cx - r * 0.7, hy + r * 1.1, cx + r * 0.7, hy + r * 1.1, cx + r * 0.8, hy + r * 0.2)
        cr.close_path()
        cr.set_source_rgba(*hair_col, 0.35)
        cr.fill()
    # eyes and brows
    ex, ey = r * 0.36, -r * 0.02
    big = mood in ("surprised",)
    er = r * (0.17 if big else 0.12)
    blink = (t % 4.3) < 0.12
    for sx in (-1, 1):
        if blink:
            cr.move_to(cx + sx * ex - er, hy + ey)
            cr.line_to(cx + sx * ex + er, hy + ey)
            cr.set_source_rgb(*INK)
            cr.set_line_width(lw * 0.8)
            cr.stroke()
        else:
            cr.arc(cx + sx * ex, hy + ey, er, 0, 2 * math.pi)
            inked(cr, WHITE, lw * 0.6)
            cr.arc(cx + sx * ex + look * er * 0.5, hy + ey + 1, er * 0.5, 0, 2 * math.pi)
            cr.set_source_rgb(*INK)
            cr.fill()
        # brows
        cr.set_line_width(max(2.5, r * 0.09))
        cr.set_source_rgb(*shade(hair_col, 0.6) if s.get("hair_colour") not in ("white", "grey", "silver", "blond") else (0.35, 0.33, 0.3))
        by = hy + ey - r * 0.3
        if mood in ("serious", "determined"):
            cr.move_to(cx + sx * ex - sx * r * 0.2, by - (r * 0.02))
            cr.line_to(cx + sx * ex + sx * r * 0.2, by - r * 0.1)
            cr.move_to(cx + sx * (ex - r * 0.2), by + r * 0.06)
            cr.line_to(cx + sx * (ex + r * 0.2), by - r * 0.04)
        elif mood in ("concerned",):
            cr.move_to(cx + sx * (ex - r * 0.2), by - r * 0.08)
            cr.line_to(cx + sx * (ex + r * 0.2), by + r * 0.04)
        elif mood in ("surprised",):
            cr.move_to(cx + sx * (ex - r * 0.2), by - r * 0.12)
            cr.curve_to(cx + sx * ex, by - r * 0.22, cx + sx * ex, by - r * 0.22, cx + sx * (ex + r * 0.2), by - r * 0.12)
        else:
            cr.move_to(cx + sx * (ex - r * 0.2), by)
            cr.line_to(cx + sx * (ex + r * 0.2), by - r * 0.02)
        cr.stroke()
    if s.get("glasses"):
        cr.set_source_rgb(*INK)
        cr.set_line_width(lw * 0.7)
        for sx in (-1, 1):
            rrect(cr, cx + sx * ex - r * 0.24, hy + ey - r * 0.17, r * 0.48, r * 0.34, r * 0.08)
            cr.stroke()
        cr.move_to(cx - ex + r * 0.24, hy + ey)
        cr.line_to(cx + ex - r * 0.24, hy + ey)
        cr.stroke()
    # nose
    cr.move_to(cx + r * 0.02, hy + r * 0.05)
    cr.line_to(cx - r * 0.1, hy + r * 0.33)
    cr.line_to(cx + r * 0.06, hy + r * 0.36)
    cr.set_source_rgb(*shade(skin, 0.7))
    cr.set_line_width(lw * 0.6)
    cr.stroke()
    # mouth
    my = hy + r * 0.58
    if facial == "beard":
        my = hy + r * 0.55
    talk = talking and (math.sin(t * 13) > -0.2)
    if talk or mood == "surprised":
        open_h = r * (0.16 + 0.1 * abs(math.sin(t * 11))) if talk else r * 0.2
        cr.save()
        cr.translate(cx, my)
        cr.scale(r * 0.22, open_h)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
        cr.set_source_rgb(0.35, 0.06, 0.06)
        cr.fill()
    else:
        cr.set_source_rgb(*INK)
        cr.set_line_width(lw * 0.8)
        if mood == "smiling":
            cr.arc(cx, my - r * 0.18, r * 0.24, 0.5, math.pi - 0.5)
        elif mood in ("concerned", "serious", "determined"):
            cr.move_to(cx - r * 0.2, my + r * 0.03)
            cr.curve_to(cx - r * 0.05, my - r * 0.03, cx + r * 0.05, my - r * 0.03, cx + r * 0.2, my + r * 0.03)
        else:
            cr.move_to(cx - r * 0.18, my)
            cr.line_to(cx + r * 0.18, my)
        cr.stroke()
    # headgear
    cap = s.get("cap")
    if cap == "officer":
        cr.move_to(cx - r * 1.05, hy - r * 0.5)
        cr.curve_to(cx - r * 1.2, hy - r * 1.35, cx + r * 1.2, hy - r * 1.35, cx + r * 1.05, hy - r * 0.5)
        cr.close_path()
        inked(cr, col, lw)
        cr.rectangle(cx - r * 1.0, hy - r * 0.62, r * 2.0, r * 0.18)
        inked(cr, INK, 1)
        cr.move_to(cx - r * 0.75, hy - r * 0.45)
        cr.curve_to(cx - r * 0.2, hy - r * 0.2, cx + r * 0.6, hy - r * 0.2, cx + r * 1.0, hy - r * 0.48)
        cr.close_path()
        cr.set_source_rgb(*INK)
        cr.fill()
        cr.arc(cx, hy - r * 0.85, r * 0.13, 0, 2 * math.pi)
        cr.set_source_rgb(0.92, 0.78, 0.3)
        cr.fill()
    elif cap in ("helmet", "pilot"):
        cr.move_to(cx - r * 1.1, hy - r * 0.2)
        cr.curve_to(cx - r * 1.15, hy - r * 1.5, cx + r * 1.15, hy - r * 1.5, cx + r * 1.1, hy - r * 0.2)
        cr.line_to(cx + r * 0.95, hy - r * 0.35)
        cr.curve_to(cx + r * 0.6, hy - r * 0.5, cx - r * 0.6, hy - r * 0.5, cx - r * 0.95, hy - r * 0.35)
        cr.close_path()
        inked(cr, shade(col, 0.85) if cap == "helmet" else (0.85, 0.85, 0.82), lw)
        if cap == "pilot":
            rrect(cr, cx - r * 0.75, hy - r * 0.62, r * 1.5, r * 0.32, r * 0.12)
            inked(cr, (0.25, 0.3, 0.4), lw * 0.7)
    elif cap == "hardhat":
        cr.move_to(cx - r * 1.2, hy - r * 0.45)
        cr.line_to(cx + r * 1.2, hy - r * 0.45)
        cr.curve_to(cx + r * 0.95, hy - r * 1.45, cx - r * 0.95, hy - r * 1.45, cx - r * 1.2, hy - r * 0.45)
        cr.close_path()
        inked(cr, (0.98, 0.82, 0.15), lw)
    elif cap == "sailor":
        cr.save()
        cr.translate(cx, hy - r * 0.75)
        cr.scale(1.0, 0.35)
        cr.arc(0, 0, r * 0.95, 0, 2 * math.pi)
        cr.restore()
        inked(cr, WHITE, lw)
    elif cap == "beret":
        cr.save()
        cr.translate(cx - r * 0.15, hy - r * 0.75)
        cr.scale(1.0, 0.45)
        cr.arc(0, 0, r * 1.0, 0, 2 * math.pi)
        cr.restore()
        inked(cr, rgb(s.get("cap_colour"), (0.5, 0.12, 0.15)), lw)
    if s.get("mic"):
        cr.move_to(cx + sh_w * 0.32, base - size * 0.1)
        cr.line_to(cx + r * 0.6, hy + r * 1.0)
        cr.set_source_rgb(*INK)
        cr.set_line_width(lw * 1.8)
        cr.stroke()
        cr.arc(cx + r * 0.55, hy + r * 0.95, r * 0.18, 0, 2 * math.pi)
        inked(cr, (0.2, 0.2, 0.22), lw * 0.6)
    cr.restore()
    if nameplate and s.get("name"):
        label_tag(cr, cx, base - size * 0.21, s["name"], max(12, size * 0.075))


def crowd_heads(cr, w, h, y0, n, t, seed=3, signs=(), sign_size=24):
    r = random.Random(seed)
    rows = 3
    for row in range(rows):
        y = y0 + row * h * 0.09
        for i in range(n):
            x = (i + 0.5 + (0.5 if row % 2 else 0)) * w / n + r.uniform(-8, 8)
            bob = 3 * math.sin(t * 3 + i + row)
            rad = h * (0.05 + row * 0.008)
            skin = list(SKIN.values())[r.randrange(len(SKIN))]
            cr.rectangle(x - rad * 1.1, y + rad * 0.6 + bob, rad * 2.2, h)
            inked(cr, [(0.3, 0.35, 0.5), (0.5, 0.3, 0.25), (0.25, 0.4, 0.3), (0.45, 0.45, 0.45)][r.randrange(4)], 2.5)
            cr.arc(x, y + bob, rad, 0, 2 * math.pi)
            inked(cr, skin, 2.5)
            cr.arc(x, y + bob - rad * 0.3, rad, math.pi, 2 * math.pi)
            cr.set_source_rgb(*[HAIR['black'], HAIR['brown'], HAIR['grey'], HAIR['blond']][r.randrange(4)])
            cr.fill()
    for k, text in enumerate(signs):
        x = (k + 0.5) * w / max(1, len(signs))
        y = y0 - h * 0.28 + 6 * math.sin(t * 2.2 + k)
        cr.move_to(x, y + h * 0.1)
        cr.line_to(x, y0 + h * 0.1)
        cr.set_source_rgb(0.45, 0.3, 0.15)
        cr.set_line_width(6)
        cr.stroke()
        font(cr, "caption", sign_size)
        lines = wrap(cr, str(text).upper(), w / max(1, len(signs)) * 0.75)
        bw = max(cr.text_extents(l).x_advance for l in lines) + sign_size
        bh = len(lines) * sign_size * 1.15 + sign_size * 0.6
        cr.rectangle(x - bw / 2, y - bh / 2, bw, bh)
        inked(cr, WHITE, 3)
        cr.set_source_rgb(*INK)
        for i, l in enumerate(lines):
            e = cr.text_extents(l)
            cr.move_to(x - e.x_advance / 2, y - bh / 2 + sign_size * 1.1 + i * sign_size * 1.15)
            cr.show_text(l)
