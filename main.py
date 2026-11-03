"""Comic pipeline: make one comic-style video from a plan written in the Claude chat.

    python main.py check plans/x.json     # check a plan without spending anything
    python main.py render plans/x.json    # make the video, thumbnail, clips and upload sheet

Everything for the upload is written to out/: video.mp4, thumbnail.jpg, captions.srt, UPLOAD.txt,
script.txt, CLIPS.txt and clips/, plus issue.md for the GitHub "Ready to upload" issue.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline import art, clips, flags, kit, maps, packaging, render, voice
from pipeline.common import ROOT, WORK, load_config, log, require_ready
from pipeline.pages import LAYOUTS

OUT = ROOT / "out"


def _when(slot) -> str:
    if not slot:
        return "your next free slot"
    uk = slot.astimezone(ZoneInfo("Europe/London"))
    text = f"{uk:%A %d %B %Y, %H:%M} (UK time)"
    if slot.utcoffset() != uk.utcoffset():
        text += f", which is {slot:%H:%M} in the channel's audience time zone"
    return text


def upload_sheet(script, desc, slot, cfg) -> str:
    return f"""UPLOAD DETAILS (copy each part into YouTube Studio)
================================================================

CHANNEL: {cfg['channel_name']}  ({cfg['label']})
>>> In YouTube Studio, switch to this channel before you upload. <<<

SUGGESTED PUBLISH TIME: {_when(slot)}

TITLE:
{script['title']}

(Other title options: {' | '.join(script.get('alt_titles', []))})

DESCRIPTION:
{desc}

TAGS (paste into "Tags", under "Show more"):
{', '.join(script.get('tags', []))}

SETTINGS:
- Audience: No, it's not made for kids
- Altered or synthetic content: Yes (AI narration)
- Category: {cfg.get('youtube_category', 'Education')}
- Subtitles: upload captions.srt (Subtitles > Add language > English > Upload file > With timing)
- Thumbnail: upload thumbnail.jpg
"""


def issue_text(script, brief, slot, attention, cfg) -> str:
    unverified = "\n".join(f"- {u.get('claim')} ({u.get('reason')})" for u in brief.get("unverified", [])) or "- none"
    head = f"### ⚠️ Needs attention\n{attention}\n\n" if attention else ""
    pages_n = sum(len(render.scene_pages(s)) for s in script["scenes"])
    return f"""{head}**Channel: {cfg['channel_name']}** ({cfg['label']})

**{script['title']}**

{script['narration_seconds'] / 60:.1f} minutes · {pages_n} comic pages · suggested publish time **{_when(slot)}**

