"""Picture render for a match-cut montage, driven by montage.json.

usage: render.py CONFIG OUTDIR [--draft] [shot ids ...]
writes OUTDIR/shots/<id>.mov (ProRes 422 HQ 10-bit, bt709) and OUTDIR/qc/<id>-{first,mid,last}.{jpg,json}

Per frame: source frame (bt709 decode, 16-bit) -> one affine warp (cover-fit to the frame, per-shot geo, digital pull,
template-A camera roll with a constant cover zoom, whip) -> grade -> film (toe, halation, grain) -> supers.
Sources may be video clips or stills (stills are held, so an animatic of key frames renders with the same moves).
--draft renders at half size without film texture, for animatics. JOBS=n sets the number of worker processes.
"""
import json, math, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff')
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
DEFAULT_FONT = {'font': '/System/Library/Fonts/HelveticaNeue.ttc', 'style': 'Bold'}
X = None   # per-process render context


class Ctx:
    def __init__(self, cfg_path, draft):
        self.cfg = cfg = common.load(cfg_path)
        t = cfg['timeline']
        self.FPS = t['fps']
        self.W0, self.H0 = t['size']                       # canvas: all config coordinates are in these pixels
        self.k = 0.5 if draft else 1.0                     # output scale
        self.W, self.H = int(self.W0 * self.k), int(self.H0 * self.k)
        self.draft = draft
        self.shots = {s['id']: s for s in cfg['shots']}
        look = cfg.get('look', {})
        roll = look.get('roll', {})
        self.roll_dps = roll.get('dps', 20.0)
        max_frames = roll.get('max_frames', round(2 * 60 / t['bpm'] * self.FPS))    # default: a 2-beat shot
        self.TH_MAX = math.radians(self.roll_dps * (max_frames - 1) / 2 / self.FPS)
        self.ZOOM_A = math.cos(self.TH_MAX) + (self.W0 / self.H0) * math.sin(self.TH_MAX)   # rotated frame still covers
        self.max_frames = max_frames
        self.grades = {'neutral': {}}
        self.grades.update(look.get('grades', {}))
        self.film = {'toe': 0.022, 'halation': 0.07, 'grain': 1.0, **look.get('film', {})}
        self.text = {**DEFAULT_FONT, 'size': 0.072, 'tracking': 0.006, 'color': [255, 255, 255],
                     'shadow_alpha': 200, 'shadow_blur': 0.008, **cfg.get('text', {})}
        self.supers = cfg.get('supers', [])
        self._sup = {}


def init(cfg_path, draft):
    global X
    X = Ctx(cfg_path, draft)


# ---------------------------------------------------------------- io
def probe(src):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,r_frame_rate', '-of', 'csv=p=0', src],
                         capture_output=True, text=True, check=True).stdout.strip().split(',')
    num, den = out[2].split('/')
    return int(out[0]), int(out[1]), float(num) / float(den)


def read_frames(src, lo, hi):
    """Decode source frames lo..hi (inclusive) as uint16 RGB (bt709, limited range in)."""
    w, h, _ = probe(src)
    vf = (f"select='between(n\\,{lo}\\,{hi})',scale=in_color_matrix=bt709:in_range=limited:"
          f"flags=accurate_rnd+full_chroma_int+lanczos,format=rgb48le")
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', vf, '-fps_mode', 'passthrough', '-f', 'rawvideo', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint16).reshape(-1, h, w, 3)
    assert len(a) == hi - lo + 1, (src, lo, hi, len(a))
    return {lo + k: a[k] for k in range(len(a))}


def read_still(src):
    im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
    assert im is not None, src
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    im = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB)
    return im.astype(np.float32) / (65535 if im.dtype == np.uint16 else 255)


def writer(path):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb48le', '-s', f'{X.W}x{X.H}',
                             '-r', str(X.FPS), '-i', '-', '-vf',
                             'scale=out_color_matrix=bt709:out_range=limited:flags=accurate_rnd+full_chroma_int,format=yuv422p10le',
                             '-c:v', 'prores_ks', '-profile:v', '3', '-vendor', 'apl0', '-color_primaries', 'bt709',
                             '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv', path], stdin=subprocess.PIPE)


