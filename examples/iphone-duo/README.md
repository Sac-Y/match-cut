# Example: iPhone Duo, "Open Up" (20 s)

`preview.mp4` is a 720p copy of the delivered film (v3); `montage.json` is its edit config as built (its `dl/`
sources are the project's downloads and are not shipped). An unofficial spec film made to test this skill; not
affiliated with or endorsed by Apple.

## The film

- **Product:** a book-style foldable phone, passport-sized when closed.
- **Angle:** one quality as a metaphor, "folds small, opens big": things that fold and open in many worlds, light
  moving from close interiors to open outdoor light.
- **Format:** 20 s, 1920×1080, 25 fps, 150 BPM (10 frames a beat), 500 frames.

| Frames | Part | What happens |
|---|---|---|
| 0–80 | Opener | Top-down, one hinge line, one size: a greeting card opens fully → a passport is closed fully by the same hand → the closed Duo is opened flat and its screen wakes. Every cut at rest |
| 80–260 | Four relay pairs | a palm presses a novel shut → presses the Duo shut; a map pushed into a coat pocket → the Duo into a jacket pocket; a topo map's last panel stands up → the Duo opens in two hands; a paint-box lid lifted by its corner → the Duo's upper half tilted back by the same grip |
| 260–300 | Breath | the Duo standing in a dark window; FOLDS / SMALL. / OPENS / BIG. word by word |
| 300–390 | Lineup | eight worlds, the phone in the same place; a fingertip touches the screen on each beat; the last one lifts it and whips |
| 390–460 | Hero | the phone lands, opens flat on a stone terrace, the screen wakes; OPEN UP. |
| 460–500 | End card | logo and name, hard cut on the music's final hit |

**Made with:** Seedream 5.0 Pro stills, Wan 3.0 1080p video (hero on Seedance 2.5), Lyria 3 Pro music,
ElevenLabs foley. Spend: v1 about 2,200 credits, v2 762, v3 198.

## What the three versions taught

| Version | Sent back for | Cause | Fix (now a rule in the skill) |
|---|---|---|---|
| v1 | the passport did not read as a passport | a blanket "no text" rule removed its printing | identity printing allowed on props (planning.md §7) |
| v1 | one fingertip "flipping" a cover; pages falling by themselves | actions planned as "what moves", never "who moves it, how" | an action column in the cut table and check 6 (planning.md) |
| v1 | the opener confused: 45° of the motion per object, the angle going backwards at one cut | fractions of one motion handed between objects | complete actions, cut at rest (check 8, §4) |
| v1 | a lid lifting, then the phone half lowering | direction not compared across the cut | check 7; review the clips, not only the stills (review.md) |
| v1 | "not smooth" | six pairs in 18 beats, 1.5–2.5× speed-ups, world shots that barely moved, holds at shot ends | four pairs, real time 0.8–1.25×, cut in motion (§4, post.md) |
| v2 | the phone stopped short of flat | the official "open" photos are posed at about 170°, and the end frame copied them | official images fix the look, not the pose (generation.md) |
| v2 | unnatural hands in two shots | the stills drew the grip that way and the review looked at small contact sheets | write the grip in prompts; full-size hand crops with `qc.py look` (review.md) |
| v2 | (shipped as a "known deviation") | a fixable product defect was listed instead of fixed | product and hand defects are fixed before delivery |

Tools that came out of it: `align.py` (Seedream re-framed the closed passport 1.37× larger and centred, so the open
frames were cropped to match instead of regenerated), `undot.py --fixed` (a camera dot on a dim screen the
detector missed), `qc.py look`.
