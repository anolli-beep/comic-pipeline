"""Comic pages: panel layouts, timing, captions, speech bubbles, sound effects and the camera.

A scene in a plan holds one page ("page") or several ("pages"). A page:
    {"layout": "trio_left",
     "panels": [{"art": "map", ..., "caption": "...", "bubble": {...}, "sfx": "..."}, ...]}
Panels appear one by one while the narration plays, and the camera drifts towards the newest one.
"""
from __future__ import annotations



from . import art, kit

GAP = 0.016            # gutter between panels, as a fraction of the page width
LAYOUTS = {
    "splash": 1, "duo_v": 2, "duo_h": 2, "trio_left": 3, "trio_right": 3, "trio_top": 3,
    "trio_bottom": 3, "strip3": 3, "quad": 4,
}


def rects(layout: str, W: float, H: float) -> list[tuple[float, float, float, float]]:
    g = W * GAP
    x0, y0, x1, y1 = g, g, W - g, H - g
    iw, ih = x1 - x0, y1 - y0

    def col(x, w, n, y=y0, h=ih):
        ph = (h - g * (n - 1)) / n
        return [(x, y + i * (ph + g), w, ph) for i in range(n)]

    def row(y, h, n, x=x0, w=iw):
        pw = (w - g * (n - 1)) / n
        return [(x + i * (pw + g), y, pw, h) for i in range(n)]

    if layout == "duo_v":
        return row(y0, ih, 2)
    if layout == "duo_h":
        return col(x0, iw, 2)
    if layout == "trio_left":
        bw = iw * 0.58
        return [(x0, y0, bw, ih)] + col(x0 + bw + g, iw - bw - g, 2)
    if layout == "trio_right":
        sw = iw * 0.42 - g
        return col(x0, sw, 2) + [(x0 + sw + g, y0, iw - sw - g, ih)]
    if layout == "trio_top":
        th = ih * 0.52
        return row(y0, th, 2) + [(x0, y0 + th + g, iw, ih - th - g)]
    if layout == "trio_bottom":
        th = ih * 0.48
        return [(x0, y0, iw, th)] + row(y0 + th + g, ih - th - g, 2)
    if layout == "strip3":
        return row(y0, ih, 3)
    if layout == "quad":
        hh = (ih - g) / 2
        return row(y0, hh, 2) + row(y0 + hh + g, hh, 2)
    return [(x0, y0, iw, ih)]


def appear_times(n: int, dur: float) -> list[float]:
    """When each panel pops in: spread over the first ~80% of the page."""
    if n <= 1:
        return [0.0]
    return [dur * 0.8 * i / n for i in range(n)]


def panel(cr, rect, t, start, spec, theme, base):
    """Draw one panel at rect (page coordinates) at page time t."""
    if t < start:
        return
    x, y, w, h = rect
    lt = t - start
    k = kit.ease(lt / 0.35)
    pop = 0.9 + 0.1 * kit.back(lt / 0.35)
    cr.save()
    cr.translate(x + w / 2, y + h / 2)
    cr.scale(pop, pop)
    cr.translate(-w / 2, -h / 2)
    cr.push_group()
    cr.rectangle(0, 0, w, h)
    cr.clip()
    # slow push-in inside the panel
    z = 1 + 0.05 * min(1.0, lt / 8)
    cr.save()
    cr.translate(w / 2, h / 2)
    cr.scale(z, z)
    cr.translate(-w / 2, -h / 2)
    art.draw_art(cr, w, h, lt, spec, theme)
    cr.restore()
    cr.set_source_surface(kit.halftone(int(w) + 1, int(h) + 1), 0, 0)
    cr.paint()
    # lettering on top
    size = base
    if spec.get("caption"):
        cw = min(w * 0.86, base * 26)
        at_bottom = spec.get("caption_pos") == "bottom"
        cy = h - base * 0.9 - (base * 1.18 * 3 + base) if at_bottom else base * 0.7
        kit.caption_box(cr, base * 0.7, cy, cw, spec["caption"], lt, 0.25, size, theme["caption"],
                        max_h=h * 0.42)
    b = spec.get("bubble")
    if b:
        bw = min(w * 0.6, base * 18)
        pos = b.get("pos", "top_right")
        bx = w * (0.68 if "right" in pos else 0.32 if "left" in pos else 0.5)
        by = h * (0.24 if "top" in pos else 0.62)
        tail = b.get("tail") or ((-bw * 0.25 if "right" in pos else bw * 0.25), h * 0.2)
        kit.bubble(cr, bx, by, bw, b.get("text", ""), lt, float(b.get("at", 0.8)), tail=tuple(tail),
                   size=base * 1.05, shout=bool(b.get("shout")), source=b.get("source"))
    sfx = spec.get("sfx")
    if sfx:
        if isinstance(sfx, str):
            sfx = {"text": sfx}
        kit.sfx(cr, w * float(sfx.get("x", 0.5)), h * float(sfx.get("y", 0.3)), str(sfx.get("text", "")).upper(),
                lt, float(sfx.get("at", 0.5)), size=min(h * 0.22, base * 4.5), rot=float(sfx.get("rot", -0.1)),
                fill=kit.rgb(sfx.get("colour"), (1, 0.85, 0.2)), shake=float(sfx.get("shake", 0)))
    cr.reset_clip()
    cr.rectangle(0, 0, w, h)
    cr.set_source_rgb(*kit.INK)
    cr.set_line_width(max(5, base * 0.25))
    cr.stroke()
    cr.pop_group_to_source()
    cr.paint_with_alpha(k)
    cr.restore()