def picks(sh, n, src_fps):
    """Source frame per timeline frame. picks: [list] | {list} | {range: [a, b]} | {linspace: [a, b]} |
    {from: a, speed: 1.0} (default: real time from frame 0); any dict may add {offset: k}."""
    p = sh.get('picks', {})
    if isinstance(p, list):
        return p
    if 'list' in p:
        out = p['list']
    elif 'range' in p:
        out = list(range(*p['range']))
    elif 'linspace' in p:
        out = [int(round(v)) for v in np.linspace(p['linspace'][0], p['linspace'][1], n)]
    else:
        a, sp = p.get('from', 0), p.get('speed', 1.0)
        out = [int(round(a + i * sp * src_fps / X.FPS)) for i in range(n)]
    return [v + p.get('offset', 0) for v in out]


# ---------------------------------------------------------------- geometry (canvas pixels)
def A3(m): return np.vstack([m, [0, 0, 1]])


def fit(w, h):
    s = max(X.W0 / w, X.H0 / h)
    return np.array([[s, 0, (X.W0 - s * w) / 2], [0, s, (X.H0 - s * h) / 2], [0, 0, 1]])


def ease(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def pull_ease(sh, i, n):
    p = sh['pull']; return ease((i - p['i0']) / (n - 1 - p['i0']))


def roll_angle(sh, i, n, f):
    """Clockwise degrees. Consecutive shots on one framing share one roll (roll_seg = [first frame, frames])."""
    if 'roll_seg' in sh:
        s0, ns = sh['roll_seg']
        return math.degrees(X.TH_MAX) * (2 * (f - s0) / (ns - 1) - 1)
    if n > X.max_frames:                                   # long shot: spread the covered angle over its length
        return math.degrees(X.TH_MAX) * (2 * i / (n - 1) - 1)
    return X.roll_dps * (i - (n - 1) / 2) / X.FPS


def affine(sh, i, n, w, h, f):
    M = fit(w, h)
    if 'geo' in sh:                                        # move source anchor (canvas px) to dst anchor at scale s
        (sx, sy), (dx, dy), s = sh['geo']
        M = np.array([[s, 0, dx - s * sx], [0, s, dy - s * sy], [0, 0, 1]]) @ M
    if 'pull' in sh:                                       # digital pull-out into the next shot's framing
        p = sh['pull']; e = pull_ease(sh, i, n)
        kk = 1 + (p['k_end'] - 1) * e
        cd = np.array(p['c_src']) + (np.array(p['c_dst']) - np.array(p['c_src'])) * e
        M = np.array([[kk, 0, cd[0] - kk * p['c_src'][0]], [0, kk, cd[1] - kk * p['c_src'][1]], [0, 0, 1]]) @ M
    if sh.get('roll'):
        M = A3(cv2.getRotationMatrix2D((X.W0 / 2, X.H0 / 2), -roll_angle(sh, i, n, f), X.ZOOM_A)) @ M
    return M


def whip(sh, i, n):
    """(scale, y offset px, vertical blur px, x offset px, horizontal blur px) for this frame: whip_out covers the
    last frames, whip_in the first. Profile entries give 3 values (a vertical whip) or 5 (also horizontal: a pan).
    The content drifts inside the overscan of a short push-in, so no frame edge shows; the blur carries the speed."""
    e = None
    if 'whip_out' in sh:
        prof = sh['whip_out']; j = i - (n - len(prof))
        if j >= 0: e = prof[j]
    if e is None and 'whip_in' in sh and i < len(sh['whip_in']):
        e = sh['whip_in'][i]
    if e is None:
        return 1.0, 0.0, 0.0, 0.0, 0.0
    return tuple(e) + (0.0, 0.0) if len(e) == 3 else tuple(e)


def pull_mask(h, w, c, r):
    """Pool of light around the subject (source pixels): 1 inside, smooth fall-off to 0 between r=0.72 and 1."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - c[0]) / r[0]) ** 2 + ((yy - c[1]) / r[1]) ** 2)
    return ease((1 - d) / 0.28).astype(np.float32)[..., None]


def edge_feather(h, w, frac):
    def ramp(n):
        a = np.ones(n, np.float32); k = int(n * frac)
        if k >= 2:
            u = np.linspace(0, 1, k, dtype=np.float32); a[:k] = u * u * (3 - 2 * u); a[n - k:] = a[:k][::-1]
        return a
    return (ramp(h)[:, None] * ramp(w)[None, :])[..., None]


def out_matrix(M):
    return (np.diag([X.k, X.k, 1.0]) @ M)[:2]


# ---------------------------------------------------------------- look
def soft_knee(x, k):
    over = x > k
    y = x.copy(); y[over] = k + (1 - k) * np.tanh((x[over] - k) / (1 - k)); return y


def look(x, sh):
    g = {k: sh[k] for k in ('gain', 'gamma', 'sat', 'knee') if k in sh}
    x = np.clip(x, 0, 1) ** g.get('gamma', 1.0) * g.get('gain', 1.0)
    gr = X.grades[sh.get('grade', 'neutral')]
    st = np.array(gr.get('shadow', [0, 0, 0]), np.float32); ht = np.array(gr.get('highlight', [0, 0, 0]), np.float32)
    l = x @ LUMA
    x = x + ((1 - np.clip(l, 0, 1)) ** 3)[..., None] * st + (np.clip(l, 0, 1) ** 2)[..., None] * ht
    l = x @ LUMA
    x = l[..., None] + gr.get('sat', 1.0) * g.get('sat', 1.0) * (x - l[..., None])
    x = soft_knee(np.clip(x, 0, None), g.get('knee', 0.80))
    return np.clip(x, 0, 1)


def film(x, f, grain=1.0, halation=True):
    """Lifted toe, halation, grain: shared by every frame so all sources sit in one camera."""
    if X.draft:
        return np.clip(x, 0, 1)
    W, H, fl = X.W, X.H, X.film
    x = x + fl['toe'] * np.clip(1 - x / 0.22, 0, 1) ** 2
    if halation and fl['halation']:
        l = x @ LUMA; hl = np.clip((l - 0.72) / 0.28, 0, 1) ** 2
        small = cv2.resize(hl, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        hb = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
        x = x + fl['halation'] * hb[..., None] * np.array([1.0, 0.42, 0.22], np.float32)
    grain = grain * fl['grain']
    rng = np.random.default_rng(1000 + f)
    nz = cv2.GaussianBlur(rng.standard_normal((H, W), np.float32), (0, 0), 0.65) * 1.6
    l = np.clip(x @ LUMA, 0, 1)
    amp = 0.013 * grain * (0.35 + 2.6 * l * (1 - l))
    nc = rng.standard_normal((H // 2, W // 2, 3), np.float32) * 0.0035 * grain
    x = x + (nz * amp)[..., None] + cv2.resize(nc, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(x, 0, 1)


# ---------------------------------------------------------------- text, supers, cards
def font(spec, size):
    path, style = spec.get('font'), spec.get('style')
    if not path or not os.path.exists(path):
        return ImageFont.load_default(size)
    if spec.get('variation'):                              # variable font (e.g. SFNS.ttf): named instance, e.g. "Semibold"
        f = ImageFont.truetype(path, size); f.set_variation_by_name(spec['variation'])
        return f
    for i in range(20):
        try:
            f = ImageFont.truetype(path, size, index=i)
        except OSError:
            break
        if style is None or f.getname()[1] == style:
            return f
    return ImageFont.truetype(path, size)


def text_layer(text, y, st, x=0.5):
    """White tracked caps centred at (x, y) (fractions), with a soft drop shadow baked in. RGBA canvas-size image."""
    W, H = X.W0, X.H0
    f = font(st, round(H * st['size']))
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shadow)
    spacing = round(H * st['tracking']); chars = list(text)
    widths = [d.textlength(ch, font=f) for ch in chars]
    xx = x * W - (sum(widths) + spacing * (len(chars) - 1)) / 2
    for ch, w in zip(chars, widths):
        sd.text((xx, y * H), ch, font=f, fill=(0, 0, 0, st['shadow_alpha']), anchor='lm')
        d.text((xx, y * H), ch, font=f, fill=(*st['color'], 255), anchor='lm')
        xx += w + spacing
    shadow = shadow.filter(ImageFilter.GaussianBlur(H * st['shadow_blur']))
    return Image.alpha_composite(shadow, im)


def super_layer(s):
    key = json.dumps(s, sort_keys=True)
    if key not in X._sup:
        if 'png' in s:
            im = cv2.cvtColor(cv2.imread(common.path(X.cfg, s['png']), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
        else:
            im = np.array(text_layer(s['text'], s.get('y', 0.5), {**X.text, **s.get('style', {})}, s.get('x', 0.5)))
        im = im.astype(np.float32) / 255
        if s.get('dy'):
            im = np.roll(im, s['dy'], axis=0)
        if X.k != 1:
            im = cv2.resize(im, (X.W, X.H), interpolation=cv2.INTER_AREA)
        al = im[..., 3:]; shd = cv2.GaussianBlur(al[..., 0], (0, 0), 9 * X.k)[..., None]
        X._sup[key] = (im[..., :3], al, np.clip(shd * 1.6, 0, 1))
    return X._sup[key]


def supers(x, f):
    for s in X.supers:
        if s['start'] <= f < s['end']:
            rgb, al, shd = super_layer(s)
            x = x * (1 - 0.42 * shd); x = x * (1 - al) + rgb * al
    return x


def card_image(sh):
    """End card: optional logo and one line of text on a flat background, at canvas size."""
    W, H = X.W0, X.H0
    im = Image.new('RGB', (W, H), tuple(sh.get('bg', [0, 0, 0])))
    if sh.get('image'):
        return np.asarray(Image.open(common.path(X.cfg, sh['image'])).convert('RGB').resize((W, H), Image.LANCZOS),
                          np.float32) / 255
    if sh.get('logo') and X.draft and not os.path.exists(common.path(X.cfg, sh['logo'])):
        ImageDraw.Draw(im).text((W / 2, H * sh.get('logo_y', 0.44)), '[logo]', font=font(DEFAULT_FONT, round(H * 0.06)),
                                fill=(128, 128, 128), anchor='mm')
    elif sh.get('logo'):
        logo = Image.open(common.path(X.cfg, sh['logo'])).convert('RGBA')
        logo = logo.crop(logo.getchannel('A').getbbox())
        lh = round(H * sh.get('logo_h', 0.26))
        logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
        im.paste(logo, ((W - logo.width) // 2, round(H * sh.get('logo_y', 0.44) - lh / 2)), logo)
    if sh.get('text'):
        st = {**DEFAULT_FONT, **sh.get('font', {})}
        ImageDraw.Draw(im).text((W / 2, H * sh.get('text_y', 0.69)), sh['text'],
                                font=font(st, round(H * sh.get('text_size', 0.075))),
                                fill=tuple(sh.get('text_color', [255, 255, 255])), anchor='mm')
    return np.asarray(im, np.float32) / 255


def placeholder(sh):
    x = np.full((X.H, X.W, 3), 46, np.uint8)
    lab = f"{sh['id']}  {sh.get('name', '')}"
    cv2.putText(x, lab, (int(0.05 * X.W), int(0.5 * X.H)), cv2.FONT_HERSHEY_SIMPLEX, 2.4 * X.k, (204, 204, 204),
                max(1, int(4 * X.k)), cv2.LINE_AA)
    return x.astype(np.float32) / 255


# ---------------------------------------------------------------- render
def render_shot(sid, outdir):
    sh = X.shots[sid]; n = sh['end'] - sh['start']; kind = sh.get('type', 'clip')
    os.makedirs(f'{outdir}/shots', exist_ok=True); os.makedirs(f'{outdir}/qc', exist_ok=True)
    frames = still = mask = card = None
    if kind == 'clip' and X.draft and not os.path.exists(common.path(X.cfg, sh['src'])):
        kind = 'placeholder'                               # animatic before every still exists
    if kind == 'clip':
        src = common.path(X.cfg, sh['src'])
        if src.lower().endswith(IMG_EXT):
            still = read_still(src); fh, fw = still.shape[:2]
        else:
            fw, fh, sfps = probe(src)
            pk = picks(sh, n, sfps); assert len(pk) == n, (sid, len(pk), n)
            frames = read_frames(src, min(pk), max(pk))
        if 'pull' in sh:
            F = fit(fw, fh); s = F[0, 0]
            c = ((sh['pull']['c_src'][0] - F[0, 2]) / s, (sh['pull']['c_src'][1] - F[1, 2]) / s)
            r = [v / s for v in sh['pull'].get('mask', [820, 640])]
            mask = pull_mask(fh, fw, c, r)
    elif kind == 'card':
        card = card_image(sh)
    p = writer(f'{outdir}/shots/{sid}.mov'); qc = {0: 'first', n // 2: 'mid', n - 1: 'last'}
    for i in range(n):
        f = sh['start'] + i
        if kind == 'black':
            x = film(np.zeros((X.H, X.W, 3), np.float32), f, halation=False)
        elif kind == 'placeholder':
            x = placeholder(sh)
        elif kind == 'card':
            M = cv2.getRotationMatrix2D((X.W0 / 2, X.H0 / 2), 0, 1 + sh.get('push', 0.02) * i / max(1, n - 1))
            x = cv2.warpAffine(card, out_matrix(A3(M)), (X.W, X.H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
            x = film(x, f, grain=sh.get('grain', 0.5), halation=sh.get('halation', False))
        else:
            src = still if still is not None else frames[pk[i]].astype(np.float32) / 65535
            M = affine(sh, i, n, fw, fh, f)
            if mask is not None:
                ep = pull_ease(sh, i, n); wgt = min(1.0, 2.5 * ep)            # pool of light grows as the shot shrinks;
                rect = edge_feather(fh, fw, 0.12 * min(1.0, 6.5 * ep))         # edge fade always wider than the gap
                x = cv2.warpAffine(src * (1 - wgt + wgt * mask) * rect, out_matrix(M), (X.W, X.H), flags=cv2.INTER_LANCZOS4,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            else:
                ws, dy, blur, dx, hblur = whip(sh, i, n)
                if ws != 1.0 or dy or dx:
                    M = A3(cv2.getRotationMatrix2D((X.W0 / 2, X.H0 / 2), 0, ws)) @ M; M[1, 2] += dy; M[0, 2] += dx
                x = cv2.warpAffine(src, out_matrix(M), (X.W, X.H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
                if blur * X.k >= 2:
                    x = cv2.blur(x, (1, int(round(blur * X.k))))
                if hblur * X.k >= 2:
                    x = cv2.blur(x, (int(round(hblur * X.k)), 1))
            x = film(look(np.clip(x, 0, 1), sh), f, grain=sh.get('grain', 1.0))
        x = supers(x, f)
        out = (np.clip(x, 0, 1) * 65535 + 0.5).astype(np.uint16)
        p.stdin.write(out.tobytes())
        if i in qc:
            l = x @ LUMA
            json.dump({'mean': float(l.mean()), 'p50': float(np.median(l)), 'p95': float(np.percentile(l, 95))},
                      open(f'{outdir}/qc/{sid}-{qc[i]}.json', 'w'))
            cv2.imwrite(f'{outdir}/qc/{sid}-{qc[i]}.jpg', cv2.cvtColor((out >> 8).astype(np.uint8), cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])
    p.stdin.close(); p.wait(); assert p.returncode == 0, sid
    return sid


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--draft']; draft = '--draft' in sys.argv
    cfg_path, outdir = args[0], os.path.abspath(args[1])
    init(cfg_path, draft)
    ids = args[2:] or [s['id'] for s in X.cfg['shots']]
    with ProcessPoolExecutor(max_workers=int(os.environ.get('JOBS', 6)), initializer=init, initargs=(cfg_path, draft)) as ex:
        for sid in ex.map(render_shot, ids, [outdir] * len(ids)):
            print('done', sid, flush=True)
