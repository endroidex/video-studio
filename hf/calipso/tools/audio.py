#!/usr/bin/env python3
"""
Audio de Negocity: voz (tomas finales) + música original sintetizada (~106 BPM, impacto en la revelación y en el cierre)
+ efectos sincronizados con las animaciones + ducking + master a −14 LUFS.
Lee timing.json (los mismos tiempos que usan las escenas) y escribe assets/audio/{mix,voz,musica,sfx}.wav
Uso: ../../.venv/bin/python tools/audio.py
"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy import signal

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audio_lib as A

SR = A.SR
T = json.loads((HERE / "timing.json").read_text())
SEG, TOTAL = T["segs"], T["total"]
N = int((TOTAL + 0.5) * SR)
S = {s["id"]: s for s in T["scenes"]}
W = lambda k, i: SEG[k]["w"][i]["s"]
LS = lambda k: SEG[k]["s"]
LE = lambda k: SEG[k]["e"]
rng = np.random.default_rng(7)


def put(buf, x, at, gain=1.0, pan=0.0):
    """mezcla x (mono) en buf (N,2) en el segundo `at`, con paneo −1..1"""
    s = int(round(at * SR))
    if s < 0:
        x = x[-s:]; s = 0
    e = min(len(buf), s + len(x))
    if e <= s:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[s:e, 0] += x[: e - s] * gain * l * 1.414
    buf[s:e, 1] += x[: e - s] * gain * r * 1.414


# ───────────────────────── instrumentos
def tone(f, t):
    return np.sin(2 * np.pi * f * t)


def pluck(midi, dur=0.42, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = A._note(midi)
    x = sum((1 / h) * tone(f * h, t) * np.exp(-t * (5 + 3.2 * h / bright)) for h in range(1, 7))
    x *= np.minimum(1, t / 0.003)
    return x * 0.5


def pad(midis, dur, det=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(tone(A._note(m) * (1 + det), t) + 0.35 * tone(A._note(m) * 2 * (1 - det), t) + 0.12 * tone(A._note(m) * 3, t) for m in midis)
    env = np.minimum(1, t / 0.22) * np.minimum(1, (dur - t) / 0.35).clip(0, 1)
    return x * env / len(midis) * 0.5


def bass(midi, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = A._note(midi)
    x = tone(f, t) + 0.55 * tone(2 * f, t) + 0.2 * tone(3 * f, t)
    return np.tanh(x * 1.4) * np.minimum(1, t / 0.004) * np.exp(-t * 5.5) * 0.6


def clap():
    n = int(0.22 * SR); t = np.arange(n) / SR
    nz = A._bp(rng.standard_normal(n), 900, 3800)
    env = sum(np.exp(-np.maximum(0, t - d) * 60) * (t >= d) for d in (0.0, 0.011, 0.023)) * np.exp(-t * 9)
    return nz * env * 0.5


def shaker():
    n = int(0.05 * SR); t = np.arange(n) / SR
    return A._hp(rng.standard_normal(n), 6500) * np.exp(-t * 60) * 0.2


def boom(dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 46 + 70 * np.exp(-t * 18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    body = (tone(98, t) + 0.5 * tone(196, t)) * np.exp(-t * 5) * 0.5      # audible en bocinas de celular
    air = A._lp(A._hp(rng.standard_normal(n), 1500), 9000) * np.exp(-t * 3.2) * 0.22
    return np.tanh((sub + body) * 1.3) * 0.8 + air


def shimmer(dur=1.8, base=84):
    n = int(dur * SR); out = np.zeros(n)
    for k, m in enumerate([0, 4, 7, 12, 16, 19, 24, 16, 12, 19]):
        t0 = k * 0.055 + rng.uniform(0, 0.02); s = int(t0 * SR); tt = np.arange(n - s) / SR
        f = A._note(base + m)
        out[s:] += (tone(f, tt) + 0.3 * tone(f * 2.01, tt)) * np.exp(-tt * 4.5) * np.minimum(1, tt / 0.004) * (0.9 - 0.05 * k)
    return A.norm(out, 0.5)


def bell(midi=88, dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR; f = A._note(midi)
    x = sum(a * tone(f * m, t) * np.exp(-t * d) for a, m, d in [(1, 1, 3.5), (0.55, 2.0, 5), (0.3, 3.01, 7), (0.2, 4.2, 10), (0.1, 5.4, 14)])
    return A.norm(x * np.minimum(1, t / 0.002), 0.5)


def rustle(dur=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    x = A._bp(rng.standard_normal(n), 1800, 7000) * np.sin(np.pi * t / dur) ** 2
    return x * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t) ** 2) * 0.35


def suck(dur=0.5):
    """aire que se aspira: barrido ascendente que corta en seco"""
    x = A.whoosh(dur, True, int(rng.integers(1, 999)))
    n = len(x); x *= np.linspace(0.1, 1, n) ** 2
    x[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))
    return x


WH = [A.whoosh(0.42, True, 11), A.whoosh(0.5, False, 23), A.whoosh(0.36, True, 37), A.whoosh(0.46, False, 51)]
_wi = [0]


def whoosh():
    _wi[0] += 1
    return WH[_wi[0] % len(WH)]


# ───────────────────────── música
MUSIC_FILE = HERE / "assets/music/step-in-style.wav"


def music():
    """Canción del cliente (Step in Style). Se recorta el inicio para que su final natural coincida con el del video."""
    import pyloudnorm as pyln
    a, sr = sf.read(MUSIC_FILE, dtype="float64")
    if a.ndim == 1: a = np.stack([a, a], 1)
    if sr != SR: a = np.stack([signal.resample_poly(a[:, c], SR, sr) for c in range(2)], 1)
    a = a * 10 ** ((-14.0 - pyln.Meter(SR).integrated_loudness(a)) / 20)       # referencia común
    off = max(0.0, len(a) / SR - TOTAL)                                        # su fade-out termina con el video
    a = a[int(off * SR):]
    m = np.zeros((N, 2)); n = min(N, len(a)); m[:n] = a[:n]
    fi = int(0.25 * SR); m[:fi] *= np.linspace(0, 1, fi)[:, None]
    end = int(TOTAL * SR); fo = int(0.6 * SR); m[end - fo:end] *= np.linspace(1, 0, fo)[:, None]; m[end:] = 0
    return m, 106.1, off, TOTAL


# ───────────────────────── efectos, con las mismas fórmulas de tiempo que las escenas
def heel(seed=0):
    """taconazo suave: clic agudo + golpe corto, como un paso sobre piso de tienda"""
    r = np.random.default_rng(100 + seed); n = int(0.14 * SR); t = np.arange(n) / SR
    click_ = A._bp(r.standard_normal(n), 2500, 9000) * np.exp(-t * 90) * 0.7
    body = np.sin(2 * np.pi * (180 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 35) * 0.5
    return A.norm(click_ + body, 0.5)


def sfx():
    x = np.zeros((N, 2))
    P = lambda name, at, g=0.4, pan=0.0: put(x, A.SFX[name]() if isinstance(name, str) else name, at + 1 / 30, g, pan)
    st = lambda sid: S[sid]["start"]
    # s1 · pasos que suben + el círculo rosa
    for i in range(7):
        P(heel(i), 0.05 + i * 0.22, 0.32 - i * 0.015, -0.25 if i % 2 == 0 else 0.25)
    P(suck(0.55), st("s2-somos") - 0.55, 0.45)
    # s2 · tienda real, logo, botas
    P(whoosh(), st("s2-somos") + 0.05, 0.3)
    P("pop", W("1", 1) - 0.06, 0.3)
    tB = W("1", 3) - 0.3
    P(whoosh(), tB, 0.32, 0.0); P("pop_hi", tB + 0.38, 0.22, 0.4)
    P(whoosh(), tB + 0.3, 0.2, -0.3)
    P(whoosh(), st("s3-familia") - 0.2, 0.3, 0.2)
    # s3 · categorías (cada palabra con un golpe seco) y collage
    for i, t in enumerate([W("2", 0), W("2", 1), W("2", 2), W("2", 3)]):
        P(A.thud(0.25, 10 + i), t - 0.08, 0.32, [-0.3, 0.3, -0.2, 0.2][i]); P("click", t - 0.06, 0.25)
    s3 = st("s3-familia")
    for i in range(8):
        P(heel(10 + i), s3 + 0.1 + i * 0.3, 0.16, -0.5 + i * 0.13)
    P(whoosh(), LS("3") - 0.25, 0.28)
    for i in range(3):
        P("pop", W("3", i) - 0.06, 0.32, [-0.3, 0.3, 0.0][i])
    P(whoosh(), W("3", 3) - 0.15, 0.32); P(whoosh(), W("3", 3) + 0.05, 0.22, -0.4); P(whoosh(), W("3", 3) + 0.13, 0.22, 0.4)
    P(shimmer(1.0, 86), W("3", 5), 0.16)
    P(whoosh(), st("s4-calidad") - 0.3, 0.3)
    # s4 · calidad (brillo), callouts y etiqueta de precio
    P(shimmer(1.2, 91), st("s4-calidad") + 0.55, 0.18, 0.2)
    P("tick", W("4", 0) + 0.05, 0.22, -0.2); P("tick", W("4", 8) - 0.05, 0.22, 0.3)
    P(shimmer(1.1, 93), W("4", 5) + 0.15, 0.22, 0.3)
    tP = W("4", 13) - 0.25
    P(whoosh(), tP, 0.25, 0.3); P(A.thud(0.3, 4), tP + 0.5, 0.22, 0.3); P(bell(93, 0.8), tP + 0.55, 0.14, 0.3)
    # s5 · ven a conocernos
    P(whoosh(), st("s5-visita"), 0.3); P("pop", st("s5-visita") + 0.42, 0.35)
    P(suck(0.45), st("s6-cierre") - 0.45, 0.4)
    # s6 · cierre: brillo del logo y pasos finales
    P(shimmer(1.6, 88), W("6", 0) + 0.9, 0.22, 0.2)
    for i in range(9):
        P(heel(30 + i), W("6", 4) + i * 0.17, 0.18, -0.6 + i * 0.15)
    return x


def main():
    out = HERE / "assets/audio"; out.mkdir(parents=True, exist_ok=True)
    voice = np.zeros(N)
    for k, s in SEG.items():
        v, sr = sf.read(ROOT / "projects/calipso/voice" / f"final_{k}.wav", dtype="float64")
        a = int(round(s["s"] * SR)); voice[a:a + len(v)] += v[: N - a]
    voice /= max(1e-9, np.percentile(np.abs(voice[np.abs(voice) > 1e-3]), 99.5)) / 0.6
    mus, bpm, t_rev, t_end = music()
    fx = sfx()
    # ducking: la música baja cuando hay voz
    env = np.abs(signal.hilbert(voice[::48])); env = signal.savgol_filter(env, 301, 2)
    env = np.interp(np.arange(N), np.arange(len(env)) * 48, env)
    talk = signal.sosfiltfilt(signal.butter(1, 2.5, fs=SR, output="sos"), (env > 0.02).astype(float)).clip(0, 1)
    mgain = 0.80 - 0.46 * talk
    mus = mus * mgain[:, None]
    mix = np.stack([voice, voice], 1) * 1.0 + mus * 0.9 + fx * 0.8
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    end = int(TOTAL * SR); mix = mix[:end]
    g = 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
    mix *= g
    ceil = 10 ** (-1.5 / 20); knee = ceil * 0.75
    a = np.abs(mix); mix = np.where(a > knee, np.sign(mix) * (knee + (ceil - knee) * np.tanh((a - knee) / (ceil - knee))), mix)
    sf.write(out / "mix.wav", mix.astype(np.float32), SR, subtype="PCM_16")
    for name, st in (("voz", np.stack([voice, voice], 1)), ("musica", mus * 0.9), ("sfx", fx * 0.8)):
        sf.write(out / f"{name}.wav", (st[:end] * g).astype(np.float32), SR, subtype="PCM_16")
    lv = lambda z: meter.integrated_loudness(z[:end] * g)
    print(f"canción: Step in Style ({bpm:.0f} BPM) · inicio recortado {t_rev:.2f}s · total {TOTAL:.2f}s")
    print(f"mix {meter.integrated_loudness(mix):.1f} LUFS · pico {20*np.log10(np.abs(mix).max()):.1f} dBFS · voz {lv(np.stack([voice,voice],1)):.1f} · música {lv(mus*0.9):.1f} · sfx {lv(fx*0.8):.1f} LUFS")


if __name__ == "__main__":
    main()
