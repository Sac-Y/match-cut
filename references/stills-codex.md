# Stills on Codex: the built-in `image_gen` tool

On Codex the key-frame stills come from the built-in `image_gen` tool (GPT Image). It is billed to the user's
ChatGPT / Codex plan, not to Renoise credits; image turns use the plan's limits several times faster than ordinary
turns, so say so in the plan. Video, music, VO and foley still run on Renoise, so every approved still is uploaded
to Renoise before stage 3.

Everything in `generation.md` stage 2 about which stills to make, the prompt modules and the checks applies here;
this page covers only what differs.

## How the tool works

- **One call per still.** Different shots are separate calls, not `n` variants of one prompt.
- **Edits and references need the image in the conversation.** The tool edits only images visible in the
  conversation: load each local file with `view_image` first (the master still, the official product image), then
  give every image its role in the prompt ("Edit the first image, the master still … The product must match the
  second image, Apple's official photo of the open state").
- **Where files land.** Results are saved under `$CODEX_HOME/generated_images/` (usually
  `~/.codex/generated_images/`). Copy each approved still into the project's `stills/` named by shot id
  (`stills/05a.png`), keep earlier tries as `05a-v1.png`, and never leave a project still only in the default
  folder.
- **No size, path or mask arguments in built-in mode.** Ask for "a 16:9 landscape photograph" in the prompt. If a
  file comes back in another ratio, crop it to 16:9 with `scripts/align.py`, choosing the window so the subject
  keeps its planned position. Never stretch.
- **The CLI fallback** (`scripts/image_gen.py` in Codex's own `imagegen` skill) needs an OpenAI API key; use it only
  if the user asks for it.

## Prompting

- GPT Image follows long, structured briefs. Use labelled lines: DELIVERABLE (16:9 photograph), SCENE (the world
  and its light from the plan), SUBJECT, COMPOSITION (positions and sizes in % of the frame, the same numbers as
  the cut table), HANDS (which hand, where the thumb and fingers are, what they are about to do), LIGHT, and for
  edits PRESERVE / CHANGE ONLY. End with AVOID (the `{NEG}` module).
- Quote any word that must appear on a prop exactly (`"PASSPORT"`); everything else stays free of text.
- Edits: "Change only X; keep everything else identical: camera, framing, the object's position and size, the
  light." Then measure: edits can still re-frame.

## Into Renoise

- Upload every approved still with `upload_files` (path, size, sha256), record its material id in
  `task-map.json` under `still_materials`, and use `material:<id>` as `first_frame` / `last_frame` in video tasks.
- Stills at least 1280 px wide work as video frames; the video model renders at the requested resolution.
- Product shots still need the official product images: upload them to Renoise too when a video task uses
  reference mode (`generation.md`, stage 3).

## Budget

The Renoise quote at checkpoint ① covers music, video, VO and foley; stills cost no Renoise credits. State the
number of stills (usually 30–45 for a 20 s film, plus retries) so the user can judge the load on their plan.
