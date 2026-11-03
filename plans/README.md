# Writing comic plans

Upload plan files (`.json`) to this folder. Each one becomes a comic-style video, a comic thumbnail,
three vertical short clips and an upload sheet. Finished plans move to `plans/done/`.
`docs/example-plan.json` is a short worked example.

## The plan file

```json
{"channel": "comic",
 "title": "Under 70 characters", "alt_titles": ["...", "..."],
 "thumbnail_text": "2-4 WORDS, one *STARRED*", "thumbnail_tag": "SHORT TAG", "thumbnail_badge": "EXPLAINED",
 "thumbnail_panel": {"art": "duo", "...": "..."},
 "description_summary": "2-3 sentences", "tags": ["..."], "publish_at": "2026-11-05T18:00:00+00:00",
 "sources": [{"title": "...", "url": "..."}], "unverified": [{"claim": "...", "reason": "..."}],
 "pronunciations": {"Word": "say-it-like-this"},
 "clips": [{"scenes": [1, 3], "hook": "...", "caption": "...", "hashtags": ["..."]}],
 "scenes": [
   {"chapter": "Introduction", "narration": "...",
    "page": {"layout": "trio_left", "panels": [{"art": "...", "caption": "..."}, {}, {}]}},
   {"narration": "...", "pages": [{"layout": "splash", "panels": [{}]}, {"layout": "duo_v", "panels": [{}, {}]}]}
 ]}
```

- One scene = one block of narration (40-75 words) with one page, or 2-3 `pages` for long scenes.
  The scene's narration time is shared between its pages by panel count.
- Panels pop in one after another across the page, and the camera drifts to the newest one,
  so put the panels in the order the narration talks about them.
- `chapter` on a scene shows a red chapter ribbon and becomes a YouTube chapter.

## Layouts

| Layout | Panels | Shape |
|---|---|---|
| `splash` | 1 | one full page |
| `duo_v` | 2 | side by side |
| `duo_h` | 2 | stacked |
| `trio_left` | 3 | big panel left, two stacked right |
| `trio_right` | 3 | two stacked left, big panel right |
| `trio_top` | 3 | two on top, one wide below |
| `trio_bottom` | 3 | one wide on top, two below |
| `strip3` | 3 | three columns |
| `quad` | 4 | 2 x 2 grid |

The panel count must match the layout exactly.

## Lettering on any panel

- `caption`: yellow narration box (max 150 characters; aim for under 70). `"caption_pos": "bottom"` moves it down.
- `bubble`: `{"text": "...", "source": "Who, date (outlet)", "pos": "top_right", "shout": false}`.
  **Speech bubbles are only for real, verified quotes**, and `source` is required (the plan check
  refuses a bubble without one). Everything else goes in captions.
- `sfx`: `"BOOM!"` or `{"text": "TICK TOCK", "x": 0.8, "y": 0.2, "colour": "#ffffff", "at": 0.5}`.
- `bg`: panel background: `night`, `dusk`, `dawn`, `day`, `dark`, `grey`, `paper`, `red`, `yellow`, `blue`, `green`, `purple`; add `_burst` for speed lines (e.g. `red_burst`).

## Art kinds

| Art | Options |
|---|---|
| `title` | text, sub, bg |
| `question` | text, bg |
| `portrait` | who, mood, talking, flag, bg |
| `duo` | who, other, mood, other_mood, talking (who|other), flags [left, right], bg |
| `group` | people [who, ...] (2-6), bg |
| `crowd` | signs [text], flags [names], count, bg |
| `podium` | who, mood, talking, sign, flags [up to 2], bg |
| `table` | who, other, flags [left, right], label, talking (who|other), bg |
| `handshake` | sleeves [colour, colour], flags [left, right], bg |
| `phone_call` | who, other, bg, other_bg |
| `map` | region | bbox, highlight {country: colour}, occupied [names], labels [names], markers, arrows, title |
| `building` | kind (dome|columns|white_house|towers|parliament|office|embassy|hospital|apartments|refinery|power_plant|nuclear_site), night, lights_out_at, flag, label |
| `city` | night, lights_out_at |
| `document` | title, lines, stamp, signature |
| `newspaper` | headline, masthead (keep it fictional) |
| `tv` | headline, ticker [text], inner (another panel spec shown on the screen) |
| `calendar` | date ('3 NOV'), year |
| `flag` | flag | stripes {colours, vertical}, bg |
| `stat` | value, label, note |
| `chart` | type (bar|line), labels, values, title, source, prefix, suffix, highlight |
| `versus` | left_title, right_title, left_items, right_items, left_flag, right_flag, left_bg, right_bg |
| `list` | title, items (max 5) |
| `quote` | text (real quote only), by |
| `scales` | tilt (-1 to 1), labels [left, right] |
| `money` | symbol, label |
| `jets` | count, night |
| `missiles` | count, intercept |
| `drones` | count |
| `warship` | kind (destroyer|carrier), count, flag, night |
| `ship` | kind (destroyer|carrier|tanker), night |
| `tanker` | blocked, label |
| `fuel_pump` | from, to, unit |
| `power_grid` | lights_out_at |
| `tanks` | count, direction, colour |
| `soldiers` | count |
| `ballot` | label |
| `plane` | label |
| `aid` | count, label, symbol (red_cross|un) |

