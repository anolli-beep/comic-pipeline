# Comic pipeline

Turns plan files written in the Claude chat into finished **comic-book style** YouTube videos:
AI narration, animated comic pages (panels, caption boxes, speech bubbles, sound effects, maps,
charts and characters, all drawn, no photos), a comic-cover thumbnail, three vertical short clips,
captions and an upload sheet. It is a separate repo from `video-pipeline`, so the history channel is
never affected.

---

## Part A: one-time setup (about 20 minutes)

1. **Create the repo.** On GitHub: **+ → New repository**, name it `comic-pipeline`, choose
   **Public** (unlimited free Actions minutes; private repos get 2,000 minutes a month), tick nothing
   else, **Create repository**.
2. **Upload the files.** On the new repo page click **uploading an existing file**. Unzip
   `comic-pipeline.zip` on your computer, open the `comic-pipeline` folder, select everything inside it
   (including the `.github` folder: on a Mac press Cmd+Shift+. to show hidden folders) and drag it in.
   **Commit changes**. Check that `.github/workflows/render.yml` is there; if not, create it with
   **Add file → Create new file**, type `.github/workflows/render.yml` as the name and paste the file's text.
3. **Set the channel.** Open `channels/comic.yaml`, click the pencil, and replace
   `REPLACE_WITH_CHANNEL_NAME` (your channel's name) and `REPLACE_WITH_VOICE_ID` (an ElevenLabs voice
   ID: elevenlabs.io → Voices → the voice → copy ID). Pick a voice you don't use on other channels.
   **Commit changes**.
4. **Add the ElevenLabs key.** **Settings → Secrets and variables → Actions → New repository secret**.
   Name: `ELEVENLABS_API_KEY`. Value: your key. Never paste the key anywhere else.
5. **Allow the workflow to save.** **Settings → Actions → General → Workflow permissions →
   Read and write permissions → Save**.
6. **Email when a video is ready (optional).** Click **Watch → Custom → Issues** at the top of the repo.

## Part B: making a video

1. In the Claude chat for this channel, ask for a plan (e.g. "comic video plan: Israel's coalition talks").
2. Upload the `.json` file to the `plans` folder (**Add file → Upload files → Commit**).
3. Rendering starts on its own and takes about 25-40 minutes. A **"[Comic] Ready to upload"** issue
   appears with the download link.
4. Download, unzip, open `UPLOAD.txt`, watch the video through, then upload and schedule it.

If a run fails at **Check the plan**, nothing was spent: paste the error into the chat for a fixed
plan. To run again after a fix, use **Actions → Render comic videos from plans → Run workflow**
(Re-run uses the old code).

## Settings you might change

- `config.yaml`: picture size, frame rate, burned-in subtitles (off by default), clips.
- `channels/comic.yaml`: name, voice, colours (accent red, caption yellow, paper), publish times,
  description wording. More channels: copy the file under a new name, e.g. `channels/history-comic.yaml`,
  and set `"channel": "history-comic"` in plans.
- `assets/`: put a royalty-free `music-comic.mp3` here for background music (optional).
- `pronunciations.yaml`: how the narrator says tricky names.

## What's in the folder

- `main.py`: checks a plan and makes the video
- `pipeline/pages.py`: page layouts, panel timing, the camera
- `pipeline/art.py`: the panel art library (people, maps, buildings, charts, jets, ships ...)
- `pipeline/kit.py`: drawing kit (ink, halftone, lettering, bubbles, people)
- `pipeline/maps.py` and `assets/maps/`: comic maps from Natural Earth outlines
- `pipeline/flags.py`: simplified flags
- `pipeline/render.py`: draws the frames on all CPU cores and adds the narration
- `pipeline/packaging.py`: comic-cover thumbnail and description
- `pipeline/clips.py`: vertical short clips
- `pipeline/voice.py`: ElevenLabs narration
- `plans/README.md`: everything a plan can contain
- `assets/fonts/`: Bangers, Comic Neue, Instrument Sans (all free, OFL licence)