def camera(layout_rects, starts, t, dur, W, H):
    """(cx, cy, zoom): drift towards the newest panel, ease back out at the end of the page."""
    if len(layout_rects) == 1:
        z = 1.0 + 0.05 * min(1.0, t / max(dur, 1))
        return W / 2, H / 2, z
    i = max(j for j, s in enumerate(starts) if t >= s)

    def target(j):
        x, y, w, h = layout_rects[j]
        z = min(1.12, 0.95 * min(W / w, H / h))
        z = max(1.0, z)
        cx = x + w / 2
        cy = y + h / 2
        return cx, cy, z

    cur = target(i)
    prev = target(i - 1) if i > 0 else (W / 2, H / 2, 1.0)
    k = kit.ease((t - starts[i]) / 0.9)
    cx = prev[0] + (cur[0] - prev[0]) * k
    cy = prev[1] + (cur[1] - prev[1]) * k
    z = prev[2] + (cur[2] - prev[2]) * k
    # last 15% of the page: pull back to show the whole page
    out = kit.ease((t - dur * 0.85) / (dur * 0.12)) if dur > 4 else 0
    cx += (W / 2 - cx) * out
    cy += (H / 2 - cy) * out
    z += (1.0 - z) * out
    # keep the page filling the frame
    half_w, half_h = W / 2 / z, H / 2 / z
    cx = min(max(cx, half_w), W - half_w)
    cy = min(max(cy, half_h), H - half_h)
    return cx, cy, z


def draw_page(cr, page, t, dur, W, H, theme, paper_surface):
    layout = page.get("layout", "splash")
    rs = rects(layout, W, H)
    panels = page.get("panels", [])[:len(rs)]
    starts = appear_times(len(panels), dur)
    cx, cy, z = camera(rs[:len(panels)] or rs, starts or [0.0], t, dur, W, H)
    cr.save()
    cr.translate(W / 2, H / 2)
    cr.scale(z, z)
    cr.translate(-cx, -cy)
    cr.set_source_surface(paper_surface, 0, 0)
    cr.paint()
    base = H * 0.026
    for r, s, p in zip(rs, starts, panels):
        panel(cr, r, t, s, p, theme, base)
    cr.restore()


def chapter_banner(cr, text, t, W, H, theme):
    """Red ribbon across the top for the first seconds of a new chapter."""
    if not text or t > 3.4:
        return
    k = kit.ease(t / 0.4) * (1 - kit.ease((t - 2.9) / 0.5))
    size = H * 0.055
    kit.font(cr, "title", size)
    label = str(text).upper()
    e = cr.text_extents(label)
    bw = e.x_advance + size * 2
    x = W / 2 - bw / 2
    y = H * 0.04 - (1 - k) * H * 0.15
    cr.save()
    cr.move_to(x, y)
    cr.line_to(x + bw, y)
    cr.line_to(x + bw - size * 0.4, y + size * 1.5)
    cr.line_to(x + size * 0.4, y + size * 1.5)
    cr.close_path()
    kit.inked(cr, theme["accent"], 5)
    cr.move_to(W / 2 - e.x_advance / 2, y + size * 1.12)
    cr.set_source_rgb(1, 1, 1)
    cr.show_text(label)
    cr.restore()