Unknown art kinds don't stop a render: they become a title panel and the plan check prints a warning.

## People

`who` / `other` / `people` take a preset name or an object with overrides:
`{"preset": "official", "name": "Shown on the name plate", "hair": "swept", "hair_colour": "grey",
"skin": "medium", "facial": "beard", "glasses": true, "outfit": "suit", "colour": "#20283c", "tie": "#8a1c1c",
"cap": "officer", "mood": "serious"}`

- Presets: `official`, `president`, `diplomat`, `analyst`, `general`, `officer`, `soldier`, `pilot`, `sailor`, `reporter`, `protester`, `worker`, `voter`, `citizen`, `scientist`, `judge`, `monarch`, `aid_worker`
- `hair`: short, swept, curly, long, receding, none · `hair_colour`: black, brown, grey, white, blond, red, silver or a hex colour
- `skin`: light, fair, medium, tan, brown, dark · `facial`: beard, stubble · `cap`: officer, helmet, pilot, hardhat, sailor, beret
- `outfit`: suit, uniform, fatigues, flightsuit, casual, coat, labcoat, robe, vest, workwear
- `mood`: neutral, serious, concerned, speaking, determined, surprised, smiling, listening · `talking: true` animates the mouth

Real people are drawn as neutral, generic figures with a name plate: no caricature, no mocking
expressions, and nothing they didn't say.

## Flags

`us`, `uk`, `eu`, `un`, `nato`, `israel`, `palestine`, `ukraine`, `russia`, `iran`, `lebanon`, `qatar`, `uae`, `france`, `germany`, `poland`, `turkey`, `china`, `japan`, `canada`, `italy`, `spain`, `netherlands`, `belarus`, `georgia`, `white`, or `"flag": "stripes", "stripes": {"colours": ["#hex", "#hex"], "vertical": false}`.
Flags are simplified (no emblems or text).

## Maps

`region`: `world`, `middle_east`, `gulf`, `hormuz`, `levant`, `israel`, `gaza`, `red_sea`, `iran`, `ukraine`, `black_sea`, `russia_ukraine`, `europe`, `eastern_europe`, `usa`, `north_atlantic`, `asia`, or `"bbox": [west, south, east, north]`.
Country names follow Natural Earth: "United States of America" (or USA, US), "United Kingdom" (UK),
"Russia", "Ukraine", "Iran", "Israel", "Lebanon", "Syria", "Saudi Arabia", "United Arab Emirates" (UAE) ...
`"Crimea"`, `"Golan Heights"`, `"West Bank"` and `"Gaza Strip"` are separate shapes; `"Palestinian territories"`
means West Bank + Gaza Strip. Maps follow internationally recognised borders: Crimea takes Ukraine's colour and
the Golan Heights take Syria's, unless coloured on their own. `"occupied": ["Crimea"]` hatches an area;
always say in the narration or a caption who controls it and since when.

## Thumbnails

The thumbnail is a comic cover built from `thumbnail_panel` (any panel spec; otherwise the first
picture panel in the video), with `thumbnail_text` in huge lettering (the `*starred*` word goes on
a yellow starburst in red), `thumbnail_tag` in a yellow caption box, and an optional round
`thumbnail_badge` sticker.
