# Post: config, edit, sound, checks, delivery

All post is code, driven by one `montage.json` per project (start from `examples/template.json`). Paths in it are
relative to the config file; `"@name"` looks up `sources`.

## Project layout

```
<project>/
├── plan.md            the approved plan (cut table, copy, models, quotes)
├── task-map.json      shot → task id → file
├── montage.json
├── assets/            official product image(s), logo
├── stills/            approved key frames (stage 2)
├── dl/                downloaded generations: renoise-<task>.mp4 / .mp3 / .png
├── build/             renders, music cue, mix (scratch)
└── output/vN/         deliverables + README.md (what changed in this version)
```

## Commands

`python` below is the venv from SKILL.md step 0 (Python 3.11 with `scripts/requirements.txt`; an Anaconda Python
with numpy 2 breaks librosa). `S=<skill>/scripts`.

| Stage | Command |
|---|---|
| pick frames from a clip (or read a whole film) | `python $S/qc.py sheet dl/renoise-123.mp4 build/123.jpg [first last step]` |
| full-size crops for the realism review | `python $S/qc.py look dl/renoise-123.mp4 build/123-hands.jpg 12,24,36 x0,y0,x1,y1` (the box at full resolution, at each listed frame; also takes a still) |
| line up a still with its cut partner | `python $S/align.py dl/renoise-456.png stills/03b.png L T Z` (window left/top in % of the source, zoom; output x = (x - L) × Z) |
| remove model-made camera dots | `python $S/undot.py dl/renoise-123.mp4 dl/renoise-123-clean.mp4 x0,y0,x1,y1` (small dark ellipses on a bright screen inside the box are inpainted per frame; always give the box). On a still screen: `--fixed cx,cy,r,from` fills one fixed circle from frame `from` on, dim frames included |
| check a cut pair of stills | `python $S/qc.py onion stills/05.png stills/06.png build/onion-05-06.jpg` |
| line up the product | `python $S/qc.py match stills/18.png x0,y0,x1,y1 stills/19.png dl/renoise-456.mp4:12` |
| read a music track | `python $S/music.py analyze dl/renoise-789.mp3 --bpm 150` |
| cut the music | `python $S/music.py cut montage.json` |
| animatic | `JOBS=6 python $S/render.py montage.json build/animatic --draft` then `python $S/assemble.py montage.json build/animatic --draft` (missing stills render as labelled placeholders) |
| full render | `JOBS=6 python $S/render.py montage.json build/v1 [shot ids]` |
| cut sheet | `python $S/qc.py cuts montage.json build/v1 build/v1/cuts.jpg` |
| mix | `python $S/mix.py montage.json` |
| deliver | `python $S/assemble.py montage.json build/v1` |

## montage.json

| Key | Meaning |
|---|---|
| `name` | file name stem of the deliverables |
| `timeline` | `fps` (25), `bpm` (150), `frames` (total), `size` ([1920, 1080]) |
| `sources` | aliases: `{"v05": "dl/renoise-373618.mp4"}` |
| `look.roll` | `dps` camera roll speed (20°/s), `max_frames` longest rolling shot the cover zoom must handle (default 2 beats) |
| `look.grades` | named looks: `shadow` and `highlight` RGB tints, `sat` |
| `look.film` | `toe` (lifted blacks), `halation`, `grain` |
| `text` | super style: `font`, `style` (a face in a .ttc), or `variation` for a variable font (`SFNS.ttf` with `"Semibold"` = SF Pro), `size` (fraction of height), `tracking`, `color` |
| `supers` | `{text, start, end, x, y, style}` (frames; x, y = text centre as fractions of width and height, x defaults to 0.5; `style` overrides `text` for this super, e.g. `{"color": [29, 29, 31], "shadow_alpha": 0}` on a bright background) or `{png, start, end}` |
| `music` | `track`, `phase` (from analyze), `segments` (`"bar:beat:nbeats"`), `out` |
| `mix` | see "Sound" below |
| `deliver` | `dir`, `crf` |
| `shots` | in order, tiling the timeline exactly |

Shot fields:

| Field | Meaning |
|---|---|
| `id`, `name`, `start`, `end` | frames, end exclusive |
| `type` | `clip` (default; `src` may be a video or a still), `card`, `black`, `placeholder` |
| `src` | path or `@alias` |
| `picks` | source frame per timeline frame: `{"from": 12}` real time from frame 12, `{"from": 0, "speed": 0.83}`, `{"range": [a, b]}`, `{"linspace": [a, b]}`, `{"list": [...]}`, any with `"offset": k` |
| `grade` | a name from `look.grades`; `gain`, `gamma`, `sat`, `knee` per shot (lower `knee` to hold bright paper) |
| `roll` | true: template-A clockwise camera roll with the constant cover zoom |
| `roll_seg` | `[first frame, frames]`: consecutive shots on one framing share one continuous roll |
| `geo` | `[[sx, sy], [dx, dy], scale]`: move source point (canvas px) to dst at scale, e.g. to match the product's place and size to the shot it cuts with. Edges outside the source are smeared, so keep `sx - dx/scale ≥ 0` (and the same for the other edges): raise the scale a little rather than expose an edge |
| `pull` | `{c_src, c_dst, k_end, i0, mask}`: from frame i0 the shot shrinks about c_src into a pool of light at c_dst, k_end of its size, so a macro lands exactly on the next framing; `mask` = pool radii [rx, ry] in canvas px (default [820, 640]). Compose the macro with the product at c_src and its size = lineup size ÷ k_end |
| `whip_out` / `whip_in` | per-frame `[scale, y offset px, vertical blur px]` for the last / first frames: a camera whip between two shots. Add `x offset px, horizontal blur px` (5 values) for a sideways whip pan, e.g. a cut to the reverse angle |
| `step_ok` | true: the brightness step into this shot is intended (lineup worlds) |
| card: `bg` (RGB), `logo`, `logo_h`, `logo_y`, `text`, `text_color` (RGB), `text_y`, `text_size`, `font` (`{"font": path, "style": "Bold"}`), `push`, `grain`, or `image` (a finished card) | end card built in code |

