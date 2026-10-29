"""Checks for a match-cut montage.

usage:
  qc.py sheet CLIP OUT.jpg [first last step]
      numbered contact sheet of a clip with a centre cross: pick the frames a shot should use.
  qc.py onion A.jpg B.jpg OUT.jpg
      the two sides of one cut: A | B | A and B blended 50/50 with a centre cross. Use it on key-frame stills before
      any video is generated: the shared shape must sit on itself in the blend (same place, same size, same angle).
  qc.py cuts CONFIG RENDERDIR OUT.jpg
      every cut in the render: last frame of the outgoing shot next to the first frame of the incoming one, from
      RENDERDIR/qc. Prints the brightness step at each cut and flags steps over 10% (the eye reads them as a jump);
      mark an intended step (a lineup alternating warm and cool worlds) with "step_ok": true on the incoming shot.
  qc.py match REF.jpg x0,y0,x1,y1 TARGET[:frame] ...
      find the subject boxed in REF inside each target (image, or video at a frame): centre and scale relative to
      REF. Use it to line up a product across a lineup or across a cut, then put the offsets in the shot's geo.
  qc.py look CLIP_OR_STILL OUT.jpg f1,f2,... x0,y0,x1,y1
      the box at full resolution at each listed frame, side by side (for a still, give 0 as the frame). For the
      realism review (review.md): hands, grips, the product's state and screen at the frames the edit uses, which a
      contact sheet is too small to show.
"""
import json, os, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def label(t, s, xy=(6, 26), scale=0.8):
    cv2.putText(t, s, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(t, s, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 255, 255), 2, cv2.LINE_AA)


def cross(t):
    h, w = t.shape[:2]
    cv2.line(t, (w // 2, 0), (w // 2, h), (0, 255, 0), 1); cv2.line(t, (0, h // 2), (w, h // 2), (0, 255, 0), 1)


def frame(spec):
    path, _, n = spec.rpartition(':')
    if not path or not n.isdigit():
        path, n = spec, None
    if n is None and path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        return cv2.imread(path)
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, int(n or 0)); ok, im = cap.read()
    assert ok, spec
    return im


def sheet(clip, out, *rng):
    cap = cv2.VideoCapture(clip); fr = []
    while True:
        ok, im = cap.read()
        if not ok: break
        fr.append(im)
    a, b, s = (int(x) for x in rng) if len(rng) == 3 else (0, len(fr) - 1, 3)
    idx = list(range(a, min(b, len(fr) - 1) + 1, s)); cols, tw, th = 5, 384, 216
    rows = (len(idx) + cols - 1) // cols; img = np.zeros((rows * th, cols * tw, 3), np.uint8)
    for k, i in enumerate(idx):
        t = cv2.resize(fr[i], (tw, th), interpolation=cv2.INTER_AREA); label(t, str(i)); cross(t)
        img[(k // cols) * th:(k // cols + 1) * th, (k % cols) * tw:(k % cols + 1) * tw] = t
    cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 85]); print(out, len(fr), 'frames')


def onion(a, b, out):
    A, B = cv2.imread(a), cv2.imread(b); tw, th = 640, 360
    A = cv2.resize(A, (tw, th), interpolation=cv2.INTER_AREA); B = cv2.resize(B, (tw, th), interpolation=cv2.INTER_AREA)
    M = cv2.addWeighted(A, 0.5, B, 0.5, 0)
    for t, s in ((A, 'A out'), (B, 'B in'), (M, 'A+B')): cross(t); label(t, s)
    cv2.imwrite(out, np.hstack([A, B, M]), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out)


def cuts(cfg_path, rdir, out):
    cfg = common.load(cfg_path); shots = cfg['shots']; tw, th = 480, 270; rows = []
    for a, b in zip(shots, shots[1:]):
        pa, pb = f"{rdir}/qc/{a['id']}-last", f"{rdir}/qc/{b['id']}-first"
        if not (os.path.exists(pa + '.jpg') and os.path.exists(pb + '.jpg')):
            continue
        ta = cv2.resize(cv2.imread(pa + '.jpg'), (tw, th), interpolation=cv2.INTER_AREA)
        tb = cv2.resize(cv2.imread(pb + '.jpg'), (tw, th), interpolation=cv2.INTER_AREA)
        la, lb = json.load(open(pa + '.json'))['mean'], json.load(open(pb + '.json'))['mean']
        step = (lb - la) / max(la, lb, 1e-6); flag = abs(step) > 0.10 and not b.get('step_ok') and b.get('type') != 'card'
        for t in (ta, tb): cross(t)
        label(ta, f"{a['id']} last"); label(tb, f"{b['id']} first  {step:+.0%}" + ('  CHECK' if flag else ''))
        rows.append(np.hstack([ta, np.zeros((th, 8, 3), np.uint8), tb]))
        print(f"cut {a['id']} -> {b['id']} at frame {b['start']}: brightness {la:.3f} -> {lb:.3f} ({step:+.0%})"
              + ('  <-- check' if flag else ''))
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85]); print(out)


def match(ref, box, *targets):
    x0, y0, x1, y1 = (int(v) for v in box.split(','))
    R = frame(ref); tpl = R[y0:y1, x0:x1]; tcx, tcy = (x0 + x1) / 2, (y0 + y1) / 2
    for spec in targets:
        im = frame(spec); best = (-1,)
        if im.shape[:2] != R.shape[:2]: im = cv2.resize(im, (R.shape[1], R.shape[0]), interpolation=cv2.INTER_LANCZOS4)
        for s in np.arange(0.60, 1.60, 0.01):
            t = cv2.resize(tpl, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            if t.shape[0] >= im.shape[0] or t.shape[1] >= im.shape[1]: continue
            r = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
            if mv > best[0]: best = (mv, s, ml[0] + t.shape[1] / 2, ml[1] + t.shape[0] / 2)
        print(f"{spec:40s} score {best[0]:.3f}  scale {best[1]:.2f}  centre {best[2]:.0f},{best[3]:.0f}  "
              f"(ref {tcx:.0f},{tcy:.0f})")


def look(src, out, frames, box):
    x0, y0, x1, y1 = (int(v) for v in box.split(','))
    tiles = []
    for n in frames.split(','):
        im = frame(src if src.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) else f'{src}:{n}')
        t = im[y0:y1, x0:x1].copy(); label(t, f'f{n}', scale=0.7); tiles.append(t)
        tiles.append(np.zeros((t.shape[0], 6, 3), np.uint8))
    cv2.imwrite(out, np.hstack(tiles[:-1]), [cv2.IMWRITE_JPEG_QUALITY, 92]); print(out)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, *args = sys.argv[1:]
    {'sheet': sheet, 'onion': onion, 'cuts': cuts, 'match': match, 'look': look}[cmd](*args)
