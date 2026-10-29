"""Mix for a match-cut montage, driven by montage.json: music cue + VO phrases + foley placed on frames, ducking,
an optional reverse swell into the final hit, mastered to the loudness target.

usage: mix.py CONFIG [OUTDIR]  -> OUTDIR/mix.wav, OUTDIR/stems/{music,vo,sfx}.wav (48 kHz 24-bit), OUTDIR/mix-report.json
OUTDIR defaults to cfg.mix.out. The report lists loudness, true peak, limiter work, sudden loudness dips (the
"music suddenly falls away" problem: a 1 s window more than 8 LU quieter than the second before) and how far each VO phrase sits above the music inside the voice band.
"""
import json, os, sys
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln
from scipy.signal import resample_poly, butter, sosfiltfilt
from scipy.ndimage import minimum_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

SR = 48000
db = lambda g: 10 ** (g / 20)


def load(path):
    y, _ = librosa.load(path, sr=SR, mono=False)
    return np.stack([y, y]) if y.ndim == 1 else y


def norm(y, peak_db=-1): return y / max(1e-9, np.abs(y).max()) * db(peak_db)


def fade(x, fin=0.005, fout=0.03):
    x = x.copy(); a, b = int(fin * SR), int(fout * SR)
    if a: x[:, :a] *= np.linspace(0, 1, a)
    if b: x[:, -b:] *= np.linspace(1, 0, b)
    return x


def smooth(g, attack, release):
    att, rel = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR)); out = np.empty_like(g); s = 1.0
    for i in range(len(g)):
        c = att if g[i] < s else rel; s = c * s + (1 - c) * g[i]; out[i] = s
    return out


def hold_limit(need, release):
    out = np.empty_like(need); s = 1.0; r = np.exp(-1 / (release * SR))
    for i in range(len(need)):
        s = need[i] if need[i] < s else r * s + (1 - r) * need[i]; out[i] = s
    return out


def peak_limit(x, ceiling, look=0.002, release=0.06):
    """Look-ahead peak limiter for one VO phrase (keeps the master limiter off the music)."""
    need = np.minimum(1.0, ceiling / np.maximum(np.abs(x).max(0), 1e-9))
    return x * hold_limit(minimum_filter1d(need, size=int(2 * look * SR) + 1), release)


def band(x, lo=None, hi=None, order=4):
    if lo and hi: return sosfiltfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x, axis=1)
    if lo: return sosfiltfilt(butter(order, lo, 'high', fs=SR, output='sos'), x, axis=1)
    return sosfiltfilt(butter(order, hi, 'low', fs=SR, output='sos'), x, axis=1)


def true_peak(x): return np.abs(resample_poly(x, 4, 1, axis=1)).max()


def limit(x, ceiling):
    """Look-ahead peak limiter on the 4x oversampled signal; gain envelope applied at 48 kHz."""
    up = np.abs(resample_poly(x, 4, 1, axis=1)).max(0)
    need = np.minimum(1.0, ceiling / np.maximum(up, 1e-9))
    need = minimum_filter1d(need, size=4 * int(0.003 * SR), origin=0)[::4][:x.shape[1]]
    g = hold_limit(need, 0.08)
    return x * g, g