## Edit rules

- Cut while the action is half done; the incoming shot is already moving. Use `qc.py sheet` to choose the frames.
  Where a direction change forces it, cut at rest: both sides still, same state, same place.
- Picks follow the motion: start where the motion starts (models often hold the first frames), end before it
  settles, play at 0.8–1.25× real time (`linspace` makes the speed explicit: source frames ÷ timeline frames ×
  25 ÷ the source fps). Never fill a slot with a hold; shorten the slot or re-pick instead. Avoid a clip's last
  2–3 frames, which often jump into the locked end frame.
- Compare the frames on both sides of every relay cut: the angle and direction must continue (a cover at 25°
  closing meets a phone at 25° closing, not one at 15° and one at 25°).
- Template A shots roll clockwise at 20°/s with one constant zoom (1.226 for 2-beat shots) so corners never show.
  Each rolling shot runs -7.6° → +7.6° and resets at the cut: fine for round subjects. For lines and rectangles,
  or the same framing back to back, use `roll_seg` over the run: one continuous roll spreading the same ±7.6° over
  the whole run (so it turns slower), with no jump at the cuts.
- Line up the shared shape across each cut with `geo` (measure with `qc.py match` at the frames the shot actually uses: generated clips drift and zoom a little even when told to stay locked off): centre within 3% of the width,
  size within 5%.
- Macro → lineup: `pull` the macro out into the next shot's framing over its last half-second, inside a pool of
  light, so the product's size and place equal the next shot's.
- Lineup → hero in a short spot: a camera whip (`whip_out` on the last lineup shot, `whip_in` on the hero), never a
  black slug. The whip lands with a musical event (band re-entry, downbeat) and a landing sound.
- Brightness step across a match cut under 10% (`qc.py cuts` flags it); lineups may alternate warm and cool
  worlds on purpose (`step_ok`).
- Supers: caps, word by word, white by default and dark (per-super `style`) where the background is bright; brand names keep their casing; the brand font if supplied (`text.font`). Keep
  them clear of the product unless the subject is dark negative space (move the payoff to the top if the hero
  fills the lower half). End card: hard cut on the final hit, 2% push over its length.
- Every frame passes through the same grade, toe, halation and grain, so all sources sit in one camera.

## Sound

`mix` keys:

| Key | Meaning |
|---|---|
| `out`, `music` | output folder; the cut cue |
| `vo` | `file`, `pre`, `post`, `phrases`: `{text, in, out, frame, gain, level, limit}`: file seconds [in, out) start on `frame`; `level` is a dB curve in file seconds for one weak word; `limit` keeps it under the louder lines |
| `sfx_files` | key → file |
| `sfx_derived` | key → `{from, pitch, reverse}` (reverse a whoosh for a riser, pitch a sound down instead of re-generating) |
| `sfx` | `[key, in, len, hit, frame, dB]`: file time `hit` lands on `frame` |
| `duck` | `{type: broadband, db, from, to}` dips the whole bed while the voice speaks; `{type: voiceband, db, other_db, from, to}` dips only 250 Hz–5 kHz, held over a range |
| `swell` | `{into, len, body_after}`: the final hit reversed, rising into it, its pitched layer only after the voice ends |
| `master` | `lufs` (-14), `ceiling_db` (-1.6, leaves room for AAC overshoot), `true_peak_db` (-1.5), `dip_lu` (8) |

Rules:
- Music: pick sections on the bar grid with `music.py analyze`; segments may use fractional beats. Keep the song's
  own ending contiguous from the hero to the final hit, and put the hit on the end-card cut. Fill a gap with the
  song's own continuation rather than silence. Listen to every join `music.py cut` flags; move it unless the jump is
  the song's own (a band re-entry).
- VO phrases land on the frames of the shots they name. Level single weak words with `level`, not the whole line.
- Foley on the action frame (`hit` = the sound's onset); keep it under the music except the landings.
- Ducking: broadband about -8 dB for lines over sparse music; voiceband (-10 dB mids, -1.5 dB elsewhere, slow
  ramps) for lines over a full band, so the music keeps its weight.
- If the song stops just before its final hit, fill the stop with `swell`, not silence.
- Report targets: integrated -14 LUFS ±0.5, true peak ≤ -1.5 dBTP, no `loudness_dips`, every VO phrase at least
  5 dB above the music in the voice band.

## Checks before checkpoint ③

1. `qc.py cuts`: every match cut reads as one motion; no unintended brightness flags.
2. Watch the whole film at full speed twice: once for picture, once listening only. An agent that cannot play
   video reads it as a `qc.py sheet` grid every 3–5 frames, section by section, plus `qc.py look` crops of hands
   and product (`review.md`, film section).
3. `mix-report.json` meets the targets above.
4. Product looks match the official image in every product shot; no model-made text or logos anywhere.
5. The deliverable plays: 1920×1080, 25 fps, the right length, AAC audio; master is ProRes 422 HQ.

## Delivery

`assemble.py` writes the ProRes master, the H.264 mp4 and the stems. Write `output/vN/README.md` (files, length,
loudness, what changed since the last version and why, spend), upload the mp4 to Renoise and `show_result` it.
Keep earlier versions; do not overwrite them. "Known deviations" in the README never include the product or a hand
(`review.md`).
