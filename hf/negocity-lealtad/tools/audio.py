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
def music():
    m = np.zeros((N, 2))
    t_rev = W("1", 3) - 0.12                   # aparece la tarjeta digital en el celular
    t_end = W("5", 0) - 0.06 + 0.03           # logo final
    bars_b = max(4, round((t_end - t_rev) * 110 / 240))     # compases enteros entre los dos impactos, a ~110 BPM
    bar = (t_end - t_rev) / bars_b
    beat = bar / 4
    bpm = 60 / beat
    # A · tensión (antes de la marca): pulso apagado en La menor, sin bombo
    nA = int(np.ceil(t_rev / bar))
    t0 = t_rev - nA * bar
    for b in range(nA):
        tb = t0 + b * bar
        chord = [[45, 52, 57], [41, 48, 53], [45, 52, 57], [43, 50, 55]][(b - nA) % 4]
        px = A._lp(pad([c + 12 for c in chord], bar * 1.02, 0.002), 1400) * 0.5
        put(m, px, tb, 0.55, -0.2); put(m, A._lp(pad([c + 12 for c in chord], bar * 1.02, -0.002), 1400) * 0.5, tb, 0.55, 0.2)
        for q in range(8):
            if b == nA - 1 and q >= 6:
                continue
            put(m, A._lp(pluck(chord[[0, 2, 1, 2, 0, 2, 1, 0][q]] + 12, 0.3, 0.6), 1800), tb + q * beat / 2, 0.32 + 0.06 * (q % 2 == 0), 0.3 if q % 2 else -0.3)
            if q % 2 == 0:
                put(m, shaker(), tb + q * beat / 2, 0.5)
    put(m, A.riser(bar * 0.95, 5), t_rev - bar * 0.95, 0.5)
    # impacto suave + brillo en la revelación de la tarjeta; brillo al aparecer el logo
    put(m, boom(), t_rev, 0.75); put(m, shimmer(), t_rev + 0.04, 0.5, 0.25)
    put(m, shimmer(1.4, 88), W("1", 1) - 0.05, 0.35, -0.25)
    # B · optimista: Do – Sol – La m – Fa
    prog = [([60, 64, 67], 48), ([59, 62, 67], 43), ([57, 60, 64], 45), ([57, 60, 65], 41)]
    arp = [0, 2, 1, 2, 0, 1, 2, 1]
    for b in range(bars_b):
        tb = t_rev + b * bar
        chord, root = prog[b % 4]
        full = b >= 2                 # el beat completo entra con las herramientas
        lift = b >= bars_b - 2        # "todo conectado": sube una octava
        last = b == bars_b - 1
        put(m, pad(chord, bar * 1.03, 0.003), tb, 0.42, -0.35); put(m, pad(chord, bar * 1.03, -0.003), tb, 0.42, 0.35)
        for q in range(8):
            tq = tb + q * beat / 2
            note = chord[arp[q]] + (24 if lift and q % 2 else 12)
            put(m, pluck(note, 0.4, 1.2 if lift else 1.0), tq, (0.5 if full else 0.38) * (1.0 if q % 2 == 0 else 0.8), 0.35 if q % 2 else -0.35)
            if b >= 1:
                put(m, bass(root, beat * 0.5), tq, 0.5 if q % 2 == 0 else 0.34)
                put(m, bass(root + 12, beat * 0.45), tq, 0.2)
            if full:
                put(m, A._hat(rng), tq, 1.0 if q % 2 else 0.6, 0.15)
        for q in range(4):
            tq = tb + q * beat
            if b >= 1 and not (last and q == 3):
                put(m, A._kick(), tq, 0.55 if full else 0.4)
            if full and q in (1, 3) and not (last and q == 3):
                put(m, clap(), tq, 0.5)
        if last:                      # redoble suave hacia el cierre
            for k in range(8):
                put(m, clap(), tb + 2 * beat + k * beat / 4, 0.14 + 0.05 * k)
            put(m, A.riser(beat * 2, 9), t_end - beat * 2, 0.45)
    # C · cierre en calma: impacto suave, acorde sostenido, melodía que resuelve
    put(m, boom(2.6), t_end, 0.8); put(m, shimmer(2.2), t_end + 0.04, 0.5, -0.2)
    tail = TOTAL - t_end
    put(m, pad([60, 64, 67, 74], tail + 0.2, 0.003), t_end, 0.5, -0.3); put(m, pad([60, 64, 67, 74], tail + 0.2, -0.003), t_end, 0.5, 0.3)
    put(m, bass(36 + 12, 2.5), t_end, 0.5)
    for k, n_ in enumerate([84, 79, 76, 79, 72, 76, 79, 84, 88]):
        tk = t_end + bar + k * beat
        if tk < TOTAL - 1.2:
            put(m, pluck(n_, 0.9, 1.1), tk, 0.36, 0.3 if k % 2 else -0.3)
    for ch in range(2):
        m[:, ch] = A._lp(m[:, ch], 11000)
    m = np.tanh(m * 0.9)
    fo = int(1.6 * SR); end = int(TOTAL * SR)
    m[end - fo:end] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    m[end:] = 0
    return m, bpm, t_rev, t_end


