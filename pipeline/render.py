"""Draw every comic page frame with pycairo (in parallel), then add narration, music and captions."""
from __future__ import annotations

import math
import multiprocessing as mp
import re
import subprocess
from pathlib import Path

import cairo

from . import kit, pages
from .common import FONTS, ROOT, log, media_duration, run

OUTRO_SECONDS = 6.0
TRANSITION = 0.45


def theme(cfg: dict) -> dict:
    return {"accent": kit.rgb(cfg.get("accent", "#d7262b")),
            "caption": kit.rgb(cfg.get("caption_colour", "#f7e07a")),
            "paper": kit.rgb(cfg.get("paper_colour", "#f4eedf"))}


def scene_pages(scene: dict) -> list[dict]:
    if scene.get("pages"):
        return list(scene["pages"])
    if scene.get("page"):
        return [scene["page"]]
    return []


def timeline(cfg: dict, script: dict) -> list[dict]:
    """One entry per page: when it starts, how long it stays up, and the chapter banner if any."""
    out, t = [], 0.0
    for si, scene in enumerate(script["scenes"]):
        scene["start"] = t
        pg = scene_pages(scene)
        weights = [max(1, len(p.get("panels", []))) for p in pg]
        total = sum(weights)
        pt = t
        for k, (p, wgt) in enumerate(zip(pg, weights)):
            dur = scene["duration"] * wgt / total
            out.append({"start": pt, "dur": dur, "page": p, "scene": si,
                        "chapter": scene.get("chapter") if (k == 0 and si > 0) else None})
            pt += dur
        t += scene["duration"]
    out.append({"start": t, "dur": OUTRO_SECONDS, "scene": -1, "chapter": None,
                "page": {"layout": "splash", "panels": [{"art": "title", "text": cfg["channel_name"],
                                                         "sub": cfg.get("end_card_line", "Sources in the description"),
                                                         "bg": "red_burst"}]}})
    return out


class Drawer:
    def __init__(self, cfg, entries):
        self.W, self.H = int(cfg.get("width", 1920)), int(cfg.get("height", 1080))
        self.fps = int(cfg.get("fps", 24))
        self.theme = theme(cfg)
        self.entries = entries
        self.paper = kit.paper(self.W, self.H, self.theme["paper"])

    def _find(self, t):
        lo = 0
        for i, e in enumerate(self.entries):
            if e["start"] <= t:
                lo = i
            else:
                break
        return lo

    def frame(self, n: int) -> cairo.ImageSurface:
        t = n / self.fps
        i = self._find(t)
        e = self.entries[i]
        lt = t - e["start"]
        s = cairo.ImageSurface(cairo.FORMAT_RGB24, self.W, self.H)
        cr = cairo.Context(s)
        cr.set_source_surface(self.paper, 0, 0)
        cr.paint()
        if i > 0 and lt < TRANSITION:
            prev = self.entries[i - 1]
            pages.draw_page(cr, prev["page"], prev["dur"] - 0.01, prev["dur"], self.W, self.H, self.theme, self.paper)
            k = kit.ease(lt / TRANSITION)
            cr.save()
            cr.translate(self.W * (1 - k), 0)
            cr.rectangle(-14, 0, 14, self.H)
            cr.set_source_rgba(0, 0, 0, 0.35)
            cr.fill()
            cr.rectangle(0, 0, self.W, self.H)
            cr.clip()
            pages.draw_page(cr, e["page"], lt, e["dur"], self.W, self.H, self.theme, self.paper)
            cr.restore()
        else:
            pages.draw_page(cr, e["page"], lt, e["dur"], self.W, self.H, self.theme, self.paper)
        pages.chapter_banner(cr, e.get("chapter"), lt, self.W, self.H, self.theme)
        return s


_DRAWER: Drawer | None = None


def _chunk(args):
    a, b, path, W, H, fps = args
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0",
                             "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps), str(path)],
                            stdin=subprocess.PIPE)
    for n in range(a, b):
        s = _DRAWER.frame(n)
        s.flush()
        proc.stdin.write(bytes(s.get_data()))
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed on frames {a}-{b}")
    return path


