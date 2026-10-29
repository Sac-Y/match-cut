# Generation

Video, music, VO and foley always run on Renoise. Stills run on Renoise too, except on Codex, where they come from
the built-in `image_gen` tool (`stills-codex.md`; the stage-2 rules below still apply). Load Renoise's
`model-routing` skill before the first estimate if it is installed; live `list_models` limits win over anything
here. Nothing is generated without the user's go-ahead on a quote. In checkpoint mode, checkpoint ① covers stills
and music candidates and checkpoint ② covers video, VO and foley. In straight-through mode, checkpoint ① approves
the whole-film cap once.

## Tools, in order

1. `get_account`: balance.
2. `upload_files` (or `request_upload`) for the official product image(s) and logo once the user supplies them
   (at the latest before stage 2). Note each material id in `plan.md`; every product still references them.
3. `estimate_cost` with the exact tasks (it returns the tasks to submit). Leave nothing to defaults that matter:
   set `resolution`, `duration`, and `audioGeneration: false` for silent video; estimates otherwise assume the
   lowest resolution. It takes at most 10 tasks per call: for the plan-level quote, price one task per
   (model, resolution, duration) and multiply; submit-ready estimates are made per batch of 10 at each checkpoint.
   At checkpoint ① no stills exist yet, so price video tasks without frames (same model, duration and resolution)
   and say they are re-estimated with the real frames at checkpoint ②.
4. After approval: `create_tasks` with the estimated tasks (give each a `label` and an `idempotencyKey`),
   `wait_tasks`, then `download_results` into the project's `dl/` folder as `renoise-<task>.<ext>`.
5. Keep `task-map.json`: shot id → task id → file, prompt, and whether it was a retry.
6. Delivery: upload the final mp4 and `show_result` it.

## Default models

| Job | Default | Notes |
|---|---|---|
| Key-frame stills | `seedream-5-0-pro`, 2k, 16:9 (on Codex: built-in `image_gen`) | product shots always reference the official image |
| Video, comfortable balance | `seedance-2.5-byteplus`, 1080p | frame mode (first / last frame), min 4 s per clip |
| Video, tighter balance | `wan3.0-video`, 1080p | frame mode, 2 s clips are enough for 1–2 beat shots and cost least |
| Video, balance too low for either | `wan3.0-video` 720p + `upscale-video-topaz-starlight-2.5` to 1080p on the picked frames, or fewer shots | say which shots get cut |
| Music | `lyria-pro`, 3 candidates | instrumental, fixed BPM (planning.md §8) |
| VO (only if the plan has VO) | `seed-audio-1.0`, 2 voices | dry studio read |
| Foley | `eleven-sfx-v2`, 1–3 s each | billed per second |

These defaults are the user's standing preference, so they win over generic routing advice and over `list_models`
hints ("use Wan only when asked"); live limits (durations, roles, resolutions) still apply.

How the video tier is chosen (state the choice and both quotes at checkpoint ①):
1. Estimate the whole plan twice, once with each video model. "Total" always means the whole plan: stills, music,
   video, VO and foley.
2. If the balance is at least twice the Seedance total, default to Seedance 2.5. Otherwise, if it covers the Wan
   total plus a 20% reserve, default to Wan 3.0. Otherwise offer the 720p + upscale route or a shorter cut.
3. In the Wan tier, put the hero shot on Seedance when the total with it stays under 40% of the balance; say so.
4. A model the user names, or a tier they pick, always wins. Never switch tiers later without asking.
5. If `get_account` shows a promotion or free channel, mention it; use it only if it meets the plan's resolution
   or the user opts in.

Budget rules:
- Each stage's cap = its estimate + a 30% retry reserve (at most one retry per task).
- Checkpoint mode: checkpoint ① approves the stage-2 cap and shows the whole-film estimate for information;
  checkpoint ② approves the stage-3 cap. Straight-through mode: checkpoint ① approves one whole-film cap (the
  whole estimate + 30%). Either way, stop and ask before anything would exceed a cap.
- Leave 15–20% of the balance untouched.
- On Codex the stills are not in the Renoise quote (`stills-codex.md`).

## Stage 2: stills, music candidates, animatic (checkpoint ②)

Stills come first because alignment is cheap to fix in a still and expensive in video.

