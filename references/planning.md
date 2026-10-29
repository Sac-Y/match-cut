# Planning: angle, story, cuts, copy, sound

Read almakan.md and look at the two examples first. The plan is what the user approves at checkpoint ①, so it has
to be complete enough to generate from. In straight-through mode it is the last thing the user approves before the
finished film, so nothing may be left to decide later.

## 1. Gather

- Product or brand, its official image(s) and logo, with one official image for every state the plan shows (closed,
  open, each mode or angle; product pages often have a viewer with one image per mode). Never let a model invent
  the product's look. If they are
  missing, plan anyway and list them in the checkpoint ① message as required before stage 2.
- What it is, how it is made, who uses it and when, its one key fact or line (slogan, mnemonic, signature detail).
  If the product is new or unfamiliar, research it online, cite the sources in `plan.md`, and mark every fact you
  could not confirm as an assumption for the user to check (shape, colours, how it opens, which face shows in each
  state, what is on screen).
- Length: default 20 s. Ratio: default 16:9. Copy language: default English unless the user prefers another.
- Credit balance and any model preference (generation.md decides the default tier).

## 2. Pick the angle (no separate confirmation)

Choose the angle that best fits the product and state it in one or two sentences at the top of the plan, with why.
Only offer alternatives if the user asks to rethink. Any angle works if the story holds together.

| Angle | Fits when | Holds together when |
|---|---|---|
| The product's own life (AlMakan's angle) | the making, the craft or the brand's history is the story | every world is a real moment in that life (made, shipped, sold, used, shared) and the matched object already belongs there |
| Pure visual showcase | the product's form, material or motion is the star (a watch, a perfume, a sneaker) | the visual idea escalates to a climax; no shot implies a story it cannot finish (no stranger who never pays off) |
| Many people, one moment | the product is shared by everyone at a time or ritual (lunch, the morning coffee, match day) | the people we meet end up using the product |
| One quality as a metaphor | one quality sells it (crunch, cold, speed, silence) | every world expresses that same quality, so the rhyme is the meaning |

Other angles are fine. Do not mix two: a people story stuffed with props placed only to rhyme is neither a clean
story nor a clean showcase.

## 3. Checks for every cut

Any "no" means redesign the cut. 1–4 are about meaning, 5–8 about what the eye sees.

1. Does it follow the chosen angle's rule, and can the viewer learn that rule within the first few cuts?
2. Does the matched thing have a reason to be in each shot? (In a story: it is there anyway. In a showcase: the
   composition itself is the reason.)
3. If the shot implies a story (a person, a place), does it pay off later, ideally by using the product?
4. Does the chain this cut belongs to say one thing, and is it the same thing the copy says? A true feature that
   only loosely fits the theme is cut, or the copy is changed to carry it; "loosely fits" is a no.
5. Can the viewer see how the two shots connect within one second (shape, position, direction, speed)?
6. **Is every motion physically real?** Something visible causes it (a hand, gravity), the hand uses the grip a
   person really uses for that object (a cover is lifted by its edge between thumb and fingers, not flipped by one
   fingertip), and each object reads as itself in half a second.
7. **Does the motion continue through the cut?** Same direction, similar speed on both sides. If the direction has
   to change (open, then close), cut at a rest state where both objects are still, never mid-motion.
8. **Is each action complete enough to land?** Prefer actions with a clear start and end state (fully open, fully
   closed, set down) over fractions of one motion split across objects; a chain of partial angles reads as weak
   and confusing.

## 4. Structure (a default for 20 s at 150 BPM = 50 beats; adapt it)

| Part | Beats | Job |
|---|---|---|
| Opener | 8 | teach the rule with the product's own shape and motion; the product shot starts on a strong beat |
| Relays | 18 | 3–4 pairs: a gesture in a world (2 beats) → the same gesture on the product (2–3 beats) |
| Breath | 4 | slow; music thins; the theme line word by word; ends by pulling out into the lineup framing |
| Lineup | 9 (7 × 1 + 2) | same framing, one world per beat, hands enter and cut on contact; the last shot lifts the product and whips |
| Hero / payoff | 7 | reached by the whip, never a black slug; the payoff line |
| End card | 4 | logo + name, hard cut on the music's final hit |

`examples/template.json` is this layout with AlMakan's templates; it is a starting point, not a rule.

- **Fewer, longer relays.** A gesture needs about 0.8 s (2 beats) to read in a world shot. One beat is enough only
  in the lineup, where the action is a single touch. Six pairs squeezed into 18 beats left 1-beat world shots
  whose motion never registered; four pairs read.
