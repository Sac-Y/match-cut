"""Crop and zoom a still so its object sits where its cut partner's does.

usage: align.py IN OUT L T Z   -> a 1920x1080 PNG
  L, T: the crop window's left and top edges in % of the source; Z: zoom (>= 1). In the output, a source point at
  x % lands at (x - L) * Z %, and the same for y with T.

Generated edits often zoom and re-centre the subject (a closed object came back 1.37x larger and centred), and
re-asking rarely fixes it. Crop the wider frames to the tighter one instead: measure both on a % grid, choose Z so
the sizes match and L, T so a shared point (a hinge, a spine) lands in the same place. The window must stay inside
the source; with a 2k+ source and Z up to about 1.4 the 1080p output loses nothing.
"""
import sys, cv2


def main(src, out, L, T, Z):
    L, T, Z = float(L), float(T), float(Z)
    im = cv2.imread(src); h, w = im.shape[:2]
    x0, y0, cw, ch = L / 100 * w, T / 100 * h, w / Z, h / Z
    if x0 < 0 or y0 < 0 or x0 + cw > w + 0.5 or y0 + ch > h + 0.5:
        sys.exit(f'window {x0:.0f},{y0:.0f} {cw:.0f}x{ch:.0f} leaves the {w}x{h} source: raise Z or move L, T')
    crop = im[round(y0):round(y0 + ch), round(x0):round(x0 + cw)]
    cv2.imwrite(out, cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_AREA if cw > 1920 else cv2.INTER_CUBIC))
    print(out, f'window {cw:.0f}x{ch:.0f}')


if __name__ == '__main__':
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    main(*sys.argv[1:])
