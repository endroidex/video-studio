"""Voz de Negocity con ElevenLabs. Escribe voice/final_<seg>.wav y voice/final.json (mismo formato que voice2.py).
Uso: ELEVEN_APPROVED=1 ../../.venv/bin/python voice_eleven.py [voz=marto]
(solo cuando el usuario pide explícitamente el video con ElevenLabs; gasta ~610 caracteres)"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import tts_eleven, pron, build as B
V = Path(__file__).parent / "voice"
voice = sys.argv[1] if len(sys.argv) > 1 else tts_eleven.default_voice()
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0   # ritmo natural, sin acelerar
SEGS = [
 ("0", "¿Tu negocio vive entre libretas, chats y hojas sueltas?"),
 ("1", "Clientes que no regresan… cuentas que no cuadran… contactos que nunca encuentras."),
 ("2a", "Conoce Negocity:"),
 ("2b", "todas las herramientas de tu negocio, en un solo lugar."),
 ("3", "Tus clientes juntan visitas o puntos con una tarjeta digital en su celular… y siempre regresan."),
 ("4", "Mira quién vuelve, tus mejores días y cuánto vendes, en tiempo real."),
 ("5", "Tu equipo trabaja desde su celular, y tus proveedores y contactos siempre están a la mano."),
 ("6", "Clientes, administración y datos, todo conectado. Sin instalar nada."),
 ("7", "Negocity. Tu negocio, más fácil."),
 ("8", "Empieza hoy en negocity punto com punto eme equis."),
]
def generate():
    final, chars = {}, 0
    for i, (key, text) in enumerate(SEGS):
        prev = " ".join(t for _, t in SEGS[max(0, i - 1):i]) or None
        nxt = SEGS[i + 1][1] if i + 1 < len(SEGS) else None
        raw = V / f"el_{key}_raw.wav"
        r = tts_eleven.synth(pron.say(text), voice, raw, speed=speed, prev=prev, nxt=nxt)
        for w, orig in zip(r["words"], text.split()): w["text"] = orig      # en pantalla, la escritura original
        chars += r["chars"]
        a, sr = sf.read(raw, dtype="float32")
        s0 = max(0.0, r["words"][0]["start"] - 0.05); e0 = min(len(a) / sr, r["words"][-1]["end"] + 0.28)
        seg = a[int(s0 * sr):int(e0 * sr)].copy()
        fo = int(0.12 * sr); seg[-fo:] *= np.linspace(1, 0, fo) ** 1.5; fi = int(0.015 * sr); seg[:fi] *= np.linspace(0, 1, fi)
        sf.write(V / "tmp.wav", seg, sr)
        B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(V / "tmp.wav"), "-af", "highpass=f=70,acompressor=threshold=-22dB:ratio=2.5:attack=5:release=90:makeup=1.5", "-ar", "48000", "-ac", "1", str(V / f"final_{key}.wav")])
        dur = sf.info(str(V / f"final_{key}.wav")).duration
        words = [{"text": w["text"], "accent": False, "start": round(max(0.0, w["start"] - s0), 3), "end": round(min(dur, w["end"] - s0), 3)} for w in r["words"]]
        span = r["words"][-1]["end"] - r["words"][0]["start"]
        final[key] = {"file": f"final_{key}.wav", "src": f"elevenlabs:{voice}", "dur": round(dur, 3), "text": text, "words": words, "ok": True, "rate": round(len(words) / span, 2)}
        print(key, f"{dur:.2f}s", f"{len(words)/span:.2f} pal/s |", " ".join(f'{w["text"]}@{w["start"]:.2f}' for w in words)[:130])
    (V / "final.json").write_text(json.dumps(final, ensure_ascii=False, indent=1))
    print("habla total", round(sum(f["dur"] for f in final.values()), 2), "s ·", chars, "caracteres")


def retempo(k):
    """Acelera/desacelera las tomas finales conservando el tono (rubberband) y reescala los tiempos."""
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
    if voice == "tempo": retempo(speed)
    else: generate()