### How to upload
1. Scroll to the bottom of the linked run page and download the **video-…** file under *Artifacts* (it's a zip).
2. Unzip it and open **UPLOAD.txt**: it has the title, description, tags and settings to copy in.
3. Watch it through, then upload and schedule. When it's done, close this issue.

### Worth a look before you upload
Points the research could not confirm (the script was told not to state these as fact):
{unverified}
"""


def check_plan(plan_path: str) -> dict:
    """Catch mistakes in a plan before any ElevenLabs credits are spent."""
    script = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    problems, warnings = [], []
    for k in ("title", "scenes"):
        if k not in script:
            problems.append(f"missing '{k}'")
    cfg = load_config(script.get("channel"))
    require_ready(cfg)
    country_names = maps.names()
    for i, scene in enumerate(script.get("scenes", []), 1):
        if not str(scene.get("narration", "")).strip():
            problems.append(f"scene {i} has no narration")
        pgs = render.scene_pages(scene)
        if not pgs:
            problems.append(f"scene {i} has no 'page' (or 'pages')")
        for pi, page in enumerate(pgs, 1):
            where = f"scene {i} page {pi}"
            layout = page.get("layout", "splash")
            if layout not in LAYOUTS:
                problems.append(f"{where}: unknown layout '{layout}' (use one of {', '.join(LAYOUTS)})")
                continue
            panels = page.get("panels") or []
            if len(panels) != LAYOUTS[layout]:
                problems.append(f"{where}: layout '{layout}' needs {LAYOUTS[layout]} panels, it has {len(panels)}")
            for k, p in enumerate(panels, 1):
                pw = f"{where} panel {k}"
                kind = p.get("art")
                if kind not in art.ART:
                    warnings.append(f"{pw}: unknown art '{kind}' (drawn as a title panel)")
                cap = str(p.get("caption", ""))
                if len(cap) > 150:
                    problems.append(f"{pw}: caption is {len(cap)} characters (max 150)")
                b = p.get("bubble")
                if b and not str(b.get("source", "")).strip():
                    problems.append(f"{pw}: speech bubbles must quote a real, sourced statement: add 'source'")
                for key in ("who", "other"):
                    who = p.get(key)
                    preset = who if isinstance(who, str) else (who or {}).get("preset")
                    if preset and preset not in kit.PEOPLE:
                        warnings.append(f"{pw}: unknown person preset '{preset}'")
                for f in (p.get("flags") or []) + [p.get("flag"), p.get("left_flag"), p.get("right_flag")]:
                    if f and f not in flags.FLAGS and f != "stripes":
                        warnings.append(f"{pw}: unknown flag '{f}' (drawn grey)")
                if kind == "map":
                    if not p.get("bbox") and p.get("region", "world") not in maps.REGIONS:
                        problems.append(f"{pw}: unknown map region '{p.get('region')}'")
                    for name in list((p.get("highlight") or {}).keys()) + list(p.get("labels") or []) + \
                            list(p.get("occupied") or []):
                        if name not in country_names:
                            warnings.append(f"{pw}: map has no country called '{name}'")
                if kind == "chart":
                    if len(p.get("labels", [])) != len(p.get("values", [])) or not p.get("values"):
                        problems.append(f"{pw}: chart labels and values must be the same length")
    n = len(script.get("scenes", []))
    for k, c in enumerate(script.get("clips", []), 1):
        sc = c.get("scenes")
        if not (isinstance(sc, list) and len(sc) == 2 and all(isinstance(x, int) for x in sc)
                and 1 <= sc[0] <= sc[1] <= n):
            problems.append(f"clip {k}: 'scenes' must be [first, last] scene numbers between 1 and {n}")
    for w in warnings:
        log(f"Warning: {w}")
    if problems:
        raise SystemExit(f"{plan_path} has problems:\n- " + "\n- ".join(problems))
    log(f"Plan OK: {script['title']} ({cfg['label']} channel)")
    return script


def render_plan(plan_path: str) -> None:
    script = check_plan(plan_path)
    cfg = load_config(script.get("channel"))
    script.setdefault("alt_titles", [])
    script.setdefault("tags", [])
    script.setdefault("description_summary", "")
    if not script["scenes"][0].get("chapter"):
        script["scenes"][0]["chapter"] = "Introduction"
    brief = {"sources": script.get("sources", []), "unverified": script.get("unverified", [])}
    slug = Path(plan_path).stem
    work = WORK / slug
    work.mkdir(parents=True, exist_ok=True)
    words = sum(len(s["narration"].split()) for s in script["scenes"])
    log(f"Rendering plan: {script['title']} ({words} words, {len(script['scenes'])} scenes)")

    voice.narrate(cfg, script, work / "audio")
    video = render.render(cfg, script, work)
    thumb = packaging.thumbnail(script, work / "thumbnail.jpg", cfg)
    desc = packaging.description(cfg, script, brief)

    attention = []
    mins = script["narration_seconds"] / 60
    if not 7.5 <= mins <= 12.5:
        attention.append(f"Narration is {mins:.1f} minutes, outside the 8-12 minute target.")
    attention = " ".join(attention)
    slot = datetime.fromisoformat(script["publish_at"]) if script.get("publish_at") else None

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    shutil.copy(video, OUT / "video.mp4")
    shutil.copy(thumb, OUT / "thumbnail.jpg")
    shutil.copy(work / "captions.srt", OUT / "captions.srt")
    (OUT / "UPLOAD.txt").write_text(upload_sheet(script, desc, slot, cfg), encoding="utf-8")
    (OUT / "script.txt").write_text("\n\n".join(
        (f"## {s['chapter']}\n\n" if s.get("chapter") else "") + s["narration"] for s in script["scenes"]),
        encoding="utf-8")
    (OUT / "issue.md").write_text(issue_text(script, brief, slot, attention, cfg), encoding="utf-8")
    (OUT / "issue_title.txt").write_text(
        f"{'⚠️ ' if attention else ''}[{cfg['label']}] Ready to upload: {script['title']}", encoding="utf-8")
    (OUT / "channel.txt").write_text(cfg["channel"], encoding="utf-8")

    clean = Path(script.get("clean_video") or OUT / "video.mp4")
    made = clips.make_all(cfg, script, clean, OUT / "clips", work / "clips")
    if made:
        (OUT / "CLIPS.txt").write_text(clips.clips_sheet(cfg, script, made), encoding="utf-8")
        with open(OUT / "issue.md", "a", encoding="utf-8") as f:
            f.write(f"\n### Short clips\n{len(made)} vertical clips (under a minute each) are in the download's "
                    "`clips` folder. `CLIPS.txt` has a title, caption and hashtags for each, plus a posting "
                    "checklist for Shorts, Reels, TikTok, Facebook and Snapchat.\n")
    shutil.rmtree(work, ignore_errors=True)
    log(f"Done: {script['title']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["render"] and len(args) > 1:
        render_plan(args[1])
    elif args[:1] == ["check"] and len(args) > 1:
        for path in args[1:]:
            check_plan(path)
    else:
        sys.exit("Usage: python main.py check plans/x.json | render plans/x.json")
