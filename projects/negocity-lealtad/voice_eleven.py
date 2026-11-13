"""Voz del video de lealtad de Negocity con ElevenLabs, en UNA sola toma (entonación continua y menos caracteres),
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
voice = sys.argv[1] if len(sys.argv) > 1 else "brian"
# (clave, texto en pantalla/subtítulos, texto que se le dice al motor)
SEGS = [
 ("0", "¿Tus tarjetas de sellos terminan olvidadas o en la basura?", None),
 ("1", "Con Negocity, la tarjeta vive en el celular de tu cliente.", None),
 ("2", "Escanea tu cartel y la recibe al instante, sin descargar nada.", None),
 ("3", "Cada visita suma un sello… o puntos por lo que gasta.", None),
 ("4", "Y al completarla, gana su premio.", None),
 ("5", "Negocity. Haz que tus clientes vuelvan.", None),
 ("6", "Empieza hoy en negocity punto com punto mx.", "Empieza hoy en negocity punto com punto eme equis."),
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
        fo = int(0.10 * sr); seg[-fo:] *= np.linspace(1, 0, fo) ** 1.5; fi = int(0.012 * sr); seg[:fi] *= np.linspace(0, 1, fi)
        sf.write(V / "tmp.wav", seg, sr)
        B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(V / "tmp.wav"), "-af", "highpass=f=70,acompressor=threshold=-22dB:ratio=2.5:attack=5:release=90:makeup=1.5",
              "-ar", "48000", "-ac", "1", str(V / f"final_{key}.wav")])
        dur = sf.info(str(V / f"final_{key}.wav")).duration
        disp = text.split()
        out_w = [{"text": disp[i] if i < len(disp) else w["text"], "accent": False, "start": round(max(0.0, w["start"] - s0), 3), "end": round(min(dur, w["end"] - s0), 3)} for i, w in enumerate(ws)]
        gap = round((nxt - ws[-1]["end"]), 3)
        final[key] = {"file": f"final_{key}.wav", "src": f"elevenlabs:{voice}", "dur": round(dur, 3), "text": text, "words": out_w, "ok": True,
                      "rate": round(n / max(0.1, ws[-1]["end"] - ws[0]["start"]), 2), "natural_gap": gap}
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


if __name__ == "__main__":
    if voice == "tempo": retempo(float(sys.argv[2]))
    else: generate()
