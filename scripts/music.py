"""Music for a match-cut montage: read a generated track's bar grid, then cut it to the timeline.

usage:
  music.py analyze TRACK [--bpm 150] [--json OUT.json]
      tempo, phase (time of the first downbeat), and per bar: start time, loudness (dB) and the strongest key.
      Use it to pick sections: a quiet intro, the groove, the build, the chorus, and the song's own ending and hit.
  music.py cut CONFIG
      builds cfg.music.out from cfg.music.segments ("bar:beat:nbeats", beats may be fractional) played back to back
      with 12 ms crossfades. The total must equal the timeline length. Prints each join with its harmonic similarity
      (chroma cosine, 0-1) and level jump. Joins under 0.5 or over 6 dB are flagged: listen to each; move it or pick
      other bars unless the jump is the song's own (a band re-entry, a chord change it makes anyway).
"""
import argparse, json, os, sys, warnings
import numpy as np, soundfile as sf, librosa

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

SR = 48000
warnings.filterwarnings('ignore', message='n_fft=')
KEYS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])   # Krumhansl-Kessler
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def load_stereo(path, sr=SR):
    y, _ = librosa.load(path, sr=sr, mono=False)
    return (y.T if y.ndim == 2 else np.stack([y, y], 1)).astype(np.float64)


def key_of(chroma):
    c = chroma / (np.linalg.norm(chroma) + 1e-9); best = (-2, '')
    for i in range(12):
        for prof, suf in ((MAJ, ''), (MIN, 'm')):
            r = np.corrcoef(c, np.roll(prof, i))[0, 1]
            if r > best[0]: best = (r, KEYS[i] + suf)
    return best[1], best[0]


def chroma_of(y_mono, sr):
    if len(y_mono) < 2048:
        return np.zeros(12)
    return librosa.feature.chroma_cqt(y=y_mono, sr=sr, hop_length=512).mean(1)


def analyze(a):
    y = load_stereo(a.track, 22050); m = y.mean(1).astype(np.float32); sr = 22050
    onset = librosa.onset.onset_strength(y=m, sr=sr, hop_length=256)
    tempo = a.bpm or float(np.atleast_1d(librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=256)[0])[0])
    beat = 60 / tempo; t_on = librosa.frames_to_time(np.arange(len(onset)), sr=sr, hop_length=256)
    # beat phase: offset whose grid collects the most onset energy
    offs = np.linspace(0, beat, 80, endpoint=False)
    score = [np.interp(np.arange(o, t_on[-1], beat), t_on, onset).sum() for o in offs]
    ph = offs[int(np.argmax(score))]
    # downbeat: of the 4 beats in a bar, the one with the most low-end onset energy
    low = librosa.onset.onset_strength(y=m, sr=sr, hop_length=256, fmax=200, n_mels=32)
    bar = 4 * beat
    db_score = [np.interp(np.arange(ph + k * beat, t_on[-1], bar), t_on, low).sum() for k in range(4)]
    phase = (ph + int(np.argmax(db_score)) * beat) % bar
    bars = []
    for i in range(int((len(m) / sr - phase) // bar)):
        s0, s1 = int((phase + i * bar) * sr), int((phase + (i + 1) * bar) * sr)
        seg = m[s0:s1]; rms = np.sqrt(np.mean(seg ** 2) + 1e-12)
        k, r = key_of(chroma_of(seg, sr))
        bars.append({'bar': i, 'time': round(phase + i * bar, 3), 'db': round(20 * np.log10(rms), 1), 'key': k, 'key_r': round(r, 2)})
    print(f'tempo {tempo:.2f} BPM, beat {beat:.4f} s, bar {bar:.3f} s, phase {phase:.3f} s, {len(bars)} bars, '
          f'whole-track key {key_of(chroma_of(m, sr))[0]}')
    for b in bars:
        print(f"bar {b['bar']:3d}  {b['time']:7.2f}s  {b['db']:6.1f} dB  {'#' * max(0, int((b['db'] + 40) / 2)):20s} {b['key']:4s} {b['key_r']:.2f}")
    if a.json:
        json.dump({'tempo': tempo, 'phase': phase, 'bars': bars}, open(a.json, 'w'), indent=1)


def cut(a):
    cfg = common.load(a.config); mu = cfg['music']
    beat = common.beat_seconds(cfg); bpb = cfg['timeline']['beats_per_bar']; total = common.seconds(cfg)
    segs = [tuple(float(v) for v in s.split(':')) for s in mu['segments']]
    nb = sum(s[2] for s in segs)
    assert abs(nb * beat - total) < 1e-6, f'segments add up to {nb} beats = {nb * beat:.3f} s; timeline is {total:.3f} s'
    y = load_stereo(common.path(cfg, mu['track'])); phase = mu['phase']; XF = mu.get('crossfade', 0.012)
    xf = int(XF * SR); cue = np.zeros((int(round(total * SR)) + xf, 2)); pos = 0; parts = []
    for bar, bt, n in segs:
        s = int(round((phase + beat * bpb * bar + beat * bt) * SR)); L = int(round(n * beat * SR))
        x = y[s - xf // 2: s + L + xf // 2].copy()
        x[:xf] *= np.linspace(0, 1, xf)[:, None]; x[-xf:] *= np.linspace(1, 0, xf)[:, None]
        i0 = pos - xf // 2
        if i0 < 0: x = x[-i0:]; i0 = 0
        cue[i0:i0 + len(x)] += x; parts.append((pos, s, L)); pos += L
    cue = cue[:int(round(total * SR))]
    fo = int(mu.get('tail_fade', 0.3) * SR)
    if fo: cue[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    cue = cue / np.abs(cue).max() * 10 ** (mu.get('peak_db', -1) / 20)
    out = common.path(cfg, mu['out']); os.makedirs(os.path.dirname(out), exist_ok=True)
    sf.write(out, cue.astype(np.float32), SR, subtype='PCM_24')
    print(f'{out}: {len(cue) / SR:.2f} s')
    fps = cfg['timeline']['fps']; win = int(0.4 * SR); flagged = 0
    for (pa, sa, La), (pb, sb, Lb) in zip(parts, parts[1:]):
        A = y[sa + La - win: sa + La].mean(1); B = y[sb: sb + win].mean(1)
        ca, cb = chroma_of(A.astype(np.float32), SR), chroma_of(B.astype(np.float32), SR)
        sim = float(ca @ cb / (np.linalg.norm(ca) * np.linalg.norm(cb) + 1e-9))
        jump = 20 * np.log10((np.sqrt(np.mean(B ** 2)) + 1e-9) / (np.sqrt(np.mean(A ** 2)) + 1e-9))
        bad = sim < 0.5 or abs(jump) > 6; flagged += bad
        print(f"join at frame {pb / SR * fps:6.1f}: harmony {sim:.2f}, level {jump:+5.1f} dB, "
              f"{key_of(ca)[0]} -> {key_of(cb)[0]}{'   <-- check' if bad else ''}")
    print(f'{flagged} join(s) flagged')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('analyze'); p.add_argument('track'); p.add_argument('--bpm', type=float); p.add_argument('--json')
    p = sub.add_parser('cut'); p.add_argument('config')
    a = ap.parse_args(); {'analyze': analyze, 'cut': cut}[a.cmd](a)