- **The opener comes from the product.** AlMakan's rolling circle chain suits round subjects. A book-like product
  (a foldable, a laptop, a compact) opens with complete actions on objects of the same size, cut at rest: a card
  opens fully, a passport closes fully, the product opens fully. Fractions of one motion handed from object to
  object (0–45°, 45–90° …) read as weak and confusing.
- **Framings.** AlMakan's templates (A overhead, B tabletop side, C canted lineup) are the default framings. A relay
  pair may use another framing (a pocket close-up, a POV toward the lens) as long as both sides share it; chains of
  three or more keep one framing so the rule is learnable.
- **Camera roll.** Each rolling shot turns from -7.6° to +7.6° and resets at the cut. That is invisible on round
  subjects but breaks a match on lines and rectangles (a hinge, a page): for those, give the run one shared roll
  (`roll_seg`, slower over a longer run) or no roll.

Timeline: 25 fps and 150 BPM, so one beat is exactly 10 frames and every cut lands on a frame (24 fps gives 9.6).
Shots: 2 beats normal, 1 beat in climaxes, 4 beats for breaths. Average ~0.7–0.8 s, like the reference.

## 5. Environments and light

The look is designed for each film from its concept and its worlds; there is no default look. AlMakan's black base
and single pool of top light belong to a restaurant at night. Copied onto a product that lives in daylight, every
world turns into the same dark room.

- Every world is a real place lit by its own source (window, sun, lamp, candle) at a stated time of day. Product
  shots get real places too; a plain studio surface only when the angle is a pure showcase and the plan says why.
- What carries a match cut is the direction of the key light on the subject and the subject's exposure (step under
  10%), not the background. The place, palette and time of day may change at every cut. Choose one key direction
  for the film (e.g. from frame-left) and keep it on every matched subject.
- Let the light follow the story, and write that arc in one line: "folds small, opens big" moves from close
  interiors to open outdoor light; a day in a life runs morning to night; a product's own life follows its making.
- Choose the product's surroundings for its colour and finish the way the brand's own photography does (a white
  phone on pale stone and oak, a dark bottle on light linen). Look at the brand's site.
- Grade, supers and end card follow the same design: text colour readable on what is behind it; the end card's
  colours chosen with the brand (Apple: white card, black logo).
- In the plan: the arc line, and a table with one row per world: place, light source and direction, time of day,
  palette.

## 6. Cut table (the core of the plan)

One row per shot:

| # | Frames / beats | Framing | World and light | Action (cause, grip, direction, from → to state) | Where we cut | How it matches | What it means | Modelled on (AlMakan time) | Sound bridge |
|---|---|---|---|---|---|---|---|---|---|

- "Action": who or what moves the object and how, in physical terms: "right hand, thumb under the right edge of the
  front cover, lifts it and lays it flat to the left: closed → open 180°". Every shot has one; a shot whose action
  cannot be written this way is redesigned.
- "Where we cut": the state and the motion at the cut ("cover at 25°, still closing, fast"; "at rest, fully open").
- "How it matches": the shared shape or motion with numbers: position in % of the frame, size in % of frame height,
  direction, speed, the moment of the cut (e.g. "lid at 45°, hinge at (34%, 64%)").
- "What it means": the meaning link under the chosen angle. In a pure showcase, write which step of the visual
  escalation this is.
- Tolerances: centre within ±3% of frame width, size within ±5%, same direction of motion and speed within about
  25%; brightness step across a match cut under 10%; the incoming shot already moving (or both sides at rest, see
  check 7); clips play at 0.8–1.25× real time; no shot ends in a hold.
- List what must be identical across the product shots (official image material id, wrapper, plate, the key light's
  direction).

## 7. Copy

- Default English. Words appear at two moments only, as in the reference: the theme line (in the breath, or over
  the lineup if the breath has no room) and the payoff at the end, word by word (e.g. EVERY / NOON. / EVERY / HAND.
  → ONE / BIG MAC.). Keep each super to 1–3 words.
- Supers are white caps by default; brand and product names keep their own casing (iPhone), and the brand's font
  is used when supplied. Words may sit on the subject where it is dark negative space (AlMakan writes in the
  pupil); otherwise keep them clear of the product.
- VO is optional. Use it when the product owns a line or a rhythmic list (a mnemonic, the ingredients); then it is
  the metronome, each phrase landing on the shot it names.
