"""Shared helpers: settings, logging, ffmpeg and fonts."""
from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
FONTS = ROOT / "assets" / "fonts"

# Every channel is a file in channels/. Add a file to add a channel.
CHANNELS = tuple(sorted(f.stem for f in (ROOT / "channels").glob("*.yaml")))
DEFAULT_CHANNEL = "comic"


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_config(channel: str | None = None) -> dict:
    """Shared settings (config.yaml) with the channel's own file (channels/<channel>.yaml) on top."""
    channel = (channel or DEFAULT_CHANNEL).strip().lower()
    if channel not in CHANNELS:
        raise SystemExit(f"Unknown channel '{channel}'. Use one of: {', '.join(CHANNELS)} "
                         f"(each channel is a file in the channels folder)")
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(ROOT / "channels" / f"{channel}.yaml", encoding="utf-8") as f:
        cfg.update(yaml.safe_load(f) or {})
    cfg["channel"] = channel
    cfg.setdefault("label", channel.title())
    return cfg


def require_ready(cfg: dict) -> None:
    """Stop before spending credits if the channel file still has placeholder values."""
    for key in ("channel_name", "elevenlabs_voice_id"):
        if "REPLACE" in str(cfg.get(key, "")):
            raise SystemExit(f"channels/{cfg['channel']}.yaml: set {key} first (see the README, step 3)")


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd[:6])}...\n{r.stderr[-2000:]}")


def media_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def font_path(bold: bool = True) -> str:
    """Plain sans font (used by the vertical clips' channel line)."""
    p = FONTS / ("InstrumentSans-Bold.ttf" if bold else "InstrumentSans-Regular.ttf")
    if p.exists():
        return str(p)
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def comic_font(kind: str = "caption") -> str:
    """'title' = Bangers (titles, sound effects), 'caption' = Comic Neue Bold, 'body' = Comic Neue Regular."""
    name = {"title": "Bangers-Regular.ttf", "caption": "ComicNeue-Bold.ttf", "body": "ComicNeue-Regular.ttf"}[kind]
    return str(FONTS / name)


def hex_rgb(h: str) -> tuple[float, float, float]:
    h = str(h).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
