"""Diseño sonoro sintetizado: SFX y música de fondo generados por código (sin samples externos)."""
import numpy as np
from scipy import signal

SR = 48000


def _env(n, a=0.005, r=0.2, curve=3.0):
    t = np.linspace(0, 1, n)
    att = max(1, int(a * SR))
    e = np.exp(-curve * t * (n / SR) / max(r, 1e-3))
    e[:att] *= np.linspace(0, 1, att)
    return e


def _bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def _lp(x, f, order=2):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def _hp(x, f, order=2):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def whoosh(dur=0.45, up=True, seed=1):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # barrido de filtro paso banda por bloques
    blocks = 24
    for i in range(blocks):
        s, e = i * n // blocks, (i + 1) * n // blocks
        p = i / (blocks - 1)
        p = p if up else 1 - p
        fc = 300 + 5200 * p ** 1.6
        seg = _bp(noise[max(0, s - 2000):e], fc * 0.6, min(fc * 1.6, 20000))
        out[s:e] = seg[-(e - s):]
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 1.5 * (t ** 0.4 if up else 1)
    return norm(out * env, 0.55)


def pop(freq=900, dur=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * np.exp(-t * 30)  + freq * 0.35
    ph = 2 * np.pi * np.cumsum(f) / SR
    return norm(np.sin(ph) * _env(n, 0.001, 0.03), 0.6)


def click(seed=3, bright=4000):
    rng = np.random.default_rng(seed)
    n = int(0.03 * SR)
    x = _hp(rng.standard_normal(n), bright) * _env(n, 0.0005, 0.006)
    t = np.arange(n) / SR
    x += 0.4 * np.sin(2 * np.pi * 2200 * t) * _env(n, 0.0005, 0.01)
    return norm(x, 0.45)


def tick():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 3100 * t) * _env(n, 0.0005, 0.012) + 0.5 * np.sin(2 * np.pi * 4700 * t) * _env(n, 0.0005, 0.006)
    return norm(x, 0.35)


def ding(freq=1320, dur=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * m * t) * np.exp(-t * d) for a, m, d in [(1, 1, 5), (0.5, 2.01, 7), (0.25, 3.0, 11), (0.15, 4.2, 15)])
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return norm(x, 0.4)


def thud(dur=0.5, seed=5):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 55 + 110 * np.exp(-t * 25)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    x += 0.35 * _lp(rng.standard_normal(n), 1800) * np.exp(-t * 30)
    return norm(np.tanh(x * 1.8), 0.8)


def riser(dur=1.2, seed=7):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    f = 200 + 1400 * p ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    nz = _hp(rng.standard_normal(n), 2500) * 0.4
    x = (tone + nz) * p ** 2.2
    x[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return norm(x, 0.45)


def typing(dur=0.8, rate=14, seed=11):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(dur * SR))
    tt = 0.0
    while tt < dur - 0.04:
        c = click(seed=int(rng.integers(0, 999)), bright=int(rng.uniform(2500, 5000))) * rng.uniform(0.5, 1)
        s = int(tt * SR)
        out[s:s + len(c)] += c[: len(out) - s]
        tt += rng.uniform(0.5, 1.5) / rate
    return norm(out, 0.4)


def cash(dur=0.9):
    a = ding(2093, 0.9) * 0.6
    b = ding(2637, 0.9) * 0.6
    out = np.zeros(int(dur * SR))
    out[: len(a)] += a
    o = int(0.07 * SR)
    out[o:o + len(b) - o] += b[: len(out) - o]
    return norm(out, 0.45)


SFX = {
    "whoosh": lambda: whoosh(0.45, True, 1),
    "whoosh_down": lambda: whoosh(0.5, False, 2),
    "pop": lambda: pop(900),
    "pop_hi": lambda: pop(1400, 0.07),
    "click": lambda: click(),
    "tick": tick,
    "ding": lambda: ding(),
    "thud": thud,
    "riser": riser,
    "typing": typing,
    "cash": cash,
}


# ----------------------------------------------------------------- música
def _note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _keys(freq, dur, vel=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * h * t + 0.3 * np.sin(2 * np.pi * 0.7 * t)) for h, a in [(1, 1), (2, 0.35), (3, 0.12), (4, 0.06)])
    env = np.minimum(1, t / 0.01) * np.exp(-t * 1.6)
    trem = 1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
    return x * env * trem * vel


def _kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 90 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def _snare(rng):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return (_bp(rng.standard_normal(n), 1200, 7000) * np.exp(-t * 18) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4)


def _hat(rng):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    return _hp(rng.standard_normal(n), 7000) * np.exp(-t * 70) * 0.25


STYLES = {
    # bpm, progresión (acordes MIDI), nivel de batería
    "lofi": (84, [[57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62]], 1.0),
    "upbeat": (112, [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 67]], 1.0),
    "dark": (76, [[50, 53, 57, 60], [46, 50, 53, 57], [48, 51, 55, 58], [45, 48, 52, 55]], 0.7),
    "ambient": (70, [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]], 0.0),
}


def music(duration, style="lofi", seed=21):
    bpm, prog, drums = STYLES.get(style, STYLES["lofi"])
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    n = int((duration + 2) * SR)
    out = np.zeros(n)

    def put(x, at, gain=1.0):
        s = int(at * SR)
        if s >= n:
            return
        e = min(n, s + len(x))
        out[s:e] += x[: e - s] * gain

    bars = int(np.ceil(duration / bar)) + 1
    for b in range(bars):
        chord = prog[b % len(prog)]
        t0 = b * bar
        for k, m in enumerate(chord):
            put(_keys(_note(m), bar * 1.1, 0.18), t0 + k * 0.012)
        put(_keys(_note(chord[0] - 24), bar, 0.35) , t0)  # bajo
        if style != "ambient":
            # arpegio suave
            for i in range(8):
                m = chord[[0, 2, 1, 3, 2, 1, 3, 2][i]] + 12
                put(_keys(_note(m), beat, 0.05), t0 + i * beat / 2 + rng.uniform(0, 0.01))
        if drums > 0 and b > 0:
            for q in range(4):
                tq = t0 + q * beat
                if q in (0, 2):
                    put(_kick(), tq, 0.55 * drums)
                if q in (1, 3):
                    put(_snare(rng), tq + 0.01, 0.28 * drums)
                put(_hat(rng), tq, drums)
                put(_hat(rng), tq + beat / 2 + 0.015, 0.6 * drums)
    out = _lp(out, 9000)
    out = np.tanh(out * 1.2)
    fade = int(1.5 * SR)
    out = out[: int(duration * SR)]
    out[-fade:] *= np.linspace(1, 0, fade)
    out[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    return norm(out, 0.8)
