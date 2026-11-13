"""Voz del video institucional de Zapatería Calipso con ElevenLabs, en UNA sola toma (entonación continua y menos caracteres),
partida después en segmentos con los tiempos exactos de cada palabra.
Escribe voice/final_<seg>.wav y voice/final.json.
Uso: ELEVEN_APPROVED=1 ../../.venv/bin/python voice_eleven.py [voz=brian]      (~310 caracteres)
     ../../.venv/bin/python voice_eleven.py tempo 1.08                          (ajusta ritmo, sin gastar créditos)"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import tts_eleven, pron, build as B
V = Path(__file__).parent / "voice"; V.mkdir(exist_ok=True)
voice = sys.argv[1] if len(sys.argv) > 1 else "dany"
# (clave, texto en pantalla/subtítulos, texto que se le dice al motor)
SEGS = [
 ("0", "Cada paso empieza aquí.", None),
 ("1", "Somos Zapaterías Calipso: moda en calzado para la mujer que sabe brillar.", None),
 ("2", "Zapatos, tacones, botines, botas,", None),
 ("3", "sandalias, huaraches, zapatillas y mucho más.", None),
 ("4", "Diseños que te hacen lucir divina, con la calidad que mereces y a precios pensados para ti.", None),
 ("5", "Ven y enamórate de tu próximo par.", None),
 ("6", "Zapaterías Calipso. Tu estilo, a cada paso.", None),
]


def generate():
    spoken = [pron.say(s or t) for _, t, s in SEGS]
    full = " ".join(spoken)
    raw = V / "take_raw.wav"
    r = tts_eleven.synth(full, voice, raw)
    words = r["words"]; a, sr = sf.read(raw, dtype="float32")
    counts = [len(s.split()) for s in spoken]
    assert sum(counts) == len(words), (sum(counts), len(words), [w["text"] for w in words])
    final, k = {}, 0
    for (key, text, _), n in zip(SEGS, counts):
        ws = words[k:k + n]; k += n
        nxt = words[k]["start"] if k < len(words) else len(a) / sr
        s0 = max(0.0, ws[0]["start"] - 0.05); e0 = min(nxt - 0.02, ws[-1]["end"] + 0.30, len(a) / sr)
        seg = a[int(s0 * sr):int(e0 * sr)].copy()
        # silencios internos de más de MAXGAP s (medidos en el audio) se acortan cortando silencio; nunca se estira la voz
        MAXGAP, xf = 0.30, int(0.02 * sr)
        hop = int(0.01 * sr)
        rms = np.array([np.sqrt(np.mean(seg[i:i + hop] ** 2) + 1e-12) for i in range(0, len(seg) - hop, hop)])
        quiet = 20 * np.log10(rms + 1e-12) < (20 * np.log10(np.percentile(rms, 95) + 1e-12) - 32)
        runs, i = [], 0
        while i < len(quiet):
            if quiet[i]:
                j = i
                while j < len(quiet) and quiet[j]: j += 1
                if i > 5 and j < len(quiet) - 5 and (j - i) * 0.01 > MAXGAP + 0.05: runs.append((i * 0.01, j * 0.01))
                i = j
            else: i += 1
        shifts, removed = [], 0.0
        for r0, r1 in runs:
            cut = (r1 - r0) - MAXGAP
            c0 = r0 + MAXGAP / 2 - removed
            i0, i1 = int(c0 * sr), int((c0 + cut) * sr)
            ramp = np.linspace(0, 1, xf)
            mixed = seg[i0 - xf:i0] * (1 - ramp) + seg[i1 - xf:i1] * ramp
            seg = np.concatenate([seg[:i0 - xf], mixed, seg[i1:]])
            shifts.append((r0 + MAXGAP / 2, cut)); removed += cut
        def shift(t):
            return t - sum(c for at, c in shifts if t > at)
        fo = int(0.10 * sr); seg[-fo:] *= np.linspace(1, 0, fo) ** 1.5; fi = int(0.012 * sr); seg[:fi] *= np.linspace(0, 1, fi)
        sf.write(V / "tmp.wav", seg, sr)
        B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(V / "tmp.wav"), "-af", "highpass=f=70,acompressor=threshold=-22dB:ratio=2.5:attack=5:release=90:makeup=1.5",
              "-ar", "48000", "-ac", "1", str(V / f"final_{key}.wav")])
        dur = sf.info(str(V / f"final_{key}.wav")).duration
        disp = text.split()
        out_w = [{"text": disp[i] if i < len(disp) else w["text"], "accent": False, "start": round(max(0.0, shift(w["start"] - s0)), 3), "end": round(min(dur, shift(w["end"] - s0)), 3)} for i, w in enumerate(ws)]
        gap = round((nxt - ws[-1]["end"]), 3)
        final[key] = {"file": f"final_{key}.wav", "src": f"elevenlabs:{voice}", "dur": round(dur, 3), "text": text, "words": out_w, "ok": True,
                      "rate": round(n / max(0.1, ws[-1]["end"] - ws[0]["start"]), 2), "natural_gap": gap}
        if shifts: print("   recortado", round(sum(c for _, c in shifts), 2), "s de silencio en", key)
        print(key, f"{dur:.2f}s", f'{final[key]["rate"]:.2f} pal/s', f"pausa {gap:.2f}s |", " ".join(f'{w["text"]}@{w["start"]:.2f}' for w in out_w)[:120])
    (V / "final.json").write_text(json.dumps(final, ensure_ascii=False, indent=1))
    print("toma", round(len(a) / sr, 2), "s ·", r["chars"], "caracteres ·", round(len(words) / (words[-1]["end"] - words[0]["start"]), 2), "pal/s promedio")


def retempo(k):
    f = json.loads((V / "final.json").read_text())
    for key, s in f.items():
        if s.get("tempo"): continue
        B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(V / s["file"]), "-af", f"rubberband=tempo={k}:pitchq=quality:formant=preserved", str(V / "tmp.wav")])
        (V / "tmp.wav").replace(V / s["file"])
        s["dur"] = round(sf.info(str(V / s["file"])).duration, 3); s["tempo"] = k; s["rate"] = round(s["rate"] * k, 2)
        for w in s["words"]: w["start"] = round(w["start"] / k, 3); w["end"] = round(min(s["dur"], w["end"] / k), 3)
    (V / "final.json").write_text(json.dumps(f, ensure_ascii=False, indent=1))
    print("tempo", k, "· habla total", round(sum(x["dur"] for x in f.values()), 2), "s")


def compact(maxgap=0.30):
    """Acorta silencios internos largos de las tomas finales cortando silencio (sin estirar la voz). Sin créditos."""
    f = json.loads((V / "final.json").read_text())
    for key, s in f.items():
        seg, sr = sf.read(V / s["file"], dtype="float32")
        hop, xf = int(0.01 * sr), int(0.02 * sr)
        rms = np.array([np.sqrt(np.mean(seg[i:i + hop] ** 2) + 1e-12) for i in range(0, len(seg) - hop, hop)])
        db = 20 * np.log10(rms + 1e-12); quiet = db < (np.percentile(db, 95) - 32)
        runs, i = [], 0
        while i < len(quiet):
            if quiet[i]:
                j = i
                while j < len(quiet) and quiet[j]: j += 1
                if i > 5 and j < len(quiet) - 5 and (j - i) * 0.01 > maxgap + 0.05: runs.append((i * 0.01, j * 0.01))
                i = j
            else: i += 1
        shifts, removed = [], 0.0
        for r0, r1 in runs:
            cut = (r1 - r0) - maxgap; c0 = r0 + maxgap / 2 - removed
            i0, i1 = int(c0 * sr), int((c0 + cut) * sr); ramp = np.linspace(0, 1, xf)
            seg = np.concatenate([seg[:i0 - xf], seg[i0 - xf:i0] * (1 - ramp) + seg[i1 - xf:i1] * ramp, seg[i1:]])
            shifts.append((r0 + maxgap / 2, cut)); removed += cut
        sh = lambda t: t - sum(c for at, c in shifts if t > at)
        for w in s["words"]: w["start"] = round(sh(w["start"]), 3); w["end"] = round(sh(w["end"]), 3)
        sf.write(V / s["file"], seg, sr); s["dur"] = round(len(seg) / sr, 3); s["compacted"] = round(removed, 2)
        print(key, f'{s["dur"]:.2f}s', "silencio recortado", round(removed, 2), "s en", len(runs), "pausas")
    (V / "final.json").write_text(json.dumps(f, ensure_ascii=False, indent=1))
    print("habla total", round(sum(x["dur"] for x in f.values()), 2), "s")


if __name__ == "__main__":
    if voice == "tempo": retempo(float(sys.argv[2]))
    elif voice == "compact": compact(float(sys.argv[2]) if len(sys.argv) > 2 else 0.30)
    else: generate()
