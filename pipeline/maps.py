"""Comic-style maps drawn from Natural Earth country outlines (assets/maps/countries.geojson).

A map panel:
    {"art": "map", "region": "middle_east",              # or "bbox": [west, south, east, north]
     "highlight": {"Iran": "#d7262b", "Israel": "#2f6db5"},
     "occupied": ["Crimea"],                              # hatched over their colour
     "labels": ["Iran", "Israel"],                        # country names written on the map
     "markers": [{"lon": 51.4, "lat": 35.7, "label": "Tehran", "style": "pulse"}],
     "arrows": [{"from": [35, 32], "to": [51, 35], "label": "Strikes", "colour": "#d7262b"}]}
Country names are Natural Earth's ("United States of America", "Russia", "Iran", ...); "Crimea",
"West Bank" and "Gaza Strip" are separate shapes. "Palestinian territories" means West Bank + Gaza.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache

import cairo

from . import kit
from .common import ROOT

REGIONS = {
    "world": (-170, -58, 180, 80),
    "middle_east": (24, 11, 64, 42),
    "gulf": (44, 21, 61, 33),
    "hormuz": (52.5, 24, 59.5, 28.2),
    "levant": (32.5, 29, 40, 37.5),
    "israel": (33.6, 29.3, 36.4, 33.6),
    "gaza": (34.1, 31.15, 34.65, 31.65),
    "red_sea": (31, 11, 46, 30),
    "iran": (43, 24, 64, 40.5),
    "ukraine": (21, 43.5, 41.5, 53.5),
    "black_sea": (26, 40, 42.5, 48.5),
    "russia_ukraine": (18, 40, 62, 62),
    "europe": (-12, 34, 45, 63),
    "eastern_europe": (12, 42, 50, 60),
    "usa": (-127, 23, -65, 50),
    "north_atlantic": (-80, 25, 10, 62),
    "asia": (60, -10, 150, 55),
}
ALIASES = {
    "USA": "United States of America", "US": "United States of America", "United States": "United States of America",
    "UK": "United Kingdom", "Britain": "United Kingdom", "UAE": "United Arab Emirates",
    "Saudi": "Saudi Arabia", "Palestinian territories": ["West Bank", "Gaza Strip"], "Gaza": "Gaza Strip",
}
SEA = (0.42, 0.62, 0.82)
LAND = (0.93, 0.89, 0.76)
DIM = (0.8, 0.77, 0.66)


@lru_cache(maxsize=1)
def countries() -> list[dict]:
    data = json.loads((ROOT / "assets" / "maps" / "countries.geojson").read_text(encoding="utf-8"))
    out = []
    for f in data["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = [p[0] for p in polys if p and p[0]]
        xs = [x for r in rings for x, _ in r]
        ys = [y for r in rings for _, y in r]
        biggest = max(rings, key=_ring_area)
        out.append({"name": f["properties"]["name"], "admin": f["properties"]["admin"], "rings": rings,
                    "bbox": (min(xs), min(ys), max(xs), max(ys)), "centre": _centroid(biggest)})
    return out


def names() -> set[str]:
    return {c["name"] for c in countries()} | {c["admin"] for c in countries()} | set(ALIASES)


def _ring_area(r):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))) / 2


def _centroid(r):
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
        k = x1 * y2 - x2 * y1
        a += k
        cx += (x1 + x2) * k
        cy += (y1 + y2) * k
    if abs(a) < 1e-9:
        return r[0]
    return (cx / (3 * a), cy / (3 * a))


def _expand(name) -> list[str]:
    v = ALIASES.get(name, name)
    return v if isinstance(v, list) else [v]


def view(spec: dict, w: float, h: float):
    """Projection for the panel: equirectangular, x squeezed by cos(latitude), bbox grown to fill."""
    west, south, east, north = spec.get("bbox") or REGIONS.get(spec.get("region", "world"), REGIONS["world"])
    mid = math.radians((south + north) / 2)
    kx = math.cos(mid)
    bw, bh = (east - west) * kx, (north - south)
    scale = min(w / bw, h / bh)
    cxl, cyl = (west + east) / 2, (south + north) / 2

    def proj(lon, lat):
        return (w / 2 + (lon - cxl) * kx * scale, h / 2 - (lat - cyl) * scale)

    vis = (cxl - w / 2 / (kx * scale), cyl - h / 2 / scale, cxl + w / 2 / (kx * scale), cyl + h / 2 / scale)
    return proj, vis, scale


@lru_cache(maxsize=24)
def _base(spec_json: str, w: int, h: int, accent: tuple) -> cairo.ImageSurface:
    spec = json.loads(spec_json)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(s)
    proj, vis, scale = view(spec, w, h)
    cr.set_source_rgb(*SEA)
    cr.paint()
    # faint lat/lon grid
    cr.set_source_rgba(1, 1, 1, 0.18)
    cr.set_line_width(1.2)
    step = 10 if vis[2] - vis[0] > 30 else (5 if vis[2] - vis[0] > 8 else 1)
    for lon in range(int(math.floor(vis[0] / step) * step), int(vis[2]) + step, step):
        x, _ = proj(lon, 0)
        cr.move_to(x, 0)
        cr.line_to(x, h)
    for lat in range(int(math.floor(vis[1] / step) * step), int(vis[3]) + step, step):
        _, y = proj(0, lat)
        cr.move_to(0, y)
        cr.line_to(w, y)
    cr.stroke()

    hl = {}
    for k, v in (spec.get("highlight") or {}).items():
        for n in _expand(k):
            hl[n] = kit.rgb(v, accent)
    if "Ukraine" in hl and "Crimea" not in hl:
        hl["Crimea"] = hl["Ukraine"]      # internationally recognised borders by default
    if "Syria" in hl and "Golan Heights" not in hl:
        hl["Golan Heights"] = hl["Syria"]
    occupied = {n for k in (spec.get("occupied") or []) for n in _expand(k)}
    dim = spec.get("dim_others", bool(hl))
    lw = max(1.2, min(3.5, scale * 0.06))

    def path(c):
        for ring in c["rings"]:
            pts = [proj(x, y) for x, y in ring]
            cr.move_to(*pts[0])
            for p in pts[1:]:
                cr.line_to(*p)
            cr.close_path()

    for c in countries():
        b = c["bbox"]
        if b[2] < vis[0] - 1 or b[0] > vis[2] + 1 or b[3] < vis[1] - 1 or b[1] > vis[3] + 1:
            continue
        path(c)
        fill = hl.get(c["name"]) or hl.get(c["admin"]) or (DIM if dim else LAND)
        cr.set_source_rgb(*fill)
        cr.fill_preserve()
        cr.set_source_rgb(*kit.INK)
        cr.set_line_width(lw * (1.5 if c["name"] in hl else 1))
        if c["name"] in ("Crimea", "Golan Heights"):
            cr.set_dash([lw * 3, lw * 2])
        cr.stroke()
        cr.set_dash([])
        if c["name"] in occupied or c["admin"] in occupied:
            cr.save()
            path(c)
            cr.clip()
            cr.set_source_rgba(*kit.INK, 0.55)
            cr.set_line_width(max(1.5, lw))
            x0, y0 = proj(b[0], b[3])
            x1, y1 = proj(b[2], b[1])
            gap = max(6, (x1 - x0 + y1 - y0) / 40)
            k = x0 - (y1 - y0)
            while k < x1:
                cr.move_to(k, y1)
                cr.line_to(k + (y1 - y0), y0)
                k += gap
            cr.stroke()
            cr.restore()
    # halftone shadow on the sea edge for a printed look
    cr.set_source_surface(kit.halftone(w, h, 9, 0.08), 0, 0)
    cr.paint()
    # country labels
    size = max(14, min(34, h / 22))
    for name in spec.get("labels") or []:
        for n in _expand(name):
            c = next((c for c in countries() if c["name"] == n or c["admin"] == n), None)
            if not c:
                continue
            x, y = proj(*c["centre"])
            if not (0 < x < w and 0 < y < h):
                # centre is off the map: use the middle of the part of the country that is visible
                b = c["bbox"]
                lon = (max(b[0], vis[0]) + min(b[2], vis[2])) / 2
                lat = (max(b[1], vis[1]) + min(b[3], vis[3])) / 2
                x, y = proj(lon, lat)
                if not (0 < x < w and 0 < y < h):
                    continue
            kit.font(cr, "caption", size)
            text = name.upper() if isinstance(ALIASES.get(name), list) else n.upper()
            text = {"UNITED STATES OF AMERICA": "USA"}.get(text, text)
            e = cr.text_extents(text)
            x = min(max(x, e.x_advance / 2 + 12), w - e.x_advance / 2 - 12)
            y = min(max(y, e.height + 12), h - 12)
            cr.move_to(x - e.x_advance / 2, y + e.height / 2)
            cr.text_path(text)
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(size * 0.28)
            cr.stroke_preserve()
            cr.set_source_rgb(*kit.INK)
            cr.fill()
    return s


def draw(cr, w, h, t, spec, theme):
    accent = theme["accent"]
    key = json.dumps({k: spec.get(k) for k in ("region", "bbox", "highlight", "occupied", "labels", "dim_others")},
                     sort_keys=True)
    cr.set_source_surface(_base(key, int(w), int(h), accent), 0, 0)
    cr.paint()
    proj, _, scale = view(spec, w, h)
    size = max(14, min(32, h / 24))
    # arrows draw on one after another
    for i, a in enumerate(spec.get("arrows") or []):
        k = kit.ease((t - 0.6 - i * 0.7) / 1.0)
        if k <= 0:
            continue
        (x0, y0), (x1, y1) = proj(*a["from"]), proj(*a["to"])
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = -(y1 - y0), (x1 - x0)
        bend = float(a.get("bend", 0.18))
        cx, cy = mx + nx * bend, my + ny * bend
        col = kit.rgb(a.get("colour"), accent)
        pts = []
        for j in range(41):
            u = j / 40 * k
            pts.append(((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1,
                        (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1))
        lw = max(6, h / 70)
        for width, colour in ((lw + 6, kit.INK), (lw, col)):
            cr.move_to(*pts[0])
            for p in pts[1:]:
                cr.line_to(*p)
            cr.set_source_rgb(*colour)
            cr.set_line_width(width)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.stroke()
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        ang = math.atan2(by - ay, bx - ax)
        hs = lw * 2.6
        cr.move_to(bx + math.cos(ang) * hs * 0.6, by + math.sin(ang) * hs * 0.6)
        cr.line_to(bx + math.cos(ang + 2.5) * hs, by + math.sin(ang + 2.5) * hs)
        cr.line_to(bx + math.cos(ang - 2.5) * hs, by + math.sin(ang - 2.5) * hs)
        cr.close_path()
        kit.inked(cr, col, 3)
        if a.get("label") and k >= 1:
            kit.label_tag(cr, cx, cy - size * 0.8, a["label"], size * 0.8, fill=(1, 1, 1))
    for i, m in enumerate(spec.get("markers") or []):
        if t < 0.3 + i * 0.35:
            continue
        x, y = proj(m["lon"], m["lat"])
        r = max(8, h / 55)
        style = m.get("style", "dot")
        cr.new_path()
        if style == "pulse":
            p = ((t - 0.3 - i * 0.35) % 1.6) / 1.6
            cr.arc(x, y, r + p * r * 4, 0, 2 * math.pi)
            cr.set_source_rgba(*accent, 1 - p)
            cr.set_line_width(4)
            cr.stroke()
        if style == "star":
            cr.move_to(x, y - r * 1.6)
            for j in range(1, 10):
                a = -math.pi / 2 + j * math.pi / 5
                rr = r * 1.6 if j % 2 == 0 else r * 0.7
                cr.line_to(x + rr * math.cos(a), y + rr * math.sin(a))
            cr.close_path()
            kit.inked(cr, (1, 0.85, 0.2), 3)
        else:
            cr.arc(x, y, r, 0, 2 * math.pi)
            kit.inked(cr, kit.rgb(m.get("colour"), accent), 3)
        if m.get("label"):
            kit.label_tag(cr, x + r * 1.4, y - size * 0.75, m["label"], size * 0.75, fill=(1, 1, 1), centre=False)