# ───────────────────────── efectos, con las mismas fórmulas de tiempo que las escenas
def sfx():
    x = np.zeros((N, 2))
    P = lambda name, at, g=0.4, pan=0.0: put(x, A.SFX[name]() if isinstance(name, str) else name, at + 1 / 30, g, pan)
    st = lambda sid: S[sid]["start"]
    # s1 · tarjeta de cartón olvidada
    P(rustle(0.3), 0.08, 0.45, -0.2)
    tB = W("0", 9) - 0.04
    P(A.thud(0.35, 3), tB + 0.04, 0.45); P(rustle(0.22), tB + 0.05, 0.5, 0.3)
    P(suck(0.5), st("s2-revela") - 0.5, 0.55)                      # zoom hacia la tarjeta
    # s2 · logo y tarjeta digital
    P("pop_hi", W("1", 3) + 0.25, 0.22, 0.2)
    P(whoosh(), W("1", 4) - 0.1, 0.3, -0.2)                        # la tarjeta se desprende y flota
    P(whoosh(), st("s3-cartel") - 0.24, 0.32, -0.4)
    # s3 · cafetería: escaneo del cartel
    s3 = st("s3-cartel"); tS = max(s3 + 0.3, W("2", 0) + 0.15)
    P(whoosh(), tS, 0.26, 0.5)
    P("tick", tS + 0.5, 0.22); P("tick", tS + 0.82, 0.22)
    tR = W("2", 5) - 0.12
    P("pop", tR + 0.05, 0.45, 0.3); P(bell(91, 0.9), tR + 0.28, 0.22, 0.3)
    P("pop_hi", W("2", 8) - 0.1, 0.3, -0.3)
    P(whoosh(), st("s4-sello") - 0.24, 0.3, 0.0)
    # s4 · el sello se llena, modo puntos
    s4 = st("s4-sello")
    P(whoosh(), s4 + 0.2, 0.22, 0.5)
    P("tick", s4 + 0.66, 0.2); P("tick", s4 + 0.92, 0.2)
    tSt = W("3", 3) - 0.04
    P("pop", tSt + 0.05, 0.6, 0.2); P("click", tSt + 0.05, 0.3, 0.2); P(bell(96, 0.7), tSt + 0.1, 0.18, 0.2)
    tP = W("3", 5) - 0.1
    P(whoosh(), tP, 0.26, -0.2)
    for k in range(7):
        P("tick", W("3", 6) + k * 0.1, 0.12 + 0.02 * k, 0.1)
    P("cash", W("3", 6) + 0.75, 0.2, 0.2)
    P(whoosh(), st("s5-premio") - 0.24, 0.3, 0.0)
    # s5 · premio dorado
    tC = W("4", 2) - 0.02
    P("pop", tC + 0.04, 0.55, 0.3)
    P(bell(88, 1.6), tC + 0.1, 0.5, 0.2); P(bell(95, 1.4), tC + 0.2, 0.4, 0.3); P(shimmer(1.6, 91), tC + 0.15, 0.4, 0.3)
    P("pop_hi", W("4", 3) - 0.05, 0.3, -0.2)
    P(suck(0.4), st("s6-cierre") - 0.32, 0.4)
    # s6 · cierre
    P(whoosh(), W("6", 3) - 0.32, 0.22); P("pop", W("6", 3) + 0.08, 0.3, 0.3); P(shimmer(1.0, 91), W("6", 6), 0.14, 0.3)
    return x


def main():
    out = HERE / "assets/audio"; out.mkdir(parents=True, exist_ok=True)
    voice = np.zeros(N)
    for k, s in SEG.items():
        v, sr = sf.read(ROOT / "projects/negocity-lealtad/voice" / f"final_{k}.wav", dtype="float64")
        a = int(round(s["s"] * SR)); voice[a:a + len(v)] += v[: N - a]
    voice /= max(1e-9, np.percentile(np.abs(voice[np.abs(voice) > 1e-3]), 99.5)) / 0.6
    mus, bpm, t_rev, t_end = music()
    fx = sfx()
    # ducking: la música baja cuando hay voz
    env = np.abs(signal.hilbert(voice[::48])); env = signal.savgol_filter(env, 301, 2)
    env = np.interp(np.arange(N), np.arange(len(env)) * 48, env)
    talk = signal.sosfiltfilt(signal.butter(1, 2.5, fs=SR, output="sos"), (env > 0.02).astype(float)).clip(0, 1)
    mgain = 0.62 - 0.36 * talk
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
    print(f"BPM {bpm:.1f} · revelación {t_rev:.2f}s · cierre {t_end:.2f}s · total {TOTAL:.2f}s")
    print(f"mix {meter.integrated_loudness(mix):.1f} LUFS · pico {20*np.log10(np.abs(mix).max()):.1f} dBFS · voz {lv(np.stack([voice,voice],1)):.1f} · música {lv(mus*0.9):.1f} · sfx {lv(fx*0.8):.1f} LUFS")


if __name__ == "__main__":
    main()