def main():
    cfg = common.load(sys.argv[1]); mx = cfg['mix']; fps = cfg['timeline']['fps']
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else common.path(cfg, mx['out'])
    os.makedirs(f'{out}/stems', exist_ok=True)
    N = int(round(common.seconds(cfg) * SR))
    fr = lambda f: int(round(f / fps * SR))

    def put(bus, x, at):
        i0 = max(0, at); x = x[:, i0 - at:]; n = min(x.shape[1], N - i0)
        if n > 0: bus[:, i0:i0 + n] += x[:, :n]

    # ------------------------------------------------------------ music
    music, msr = sf.read(common.path(cfg, mx['music']), always_2d=True)
    assert msr == SR, f'music cue must be {SR} Hz'
    music = music.T[:, :N]
    if music.shape[1] < N: music = np.pad(music, ((0, 0), (0, N - music.shape[1])))
    if music.shape[0] == 1: music = np.vstack([music, music])

    # ------------------------------------------------------------ VO: phrase [in, out) of its file lands on `frame`
    vo = np.zeros((2, N)); spans = []
    v = mx.get('vo')
    if v:
        files = {}
        pre, post = v.get('pre', 0.03), v.get('post', 0.10)
        for ph in v['phrases']:
            fpath = common.path(cfg, ph.get('file', v['file']))
            if fpath not in files: files[fpath] = norm(load(fpath))
            src = files[fpath]; a, b = ph['in'], ph['out']
            x = fade(src[:, int((a - pre) * SR):int((b + post) * SR)], v.get('fade_in', 0.01), v.get('fade_out', 0.06))
            x = x * db(ph.get('gain', 0))
            if ph.get('level'):                            # per-word gain curve in file seconds, dB
                ts = a - pre + np.arange(x.shape[1]) / SR; pts = np.array(ph['level'])
                x = x * db(np.interp(ts, pts[:, 0], pts[:, 1]))
            if ph.get('limit'):                            # no louder peaks than the lines already placed
                x = peak_limit(x, np.abs(vo).max() * db(0.0))
            put(vo, x, fr(ph['frame']) - int(pre * SR))
            spans.append((ph.get('text', ''), fr(ph['frame']), fr(ph['frame']) + int((b - a) * SR)))

    # ------------------------------------------------------------ foley: file seconds [in, in+len), file time `hit` lands on `frame`
    sfx = np.zeros((2, N))
    src = {k: norm(load(common.path(cfg, p))) for k, p in mx.get('sfx_files', {}).items()}
    for k, d in mx.get('sfx_derived', {}).items():
        y = src[d['from']]
        if d.get('pitch'): y = np.stack([librosa.effects.pitch_shift(y[c], sr=SR, n_steps=d['pitch']) for c in range(2)])
        if d.get('reverse'): y = y[:, ::-1].copy()
        src[k] = y
    for e in mx.get('sfx', []):
        if isinstance(e, dict): e = [e['key'], e['in'], e['len'], e['hit'], e['frame'], e.get('db', 0)]
        k, t0, ln, hit, f, g = e
        x = fade(src[k][:, int(t0 * SR):int((t0 + ln) * SR)], 0.004, min(0.12, ln / 3)) * db(g)
        put(sfx, x, fr(f) - int((hit - t0) * SR))

    # ------------------------------------------------------------ ducking
    # broadband: whole bed dips while the voice is active (inside from..to frames).
    # voiceband: only 250 Hz-5 kHz dips, bass and air barely move, held over from..to; use it under the last line on a
    # full band so the music keeps its weight instead of falling away.
    g_all = np.ones(N); g_mid = np.ones(N); g_lh = np.ones(N); vb = None
    act_v = np.abs(vo).max(0) > db(-40)
    kk = np.ones(int(0.04 * SR)) / int(0.04 * SR)
    act_v = np.convolve(act_v.astype(float), kk, 'same') > 0
    for d in mx.get('duck', []):
        rng = np.zeros(N, bool); rng[fr(d.get('from', 0)):fr(d['to']) if 'to' in d else N] = True
        if d['type'] == 'broadband':
            g = np.where(act_v & rng, db(d['db']), 1.0)
            g_all *= smooth(g, d.get('attack', 0.04), d.get('release', 0.25))
        else:
            vb = (d.get('lo', 250), d.get('hi', 5000))
            g_mid *= smooth(np.where(rng, db(d['db']), 1.0), d.get('attack', 0.15), d.get('release', 0.4))
            g_lh *= smooth(np.where(rng, db(d.get('other_db', -1.5)), 1.0), d.get('attack', 0.15), d.get('release', 0.4))
    if vb:
        lo, hi = band(music, hi=vb[0]), band(music, lo=vb[1])
        music_d = (lo * g_lh + (music - lo - hi) * g_mid + hi * g_lh) * g_all
    else:
        music_d = music * g_all

    # ------------------------------------------------------------ reverse swell into the final hit
    # Fills a silent stop before the hit with the hit itself played backwards: an air layer (no pitch) plus, after the
    # voice ends, a quieter body layer that is the hit's own chord, so it can only agree with what it leads into.
    sw = mx.get('swell')
    if sw:
        h0 = fr(sw['into']); hit = music[:, h0 - int(0.004 * SR): h0 + int(sw.get('len', 1.0) * SR)]
        air = band(hit, lo=2500); body = band(hit, 600, 2500, order=2)
        ramp = 0.4 + 0.6 * np.linspace(0, 1, hit.shape[1]); ramp[:int(0.08 * SR)] *= np.linspace(0, 1, int(0.08 * SR))
        t = np.arange(hit.shape[1]) / SR
        body_in = np.clip((t - (hit.shape[1] / SR - (sw['into'] - sw.get('body_after', sw['into'] - 25)) / fps)) / 0.1, 0, 1)
        swell = (air[:, ::-1] * db(sw.get('air_db', 6)) + body[:, ::-1] * db(sw.get('body_db', -3)) * body_in) * ramp
        put(music_d, swell, h0 - swell.shape[1])

    # ------------------------------------------------------------ master
    ms = {'lufs': -14, 'ceiling_db': -1.6, 'true_peak_db': -1.5, 'dip_lu': 8, **mx.get('master', {})}
    mix = music_d + vo + sfx
    meter = pyln.Meter(SR)
    gain = db(ms['lufs'] - meter.integrated_loudness(mix.T))
    master, lg = limit(mix * gain, db(ms['ceiling_db']))
    for _ in range(3):
        if true_peak(master) <= db(ms['true_peak_db']): break
        master, lg2 = limit(master, db(ms['ceiling_db'] - 0.2)); lg = lg * lg2
    stems = {'music': music_d * gain * lg, 'vo': vo * gain * lg, 'sfx': sfx * gain * lg}
    sf.write(f'{out}/mix.wav', master.T, SR, subtype='PCM_24')
    for k, x in stems.items(): sf.write(f'{out}/stems/{k}.wav', x.T, SR, subtype='PCM_24')

    # ------------------------------------------------------------ report
    # loudness of each 1 s window, every 0.1 s; a dip = a window more than dip_lu quieter than the second before it
    mom = pyln.Meter(SR, block_size=1.0); step, win = int(0.1 * SR), int(1.0 * SR)
    curve = np.array([max(-70.0, mom.integrated_loudness(master[:, i:i + win].T)) for i in range(0, N - win, step)])
    dips = [(round(j * 0.1 * fps), round(float(curve[j - 10] - curve[j]), 1)) for j in range(10, len(curve))
            if curve[j - 10] - curve[j] > ms['dip_lu']]
    clarity = {}
    if spans:
        vb_vo = band(stems['vo'], 250, 5000); vb_mu = band(stems['music'], 250, 5000)
        for text, a, b in spans:
            r = lambda x: np.sqrt(np.mean(x[:, a:b] ** 2) + 1e-12)
            clarity[text] = round(float(20 * np.log10(r(vb_vo) / r(vb_mu))), 1)
    rep = {'integrated_lufs': round(float(meter.integrated_loudness(master.T)), 2),
           'true_peak_dbtp': round(float(20 * np.log10(true_peak(master))), 2),
           'max_gain_reduction_db': round(float(-20 * np.log10(lg.min())), 2),
           'gain_reduction_over_1db_frames': sorted({int(i / SR * fps) for i in np.flatnonzero(lg < db(-1))}),
           'stem_lufs': {k: round(float(meter.integrated_loudness(x.T)), 1) for k, x in stems.items()},
           'loudness_dips': [{'frame': f, 'drop_lu': d} for f, d in dips],
           'vo_over_music_in_voice_band_db': clarity,
           'loudness_1s_every_100ms': [round(float(v), 1) for v in curve]}
    json.dump(rep, open(f'{out}/mix-report.json', 'w'), indent=1)
    print({k: v for k, v in rep.items() if k != 'loudness_1s_every_100ms'})


if __name__ == '__main__':
    main()
