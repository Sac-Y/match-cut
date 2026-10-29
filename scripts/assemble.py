"""Join rendered shots and the mix into deliverables.

usage: assemble.py CONFIG RENDERDIR [--draft] [--audio WAV]
  full:  cfg.deliver.dir/<name>-master-prores422hq.mov (ProRes 422 HQ + 24-bit PCM), <name>-1080p.mp4 (H.264 crf 14,
         AAC 320k), stems/ copied from the mix folder.
  draft: RENDERDIR/<name>-animatic.mp4 only (for the key-frame animatic; audio defaults to the music cue, or
         silence if there is no cue yet).
Audio defaults to cfg.mix.out/mix.wav.
"""
import argparse, os, subprocess, sys, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def run(cmd): subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config'); ap.add_argument('renderdir'); ap.add_argument('--draft', action='store_true'); ap.add_argument('--audio')
    a = ap.parse_args(); draft, audio = a.draft, a.audio
    cfg = common.load(a.config); rdir = os.path.abspath(a.renderdir); name = cfg.get('name', 'montage')
    if audio is None:
        audio = common.path(cfg, cfg['music']['out']) if draft else os.path.join(common.path(cfg, cfg['mix']['out']), 'mix.wav')
    lst = os.path.join(rdir, 'concat.txt')
    open(lst, 'w').write(''.join(f"file '{rdir}/shots/{s['id']}.mov'\n" for s in cfg['shots']))
    color = ['-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv']
    if draft:
        out = os.path.join(rdir, f'{name}-animatic.mp4')
        ain = ['-i', audio] if os.path.exists(audio) else ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']  # no cue yet
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, *ain, '-map', '0:v', '-map', '1:a',
             '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', *color, '-c:a', 'aac', '-b:a', '192k', '-shortest',
             '-movflags', '+faststart', out])
        print(out); return
    d = cfg.get('deliver', {}); odir = common.path(cfg, d.get('dir', 'output')); os.makedirs(odir, exist_ok=True)
    master = os.path.join(odir, f'{name}-master-prores422hq.mov'); mp4 = os.path.join(odir, f'{name}-1080p.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio, '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'pcm_s24le', '-shortest', master])
    run(['ffmpeg', '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'slow', '-crf', str(d.get('crf', 14)),
         '-tune', 'grain', '-profile:v', 'high', '-pix_fmt', 'yuv420p', *color, '-c:a', 'aac', '-b:a', '320k',
         '-movflags', '+faststart', mp4])
    sdir = os.path.join(os.path.dirname(audio), 'stems')
    if os.path.isdir(sdir):
        os.makedirs(os.path.join(odir, 'stems'), exist_ok=True)
        for f in os.listdir(sdir): shutil.copy(os.path.join(sdir, f), os.path.join(odir, 'stems', f))
        shutil.copy(audio, os.path.join(odir, 'stems', 'mix.wav'))
    print(master); print(mp4)


if __name__ == '__main__':
    main()
