# Review: stills, clips, cuts, film

`qc.py` measures alignment, size and brightness. This page covers what those numbers cannot show: whether the
picture is physically believable. Every user-sent-back problem in the examples was of this kind (an impossible
grip, a motion with no cause, a direction reversed at a cut, a product short of its state), and every one was
visible in a still or a clip before delivery.

Look at full size. A 384-pixel contact-sheet cell hides fingers: use `qc.py look` for full-size crops of the hands
and the product at the frames the edit actually uses.

## Every still, before the next wave edits it

| Look at | It fails when |
|---|---|
| Identity | a prop does not read as itself in half a second (a passport with no cover printing, a card that could be a notebook) |
| Product | wrong shape or face for the state, the hinge on the wrong side, extra cameras, buttons, text or interface; it differs from the official image |
| End states | "flat" is not flat (the edges must run straight across the hinge), "closed" has a gap, "upright" leans. Official photos are posed: the still must show the state the plan names, not the photo's pose |
| Hands | not five plausible fingers; a grip nobody would use for this action; fingers across a screen or the product's face; the grip does not show what happens next (thumb under the edge before a lift, palm on top before a press); jewellery differs across a pair (default: none) |
| Physics | the object could not rest in that state, or something floats or bends where it cannot |
| Framing | the shared shape is off its cut partner: check with `qc.py onion` and `qc.py match`. Generated edits often zoom or re-centre; measure after every edit and fix with `align.py` (crop the wider frames to the tighter one) instead of regenerating |
| Light | the key comes from another side than on the partner, or the exposure step is over 10% |

## Every clip, before it is picked

- **Watch the motion, not just the ends.** `qc.py sheet` across the whole clip (every 2–4 frames). Many problems sit
  in the middle: a grip that morphs, a cover that goes the wrong way, a hand that appears from nowhere.
- **When does the motion start and end?** Models often hold the first frames and settle early. Start the pick
  where the motion starts; end it before the motion stops (or at rest, if the cut is a rest cut).
- **Direction and speed at the cut frames**, compared with the partner shot's.
- **Hands stay plausible all the way through.** The product stays rigid except at its hinge and reaches its state.
- **Screens.** Model-made camera dots, interfaces or text: remove dots with `undot.py`; use another take for UI.
- **The last 2–3 frames.** Models often jump or smear into the locked end frame; do not use them.
- **The camera.** No drift or zoom unless planned: `qc.py match` at the frames used.

## Every cut, after the render

- `qc.py cuts`: brightness steps (under 10% on match cuts) and alignment.
- For each relay, the last frames of the outgoing shot and the first of the incoming: same direction and similar
  speed, or both at rest. A world shot whose first and last frames look the same has no motion: re-pick or remake.
- Every shot plays at 0.8–1.25× real time and none ends in a hold.

## The film, before delivery

- A frame grid of the whole film (`qc.py sheet` on the mp4, every 3–5 frames), read section by section as a
  sequence: does each part read as one continuous motion?
- Listen: foley on the action frames, every music join, the final hit on the end card.
- Anything wrong on the product or on a hand is fixed (re-pick, post fix, or one regeneration) before delivery. If
  the cap does not allow it, ask; never ship it as a "known deviation". Known deviations are for small things
  elsewhere in the frame, and the README says what each would cost to fix.