def draw_video(cfg: dict, script: dict, work: Path) -> Path:
    global _DRAWER
    entries = timeline(cfg, script)
    _DRAWER = Drawer(cfg, entries)
    fps, W, H = _DRAWER.fps, _DRAWER.W, _DRAWER.H
    total = entries[-1]["start"] + entries[-1]["dur"]
    frames = int(round(total * fps))
    workers = max(1, int(cfg.get("render_workers", 4)))
    n_chunks = max(workers * 3, 1)
    step = math.ceil(frames / n_chunks) if frames else 1
    chunks_dir = work / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(a, min(a + step, frames), chunks_dir / f"c{i:03d}.mp4", W, H, fps)
            for i, a in enumerate(range(0, frames, step))]
    log(f"Drawing {frames} frames ({total / 60:.1f} minutes) on {workers} cores")
    ctx = mp.get_context("fork")
    done = 0
    with ctx.Pool(workers) as pool:
        for _ in pool.imap_unordered(_chunk, jobs):
            done += 1
            if done % max(1, len(jobs) // 6) == 0 or done == len(jobs):
                log(f"Drawn {done}/{len(jobs)} parts")
    listing = work / "chunks.txt"
    listing.write_text("".join(f"file '{j[2].resolve()}'\n" for j in jobs))
    silent = work / "video_silent.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(silent)])
    return silent



def render(cfg: dict, script: dict, work: Path) -> Path:
    silent = draw_video(cfg, script, work)
    chapters = [(s["start"], s["chapter"]) for s in script["scenes"] if s.get("chapter")]

    inputs, filters = [], []
    for i, scene in enumerate(script["scenes"]):
        inputs += ["-i", scene["audio"]]
        filters.append(f"[{i}:a]aresample=44100,apad=whole_dur={scene['duration']}[a{i}]")
    n = len(script["scenes"])
    total = media_duration(silent)
    filters.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,apad=whole_dur={total}[narr]")
    music = ROOT / "assets" / cfg.get("music_file", "music.mp3")
    if music.exists():
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        filters.append(f"[{n}:a]volume={cfg.get('music_volume', 0.07)},atrim=0:{total},"
                       f"afade=t=out:st={max(total - 4, 0)}:d=4[mus]")
        filters.append("[narr][mus]amix=inputs=2:duration=first:normalize=0[aout]")
        out_label = "[aout]"
    else:
        out_label = "[narr]"
    audio = work / "audio.m4a"
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", out_label, "-c:a", "aac", "-b:a", "192k", "-t", str(total), str(audio)])
    final = work / "final.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest",
         "-movflags", "+faststart", str(final)])

    build_srt(script, work / "captions.srt")
    script["chapter_times"] = chapters
    script["clean_video"] = str(final)
    if cfg.get("burn_captions", False):
        final = _burn(work / "captions.srt", final, work / "final_captioned.mp4")
    log(f"Video rendered: {media_duration(final) / 60:.1f} minutes")
    return final


# ------------------------------------------------------------------ captions (.srt)
def _srt_time(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def _two_lines(text: str, width: int = 42) -> str:
    if len(text) <= width:
        return text
    mid = len(text) // 2
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    cut = min(spaces, key=lambda i: abs(i - mid)) if spaces else mid
    return text[:cut] + "\n" + text[cut + 1:]


def _word_cues(scene: dict, offset: float, max_chars: int = 78):
    cues, cur, t0, last_end = [], [], None, 0.0
    for word, a, b in scene["words"]:
        text = " ".join(cur + [word])
        if cur and (len(text) > max_chars or a - last_end > 0.6):
            cues.append((offset + t0, offset + last_end, " ".join(cur)))
            cur, t0 = [], None
        if t0 is None:
            t0 = a
        cur.append(word)
        last_end = b
        if word[-1] in ".?!" and len(" ".join(cur)) > 25:
            cues.append((offset + t0, offset + last_end, " ".join(cur)))
            cur, t0 = [], None
    if cur:
        cues.append((offset + t0, offset + last_end, " ".join(cur)))
    out = []
    for i, (a, b, text) in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else b + 0.3
        out.append((a, max(b, min(nxt, b + 0.7)), text))
    return out


def build_srt(script: dict, path: Path) -> None:
    lines, t, n = [], 0.0, 1
    for scene in script["scenes"]:
        if scene.get("words"):
            for a, b, text in _word_cues(scene, t):
                lines += [str(n), f"{_srt_time(a)} --> {_srt_time(b)}", _two_lines(text), ""]
                n += 1
        else:
            speech = scene["duration"] - 0.45
            words = scene["narration"].split()
            chunks = [" ".join(words[i:i + 11]) for i in range(0, len(words), 11)]
            total_chars = sum(len(c) for c in chunks) or 1
            ct = t
            for c in chunks:
                d = speech * len(c) / total_chars
                lines += [str(n), f"{_srt_time(ct)} --> {_srt_time(ct + d)}", c, ""]
                ct += d
                n += 1
        t += scene["duration"]
    path.write_text("\n".join(lines), encoding="utf-8")


def _burn(srt: Path, video: Path, out: Path) -> Path:
    fonts = str(FONTS).replace("\\", "/").replace(":", r"\:")
    sub = str(srt).replace("\\", "/").replace(":", r"\:")
    style = ("FontName=Comic Neue,Bold=1,FontSize=14,PrimaryColour=&H00FFFFFF,"
             "BackColour=&H5A000000,OutlineColour=&H5A000000,BorderStyle=3,Outline=0.7,Shadow=0,"
             "Alignment=2,MarginV=14,MarginL=40,MarginR=40")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
         "-vf", f"subtitles='{sub}':fontsdir='{fonts}':force_style='{style}'",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "copy", "-movflags", "+faststart", str(out)])
    log("Captions burned into the video")
    return out


def fmt_ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def chapter_lines(script: dict) -> list[str]:
    """YouTube chapters: first at 0:00, at least 3, each at least 10 seconds apart."""
    out, last = [], -999.0
    for t, name in script.get("chapter_times", []):
        if not out:
            t = 0.0
        if t - last < 10:
            continue
        out.append(f"{fmt_ts(t)} {re.sub(r'\s+', ' ', name).strip()}")
        last = t
    return out if len(out) >= 3 else []