- Supers, logos and the end card are rendered in post (render.py); never ask a model to draw them.
- Printing that makes a prop recognisable is part of the prop, not copy: a passport needs PASSPORT on its cover.
  Allow that one word in the still's prompt, quoted exactly, and check it; keep every other surface free of text.

## 8. Sound plan

- Music brief: instrumental, the fixed BPM, a quiet intro, a groove, a build, a chorus, and the song's own ending
  with one clear final hit that rings out. Three candidates; the user picks at checkpoint ②.
- Foley: one short sound per visible action (tick, press, sizzle, pour, land, whoosh), placed on the action frame.
- The final hit lands on the end-card cut. The song's ending runs uncut into that hit.

## 9. Mistakes already made once (do not repeat)

- Props placed only to rhyme (coins → pickles, confetti → lettuce): the cut reads as forced.
- A person introduced and never paid off (a builder sets down a hard hat but never eats the burger).
- A black slug and silence before the hero in a 20 s spot: it reads as the film breaking. Use a whip and keep
  the music going.
- Music joins between different keys or energy levels (a quiet bridge before a loud final bar): it sounds
  "weak then strong, out of tune". Keep the song's own ending contiguous.
- Ducking the whole bed under the last line on a full band: the music falls away. Duck the voice band only.
- Generating video before the stills are aligned: framing mismatches show up after the money is spent.
- Model-rendered text or logos.
- AlMakan's black base and top pool used for every shot of an iPhone: ten worlds that looked like one dark room.
  Design environments and light per world (§5).
- A reference image showing two views side by side (a phone's back next to its front) was read as one object: the
  model drew a phone folded backwards with the cameras and the screen on one side. For a product with several faces
  or states (foldables, laptops, compacts, packaging), the plan states for every product shot which face is visible,
  and each still uses the official image that shows that state.
- Prompts that named things meant to be absent: "the cameras are hidden underneath" drew the cameras, and a
  negative mentioning the phone's logo put phones into world shots. Describe only what is visible.
- Motion with no visible cause or an impossible grip: one fingertip "flipping" a cover, pages falling by
  themselves, fingertips draped over the top of a screen with a ringed finger across the picture. Write the grip in
  the cut table and in the prompt, and review hands at full size.
- A direction reversed across a cut: a paint-box lid lifting, then the phone half lowering. Check the direction in
  the generated clips, not only in the stills.
- An opener handing fractions of one motion from object to object (0–45°, 45–90°, 90–135°, 135–180°): the angle
  even went backwards at one cut, and no single action landed. Complete actions, cut at rest, hit harder.
- A blanket "no text" rule applied to a prop whose identity is its printing: the passport read as a notebook.
- Official product photos are posed: the "open" photos showed the phone at about 170° in a slight V, the end frame
  copied that, and the phone never lay flat. Official images fix the product's look, not its pose; state end states
  ("flat at 180°, straight edges") in words and check them in the still.
- Six relay pairs in 18 beats: 1-beat world shots, 1.5–2.5× speed-ups, shots ending in a hold. The film read as
  "not smooth". Fewer pairs, real-time clips, cut in motion.
- A visible product defect shipped as a "known deviation" (a phone stopping short of flat). It cost less than 100
  credits to fix. Fix product and hand defects before delivery.

## 10. What to show at checkpoint ①

In the user's language; the message carries a condensed cut table (one line per cut or pair) and `plan.md`
holds the full one:
1. Angle and why (1–2 sentences), the concept in one line.
2. Copy (supers, optional VO), English by default.
3. The look: the light arc in one line and the environments-and-light table.
4. The cut table.
5. Music and sound plan.
6. Tools and models per job and what each bills (stills: Codex `image_gen` on the user's plan, or Renoise
   credits; video, music, VO, foley: Renoise credits), resolution and quotes for both video tiers
   (generation.md), the default chosen, the spending caps.
7. What the user must supply or confirm: official images, logo, unconfirmed facts, rights to any borrowed line.
8. The working-mode question (SKILL.md): straight through, approving the whole-film cap now, or checkpoint by
   checkpoint, approving the stage-2 cap now and the animatic and video quote at checkpoint ②.

Save it as `plan.md` in the project folder, and write the matching first `montage.json`: stills as sources
(`render.py --draft` shows a missing still as a labelled placeholder, so the timing can be checked before any
still exists), the planned supers and foley frames, `music.segments` kept as placeholders until a track is
picked, and no `vo` block if the plan has no VO.
