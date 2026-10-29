"""Remove model-made punch-hole camera dots from a screen (video models add them; many products hide the camera).

usage:
  undot.py IN.mp4 OUT.mp4 x0,y0,x1,y1
      detect: small dark ellipses on bright screen areas inside the box are inpainted, frame by frame. Writes a sheet
      of fixed spots to OUT.jpg for checking. Misses frames where the screen is still dim.
  undot.py IN.mp4 OUT.mp4 --fixed cx,cy,r,from
      fixed: for frames >= from, every row of the circle (cx, cy, r) is replaced by a straight blend between the
      pixels just left and right of it. For a still screen with the dot in one place; screen photos graded top to
      bottom (sky, sea) fill without a trace, dim frames included.
"""
import sys, subprocess, cv2, numpy as np


def encoder(dst, W, H, fps):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                             '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-crf', '10', '-preset', 'slow',
                             '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)


def detect(im, roi):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    bg = cv2.medianBlur(g, 41).astype(np.int16)
    m = ((bg - g) > 45).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if not (25 <= a <= 900 and w <= 48 and h <= 40 and 0.6 <= w / max(h, 1) <= 3.2): continue
        if not (roi[0] <= x and x + w <= roi[2] and roi[1] <= y and y + h <= roi[3]): continue
        ring = bg[max(0, y - 20):y + h + 20, max(0, x - 20):x + w + 20]
        if np.median(ring) < 110 or a / (w * h) < 0.55: continue
        keep[lab == i] = 1
    return keep


def fill_circle(im, cx, cy, r):
    im = im.astype(np.float32)
    for y in range(cy - r, cy + r + 1):
        h = int((r * r - (y - cy) ** 2) ** 0.5) + 2
        a, b = im[y, cx - h - 2], im[y, cx + h + 2]
        t = np.linspace(0, 1, 2 * h + 1)[:, None]
        im[y, cx - h:cx + h + 1] = a * (1 - t) + b * t
    return np.clip(im, 0, 255).astype(np.uint8)


def main(src, dst, *opt):
    fixed = opt[0] == '--fixed'
    spec = tuple(int(v) for v in (opt[1] if fixed else opt[0]).split(','))
    cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS); W, H = int(cap.get(3)), int(cap.get(4))
    enc = encoder(dst, W, H, fps); n = hits = 0; sheet = []
    while True:
        ok, im = cap.read()
        if not ok: break
        if fixed:
            cx, cy, r, f0 = spec
            if n >= f0:
                im = fill_circle(im, cx, cy, r); hits += 1
        else:
            keep = detect(im, spec)
            if keep.any():
                hits += 1
                keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
                im = cv2.inpaint(im, keep, 7, cv2.INPAINT_TELEA)
                if len(sheet) < 6 and hits % 6 == 1:
                    ys, xs = np.nonzero(keep); y, x = int(ys.mean()), int(xs.mean())
                    sheet.append(cv2.resize(im[max(0, y - 90):y + 90, max(0, x - 160):x + 160], (320, 180)))
        enc.stdin.write(im.tobytes()); n += 1
    enc.stdin.close(); enc.wait()
    if sheet: cv2.imwrite(dst[:-4] + '.jpg', np.hstack(sheet))
    print(dst, f'{n} frames, {hits} fixed')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
