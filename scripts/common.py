"""Shared helpers: load montage.json and resolve paths relative to it."""
import json, os


def load(path):
    path = os.path.abspath(path)
    cfg = json.load(open(path))
    cfg['_dir'] = os.path.dirname(path)
    t = cfg['timeline']
    t.setdefault('size', [1920, 1080])
    t.setdefault('beats_per_bar', 4)
    shots = cfg.get('shots', [])
    pos = 0
    for s in shots:                       # shots must tile the timeline with no gap or overlap
        assert s['start'] == pos, f"shot {s['id']} starts at {s['start']}, expected {pos}"
        assert s['end'] > s['start'], f"shot {s['id']} is empty"
        pos = s['end']
    if shots:
        assert pos == t['frames'], f"shots end at frame {pos}, timeline has {t['frames']}"
    return cfg


def path(cfg, rel):
    """Resolve a config path: '@alias' looks up cfg['sources']; relative paths start at the config's folder."""
    if rel.startswith('@'):
        rel = cfg['sources'][rel[1:]]
    return rel if os.path.isabs(rel) else os.path.normpath(os.path.join(cfg['_dir'], rel))


def beat_seconds(cfg):
    return 60.0 / cfg['timeline']['bpm']


def seconds(cfg):
    t = cfg['timeline']
    return t['frames'] / t['fps']
