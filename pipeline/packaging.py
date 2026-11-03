"""Comic-book thumbnail, YouTube description and the credits/notes that go with each video."""
from __future__ import annotations

import math
from pathlib import Path

import cairo

from . import art, kit
from .render import chapter_lines, theme

DESC_LIMIT = 4900
TW, TH = 1280, 720


def _cover_panel(script: dict) -> dict:
    """The art behind the thumbnail: the plan's thumbnail_panel, else the first panel of the video."""
    if script.get("thumbnail_panel"):
        return script["thumbnail_panel"]
    for sc in script["scenes"]:
        for page in ([sc["page"]] if sc.get("page") else []) + list(sc.get("pages") or []):
            for p in page.get("panels", []):
                if p.get("art") not in ("title", "question", "list", "quote", "stat", "chart"):
                    return p
    return {"art": "title", "text": script["title"]}


def _burst(cr, cx, cy, rx, ry, spikes=18, inner=0.8):
    cr.move_to(cx + rx, cy)
    for i in range(1, spikes * 2 + 1):
        a = math.pi * i / spikes
        k = 1.0 if i % 2 == 0 else inner
        cr.line_to(cx + rx * k * math.cos(a), cy + ry * k * math.sin(a))
    cr.close_path()


def thumbnail(script: dict, out: Path, cfg: dict) -> Path:
    """1280x720 comic cover: the video's own artwork, halftone, a starburst behind the key word,
    huge Bangers lettering, a yellow caption tag and thick ink borders.

    Plan options: thumbnail_text (2-4 words; *star* the word that goes in the burst),
    thumbnail_tag (short line for the yellow box), thumbnail_panel (any panel spec for the art),
    thumbnail_badge (optional round sticker, e.g. "EXPLAINED")."""
    th = theme(cfg)
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, TW, TH)
    cr = cairo.Context(s)
    # artwork, slightly zoomed so it reads at small sizes
    spec = dict(_cover_panel(script))
    spec.pop("caption", None)
    spec.pop("bubble", None)
    spec.pop("sfx", None)
    cr.save()
    cr.translate(TW * 0.62, TH * 0.5)
    cr.scale(1.12, 1.12)
    cr.translate(-TW * 0.62, -TH * 0.5)
    art.draw_art(cr, TW, TH, 3.5, spec, th)
    cr.restore()
    cr.set_source_surface(kit.halftone(TW, TH, 10, 0.16), 0, 0)
    cr.paint()
    # darken the left side so the lettering pops
    g = cairo.LinearGradient(0, 0, TW * 0.75, 0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.55)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cr.rectangle(0, 0, TW, TH)
    cr.set_source(g)
    cr.fill()

    raw = str(script.get("thumbnail_text") or script["title"]).upper().split()
    hot = next((i for i, w in enumerate(raw) if w.startswith("*") and w.endswith("*")), len(raw) - 1)
    words = [w.strip("*") for w in raw]
    lines, cur = [], []
    for i, w in enumerate(words):
        if cur and len(" ".join(words[j] for j in cur + [i])) > 10:
            lines.append(cur)
            cur = [i]
        else:
            cur.append(i)
    lines.append(cur)
    lines = lines[:3]
    size = {1: 210, 2: 170, 3: 130}[len(lines)]
    kit.font(cr, "title", size)
    while max(cr.text_extents(" ".join(words[i] for i in ln)).x_advance for ln in lines) > TW * 0.68 and size > 80:
        size -= 8
        kit.font(cr, "title", size)
    lh = size * 0.95
    tag = str(script.get("thumbnail_tag") or "").upper()
    block = lh * len(lines) + (size * 0.55 if tag else 0)
    y = (TH - block) / 2 + size * 0.78
    x0 = 58

    # starburst behind the key word
    kit.font(cr, "title", size)
    yy = y
    for ln in lines:
        xx = x0
        for k, i in enumerate(ln):
            piece = words[i] + (" " if k < len(ln) - 1 else "")
            wd = cr.text_extents(words[i]).x_advance
            if i == hot:
                cx, cy = xx + wd / 2, yy - size * 0.36
                _burst(cr, cx + 8, cy + 8, wd * 0.72 + 40, size * 0.75, 20, 0.78)
                cr.set_source_rgba(0, 0, 0, 0.5)
                cr.fill()
                _burst(cr, cx, cy, wd * 0.72 + 40, size * 0.75, 20, 0.78)
                kit.inked(cr, (1, 0.86, 0.22), 7)
            xx += cr.text_extents(piece).x_advance
        yy += lh

    yy = y
    for ln in lines:
        xx = x0
        for k, i in enumerate(ln):
            piece = words[i] + (" " if k < len(ln) - 1 else "")
            fill = th["accent"] if i == hot else (1, 1, 1)
            cr.move_to(xx + 9, yy + 9)
            cr.text_path(words[i])
            cr.set_source_rgba(0, 0, 0, 0.75)
            cr.fill()
            cr.move_to(xx, yy)
            cr.text_path(words[i])
            cr.set_source_rgb(*kit.INK)
            cr.set_line_width(size * 0.11)
            cr.set_line_join(cairo.LINE_JOIN_ROUND)
            cr.stroke_preserve()
            cr.set_source_rgb(*fill)
            cr.fill()
            xx += cr.text_extents(piece).x_advance
        yy += lh

    if tag:
        kit.font(cr, "caption", 38)
        e = cr.text_extents(tag)
        ty = yy - lh + size * 0.35
        cr.rectangle(x0 + 7, ty + 7, e.x_advance + 44, 62)
        cr.set_source_rgba(0, 0, 0, 0.5)
        cr.fill()
        cr.rectangle(x0, ty, e.x_advance + 44, 62)
        kit.inked(cr, th["caption"], 5)
        cr.move_to(x0 + 22, ty + 44)
        cr.set_source_rgb(*kit.INK)
        cr.show_text(tag)

    badge = script.get("thumbnail_badge")
    if badge:
        cr.save()
        cr.translate(TW - 140, 130)
        cr.rotate(0.18)
        _burst(cr, 0, 0, 112, 112, 16, 0.86)
        kit.inked(cr, th["accent"], 6)
        kit.font(cr, "title", 46)
        e = cr.text_extents(str(badge).upper())
        cr.move_to(-e.x_advance / 2, 16)
        cr.set_source_rgb(1, 1, 1)
        cr.show_text(str(badge).upper())
        cr.restore()

    # comic cover border: thick ink, then a thin white line inside
    cr.rectangle(7, 7, TW - 14, TH - 14)
    cr.set_source_rgb(*kit.INK)
    cr.set_line_width(14)
    cr.stroke()
    cr.rectangle(20, 20, TW - 40, TH - 40)
    cr.set_source_rgb(1, 1, 1)
    cr.set_line_width(4)
    cr.stroke()
    s.write_to_png(str(out.with_suffix(".png")))
    from PIL import Image
    Image.open(out.with_suffix(".png")).convert("RGB").save(out, "JPEG", quality=92)
    out.with_suffix(".png").unlink()
    return out


def description(cfg: dict, script: dict, brief: dict) -> str:
    parts = [str(script.get("description_summary", "")).strip(), ""]
    ch = chapter_lines(script)
    if ch:
        parts += ["CHAPTERS", *ch, ""]
    srcs = brief.get("sources", [])[:12]
    if srcs:
        parts.append("SOURCES")
        parts += [f"{s.get('title', 'Source')}: {s.get('url', '')}" for s in srcs]
        parts.append("")
    note = cfg.get("description_note") or "Spotted an error? Leave a comment with a source."
    parts += [note.strip(), "",
              f"Narration is AI-generated. Research, script checks, artwork and editing by {cfg['channel_name']}."]
    text = "\n".join(parts)
    return text[:DESC_LIMIT]