- **Which stills.** One first frame per generated shot. Add a last frame only where the shot must land on a
  framing: the outgoing side of a relay that has to end in the matched position, the hero landing. Shots that must
  share framing (a relay pair, the lineup) are made from one master still by editing, not by generating twice.
  A 20 s plan usually needs 30–45 stills.
- **Lineup.** One master still on template C with the product placed exactly; each other world is an edit of it
  that changes only the surface and room ("Same photograph as @task:<master>: keep the camera, lens and framing,
  and keep the product at exactly the same position and size, unchanged. Change only the surface and the room: …").
- **Product.** Describe in each product still only what the camera sees in that state ("seen from above, the open
  phone is one continuous glass screen across both halves"). Do not name hidden parts, not even to say they are
  hidden: "the cameras face down" put the cameras on screen. Each product still references the official image(s)
  showing that state ("The product must match @material:<id>"). Never use an image with two views side by side
  (front next to back) as a reference: the model fuses them into one impossible object. If a state still comes out
  wrong after one corrected prompt, stop rewording and find the official image of exactly that state (a
  foldable's seated L stayed wrong through two text fixes and came right only with the maker's own seated photo as
  the reference). An edit keeps the old shape: when the shape itself is wrong, generate the still fresh.
- **Official images fix the look, not the pose.** Marketing photos are posed: the "open" photos of a foldable show
  it at about 170° in a slight V, and a still that referenced them never lay flat. Write the end state in words
  ("lies completely flat at 180°; its top and bottom edges run straight across the hinge"); when an official photo
  shows another pose, reference only images that show the look without the pose (a hinge close-up), and check the
  state in the still.
- **Hands.** Write the grip in every prompt with a hand: which hand, where the thumb and fingers are, what they are
  about to do ("right hand holds the lid by its right side edge near the top corner, thumb on the inner face,
  fingers behind it"). Default: no rings or jewellery. A grip in a still carries into the video, so fix it in the
  still.
- **Edits re-frame.** An edit may zoom, re-centre, or refuse to change an angle (a book cover stayed at 25° through
  two edits asking for 70°). Measure position and size after every edit; align by cropping with `align.py` (crop
  the wider frames to match the tighter one) rather than regenerating. If two edits will not change an angle,
  generate that state fresh, or make it the master and edit the others from it.
- **Prompt modules** (fill in per project, keep them identical across shots):
  - `{LOOK}` built per world from the plan's environments-and-light table (planning.md §5): "Photoreal premium
    commercial photograph on a cinema camera, natural lens rendering, shallow depth of field. A real place in its
    own natural light: <place; light source and direction; time of day>. The surroundings are naturally exposed and
    readable. <grade words from the plan, e.g. clean true-to-life colour, gentle contrast>, crisp micro-texture,
    subtle film grain. Only hands and forearms may appear; no faces." The camera and grade words stay identical
    across shots; the place and its light change per world. Never fall back to a black void or a spotlight unless
    the plan chose that look. (Drop the last sentence when the angle needs people.)
  - `{A}` "True top-down camera pointing straight down at 90 degrees, locked off. The main round subject is centred
    exactly at the frame centre and its diameter equals 55% of the frame height."
  - `{B}` "Low camera at counter height, locked off; the counter edge runs level across the frame at 62% of its
    height; hands enter from the top or side."
  - `{C}` "Camera tilted 12 degrees to the right, about 15 degrees above the table; the table forms a trapezoid in
    the lower half; the product's base centre sits at 50% of the width and 62% of the height and the product is
    30% of the frame height tall."
  - `{NEG}` "No readable text, letters or numbers anywhere, no logos, no watermarks, no subtitles. No extra objects,
    no morphing, no extra or missing fingers, no duplicated items." Keep the product out of it: a world shot's
    negative that mentioned "the phone's logo" put phones into four world shots.
  - Positions and sizes in prompts are always given in % of the frame, the same numbers as the cut table.
- **Style reference (optional).** If one image shows the planned look (usually the brand's own photography),
  upload it once and pass it as a `reference_image` ("in the lighting and colour of @material:<id>"). A reference
  film only fits Seedance reference mode, which cannot be combined with frame mode, so it is rarely useful.
- **Breath still.** If the breath pulls out into the lineup (`pull`), compose it for that: the product's centre at
  the `c_src` point, and its size in the macro = its lineup size ÷ `k_end` (e.g. lineup 30% of frame height,
  k_end 0.5 → 60% in the macro).
- **World swaps.** An edit that moves a matched shot into another world keeps the camera, the object's position,
  size and angle, and the direction of the light on it; it changes the object, the place and the place's light.
- **Check.** Review every still with `review.md` before the next wave edits it: identity, product and its state,
  hands, physics, framing against its cut partner, light. Regenerate a failing still once with a corrected prompt;
  if framing is the only problem, crop with `align.py`; if it still fails, fix it in post with `geo`, or redesign
  the cut.
- **Music.** Three `lyria-pro` candidates from one brief: "Instrumental … at exactly 150 BPM, 4/4 … Structure:
  quiet intro, groove, build, a full chorus, then the song's own ending: the band drops out for a moment and comes
  back for one big final hit that rings out. About 2 minutes." Run `music.py analyze` on each, pick sections,
  cut each candidate with `music.py cut` so the user hears all three against the animatic.
- **Animatic.** `render.py --draft` with stills as sources (camera rolls, pulls and whips already work on stills),
  `assemble.py --draft`. Show it with the music candidates at checkpoint ②, together with the video quote.

## Stage 3: video, VO, foley

- **Frame mode.** Each video task gets its approved stills as `first_frame` (and `last_frame` when the shot must
  land on a framing). Omit `ratio` in frame mode. No other references can be mixed in.
- **Prompt pattern (Wan / Seedance in frame mode):** "Locked-off camera, no camera movement. <the one action, with
  its timing in seconds: what starts at 0.2 s, what touches at 0.8 s>. <what must not move>. No audio."
  Camera roll, pulls, zooms and whips are added in post, never asked of the model.
- **Length.** Generate the model's shortest clip that covers the action (Wan 2–3 s, Seedance 4 s) and pick frames
  in post; the action should peak around the middle so the cut can land mid-action.
- **Timing with locked ends.** With both first and last frames locked, models spread the action over the whole
  clip, so it plays slowly and the edit is tempted to speed it up. Give the action's timing in seconds ("lies flat
  at 1.0 s, then rests"), or lock only the first frame when the action must be quick and its end is not a match
  point. Plan for 0.8–1.25× in the edit.
- **Model test.** When it is unclear which video model suits the actions (quick hand gestures, landing on an exact
  end frame), generate one representative shot on both and compare speed, landing and hands before committing
  the rest. On short, quick actions with locked ends, Wan 3.0 landed faster and more exactly than Seedance 2.5 at a
  quarter of the price; Seedance is still the choice for slow, long or reference-heavy shots.
- **Hero.** Usually the one shot worth Seedance; a slow push-in or a reveal, 4–5 s.
- **VO.** Seed Audio: "Voiceover for a premium commercial, recorded close to a studio microphone, completely dry:
  no music, no sound effects, no room echo. Speaker: <voice>. Line 1, crisp and rhythmic …: "<text>". Then one
  second of silence. Line 2, slower and lower …: "<payoff>"." Two voices (e.g. warm baritone, warm alto).
- **Foley.** One prompt per action: source, action, texture, space ("Heavy steel press pushed down onto patties,
  sharp burst of steam hiss"). 1–3 s each. If one comes back as noise, derive it from another in post
  (`sfx_derived` pitch shift) instead of paying again.
- **Retries.** At most one per task, same model, corrected prompt. Log it in `task-map.json`.
- **Product shots: frame mode or the official image.** Frame and reference roles cannot be mixed in one task. For
  a product shot whose still was not edited from an official photo, also run a reference-mode variant: the approved
  still named as the first frame plus the official photo of that state ("@<still> is the first frame of the video:
  start exactly from this image … The phone must look exactly like the product in @material:<official>"). Wan 3.0
  kept the still's framing in reference mode. Pick per shot; neither mode always wins (on a foldable, reference
  mode fixed a phone that flipped over and gave a cleaner opening, but added a third panel to another shot and an
  interface to a screen). Stills edited from an official photo (the lineup, the hero) need only frame mode.
- **Screens.** Video models add punch-hole camera dots and interfaces to blank screens. Name the photograph that
  fills the screen, and remove dots in post with `undot.py` rather than paying for a retry (`--fixed` when the
  screen is still and the dot sits in one place, which also catches the dim frames the detector misses).
- **Frame rates.** Wan returns 30 fps (60 frames for 2 s), Seedance 24 fps; `picks` convert to the timeline.
- **Low-resolution sources.** Upscale with Topaz Starlight (no prompt) instead of regenerating.
